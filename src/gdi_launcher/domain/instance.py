from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Instance:
    name: str
    path: Path
    has_geode: bool = False

