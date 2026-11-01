"""Launch the browser-based FastePlate application."""
import atexit
import shutil
try:
    from fasteplate.web import create_app
except ImportError as exc:
    raise SystemExit(f'Missing dependency: {exc}\nInstall: python -m pip install -r requirements.txt')

if __name__=='__main__':
    app=create_app()
    service=app.extensions['analysis_service']
    def cleanup():
        service.shutdown()
        shutil.rmtree(service.directory,ignore_errors=True)
    atexit.register(cleanup)
    print('\nFastePlate web app: http://127.0.0.1:5000\nPress Ctrl+C to stop.\n')
    app.run(host='127.0.0.1',port=5000,debug=False,threaded=True,use_reloader=False)
