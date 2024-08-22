
================
PyRope Changelog
================


v0.1.1
======

New
---

* Empty input fields can be scored manually with :code:`treat_none_manually`.
* Test if :code:`treat_none_manually` is set to :code:`True` for cases where
  :code:`None` has to be treated manually.
* Add type hints to configurations to make it clearer for users.
* Configure how many options of :code:`OneOf` nodes will be rendered as radio
  buttons at most with :code:`one_of_maximum_radio_buttons`.
* :code:`ExpressionType` interprets :code:`e` and :code:`i` as euler's number
  and the imaginary unit if they are not specified as symbols.
* Input fields have a :code:`correct` flag. Jupyter frontends use this flag to
  highlight input fields after submission.
* Weight scores with :code:`weights` when instantiating an exercise and test
  :code:`weights`.
* Implement :code:`atol` and :code:`rtol` for :code:`Complex` and :code:`Real`
  nodes.
* Add specific exercises from a Python script to an exercise pool via the CLI,
  i.e. :code:`/path/to/exercises/exercises.py:Example1,Example2,...`.
* New nodes: :code:`Polynomial`, :code:`ElementwisePolynomial`,
  :code:`LinearExpression`, :code:`ElementwiseLinearExpression` and
  :code:`MultipleChoice`.
* New compare option :code:`up_to_multiple` for :code:`Vector`. With this
  option linear dependent input vectors will also get the maximal score.
* An exercise's difficulty can be set with :code:`difficulty` on
  :code:`Exercise.run()`.
* When an exercise is instantiated, the range from which :code:`difficulty` is
  randomly chosen from can be specified with keyword arguments
  :code:`min_difficulty` and :code:`max_difficulty`.
* The following metadata can be specified as class attributes for an exercise:
  :code:`title`, :code:`subtitle`, :code:`author`, :code:`language`,
  :code:`license`, :code:`URL`, :code:`origin`, :code:`discipline`,
  :code:`area`, :code:`topic`, :code:`topic_contingent`, :code:`keywords` and
  :code:`taxonomy`. If specified, they get tested via unit tests when
  :code:`MyExercise().test()` is called.
* Rudimentary database functionalities.
* New exercise method :code:`hints`: This method can be used to return a string
  or an iterable of strings containing tips for students to solve an exercise.
  In :code:`JupyterFrontend` these hints can be rendered via a button.

Changes
-------

* Downgrade required Python version to 3.10.
* While adding exercises to an exercise pool, reload already imported modules
  so that changes in exercises are considered.
* In Jupyter frontends, Feedbacks and total scores will now have the same style
  as problem and preamble templates.
* Remove :code:`Widget.new_instance()` because :code:`Node.clone()` made it
  obsolete.
* Jupyter frontend: Encode and decode templates with Base64.
* Drop :code:`ColumnVector` and :code:`RowVector`. Use :code:`Vector` with
  keyword argument :code:`orientation` instead. Vectors are now represented as
  a flat :code:`numpy.array` internally.
* Validate arguments of widgets.
* Rename :code:`score_types` to :code:`float_types`.
* Create a :code:`nodes` package and outsource errors into a separate module to
  avoid circular imports.
* Composed input fields can be invalid even if all children nodes are valid.
  Therefore all children nodes are now invalid if the composed input field is
  invalid.
* Messages sent between frontends and runners are now encapsulated by the class
  :code:`Message`.
* Line breaks are handled differently in templates: One or more blank lines
  start a new paragraph and escaping a newline character enforces a line break.
  For multiline this means you only have to write a double backslash at the
  end of a line or a single backslash in case of raw multiline strings.

Fixes
-----

* Raise an error in :code:`MatrixType` if :code:`atol` or :code:`rtol` are not
  real numbers.
* :code:`\n\n` will now create a new paragraph in templates.
* In Jupyter frontends, use Pandoc's :code:`tex_math_dollars` Markdown
  extension to respect LaTeX environments in all templates.
* Return :code:`False` in :code:`ExpressionType.compare()` if
  :code:`sympy.Expr.equals` returns :code:`None`.
