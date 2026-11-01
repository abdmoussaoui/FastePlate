from dataclasses import dataclass, field
import numpy as np
@dataclass
class Token:
    box: list
    text: str
    confidence: float
@dataclass
class Plate:
    bbox: tuple
    detection_confidence: float
    crop: np.ndarray
    raw_text: str
    normalized_text: str
    ocr_confidence: float | None
    tokens: list[Token] = field(default_factory=list)
    corrected_text: str | None = None
    warning: str = ''
@dataclass
class Result:
    source: str
    annotated: np.ndarray
    plates: list[Plate]
    seconds: float
    initialization_seconds: float
