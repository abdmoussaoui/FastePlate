import json,time,pathlib,hashlib,argparse
import cv2,easyocr,torch,psutil
from ultralytics import YOLO
torch.set_num_threads(2)
r=pathlib.Path(__file__).resolve().parents[1]
report={'weights':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [r/'best.pt']},'runs':[]}
parser=argparse.ArgumentParser()
parser.add_argument('images',nargs='+',type=pathlib.Path,help='Images supplied by the user; no dataset is bundled.')
args=parser.parse_args()
images=args.images
for path in images:
 if not path.is_file(): parser.error('Image not found: '+str(path))
model=YOLO(r/'best.pt')
report['model']={'names':model.names,'architecture':str(model.model.yaml)}
for lang in [['en'],['ar','en']]:
 reader=easyocr.Reader(lang,gpu=False,download_enabled=False,verbose=False)
 for path in images:
  im=cv2.imread(str(path))
  if im is None: raise ValueError('Unreadable image: '+str(path))
  for box in model.predict(im,device='cpu',verbose=False)[0].boxes:
   x1,y1,x2,y2=map(int,box.xyxy[0].tolist()); crop=im[y1:y2,x1:x2]
   gray=cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY)
   legacy=cv2.threshold(cv2.createCLAHE(3,(8,8)).apply(gray),64,25,cv2.THRESH_BINARY_INV)[1]
   lab=cv2.cvtColor(cv2.bilateralFilter(crop,5,7,7),cv2.COLOR_BGR2LAB)
   lab[:,:,0]=cv2.createCLAHE(2,(8,4)).apply(lab[:,:,0])
   g=cv2.cvtColor(cv2.cvtColor(lab,cv2.COLOR_LAB2BGR),cv2.COLOR_BGR2GRAY)
   binary=cv2.threshold(g,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
   if (binary==255).sum()>(binary==0).sum(): binary=255-binary
   binary=cv2.morphologyEx(binary,cv2.MORPH_OPEN,(5,5))
   scale=max(1,min(4,96/crop.shape[0])); resized=cv2.resize(crop,None,fx=scale,fy=scale,interpolation=cv2.INTER_CUBIC)
   for name,img in [('main',legacy),('main2',binary),('raw',crop),('resized',resized)]:
    t=time.perf_counter(); tokens=reader.readtext(img)
    report['runs'].append(dict(image=path.name,languages=lang,approach=name,box=[x1,y1,x2,y2],detection_confidence=float(box.conf[0]),tokens=[dict(text=s,confidence=float(c)) for _,s,c in tokens],seconds=time.perf_counter()-t,rss_mb=psutil.Process().memory_info().rss/1024**2))
 del reader
(r/'evaluation/comparison_latest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('Saved comparison_latest.json')
