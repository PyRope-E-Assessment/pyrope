
=========
Changelog
=========


v0.1.1
======

New
---

* Add type hints to configurations to make it clearer for users.
* Configure how many options of :py:class:`OneOf` nodes will be rendered as
  radio buttons at most with ``maximal_radio_buttons``.
* :py:class:`ExpressionType` interprets :code:`e` and :code:`i` as euler's
  number and the imaginary unit if they are not specified as symbols.
* Input fields have a ``correct`` flag. Jupyter frontends use this flag to
  highlight input fields after submission.
* Weight scores with ``weights`` when instantiating an exercise and test
  ``weights``.
* Implement ``atol`` and ``rtol`` for :py:class:`Complex` and :py:class:`Real`
  nodes.
* Add specific exercises from a Python script to an exercise pool via the CLI,
  i.e. ``/path/to/exercises/exercises.py:Example1,Example2,...``.
* New nodes: :py:class:`Polynomial`, :py:class:`ElementwisePolynomial`,
  :py:class:`LinearExpression`, :py:class:`ElementwiseLinearExpression` and
  :py:class:`MultipleChoice`.
* New compare option ``up_to_multiple`` for :py:class:`Vector`. With this
  option linear dependent input vectors will also get the maximal score.
* An exercise's difficulty can be set with ``difficulty`` on
  :py:meth:`Exercise.run`.
* When an exercise is instantiated, the range from which ``difficulty`` is
  randomly chosen from can be specified with keyword arguments
  ``min_difficulty`` and ``max_difficulty``.
* The following metadata can be specified as class attributes for an exercise:
  ``title``, ``subtitle``, ``author``, ``language``, ``license``, ``URL``,
  ``pyrope_versions``, ``origin``, ``discipline``, ``area``, ``topic``,
  ``keywords`` and ``taxonomy``. If specified, they get tested via unit tests
  when :py:meth:`MyExercise().test` is called.
* Rudimentary database functionalities.
* History log for statistical purposes and learning analytics.
* New exercise method :py:meth:`hints`: This method can be used to return a
  string or an iterable of strings containing tips for students to solve an
  exercise. In :py:class:`JupyterFrontend` these hints can be rendered via a
  button.
* History logging for learning analytics.
* Define default values in :py:meth:`scores` for input fields.

Changes
-------

* Downgrade required Python version to 3.10.
* While adding exercises to an exercise pool, reload already imported modules
  so that changes in exercises are considered.
* In Jupyter frontends, Feedbacks and total scores will now have the same style
  as problem and preamble templates.
* Remove :py:meth:`Widget.new_instance` because :py:meth:`Node.clone` made it
  obsolete.
* Jupyter frontend: Encode and decode templates with Base64.
* Drop :py:class:`ColumnVector` and :py:class:`RowVector`. Use
  :py:class:`Vector` with keyword argument ``orientation`` instead. Vectors are
  now represented as a flat :py:class:`numpy.array` internally.
* Validate arguments of widgets.
* Rename ``score_types`` to ``float_types``.
* Create a :py:mod:`nodes` package and outsource errors into a separate module
  to avoid circular imports.
* Composed input fields can be invalid even if all children nodes are valid.
  Therefore all children nodes are now invalid if the composed input field is
  invalid.
* Messages sent between frontends and runners are now encapsulated by the class
  :py:class:`Message`.
* Line breaks are handled differently in templates: One or more blank lines
  start a new paragraph and escaping a newline character enforces a line break.
  For multiline strings this means you only have to write a double backslash at
  the end of a line or a single backslash in case of raw multiline strings.
* Accept ``None`` and empty strings as solutions.
* If there are empty input fields with no default values in a joint input
  field scoring scenario, the exercise gets a total score of zero.

Fixes
-----

* Raise an error in :py:class:`MatrixType` if ``atol`` or ``rtol`` are not
  real numbers.
* In Jupyter frontends, use Pandoc's ``tex_math_dollars`` Markdown extension to
  respect LaTeX environments in all templates.
* Return ``False`` in :py:meth:`ExpressionType.compare` if
  :py:meth:`sympy.Expr.equals` returns ``None``.
* Widgets now use their correct parent node to calculate scores automatically.
