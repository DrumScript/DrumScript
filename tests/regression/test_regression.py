#!/usr/bin/env python3
"""
Transcription regression checks: run a fixed set of audio, compare against last time.

What this file is
-----------------
One script that does three jobs, because they share a single list of audio files
and must never disagree about it:

1. **Runs** every file in ``songs.json`` through the transcription pipeline and
   archives the results into a dated folder.
2. **Compares** two of those archives and reports what moved.
3. **Asserts**, under pytest, that isolated single drum hits still classify as
   the right instrument.

It is both a pytest module and a command-line tool. Importing it (what pytest
does) defines the tests; running it directly gives you the runner and the
comparator.

Two kinds of check, and why they differ
---------------------------------------
A full track has no known-correct transcription. Nobody can say what the
"right" 1,500 events are for a seven-minute song, so the only meaningful check
is to compare one run against another and read what changed.

An isolated single hit is different. A recording of one drum has a correct
answer: a kick sample must classify as ``kick``. Those are real pass/fail
assertions, and they are what catches a threshold change breaking detection
without anyone reading a diff.

Both kinds live in the same ``songs.json``, distinguished by their ``kind``
field.

Why it does not trust exit codes
--------------------------------
``drumscript.main`` prints errors but still exits 0, so a failing file does not
stop a shell chain of ``&&``. Worse, a file that fails the same way in *both*
halves of a before/after pair cancels out: the comparison looks clean while that
file contributed nothing.

This script confirms the expected ``.json``, ``.pdf`` and ``.mid`` were actually
written, and refuses to report success otherwise. It also checks every audio
file exists before running anything.

Why the JSON and not the log
----------------------------
``drumscript.log`` records ``Classified 1550 events``. The transcription JSON
records *which* 1,550 and the physics behind each one, so a comparison can say
``kick 412 -> 598 (+186)`` and list the onsets that changed, rather than leaving
you to read two columns of text side by side.

Setting it up
-------------
``songs.json`` is gitignored: it names audio on your own machine. Copy the
template and edit it::

    cp tests/regression/songs.example.json tests/regression/songs.json

Point the entries at your own recordings. For each single hit, set ``expect`` to
the instrument it should classify as. If you do not know what a file *should*
produce, make it a ``track`` instead and it will be compared rather than
asserted.

Without ``songs.json`` the tests skip cleanly and the CLI prints these
instructions, so a fresh clone is never broken by its absence.

How to run
----------
::

    # pytest
    pytest tests/regression/ -v
    pytest -m "not slow"                  # included; skips without songs.json

    # command line
    python3 tests/regression/test_regression.py run --label <name> --timing BEFORE
    python3 tests/regression/test_regression.py run --label <name> --timing AFTER
    python3 tests/regression/test_regression.py compare <before_folder> <after_folder>
    python3 tests/regression/test_regression.py verify <run_folder>
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import pytest

# Only the pytest assertions need DrumScript itself. Importing lazily means the
# `compare` and `verify` subcommands still work on archived folders from a
# checkout where the package is not installed.
try:
    import drumscript as ds
except ImportError:  # pragma: no cover - depends on the environment, not the code
    ds = None


# =============================================================================
# Constants
# =============================================================================

#: The audio list. Gitignored: it names files on your own machine.
CONFIG_FILENAME = "songs.json"

#: Committed template, copied to CONFIG_FILENAME to get started.
EXAMPLE_FILENAME = "songs.example.json"

#: Suffix DrumScript appends to the input stem when writing its outputs.
TRANSCRIPTION_SUFFIX = "_transcription"

#: Extensions written for every successful transcription. Their presence is the
#: only trustworthy success signal, since the CLI exits 0 on failure.
EXPECTED_EXTENSIONS = ("json", "pdf", "mid")

#: debug_features reported when an onset keeps its label but its physics moved.
FEATURE_KEYS = ("peak_freq", "centroid", "decay", "lfer", "hfer", "hfer_5k")

#: Onsets are paired by position, then sanity-checked on time. A pair whose
#: times differ by more than this is a detection shift, not a relabel.
TIME_MATCH_TOLERANCE_S = 0.002

#: Folder-name date format, e.g. "sat18october2026". Lowercased after formatting.
FOLDER_DATE_FORMAT = "%a%d%B%Y"

#: Scope segment used when a run covered every configured entry.
DEFAULT_SCOPE = "all-files"

#: Entry kinds.
KIND_TRACK = "track"
KIND_SINGLE_HIT = "single_hit"

#: Set to a run folder to verify an archived run without re-running anything.
RUN_FOLDER_ENV = "DRUMSCRIPT_REGRESSION_RUN_FOLDER"

#: Environment variables the patched scripts/backup.sh reads to skip its prompts.
BACKUP_ENV_TIMING = "E2E_TIMING"
BACKUP_ENV_REASON = "E2E_REASON"
BACKUP_ENV_NUMBER = "E2E_BACKUP_NUM"

#: Seconds before a subprocess is treated as hung and killed. Every child is
#: also given a closed stdin, so a script that prompts gets EOF and carries on
#: instead of waiting for a keypress nobody can see: `capture_output` swallows
#: the prompt, so a blocking `read` looks exactly like a stall.
BACKUP_TIMEOUT_S = 900
GIT_TIMEOUT_S = 30
DEFAULT_ENTRY_TIMEOUT_S = 3600

SETUP_HINT = (
    f"No {CONFIG_FILENAME} found.\n"
    f"  Copy the template and point it at your own audio:\n"
    f"    cp tests/regression/{EXAMPLE_FILENAME} tests/regression/{CONFIG_FILENAME}"
)


# =============================================================================
# Configuration
# =============================================================================


def repo_root():
    """
    Returns the repository root.

    Resolved from this file's location (``<root>/tests/regression/test_regression.py``)
    so the script works regardless of the current working directory.

    :return: Absolute path to the repository root.
    :rtype: pathlib.Path
    """
    return Path(__file__).resolve().parents[2]


def config_path():
    """
    Returns the path to the audio list, which sits beside this script.

    :return: Absolute path to ``songs.json``.
    :rtype: pathlib.Path
    """
    return Path(__file__).resolve().parent / CONFIG_FILENAME


def load_config(path=None):
    """
    Loads the audio list.

    :param path: Path to the JSON config; defaults to ``songs.json`` beside this file.
    :type path: pathlib.Path, optional
    :return: The parsed configuration.
    :rtype: dict
    :raises SystemExit: If the file is missing, unreadable or has no ``entries``.
    """
    target = Path(path) if path else config_path()

    try:
        with open(target, encoding="utf-8") as handle:
            config = json.load(handle)
    except FileNotFoundError:
        raise SystemExit(f"[ERROR] {SETUP_HINT}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"[ERROR] {target} is not valid JSON: {exc}")

    if "entries" not in config:
        raise SystemExit(f"[ERROR] {target} has no 'entries' list")

    config["_path"] = str(target)
    return config


def entries_of_kind(config, kind):
    """
    Filters config entries by kind.

    :param config: The loaded configuration.
    :type config: dict
    :param kind: Either ``track`` or ``single_hit``.
    :type kind: str
    :return: Matching entries, in config order.
    :rtype: list
    """
    return [entry for entry in config["entries"] if entry.get("kind") == kind]


def audio_path(config, entry, root=None):
    """
    Builds the absolute path to an entry's audio file.

    An entry's ``file`` is resolved against ``audio_root`` unless it is already
    absolute, which lets you point at recordings outside the repository.

    :param config: The loaded configuration.
    :type config: dict
    :param entry: One config entry.
    :type entry: dict
    :param root: Repository root; defaults to the detected root.
    :type root: pathlib.Path, optional
    :return: Absolute path to the audio file.
    :rtype: pathlib.Path
    """
    candidate = Path(entry["file"])
    if candidate.is_absolute():
        return candidate
    base = Path(root) if root else repo_root()
    return base / config.get("audio_root", "test_audio") / candidate


def output_paths(config, entry, root=None):
    """
    Builds the output paths DrumScript is expected to write for an entry.

    :param config: The loaded configuration.
    :type config: dict
    :param entry: One config entry.
    :type entry: dict
    :param root: Repository root; defaults to the detected root.
    :type root: pathlib.Path, optional
    :return: Extension to expected output path.
    :rtype: dict
    """
    base = Path(root) if root else repo_root()
    out_dir = base / config.get("output_dir", "outputs")
    stem = f"{entry['name']}{TRANSCRIPTION_SUFFIX}"
    return {ext: out_dir / f"{stem}.{ext}" for ext in EXPECTED_EXTENSIONS}


def transcription_json_in(folder, entry):
    """
    Locates an entry's transcription JSON inside a completed run folder.

    :param folder: A run folder.
    :type folder: pathlib.Path
    :param entry: One config entry.
    :type entry: dict
    :return: Path to the JSON file, which may not exist.
    :rtype: pathlib.Path
    """
    return Path(folder) / f"{entry['name']}{TRANSCRIPTION_SUFFIX}.json"


def load_events(json_path):
    """
    Loads the onset events from a transcription JSON.

    :param json_path: Path to a transcription JSON file.
    :type json_path: pathlib.Path
    :return: The list of onset event dicts.
    :rtype: list
    """
    with open(json_path, encoding="utf-8") as handle:
        return json.load(handle)


# =============================================================================
# Expectations
# =============================================================================


def check_single_hit(entry, events):
    """
    Checks a single-hit entry's events against its expected classification.

    :param entry: One ``single_hit`` config entry.
    :type entry: dict
    :param events: Onset events from that entry's transcription JSON.
    :type events: list
    :return: ``(passed, message)`` where message explains any failure.
    :rtype: tuple
    """
    expected_labels = entry.get("expect")
    if expected_labels is None:
        return True, "no expectation set"

    expected_count = entry.get("expect_events")
    if expected_count is not None and len(events) != expected_count:
        got = [sorted(event.get("instruments", [])) for event in events]
        return False, f"expected {expected_count} onset(s), got {len(events)}: {got}"

    if not events:
        return False, "no onsets produced"

    actual_labels = sorted(events[0].get("instruments", []))
    if actual_labels != sorted(expected_labels):
        features = events[0].get("debug_features") or {}
        detail = ", ".join(f"{key}={features[key]:.4f}" for key in sorted(features) if isinstance(features.get(key), float))
        return False, f"expected {sorted(expected_labels)}, got {actual_labels} [{detail}]"

    return True, f"{actual_labels}"


def check_track(entry, events):
    """
    Applies a track entry's floor check.

    Full tracks have no known-correct transcription, so the only automatic check
    worth making is that the track produced something at all. Everything else is
    handled by comparing against a previous run.

    :param entry: One ``track`` config entry.
    :type entry: dict
    :param events: Onset events from that entry's transcription JSON.
    :type events: list
    :return: ``(passed, message)``.
    :rtype: tuple
    """
    floor = entry.get("min_events", 1)
    if len(events) < floor:
        return False, f"produced {len(events)} onsets, expected at least {floor}"
    return True, f"{len(events)} onsets"


def check_entry(entry, events):
    """
    Dispatches to the right check for an entry's kind.

    :param entry: One config entry.
    :type entry: dict
    :param events: Onset events from that entry's transcription JSON.
    :type events: list
    :return: ``(passed, message)``.
    :rtype: tuple
    """
    if entry.get("kind") == KIND_SINGLE_HIT:
        return check_single_hit(entry, events)
    return check_track(entry, events)


def verify_run_folder(config, folder):
    """
    Verifies a completed run folder against every expectation in the config.

    Lets an archive from months ago be re-checked without re-running anything.

    :param config: The loaded configuration.
    :type config: dict
    :param folder: A run folder to verify.
    :type folder: pathlib.Path
    :return: List of ``(entry_name, passed, message)`` in config order.
    :rtype: list
    """
    results = []
    for entry in config["entries"]:
        json_path = transcription_json_in(folder, entry)
        if not json_path.is_file():
            results.append((entry["name"], False, "transcription JSON missing from run folder"))
            continue
        try:
            events = load_events(json_path)
        except (OSError, json.JSONDecodeError) as exc:
            results.append((entry["name"], False, f"could not read JSON: {exc}"))
            continue
        passed, message = check_entry(entry, events)
        results.append((entry["name"], passed, message))
    return results


# =============================================================================
# Comparison
# =============================================================================


def run_name_from(json_path):
    """
    Recovers an entry name from a transcription JSON filename.

    :param json_path: Path to a transcription JSON.
    :type json_path: pathlib.Path
    :return: The entry name with the DrumScript suffix stripped.
    :rtype: str
    """
    suffix = f"{TRANSCRIPTION_SUFFIX}.json"
    name = json_path.name
    return name[: -len(suffix)] if name.endswith(suffix) else json_path.stem


def load_run(folder):
    """
    Loads every transcription JSON in a run folder, keyed by entry name.

    Works on any folder containing transcription JSON, including archives made
    before this script existed.

    :param folder: Path to a run folder.
    :type folder: pathlib.Path
    :return: Mapping of entry name to its list of onset events.
    :rtype: dict
    """
    if not folder.is_dir():
        raise SystemExit(f"[ERROR] Not a directory: {folder}")

    run = {}
    for path in sorted(folder.glob(f"*{TRANSCRIPTION_SUFFIX}.json")):
        try:
            run[run_name_from(path)] = load_events(path)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[WARN] Could not read {path.name}: {exc}", file=sys.stderr)

    if not run:
        raise SystemExit(f"[ERROR] No transcription JSON found in {folder}")
    return run


def label_counts(events):
    """
    Counts how many times each instrument label appears across a track's onsets.

    An onset may carry several instruments, so the total can exceed the onset
    count. That is expected, and why onsets and labels are reported separately.

    :param events: Onset events from one transcription JSON.
    :type events: list
    :return: Instrument label to occurrence count.
    :rtype: collections.Counter
    """
    return Counter(label for event in events for label in event.get("instruments", []))


def feature_deltas(before_event, after_event, eps):
    """
    Finds debug_features that moved between two paired onsets.

    :param before_event: The onset from the BEFORE run.
    :type before_event: dict
    :param after_event: The onset from the AFTER run.
    :type after_event: dict
    :param eps: Absolute change below which a feature counts as unmoved.
    :type eps: float
    :return: Feature name to ``(before_value, after_value)`` for each moved feature.
    :rtype: dict
    """
    before_features = before_event.get("debug_features") or {}
    after_features = after_event.get("debug_features") or {}

    moved = {}
    for key in FEATURE_KEYS:
        old = before_features.get(key)
        new = after_features.get(key)
        if old is None or new is None:
            if old != new:
                moved[key] = (old, new)
            continue
        if abs(float(new) - float(old)) > eps:
            moved[key] = (float(old), float(new))
    return moved


def compare_entry(before_events, after_events, eps):
    """
    Compares one entry's onsets across two runs.

    Onsets are paired by position. If the two runs produced different onset
    counts, pairing is meaningless, so only aggregate figures are reported and
    the entry is flagged as an onset-count change. That distinction matters: it
    tells you whether onset detection moved or only classification.

    :param before_events: Onsets from the BEFORE run.
    :type before_events: list
    :param after_events: Onsets from the AFTER run.
    :type after_events: list
    :param eps: Absolute change below which a feature counts as unmoved.
    :type eps: float
    :return: A dict describing what changed.
    :rtype: dict
    """
    before_counts = label_counts(before_events)
    after_counts = label_counts(after_events)

    changed_labels = {
        label: (before_counts.get(label, 0), after_counts.get(label, 0))
        for label in sorted(set(before_counts) | set(after_counts))
        if before_counts.get(label, 0) != after_counts.get(label, 0)
    }

    result = {
        "onsets_before": len(before_events),
        "onsets_after": len(after_events),
        "onset_count_changed": len(before_events) != len(after_events),
        "label_changes": changed_labels,
        "relabelled": [],
        "features_only": 0,
        "time_shifted": 0,
    }

    if result["onset_count_changed"]:
        return result

    for index, (before_event, after_event) in enumerate(zip(before_events, after_events)):
        before_time = before_event.get("time_sec")
        after_time = after_event.get("time_sec")

        times_known = before_time is not None and after_time is not None
        if times_known and abs(float(after_time) - float(before_time)) > TIME_MATCH_TOLERANCE_S:
            result["time_shifted"] += 1

        before_labels = list(before_event.get("instruments", []))
        after_labels = list(after_event.get("instruments", []))

        if before_labels != after_labels:
            result["relabelled"].append(
                {
                    "index": index,
                    "time_sec": before_time,
                    "before": before_labels,
                    "after": after_labels,
                    "features": feature_deltas(before_event, after_event, eps),
                }
            )
        elif feature_deltas(before_event, after_event, eps):
            result["features_only"] += 1

    return result


def compare_runs(before_run, after_run, eps):
    """
    Compares two whole runs, entry by entry.

    :param before_run: Entry name to onsets, from the BEFORE run.
    :type before_run: dict
    :param after_run: Entry name to onsets, from the AFTER run.
    :type after_run: dict
    :param eps: Absolute change below which a feature counts as unmoved.
    :type eps: float
    :return: ``(per_entry_results, only_in_before, only_in_after)``.
    :rtype: tuple
    """
    shared = sorted(set(before_run) & set(after_run))
    only_before = sorted(set(before_run) - set(after_run))
    only_after = sorted(set(after_run) - set(before_run))

    results = {name: compare_entry(before_run[name], after_run[name], eps) for name in shared}
    return results, only_before, only_after


def entry_changed(result):
    """
    Reports whether an entry differs at all between the two runs.

    :param result: One entry's comparison result.
    :type result: dict
    :return: True when anything moved.
    :rtype: bool
    """
    return bool(result["onset_count_changed"] or result["label_changes"] or result["relabelled"] or result["features_only"] or result["time_shifted"])


def format_label_changes(changes):
    """
    Renders per-instrument count changes as a compact one-line string.

    :param changes: Instrument label to ``(before_count, after_count)``.
    :type changes: dict
    :return: A readable summary, or a dash when nothing changed.
    :rtype: str
    """
    if not changes:
        return "-"
    parts = []
    for label, (old, new) in changes.items():
        arrow = "+" if new > old else ""
        parts.append(f"{label} {old}->{new} ({arrow}{new - old})")
    return ", ".join(parts)


def build_report(results, only_before, only_after, before_dir, after_dir, show_onsets, quiet_identical, markdown):
    """
    Builds the comparison report.

    :param results: Per-entry comparison results.
    :type results: dict
    :param only_before: Entry names present only in the BEFORE run.
    :type only_before: list
    :param only_after: Entry names present only in the AFTER run.
    :type only_after: list
    :param before_dir: The BEFORE run folder.
    :type before_dir: pathlib.Path
    :param after_dir: The AFTER run folder.
    :type after_dir: pathlib.Path
    :param show_onsets: Maximum changed onsets to list per entry.
    :type show_onsets: int
    :param quiet_identical: When True, omit entries that did not change.
    :type quiet_identical: bool
    :param markdown: When True, emit markdown rather than a terminal table.
    :type markdown: bool
    :return: The rendered report.
    :rtype: str
    """
    lines = []
    bullet = "* " if markdown else "  - "
    rule = "" if markdown else "-" * 118

    def heading(text, level=2):
        lines.append(f"{'#' * level} {text}" if markdown else f"\n{text}\n{'=' * len(text)}")

    heading("Transcription regression comparison", level=1 if markdown else 2)
    lines.append("")
    lines.append(f"{bullet}**BEFORE:** `{before_dir}`" if markdown else f"  BEFORE: {before_dir}")
    lines.append(f"{bullet}**AFTER:**  `{after_dir}`" if markdown else f"  AFTER:  {after_dir}")
    lines.append("")

    # Reported first: an entry missing from one side is the case that silently
    # passes a manual diff when a file failed identically in both runs.
    if only_before or only_after:
        heading("Entries that do not appear in both runs")
        lines.append("")
        for name in only_before:
            lines.append(f"{bullet}`{name}` -- in BEFORE only (did it fail, or was it dropped?)")
        for name in only_after:
            lines.append(f"{bullet}`{name}` -- in AFTER only (newly added?)")
        lines.append("")

    changed = {name: res for name, res in results.items() if entry_changed(res)}

    heading("Summary")
    lines.append("")
    if markdown:
        lines.append("| Entry | Onsets | Label changes | Relabelled | Features only |")
        lines.append("|---|---|---|---|---|")
    else:
        lines.append(f"  {'Entry':<44} {'Onsets':>13}  {'Relabel':>7} {'FeatOnly':>8}  Label changes")
        lines.append(rule)

    for name, res in sorted(results.items()):
        if quiet_identical and name not in changed:
            continue

        onsets = f"{res['onsets_before']}->{res['onsets_after']}" if res["onset_count_changed"] else str(res["onsets_before"])
        labels = format_label_changes(res["label_changes"])
        relabelled = len(res["relabelled"])

        if markdown:
            flag = " **(onset count moved)**" if res["onset_count_changed"] else ""
            lines.append(f"| `{name}` | {onsets}{flag} | {labels} | {relabelled} | {res['features_only']} |")
        else:
            lines.append(f"  {name[:42]:<44} {onsets:>13}  {relabelled:>7} {res['features_only']:>8}  {labels}")

    lines.append("")

    detailed = {name: res for name, res in changed.items() if res["relabelled"]}
    if detailed and show_onsets > 0:
        heading("Changed onsets")
        for name, res in sorted(detailed.items()):
            lines.append("")
            lines.append(f"### `{name}`" if markdown else f"  {name}")
            if not markdown:
                lines.append(rule)

            for item in res["relabelled"][:show_onsets]:
                time_str = "?" if item["time_sec"] is None else f"{item['time_sec']:.3f}s"
                before_labels = ", ".join(item["before"]) or "(none)"
                after_labels = ", ".join(item["after"]) or "(none)"
                if markdown:
                    lines.append(f"{bullet}`{time_str}` {before_labels} -> **{after_labels}**")
                else:
                    lines.append(f"      {time_str:>10}  {before_labels} -> {after_labels}")

                for key, (old, new) in item["features"].items():
                    if isinstance(old, float) and isinstance(new, float):
                        detail = f"{key}: {old:.4f} -> {new:.4f}"
                    else:
                        detail = f"{key}: {old} -> {new}"
                    lines.append(f"    {bullet}{detail}" if markdown else f"                  {detail}")

            remaining = len(res["relabelled"]) - show_onsets
            if remaining > 0:
                lines.append(f"{bullet}...and {remaining} more (raise --show-onsets to see them)")

        lines.append("")

    heading("Verdict")
    lines.append("")
    if only_before or only_after:
        lines.append(f"{bullet}**Runs are not directly comparable** -- the folders hold different entries.")
    if not changed:
        lines.append(f"{bullet}No differences. Every entry produced identical onsets, labels and features.")
    else:
        lines.append(f"{bullet}{len(changed)} of {len(results)} entries changed.")
        shifted = sum(res["time_shifted"] for res in changed.values())
        if shifted:
            lines.append(f"{bullet}{shifted} onsets moved in time -- onset detection changed, not only classification.")

    lines.append("")
    return "\n".join(lines)


# =============================================================================
# Running
# =============================================================================


def say(message, prefix="  "):
    """
    Prints a progress line and flushes it immediately.

    Without the flush, stdout is block-buffered when piped (into ``tee``, say),
    so nothing appears until the run ends. The whole point of these lines is to
    show what is happening while a long track is transcribing.

    :param message: The line to print.
    :type message: str
    :param prefix: Indentation prefix.
    :type prefix: str
    """
    print(f"{prefix}{message}", flush=True)


def git_commit(root):
    """
    Returns the current short git commit, for the manifest.

    :param root: Repository root.
    :type root: pathlib.Path
    :return: Short commit hash, or ``"unknown"`` if git is unavailable.
    :rtype: str
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
            stdin=subprocess.DEVNULL,
            timeout=GIT_TIMEOUT_S,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "unknown"


def git_is_dirty(root):
    """
    Reports whether the working tree has uncommitted changes.

    Worth recording: a run against a dirty tree cannot be reproduced from the
    commit hash alone, which matters when comparing runs weeks apart.

    :param root: Repository root.
    :type root: pathlib.Path
    :return: True when the tree has uncommitted changes.
    :rtype: bool
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
            stdin=subprocess.DEVNULL,
            timeout=GIT_TIMEOUT_S,
        )
        return bool(result.stdout.strip()) if result.returncode == 0 else False
    except (OSError, subprocess.TimeoutExpired):
        return False


def build_folder_name(archive_dir, label, timing, tag=None, scope=DEFAULT_SCOPE):
    """
    Builds a non-clashing dated archive folder name.

    The shape is::

        thu22october2026__orchestration_outputs__BEFORE__my_label__all-files__1
        |______________|  |___________________|  |____|  |______|  |_______|  |
          date            tag                    timing  label     scope      number

    ``timing`` is omitted when it was not supplied. The trailing number
    increments until the name is free, so two runs on the same day never
    overwrite each other.

    :param archive_dir: Directory the run folders live in.
    :type archive_dir: pathlib.Path
    :param label: Descriptive part of the name.
    :type label: str
    :param timing: ``BEFORE``, ``AFTER`` or None.
    :type timing: str, optional
    :param tag: Second segment; defaults to the archive directory's own name.
    :type tag: str, optional
    :param scope: What the run covered, e.g. ``all-files``.
    :type scope: str
    :return: A path that does not yet exist.
    :rtype: pathlib.Path
    """
    date_part = datetime.now().strftime(FOLDER_DATE_FORMAT).lower()
    safe_label = "".join(char if char.isalnum() or char in "_-" else "_" for char in label)
    folder_tag = tag or Path(archive_dir).name

    segments = [date_part, folder_tag]
    if timing:
        segments.append(timing)
    segments.extend([safe_label, scope])
    stem = "__".join(segments)

    number = 1
    while True:
        candidate = archive_dir / f"{stem}__{number}"
        if not candidate.exists():
            return candidate
        number += 1


def describe_scope(config, entries, only, kind):
    """
    Describes what a run covered, for the folder name's scope segment.

    A filtered run must not be labelled ``all-files``: a later comparison would
    otherwise look like entries had vanished, when they were never run.

    :param config: The loaded configuration.
    :type config: dict
    :param entries: The entries actually selected.
    :type entries: list
    :param only: The ``--only`` names given, if any.
    :type only: list
    :param kind: The ``--kind`` filter given, if any.
    :type kind: str, optional
    :return: A filename-safe scope description.
    :rtype: str
    """
    if not only and not kind:
        return DEFAULT_SCOPE
    if kind and not only:
        return f"{kind.replace('_', '-')}-files"
    return f"{len(entries)}-of-{len(config['entries'])}-files"


def select_entries(config, only, kind):
    """
    Applies the ``--only`` and ``--kind`` filters to the config entries.

    :param config: The loaded configuration.
    :type config: dict
    :param only: Entry names to keep; empty means keep all.
    :type only: list
    :param kind: Entry kind to keep, or None for all.
    :type kind: str, optional
    :return: The selected entries, in config order.
    :rtype: list
    """
    entries = config["entries"]
    if kind:
        entries = [entry for entry in entries if entry.get("kind") == kind]
    if only:
        wanted = set(only)
        entries = [entry for entry in entries if entry["name"] in wanted]
        missing = wanted - {entry["name"] for entry in entries}
        if missing:
            raise SystemExit(f"[ERROR] --only named entries not in the config: {', '.join(sorted(missing))}")
    return entries


def preflight(config, entries, root):
    """
    Checks every audio file exists before anything is run.

    Failing fast here is the single biggest improvement over a shell chain: a
    missing file is reported up front rather than part-way through a long run.

    :param config: The loaded configuration.
    :type config: dict
    :param entries: The entries selected for this run.
    :type entries: list
    :param root: Repository root.
    :type root: pathlib.Path
    :return: List of human-readable problems; empty when all is well.
    :rtype: list
    """
    problems = []
    for entry in entries:
        path = audio_path(config, entry, root)
        if not path.is_file():
            problems.append(f"missing audio: {entry['name']} -> {path}")
    return problems


def run_entry(config, entry, root, log_handle, tee, timeout_s=DEFAULT_ENTRY_TIMEOUT_S):
    """
    Runs the transcription CLI for one entry and verifies its outputs.

    The CLI is used rather than the Python API deliberately: this reproduces the
    command a person would type, so a regression in argument handling or in the
    CLI's own error paths is caught too. Each entry also gets its own process,
    so one file crashing does not take the rest of the run down.

    :param config: The loaded configuration.
    :type config: dict
    :param entry: The entry to run.
    :type entry: dict
    :param root: Repository root.
    :type root: pathlib.Path
    :param log_handle: Open file handle the combined output is appended to.
    :type log_handle: io.TextIOBase
    :param tee: When True, also stream the output to the terminal.
    :type tee: bool
    :param timeout_s: Seconds before this entry is treated as hung and killed.
    :type timeout_s: int
    :return: A result dict describing what happened.
    :rtype: dict
    """
    audio = audio_path(config, entry, root)
    python_flags = list(entry.get("python_flags", []))
    command = [sys.executable] + python_flags + ["-m", "drumscript.main", str(audio)] + list(entry.get("args", []))

    started = datetime.now()
    # stdin is closed so anything that tries to prompt gets EOF rather than
    # blocking on input nobody can see, and the timeout is a hard backstop.
    timed_out = False
    try:
        completed = subprocess.run(
            command,
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
            stdin=subprocess.DEVNULL,
            timeout=timeout_s,
        )
        output = completed.stdout + (completed.stderr or "")
        returncode = completed.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = None
        output = (exc.stdout or "") + (exc.stderr or "") if isinstance(exc.stdout, str) else ""
    duration = (datetime.now() - started).total_seconds()

    log_handle.write(output)
    log_handle.flush()
    if tee:
        print(output, end="")

    result = {
        "name": entry["name"],
        "kind": entry.get("kind"),
        "command": command,
        "returncode": returncode,
        "duration_s": round(duration, 2),
        "passed": False,
        "message": "",
    }

    if timed_out:
        result["message"] = f"timed out after {timeout_s}s and was killed"
        return result

    # The CLI exits 0 even on failure, so the written files are the real signal.
    expected = output_paths(config, entry, root)
    missing = [ext for ext, path in expected.items() if not path.is_file()]
    if missing:
        result["message"] = f"outputs not written: {', '.join(sorted(missing))}"
        return result

    try:
        events = load_events(expected["json"])
    except (OSError, json.JSONDecodeError) as exc:
        result["message"] = f"could not read transcription JSON: {exc}"
        return result

    passed, message = check_entry(entry, events)
    result["passed"] = passed
    result["message"] = message
    result["onsets"] = len(events)
    return result


def run_backup(root, timing, label, number):
    """
    Regenerates the code bundle by calling ``scripts/backup.sh`` without prompting.

    Optional: the script is skipped with a warning when it is not present, so
    this works in a checkout that does not have it.

    :param root: Repository root.
    :type root: pathlib.Path
    :param timing: ``BEFORE`` or ``AFTER``; defaults to ``AFTER`` when not supplied.
    :type timing: str, optional
    :param label: Reason string recorded in the backup filename.
    :type label: str
    :param number: Backup number for the day.
    :type number: int
    :return: ``(ok, message)``.
    :rtype: tuple
    """
    script = root / "scripts" / "backup.sh"
    if not script.is_file():
        return False, f"not found, skipped: {script}"

    answers = [timing or "AFTER", label, str(number)]

    # Two kinds of backup.sh exist in the wild and this has to drive both:
    #
    #   the interactive original  asks its three questions with `read -r -p`
    #   the non-interactive one   reads E2E_TIMING / E2E_REASON / E2E_BACKUP_NUM
    #
    # So do both. The environment is set for the second, and the three answers
    # are piped in for the first. A script that reads the environment simply
    # never consumes the stdin, which costs nothing.
    #
    # This is also what stops the hang: stdin is a pipe that closes after those
    # three lines, so a fourth `read` gets EOF instead of waiting forever on a
    # prompt that capture_output has swallowed.
    environment = dict(os.environ)
    environment[BACKUP_ENV_TIMING] = answers[0]
    environment[BACKUP_ENV_REASON] = answers[1]
    environment[BACKUP_ENV_NUMBER] = answers[2]

    try:
        completed = subprocess.run(
            ["bash", str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            env=environment,
            check=False,
            input="\n".join(answers) + "\n",
            timeout=BACKUP_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return False, f"timed out after {BACKUP_TIMEOUT_S}s and was killed. Re-run with --no-backup to skip it."
    except OSError as exc:
        return False, f"could not run backup.sh: {exc}"

    if completed.returncode != 0:
        return False, f"backup.sh exited {completed.returncode}: {completed.stderr.strip()[:200]}"
    return True, f"code bundle regenerated (answers: {', '.join(answers)})"


def archive_outputs(config, entries, root, destination, keep_outputs):
    """
    Moves (or copies) this run's outputs into the dated archive folder.

    Only files belonging to the entries that were run are touched, so an
    unrelated file in the output folder is left alone.

    :param config: The loaded configuration.
    :type config: dict
    :param entries: The entries that were run.
    :type entries: list
    :param root: Repository root.
    :type root: pathlib.Path
    :param destination: The dated archive folder.
    :type destination: pathlib.Path
    :param keep_outputs: When True, copy rather than move.
    :type keep_outputs: bool
    :return: Number of files archived.
    :rtype: int
    """
    destination.mkdir(parents=True, exist_ok=True)
    transfer = shutil.copy2 if keep_outputs else shutil.move

    archived = 0
    for entry in entries:
        for path in output_paths(config, entry, root).values():
            if path.is_file():
                transfer(str(path), str(destination / path.name))
                archived += 1
    return archived


def copy_supporting_files(config, root, destination):
    """
    Copies any configured extra files into the archive folder.

    ``extra_files`` is a list of repository-relative paths, each copied in if it
    exists. Use it for a notation reference image, a code bundle, or anything
    else that should travel with the results. Missing entries are reported but
    are never fatal.

    :param config: The loaded configuration.
    :type config: dict
    :param root: Repository root.
    :type root: pathlib.Path
    :param destination: The dated archive folder.
    :type destination: pathlib.Path
    :return: Human-readable notes about what was and was not copied.
    :rtype: list
    """
    notes = []
    for relative in config.get("extra_files", []):
        source = root / relative
        if source.is_file():
            shutil.copy2(str(source), str(destination / source.name))
            notes.append(f"copied {source.name}")
        else:
            notes.append(f"not found, skipped: {relative}")
    return notes


def write_manifest(destination, config, results, root, label, timing, notes):
    """
    Writes ``manifest.json`` recording exactly what this run did.

    This is what makes an archived run self-describing months later: the commit,
    whether the tree was dirty, which entries ran, how long each took and what
    each produced.

    :param destination: The dated archive folder.
    :type destination: pathlib.Path
    :param config: The loaded configuration.
    :type config: dict
    :param results: Per-entry run results.
    :type results: list
    :param root: Repository root.
    :type root: pathlib.Path
    :param label: The run label.
    :type label: str
    :param timing: ``BEFORE``, ``AFTER`` or None.
    :type timing: str, optional
    :param notes: Notes from the supporting-file copy step.
    :type notes: list
    :return: Path to the written manifest.
    :rtype: pathlib.Path
    """
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "label": label,
        "timing": timing,
        "git_commit": git_commit(root),
        "git_dirty": git_is_dirty(root),
        "python": sys.version.split()[0],
        "config_path": config.get("_path"),
        "entries_run": len(results),
        "entries_passed": sum(1 for result in results if result["passed"]),
        "notes": notes,
        "results": results,
    }

    path = destination / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


# =============================================================================
# pytest -- availability flags resolved once at import
# =============================================================================

CONFIG_AVAILABLE = config_path().is_file()
DRUMSCRIPT_AVAILABLE = ds is not None


def _load_config_quietly():
    """
    Loads the config for collection-time parameterisation.

    Returns None rather than raising if the config is absent or malformed, so a
    missing file shows up as skipped tests instead of a collection error.
    """
    if not CONFIG_AVAILABLE:
        return None
    try:
        return load_config()
    except SystemExit:
        return None


_COLLECTION_CONFIG = _load_config_quietly()

AUDIO_AVAILABLE = False
if _COLLECTION_CONFIG is not None:
    _audio_root = repo_root() / _COLLECTION_CONFIG.get("audio_root", "test_audio")
    AUDIO_AVAILABLE = _audio_root.is_dir()

SINGLE_HITS = entries_of_kind(_COLLECTION_CONFIG, KIND_SINGLE_HIT) if _COLLECTION_CONFIG else []

CAN_TRANSCRIBE = AUDIO_AVAILABLE and DRUMSCRIPT_AVAILABLE

# Touches real files and runs the real pipeline, so `integration`. Not `slow`:
# single hits are under two seconds each and none needs stem separation.
pytestmark = pytest.mark.integration


def _entry_id(entry):
    """Readable pytest test id for a config entry."""
    return entry["name"]


@pytest.fixture(scope="module")
def config():
    """The loaded audio list, shared across the module."""
    if not CONFIG_AVAILABLE:
        pytest.skip(SETUP_HINT)
    return load_config()


@pytest.fixture(scope="module")
def root():
    """The repository root, used to resolve configured audio paths."""
    return repo_root()


@pytest.mark.skipif(not CAN_TRANSCRIBE, reason="needs the configured audio folder and an installed drumscript")
class TestSingleHitClassification:
    """
    Real transcription runs on isolated drum and cymbal recordings.

    Each test transcribes one file and asserts the classifier named the right
    instrument. Parameterised from the config, so adding a sample there adds a
    test here with no code change.
    """

    @pytest.mark.parametrize("entry", SINGLE_HITS, ids=_entry_id)
    def test_hit_classifies_as_expected_instrument(self, entry, config, root, tmp_path):
        """An isolated drum hit must classify as that drum."""
        # Arrange
        audio = audio_path(config, entry, root)
        if not audio.is_file():
            pytest.skip(f"audio not available: {audio}")

        # Act -- output_dir keeps this out of the real output folder, per the
        # project rule against writing to the working directory.
        result = ds.transcribe(
            str(audio),
            is_rudiment="--rudiment" in entry.get("args", []),
            output_dir=str(tmp_path),
        )

        # Assert
        json_path = Path(result["json_path"])
        assert json_path.exists(), f"transcription JSON reported but not written: {json_path}"

        events = load_events(json_path)
        passed, message = check_single_hit(entry, events)
        assert passed, f"{entry['name']}: {message}"

    def test_transcribe_raises_on_missing_audio(self, tmp_path):
        """
        A missing input raises rather than failing quietly.

        Worth pinning: the CLI prints an error and still exits 0, so a failing
        file does not stop a shell chain. The Python API does not share that
        behaviour, and the runner's own checks assume it will not start.
        """
        with pytest.raises(FileNotFoundError):
            ds.transcribe(str(tmp_path / "does_not_exist.wav"), output_dir=str(tmp_path))


class TestConfig:
    """
    Guards on ``songs.json`` itself.

    These run without the audio present, because a malformed config is worth
    catching on any machine.
    """

    def test_every_single_hit_declares_an_expectation(self, config):
        """
        Every ``single_hit`` entry must say what it should classify as.

        Without this, adding a sample and forgetting ``expect`` would make the
        accuracy tests silently pass on anything.
        """
        entries = entries_of_kind(config, KIND_SINGLE_HIT)
        if not entries:
            pytest.skip("no single_hit entries configured")

        missing = [entry["name"] for entry in entries if not entry.get("expect")]
        assert not missing, f"single_hit entries with no 'expect': {missing}"

    def test_entry_names_are_unique(self, config):
        """
        Entry names must be unique.

        Names become output filenames, so a duplicate would mean two entries
        overwriting each other's transcription, and a comparison silently losing
        one of them.
        """
        names = [entry["name"] for entry in config["entries"]]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        assert not duplicates, f"duplicate entry names in config: {duplicates}"

    def test_every_entry_declares_a_known_kind(self, config):
        """Each entry must be a ``track`` or a ``single_hit``."""
        valid = {KIND_TRACK, KIND_SINGLE_HIT}
        wrong = [(entry["name"], entry.get("kind")) for entry in config["entries"] if entry.get("kind") not in valid]
        assert not wrong, f"entries with an unknown 'kind' (expected one of {sorted(valid)}): {wrong}"

    @pytest.mark.skipif(not AUDIO_AVAILABLE, reason="configured audio folder not found")
    def test_configured_audio_files_all_exist(self, config, root):
        """
        Every configured audio file must be present.

        A path that has gone stale is the worst kind of failure here: the file
        fails identically in both halves of a before/after pair, cancels out,
        and the comparison looks clean while that file contributed nothing.
        """
        missing = [entry["name"] for entry in config["entries"] if not audio_path(config, entry, root).is_file()]
        assert not missing, f"configured audio files not found: {missing}"


class TestArchivedRun:
    """
    Checks a completed run folder against today's expectations.

    Lets an archive from months ago be re-verified without re-running anything.
    Both tests skip unless the environment variable names a folder.
    """

    def test_archived_run_still_meets_expectations(self, config):
        """Every entry in the archived folder still classifies as expected."""
        folder = os.environ.get(RUN_FOLDER_ENV)
        if not folder:
            pytest.skip(f"{RUN_FOLDER_ENV} not set")

        path = Path(folder)
        assert path.is_dir(), f"not a directory: {path}"

        results = verify_run_folder(config, path)
        failures = [(name, message) for name, passed, message in results if not passed]

        report = "\n".join(f"  {name}: {message}" for name, message in failures)
        assert not failures, f"{len(failures)} of {len(results)} entries failed in {path}:\n{report}"

    def test_manifest_is_readable_when_present(self):
        """
        A folder written by the runner carries a readable manifest.

        Folders assembled by hand before the runner existed have none, so an
        absent manifest is not a failure. Only a corrupt one is.
        """
        folder = os.environ.get(RUN_FOLDER_ENV)
        if not folder:
            pytest.skip(f"{RUN_FOLDER_ENV} not set")

        manifest_path = Path(folder) / "manifest.json"
        if not manifest_path.is_file():
            pytest.skip("no manifest.json (run folder assembled by hand)")

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            pytest.fail(f"manifest.json is not valid JSON: {exc}")

        for key in ("generated_at", "git_commit", "results"):
            assert key in manifest, f"manifest.json missing '{key}'"


# =============================================================================
# Command line
# =============================================================================


def cmd_run(args):
    """
    Runs the configured audio and archives the results.

    :param args: Parsed command-line arguments.
    :type args: argparse.Namespace
    :return: Process exit code.
    :rtype: int
    """
    started_at = datetime.now()

    say(f"Loading config from {args.config or config_path()}", prefix="")
    config = load_config(args.config)
    root = repo_root()
    entries = select_entries(config, args.only, args.kind)

    if not entries:
        print("[ERROR] No entries selected.")
        return 2

    say(f"Repository root: {root}", prefix="")
    dirty = " (dirty tree)" if git_is_dirty(root) else ""
    say(f"Commit: {git_commit(root)}{dirty}", prefix="")
    say(f"Selected {len(entries)} of {len(config['entries'])} configured entries", prefix="")
    print()

    say("Pre-flight: checking every audio file exists...", prefix="")
    problems = preflight(config, entries, root)
    if problems:
        print("[ERROR] Pre-flight failed. Nothing was run:")
        for problem in problems:
            print(f"  - {problem}")
        return 2
    say(f"Pre-flight OK: all {len(entries)} files present", prefix="")
    print()

    archive_dir = root / config.get("archive_dir", "outputs/regression_runs")
    folder_tag = config.get("folder_tag")
    scope = describe_scope(config, entries, args.only, args.kind)

    if args.dry_run:
        print("[DRY RUN] Would run, in order:")
        for position, entry in enumerate(entries, start=1):
            flags = " ".join(entry.get("python_flags", []) + entry.get("args", []))
            print(f"  [{position:>2}/{len(entries)}] {entry['name'][:52]:<54} {entry['file']} {flags}".rstrip())
        print()
        print(f"[DRY RUN] Would archive to: {build_folder_name(archive_dir, args.label, args.timing, folder_tag, scope)}")
        return 0

    log_path = root / config.get("run_log", "drumscript/logs/drumscript.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    say(f"Appending transcription output to {log_path}", prefix="")
    print()

    results = []
    with open(log_path, "a", encoding="utf-8") as log_handle:
        stamp = f"{datetime.now():%Y-%m-%d %H:%M:%S}"
        log_handle.write(f"\n{'=' * 78}\nREGRESSION RUN  {stamp}  label={args.label}  timing={args.timing or '-'}\n{'=' * 78}\n")

        total = len(entries)
        for position, entry in enumerate(entries, start=1):
            counter = f"[{position:>2}/{total}]"
            kind_note = "single hit" if entry.get("kind") == KIND_SINGLE_HIT else "track"
            say(f"{counter} running  {entry['name'][:52]:<54} ({kind_note})")

            result = run_entry(config, entry, root, log_handle, args.tee, args.timeout)
            results.append(result)

            status = "PASS" if result["passed"] else "FAIL"
            say(f"{counter} [{status}]  {result['name'][:52]:<54} {result['duration_s']:>7.2f}s  {result['message']}")

    failures = [result for result in results if not result["passed"]]
    elapsed = (datetime.now() - started_at).total_seconds()
    print()
    say(f"{len(results) - len(failures)}/{len(results)} entries passed in {elapsed:.1f}s total.", prefix="")

    if args.no_archive:
        say(f"Outputs left in {config.get('output_dir', 'outputs')}/ (--no-archive).", prefix="")
        return 1 if failures else 0

    print()
    if not args.no_backup:
        say("Running scripts/backup.sh to regenerate the code bundle...", prefix="")
        ok, message = run_backup(root, args.timing, args.label, 1)
        say(f"[{'OK' if ok else 'WARN'}] backup.sh: {message}")

    destination = build_folder_name(archive_dir, args.label, args.timing, folder_tag, scope)
    say(f"Archiving to {destination.name} ...", prefix="")
    archived = archive_outputs(config, entries, root, destination, args.keep_outputs)
    say(f"moved {archived} output files", prefix="    ")

    notes = copy_supporting_files(config, root, destination)
    for note in notes:
        say(note, prefix="    ")

    manifest_path = write_manifest(destination, config, results, root, args.label, args.timing, notes)
    say(f"wrote {manifest_path.name}", prefix="    ")

    print()
    print("Archived to:")
    print(f"  {destination}")

    if failures:
        print()
        print("[FAIL] Some entries did not pass. Do not treat this run as a clean baseline.")
        return 1

    print()
    print("Next: compare against a previous run with")
    print(f"  python3 {Path(__file__).name} compare <previous_folder> {destination}")
    return 0


def cmd_compare(args):
    """
    Compares two run folders and prints the report.

    :param args: Parsed command-line arguments.
    :type args: argparse.Namespace
    :return: Process exit code.
    :rtype: int
    """
    before_run = load_run(args.before)
    after_run = load_run(args.after)

    results, only_before, only_after = compare_runs(before_run, after_run, args.feature_eps)
    report = build_report(results, only_before, only_after, args.before, args.after, args.show_onsets, args.quiet_identical, args.markdown)
    print(report)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
        print(f"[OK] Report written to {args.out}")

    if only_before or only_after:
        return 2
    return 1 if any(entry_changed(res) for res in results.values()) else 0


def cmd_verify(args):
    """
    Verifies an archived run folder against the configured expectations.

    :param args: Parsed command-line arguments.
    :type args: argparse.Namespace
    :return: Process exit code.
    :rtype: int
    """
    config = load_config(args.config)
    results = verify_run_folder(config, args.folder)

    for name, passed, message in results:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name[:54]:<56} {message}")

    failures = [item for item in results if not item[1]]
    print()
    print(f"{len(results) - len(failures)}/{len(results)} entries passed.")
    return 1 if failures else 0


def build_parser():
    """
    Builds the argument parser.

    Kept as its own function so tests can import the real parser rather than
    mirror it.

    :return: The configured parser.
    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        description="Run, compare and verify DrumScript transcription regression checks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the configured audio and archive the results")
    run.add_argument("--label", required=True, help="Descriptive part of the archive folder name")
    run.add_argument("--timing", choices=["BEFORE", "AFTER"], default=None, help="Mark this run as BEFORE or AFTER a change")
    run.add_argument("--only", action="append", default=[], help="Run only this entry name (repeatable)")
    run.add_argument("--kind", choices=[KIND_TRACK, KIND_SINGLE_HIT], default=None, help="Run only entries of this kind")
    run.add_argument("--tee", action="store_true", help="Stream each entry's output to the terminal as well as the log")
    run.add_argument("--no-backup", action="store_true", help="Skip scripts/backup.sh")
    run.add_argument("--no-archive", action="store_true", help="Run and verify, but do not create a dated folder")
    run.add_argument("--keep-outputs", action="store_true", help="Copy rather than move, leaving the output folder populated")
    run.add_argument("--config", type=Path, default=None, help="Use a different config file")
    run.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_ENTRY_TIMEOUT_S,
        help=f"Seconds before one entry is treated as hung and killed (default: {DEFAULT_ENTRY_TIMEOUT_S})",
    )
    run.add_argument("--dry-run", action="store_true", help="Print what would run and change nothing")
    run.set_defaults(func=cmd_run)

    compare = sub.add_parser("compare", help="Compare two run folders")
    compare.add_argument("before", type=Path, help="Run folder from BEFORE the change")
    compare.add_argument("after", type=Path, help="Run folder from AFTER the change")
    compare.add_argument("--markdown", action="store_true", help="Emit markdown (for pasting into a PR)")
    compare.add_argument("--out", type=Path, default=None, help="Also write the report to this file")
    compare.add_argument("--show-onsets", type=int, default=15, help="Max changed onsets to list per entry (default: 15)")
    compare.add_argument("--feature-eps", type=float, default=1e-9, help="Ignore feature moves smaller than this")
    compare.add_argument("--quiet-identical", action="store_true", help="Omit entries that did not change")
    compare.set_defaults(func=cmd_compare)

    verify = sub.add_parser("verify", help="Check an archived run folder against the configured expectations")
    verify.add_argument("folder", type=Path, help="Run folder to verify")
    verify.add_argument("--config", type=Path, default=None, help="Use a different config file")
    verify.set_defaults(func=cmd_verify)

    return parser


def main(argv=None):
    """
    Command-line entry point.

    :param argv: Arguments to parse; defaults to ``sys.argv[1:]``.
    :type argv: list
    :return: Process exit code.
    :rtype: int
    """
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
