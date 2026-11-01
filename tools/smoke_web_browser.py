"""Optional Chromium QA using the already installed Qt WebEngine, not a runtime dependency."""
import os,sys,pathlib,threading,base64,json,time
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS']='--disable-gpu'
os.environ['QT_QUICK_BACKEND']='software'
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QTimer,QUrl
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage
from werkzeug.serving import make_server,WSGIRequestHandler
class QuietHandler(WSGIRequestHandler):
    def log_request(self,*args,**kwargs): pass
from fasteplate.web import create_app
from fasteplate.config import ROOT
from sample_image import sample_image
import tempfile

class Page(QWebEnginePage):
    def javaScriptConsoleMessage(self,level,message,line,source):
        if level==QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
            failures.append(f'Browser console: {message} ({line})')

application=QApplication([])
font_root=pathlib.Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
for name in ['segoeui.ttf','tahoma.ttf']:
    if (font_root/name).exists():QFontDatabase.addApplicationFont(str(font_root/name))
runtime=tempfile.TemporaryDirectory()
app=create_app(runtime.name)
server=make_server('127.0.0.1',0,app,threaded=True,request_handler=QuietHandler)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
failures=[]
view=QWebEngineView();page=Page(view);view.setPage(page);view.resize(1440,1100);view.show()
phase='loading';started=time.monotonic();in_callback=False;phase_started=started
payload=base64.b64encode(sample_image().read_bytes()).decode()

def fail(message):
    failures.append(message);application.quit()

def initial(ok):
    global phase
    if not ok:fail('Page failed to load');return
    phase='upload'
    QTimer.singleShot(600,begin)

def begin():
    script="""(()=>{const bytes=Uint8Array.from(atob('%s'),c=>c.charCodeAt(0));const file=new File([bytes],'test-vehicle.jpg',{type:'image/jpeg'});const transfer=new DataTransfer();transfer.items.add(file);document.getElementById('file-input').files=transfer.files;document.getElementById('file-input').dispatchEvent(new Event('change',{bubbles:true}));})()"""%payload
    page.runJavaScript(script)

def inspect(data):
    global phase,in_callback,phase_started
    in_callback=False
    if not data:return
    d=json.loads(data)
    if d.get('notice'):fail(d['notice']);return
    if phase=='upload' and d['canAnalyze']:
        phase='analyzing';page.runJavaScript("document.getElementById('analyze-button').click()")
    elif phase=='analyzing' and d['rows']>0 and d['canAnalyze']:
        if not d['reading'] or d['reading']=='—':fail('Missing OCR reading');return
        phase='correcting'
        page.runJavaScript("(()=>{const input=document.getElementById('correction');input.value='90743 \\u0628 26';input.dispatchEvent(new Event('input',{bubbles:true}));document.getElementById('save-correction').click();})()")
    elif phase=='correcting' and d['correctionSaved'] and d['canExport']:
        if '\u0628' not in d['tableText']:fail('Arabic correction missing from results');return
        phase='exporting'
        page.runJavaScript("fetch(document.getElementById('download-annotated').href).then(r=>{if(!r.ok)throw new Error('Download failed');window.qaDownload=true;}).catch(e=>{window.qaError=e.message;})")
    elif phase=='exporting' and d['download']:
        phase='desktop-paint';phase_started=time.monotonic()
    elif phase=='desktop-paint' and time.monotonic()-phase_started>2:
        view.grab().save(str(ROOT/'evaluation/web-preview.png'))
        phase='mobile';phase_started=time.monotonic();view.resize(420,1500)
    elif phase=='mobile' and time.monotonic()-phase_started>2 and d['viewportWidth']<=420:
        if d['scrollWidth']>d['viewportWidth']+1:fail('Mobile viewport overflows horizontally');return
        phase='done';print('PASS: real Chromium page, image upload, async recognition, Arabic correction, image download, desktop/mobile layout and screenshots',flush=True);application.quit()

def tick():
    global in_callback
    if time.monotonic()-started>180:fail('Browser test timeout at '+phase);return
    if phase in {'loading','done'} or in_callback:return
    in_callback=True
    page.runJavaScript("JSON.stringify({notice:document.getElementById('notice').hidden?'':document.getElementById('notice').textContent,canAnalyze:!document.getElementById('analyze-button').disabled,canExport:!document.getElementById('export-button').disabled,rows:document.querySelectorAll('.plate-row').length,reading:document.getElementById('ocr-reading').textContent,correctionSaved:document.getElementById('correction-status').textContent.includes('Correction saved'),tableText:document.getElementById('results-body').textContent,download:window.qaDownload===true,viewportWidth:innerWidth,scrollWidth:document.documentElement.scrollWidth})",inspect)

page.loadFinished.connect(initial)
timer=QTimer();timer.timeout.connect(tick);timer.start(500)
view.load(QUrl(f'http://127.0.0.1:{server.server_port}'))
application.exec()
timer.stop();view.close();server.shutdown();thread.join(timeout=5)
app.extensions['analysis_service'].shutdown();runtime.cleanup()
if failures:raise SystemExit('\n'.join(failures))
if phase!='done':raise SystemExit('Browser test did not finish')
