"""Investigate numeric re-recognition with the SAME Arabic model; no extra model."""
import pathlib,json,cv2,easyocr,torch
root=pathlib.Path(__file__).resolve().parents[1]
torch.set_num_threads(2)
reader=easyocr.Reader(['ar','en'],gpu=False,download_enabled=False,verbose=False)
results=[]
for file in [root/'evaluation/verified_plate.png']:
 image=cv2.imread(str(file)); h,w=image.shape[:2]
 scale=max(1,min(4,96/h)); image=cv2.resize(image,None,fx=scale,fy=scale)
 for box,text,score in reader.readtext(image):
  if any(c.isdigit() for c in text) and all(c.isdigit() or c.isspace() for c in text):
   x1=max(0,int(min(p[0] for p in box))-3); y1=max(0,int(min(p[1] for p in box))-3)
   x2=min(image.shape[1],int(max(p[0] for p in box))+4); y2=min(image.shape[0],int(max(p[1] for p in box))+4)
   crop=cv2.cvtColor(image[y1:y2,x1:x2],cv2.COLOR_BGR2GRAY)
   restricted=reader.recognize(crop,allowlist='0123456789٠١٢٣٤٥٦٧٨٩',detail=1)
   results.append(dict(image=file.name,original=text,restricted=[t[1] for t in restricted]))
(root/'evaluation/numeric_experiment_latest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=True))
