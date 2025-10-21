#!/bin/bash

# This script sets up the custom styling for the DrumScript Sphinx documentation.
# Run it from the root of your repository (e.g., ./setup_docs_style.sh)

echo "Creating static directory..."
mkdir -p developer_docs/_static

# -----------------------------------------------------------------
# 1. Create the custom.css file
# -----------------------------------------------------------------
echo "Creating developer_docs/_static/custom.css..."
cat << 'EOF' > developer_docs/_static/custom.css
/* developer_docs/_static/custom.css */

/* --- Import a modern font (optional, but nice) --- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

/* --- Set the base font to match the UI's modern feel --- */
body {
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
}

/* --- Style links to use "DrumScript Green" --- */
a,
a:visited {
    color: #39FF14; /* DrumScript Green */
    text-decoration: none;
}

a:hover {
    color: #39FF14;
    text-decoration: underline;
}

/* --- Style sidebar links --- */
.sidebar-tree a.current {
    color: #39FF14 !important; /* Green for active page */
}

/* --- Style for a "Transcribe" style button --- */
/* You can use this class in your .md files like this:
   <a href="#" class="btn-primary">Transcribe</a>
*/
.btn-primary {
    display: inline-block;
    padding: 10px 20px;
    font-weight: 600;
    color: #121212; /* Dark text on button */
    background-color: #39FF14; /* DrumScript Green */
    border: none;
    border-radius: 8px;
    text-decoration: none;
    transition: all 0.2s ease-in-out;
    box-shadow: 0 4px 15px -5px rgba(57, 255, 20, 0.6);
}

.btn-primary:hover {
    color: #121212;
    text-decoration: none;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px -5px rgba(57, 255, 20, 0.8);
}
EOF

# -----------------------------------------------------------------
# 2. Create/Overwrite the conf.py file
# -----------------------------------------------------------------
echo "Creating developer_docs/conf.py..."
cat << 'EOF' > developer_docs/conf.py
# developer_docs/conf.py

import os
import sys
# Point to the project root to find the Python modules
sys.path.insert(0, os.path.abspath('..')) 

# -- Project information -----------------------------------------------------
project = 'DrumScript'
copyright = '2025, DrumScript'
author = 'DrumScript'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',  # Pull documentation from docstrings
    'sphinx.ext.napoleon', # Support Google/NumPy style docstrings
    'myst_parser',       # Read .md files
]

# Tell Sphinx to read .md files
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# -- Options for HTML output -------------------------------------------------

# Set the theme to Furo
html_theme = 'furo'

# --- Custom static files ---
# Tell Sphinx to look in the _static folder
html_static_path = ['_static']
# Tell Sphinx to load our custom.css file
html_css_files = ['custom.css']

# --- Furo Theme Options (for custom styling) ---
html_theme_options = {
    # Set default theme to dark
    "default_mode": "dark",
    
    # --- Color Overrides to match your UI Prototype ---
    # These are CSS variables that Furo uses.
    
    # Fallback light mode colors (based on your green)
    "light_css_variables": {
        "color-brand-primary": "#39FF14",
        "color-brand-content": "#39FF14",
        "color-background-primary": "#F1F1F1",
        "color-background-secondary": "#FFFFFF",
        "color-text-primary": "#121212",
    },
    
    # Your dark mode colors
    "dark_css_variables": {
        # -- Brand Colors --
        "color-brand-primary": "#39FF14",   # "DrumScript Green" for links, headers
        "color-brand-content": "#39FF14",   # "DrumScript Green" for links in content
        
        # -- Base Backgrounds --
        "color-background-primary": "#121212",   # Main dark background
        "color-background-secondary": "#1E1E1E", # Lighter card/sidebar background
        
        # -- Text Colors --
        "color-text-primary": "#F1F1F1",       # Main text
        "color-text-secondary": "#AAAAAA",     # Lighter secondary text
        
        # -- Other UI elements --
        "color-sidebar-background": "#1E1E1E",
        "color-sidebar-link-text": "#F1F1F1",
        "color-sidebar-link-text--top-level": "#F1F1F1",
        "color-foreground-primary": "#F1F1F1",
    },
}
EOF

echo "Done! Your documentation styling files have been created."
echo "Next steps:"
echo "1. Create/update 'developer_docs/index.md' to add your content and toctree."
echo "2. Create 'developer_docs/api.rst' to set up your API reference."
echo "3. Commit and push these new files to GitHub."