*********
Exercises
*********

The following explains in detail and with lots of examples how to use PyRope
to create interactive exercises. For a quick glimpse on the bare essentials,
please have a look into the :doc:`Quickstart Tutorial <quickstart>` instead.

For the examples in this documentation one needs to import the PyRope module.
We will assume this has already been done.

.. code-block:: python

    import pyrope

This is to make the origin of PyRope objects explicit by referencing them via
the dot notation and the ``pyrope`` module prefix, as in ``pyrope.Exercise``
or ``pyrope.Problem``. Writing the prefix each time an object is referenced
can be avoided by importing it from the PyRope module instead:

.. code-block:: python

    from pyrope import Exercise, Problem


.. toctree::
    :caption: Table of Contents
    :maxdepth: 2

    exercise_class
    preamble
    parameters
    problem
    scoring
    solution
    hints
    feedback

