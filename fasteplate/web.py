"""Local browser application; one persistent CPU inference worker."""
from __future__ import annotations
import io
import math
import os
import secrets
import shutil
import tempfile
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file, session
from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.exceptions import HTTPException

from .config import ROOT
from .detection import save_image
from .exporting import export_result
from .pipeline import Pipeline

MODES = {'color', 'resize', 'contrast', 'threshold', 'perspective'}
MAX_PIXELS = 12_000_000

@dataclass
class Job:
    id: str
    owner: str
    directory: Path
    filename: str
    created: float
    state: str = 'queued'
    message: str = 'Waiting for analysis…'
    result: object = None
    error: str | None = None

class AnalysisService:
    def __init__(self, directory, pipeline=None):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.pipeline = pipeline or Pipeline()
        self.jobs = {}
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='fasteplate')

    def cleanup(self):
        now = time.time()
        finished = sorted((j for j in self.jobs.values() if j.state in {'done','error'}), key=lambda j:j.created)
        for i, job in enumerate(finished):
            if now-job.created > 1800 or i < len(finished)-3:
                self.jobs.pop(job.id, None)
                shutil.rmtree(job.directory, ignore_errors=True)

    def submit(self, image, owner, filename, mode, confidence):
        with self.lock:
            self.cleanup()
            if any(j.state in {'queued','running'} for j in self.jobs.values()):
                raise RuntimeError('An analysis is already running. Please wait and try again.')
            job_id = secrets.token_urlsafe(24)
            directory = self.directory / job_id
            directory.mkdir()
            try:
                image.save(directory/'input.png')
            except Exception:
                shutil.rmtree(directory, ignore_errors=True)
                raise
            job = Job(job_id, owner, directory, filename, time.time())
            self.jobs[job_id] = job
            self.executor.submit(self.run, job, mode, confidence)
            return job

    def run(self, job, mode, confidence):
        def progress(message):
            with self.lock:
                job.state = 'running'
                job.message = message
        try:
            result = self.pipeline.run(job.directory/'input.png',mode,confidence,progress)
            result.source = job.filename
            save_image(job.directory/'annotated.png', result.annotated)
            for i, plate in enumerate(result.plates):
                save_image(job.directory/f'crop_{i}.png', plate.crop)
            with self.lock:
                job.result = result
                job.state = 'done'
                job.message = 'Analysis complete' if result.plates else 'No plates detected'
        except Exception as exc:
            with self.lock:
                job.state = 'error'
                job.error = f'{type(exc).__name__}: {exc}'
                job.message = 'Analysis failed'

    def owned(self, job_id, owner):
        self.cleanup()
        job = self.jobs.get(job_id)
        return job if job is not None and job.owner == owner else None

    def shutdown(self):
        self.executor.shutdown(wait=True)


def create_app(runtime_directory=None, pipeline=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=secrets.token_hex(32),MAX_CONTENT_LENGTH=20*1024*1024,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Strict')
    runtime = Path(runtime_directory or tempfile.mkdtemp(prefix='fasteplate-web-'))
    service = AnalysisService(runtime, pipeline)
    app.extensions['analysis_service'] = service

    @app.before_request
    def same_origin():
        if request.method in {'POST','PATCH','DELETE'} and request.headers.get('X-FastePlate') != '1':
            return jsonify(error='Please submit this request through the FastePlate application.'),403
        if 'owner' not in session:
            session['owner'] = secrets.token_urlsafe(24)

    @app.after_request
    def response_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' blob: data:; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'"
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(HTTPException)
    def http_error(exc):
        if request.path.startswith('/api/'):
            message='Image exceeds the 20 MB upload limit.' if exc.code==413 else exc.description
            return jsonify(error=message),exc.code
        return exc

    def get_job(job_id):
        from flask import abort
        job = service.owned(job_id, session['owner'])
        if job is None:
            abort(404, description='Analysis not found or expired. Please upload the image again.')
        return job

    def describe(job):
        data=dict(id=job.id,state=job.state,message=job.message,error=job.error,filename=job.filename)
        if job.result is not None:
            result=job.result
            data.update(seconds=result.seconds,initialization_seconds=result.initialization_seconds,original_url=f'/api/jobs/{job.id}/image/original',annotated_url=f'/api/jobs/{job.id}/image/annotated',plates=[dict(index=i,bbox=list(p.bbox),detection_confidence=p.detection_confidence,raw_text=p.raw_text,normalized_text=p.normalized_text,corrected_text=p.corrected_text,ocr_confidence=p.ocr_confidence,warning=p.warning,crop_url=f'/api/jobs/{job.id}/image/crop/{i}') for i,p in enumerate(result.plates)])
        return data

    @app.get('/')
    def index():
        return render_template('index.html')

    @app.post('/api/jobs')
    def analyze():
        upload=request.files.get('image')
        if upload is None or not upload.filename:
            return jsonify(error='Choose an image before starting analysis.'),400
        mode=request.form.get('mode','color')
        try:
            confidence=float(request.form.get('confidence','.35'))
            if not math.isfinite(confidence) or not .05<=confidence<=.95: raise ValueError()
        except ValueError:
            return jsonify(error='Detection threshold must be between 0.05 and 0.95.'),400
        if mode not in MODES:
            return jsonify(error='Unknown image preprocessing mode.'),400
        try:
            with Image.open(upload.stream) as source:
                if source.format not in {'JPEG','PNG','BMP','WEBP'}:
                    return jsonify(error='Use a JPG, PNG, BMP or WebP image.'),400
                if source.width*source.height>MAX_PIXELS:
                    return jsonify(error='Image exceeds 12 megapixels. Please resize it before uploading.'),400
                image=ImageOps.exif_transpose(source).convert('RGB')
                image.load()
        except (UnidentifiedImageError,OSError,ValueError,Image.DecompressionBombError):
            return jsonify(error='This image could not be read. Choose a valid JPG, PNG, BMP or WebP file.'),400
        filename=upload.filename.replace('\\','/').split('/')[-1][:180]
        try:
            job=service.submit(image,session['owner'],filename,mode,confidence)
        except RuntimeError as exc:
            return jsonify(error=str(exc)),409
        return jsonify(id=job.id,state='queued'),202

    @app.get('/api/jobs/<job_id>')
    def status(job_id):
        with service.lock:
            return jsonify(describe(get_job(job_id)))

    @app.get('/api/jobs/<job_id>/image/<kind>')
    @app.get('/api/jobs/<job_id>/image/<kind>/<int:plate_index>')
    def image(job_id,kind,plate_index=None):
        from flask import abort
        with service.lock:
            job=get_job(job_id)
            if job.state!='done': abort(409,description='The analysis is not complete.')
            if kind=='original' and plate_index is None: path=job.directory/'input.png'
            elif kind=='annotated' and plate_index is None: path=job.directory/'annotated.png'
            elif kind=='crop' and plate_index is not None and 0<=plate_index<len(job.result.plates): path=job.directory/f'crop_{plate_index}.png'
            else: abort(404)
            return send_file(path,mimetype='image/png',as_attachment=request.args.get('download')=='1',download_name=path.name)

    @app.patch('/api/jobs/<job_id>/plates/<int:plate_index>')
    def correct(job_id,plate_index):
        payload=request.get_json(silent=True)
        if not isinstance(payload,dict) or 'text' not in payload or (payload['text'] is not None and not isinstance(payload['text'],str)):
            return jsonify(error='Correction must be text, or null to restore the OCR result.'),400
        text=payload['text']
        if text is not None and len(text)>250:
            return jsonify(error='Correction must be 250 characters or fewer.'),400
        with service.lock:
            job=get_job(job_id)
            if job.state!='done' or not 0<=plate_index<len(job.result.plates):
                return jsonify(error='Plate not found.'),404
            job.result.plates[plate_index].corrected_text=text
            return jsonify(describe(job))

    @app.get('/api/jobs/<job_id>/export')
    def export(job_id):
        from flask import abort
        with service.lock:
            job=get_job(job_id)
            if job.state!='done': abort(409,description='The analysis is not complete.')
            # Exports are rebuilt from the current corrections; each is isolated.
            with tempfile.TemporaryDirectory(prefix='export-',dir=runtime) as directory:
                export_path=export_result(job.result,Path(directory)/'results')
                stream=io.BytesIO()
                with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as archive:
                    for path in export_path.iterdir(): archive.write(path,path.name)
                stream.seek(0)
            return send_file(stream,mimetype='application/zip',as_attachment=True,download_name='FastePlate_results.zip')

    return app
