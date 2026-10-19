# Transcription regression checks

<!--date_added:sun-18-oct-2026-->
<!--date_updated:mon-19-oct-2026-->

Run a fixed set of audio through DrumScript, archive the results, and compare against
last time. One script, one config, three jobs.

Point it at your own recordings. Nothing here is tied to any particular audio.

---

## Contents

- [What it does](#what-it-does)
- [Setup](#setup)
- [Running it](#running-it)
- [The config](#the-config)
- [Two kinds of check](#two-kinds-of-check)
- [Reading a comparison](#reading-a-comparison)
- [Exit codes](#exit-codes)
- [Design notes](#design-notes)

---

## What it does

| Job | Command |
|---|---|
| Run the audio and archive the results | `run` |
| Compare two archives | `compare` |
| Re-check an old archive against today's expectations | `verify` |
| Assert that single hits still classify correctly | `pytest` |

All four live in `test_regression.py`. It is a pytest module *and* a command-line tool:
importing it defines the tests, running it gives you the runner and the comparator.

### Why one file

The four jobs share a single list of audio files. Split across modules, the runner and
the assertions could drift apart, and a change would pass in pytest while the archive
recorded something different. One file, one config, no drift.

---

## Setup

```zsh
cp tests/regression/songs.example.json tests/regression/songs.json
```

Then edit `songs.json` to point at your own audio.

`songs.json` is **gitignored** - it names files on your machine. `songs.example.json` is
committed, so a fresh clone always has a template.

Without `songs.json`, the tests skip and the CLI prints these instructions. Nothing
breaks.

Add to `.gitignore`:

```gitignore
tests/regression/songs.json
```

### Nothing else to configure

The `integration` marker it uses is already defined in `pyproject.toml`. No new markers,
no new dependencies - the script is standard library only, apart from pytest and
DrumScript itself.

---

## Running it

### The main loop

```zsh
# before your change
python3 tests/regression/test_regression.py run --label <what_you_are_changing> --timing BEFORE

# ...make the change...

# after
python3 tests/regression/test_regression.py run --label <what_you_are_changing> --timing AFTER

# compare the two folders it printed
python3 tests/regression/test_regression.py compare <before_folder> <after_folder>
```

### Faster feedback

```zsh
# what would run, without running it. Catches a missing file in seconds.
python3 tests/regression/test_regression.py run --label check --dry-run

# single hits only, no archiving
python3 tests/regression/test_regression.py run --label quick --kind single_hit --no-archive --no-backup

# one entry
python3 tests/regression/test_regression.py run --label one --only example_kick --no-archive --no-backup

# watch the transcription as it goes, instead of a silent wait
python3 tests/regression/test_regression.py run --label watch --tee
```

### As pytest

```zsh
pytest tests/regression/ -v
pytest -m "not slow"        # included; skips without songs.json
```

### Re-check an old archive

```zsh
python3 tests/regression/test_regression.py verify <run_folder>
```

Or through pytest:

```zsh
DRUMSCRIPT_REGRESSION_RUN_FOLDER=<run_folder> pytest tests/regression/ -k Archived
```

### `run` flags

| Flag | Effect |
|---|---|
| `--label TEXT` | Descriptive part of the folder name (**required**) |
| `--timing BEFORE\|AFTER` | Folded into the folder name and passed to `backup.sh` |
| `--only NAME` | Run just this entry; repeatable |
| `--kind track\|single_hit` | Run only entries of that kind |
| `--tee` | Stream each entry's output to the terminal as well as the log |
| `--no-backup` | Skip `scripts/backup.sh` |
| `--no-archive` | Run and verify, but create no dated folder |
| `--keep-outputs` | Copy rather than move, leaving the output folder populated |
| `--config PATH` | Use a different config file |
| `--dry-run` | Print what would run, change nothing |

### `compare` flags

| Flag | Effect |
|---|---|
| `--markdown` | Emit markdown, for pasting into a PR |
| `--out FILE` | Also write the report to a file |
| `--show-onsets N` | Max changed onsets to list per entry (default 15) |
| `--feature-eps F` | Ignore feature moves smaller than this |
| `--quiet-identical` | Omit entries that did not change |

---

## The config

Each entry:

| Field | Applies to | Meaning |
|---|---|---|
| `name` | both | Output basename. Must be unique and match the audio file's stem |
| `file` | both | Path relative to `audio_root`, or absolute |
| `kind` | both | `track` or `single_hit` |
| `python_flags` | both | Flags for the interpreter, e.g. `["-W", "ignore", "-B"]` |
| `args` | both | Flags for `drumscript.main`, e.g. `["--rudiment"]` |
| `expect` | `single_hit` | The exact instruments list expected |
| `expect_events` | `single_hit` | Exact onset count expected, usually 1 |
| `min_events` | `track` | A floor, to catch a track producing nothing |

Valid instrument labels: `kick`, `snare`, `hi_hat_closed`, `hi_hat_open`, `low_tom`,
`mid_tom`, `high_tom`, `crash`, `ride`.

Top-level keys control `audio_root`, `output_dir`, `archive_dir`, `run_log`, and
`extra_files` - a list of repo-relative files copied into every run folder, for anything
you want travelling beside the results.

---

## Two kinds of check

**A `track` has no known-correct answer.** Nobody can say what the right 1,500 events
are for a seven-minute song. So a track is **compared** against a previous run, never
asserted. The only automatic check is `min_events`, which catches a track silently
producing nothing.

**A `single_hit` does have a known answer.** A recording of one kick drum must classify
as `kick`. These are **asserted** - real pass/fail, and what catches a threshold change
breaking detection without anyone reading a diff.

If you do not know what a file should produce, make it a `track`. It will be compared
rather than asserted against a label you had to guess.

---

## Reading a comparison

```
Entry                     Onsets  Relabel FeatOnly  Label changes
track_one                   1550      265        0  kick 412->598 (+186)
track_two                    158        1        0  kick 59->60 (+1)
example_kick                   1        0        0  -
```

Then the onsets themselves:

```
80.805s  hi_hat_closed -> kick, hi_hat_closed
87.307s  crash         -> kick, crash
```

Read that carefully: the kick is being **added alongside** existing labels, not replacing
them. A relabel that adds a part behaves very differently from one that swaps a part, and
only the per-onset view tells them apart.

### Onsets versus classification

Onsets are paired by position. If the two runs produced different onset counts, pairing
is meaningless, so the entry is flagged and only aggregate figures are reported.

That distinction is the point: counts holding steady while labels change means the
**classifier** moved. Counts changing means **onset detection** moved. Very different
problems.

### Old archives work

`compare` and `verify` read any folder containing `*_transcription.json`, including
archives made long before this script existed. No migration.

---

## Exit codes

**`run`**

| Code | Meaning |
|---|---|
| `0` | Every entry ran and passed |
| `1` | At least one entry failed to run or failed its expectation |
| `2` | Setup problem - missing audio or config. Nothing was run |

**`compare`**

| Code | Meaning |
|---|---|
| `0` | No differences |
| `1` | Differences found |
| `2` | Folders not comparable (different entry sets) |

**`verify`**

| Code | Meaning |
|---|---|
| `0` | Every entry met its expectations |
| `1` | At least one did not |

---

## Design notes

### It does not trust exit codes

`drumscript.main` prints errors but still exits 0, so a failing file does not stop a
shell chain of `&&`. Worse, a file that fails the same way in *both* halves of a
before/after pair cancels out: the comparison looks clean while that file contributed
nothing.

So the runner checks every audio file exists **before** running anything, and afterwards
confirms the `.json`, `.pdf` and `.mid` were actually written.

### It compares JSON, not the log

`drumscript.log` records `Classified 1550 events`. The transcription JSON records *which*
1,550 and the physics behind each:

```json
{"time_sec": 0.928, "instruments": ["snare", "hi_hat_closed"],
 "debug_features": {"peak_freq": 172.2, "lfer": 0.017, "hfer": 0.704, ...}}
```

That is the difference between `kick 412 -> 598 (+186)` and two columns of text to read
by eye.

### The runner uses the CLI; the tests use the Python API

Not an oversight. The runner reproduces a command a person would type, so a regression in
argument handling or the CLI's own error paths is caught too, and each entry gets its own
process so one crash does not end the run.

The pytest assertions call `ds.transcribe()` with `output_dir` set to `tmp_path` instead.
That honours the project rule against writing to the working directory, leaves the real
output folder untouched, and gets a proper `FileNotFoundError` instead of a silent exit 0.

### Not the same as "regression tests" in `tests/README.md`

That section means individual pytest tests locking in previously-fixed behaviour, living
in `unit/` and `integration/`. This folder is a before/after comparison harness. Same
word, different thing.

### `manifest.json`

Every run folder gets one: the commit, whether the tree was dirty, the Python version,
per-entry timings and results. It is what makes an archive self-describing months later.
