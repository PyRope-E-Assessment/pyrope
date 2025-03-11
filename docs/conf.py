# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PyRope'
copyright = '2024'
author = 'Konrad Schöbel, Paul Brassel'
release = '0.1.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

exclude_patterns = ['README.rst']
extensions = ['sphinx.ext.autosectionlabel', 'sphinx_tabs.tabs']
html_logo = 'logo-pyrope-icon.png'
html_title = 'Documentation'
html_favicon = 'favicon-48x48.png'
suppress_warnings = ['autosectionlabel.quickstart']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
