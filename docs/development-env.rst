#######################
Development Environment
#######################

To create a development environment, you have to make sure that the
requirements from :doc:`Installation <installation>` are installed on your
system.

First clone the repository to your system and change your current working
directory inside the downloaded folder.

.. tabs::

   .. group-tab:: Windows

     .. code:: console

       git clone https://github.com/PyRope-E-Assessment/pyrope.git
       cd pyrope

   .. group-tab:: Linux

     .. code:: console

       git clone https://github.com/PyRope-E-Assessment/pyrope.git
       cd pyrope

Then create and activate a virtual environment.

.. tabs::

   .. group-tab:: Windows

     .. code:: console

       python -m venv venv
       venv\Scripts\activate

   .. group-tab:: Linux

     .. code:: console

       python3 -m venv venv
       source venv/bin/activate

Finally install PyRope's development dependencies and make the package
editable.

.. tabs::

   .. group-tab:: Windows

     .. code:: console

       python -m pip install pyrope[dev]@git+https://github.com/PyRope-E-Assessment/pyrope.git
       python -m pip install --no-deps -e .

   .. group-tab:: Linux

     .. code:: console

       python3 -m pip install pyrope[dev]@git+https://github.com/PyRope-E-Assessment/pyrope.git
       python3 -m pip install --no-deps -e .


=============
Documentation
=============

To generate this documentation by yourself, you need to run `Sphinx
<https://www.sphinx-doc.org/>`_ which is part of PyRope's development
dependencies.

.. tabs::

   .. group-tab:: Windows

     .. code:: console

       sphinx-autobuild docs docs/build

   .. group-tab:: Linux

     .. code:: console

       sphinx-autobuild docs docs/build
