"""Sphinx configuration."""
from datetime import datetime


project = "Charter"
author = "Paulo S. Costa"
copyright = f"{datetime.now().year}, {author}"
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon"]
autodoc_typehints = "description"
