"""Sphinx configuration for the installed PeriScope distribution."""

from importlib.metadata import version as distribution_version

project = "PeriScope"
copyright = "2026, Colin Orion Chandler"
author = "Colin Orion Chandler"
release = distribution_version("periscope-planner")
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "autoapi.extension",
]
exclude_patterns = ["build", "_build"]
master_doc = "index"
html_theme = "sphinx_rtd_theme"
html_show_sourcelink = False
html_context = {
    "display_github": True,
    "github_user": "ColinOrionChandler",
    "github_repo": "PeriScope",
    "github_version": "main",
    "conf_py_path": "/docs/",
}
add_module_names = False
autoapi_type = "python"
autoapi_dirs = ["../src/periscope"]
# Parse _version.py so AutoAPI can resolve the public __version__ export.
autoapi_ignore = ["*/__main__.py"]
autoapi_add_toc_tree_entry = False
autoapi_member_order = "bysource"
copybutton_prompt_text = r"\$ "
copybutton_prompt_is_regexp = True
