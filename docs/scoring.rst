
Scoring
=======

Notice that in the examples above, we did not provide a method to score the
result. This is because PyRope has a sophisticated auto-scoring, which scores
a correct answer with one point by default. If you prefer to score the answer
yourself, you have to implement a :py:meth:`scores` method.


Scores
------

A *score* in PyRope is either a number or a pair of to numbers. A single
number is interpreted as the number of achieved points. In a pair of numbers,
the first is interpreted as the achieved points and the second as the maximal
possible number of points. In short, a pair ``(p, q)`` should be read as "p of
q points".

In scores, a *number* can be of any type convertible to a ``float`` (and will
internally be treated as ``float``). This also includes booleans, where
``True`` means one point and ``False`` zero.

There are multiple ways how to return scores from the :py:meth:`scores` method.


Individual Input Field Scoring
------------------------------

In general, an exercise will have multiple input fields. These are scored
using a dictionary with the input field names as keys and the corresponding
:ref:`scores <Scores>` as values.

.. code-block:: python

    import random

    class IntegerDivision(pyrope.Exercise):

        def parameters(self):
            dividend = random.randint(2, 10)
            divisor = random.randint(1, dividend)
            return dict(dividend=dividend, divisor=divisor)

        def problem(self):
            return pyrope.Problem('''
                <<dividend>> divided by <<divisor>> is equal to
                <<quotient>> with remainder <<remainder>>.
                ''',
                quotient=pyrope.Natural(),
                remainder=pyrope.Natural(),
            )

        def scores(self, dividend, divisor, quotient, remainder):
            scores = {}
            if quotient == dividend // divisor:
                scores['quotient'] = (2, 2)
            else:
                scores['quotient'] = (0, 2)
            if remainder == dividend % divisor:
                scores['remainder'] = (1, 1)
            else:
                scores['remainder'] = (0, 1)
            return scores


Using the fact that booleans are allowed as scores and that they are
interpreted as ``1`` for ``True`` and ``0`` for ``False``, the
:py:meth:`scores` method in the example above can be written more concisely as:

.. code-block:: python

    def scores(self, dividend, divisor, quotient, remainder):
        return {
            'quotient': (2 * (quotient == dividend // divisor), 2),
            'remainder': (remainder == dividend % divisor, 1)
        }


Joint Input Field Scoring
-------------------------

If it is not possible to score the input fields individually or if the
instructor prefers to score them in common, then the :py:meth:`scores` method
must return a single :ref:`score <Scores>`.

.. _IntegerDivision:

.. code-block:: python

    import random

    class IntegerDivision(pyrope.Exercise):

        def parameters(self):
            dividend = random.randint(2, 10)
            divisor = random.randint(1, dividend)
            return dict(dividend=dividend, divisor=divisor)

        def problem(self):
            return pyrope.Problem('''
                <<dividend>> divided by <<divisor>> is equal to
                <<quotient>> with remainder <<remainder>>.
                ''',
                quotient=pyrope.Natural(),
                remainder=pyrope.Natural(),
            )

        def scores(self, dividend, divisor, quotient, remainder):
            scores = 0
            if quotient * divisor + remainder == dividend:
                scores += 2
            if remainder < divisor:
                scores += 1
            return (scores, 3)


.. note::

    Input fields have to be scored either all individually or all together.
    Currently it is not possible to score groups of input fields together,
    although this is planned for the future.


Auto-Scoring
------------

If no maximal score is given, PyRope needs a (not necessarily unique)
:ref:`sample solution <Non-Unique Sample solution>`. The maximal score then
is the score assigned to this solution.

.. code-block:: python

    import random

    class Factors(pyrope.Exercise):

        def parameters(self):
            a=random.randint(2, 9)
            b=random.randint(2, 9)
            return dict(a=a, b=b, product=a*b)

        def problem(self, a, b, product):

            return pyrope.Problem(
                'Give a proper divisor of <<product>>: <<divisor>>',
                divisor=pyrope.Natural(minimum=2, maximum=product-1)
            )

        def scores(self, product, divisor):
            return product % divisor == 0

        def a_solution(self, a):
            return a

If no score is given, PyRope needs a :ref:`unique sample solution <Unique
Sample Solution>` and determines the score from a comparison with this sample
solution. By default, a correct answer is scored one point and an incorrect
zero.

.. code-block:: python

    import random

    class IntegerDivision(pyrope.Exercise):

        def parameters(self):
            dividend = random.randint(2, 10)
            divisor = random.randint(1, dividend)
            return dict(dividend=dividend, divisor=divisor)

        def problem(self):
            return pyrope.Problem('''
                <<dividend>> divided by <<divisor>> is equal to
                <<quotient>> with remainder <<remainder>>.
                ''',
                quotient=pyrope.Natural(),
                remainder=pyrope.Natural(),
            )

        def the_solution(self, dividend, divisor):
            return dict(
                quotient=dividend // divisor,
                remainder=dividend % divisor
            )

In this example, the auto-scoring is equivalent to the following
:py:meth:`scores` method:

.. code-block:: python

    def scores(self, dividend, divisor, quotient, remainder):
        return (quotient == dividend // divisor) + (remainder == dividend % divisor)


Empty Input Fields
------------------

PyRope allows the learner to leave input fields empty, although a warning will
be issued before submitting the answers. Note that an instructor does not
have to bother about how to deal with empty inputs. PyRope will assume an
empty input field means the learner doesn't know the answer and score it
accordingly.

* In case of :ref:`Individual Input Field Scoring`, PyRope simply scores any
  empty input field with zero points. What happens behind the scenes is that
  PyRope inserts some valid (usually trivial) value into each empty input
  field before calling the :py:meth:`scores` method and ignores the
  corresponding score for this input.
* In case of :ref:`Joint Input Field Scoring`, it is not possible to score an
  exercise, if the learner leaves an input field empty and ignores the
  corresponding warning. PyRope will give zero points for the entire exercise
  in this case.

However, sometimes empty input fields have a special meaning. If you ask
for a solution of some equation, for example, then an empty input field can
also mean that there is no solution. In such cases, the instructor needs to
take care of scoring empty input fields. To deal with empty input manually,
the :py:meth:`scores` method must declare a default value for the respective
parameter, which will be substituted for an empty input.

* In case of :ref:`Individual Input Field Scoring`, PyRope will score only
  those empty input fields with zero points that do not have a default
  value. The scoring of empty input fields with default value is left to
  the :py:meth:`scores` method, called with the corresponding default values.
* In case of :ref:`Joint Input Field Scoring`, the entire exercise is scored
  with zero points unless every empty input field has a default value.
  Otherwise, scoring is left to the :py:meth:`scores` method, called with
  default values assigned to every variable of an empty input field.

In the :ref:`integer division example <IntegerDivision>` from above, for
example, we check two conditions and assign points if they are satisfied. The
first involves both input fields ``quotient`` and ``remainder``, the second
only ``remainder``. This means we can score the second condition even if
``quotient`` is left empty.

.. code-block:: python

    def scores(self, dividend, divisor, remainder, quotient=None):
        scores = 0
        if quotient is not None:
            if quotient * divisor + remainder == dividend:
                scores += 2
        if remainder < divisor:
            scores += 1
        return (scores, 3)
