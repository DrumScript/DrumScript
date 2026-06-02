#!/usr/bin/env python3
"""Run a DrumScript benchmark on one dataset.

Usage::

    python benchmarks/run.py idmt --root /path/to/IDMT-SMT-DRUMS-V2

Global flags (``--output``, ``--run-name``, ``--limit``) go before the dataset
name. See ``benchmarks/README.md`` for per-dataset preparation and required
layout. Only ``idmt`` is currently verified end-to-end.
"""

from __future__ import annotations

import argparse
import csv
import json
import shlex
import subprocess
import sys
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import ModuleType

import mir_eval
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from drumscript.audio_processor.audio_loader import load_audio, normalise_audio
from drumscript.audio_processor.onset_detector import detect_onsets
from drumscript.datasets import idmt as idmt_adapter
from drumscript.datasets.base import BenchmarkItem
from drumscript.drum_classifier.classify import classify_events
from drumscript.notation_generator.constants import SAMPLE_RATE

ONSET_WINDOW = 0.050  # 50 ms tolerance, standard in ADT literature.
ADAPTERS: dict[str, ModuleType] = {
    idmt_adapter.DATASET_NAME: idmt_adapter,
}


# ── shared evaluation primitives ─────────────────────────────────────────────


def onset_metrics(reference: np.ndarray, estimated: np.ndarray) -> dict[str, float]:
    """Return named onset precision, recall, and F-measure metrics."""
    if len(estimated) == 0:
        return {"precision": 0.0, "recall": 0.0, "f_measure": 0.0}
    f_measure, precision, recall = mir_eval.onset.f_measure(
        reference, estimated, window=ONSET_WINDOW
    )
    return {"precision": precision, "recall": recall, "f_measure": f_measure}


def evaluate_per_instrument(
    predictions: Mapping[str, Sequence[float]],
    references: Mapping[str, np.ndarray],
    code_to_labels: Mapping[str, Sequence[str]],
) -> dict[str, dict]:
    """Evaluate predictions against reference onsets for each dataset code."""
    metrics: dict[str, dict] = {}
    for code, ref_onsets in references.items():
        est_times: list[float] = []
        for label in code_to_labels.get(code, ()):
            est_times.extend(predictions.get(label, []))
        est_onsets = np.array(sorted(est_times))

        onset_scores = onset_metrics(ref_onsets, est_onsets)
        metrics[code] = {
            "precision": onset_scores["precision"],
            "recall": onset_scores["recall"],
            "f_measure": onset_scores["f_measure"],
            "n_ref": len(ref_onsets),
            "n_est": len(est_onsets),
        }
    return metrics


def summarise(results: Iterable[dict]) -> dict:
    """Macro-average per-item metric dictionaries."""
    accum: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for file_res in results:
        for inst, metrics in file_res.items():
            for metric, value in metrics.items():
                accum[inst][metric].append(value)
    return {
        inst: {m: float(np.mean(values)) for m, values in metrics.items()}
        for inst, metrics in accum.items()
    }


def summarise_by_bucket(items: Sequence[BenchmarkItem], results: Sequence[dict]) -> dict[str, dict]:
    """Macro-average metrics grouped by each benchmark item's bucket."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item, result in zip(items, results, strict=True):
        if result:
            grouped[item.bucket].append(result)
    return {bucket: summarise(values) for bucket, values in grouped.items()}


def print_summary(title: str, summary: dict) -> None:
    """Print a compact metric table."""
    print(title)
    print(f"{'Instrument':<12} {'Precision':>10} {'Recall':>10} {'F-measure':>10}")
    print("-" * 44)
    for inst, metrics in summary.items():
        print(
            f"{inst:<12} {metrics['precision']:>10.3f} "
            f"{metrics['recall']:>10.3f} {metrics['f_measure']:>10.3f}"
        )


def fmt_optional(value) -> str:
    """Format optional numeric CSV values."""
    if value is None or value == "":
        return ""
    return f"{float(value):.4f}"


def write_metrics_csv(
    items: Sequence[BenchmarkItem],
    results: Sequence[dict | None],
    instrument_codes: Sequence[str],
    output_path: Path,
) -> None:
    """Write per-item benchmark metrics to a CSV file."""
    extra_cols = sorted({key for item in items for key in item.extra})
    with open(output_path, "w", newline="") as fh:
        writer = csv.writer(fh)
        header: list[str] = ["track", "bucket", *extra_cols]
        for code in instrument_codes:
            header += [f"{code}_P", f"{code}_R", f"{code}_F", f"{code}_n_ref", f"{code}_n_est"]
        writer.writerow(header)

        for item, metrics in zip(items, results, strict=True):
            if metrics is None:
                continue
            row: list = [item.track_id, item.bucket] + [item.extra.get(col, "") for col in extra_cols]
            for code in instrument_codes:
                m = metrics.get(code, {})
                row += [
                    fmt_optional(m.get("precision")),
                    fmt_optional(m.get("recall")),
                    fmt_optional(m.get("f_measure")),
                    m.get("n_ref", ""),
                    m.get("n_est", ""),
                ]
            writer.writerow(row)


def predict_instruments(audio_path: Path) -> dict[str, list[float]]:
    """Run DrumScript inference and return predicted times per instrument."""
    audio, sr = load_audio(str(audio_path), sr=SAMPLE_RATE)
    audio = normalise_audio(audio)
    onsets = detect_onsets(audio, sr)
    events = classify_events(audio, sr, onsets)

    predictions: dict[str, list[float]] = defaultdict(list)
    for event in events:
        for instrument in event["instruments"]:
            predictions[instrument].append(event["time_sec"])
    return {instrument: sorted(times) for instrument, times in predictions.items()}


# ── archive ──────────────────────────────────────────────────────────────────


def git_output(args: list[str]) -> str:
    """Return stdout from a git command, or ``unknown`` if unavailable."""
    try:
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def safe_name(value: str) -> str:
    """Convert a free-form run name into a filesystem-safe suffix."""
    cleaned = "".join(ch if ch.isalnum() or ch in ("-", "_") else "-" for ch in value.strip())
    return cleaned.strip("-") or "run"


@dataclass
class RunContext:
    """Runtime context shared by benchmark archive helpers."""

    dataset_name: str
    adapter: ModuleType
    args: argparse.Namespace


def archive_run(
    ctx: RunContext,
    items: Sequence[BenchmarkItem],
    results: Sequence[dict | None],
    summary: dict,
    bucket_summaries: dict,
) -> Path:
    """Archive metrics and run metadata under ``outputs/benchmarks``."""
    commit = git_output(["rev-parse", "--short", "HEAD"])
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_suffix = f"_{safe_name(ctx.args.run_name)}" if ctx.args.run_name else ""
    archive_dir = Path("outputs") / "benchmarks" / ctx.dataset_name / f"{timestamp}_{commit}{run_suffix}"
    archive_dir.mkdir(parents=True, exist_ok=True)

    write_metrics_csv(items, results, ctx.adapter.INSTRUMENT_CODES, archive_dir / "results.csv")

    metadata = {
        "dataset": ctx.dataset_name,
        "window_seconds": ONSET_WINDOW,
        "files_total": len(items),
        "files_evaluated": len([r for r in results if r]),
        "git_commit": git_output(["rev-parse", "HEAD"]),
        "git_dirty": bool(git_output(["status", "--short"])),
        "command": " ".join(shlex.quote(part) for part in sys.argv),
        "args": {k: str(v) for k, v in vars(ctx.args).items() if k != "dataset"},
        "summary": summary,
        "bucket_summaries": bucket_summaries,
    }
    (archive_dir / "summary.json").write_text(json.dumps(metadata, indent=2))
    (archive_dir / "command.txt").write_text(metadata["command"] + "\n")
    (archive_dir / "git_commit.txt").write_text(
        f"{metadata['git_commit']}\ndirty={metadata['git_dirty']}\n"
    )
    return archive_dir


# ── per-item loop ────────────────────────────────────────────────────────────


def evaluate_item(item: BenchmarkItem, code_to_labels: Mapping[str, Sequence[str]]) -> dict | None:
    """Run DrumScript on one benchmark item and score its predictions."""
    print(f"  {item.track_id} [{item.bucket}]")
    if not item.references:
        print("    [WARN] No annotations, skipping.")
        return {}

    try:
        predictions = predict_instruments(item.audio_path)
    except Exception as exc:  # noqa: BLE001 — surface any runtime failure
        print(f"    [ERROR] DrumScript failed: {exc}")
        return None

    metrics = evaluate_per_instrument(predictions, item.references, code_to_labels)
    for code, m in metrics.items():
        print(
            f"    {code}: P={m['precision']:.3f}  R={m['recall']:.3f}  F={m['f_measure']:.3f}  "
            f"(ref={m['n_ref']}, est={m['n_est']})"
        )
    return metrics


# ── CLI ──────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build the benchmark command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", default=None,
                        help="Per-item CSV path (default: <dataset>_results.csv)")
    parser.add_argument("--run-name", default=None,
                        help="Optional suffix for the archived run directory")
    parser.add_argument("--limit", type=int, default=None, help="Process only first N items")

    subparsers = parser.add_subparsers(dest="dataset", required=True, metavar="DATASET",
                                       help="Which dataset adapter to use")
    for name, adapter in sorted(ADAPTERS.items()):
        sub = subparsers.add_parser(name, help=adapter.__doc__.splitlines()[0] if adapter.__doc__ else name)
        adapter.add_cli_args(sub)
    return parser


def main() -> None:
    """Run the selected benchmark from command-line arguments."""
    parser = build_parser()
    args = parser.parse_args()

    adapter = ADAPTERS[args.dataset]
    ctx = RunContext(dataset_name=args.dataset, adapter=adapter, args=args)

    items = list(adapter.iter_items(args))
    if args.limit:
        items = items[: args.limit]
    if not items:
        sys.exit(f"[ERROR] No items produced by {args.dataset} adapter")

    print(f"\nDataset : {ctx.dataset_name}")
    print(f"Items   : {len(items)}")
    print(f"Window  : {int(ONSET_WINDOW * 1000)}ms\n")
    print("─" * 60)

    results: list[dict | None] = [evaluate_item(item, adapter.CODE_TO_DRUMSCRIPT) for item in items]
    valid = [r for r in results if r]
    print(f"\n{'─' * 60}\nEvaluated {len(valid)} / {len(items)} items successfully.\n")

    summary = summarise(valid)
    print_summary("── SUMMARY (macro-average across items) ──", summary)

    bucket_summaries = summarise_by_bucket(items, results)
    if len(bucket_summaries) > 1 or next(iter(bucket_summaries), "all") != "all":
        print("\n── SUMMARY BY BUCKET ──")
        for bucket, bucket_summary in bucket_summaries.items():
            print()
            print_summary(f"[{bucket}]", bucket_summary)

    output_path = Path(args.output or f"{ctx.dataset_name}_results.csv")
    write_metrics_csv(items, results, adapter.INSTRUMENT_CODES, output_path)
    print(f"\nPer-item results saved to: {output_path}")

    archive_dir = archive_run(ctx, items, results, summary, bucket_summaries)
    print(f"Archived benchmark run to: {archive_dir}")


if __name__ == "__main__":
    main()
