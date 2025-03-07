
Preamble
========

With the :py:meth:`preamble` method you can put the exercise to be solved into
context for the learner, for example by providing information on:

* motivation
* relevant theory
* solution methods
* pitfalls
* scoring used or
* unusual input syntax

It depends on the :ref:`configuration <configuration>`, whether the preamble is
prepended to an exercise or not. Therefore, any information absolutely
necessary to solve the exercise should go into the
:ref:`problem template <template>`. On the other hand, since the preamble can
easily be suppressed or changed, you should avoid putting any other context
information into the problem template.

.. code:: python

    import random

    class Gauss(pyrope.Exercise):

        def preamble(self):
            return '''
                The legend says his teacher gave Carl Friedrich Gauß the
                task to sum all natural numbers from 1 through 100, hoping to
                occupy him for a while. But he immediately came up with the
                correct answer: 5050. How long will you need?
            '''

        def parameters(self):
            return dict(n=random.randint(10, 99))

        def problem(self):
            return pyrope.Problem(
                r'$1+2+3+\cdots+<<n:latex>>=$ <<sum_>>',
                sum_=pyrope.Natural()
            )

        def the_solution(self, n):
            return n * (n + 1) / 2

