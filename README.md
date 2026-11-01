# FastePlate

A web application for detecting Moroccan license plates and recognizing Arabic and Latin characters using YOLO and EasyOCR.

## Features

- Upload or drag and drop an image.
- Detect multiple plates and display their cropped images.
- View recognized text, confidence scores and processing time.
- Correct OCR results manually.
- Export annotated images, plate crops and CSV, TXT or JSON results.
- Run on CPU with a dark, responsive interface.

## Installation

Requirements: Python 3.10 and the included `best.pt` model at the project root.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
python tools/download_ocr.py
```

The OCR models are downloaded once during setup.

## Run

```powershell
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

## Usage

1. Upload an image and click **Analyze image**.
2. Select a detected plate to inspect its crop and recognized text.
3. Save a manual correction if needed.
4. Click **Export results** to download the results.

OCR can miss characters or confuse digits. Check the reading before exporting.

## Project structure

```text
app.py               Application entry point
best.pt              Trained YOLO detector
fasteplate/          Web interface and recognition pipeline
tools/               Setup and evaluation scripts
tests/               Automated tests
evaluation/          Evaluation results
experiments/legacy/  Original experiments
```

## Tests

```powershell
python -m unittest discover -s tests -v
python tools/smoke_web.py
```
