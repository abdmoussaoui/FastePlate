# Preserved experiments

`legacy/` contains the original detection/OCR experiments, utilities, segmentation, exploratory scripts and SORT tracker. These files are not imported by the web app. The embedded Roboflow credential was removed from comments in the three affected scripts; examples now reference the `ROBOFLOW_API_KEY` environment variable.

Historical scripts contain hard-coded sample, dataset and model paths. The full dataset, old sample folder and unused COCO weights were removed during cleanup, so supply appropriate inputs/models before attempting to run those experiments. The maintained app starts with `python app.py` from the project root and needs only `best.pt` plus EasyOCR models.

For maintained comparisons, use `tools/probe.py` with explicit image paths, or `tools/evaluate_detection.py --dataset PATH` with externally stored annotated images. New outputs use `_latest.json` filenames and do not replace historical measurements. Existing trained checkpoints remain locally in `runs/`, excluded from GitHub by `.gitignore`.
