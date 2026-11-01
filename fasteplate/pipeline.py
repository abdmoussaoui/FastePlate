from time import perf_counter
import cv2
from .config import Config
from .detection import Detector, read_image
from .ocr import EasyOCREngine
from .preprocessing import prepare
from .formatting import physical_order,normalize,review_warning
from .results import Plate,Result

class Pipeline:
    def __init__(self,config=None):
        self.config=config or Config()
        self.detector=None
        self.ocr=None
    def initialize(self):
        start=perf_counter()
        import torch
        torch.set_num_threads(self.config.threads)
        if self.detector is None: self.detector=Detector(self.config)
        if self.ocr is None: self.ocr=EasyOCREngine(self.config.device)
        return perf_counter()-start
    def run(self,path,mode=None,confidence=None,progress=lambda text:None):
        progress('Chargement des modèles…')
        initialization=self.initialize()
        start=perf_counter()
        image=read_image(path); annotated=image.copy(); h,w=image.shape[:2]
        progress('Détection des plaques…')
        boxes=self.detector.detect(image,self.config.confidence if confidence is None else confidence)
        plates=[]
        for index,box in enumerate(boxes):
            x1,y1,x2,y2=box.xyxy[0].tolist()
            x1,y1=max(0,int(x1)),max(0,int(y1)); x2,y2=min(w,int(x2+.999)),min(h,int(y2+.999))
            if x2<=x1 or y2<=y1: continue
            crop=image[y1:y2,x1:x2].copy()
            progress(f'OCR de la plaque {index+1}/{len(boxes)}…')
            tokens=self.ocr.read(prepare(crop,mode or self.config.preprocessing))
            text=physical_order(tokens)
            total=sum(max(1,len(t.text)) for t in tokens)
            score=sum(t.confidence*max(1,len(t.text)) for t in tokens)/total if total else None
            plates.append(Plate((x1,y1,x2,y2),float(box.conf[0]),crop,text,normalize(text),score,tokens,warning=review_warning(text,score)))
            cv2.rectangle(annotated,(x1,y1),(x2,y2),(85,180,95),2)
            cv2.putText(annotated,f'{len(plates)} | {float(box.conf[0]):.0%}',(x1,max(16,y1-7)),cv2.FONT_HERSHEY_SIMPLEX,.55,(85,180,95),2)
        return Result(str(path),annotated,plates,perf_counter()-start,initialization)
