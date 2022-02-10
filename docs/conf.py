##########################################################################
# Copyright (c) 2010-2022 Robert Bosch GmbH
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0.
#
# SPDX-License-Identifier: EPL-2.0
##########################################################################

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys

sys.path.insert(0, os.path.abspath("../src/pykiso"))


# -- Project information -----------------------------------------------------
import pykiso

project = "pykiso"
copyright = "2020, Sebastian Fischer, Daniel Bühler, Damien Kayser"
author = "Sebastian Fischer, Daniel Bühler, Damien Kayser"

version = pykiso.__version__.split(".")[0]
release = pykiso.__version__


# -- General configuration ---------------------------------------------------

primary_domain = "py"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinxcontrib.programoutput",
    "sphinx_autodoc_typehints",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "restructuredtext",
}
# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# Include documentation from both the class level and __init__
autoclass_content = "both"

# The default autodoc directive flags
autodoc_default_flags = ["members", "show-inheritance"]
