"""Evaluate local weights on labelled YOLO images, without changing data.yaml."""
import argparse,json,time,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import torch,psutil
from fasteplate.config import Config,ROOT
from fasteplate.detection import Detector,read_image

def iou(a,b):
    area=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    return area/max(1e-9,(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-area)

def evaluate(weights,split,limit):
    start=time.perf_counter(); detector=Detector(Config(weights=weights)); loading=time.perf_counter()-start
    paths=sorted((split/'images').glob('*')); paths=paths[:limit] if limit else paths
    if not paths: raise ValueError('No images found in the supplied dataset split.')
    tp=fp=fn=0; elapsed=0; measured=0; missing=0; peak=0
    for path in paths:
        annotation=split/'labels'/(path.stem+'.txt')
        if not annotation.is_file(): missing+=1; continue
        image=read_image(path); h,w=image.shape[:2]; truth=[]
        for line in annotation.read_text().splitlines():
            if not line.strip(): continue
            cls,x,y,bw,bh=map(float,line.split())
            if cls==0: truth.append([(x-bw/2)*w,(y-bh/2)*h,(x+bw/2)*w,(y+bh/2)*h])
        start=time.perf_counter(); boxes=detector.detect(image,.35); elapsed+=time.perf_counter()-start; used=set()
        for box in sorted(boxes,key=lambda b:float(b.conf[0]),reverse=True):
            a=box.xyxy[0].tolist()
            scores=[(iou(a,b),j) for j,b in enumerate(truth) if j not in used]
            score,j=max(scores,default=(0,-1))
            if score>=.5: tp+=1; used.add(j)
            else: fp+=1
        fn+=len(truth)-len(used); measured+=1
        peak=max(peak,psutil.Process().memory_info().rss/1024**2)
    return dict(weights=str(weights),split=str(split),images=measured,missing_annotations=missing,confidence=.35,nms_iou=.45,iou=.5,tp=tp,fp=fp,fn=fn,precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else None,model_load_seconds=loading,inference_seconds=elapsed,mean_inference_seconds=elapsed/measured if measured else None,peak_sampled_rss_mb=peak)

if __name__=='__main__':
    p=argparse.ArgumentParser(description='Evaluate supplied YOLO weights on an external annotated dataset.')
    p.add_argument('--dataset',type=pathlib.Path,required=True,help='Dataset root containing test/images and test/labels (or valid).')
    p.add_argument('--weights',type=pathlib.Path,nargs='+',default=[ROOT/'best.pt'])
    p.add_argument('--limit',type=int,default=0)
    p.add_argument('--split',default='test',choices=['test','valid'])
    p.add_argument('--output',type=pathlib.Path,default=ROOT/'evaluation/detection_latest.json')
    args=p.parse_args()
    split=args.dataset.resolve()/args.split
    if args.limit<0: p.error('--limit must be zero or positive')
    if not (split/'images').is_dir() or not (split/'labels').is_dir():
        p.error('Dataset must contain '+args.split+'/images and '+args.split+'/labels. The application does not bundle the training dataset.')
    for weights in args.weights:
        if not weights.is_file(): p.error('Weights not found: '+str(weights))
    torch.set_num_threads(2)
    results=[]
    for weights in args.weights:
        results.append(evaluate(weights.resolve(),split,args.limit))
        print(json.dumps(results[-1]),flush=True)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(results,indent=2),encoding='utf-8')
