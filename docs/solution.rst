
Solution
========

Unique Sample Solution
----------------------

.. code-block:: python

    class Multiplication(pyrope.Exercise):

        def problem(self):
            return pyrope.Problem(
                'What is 6x7?  <<answer>>',
                answer=pyrope.Natural()
            )

        def the_solution(self):
            return 42


Non-Unique Sample Solution
--------------------------

.. code-block:: python

    class Factors(pyrope.Exercise):

        def problem(self):

            return pyrope.Problem(
                'Give a prime factor of 42: <<factor>>',
                factor=pyrope.Natural()
            )

        def score(self, factor):
            return factor in {2, 3, 7}

        def a_solution(self):
            return 7

Implicit Sample Solution
------------------------

.. code-block:: python

    import random

    class QuadraticEquation(pyrope.Exercise):

        def parameters(self):
            x=random.randint(1, 9)
            return dict(x=r, q=x**2)

        def problem(self, q):
            return Problem(
                'Give a root of the quadratic equation $x^2-<<q>>=0$.',
                x_=pyrope.Integer()
            )


