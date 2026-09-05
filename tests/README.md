# DrumScript Tests

<!--date_added:weds-29-apr-2026-->
<!--date_updated:sun-09-aug-2026-->

This directory contains the pytest test suite for `DrumScript`.

---
## Repository Tree (`tests/`)

```zsh
DrumScript/
├── pyproject.toml                          ← project root (test config here)
└── tests/
    ├── __init__.py
    ├── README.md                           ← you are here
    ├── conftest.py                         ← shared fixtures
    ├── fixtures/
    │   └── audio/                          ← real audio files
    │                                         (empty; synthesised in conftest)
    ├── unit/                               ← fast, no I/O, no subprocess
    │   ├── __init__.py
    │   ├── test_audio_loader.py            ← 13 tests
    │   ├── test_benchmarks_run.py          ←  6 tests (added v0.1.6,{PR#273})
    │   ├── test_classify.py                ← 24 tests
    │   ├── test_cli_args.py                ←  4 tests (added v0.1.6)
    │   ├── test_deprecation_warnings.py    ← 13 tests (added v0.1.6)
    │   ├── test_helpers.py                 ← 24 tests
    │   ├── test_idmt_dataset.py            ←  4 tests  (added v0.1.6,{PR#273})
    │   ├── test_onset_detector.py          ←  7 tests
    │   ├── test_stem_splitter_helpers.py    ← 17 tests (includes regression)
    │   ├── test_tempo_detector.py          ←  6 tests
    │   └── test_transcribe.py              ← 20 tests
    └── integration/                        ← real files; Demucs/ffmpeg where noted
        ├── __init__.py
        ├── test_stem_splitter_real.py      ←  8 tests (all require Demucs)
        └── test_transcribe_real.py         ← 15 tests (added v0.2.0)
                                                12 need no Demucs, 3 do
```

> **Note:** Counts above reflect pytest's collected case count, ie parametrised
> tests are expanded into their individual cases. Unit total: **138** cases
> across **11** files. 
> Integration total: **23** cases across **2** files.

> **Not all integration tests are slow.** The 12 Demucs-free cases in
> `test_transcribe_real.py` are marked `integration` but **not** `slow`, so they
> still run under `pytest -m "not slow"` — and therefore in CI. They give the
> v0.2.0 `_TranscribeResult` change real end-to-end coverage (files genuinely
> written to disk) without needing model weights. Expect them to add roughly
> 30 seconds to a "fast" run.


---

## Setup

`DrumScript` uses **[`uv`](https://docs.astral.sh/uv/)** to manage dependencies. Install it via:

- **macOS (Homebrew):** [`brew install uv`](https://formulae.brew.sh/formula/uv)
- **macOS / Linux:** [`curl -LsSf https://astral.sh/uv/install.sh | sh`](https://docs.astral.sh/uv/getting-started/installation/)
- **Windows:** [`curl -LsSf https://astral.sh/uv/install.sh | sh`](https://docs.astral.sh/uv/getting-started/installation/#__tabbed_1_2)

There is no `requirements.txt`. All dependencies are declared in **[`pyproject.toml`](../pyproject.toml)**, with all `dev` dependencies in a single group.

To get set up:

```zsh
uv venv && source .venv/bin/activate && uv sync --extra dev
```

That creates the virtual environment, activates it, and installs all dev dependencies. To verify what's installed:

```zsh
uv pip list
```

> **Note:** `uv pip install -e ".[dev]"` (with the `-e` editable flag) also works but has shown caching issues in practice. The `uv sync` form above is recommended.

The `[dev]` group installs:

1. Documentation tooling (`shibuya`, `myst-parser`)
2. Testing suite (`pytest`, `pytest-cov`)
3. Jupyter support (`ipykernel`) — convenience only
4. Benchmarking (`mir_eval` — for benchmark runners under `benchmarks/`)

> **Note:** `ipykernel`/Jupyter is a convenience package; **`.ipynb` files must never be committed**. PRs containing `.ipynb` files (or their metadata) will not be reviewed until they are removed.

---

## Quick start

> * Install [`dev`] dependencies:  `uv sync --extra dev`
> **Note**: You can also use `uv pip install -e ".[dev]"` (ie using the `-e: editable` flag) but experience shows that this can be problematic with cacheing.  It is recommended to use `uv sync...` version

> * Check which dependencies have actually been installed: `uv pip list`

**
```zsh
# Run all fast tests (default development loop):
pytest -m "not slow"

# Run a single test file:
pytest tests/unit/test_audio_loader.py

# Run a single test:
pytest tests/unit/test_audio_loader.py::TestNormaliseAudio::test_normalises_to_unit_peak

# Show stdout from passing tests (handy for debugging fixtures):
pytest -s

# Run with a coverage report:
pytest --cov=drumscript --cov-report=term-missing
```

---

## Running the suite

The recommended way is via the runner script:

```zsh
./scripts/run_tests.sh                  # All unit tests, one file at a time
./scripts/run_tests.sh --all-at-once    # Single pytest invocation
./scripts/run_tests.sh --integration    # Include integration tests
./scripts/run_tests.sh --everything     # Unit + integration in one pytest call
./scripts/run_tests.sh --help           # Show all options
```

Per-file logs are written to `scripts/logs/tests/<timestamp>/`.

For one-off direct pytest runs, see [Quick start](#quick-start).

---

## Markers

Tests can be tagged with custom markers (defined in `pyproject.toml`):

- `@pytest.mark.slow` — skip by default during development
- `@pytest.mark.integration` — touches real files, not mocked

The two are independent, which matters. A test can be `integration` without
being `slow`: it does real work (real audio, real file writes) but finishes in
seconds because it never invokes Demucs. Those still run in the fast loop.

| Marks | Example | Runs under `-m "not slow"`? |
|---|---|---|
| neither | `tests/unit/*` | Yes |
| `integration` only | `test_transcribe_real.py` (12 cases) | Yes |
| `integration` + `slow` | `test_stem_splitter_real.py`, and 3 cases in `test_transcribe_real.py` | No |

Tests needing the `demucs` CLI also carry a `skipif` so they degrade to a clean
skip rather than a noisy failure when it isn't on `PATH`.

Run only fast tests:

```zsh
pytest -m "not slow"
```

Run only integration tests:

```zsh
pytest -m integration
```
---

## Adding a new test file


1. Place it under `tests/unit/` if everything heavy is mocked, or
   `tests/integration/` if it touches real files, audio, or subprocesses.
   If it's an integration test that does *not* need Demucs, mark it
   `integration` only — leave `slow` off so it still runs in CI.
2. Name the file `test_*.py`. The runner script auto-discovers anything
   matching this pattern; no extra wiring required.
3. Group related tests in a `Test*` class with `test_*` methods.
4. Reuse fixtures from `conftest.py` where possible. Only add new ones to
   `conftest.py` if multiple files will use them.

---
## Style conventions

- One concept per test. Many small tests > one mega-test.
- Use the **Arrange / Act / Assert** structure inside each test.
- Use the `tmp_path` fixture for any file output. **Never** write to the
  working directory or hardcoded paths.
- Use `pytest.approx(...)` for float comparisons. Direct `==` on floats
  is unreliable.
- Use `pytest.raises(...)` for expected exceptions.
- Use `pytest.warns(...)` for expected warnings (e.g. deprecation tests).

---

## Regression tests

A handful of tests exist specifically to lock in behaviour that was previously
inconsistent or ambiguous. These shouldn't be removed without a deliberate
decision:

- `test_cli_args.py` — locks in `--full-song` (hyphenated) as the canonical
  CLI flag after the v0.1.6 rename from `--full`.
- `test_deprecation_warnings.py` — locks in the `full` → `verbose` shim
  behaviour on the Python API. Delete (or flip) this when `full` is removed
  in v1.0.0.
- `test_transcribe.py::TestTranscribeWrittenPaths` — locks in that
  `transcribe()` reports only the files `build_score()` actually wrote. Before
  v0.2.0 all three paths were returned unconditionally, including files that
  failed to write.
- `test_transcribe_real.py::TestCliStemFlagsReal::test_drumless_produces_backing_track_and_no_score`
  — locks in the v0.2.0 fix where `--drumless` / `--all-stems` / `--mute` were
  only reachable from inside an `except` handler, so they silently did nothing
  on the happy path. Requires Demucs.

---

## Known issues

None

---

<!--END-->