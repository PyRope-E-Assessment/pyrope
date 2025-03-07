
Hints
=====

Hints can be provided to the learner via the :py:meth:`hints` method. Whether
or not the learner is allowed to request hints and how many depends on the
:ref:`configuration <configuration>`. Multiple hints can be given using
Python's ``yield`` statement.

.. code:: python

    import random

    class Gauss(pyrope.Exercise):

        def parameters(self):
            n = random.randint(10, 99)
            return dict(n=n, thesum=n * (n + 1) / 2)

        def problem(self):
            return pyrope.Problem(
                r'$1+2+3+\cdots+<<n:latex>>=$ <<thesum_>>',
                thesum_=pyrope.Natural()
            )

        def hints(self, n):
            yield '''
                The order of terms in a sum does not matter.
                Find a clever one.
            '''
            yield '''
                Sum in pairs: First and last, second and second-to-last,
                and so on.
            '''
            yield 'How many pairs do you have?'
            if n % 2 == 0:
                yield f'You have {n // 2} pairs.'
            else:
                yield f'After {n // 2} pairs a single number is left: {(n + 1) // 2}.'
