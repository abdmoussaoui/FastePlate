import cv2
import numpy as np

def read_image(path):
    try:
        image=cv2.imdecode(np.fromfile(str(path),dtype=np.uint8),cv2.IMREAD_COLOR)
    except OSError as exc:
        raise ValueError('Image inaccessible : '+str(path)) from exc
    if image is None:
        raise ValueError('Format illisible ou fichier endommagé : '+str(path))
    return image

def save_image(path,image):
    from pathlib import Path
    suffix=Path(path).suffix.lower()
    if suffix not in ['.png','.jpg','.jpeg','.bmp','.webp']:
        raise ValueError('Utiliser une extension PNG, JPG, BMP ou WebP.')
    ok,encoded=cv2.imencode(suffix,image)
    if not ok: raise OSError('Impossible d’encoder l’image.')
    encoded.tofile(str(path))

class Detector:
    def __init__(self,config):
        if not config.weights.is_file():
            raise FileNotFoundError('Poids YOLO introuvables : '+str(config.weights))
        from ultralytics import YOLO
        self.model=YOLO(str(config.weights))
        self.config=config
    def detect(self,image,confidence):
        return self.model.predict(image,device=self.config.device,conf=confidence,iou=.45,imgsz=640,verbose=False)[0].boxes
