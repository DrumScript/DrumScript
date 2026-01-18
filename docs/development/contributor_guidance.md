# Contributing to `DrumScript`
<!--date_created: thurs-03-jul-2025 -->
<!--date_updated: tues-13-jan-2026 -->



First off, thank you for considering contributing to `DrumScript`! :)

We're thrilled to have you join us. Whether you are a drummer, a Python developer, a sound engineer, or all three, your help is vital to making this the standard open-source tool for drum transcription.

This document outlines the project's philosophy, how to set up your environment, and how we manage our releases.

> **Code of Conduct**
> Please note that this project is released with a contributor **`Code of Conduct`**. By participating in this project, you agree to abide by its terms.

---

## The Deterministic Mission
*Why we aren't using deep learning (for now).*

**DrumScript is pivoting to a rule-based, deterministic classification engine.**

**Why?**
* **Transparency:** We don't want a "Black Box" that guesses. We want to understand *why* a sound is classified as a Snare vs. a Tom based on physics (frequencies, decay, energy).
* **Hackability:** It is much easier for a contributor to tweak a threshold value in a config file than it is to retrain a massive dataset on a GPU.
* **Precision:** By defining the acoustic "fingerprint" of drum hits mathematically, we aim for predictable, reproducible results.

> **Where we need you:**
We have the skeleton (stem splitting, tempo detection, onset detection). We need help building the **Classifier Logic**. If you can look at a spectrogram and say *"That's a ride cymbal because it has high energy above 8kHz and a long decay,"* we need you to help us write that rule into code!

---
## `CODEOWNERS`

We use the GitHub tool of assigning code 'owners' to the `DrumScript` repository. In the earliest release phases for the library only founding users will be on the `CODEOWNERS` documentation; but as people volunteer to contribute we will expand the scope of the `CODEOWNERS` doc. See [GitHub CODEOWNERS guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) for more information, or if this will be your first time contributing to an open-source project.

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
git clone https://github.com/DrumScript/DrumScript.git
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

> It's best practise to run `uv sync --all-groups` even when working in `[dev]` mode on a branch or PR as this will keep all the project dependencies in sync. It will update `uv.lock`, which you commit to your branch as you would any other change

**Install dependencies AND the package in editable mode**

1. Install `[dev]` dependencies:

> For simplicity ••all•• of the dependencies you will need for contributing to `DrumScript` have been grouped into one clean dependency group, which we have called `[dev]`. You might not need everything, ie `sphinx` (which is for the documentation website), but nevertheless it simplifies the development process by having all the optionals in one place

```zsh
uv pip install -e ".[dev]"
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
    Name it descriptively (`feature/`, `fix/`, `docs/`, `build/`).
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
## Forking `DrumScript`


You can also contribute to `DrumScript` using forks [main repository](http://github.com/DrumScript/DrumScript/) on GitHub:

1. Fork the [project repository](http://github.com/DrumScript/DrumScript/): 
    * click on the 'Fork' button near the top of the page. This creates a copy of the code under your account on the GitHub server.

2. Clone this copy to your local machine:

          $ git clone --recursive git@github.com:YourLogin/DrumScript.git
          $ cd DrumScript 
          $ git pull --recurse-submodules

    These commands will clone the main `DrumScript` repository.

3. Set the upstream remote to DrumScript's repo:

          $ git remote add upstream git@github.com:DrumScript/DrumScript.git 

4. Create a new `uv` environment to install dependencies:

```zsh
uv venv
source .venv/bin/activate # activate venv
uv pip install -e . # install venv in 'editable' mode
```

> We use `uv` to manage dependencies as standard. 

<!--4. Create a new conda environment in order to install dependencies:

          $ conda create -n librosa-dev python=3.9

          $ conda env update -n librosa-dev --file .github/environment-ci.yml

          $ conda activate librosa-dev

          $ python -m pip install -e '.[tests]'-->

5. Create a branch to hold your changes:

          ```zsh
          git switch -c <TYPE/BRANCH_NAME>
          # ie `git switch -c feature/improve-
          # or 

          git checkout -b <>
          ```

   and start making changes. Never work in the `main` branch!

6. Work on this copy on your machine using Git to do the version control. You can check your modified files using:

        ```zsh
        git status
        ```

7. When you're done editing, do:

        ```zsh
        git add <PATH_NAME>
        ```
        # or 

        ```zsh
        git add . # stages all current modifications to git at once
        ```
        
        ```zsh
        git commit -m "<COMMIT-MESSAGE>"
        ```

   to record your changes in Git, then push them to GitHub with:

        ```zsh
        git push --set-upstream origin <NAME-NEW-BRANCH>
        ```

8. Go to the web page of your fork of the `DrumScript` repo, and click 'Pull request' to review your changes and add a description of what you did. 

Finally, click 'Create pull request' to send your changes to the maintainers for review. This will send an email to the committers.

(If any of the above seems like magic to you, then look up the [Git documentation](http://git-scm.com/documentation) on the web.)


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

  * **Provide Context:** Tell us your OS (Mac/Windows/Ubuntu/Linux) and Python version.  This information can be found by running the following code snippet:

  ```python
  import platform; print(platform.platform())
  import sys; print("Python", sys.version)
  import numpy; print("NumPy", numpy.__version__)
  import scipy; print("SciPy", scipy.__version__)
  import librosa; print("librosa", librosa.__version__)
  ```


It is recommended to check that your issue complies with the following rules before submitting:

-  Verify that your issue is not being currently addressed by other [issues](https://github.com/DrumScript/DrumScript/issues)
 or [pull requests](https://github.com/DrumScript/DrumScript/pulls).

-  Please ensure all code snippets and error messages are formatted in appropriate code blocks. See [Creating and highlighting code blocks](https://help.github.com/articles/creating-and-highlighting-code-blocks).

---

## Questions & Support

If you have questions, feel free to reach out at **[hello.drumscript@gmail.com](mailto:hello.drumscript@gmail.com)**.

Thank you for helping us build `DrumScript`! 🥁🚀 :D





---
<!--END-->