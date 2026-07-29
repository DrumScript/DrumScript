# docs/conf.py
# Configuration file for the Sphinx documentation builder.


# -- Path setup --------------------------------------------------------------
# Add the project root directory (one level up) to Python's path
# This allows Sphinx's 'autodoc' to find 'audio_processor', 'drum_classifier', etc.
import os
import sys

sys.path.insert(0, os.path.abspath(".."))

import drumscript as ds

#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "DrumScript"
# project = f"DrumScript v{ds.__version__}"
copyright = "© 2026, DrumScript"
author = "DrumScript"
release = ds.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Add extensions
extensions = [
    "sphinx.ext.autodoc",  # Pull documentation from docstrings
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",  # Required for API tables
    # "myst_parser",  # Read .md files
    "myst_nb",  # Read .ipynb files
]


## -- MyST configuration ------------------------------------------------------
myst_heading_anchors = 3  # auto-generate anchors for H1-H3, anchor IDs for H1 through H3 headings, slugified from the heading text.

# Dynamic substitutions for use in .md files via {{variable_name}} syntax.
myst_substitutions = {
    "version": ds.__version__,
}

myst_enable_extensions = ["substitution", "colon_fence"]

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
    # Logos: Shibuya prefers the full relative path from docs folder
    # "announcement": f"Alpha release — v{ds.__version__}",
    "announcement": f"DrumScript v{ds.__version__} now available: with mir_eval benchmarking",
    "light_logo": "_static/logo-light.svg",
    "dark_logo": "_static/logo-dark.svg",
    "github_url": "https://github.com/DrumScript/DrumScript",
    "nav_links": [  # Amend groups that appear in Sphinx top navbar
        {"title": "Getting Started", "url": "index"},
        {"title": "API Reference", "url": "api"},
        {"title": "Guide", "url": "guide/installation"},
        {"title": "Runbooks", "url": "guide/interactive/index"},
        {"title": "Contributing", "url": "development/contributor_guidance"},
        {"title": "Release Notes", "url": "release_notes/index"},
        {"title": "Fun Theory", "url": "theory/drum_notation_guide"},
    ],
}

html_context = {
    "source_type": "github",
    "source_user": "DrumScript",
    "source_repo": "DrumScript",
    # "versions_url": "/versions.json",  # Not used by Shibuya — kept for reference
    # ── Version switcher (Shibuya nav-versions.html) ───────────────
    # Shibuya expects `versions` as a list of (label, url) tuples and
    # `current_version` as a string. URLs are relative to the docs root.
    # Update this list when adding new tagged releases.
    # "current_version": f"v{ds.__version__}",
    "versions": [
        ("latest", "/DrumScript/latest/"),
        ("dev", "/DrumScript/dev/"),
        ("v0.1.6", "/DrumScript/v0.1.6/"),
    ],
}
