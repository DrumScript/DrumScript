# DrumScript Tests

<!--date_added:weds-29-apr-2026-->
<!--date_updated:thurs-30-apr-2026-->

This directory contains the pytest test suite for `DrumScript`.

---
## Repository Tree (Testing)

```zsh
DrumScript/
├── pytest.ini                              ← project root
└── tests/
    ├── __init__.py                         ← empty
    ├── README.md                           ← orientation guide
    ├── conftest.py                         ← shared fixtures
    ├── fixtures/audio/                     ← (empty for now)
    └── unit/
        ├── __init__.py                     ← empty
        ├── test_audio_loader.py            ← ~14 tests
        ├── test_helpers.py                 ← ~16 tests
        └── test_stem_splitter_helpers.py   ← ~14 tests, includes regression
```

--

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

> **Note:** `ipykernel`/Jupyter is a convenience package; **`.ipynb` files must never be committed**. PRs containing `.ipynb` files (or their metadata) will not be reviewed until they are removed.

--
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


## Layout

```
DrumScript/
├── pytest.ini                              ← project root
└── tests/
    ├── __init__.py
    ├── README.md                           ← you are here
    ├── conftest.py                         ← shared fixtures (auto-discovered)
    ├── fixtures/
    │   └── audio/                          ← real audio files
    │                                         (empty; synthesised in conftest)
    ├── unit/                               ← fast, no I/O, no subprocess
    │   ├── __init__.py
    │   ├── test_audio_loader.py
    │   ├── test_helpers.py
    │   ├── test_stem_splitter_helpers.py
    │   ├── test_tempo_detector.py
    │   ├── test_onset_detector.py
    │   └── test_classify.py
    └── integration/                        ← real Demucs / ffmpeg / files (slow)
        ├── __init__.py
        └── test_stem_splitter_real.py
```

## Markers

Tests can be tagged with custom markers (defined in `pytest.ini`):

- `@pytest.mark.slow` — skip by default during development
- `@pytest.mark.integration` — requires Demucs/ffmpeg installed

Run only fast tests:

```zsh
pytest -m "not slow"
```

Run only integration tests:

```zsh
pytest -m integration
```

## Adding a new test file


1. Place it under `tests/unit/` (or `tests/integration/` if it's slow).
2. Name the file `test_*.py`.
3. Group related tests in a `Test*` class with `test_*` methods.
4. Reuse fixtures from `conftest.py` where possible. Only add new ones to
   `conftest.py` if multiple files will use them.


## Style conventions

- One concept per test. Many small tests > one mega-test.
- Use the **Arrange / Act / Assert** structure inside each test.
- Use the `tmp_path` fixture for any file output. **Never** write to the
  working directory or hardcoded paths.
- Use `pytest.approx(...)` for float comparisons. Direct `==` on floats
  is unreliable.
- Use `pytest.raises(...)` for expected exceptions.

## Known issues

None

---

<!--END-->