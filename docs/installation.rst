############
Installation
############

Make sure you have the following installed on your system:

* `Python3 <https://www.python.org/downloads>`_, version 3.10 or
  higher
* `Git <https://git-scm.com/downloads>`_

.. tip::
  We recommend to install PyRope into a virtual environment. This avoids
  conflicts with other Python packages on your system.

First change to a directory where you want to store the virtual environment,
then create and activate it.

.. tabs::

   .. group-tab:: Windows

     .. code:: console

       python -m venv venv
       venv\Scripts\activate

   .. group-tab:: Linux

     .. code:: console

       python3 -m venv venv
       source venv/bin/activate

Download and install the current version of PyRope.

.. tabs::

   .. group-tab:: Windows

     .. code:: console

       python -m pip install git+https://github.com/PyRope-E-Assessment/pyrope.git

   .. group-tab:: Linux

     .. code:: console

       python3 -m pip install git+https://github.com/PyRope-E-Assessment/pyrope.git

To see that everything works fine, you can run tests on the sample exercises.

.. tabs::

   .. group-tab:: Windows

     .. code:: console

       python -m pyrope test

   .. group-tab:: Linux

     .. code:: console

       python3 -m pyrope test

You should see an output similar to the following.

.. code:: console

  ..............................................................................
  ..............................................................................
  .....................................................................
  ----------------------------------------------------------------------
  Ran 225 tests in 0.605s

  OK

Run the sample exercises.

.. tabs::

   .. group-tab:: Windows

     .. code:: console

       python -m pyrope run

   .. group-tab:: Linux

     .. code:: console

       python3 -m pyrope run

To generate this documentation yourself, you first need to install `Sphinx
<https://www.sphinx-doc.org/>`_ together with the necessary extensions. Then
change to the PyRope documentation directory and run Sphinx.

.. tabs::

   .. group-tab:: Windows

     .. code:: console

       python -m pip install sphinx sphinx-tabs sphinx_rtd_theme
       cd docs
       sphinx-build . build/

   .. group-tab:: Linux

     .. code:: console

       python3 -m pip install sphinx sphinx-tabs sphinx_rtd_theme
       cd docs
       sphinx-build . build/

