# Contributing to `DrumScript`
<!--date_created: thurs-03-jul-2025 -->
<!--date_updated: sun-11-jan-2026 -->



First off, thank you for considering contributing to `DrumScript`! :)

We're thrilled to have you join us. Whether you are a drummer, a Python developer, a sound engineer, or all three, your help is vital to making this the standard open-source tool for drum transcription.

This document outlines the project's philosophy, how to set up your environment, and how we manage our releases.

> **Code of Conduct**
> Please note that this project is released with a contributor **`Code of Conduct`**. By participating in this project, you agree to abide by its terms.

---

## The "Deterministic" Mission
*Why we aren't using deep learning (for now).*

**DrumScript is pivoting to a rule-based, deterministic classification engine.**

**Why?**
* **Transparency:** We don't want a "Black Box" that guesses. We want to understand *why* a sound is classified as a Snare vs. a Tom based on physics (frequencies, decay, energy).
* **Hackability:** It is much easier for a contributor to tweak a threshold value in a config file than it is to retrain a massive dataset on a GPU.
* **Precision:** By defining the acoustic "fingerprint" of drum hits mathematically, we aim for predictable, reproducible results.

> **Where we need you:**
We have the skeleton (stem splitting, tempo detection, onset detection). We need help building the **Classifier Logic**. If you can look at a spectrogram and say *"That's a ride cymbal because it has high energy above 8kHz and a long decay,"* we need you to help us write that rule into code!

---


##  How to Get Started
### 1. Prerequisites

Before you begin, ensure you have the following installed:

* **Git:** For version control.
* **Python 3.10+:** The language `DrumScript` is built with.
* **`uv`:** A fast Python package installer and dependency resolver.
    * *Install:* `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux) or see [uv docs](https://astral.sh/uv/install/).
* **`ffmpeg`:** Required for audio processing.
> **We provide a utility script for installing `ffmpeg` in [`.drumscript/utils/ffmpeg_installer.py`](drumscript/utils/ffmpeg_installer.py)**. See also **[`ffmpeg` guidance](https://www.ffmpeg.org/download.html)**

### 2. Clone the Repository

Start by cloning the `DrumScript` repository to your local machine:

```zsh
git clone [https://github.com/DrumScript/DrumScript.git](https://github.com/DrumScript/DrumScript.git)
cd DrumScript
```

### 3. Set Up Your Development Environment

We use `uv` to manage our virtual environment and dependencies. We recommend installing the package in **editable mode** so changes you make are immediately reflected when you run tests.

```zsh
# 1. Create a virtual environment
uv venv

# 2. Activate the virtual environment
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# 3. Install dependencies AND the package in editable mode
uv pip install -e .

# 4. Install pre-commit hooks (for automatic formatting)
uv pip install pre-commit
pre-commit install
```

**Install dependencies AND the package in editable mode**

Install [test] dependencies

```zsh
uv pip install -e ".[test]"
```

### 4. Verify Setup

Run the local interface test to ensure your environment handles imports correctly:

```zsh
uv run python local_tests/drumscript_lite/test_local_interface.py
```

---

## Development Workflow

We follow a **Feature Branch** workflow. We generally do not commit directly to `main`.

1.  **Sync with Main:**
    ```zsh
    git checkout main
    git pull origin main
    ```
2.  **Create a Branch:**
    Name it descriptively (`feature/`, `fix/`, `docs/`).
    ```zsh
    git checkout -b feature/improve-hihat-detection
    ```
3.  **Code & Test:**
    Make your changes. Run tests frequently.
4.  **Publish on remote:**
    Push your local branch to the remote

    ```zsh
    push origin -u feature/improve-hihat-detection
    ```
5. **When you have made your first commit on the branch, [open a PR](https://github.com/DrumScript/DrumScript/compare)**

6. **When you feel you are ready to merge your changes into main branch *request a review from a drumscript-admin***

---

## Version Management & Release Strategy

We strive to keep `DrumScript` stable for users. To achieve this, we follow **Semantic Versioning (SemVer)** and a grouped release strategy.

### How we number releases (X.Y.Z)

  * **Major (X.0.0):** Breaking changes. (e.g., Changing the function name from `stem_split` to `extract_stems`).
  * **Minor (0.Y.0):** New features that don't break existing code. (e.g., Adding a new detection algorithm for Crash Cymbals).
  * **Patch (0.0.Z):** Bug fixes and documentation updates.

### When do we release?

We do **not** publish a new PyPI package for every single bug fix.

1.  **Development:** Fixes and features are merged into `main` continuously.
2.  **Staging:** When enough fixes (or a significant feature) are ready, we tag a **Release Candidate** (e.g., `v0.1.2-rc1`) for testing.
3.  **Release:** Once validated, we publish the official version.

**For Contributors:**
You don't need to worry about bumping the version number in `pyproject.toml`. The maintainers will handle versioning upon release. Just ensure your PR description clearly states *what* you fixed so we can classify it (Patch vs Minor).

---

## Coding Standards

To maintain consistency, please adhere to the following:

  * **Python Style:** Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/).
  * **Formatting:** We use `ruff`. The pre-commit hooks set up in step 3 will handle this automatically.
      * *Manual run:* `uv run ruff format .`
  * **Docstrings:** Every function must have a docstring.**`DrumScript` uses the [`Sphinx reStructuredText`](https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html) DocString convention**. All contributed code must follow this.

---

## Reporting Issues

If you find a bug, please open an issue on the [GitHub Issues page](https://github.com/DrumScript/DrumScript/issues).

  * **Be Specific:** "The code crashed" is hard to fix. "The code crashed with `ValueError` when inputting a 48kHz WAV file" is helpful!

  * **Provide Context:** Tell us your OS (Mac/Windows/Ubuntu/Linux) and Python version.

---

## Questions & Support

If you have questions, feel free to reach out at **[hello.drumscript@gmail.com](mailto:hello.drumscript@gmail.com)**.

Thank you for helping us build `DrumScript`! 🥁🚀 :D





---
<!--END-->