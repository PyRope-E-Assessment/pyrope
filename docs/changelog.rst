
================
PyRope Changelog
================


v0.1.1
======

New
---

* Empty input fields can be scored manually with :code:`treat_none_manually`.
* Test if :code:`treat_none_manually` is set to :code:`True` for cases where :code:`None` has to be treated manually.
* Add type hints to configurations to make it clearer for users.
* Configure how many options of :code:`OneOf` nodes will be rendered as radio buttons at most with :code:`one_of_maximum_radio_buttons`.
* :code:`ExpressionType` interprets :code:`e` and :code:`i` as euler's number and the imaginary unit if they are not specified as symbols.
* Input fields have a :code:`correct` flag. Jupyter frontends use this flag to highlight input fields after submission.
* Weight scores with :code:`weights` when instantiating an exercise and test :code:`weights`.
* Implement :code:`atol` and :code:`rtol` for :code:`Complex` and :code:`Real` nodes.
* Add specific exercises from a Python script to an exercise pool via the CLI, i.e. :code:`/path/to/exercises/exercises.py:Example1,Example2,...`.

Changes
-------

* While adding exercises to an exercise pool, reload already imported modules so that changes in exercises are considered.
* In Jupyter frontends, Feedbacks and total scores will now have the same style as problem and preamble templates.
* Remove :code:`Widget.new_instance()` because :code:`Node.clone()` made it obsolete.
* Jupyter frontend: Encode and decode templates with Base64.
* Drop :code:`ColumnVector` and :code:`RowVector`. Use :code:`Vector` with keyword argument :code:`orientation` instead. Vectors are now represented as a flat :code:`numpy.array` internally.
* Validate arguments of widgets.
* Rename :code:`score_types` to :code:`float_types`.
* Create a :code:`nodes` package and outsource errors into a separate module to avoid circular imports.

Fixes
-----

* Raise an error in :code:`MatrixType` if :code:`atol` or :code:`rtol` are not real numbers.
* :code:`\n\n` will now create a new paragraph in templates.
* In Jupyter frontends, use Pandoc's :code:`tex_math_dollars` Markdown extension to respect LaTeX environments in all templates.
* Return :code:`False` in :code:`ExpressionType.compare()` if :code:`sympy.Expr.equals` returns :code:`None`.
