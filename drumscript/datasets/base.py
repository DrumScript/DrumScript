from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass
class BenchmarkItem:
    """One audio file plus its per-instrument reference onsets."""

    track_id: str
    audio_path: Path
    references: dict[str, np.ndarray]  # instrument code → onset times (sec)
    bucket: str = "all"  # subset / split label for grouped summaries
    extra: dict = field(default_factory=dict)  # dataset-specific id columns
