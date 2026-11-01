from .results import Token
class EasyOCREngine:
    def __init__(self, device='cpu', languages=None):
        import easyocr
        try:
            self.reader=easyocr.Reader(languages or ['ar','en'],gpu=False if device=='cpu' else device,download_enabled=False,verbose=False)
        except FileNotFoundError as exc:
            raise RuntimeError('Modèles EasyOCR absents. Exécuter : python tools/download_ocr.py (connexion requise).') from exc
    def read(self,image):
        return [Token([[float(x),float(y)] for x,y in box],str(text),float(score)) for box,text,score in self.reader.readtext(image,detail=1,paragraph=False,workers=0)]
