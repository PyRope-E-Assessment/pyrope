
Feedback
========

Feedback based on the learner's answers can be provided via the
:py:meth:`feedback` method. Note that it depends on the
:ref:`configuration <configuration>`, whether the feedback is shown to the user
or not.

.. code:: python

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
                return "Be honest: You knew the quiz, didn't you?"
            return 'You took three apples, so you have three!'

