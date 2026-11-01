import csv,json
from pathlib import Path
from .detection import save_image

def export_result(result,directory):
    # A new directory avoids overwriting any previous export or original image.
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=False)
    save_image(directory/'detection.png',result.annotated)
    rows=[]
    for i,p in enumerate(result.plates,1):
        save_image(directory/f'plate_{i:02}.png',p.crop)
        rows.append(dict(source=result.source,plate=i,bbox=list(p.bbox),detection_confidence=p.detection_confidence,raw_ocr=p.raw_text,normalized_ocr=p.normalized_text,corrected_text=p.corrected_text,ocr_confidence=p.ocr_confidence,processing_seconds=result.seconds,initialization_seconds=result.initialization_seconds,warning=p.warning,tokens=[dict(box=t.box,text=t.text,confidence=t.confidence) for t in p.tokens]))
    keys=['source','plate','bbox','detection_confidence','raw_ocr','normalized_ocr','corrected_text','ocr_confidence','processing_seconds','initialization_seconds','warning']
    with (directory/'results.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore'); writer.writeheader(); writer.writerows(rows)
    (directory/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    (directory/'results.txt').write_text('\n\n'.join(f"Plaque {row['plate']}\nOCR : {row['raw_ocr']}\nCorrection : {row['corrected_text'] if row['corrected_text'] is not None else '(aucune)'}" for row in rows),encoding='utf-8')
    return directory
