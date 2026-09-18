from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Iterator
from pathlib import Path

import numpy as np

from drumscript.datasets.base import BenchmarkItem

logger = logging.getLogger(__name__)

DATASET_NAME = "mdb"

# ─────────────────────────────────────────────────────────────────────────────
# TAXONOMY MAPPING  (MDB-Drums subclass label → DrumScript instrument label)
#
# Principle (per project decision): a label maps to a DrumScript notation ONLY
# if there is a direct, unambiguous equivalent. Anything without a direct
# DrumScript notation is EXCLUDED from evaluation — never lumped into a nearby
# class. DrumScript is a transcription engine; china ≠ crash, splash ≠ crash,
# side-stick ≠ snare. Excluded reference events are dropped entirely (they count
# as neither hits nor false positives), which is the standard way to benchmark a
# model against classes it cannot produce.
#
# DrumScript output vocabulary (from drum_classifier/classify.py):
#   kick, snare, low_tom, mid_tom, high_tom,
#   hi_hat_closed, hi_hat_open, crash, ride
# ─────────────────────────────────────────────────────────────────────────────

#: MDB-Drums *subclass* code → DrumScript label. Only directly-mappable codes
#: appear here; everything else is excluded (see EXCLUDED_CODES below).
MDB_SUBCLASS_TO_DRUMSCRIPT: dict[str, str] = {
    # --- Kick ---
    "KD": "kick",
    # --- Snare (all snare articulations are still the snare drum) ---
    "SD": "snare",  # plain snare
    "SDG": "snare",  # ghost note
    "SDB": "snare",  # brush
    "SDF": "snare",  # flam
    "SDD": "snare",  # drag
    # --- Hi-hat ---
    "CHH": "hi_hat_closed",  # closed hi-hat
    "PHH": "hi_hat_closed",  # pedal hi-hat (closed sound)
    "OHH": "hi_hat_open",  # open hi-hat
    # --- Ride ---
    "RDC": "ride",  # ride cymbal
    "RDB": "ride",  # ride bell
    # --- Crash ---
    "CRC": "crash",  # crash cymbal
    # --- Toms (direct 1:1 with DrumScript's three tom classes) ---
    "LFT": "low_tom",  # low floor tom
    "MHT": "mid_tom",  # mid/high tom
    "HFT": "high_tom",  # high floor tom
}

#: Codes deliberately excluded — no direct DrumScript notation exists, so they
#: are dropped from evaluation rather than mapped to an approximate class.
#:   SDNS = snare, snares-off (sounds tom-like; not a DrumScript class)
#:   CHC  = china cymbal   (distinct notation ≠ crash)
#:   SPC  = splash cymbal  (distinct notation ≠ crash)
#:   SST  = side/cross-stick (distinct notation ≠ snare)
#:   TMB  = tambourine     (auxiliary percussion)
#:   HIT  = generic/ambiguous hit
#:   OT   = "other" (class-level catch-all)
EXCLUDED_CODES: frozenset[str] = frozenset({"SDNS", "CHC", "SPC", "SST", "TMB", "HIT", "OT"})

#: DrumScript target classes this dataset can score. Each maps to itself so the
#: runner's evaluate_per_instrument (code → DrumScript labels) works unchanged.
CODE_TO_DRUMSCRIPT: dict[str, list[str]] = {
    "kick": ["kick"],
    "snare": ["snare"],
    "hi_hat_closed": ["hi_hat_closed"],
    "hi_hat_open": ["hi_hat_open"],
    "ride": ["ride"],
    "crash": ["crash"],
    "low_tom": ["low_tom"],
    "mid_tom": ["mid_tom"],
    "high_tom": ["high_tom"],
}

#: Instrument codes this dataset reports, in output/CSV column order.
#: (Same keys as CODE_TO_DRUMSCRIPT — the DrumScript classes MDB can score.)
INSTRUMENT_CODES: list[str] = [
    "kick",
    "snare",
    "hi_hat_closed",
    "hi_hat_open",
    "low_tom",
    "mid_tom",
    "high_tom",
    "crash",
    "ride",
]


# ── runner protocol ──────────────────────────────────────────────────────────


def add_cli_args(parser: argparse.ArgumentParser) -> None:
    """Add MDB-Drums-specific command-line arguments to a benchmark parser."""
    parser.add_argument(
        "--root",
        required=True,
        help='Path to extracted "MDB Drums/" directory (contains audio/ and annotations/)',
    )
    parser.add_argument(
        "--audio",
        default="drum_only",
        choices=("drum_only", "full_mix"),
        help="Which audio to transcribe (default: drum_only)",
    )


def iter_items(args: argparse.Namespace) -> Iterator[BenchmarkItem]:
    """Yield benchmark items from an extracted MDB-Drums directory."""
    root = Path(args.root)
    if not root.is_dir():
        sys.exit(f"[ERROR] MDB dataset directory not found: {root}")

    audio_dir = root / "audio" / args.audio
    ann_dir = root / "annotations" / "subclass"
    if not audio_dir.is_dir():
        sys.exit(f"[ERROR] Audio directory not found: {audio_dir}")
    if not ann_dir.is_dir():
        sys.exit(f"[ERROR] Subclass annotation directory not found: {ann_dir}")

    audio_files = sorted(audio_dir.glob("*.wav"))
    if not audio_files:
        sys.exit(f"[ERROR] No .wav files found in {audio_dir}")

    for audio_path in audio_files:
        ann_path = annotation_for_audio(audio_path, ann_dir)
        if ann_path is None:
            logger.warning("No subclass annotation for %s; skipping", audio_path.name)
            continue
        references = reference_onsets(ann_path)
        yield BenchmarkItem(
            track_id=audio_path.name,
            audio_path=audio_path,
            references=references,
            bucket=genre_of(audio_path),
        )


# ── file discovery ───────────────────────────────────────────────────────────


def track_stem(name: str) -> str:
    """Strip MDB audio/annotation suffixes to the shared track stem.

    e.g. ``MusicDelta_Rock_MIX.wav``        → ``MusicDelta_Rock``
         ``MusicDelta_Rock_Drum.wav``       → ``MusicDelta_Rock``
         ``MusicDelta_Rock_subclass.txt``   → ``MusicDelta_Rock``
    """
    stem = Path(name).stem
    for suffix in ("_subclass", "_class", "_beats", "_MIX", "_Drum", "_drum_only"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return stem


def annotation_for_audio(audio_path: Path, ann_dir: Path) -> Path | None:
    """Find the subclass annotation whose track stem matches ``audio_path``."""
    want = track_stem(audio_path.name)
    for ann_path in ann_dir.glob("*.txt"):
        if track_stem(ann_path.name) == want:
            return ann_path
    return None


def genre_of(audio_path: Path) -> str:
    """Best-effort genre/bucket label from an MDB MedleyDB track name.

    MDB tracks look like ``MusicDelta_<Genre>_MIX.wav``; use ``<Genre>`` as the
    bucket so summaries group by musical style.
    """
    stem = track_stem(audio_path.name)
    if stem.startswith("MusicDelta_"):
        return stem[len("MusicDelta_") :]
    return stem


# ── annotation parsing ───────────────────────────────────────────────────────


def reference_onsets(annotation_path: Path) -> dict[str, np.ndarray]:
    """Parse an MDB-Drums subclass annotation into per-DrumScript-class onsets.

    File format: whitespace-separated ``<onset_seconds> <SUBCLASS_CODE>`` per
    line. Codes without a direct DrumScript equivalent are excluded. Returns
    ``{drumscript_label: sorted onset array in seconds}``.
    """
    by_label: dict[str, list[float]] = {}
    seen_unknown: set[str] = set()

    try:
        text = annotation_path.read_text()
    except OSError as exc:  # pragma: no cover - unreadable file
        logger.warning("Could not read %s: %s", annotation_path.name, exc)
        return {}

    for raw_line in text.splitlines():
        parts = raw_line.split()
        if len(parts) < 2:
            continue
        time_str, code = parts[0], parts[1].strip().upper()

        try:
            onset = float(time_str)
        except ValueError:
            continue

        if code in EXCLUDED_CODES:
            continue

        label = MDB_SUBCLASS_TO_DRUMSCRIPT.get(code)
        if label is None:
            # Unknown code (not mapped and not explicitly excluded) — skip, but
            # warn once so new/renamed labels are noticed rather than silently
            # dropped.
            if code not in seen_unknown:
                seen_unknown.add(code)
                logger.warning(
                    "Unmapped MDB code %r in %s — excluded from evaluation",
                    code,
                    annotation_path.name,
                )
            continue

        by_label.setdefault(label, []).append(onset)

    return {label: np.array(sorted(times)) for label, times in by_label.items()}
