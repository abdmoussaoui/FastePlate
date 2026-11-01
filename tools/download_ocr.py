"""Explicit network-enabled model preparation, separate from application startup."""
import easyocr
if __name__ == '__main__':
    easyocr.Reader(['ar','en'],gpu=False,verbose=True)
    print('Modèles OCR prêts.')
