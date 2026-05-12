# docs/conf.py
# Configuration file for the Sphinx documentation builder.


# -- Path setup --------------------------------------------------------------
# Add the project root directory (one level up) to Python's path
# This allows Sphinx's 'autodoc' to find 'audio_processor', 'drum_classifier', etc.
import os
import sys

sys.path.insert(0, os.path.abspath(".."))

#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "DrumScript"
copyright = "© 2026, DrumScript"
author = "DrumScript"
release = "0.1.3"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Add extensions
extensions = [
    "sphinx.ext.autodoc",  # Pull documentation from docstrings
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",  # Required for API tables
    "myst_parser",  # Read .md files
    "myst_nb",  # Read .ipynb files
]

## -- MyST configuration ------------------------------------------------------
myst_heading_anchors = 3  # auto-generate anchors for H1-H3, anchor IDs for H1 through H3 headings, slugified from the heading text.

# Generate the stub pages automatically
autosummary_generate = True
add_module_names = False

# Tell Sphinx to treat .md files as Markdown
# source_suffix = {
#   '.rst': 'restructuredtext',
#   '.md': 'markdown',
# }


templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**/_template.md"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "shibuya"
html_static_path = ["_static"]
# This loads your custom.css
html_css_files = [
    "custom.css",
]
# Shibuya Setup
html_theme_options = {
    # Logos: Shibuya prefers the full relative path from your docs folder
    "light_logo": "_static/logo-light.svg",
    "dark_logo": "_static/logo-dark.svg",
    "github_url": "https://github.com/DrumScript/DrumScript",
    "nav_links": [  # Amend groups that appear in Sphinx top navbar
        {"title": "Getting Started", "url": "index"},
        {"title": "API Reference", "url": "api"},
        {"title": "Guide", "url": "guide"},
        {"title": "Runbooks", "url": "guide/interactive"},
        {"title": "Contributing", "url": "development/contributor_guidance"},
        {"title": "Release Notes", "url": "release_notes/index"},
        {"title": "Fun Theory", "url": "theory/drum_notation_guide"},
    ],
}

html_context = {
    "source_type": "github",
    "source_user": "DrumScript",
    "source_repo": "DrumScript",
    "versions_url": "/versions.json",
}
