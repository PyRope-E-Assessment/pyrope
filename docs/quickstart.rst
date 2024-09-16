===================
Quickstart Tutorial
===================

The following examples serve to get a glimpse on how exercises are modelled in
PyRope. For an extensive introduction with detailed explanations, please refer
to the :doc:`In-Depth Tutorial <tutorial>` or the :doc:`Reference Manual
<manual>`.

We recommend to develop exercises interactively within a Jupyter Notebook.
This is by far the simplest and fastest way, as it allows to seamlessly
alternate between writing code and testing it.  To follow the examples below,
you must import the PyRope module beforehand.

.. code:: ipython3

  import pyrope


Minimal Example
---------------

For simplicity, let us start with a static exercise that has single input
field with a fixed answer.  Copy the following code into a Notebook cell and
execute it by pressing ``Shift+Enter``.

.. code:: ipython3

  class FourtyTwo(pyrope.Exercise):

      def problem(self):
          return pyrope.Problem('''
              What is the answer to the Ultimate Question of Life, The Universe,
              and Everything?

              <<answer>>
              ''',
              answer=pyrope.Natural()
          )

      def the_solution(self):    # prefix 'the_' indicates uniqueness
          return 42


This *defines* the exercise.  To see if it *runs* as expected, execute the
following cell.

.. code:: ipython3

  FourtyTwo().run()

.. image:: FourtyTwo.png
  :alt: Exercise as shown to the learner


To rerun the exercise, simply execute the cell again.  If you are not
satisfied, you can go back, edit the code in the exercise definition and then
run the exercise again to see the effect of your changes.


Scoring
-------

Observe that we do not need to implement a method to score the answer in the
example above.  This is because PyRope has an auto-scoring mechanism, which by
default awards one point if the answer is correct and zero if not.  The
correctness of the answer is deduced from comparing it to the given sample
solution.  If you are not satisfied with the auto-scoring, you can implement
your own as follows.

.. code:: ipython3

  class FourtyTwo(pyrope.Exercise):

      def problem(self):
          return pyrope.Problem('''
              What is the answer to the Ultimate Question of Life, The Universe,
              and Everything?

              <<answer>>
              ''',
              answer=pyrope.Natural()
          )

      def scores(self, answer):
          if answer == 42:
              return 100
          else:
              return 0

      def the_solution(self):
          return 42


In the example above we still need to provide a sample solution.  This is
because the auto-scoring will deduce the maximal score from it.  Omitting the
sample solution will result in an error when submitting the answer, since
PyRope can not determine the maximal score.

.. code:: none

    ---------------------------------------------------------------------------
    IllPosedError                             Traceback (most recent call last)

    [...]

    IllPosedError: Unable to determine maximal score for input field 'answer'.

Alternatively, the maximal score can be given explicitly by returning a pair
instead of a single number from the ``scores`` method.

.. code:: ipython3

  class FourtyTwo(pyrope.Exercise):

      def problem(self):
          return pyrope.Problem('''
              What is the answer to the Ultimate Question of Life, The Universe,
              and Everything?

              <<answer>>
              ''',
              answer=pyrope.Natural()
          )

      def scores(self, answer):
          if answer == 42:
              return (100, 100)  # read "100 of 100"
          else:
              return (0, 100)  # read "0 of 100"


Sample Solution
---------------

Notice that in the above example the learner does not get the correct solution
as feedback for a wrong answer. This is why you should always implement a
sample solution.  After all, if you can not provide a solution, why should
your students?

A unique sample solution is provided via the method ``the_solution``.  If the
solution is not unique, you must use ``a_solution`` instead.

.. code:: ipython3

  class Factor(pyrope.Exercise):

      def problem(self):
          return pyrope.Problem(
              'Give a factor of 42: <<answer>>',
              answer=pyrope.Integer(minimum=1)
          )

      def scores(self, answer):
          return 42 % answer == 0

      def a_solution(self):  # prefix 'a_' indicates non-uniqueness
          return 7

In this case we still need to implement the ``scores`` method.  Otherwise the
auto-scoring can not determine the correctness of the answer and raises an
error when submitting the exercise.

.. code:: none

    ---------------------------------------------------------------------------
    IllPosedError                             Traceback (most recent call last)

    [...]

    IllPosedError: Automatic scoring for  needs a unique sample solution.


Randomisation
-------------

Let us now see how to randomise exercises.

.. code:: ipython3

  import random

  class SquareRoot(pyrope.Exercise):

      def parameters(self):
          return {'root': random.randint(1, 10)}

      def problem(self, root):
          return pyrope.Problem(
              f'The square root of {root**2} is <<answer>>.',
              answer=pyrope.Natural()
          )

      def scores(self, root, answer):
          return answer == root


Implicit solution
-----------------

Often the sample solution is one of the parameters, as in the example above.
In this case, there is no need to implement a sample solution or a scoring
method.  Instead, you can indicate that an input field has a particular
parameter as correct answer by appending an underscore to the parameter name
and let PyRope do the rest.

.. code:: ipython3

  import random

  class SquareRoot(pyrope.Exercise):

      def parameters(self):
          return {'root': random.randint(1, 10)}

      def problem(self, root):
          return pyrope.Problem(
              f'The square root of {root**2} is <<answer>>.',
              answer=pyrope.Natural()
          )

      def the_solution(self, root):
          return root


For input fields using this naming convention, the solution is assumed to be
unique.  This is why PyRope here automatically inserts the sample solution
into the feedback.


Multiple input fields
---------------------

If the exercise has more than one input field, then the solution method must
return a dictionary with the solutions for each input field.

.. code:: ipython3

  import random

  class IntegerDivision(pyrope.Exercise):

      def parameters(self):
          a = random.randint(1, 9)
          b = random.randint(1, a)
          return dict(a=a, b=b)

      def problem(self):
          return pyrope.Problem('''
              <<a>> divided by <<b>> is <<q_>> with remainder <<r_>>.
              ''',
              q_=pyrope.Natural(),
              r_=pyrope.Natural(),
          )

      def the_solution(self, a, b):
          return dict(q_=a // b, r_=a % b)


In cases where it is not possible to score input fields individually, you can
return an overall score from the ``scores`` method.

.. code:: ipython3

  import random

  class Factorisation(pyrope.Exercise):

      def parameters(self):
          return dict(
              p=random.randint(2, 9),
              q=random.randint(2, 9),
          )

      def problem(self, p, q):
          return pyrope.Problem(
              fr'{p*q} = <<p_>> $\times$ <<q_>>',
              p_=pyrope.Integer(minimum=2),
              q_=pyrope.Integer(minimum=2),
          )

      def scores(self, p, q, p_, q_):
          return p_ * q_ == p * q


Unit testing
------------

Examples may contain inconsistencies, for instance when providing both, a
maximal score and a sample solution, as in the following example..

.. code:: ipython3

  import random

  class SmallestPrime(pyrope.Exercise):

      def problem(self):
          return pyrope.Problem(
              r'What is the smallest prime number? <<answer>>',
              answer=pyrope.Natural()
          )

      def scores(self, answer):
          if answer == 2:
              return (1, 1)
          return (0, 1)

      def the_solution(self):
          return 1


To avoid this and other common mistakes, you can unit-test an exercise.

.. code:: none

    .........F...............
    ======================================================================
    FAIL: test_maximal_total_score_for_sample_solution (pyrope.tests.TestParametrizedExercise.test_maximal_total_score_for_sample_solution) (exercise=<class '__main__.SpotTheError'>)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "~/pyrope/venv/lib/python3.12/site-packages/pyrope/tests.py", line 101, in wrapped_test
        test(self, pexercise)
      File "~/pyrope/venv/lib/python3.12/site-packages/pyrope/tests.py", line 399, in test_maximal_total_score_for_sample_solution
        self.assertEqual(
    AssertionError: 0.0 != 1.0 : The sample solution does not get maximal total score.

    ----------------------------------------------------------------------
    Ran 25 tests in 0.045s

    FAILED (failures=1)

This helps to avoid execptions during exercise runs and to gain confidence on
third party exercises obtained from foreign sources.


Feedback
--------

.. code:: ipython3

  class Apples(pyrope.Exercise):

      def problem(self):
          return pyrope.Problem(
              '''
              If there are five apples and you take away three,
              how many do you have?

              <<number>>
              ''',
              number=pyrope.Natural()
          )

      def the_solution(self):
          return 3

      def feedback(self, number):
          if number == 3:
              return "Be honest! You knew the quiz, didn't you?"
          return 'You took three apples, so you have three!'


Hints
-----

.. code:: ipython3

  class HelpMe(pyrope.Exercise):

      def problem(self):
          return pyrope.Problem('''
              What is the answer to the Ultimate Question of Life, The Universe,
              and Everything?

              <<answer>>
              ''',
              answer=pyrope.Natural()
          )

      def the_solution(self):
          return 42

      def hints(self):
          yield "It is a number."
          yield 'You should read the "Hitchhiker\'s Guide to the Galaxy."'

