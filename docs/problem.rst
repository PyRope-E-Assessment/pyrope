
Problem Statement
=================

Obviously, an exercise needs to state the actual problem that has to be
solved. This is the purpose of the :py:meth:`problem` method, the only
mandatory method of an exercise. Let's first give a simple example with a
single input field and a static answer.

.. code-block:: python

    class Multiplication(pyrope.Exercise):

        def problem(self):
            return pyrope.Problem(
                'What is 6x7?  <<answer>>',
                answer=pyrope.Natural()
            )

        def the_solution(self):
            return 42

The problem statement consists of a template with placeholders for input and
output fields, together with a specification of the input field types.  It is
is created by calling :py:meth:`pyrope.Problem` with appropriate parameters.

.. code-block:: python

    pyrope.Problem(template, **ifields)


Template
--------

An exercise template is a string with placeholders for input and output
fields.  The string is interpreted as `Markdown
<https://www.markdownguide.org/>`_ to allow for basic `formatting
<https://www.markdownguide.org/cheat-sheet/>`_ such as

* `heading <https://www.markdownguide.org/basic-syntax/#headings>`_
* `bold <https://www.markdownguide.org/basic-syntax/#bold>`_ and `italic <https://www.markdownguide.org/basic-syntax/#italic>`_
* `blockquote <https://www.markdownguide.org/basic-syntax/#blockquotes-1>`_
* `unordered <https://www.markdownguide.org/basic-syntax/#unordered-lists>`_ and `ordered list <https://www.markdownguide.org/basic-syntax/#ordered-lists>`_
* `code <https://www.markdownguide.org/basic-syntax/#code>`_
* `horizontal rule <https://www.markdownguide.org/basic-syntax/#horizontal-rules>`_
* `link <https://www.markdownguide.org/basic-syntax/#links>`_
* `image <https://www.markdownguide.org/basic-syntax/#images-1>`_
* `tables <https://www.markdownguide.org/extended-syntax/#tables>`_

Template strings will usually span multiple lines and Python's triple quoted
strings are best suited for that.  In order to allow for a consistent
indentation, PyRope will eliminate any common leading whitespace from every
line in the template string.

For mathematical expressions, PyRope admits the use of :math:`\LaTeX` if it
is properly enclosed in ``$`` respectively ``$$`` delimiters.

.. tip::

    Using `raw strings
    <https://docs.python.org/3/reference/lexical_analysis.html#string-and-bytes-literals>`_
    for template strings containing :math:`\LaTeX` will prevent Python from
    interpreting the backslashes in :math:`\LaTeX` commands as `escape
    sequences
    <https://docs.python.org/3/reference/lexical_analysis.html#escape-sequences>`_.
    For example, write ``r'... $\beta$ ...'`` to avoid that ``\b`` is understood
    as a backspace.  Otherwise you would have to write ``'...$\\beta$...'``.


Placeholders
------------

The syntax for a placeholder is ``<<name>>``, where ``name`` is the name of
the input or output field.  The delimiters ``<<`` and ``>>`` were chosen to
interfere as little as possible with markup, :math:`\LaTeX`, HTML or Python.
Placeholders can be placed within most Markdown elements.  Note that there is
no syntactical difference between placeholders for input and output fields.
In the exercise below, for example, ``a`` and ``b`` are output fields whereas
``answer`` is an input field.

.. code-block:: python

    import random

    class Multiplication(pyrope.Exercise):

        def parameters(self):
            return dict(
                a=random.randint(2, 9),
                b=random.randint(2, 9),
            )

        def problem(self, a, b):
            return pyrope.Problem(
                '<<a>> * <<b>> = <<answer>>',
                answer=pyrope.Natural()
            )

        def the_solution(self, a, b):
            return a * b


Input Fields
------------

Input fields in PyRope are typed.  This assures two important facts:

1. The learner gets immediate visual feedback on syntactically invalid input.
2. The instructor is guaranteed that variables coming from user input have the
   correct type.

=======================================  ======================================
Input field                              Python Type
=======================================  ======================================
:py:class:`Boolean` or :py:class:`Bool`  ``bool``
:py:class:`Natural`                      ``int``, non-negative
:py:class:`Integer` or :py:class:`Int`   ``int``
:py:class:`Real`                         ``float``
:py:class:`Complex`                      ``complex``
:py:class:`String`                       ``str``
:py:class:`Tuple`                        ``tuple``
:py:class:`List`                         ``list``
:py:class:`Dict`                         ``dict``
:py:class:`Rational`                     ``fraction.Fraction``
:py:class:`Vector`                       ``np.array``, one-dimensional
:py:class:`RowVector`                    ``np.array`` of shape (1, N)
:py:class:`ColumnVector`                 ``np.array`` of shape (N, 1)
:py:class:`Matrix`                       ``np.array``, two-dimensional
=======================================  ======================================

The keyword arguments to :py:meth:`pyrope.Problem` define which placeholders
stand for input fields.  The keys are the names of the input fields and the
values are the input fields, created by calling the corresponding constructor.


.. attention::

    Currently it is not possible to place input fields within :math:`\LaTeX`
    environments, although this is planned for the future.  For the time being,
    there are two options to deal with this:

    1. Break up the :math:`\LaTeX` environment for the input fields.

    2. Use variables instead and ask for them in separate input fields outside
       the :math:`\LaTeX` environment.

    For example, you can not use ``r'... $\frac{<<a>>}{<<b>>}$ ...'`` to ask
    for a fraction with separated input fields for numerator :math:`a` and
    denominator :math:`b`.  Instead, use:

    .. code-block:: python

        pyrope.Problem(
            r'... $\frac{a}{b}$ with $a=$ <<a>> and $b=$ <<b>> ...',
            a=pyrope.Int(),
            b=pyrope.Int()
        )

    Note that PyRope also provides a :py:class:`pyrope.Rational` input field
    for fractions.  With the ``elementwise=True`` option, numerator and
    denominator have separate input fields.


Output Fields
-------------

Any placeholder whose name is not a keyword argument to
:py:meth:`pyrope.Problem` is considered an output field and will be replaced
by the corresponding parameter when the problem is rendered. Therefore any
output parameter must be part of the :ref:`parameters <Parameters>` returned
by the :py:meth:`parameters` method. PyRope takes care to properly render
output fields according to the corresponding parameter's type. In this way
you can, for instance, embed dynamically generated Pyplot figures into your
problem statement.

Note that it is not necessary to specify the output parameters as keyword
parameters to the :py:meth:`problem` method if they only appear in the
template string.  Your linter or IDE will probably complain about unused
variables if you do so.

Output fields can be placed in all Markdown elements, even
within :math:`\LaTeX` environments.  However, to avoid parsing issues, you
have to indicate when an output field ``name`` is placed inside a
:math:`\LaTeX` environment by using the special syntax ``<<name:latex>>``.

.. code-block:: python

    import random

    class SquareRoot(pyrope.Exercise):

        def parameters(self):
            root = random.randint(1, 9)
            return dict(root=root, square=root**2)

        def problem(self):
            return pyrope.Problem(
                r'The square root $\sqrt{<<square:latex>>}$ equals <<root>>.',
                root=pyrope.Natural()
            )

        def the_solution(self, root):
            return root


