======
PyRope
======

PyRope is a Python package for creating randomised (electronic) assessment
exercises and for running them in different contexts. It is especially
designed for the needs in science, technology, engineering and mathematics
(STEM), but not limited to these domains.

In contrast to classical e-assessment systems, PyRope's philosophy is:

.. epigraph::
  **„Coding, not clicking.“**

If you want to develop an exercise, you should spend your time on its
didactical design, not on the process of getting it into the system.
Representing exercises as pure source code allows one to benefit from well
established software developing practices and tools, and therefore help to:

* develop exercises more efficiently
* use a familiar integrated development environment (IDE)
* improve documentation
* spot and fix bugs
* share exercise pools as open educational ressources (OER)
* better understand exercises authored by others
* make exercises easily accessible to automated analyses
* increase confidence in the e-assessment system


Design Principles
=================

**Simplicity**
  Creating exercises should make fun. PyRope aims for simple and fast exercise
  coding, even for users inexperienced with Python.
**Python**
  With PyRope, you have the full power of Python at hand to create elaborate
  exercises, limited only by your creativity.
**Flexibility**
  PyRope not only allows you to easily adapt available exercises, but also to
  create your own, new exercise formats.
..
  **Collections**
    Be it from your personal fund or from public sources, PyRope lets you
    compile new exercise collections by selection, aggregation and filtering
    mechanisms.
**Autonomy**
  You can run PyRope locally, without the need of a database, a remote server
  or a learning management system. This is particularly interesting for
  students who want to practice in private, without the fear of being tracked
  permanently.
**Modularity**
  The modular design of PyRope allows different user frontends and database
  backends.
**Open Source**
  PyRope is open source and licensed under the `GNU Affero General Public
  License <https://www.gnu.org/licenses/agpl-3.0.en.html>`_.  You are free to
  run, study, share and modify the source code, provided you distribute
  derived versions under the same license terms.

To keep PyRope simple, it will not:

* tie to a Learning Management System (LMS)
* provide user or course management
* provide tools for analysing stored user data
* allow exercises with branched control flow


Features
========

* short exercise development cycle using Jupyter Notebooks
* templates in `Markdown <https://www.markdownguide.org/>`_ format
* embedding of images, videos or `LaTeX <https://www.latex-project.org/>`_
* typed input fields
* interactive input validation
* unrestricted use of powerful Python modules, e.g.

  * `Sympy <http://sympy.org/>`_ for symbolic manipulation
  * `NumPy <https://numpy.org/>`_ and `SciPy <https://scipy.org/>`_ for numeric
    computation
  * `Matplotlib <https://matplotlib.org/>`_ for dynamic generation of diagrams
    and images
  * `Pandas <https://pandas.pydata.org/>`_ for incorporating external data

* sophisticated auto-scoring mechanism
* programmable individual feedback
* unit testing of exercises for inconsistencies or common errors like missing or
  inappropriate treatment of trivial user input
* Jupyter Notebook based frontend
* flexible configuration


.. warning::

  This package is still in a very early stage of development and therefore
  subject to heavy changes.  Please do not rely on stability or continuity yet,
  especially not in exam contexts.


Getting started
===============

For the impatient, here is what you need to do to get PyRope up and running.  More detailed instructions can be found in the section :doc:`Download and Installation <installation>`.

First, install the following packages:

* `Python3 <https://www.python.org/downloads>`_ (version >= 3.10)
* `Pandoc <https://pandoc.org/installing.html>`_ (2.9.2 <= version < 4.0.0).
* `Git <https://git-scm.com/downloads>`_

Then change to your install directory and run the commands below.

.. tabs:: 

  .. tab:: Windows

    .. code-block:: console

      python -m venv venv
      venv\Scripts\activate
      python -m pip install git+https://github.com/PyRope-E-Assessment/pyrope.git
      python -m pyrope run

  .. tab:: Linux

    .. code-block:: console

      python3 -m venv venv
      source venv/bin/activate
      python3 -m pip install git+https://github.com/PyRope-E-Assessment/pyrope.git
      python3 -m pyrope run


Documentation
=============

* :doc:`Download and installation <installation>`
* :doc:`Quickstart tutorial <quickstart>`
* :doc:`In-depth tutorial <tutorial>`
* :doc:`Frequently asked questions <FAQ>`

You can contribute to this project in several ways:

* Tell us your user experience.
* Create your own exercises or exercise pools and make them public.  Send us a
  reference if you do so.
* Find bugs and report them in our `issue tracker
  <https://github.com/PyRope-E-Assessment/pyrope/issues>`_.
* Request features you would like to see in the next version.
* Participate in the development of the code base.


Contact
=======

Software development:
  * Konrad Schöbel <konrad.schoebel@htwk-leipzig.de>
  * Paul Brassel <paul.brassel@htwk-leipzig.de>

Exercise pools:
  * Jochen Merker <jochen.merker@htwk-leipzig.de>
  * Heike Hain <heike.hain@htwk-leipzig.de>


Acknowledgements
================

This project is developed at the HTWK Leipzig University of Applied Sciences
and funded by the "Stiftung Innovation in der Hochschullehre".

.. image:: Logo_StIL.png
  :alt: logo Stiftung Innovation in der Hochschullehre
  :width: 256px
