
Parameters
==========

Randomisation of exercises is achieved by generating arbitrary parameters in
the :py:meth:`parameters` method.


Static Exercises
----------------

Exercises that do not contain a :py:meth:`parameters` method are static, i.e.
do not change if run twice and have always the same answer.

.. code-block:: python

    class Multiplication(pyrope.Exercise):

        def problem(self):
            return pyrope.Problem(
                r'What is $6 \times 7$? <<answer>>',
                answer=pyrope.Natural()
            )

        def the_solution(self):
            return 42


Randomized Exercises
--------------------

To diversify exercises, you can generate arbitrary parameters via the
:py:meth:`parameters` method and return them in a dictionary. The keys of this
dictionary can then be used as parameters in other :py:class:`pyrope.Exercise`
methods.

.. code-block:: python

    import random

    class Multiplication(pyrope.Exercise):

        def parameters(self):
            return dict(
                a=random.randint(2, 9),
                b=random.randint(2, 9),
            )

        def problem(self):
            return pyrope.Problem(
                r'$<<a>> \times <<b>> =$ <<answer>>',
                answer=pyrope.Natural()
            )

        def the_solution(self, a, b):
            return a * b

Note that the parameters ``a`` and ``b`` are not needed in the
:py:meth:`problem` method of the above example, as they only appear in the
template string.


Global Parameters
-----------------

Parameters of the :py:meth:`parameters` method that have default values
are conѕidered *global parameters* and will be taken from a dictionary
``global_parameters`` provided to the :py:class:`ExerciseRunner` instance.
The default values assure that they will always have a valid value.

.. code-block:: python

    class Count(pyrope.Exercise):

        def parameters(self, username='John Doe'):
            return dict(count=len(username.replace(' ', '')))

        def problem(self):
            return pyrope.Problem('''
                Hello <<username>>!

                How many letters has your name? <<count_>>
                ''',
                count_=pyrope.Natural()
            )


Global parameters can be used to personalise exercises or adapting their
difficulty. Currently, PyRope only provides the following few global
parameters.

================  =====================  =================================
Global parameter  Type                   Meaning
================  =====================  =================================
``userID``        string                 user ID as provided from the
                                         authenticator
``username``      string                 user name
``difficulty``    float between 0 and 1  value parametrising the
                                         difficulty of the exercise
================  =====================  =================================
