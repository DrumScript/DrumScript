from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Iterator
from pathlib import Path

import numpy as np

from drumscript.datasets.base import BenchmarkItem

logger = logging.getLogger(__name__)

# DATASET_NAME = "enst"
DATASET_NAME = "ENST-drums-public"

# ─────────────────────────────────────────────────────────────────────────────
# TAXONOMY MAPPING  (ENST-Drums label → DrumScript instrument label)
#
# Same principle as the MDB adapter: a label maps to a DrumScript notation ONLY
# if there is a direct, unambiguous equivalent. Anything without a direct
# DrumScript notation is EXCLUDED from evaluation #  never lumped into a nearby
# class. Excluded reference events are dropped entirely (they count as neither
# hits nor false positives).
#
# ENST label vocabulary (Gillet & Richard, ISMIR 2006, Table 2):
#   bd, sd, sweep, sticks, rs, cs, chh, ohh, cb, c,
#   lmt, mt, mtr, lt, ltr, lft, rc, ch, cr, spl
#
# ENST annotation files may append an instance number to a label (e.g. a
# second crash). The number identifies WHICH physical cymbal/drum, not a
# different class, so it is stripped before lookup (see normalise_code).
#
# DrumScript output vocabulary (from drum_classifier/classify.py):
## defined in drumscript/notation_generator/constants.py
## DRUM_NOTATION_MAPPING
#   kick, snare, low_tom, mid_tom, high_tom,
#   hi_hat_closed, hi_hat_open, crash, ride
# ─────────────────────────────────────────────────────────────────────────────

# ENST label → DrumScript label. Only directly-mappable labels appear here;
# everything else is excluded (see EXCLUDED_CODES below).
ENST_CODE_TO_DRUMSCRIPT: dict[str, str] = {
    # --- Kick ---
    "bd": "kick",  # bass drum
    # --- Snare ---
    "sd": "snare",  # snare drum
    # --- Hi-hat ---
    "chh": "hi_hat_closed",  # closed hi-hat
    "ohh": "hi_hat_open",  # open hi-hat
    # --- Ride ---
    "rc": "ride",  # ride cymbal
    # --- Crash ---
    "cr": "crash",  # crash cymbal
    # --- Toms: PENDING DECISION -- confirm against label counts before enabling ---
    # (left unmapped AND unexcluded on purpose, so they log a warning and stay visible)
    # "lft": "low_tom",  # lowest tom
    # "lt": "low_tom",  # low tom
    # "lmt": "mid_tom",  # low-mid tom
    # "mt": "mid_tom",  # mid tom
}

# Labels deliberately excluded #  no direct DrumScript notation exists, so they
# are dropped from evaluation rather than mapped to an approximate class.
EXCLUDED_CODES: frozenset[str] = frozenset(
    {
        "sweep",  # brush sweep (not an onset-style hit)
        "sticks",  # sticks hit together (not a drum)
        "rs",  # rim shot
        "cs",  # cross stick
        "cb",  # cowbell
        "c",  # other cymbals
        "ch",  # chinese ride cymbal
        "spl",  # splash cymbal
        "mtr",  # mid tom, hit on the rim
        "ltr",  # low tom, hit on the rim
    }
)

# DrumScript target classes this dataset can score. Each maps to itself so the
# runner's evaluate_per_instrument (code → DrumScript labels) works unchanged.
DRUMSCRIPT_DICT: dict[str, list[str]] = {  # DICTIONARY OF CURRENT DRUMSCRIPT COVERAGE
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

# Instrument codes this dataset reports, in output/CSV column order.
# Same as MDB, so ENST and MDB CSVs line up column-for-column.
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

#: Audio folders under each drummer_N/audio/ that hold a full-kit drum mix.
AUDIO_CHOICES: tuple[str, ...] = ("wet_mix", "dry_mix")

#: Recording types, taken from the second token of each ENST filename
#: (e.g. ``001_hits_snare-drum_sticks_x6.wav`` → ``hits``).
SUBSETS: tuple[str, ...] = ("hits", "phrase", "solo", "minus-one")


# ── runner protocol ──────────────────────────────────────────────────────────


def add_cli_args(parser: argparse.ArgumentParser) -> None:
    """Add ENST-Drums-specific command-line arguments to a benchmark parser."""
    parser.add_argument(
        "--root",
        required=True,
        help="Path to extracted ENST directory (contains drummer_1/, drummer_2/, drummer_3/)",
    )
    parser.add_argument(
        "--audio",
        default="wet_mix",
        choices=AUDIO_CHOICES,
        help="Which drum mix to transcribe (default: wet_mix)",
    )
    parser.add_argument("--subset", default=None, choices=SUBSETS, help="Filter by recording type")


def iter_items(args: argparse.Namespace) -> Iterator[BenchmarkItem]:
    """Yield benchmark items from an extracted ENST-Drums directory."""
    root = Path(args.root)
    if not root.is_dir():
        sys.exit(f"[ERROR] ENST dataset directory not found: {root}")

    drummer_dirs = sorted(p for p in root.glob("drummer_*") if p.is_dir())
    if not drummer_dirs:
        sys.exit(f"[ERROR] No drummer_* directories found in {root}")

    found_any = False
    for drummer_dir in drummer_dirs:
        audio_dir = drummer_dir / "audio" / args.audio
        ann_dir = drummer_dir / "annotation"
        if not audio_dir.is_dir():
            logger.warning("Audio directory not found: %s; skipping drummer", audio_dir)
            continue
        if not ann_dir.is_dir():
            logger.warning("Annotation directory not found: %s; skipping drummer", ann_dir)
            continue

        for audio_path in sorted(audio_dir.glob("*.wav")):
            subset = subset_of(audio_path)
            if args.subset and subset != args.subset:
                continue
            ann_path = ann_dir / f"{audio_path.stem}.txt"
            if not ann_path.is_file():
                logger.warning("No annotation for %s; skipping", audio_path.name)
                continue
            found_any = True
            yield BenchmarkItem(
                # Filenames repeat across drummers (e.g. 001_hits_... exists for each),
                # so the drummer is prefixed to keep track_id unique.
                track_id=f"{drummer_dir.name}_{audio_path.name}",
                audio_path=audio_path,
                references=reference_onsets(ann_path),
                bucket=subset,
            )

    if not found_any:
        sys.exit(f"[ERROR] No annotated .wav files found under {root}/drummer_*/audio/{args.audio}")


# ── file discovery ───────────────────────────────────────────────────────────


def subset_of(audio_path: Path) -> str:
    """Return the recording type (``hits``/``phrase``/``solo``/``minus-one``) from the filename."""
    parts = audio_path.stem.split("_")
    if len(parts) >= 2 and parts[1] in SUBSETS:
        return parts[1]
    return "Unknown"


# ── annotation parsing ───────────────────────────────────────────────────────


def normalise_code(raw_code: str) -> str:
    """Lower-case a label and strip any trailing instance number (e.g. ``cr2`` → ``cr``)."""
    return raw_code.strip().lower().rstrip("0123456789")


def reference_onsets(annotation_path: Path) -> dict[str, np.ndarray]:
    """Parse an ENST annotation into per-DrumScript-class onsets.

    File format: whitespace-separated ``<onset_seconds> <label>`` per line.
    ``splitlines()`` handles Unix, Windows and old-Mac line endings. Labels
    without a direct DrumScript equivalent are excluded. Returns
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
        time_str, raw_code = parts[0], parts[1]
        code = normalise_code(raw_code)

        try:
            onset = float(time_str)
        except ValueError:
            continue

        if code in EXCLUDED_CODES:
            continue

        label = ENST_CODE_TO_DRUMSCRIPT.get(code)
        if label is None:
            # Unknown label (not mapped and not explicitly excluded) #  skip, but
            # warn once per file so new/pending labels are noticed rather than
            # silently dropped. The raw label is logged so instance numbers show.
            if code not in seen_unknown:
                seen_unknown.add(code)
                logger.warning(
                    "Unmapped ENST label %r in %s #  excluded from evaluation",
                    raw_code,
                    annotation_path.name,
                )
            continue

        by_label.setdefault(label, []).append(onset)

    return {label: np.array(sorted(times)) for label, times in by_label.items()}
