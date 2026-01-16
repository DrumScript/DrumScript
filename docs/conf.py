
# docs/conf.py
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'DrumScript'
copyright = '© 2026, DrumScript'
author = 'DrumScript'
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
    'sphinx.ext.autosummary', # Required for API tables
    'myst_parser'       # Read .md files
]

# Generate the stub pages automatically
autosummary_generate = True
add_module_names = False

# Tell Sphinx to treat .md files as Markdown
#source_suffix = {
 #   '.rst': 'restructuredtext',
 #   '.md': 'markdown',
#}


templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'shibuya'
html_static_path = ['_static']
# This loads your custom.css
html_css_files = [
    'custom.css',
]
# Shibuya Setup
html_theme_options = { 
    # Logos: Shibuya prefers the full relative path from your docs folder
    "light_logo": "_static/logo-light.svg",
    "dark_logo": "_static/logo-dark.svg",

    "github_url": "https://github.com/DrumScript/DrumScript",
    
    "nav_links": [
        {"title": "Getting Started", "url": "index"},
        {"title": "API Reference", "url": "api"},
        {"title": "Development", "url": "development/contributor_guidance"},
    ]
}

# Optional: Add your context for the "Edit on GitHub" button
html_context = {
    "source_type": "github",
    "source_user": "DrumScript",
    "source_repo": "DrumScript",
}


