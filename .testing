# DrumScript Tests

<!--date_added:weds-29-apr-2026-->
<!--date_updated:weds-29-apr-2026-->

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
## Intro

`DrumScript` uses **[`uv`](https://docs.astral.sh/uv/)** for managing dependencies. You can install this using either:
- **[`brew install uv` (for Homebrew users)](https://formulae.brew.sh/formula/uv)**
- **[`curl -LsSf https://astral.sh/uv/install.sh | sh`](https://docs.astral.sh/uv/getting-started/installation/)** (MacOS/Linux)
- **[`curl -LsSf https://astral.sh/uv/install.sh | sh`](https://docs.astral.sh/uv/getting-started/installation/#__tabbed_1_2)** (Windows)

The project does not use a `requirements.txt` file. All dependencies are declared in **[`pyproject.toml`](../pyproject.toml)**. For efficiency all `dev` dependencies are stored in the **same dependency group**. 

This simplifies contributing because it means you only need to run `uv venv && source .venv/bin/activate && uv sync --extra dev` to a) create a virtual env through uv, activate the venv, install dev dependencies. Check which dependencies have actually been installed: `uv pip list`

> **Note:** You can also use `uv pip install -e ".[dev]"` (ie using the `-e: editable` flag) but experience shows that this can be problematic with cacheing.  It is recommended to use `uv sync...` version

The [`dev`] installs the following packages for contributing to `DrumScript`

1) Technical documentation (`shibuya`, `myst-parser`) <!--TO DO: Add in links to actual pages once first release is done-->
2) Complete unit testing suite (`pytest`, `pytest-cov`)
3) Jupyter notebooks (for those who would like to use) (`ipykernel`)

> **Note**: `ipykernel`/`Jupyter` is added as a **courtesy package**, however  **`.ipynb` files should never be committed**. Any PR requests raised that contain either Jupyter/`.ipynb` files, or metadata files, will **not be reviewed until they have been removed**

--
## Quick start

* Install [`dev`] dependencies: 

`uv sync --extra dev`

> **Note**: You can also use `uv pip install -e ".[dev]"` (ie using the `-e: editable` flag) but experience shows that this can be problematic with cacheing.  It is recommended to use `uv sync...` version

* Check which dependencies have actually been installed:

`uv pip list`


```zsh

# Run everything (fast tests only):
pytest -m "not slow"

# Run a single test file:
pytest tests/unit/test_audio_loader.py

# Run a single test:
pytest tests/unit/test_audio_loader.py::TestNormaliseAudio::test_normalises_to_unit_peak

# Show output even from passing tests (handy for debugging fixtures):
pytest -s

# Generate a coverage report (requires pytest-cov):
uv pip install pytest-cov
pytest --cov=drumscript --cov-report=term-missing
```

## Layout

```
tests/
├── conftest.py              ← shared fixtures (auto-discovered)
├── fixtures/audio/          ← real audio files (currently empty;
│                              everything is synthesised in conftest)
├── unit/                    ← fast, no I/O, no subprocess
│   ├── test_audio_loader.py
│   ├── test_helpers.py
│   └── test_stem_splitter_helpers.py
└── integration/             ← real Demucs / ffmpeg / files
    └── (to be added)
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

1. Put it under `tests/unit/` (or `tests/integration/` if it's slow).
2. Name the file `test_*.py`.
3. Inside, group related tests in a `Test*` class with `test_*` methods.
4. Reuse fixtures from `conftest.py` where possible. Add new ones to
   `conftest.py` only if multiple files will use them.

## Style conventions

- Each test does one thing. Many small tests > one mega-test.
- Use the **Arrange / Act / Assert** structure inside each test.
- Use `tmp_path` for any file output. **Never** write to the working
  directory or hardcoded paths.
- Use `pytest.approx(...)` for float comparisons. Direct `==` on floats
  is unreliable.
- Use `pytest.raises(...)` for expected exceptions.

## Known issues

- `test_helpers.py::TestGetNoteDurationName` will fail until the
  `DURATION_*` constants are uncommented in
  `drumscript/notation_generator/constants.py`. See that file's
  docstring for the fix.

---

<!--END-->