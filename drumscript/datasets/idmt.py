from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from pathlib import Path

import numpy as np

from drumscript.datasets.base import BenchmarkItem

DATASET_NAME = "idmt"

#: IDMT instrument codes → DrumScript label list. ``HH`` matches both open and
#: closed hi-hat.
CODE_TO_DRUMSCRIPT: dict[str, list[str]] = {
    "KD": ["kick"],
    "SD": ["snare"],
    "HH": ["hi_hat_closed", "hi_hat_open"],
}

#: Back-compat alias for callers that still import the old name.
IDMT_TO_DRUMSCRIPT = CODE_TO_DRUMSCRIPT

INSTRUMENT_CODES: tuple[str, ...] = tuple(CODE_TO_DRUMSCRIPT.keys())

#: Filename prefixes that identify the three IDMT subsets.
SUBSETS: tuple[str, ...] = ("RealDrum", "WaveDrum", "TechnoDrum")

#: GM MIDI pitch → IDMT code, used when annotations carry a ``<pitch>`` instead
#: of an ``<instrument>`` label.
GM_PITCH_TO_IDMT: dict[int, str] = {
    35: "KD", 36: "KD",
    37: "SD", 38: "SD", 40: "SD",
    42: "HH", 44: "HH", 46: "HH",
}


# ── runner protocol ──────────────────────────────────────────────────────────


def add_cli_args(parser: argparse.ArgumentParser) -> None:
    """Add IDMT-specific command-line arguments to a benchmark parser."""
    parser.add_argument("--root", required=True, help="Path to extracted IDMT-SMT-DRUMS-V2/")
    parser.add_argument("--subset", default=None, help=f"Filter by subset: {', '.join(SUBSETS)}")


def iter_items(args: argparse.Namespace) -> Iterator[BenchmarkItem]:
    """Yield benchmark items from an extracted IDMT-SMT-Drums directory."""
    root = Path(args.root)
    if not root.is_dir():
        sys.exit(f"[ERROR] IDMT dataset directory not found: {root}")

    mix_files = find_mix_files(root, args.subset)
    if not mix_files:
        sys.exit(f"[ERROR] No #MIX.wav files found in {root}")

    for mix_path in mix_files:
        references = reference_onsets_for_file(mix_path)
        yield BenchmarkItem(
            track_id=mix_path.name,
            audio_path=mix_path,
            references=references,
            bucket=subset_of(mix_path),
        )


# ── file discovery ───────────────────────────────────────────────────────────


def find_mix_files(dataset_dir: Path, subset: str | None = None) -> list[Path]:
    """Return all ``*#MIX.wav`` files under ``dataset_dir``, sorted."""
    mixes = sorted(dataset_dir.rglob("*#MIX.wav"))
    if subset:
        needle = subset.lower()
        mixes = [p for p in mixes if needle in p.name.lower()]
    return mixes


def find_dataset_root(path: Path) -> Path:
    """Walk up from ``path`` to the first dir containing IDMT annotation dirs."""
    for parent in [path, *path.parents]:
        if (parent / "annotation_xml").is_dir() or (parent / "annotation_svl").is_dir():
            return parent
    return path


def subset_of(mix_path: Path) -> str:
    """Infer subset name (``RealDrum``/``WaveDrum``/``TechnoDrum``) from filename."""
    for name in SUBSETS:
        if mix_path.name.startswith(name):
            return name
    return "Unknown"


def annotation_dirs_for(mix_path: Path) -> list[Path]:
    """Return candidate annotation directories for an IDMT mix file."""
    root = find_dataset_root(mix_path)
    candidates = [root / "annotation_xml", mix_path.parent, root / "annotation_svl"]
    return [p for p in candidates if p.is_dir()]


def get_annotation_path(mix_path: Path, instrument_code: str) -> Path | None:
    """Find the annotation file matching ``mix_path`` for one instrument code."""
    mix_stem = mix_path.stem
    base_stem = mix_stem.replace("#MIX", "")
    patterns = [
        f"{mix_stem}.xml",
        f"{base_stem}#{instrument_code}*.xml",
        f"{base_stem}*.xml",
        f"{mix_stem}.svl",
        f"{base_stem}#{instrument_code}*.svl",
        f"{base_stem}*.svl",
    ]
    for ann_dir in annotation_dirs_for(mix_path):
        for pattern in patterns:
            matches = sorted(ann_dir.rglob(pattern))
            if matches:
                return matches[0]
    return None


# ── annotation parsing ───────────────────────────────────────────────────────


def parse_annotation(
    annotation_path: Path,
    instrument_code: str | None = None,
    sr: int = 44100,
) -> np.ndarray:
    """Parse an IDMT XML or Sonic Visualiser SVL annotation file.

    Returns a sorted array of onset times in seconds. If ``instrument_code`` is
    given, only events for that drum are kept.
    """
    try:
        tree = ET.parse(annotation_path)
    except ET.ParseError as e:  # pragma: no cover - corrupt file
        print(f"  [WARN] Could not parse {annotation_path.name}: {e}")
        return np.array([])

    root = tree.getroot()
    xml_events = _parse_xml_events(root, instrument_code)
    if xml_events is not None:
        return xml_events

    onsets: list[float] = []
    for elem in root.iter():
        label = _element_label(elem)
        if instrument_code and label and instrument_code not in label:
            continue
        time_value = _element_time_seconds(elem, sr)
        if time_value is not None:
            onsets.append(time_value)

    return np.array(sorted(onsets)) if onsets else np.array([])


def reference_onsets_for_file(mix_path: Path) -> dict[str, np.ndarray]:
    """Return ``{instrument_code: onset_array}`` for ``mix_path``."""
    references: dict[str, np.ndarray] = {}
    for code in INSTRUMENT_CODES:
        ann_path = get_annotation_path(mix_path, code)
        if ann_path is None:
            continue
        onsets = parse_annotation(ann_path, code)
        if len(onsets) > 0:
            references[code] = onsets
    return references


# ── internal XML helpers ─────────────────────────────────────────────────────


def _parse_xml_events(root: ET.Element, instrument_code: str | None) -> np.ndarray | None:
    events = list(root.iter("event"))
    if not events:
        return None

    onsets: list[float] = []
    for event in events:
        code = _idmt_code_for_event(event)
        if instrument_code and code != instrument_code:
            continue
        onset_text = _child_text(event, "onsetSec")
        if onset_text is None:
            continue
        try:
            onsets.append(float(onset_text))
        except ValueError:
            continue
    return np.array(sorted(onsets)) if onsets else np.array([])


def _idmt_code_for_event(event: ET.Element) -> str | None:
    instrument = (_child_text(event, "instrument") or "").strip().upper()
    if instrument in INSTRUMENT_CODES:
        return instrument

    pitch_text = _child_text(event, "pitch")
    if pitch_text is None:
        return None
    try:
        pitch = int(float(pitch_text))
    except ValueError:
        return None
    return GM_PITCH_TO_IDMT.get(pitch)


def _child_text(elem: ET.Element, tag: str) -> str | None:
    child = elem.find(tag)
    return child.text if child is not None and child.text is not None else None


def _element_label(elem: ET.Element) -> str:
    label = elem.attrib.get("label")
    if label:
        return label
    text = (elem.text or "").strip()
    return text


def _element_time_seconds(elem: ET.Element, sr: int) -> float | None:
    frame = elem.attrib.get("frame")
    if frame is not None:
        try:
            return float(frame) / sr
        except ValueError:
            return None
    for attr in ("time", "onset", "onsetSec"):
        value = elem.attrib.get(attr)
        if value is not None:
            try:
                return float(value)
            except ValueError:
                continue
    return None
