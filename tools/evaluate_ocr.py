"""OCR metric evaluator for manually transcribed plate crops (no inferred labels).
Manifest: [{"image":"path/to/crop.png", "text":"90743 ب 26"}].
Paths resolve relative to the manifest. Never include uncertain transcriptions.
"""
import argparse,json,pathlib,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from fasteplate.ocr import EasyOCREngine
from fasteplate.formatting import normalize,physical_order
from fasteplate.detection import read_image
from fasteplate.preprocessing import prepare

def distance(a,b):
 row=list(range(len(b)+1))
 for i,ca in enumerate(a,1):
  nxt=[i]
  for j,cb in enumerate(b,1): nxt.append(min(nxt[-1]+1,row[j]+1,row[j-1]+(ca!=cb)))
  row=nxt
 return row[-1]

def canonical(text): return ''.join(normalize(text).split())

if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('manifest',type=pathlib.Path); p.add_argument('--mode',default='color'); p.add_argument('--language',choices=['ar','en'],default='ar'); p.add_argument('--output',type=pathlib.Path,default=pathlib.Path('evaluation/ocr_metrics.json')); args=p.parse_args()
 import torch
 torch.set_num_threads(2)
 engine=EasyOCREngine(languages=['ar','en'] if args.language=='ar' else ['en'])
 rows=[]; edits=characters=exact=ar_edits=ar_chars=0
 for sample in json.loads(args.manifest.read_text(encoding='utf-8-sig')):
  image=read_image(args.manifest.parent/sample['image']); start=time.perf_counter()
  text=physical_order(engine.read(prepare(image,args.mode))); elapsed=time.perf_counter()-start
  expected=canonical(sample['text']); actual=canonical(text); error=distance(expected,actual)
  # Arabic letter subsequence metric is diagnostic, separate from full-string CER.
  arabic=lambda s: ''.join(c for c in s if '\u0621'<=c<='\u064a')
  a,b=arabic(expected),arabic(actual)
  ar_edits+=distance(a,b); ar_chars+=len(a)
  edits+=error; characters+=len(expected); exact+=expected==actual
  rows.append(dict(image=sample['image'],expected=sample['text'],actual=text,edit_distance=error,seconds=elapsed))
 report=dict(language=args.language,mode=args.mode,samples=len(rows),character_error_rate=edits/characters if characters else None,character_accuracy=max(0,1-edits/characters) if characters else None,exact_accuracy=exact/len(rows) if rows else None,arabic_letter_error_rate=ar_edits/ar_chars if ar_chars else None,rows=rows)
 args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=True))
