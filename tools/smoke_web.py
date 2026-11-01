"""Real-model web integration smoke test; no mocked detection or OCR."""
import io,json,pathlib,sys,tempfile,time,zipfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from fasteplate.web import create_app
from fasteplate.config import ROOT
from sample_image import sample_image
from PIL import Image
HEADERS={'X-FastePlate':'1'}

def wait(client,job_id,timeout=120):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        response=client.get('/api/jobs/'+job_id)
        assert response.status_code==200,response.json
        data=response.json
        if data['state']=='error': raise AssertionError(data['error'])
        if data['state']=='done': return data
        time.sleep(.15)
    raise AssertionError('Analysis timed out')

def upload(client,image,**fields):
    return client.post('/api/jobs',headers=HEADERS,data={'image':(io.BytesIO(image),'voiture_ب.jpg'),'mode':'color','confidence':'.35',**fields})

with tempfile.TemporaryDirectory() as runtime:
    app=create_app(runtime); app.testing=True
    service=app.extensions['analysis_service']
    try:
        client=app.test_client()
        page=client.get('/')
        assert page.status_code==200 and b'FASTEPLATE' in page.data
        for asset in ['app.js','style.css','favicon.svg']:
            assert client.get('/static/'+asset).status_code==200
        source=sample_image().read_bytes()
        assert client.post('/api/jobs').status_code==403
        assert upload(client,source,mode='invalid').status_code==400
        assert upload(client,source,confidence='nan').status_code==400
        assert upload(client,b'not an image').status_code==400
        assert client.post('/api/jobs',headers=HEADERS).status_code==400
        start=upload(client,source)
        assert start.status_code==202,start.json
        job_id=start.json['id']
        assert upload(client,source).status_code==409
        data=wait(client,job_id)
        assert data['plates'],data
        other=app.test_client()
        assert other.get('/api/jobs/'+job_id).status_code==404
        assert client.get(data['annotated_url']).mimetype=='image/png'
        assert client.get(data['original_url']).status_code==200
        assert client.get(data['plates'][0]['crop_url']).mimetype=='image/png'
        assert client.get('/api/jobs/'+job_id+'/image/crop/999').status_code==404
        raw=data['plates'][0]['raw_text']
        correction='90743 ب 26'
        path='/api/jobs/'+job_id+'/plates/0'
        corrected=client.patch(path,headers=HEADERS,json={'text':correction})
        assert corrected.status_code==200,corrected.json
        assert corrected.json['plates'][0]['raw_text']==raw
        assert corrected.json['plates'][0]['corrected_text']==correction
        assert client.patch(path,headers=HEADERS,json={'text':'x'*251}).status_code==400
        exported=client.get('/api/jobs/'+job_id+'/export')
        assert exported.status_code==200
        with zipfile.ZipFile(io.BytesIO(exported.data)) as archive:
            assert {'detection.png','plate_01.png','results.csv','results.json','results.txt'}<=set(archive.namelist())
            rows=json.loads(archive.read('results.json'))
            assert rows[0]['raw_ocr']==raw and rows[0]['corrected_text']==correction
            assert rows[0]['source']=='voiture_ب.jpg'
            assert archive.read('results.csv').startswith(b'\xef\xbb\xbf')
            assert correction in archive.read('results.txt').decode('utf-8')
        assert client.patch(path,headers=HEADERS,json={'text':None}).json['plates'][0]['corrected_text'] is None
        detector,ocr=service.pipeline.detector,service.pipeline.ocr
        blank=io.BytesIO(); Image.new('RGB',(640,480),'white').save(blank,format='PNG')
        second=upload(client,blank.getvalue()); assert second.status_code==202
        empty=wait(client,second.json['id']); assert not empty['plates']
        assert service.pipeline.detector is detector and service.pipeline.ocr is ocr
        # Verify dimensions before expensive image decoding or inference.
        huge=io.BytesIO();Image.new('RGB',(4000,3100),'white').save(huge,format='PNG')
        assert upload(client,huge.getvalue()).status_code==400
        print('PASS: web page/assets, real YOLO/OCR, async job status, concurrent request guard, Arabic correction/reset, downloads/ZIP, session isolation, upload validation, no detections, model reuse')
        print(json.dumps({'plates':len(data['plates']),'seconds':data['seconds'],'initialization_seconds':data['initialization_seconds'],'raw_ocr':raw},ensure_ascii=True))
    finally:
        service.shutdown()
