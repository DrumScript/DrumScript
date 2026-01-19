# Documentation

We use [`Sphinx`](https://www.sphinx-doc.org/en/master/) for `DrumScript` documentation. We use the [`Shibuya`](https://shibuya.lepture.com/) Sphinx theme for layout.


## `DrumScript` documentation structure

See [`here`](docs/FOLDER_STRUCTURE.txt) and below

```text
DrumScript Documentation Structure
==================================

This folder contains the source files for the DrumScript Sphinx documentation website.

Key Folders:
------------
/guide          -> User-focused tutorials (Installation, Usage).
/theory         -> Explanations, Background Science, and Notation Guides.
    /images     -> PNG/JPG assets for theory pages.
/development    -> Guides for code contributors (Testing, Code of Conduct).
/release_notes  -> Documentation related to `DrumScript` releases.
/_static        -> Website assets (Logos, Custom CSS).
/_build         -> The output folder (Generated HTML lives here).

Key Files:
----------
index.md        -> The Homepage (Table of Contents).
conf.py         -> Sphinx Configuration (Theme, Plugins).
api.rst         -> Auto-generated Python API Reference.

```

## Setup your development environment

1. Clone DrumScript repo
2. Use `git checkout -b feature/update_sphinx_docs`. Github will switch you to the `feature/update_sphinx_docs` branch. NOTE: `feature/update_sphinx_docs` is indicative of branch name. Please always use a subfolder, ie `build/`, `2.1.x/`, `feature/` etc depending on your changes
3. Use `git push origin -u feature/update_sphinx_docs` to publish your branch to the remote origin
4. Activate `.venv` using `source .venv/bin/activate`, then type `uv pip install -e ".[dev]"` to install the sphinx packages
> You can deactivate your `.venv` anytime from the root folder of `DrumScript` using `deactivate` 
5. Start making changes. Once you push a change, raise a [PR](https://github.com/DrumScript/DrumScript/pulls). CODEOWNERS will automatically be assigned to review once the PR is ready for review.

## About testing the documentation

> **Always** test local rendering before submitting changes for review in your PR.

There are three main files that we use to amend the Sphinx documentation: 

1. `docs/conf.py`: Configures the Shibuya theme. Use this to define how Sphinx builds the layout, amend navbar links. 
2. `docs/index.md`: Sets up the structure of the `documentation/` subfolders
3. `docs/api.rst`: Recursively obtains functions and arguments to post under `API reference` on the documentation

Images are stored in `docs/_static`. 

## How to re-build the documentation

1. `cd docs`
2. `rm -rf _build`
3. `make html`: a short way of executing the full command `python -m sphinx -b html -d _build/doctrees . _build/html`. Check the output in your Terminal to verify the build and scan for errors. 

## Render locally (opens in browser)

1. Ensure you are in the root directory (`DrumScript/`)
2. `open docs/_build/html/index.html`
3. Once you are happy, commit the changes.
