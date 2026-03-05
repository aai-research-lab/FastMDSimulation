import os
import sys
from datetime import datetime

project = "FastMDSimulation"
author = "FastMDSimulation contributors"
copyright = f"{datetime.now().year}, {author}"
release = "0.1.0"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

autosummary_generate = True
autodoc_typehints = "description"
autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    # If an OpenMM inventory becomes available, add it; None skips fetching
    # "openmm": ("https://openmm.org/documentation/", None),
}

myst_enable_extensions = ["colon_fence", "deflist"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
    ".txt": "markdown",
}

# Treat top-level README headings as-is (MyST default), no extra config here.

html_theme = "furo"
html_theme_options = {
    "navigation_with_keys": True,
    "sidebar_hide_name": True,
}
html_logo = "assets/fastmdsimulation_banner.png"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

# Relax MyST heading level warnings from imported Markdown (README)
suppress_warnings = ["myst.header"]
html_title = project
exclude_patterns = ["_build", "**/furo.js.LICENSE.txt"]

# Ensure src is on path for autodoc
sys.path.insert(0, os.path.abspath("../src"))
