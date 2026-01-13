
# docs/conf.py
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'DrumScript'
copyright = '© 2025, DrumScript'
author = '© 2025, DrumScript'
release = '0.1.0'

# -- Path setup --------------------------------------------------------------
# Add the project root directory (one level up) to Python's path
# This allows Sphinx's 'autodoc' to find 'audio_processor', 'drum_classifier', etc.
import os
import sys
sys.path.insert(0, os.path.abspath('..'))


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Add extensions
extensions = [
    'sphinx.ext.autodoc',  # Pull documentation from docstrings
    'sphinx.ext.viewcode',
    'myst_parser',       # Read .md files
]

# Generate the stub pages automatically
autosummary_generate = True

# Tell Sphinx to treat .md files as Markdown
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}


templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo' # Requires: `uv pip install furo, but this is also added if you install dependencies when you first create your `.venv` on a local branch, if you use `uv pip install -e ".[dev]"`

# Optional: Furo allows custom light/dark mode logos
# html_theme_options = {
#     "light_logo": "_static/logo-light.png",
#     "dark_logo": "logo-dark.png",
# }


html_static_path = ['_static']
html_theme_options = {# --- ADD THESE LINES FOR THE GITHUB LINK ---
    "source_repository": "https://github.com/DrumScript/DrumScript",
    "source_branch": "main",
    "source_directory": "docs/",
    # -------------------------------------------
}   
# (Optional) Set a logo
html_logo = "_static/logo.png"