=======
Running
=======

If you have no exercise at hand, you can copy the file ``examples.py`` from
the PyRope sources to your current folder. To find out where it is located,
run the following command.

.. tabs::

  .. group-tab:: Windows

    .. code:: console

      python -c 'import pyrope; print(pyrope.examples.__file__)'

  .. group-tab:: Linux

    .. code:: console

      python3 -c 'import pyrope; print(pyrope.examples.__file__)'


Command Line
============

.. tabs::

  .. group-tab:: Windows

    .. code:: console

      python -m pyrope run

  .. group-tab:: Linux

    .. code:: console

      python3 -m pyrope run


.. tabs::

  .. group-tab:: Windows

    .. code:: console

      python -m pyrope run examples.py

  .. group-tab:: Linux

    .. code:: console

      python3 -m pyrope run examples.py


.. tabs::

  .. group-tab:: Windows

    .. code:: console

      python -m pyrope run examples.py:FortyTwo

  .. group-tab:: Linux

    .. code:: console

      python3 -m pyrope run examples.py:FortyTwo


Jupyter Cell Magics
===================

.. code::

  %pyrope run examples.py:FortyTwo


User input validation
=====================

