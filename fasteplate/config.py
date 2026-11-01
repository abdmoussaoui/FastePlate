from dataclasses import dataclass
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
@dataclass(frozen=True)
class Config:
    weights: Path = ROOT / 'best.pt'
    device: str = 'cpu'
    confidence: float = .35
    preprocessing: str = 'color'
    threads: int = 2
