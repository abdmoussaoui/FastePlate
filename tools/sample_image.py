"""Find the single retained vehicle image for real-model regression checks."""
from fasteplate.config import ROOT

def sample_image():
    for image in sorted((ROOT/'tests/fixtures').glob('vehicle.*')):
        if image.suffix.lower() in {'.jpg','.jpeg','.png','.webp'}:
            return image
    raise FileNotFoundError('Missing regression fixture in tests/fixtures/. Supply a vehicle image there before running the smoke checks.')
