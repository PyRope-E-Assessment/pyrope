
import fractions
import math
import random
import sympy

from pyrope.core import Exercise
from pyrope.nodes import (
    Equation, Expression, Natural, Integer, Problem, Rational, Set
)


class Apples(Exercise):

    def problem(self):
        return Problem(
            '''
            If there are five apples and you take away three,
            how many do you have?

            <<number>>
            ''',
            number=Natural()
        )

    def the_solution(self):
        return 3

    def feedback(self, number):
        if number == 3:
            return "Be honest: You knew the quiz, didn't you?"
        return 'You took three apples, so you have three!'


class CinemaTickets(Exercise):

    def problem(self):
        return Problem(
            '''
            One grandmother, two mothers, two daughters and one granddaughter
            go to the cinema and buy one ticket each. How many tickets do they
            have to buy in total?

            <<number>>
            ''',
            number=Natural()
        )

    def the_solution(self):
        return 3

    def feedback(self, number):
        if number == 3:
            return "Be honest: You knew the problem, didn't you?"
        return (
            "The grandmother is also a mother and the mother is also "
            "a daughter."
        )


class Einstein(Exercise):

    def problem(self):
        return Problem(
            """
            Einstein's most famous formula, relating Energy $E$ and mass $m$
            via the speed of light $c$, reads $E=$<<RHS>>.
            """,
            RHS=Expression(symbols='m,c')
        )

    def the_solution(self):
        return sympy.parse_expr('m * c**2')


class Factor(Exercise):

    def problem(self):
        return Problem(
            'Give a factor of 42: <<answer>>',
            answer=Integer(minimum=1)
        )

    def scores(self, answer):
        return 42 % answer == 0

    def a_solution(self):  # prefix 'a_' indicates non-uniqueness
        return 7


#class Factorisation(Exercise):
#
#    def parameters(self):
#        return dict(
#            p=random.randint(2, 9),
#            q=random.randint(2, 9),
#        )
#
#    def problem(self, p, q):
#        return Problem(
#            fr'{p*q} = <<p_>> $\times$ <<q_>>',
#            p_=Integer(minimum=2),
#            q_=Integer(minimum=2),
#        )
#
#    def scores(self, p, q, p_, q_):
#        return p_ * q_ == p * q


class FourtyTwo(Exercise):

    def problem(self):
        return Problem(
            '''
            What is the answer to the Ultimate Question of Life, The Universe,
            and Everything?

            <<answer>>
            ''',
            answer=Natural()
        )

    def the_solution(self):
        return 42


class FreeLunch(Exercise):

    def problem(self):
        return Problem('Free lunch!')

    def scores(self):
        return 100


class IntegerDivision(Exercise):

    def parameters(self):
        dividend = random.randint(2, 10)
        divisor = random.randint(1, dividend)
        return dict(dividend=dividend, divisor=divisor)

    def problem(self):
        return Problem('''
            <<dividend>> divided by <<divisor>> is <<quotient>> with remainder <<remainder>>.
            ''',
            quotient=Natural(),
            remainder=Natural(),
        )

    def the_solution(self, dividend, divisor):
        return dict(
            quotient=dividend // divisor,
            remainder=dividend % divisor,
        )


class MultiplicationTable(Exercise):

    def parameters(self):
        return dict(
            a=random.randint(1, 10),
            b=random.randint(1, 10),
        )

    def problem(self):
        return Problem(r'<<a>> $\times$ <<b>> = <<c>>', c=Natural())

    def the_solution(self, a, b):
        return a * b


class PythagoreanTheorem(Exercise):

    def problem(self):
        return Problem(
            'The Pythagorean Theorem reads <<equation>>.',
            equation=Equation(symbols='a,b,c')
        )

    def the_solution(self):
        return sympy.parse_expr('Eq(a**2 + b**2, c**2)')


class RationalExample(Exercise):

    def problem(self):
        return Problem(
            '''
            A half is a third of it. What is it?

            <<number>>
            ''',
            number=Rational()
        )

    def the_solution(self):
        return fractions.Fraction(3, 2)


class Sextillion(Exercise):

    def problem(self):
        return Problem("A 'Sextillion' equals <<answer>>.", answer=Natural())

    def the_solution(self):
        return 1e21


class SumEqualsProduct(Exercise):

    def preamble(self):
        return r'You know that $2 + 2 = 2 \times 2$.'

    def problem(self):
        return Problem(
            '''
            Find a set of three different integers whose sum is equal to their
            product.

            <<numbers>>
            ''',
            numbers=Set(count=3)
        )

    def a_solution(self):
        return {1, 2, 3}

    def scores(self, numbers):
        return sum(numbers) == math.prod(numbers)


class SquareRoot(Exercise):

    def parameters(self):
        return {'root': random.randint(1, 10)}

    def problem(self, root):
        return Problem(
            f'The square root of {root**2} is <<root_>>.',
            root_=Natural()
        )
