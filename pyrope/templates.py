"""
This file contains templates for coding exercises in PyRope.
"""

import math
import random
import sympy

from pyrope.core import Exercise
from pyrope.nodes import Problem, Natural, Int, Expression, Dropdown

plaudits = (
    'Fine',
    'Nice',
    'Excellent',
    'Impressive',
    'Amazing',
    'Fantastic',
    'Outstanding',
    'Exceptional',
    'Brilliant',
    'Magnificent',
    'Superb',
    'Terrific',
    'Phenomenal',
    'Remarkable',
    'Spectacular',
    'Stunning',
    'Sublime',
    'Bravo',
)


def pigeonhole(p, levels, sublevels=1):
    try:
        nlevels = len(levels)
    except TypeError:
        nlevels = levels
        levels = range(nlevels)
    try:
        nsublevels = len(sublevels)
    except TypeError:
        nsublevels = sublevels
        sublevels = range(nsublevels)
    level, sublevel = divmod(
        math.floor((nlevels * nsublevels - 0.01) * p),
        nsublevels
    )
    if nsublevels == 1:
        return levels[level]
    return levels[level], sublevels[sublevel]


# The following is a minimalistic template without metadata or comments,
# including only the essential parts of an exercise. For writing custom
# quality exercises in PyRope, we recommend using the fully fledged template
# provided below.
#
class IntegerDivision(Exercise):

    def preamble(self):
        return r'''
            Integer division of two natural numbers, the *divisor* $m$ and
            the *dividend* $n$, results in an *integer quotient* $q$ and a
            *remainder* $r$ satisfying

            $$n=q\cdot m+r$$

            with

            $$0\leq r<m.$$
        '''

    def parameters(self):
        dividend = random.randint(10, 99)
        divisor = random.randint(2, dividend - 1)
        return dict(dividend=dividend, divisor=divisor)

    def problem(self):
        return Problem(
            '''
            <<dividend>> divided by <<divisor>> is equal to
            <<quotient>> with remainder <<remainder>>.
            ''',
            quotient=Natural(),
            remainder=Natural(),
        )

    def the_solution(self, dividend, divisor):
        return dict(
            quotient=dividend // divisor,
            remainder=dividend % divisor
        )

    def scores(self, dividend, divisor, quotient, remainder):
        scores = {'quotient': 0, 'remainder': 0}
        if quotient == dividend // divisor:
            scores['quotient'] = 2
        if remainder == dividend % divisor:
            scores['remainder'] = 1
        return scores

    def hints(self):
        yield '''
            Imagine you give a pizza party. You have ordered <<dividend>>
            pizzas for <<divisor>> people and want to share them in equal
            parts. How many entire pizzas can everyone eat?
        '''
        yield "That's the first answer, the *quotient*."
        yield 'How many pizzas will be left?'
        yield "That's the second answer, the *remainder*."

    def feedback(self, dividend, divisor, quotient, remainder):
        if None not in {quotient, remainder}:
            if quotient * divisor + remainder != dividend:
                return fr'''
                    ${quotient} \times {divisor} + {remainder}$
                    equals {quotient * divisor + remainder}, not
                    {dividend}.
                '''
        if remainder is not None and remainder >= divisor:
            return f'''
                Your remainder {remainder} is not smaller than the divisor
                {divisor}.
            '''


# The following is an extensive template for a PyRope exercise, including all
# recommended metadata and all relevant aspects of an exercise. For a minimal
# template without comments, see the example above.
#
class QuadraticEquation(Exercise):

    # Abstract
    #
    # Use the docstring to explain the exercise to another tutor, for example:
    #   * didactical motivation
    #   * exercise parameters
    #   * instance parameters
    #   * description of the randomization
    #   * corner cases like trivial or particularly difficult cases
    #   * typical errors or pitfalls
    #
    # The abstract may be accessed from a Python shell, an IDE or an exercise
    # pool browser.
    #
    #   >>> QuadraticEquation?
    #
    # Therefore, avoid putting the abstract into code comments, where it is
    # inaccessible.
    #
    # Use [Markdown syntax](https://www.markdownguide.org/basic-syntax/), so
    # that the description can be nicely formatted.
    #
    """
    Train knowledge and application of the quadratic formula.

    Exercise Parameters
    -------------------

    p_monic: float in [0,1], default=1/2
        Approximate probability that the coefficient of the quadratic term is
        1.
    w: triple of positive floats, default=(4, 4, 10)
        Weights for no, one and two distinct roots. The default weights are
        equal to the number of difficulty levels in each of these three cases
        (see below).
    small_ints: list of int, default: non-zero single digit integers
        Integers considered to be 'small' for use as roots or coefficients.
    big_ints: list of int, default: two digit integers
        Integers considered to be 'big' for use as roots or coefficients.
    nice_fracs: list of Fractions, default: fractions of nice integers
        Fractions considered to be 'nice' for use as roots or coefficients.

    Instance Parameters
    -------------------

    difficulty: float in [0,1], default: uniformly random
        Measure for difficulty, normed between 0 (trivial) and 1 (hard).
        The interval [0,1] is divided into equal subintervals, or 'levels'.

        Levels of difficulty for two simple roots:
             0: trivial case: double root at zero
             1: simple root at zero
             2: roots of a square
             3: double integer root
             4: small simple integer roots
             5: big simple integer roots
             6: one integer and one rational root
             7: simple rational roots
             8: quadratic formula with small integer coefficients
             9: quadratic formula with big integer coefficients
            10: quadratic formula with rational coefficients

        Levels of difficulty for a double root:
            0: trivial case: zero
            1: small integer root
            2: big integer root
            3: rational root

        Levels of difficulty for no roots:
            0: no linear term
            1: small integer coefficients
            2: big integer coefficients
            3: rational coefficients

    Remarks
    -------
    * We explicitly ask the number of roots for several reasons:
      * It can be determined independently of the discriminant.
      * If learners know there are two roots, but are unable to find them, they
        will still get more points than someone leaving all input fields empty.
      * The entered number of roots allows to distinguish between the two
        possible interpretations for empty input fields:
        * "I do not know how to compute the roots."
        * "There are no more roots."
    * Roots entered with the wrong sign get half the points.

    Caveats
    -------
    For simplicity, quadratic equations with complex coefficients are not
    modelled with this exercise.
    """

    # Provide exercise metadata via class attributes.
    #
    # The use of metadata is not mandatory, but strongly recommended. Please
    # provide at least an expressive title as a more descriptive reference of
    # your exercise than the class name, as well as a license and the origin.
    #
    # There is no explicit convention for metadata names either, but if you
    # stick to the naming used here, you facilitate easy filtering of exercise
    # pools based on keywords or search patterns. However, if you use names
    # from this template, they must be strings unless otherwise stated.
    #
    # Avoid metadata depending on context, such as a course name or the
    # difficulty of the exercise.

    # Short description of the exercise
    title = 'Quadratic equation'

    # Additional information
    subtitle = 'Solve a quadratic equation over the reals.'

    # Author with email
    authors = (
        'Konrad Schöbel <konrad.schoebel@htwk-leipzig.de>',
        'Paul Brassel <paul.brassel@htwk-leipzig.de>',
    )

    # Note that your exercise definitions are actually source code. So you
    # should choose a software license, preferably a liberal one to make your
    # exercises an Open Educational Resource.
    #
    # https://en.wikipedia.org/wiki/Open_educational_resources
    #
    license = '''
        GNU Affero General Public License <https://www.gnu.org/licenses/#AGPL>
    '''

    # URL to a publicly accessible repository, where this exercise and
    # possibly newer versions can be found.
    URL = 'https://github.com/PyRope-E-Assessment/pyrope.git'

    # PyRope version(s) this exercise has been tested with. Use a tuple to
    # enumerate multiple versions.
    pyrope_versions = '0.1.0', '0.1.1'

    # If your exercise is derived, inspired or translated from another one,
    # you can indicate this here for reference. Set to 'None' if you write it
    # from scratch.
    origin = None

    # The following categories serve to classify your exercise. Use a tuple
    # for each category, ordered by relevance.
    discipline = 'Mathematics'
    area = 'Calculus'
    topics = 'Polynomials', 'Quadratic Equations'
    keywords = (
        'quadratic equations',
        'quadratic formula',
        'zeros',
        'roots',
        "Vieta's formulas",
    )

    # Natural language in which the exercise is presented
    #
    # Note that an exercise can easily be translated into other languages by
    # replacing only the language specific methods, i.e. the preamble, the
    # problem statement, hints and feedback. Metadata, documentation and
    # comments should therefore be written in English.
    #
    language = 'English'

    # Taxonomy according to Bloom
    # https://en.wikipedia.org/wiki/Bloom%27s_taxonomy
    #
    # Tuple of cognitive domain levels, ordered by descending relevance:
    #   * 'knowledge'
    #   * 'comprehension'
    #   * 'application'
    #   * 'analysis'
    #   * 'synthesis'
    #   * 'evaluation'
    #
    taxonomy = 'application', 'knowledge'

    # Class variables
    small_ints = range(-9, 10)
    big_ints = range(-20, 21)

    # Exercise parameters should be defined in the Exercise class constructor
    # and stored as class attributes. These are parameters which determine
    # the behaviour of the exercise and should not change on repetitions of
    # the exercise within the same test or by the same user.
    #
    def __init__(
        self,
        p_monic=1 / 2,
        w=(4, 4, 10),
        small_ints=small_ints,
        big_ints=big_ints,
        nice_fracs=None,
    ):

        self.small_ints = tuple(set(small_ints) - {0})
        self.big_ints = tuple(set(big_ints) - set(small_ints) - {0})

        if nice_fracs is None:
            self.nice_fracs = list({
                sympy.Rational(p, q)
                for p in self.small_ints
                for q in self.small_ints
                if p % q
            })
        else:
            self.nice_fracs = nice_fracs

        self.p_monic = p_monic
        self.p = (w[0] / sum(w), (w[0] + w[1]) / sum(w))

    # The preamble is the place to put the exercise into context for the
    # learner, for example by providing information on
    #   * motivation
    #   * relevant theory
    #   * solution methods
    #   * pitfalls
    #   * scoring used
    #   * unusual input syntax
    #
    # Note that the preamble can easily be suppressed or changed by
    # subclassing the exercise and overriding this method. So please avoid
    # putting this context information into the problem template.
    #
    def preamble(self):
        return r'''
            A *quadratic equation* is an equation in one indeterminate $x$ of
            the form

            $$
                \begin{align*}
                    ax^2+bx+c&=0&
                    a&\not=0
                \end{align*}
            $$

            with given numbers $a$, $b$ and $c$. Since $a$ is not zero, we
            can divide this equation by $a$ to obtain the equivalent equation

            $$
                \begin{align*}
                    x^2+px+q&=0&
                    p&=\frac ba&
                    q&=\frac ca.
                \end{align*}
            $$

            The solutions of the quadratic equation are called *roots*. Their
            number is determined by the *discriminant*

            $$
                D=\left(\frac p2\right)^2-q.
            $$

            * If $D\geq0$, the two roots are different and given by the
            *Quadratic Formula*:

            $$
                x_{1/2}=-\frac p2\pm\sqrt{\left(\frac p2\right)^2-q}.
            $$

            * If $D=0$, both roots coincide and called a *double root*:

            $$
                x_1=x_2=-\frac p2
            $$

            * If $D<0$, there are no real roots.
        '''

    # You can also define proper (non PyRope) methods.
    #
    # We compute the coefficients and roots of the quadratic equation
    # separately for the following three cases:
    # * no roots
    # * double root
    # * two simple roots

    def no_roots(self, difficulty, monic):

        # discretize difficulty into 3 levels at 3 sublevels
        sublevels = (self.small_ints, self.big_ints, self.nice_fracs)
        level, coefs = pigeonhole(difficulty, 3, sublevels)

        a, c = random.sample(coefs, k=2)
        if monic:
            a = 1

        # ensure roots do not exist
        if a * c < 0:
            c *= -1

        # negative leading coefficient
        if level == 1 and not monic:
            a *= -1
            c *= -1

        # linear term
        b = 0
        if level == 2:
            D = math.sqrt(4 * a * c)
            b = math.trunc(random.uniform(-D, +D))

        return a, b, c

    def double_root(self, difficulty, monic):

        # discretize difficulty into 4 levels at 4 sublevels
        sublevels = ([1], self.small_ints, self.big_ints, self.nice_fracs)
        levels = ([0], self.small_ints, self.big_ints, self.nice_fracs)
        level, sublevel = pigeonhole(difficulty, levels, sublevels)

        # leading coefficient
        if monic:
            a = 1
        else:
            a = random.choice(sublevel)

        # double root
        x0 = random.choice(level)

        # binomial theorem
        p = -2 * x0
        q = x0**2

        return a, a * p, a * q, x0

    def simple_roots(self, difficulty, monic):

        a = None
        coefs = None

        # discretize difficulty into 10 levels
        level = pigeonhole(difficulty, 9)

        # simple root at zero
        if level == 0:
            x1 = 0
            x2 = random.choice(self.small_ints)

        # roots of a square
        if level == 1:
            x1 = random.choice(self.small_ints)
            x2 = -x1

        # small simple integer roots
        if level == 2:
            x1, x2 = random.sample(self.small_ints, k=2)

        # big simple integer roots
        if level == 3:
            x1, x2 = random.sample(self.big_ints, k=2)

        # one integer and one rational root
        if level == 4:
            x1 = random.choice(self.small_ints)
            x2 = random.choice(self.nice_fracs)
            if not monic:
                a = x2.denominator

        # simple rational roots
        if level == 5:
            x1, x2 = random.sample(self.nice_fracs, k=2)
            if not monic:
                a = math.lcm(x1.denominator, x2.denominator)

        # Up to this level, the roots are chosen randomly and the coefficients
        # are derived from the roots via Vieta's formulas.
        if level <= 5:

            # Vieta's Formulas
            p = -(x1 + x2)
            q = x1 * x2

            # leading coefficient
            if a is None:
                if monic:
                    a = 1
                else:
                    a = random.choice(self.small_ints)

            return a, a * p, a * q, x1, x2

        # Past this level, the coefficients are chosen randomly and the roots
        # are derived from the coefficients via the quadratic formula.

        # small integer coefficients
        if level == 6:
            coefs = self.small_ints

        # big integer coefficients
        if level == 7:
            coefs = self.big_ints

        # rational coefficients
        if level == 8:
            coefs = self.nice_fracs

        # choose coefficients randomly
        a, b, c = random.choices(coefs, k=3)
        if monic:
            a = 1

        # ensure roots exist
        if b**2 < 4 * a * c:
            c *= -1

        # quadratic formula
        a = sympy.Number(a)  # force symbolic expressions
        p_half = b / (2 * a)
        q = c / a
        x1 = -p_half + sympy.sqrt(p_half**2 - q)
        x2 = -p_half - sympy.sqrt(p_half**2 - q)

        return a, b, c, x1, x2

    # Instance parameters should be defined in the 'parameters' method. These
    # are parameters which may vary between repetitions of the exercise within
    # the same test or by the same user, just as the randomised parameters do.
    #
    # The following instance parameters will be provided by the exercise
    # runner:
    #   'difficulty': float in [0,1]
    #       A measure for the difficulty of the exercise, ranging from 0
    #       (trivial) to 1 (hard). For discrete levels of difficulty the
    #       interval [0,1] can be divided into subintervals, or 'levels'.
    #       Use this to allow the runner to make the exercise adaptive.
    #   'user_name': string
    #       The student's name. Used this to personalise the exercise.
    #   'user_ID': string
    #       The student's ID. Maybe used for individually reproducible
    #       parameter randomisation, e.g. via a random seed.
    #
    # Note that all instance parameters must have sensible default values,
    # as it can not be assured they are available in every exercise context.
    #
    def parameters(self, difficulty=random.random()):

        monic = (random.random() < self.p_monic)

        p = random.random()
        if p < self.p[0]:
            count = 0
            a, b, c = self.no_roots(difficulty, monic)
            x1 = x2 = None
        elif p < self.p[1]:
            count = 1
            a, b, c, x0 = self.double_root(difficulty, monic)
            x1 = x2 = x0
        else:
            a, b, c, x1, x2 = self.simple_roots(difficulty, monic)
            # We can not completely exclude that both roots coincide,
            # so better be sure here.
            count = 2 if x1 != x2 else 1

        x = sympy.symbols('x')
        qeq = sympy.Eq(a * x**2 + b * x + c, 0)

        return dict(
            a=sympy.Number(a), b=b, c=c, x1=x1, x2=x2, count=count, qeq=qeq,
            difficulty=difficulty
        )

    # The problem definition is mandatory. Avoid using information in the
    # template depending on context, such as the course name. Put this into
    # the preamble, which is easier to skip or change.
    #
    def problem(self, qeq):
        return Problem(
            '''
            The quadratic equation

            $$
                <<qeq:latex>>.
            $$

            has <<count_>> solutions:

            $x_1=$ <<x1_>>

            $x_2=$ <<x2_>>.

            (Leave input fields empty where necessary.)
            ''',
            count_=Int(minimum=0, maximum=2, widget=Dropdown(0, 1, 2)),
            x1_=Expression(),
            x2_=Expression(),
        )

    # A sample solution is provided via the 'the_solution' and 'a_solution'
    # methods. These are optional but mutually exclusive.
    #
    # The auto scoring needs to know whether a sample solution is unique or
    # not. A unique solution is provided via the 'the_solution' method and is
    # used to determine the maximal score and to check the correctness of the
    # user input.
    #
    # Note that in this example the following method could be entirely
    # omitted, due to the underscore naming convention for user input.
    #
    def the_solution(self, count, x1, x2):
        return dict(count_=count, x1_=x1, x2_=x2)

    # The auto scoring needs to know whether a sample solution is unique or
    # not. A non-unique solution is provided via the 'a_solution' method and
    # is used to determine the maximal score, but not to check the correctness
    # of the user input.
    #
    # def a_solution(self, ...):
    #   ...

    # Context sensitive, progressive hints can be provided using Python's
    # 'yield' statement.
    #
    def hints(self, x1, x2, count, a):

        if a != 1:
            yield f'Bring the leading coefficient {a} to one.'

        if x1 == 0 or x2 == 0:
            yield 'Do you see a common factor?'
            yield 'Factor it out.'
            yield 'When does a product vanish?'
            yield "If you don't see the shortcut, use the quadratic formula."

        if None not in {x1, x2} and x2 == -x1:
            yield 'Solve for $x^2$.'
            yield 'Be careful when you take the root on both sides.'
            yield "If you don't see the shortcut, use the quadratic formula."

        yield 'Compute the discriminant.'
        yield 'Deduce the number of solutions from the discriminant.'
        yield 'Now use the quadratic formula.'

    # Scoring
    def scores(self, a, b, c, x1, x2, count_, x1_=None, x2_=None):

        # no roots
        if x1 is None and x2 is None:
            return {'x1_': x1_ is None, 'x2_': x2_ is None}

        # default scores for roots:
        #   1.0 if correct
        #   0.5 if correct up to sign
        s1 = max(x1_ in {x1, x2}, (x1_ in {-x1, -x2}) / 2)
        s2 = max(x2_ in {x1, x2}, (x2_ in {-x1, -x2}) / 2)

        # double root
        if x1 == x2:
            if count_ == 1:
                # empty input fields are interpreted as repeated
                if x1_ is None:
                    s1 = s2
                if x2_ is None:
                    s2 = s1
            if count_ == 2:
                # empty input fields are interpreted as unknown
                if x1_ is None:
                    s1 = 0
                if x2_ is None:
                    s2 = 0

        # simple roots
        if x1 != x2:
            # do not score twice the same root if roots are different
            if x1_ == x2_:
                s2 = 0

        # see whether we can give grace points
        # other than for sign errors
        if None not in {x1_, x2_}:

            p = b / a
            q = c / a

            # Vieta
            p_ = -(x1_ + x2_)
            q_ = x1_ * x2_

            # +q instead of -q under the root
            if p_ == p and q != 0 and q_ == -q:
                s1 = s2 = 1 / 2

        # 'count' is autoscored
        return {'x1_': s1, 'x2_': s2}

    def feedback(self, x1, x2, count, x1_, x2_, count_, difficulty):

        # correct solution
        if {x1_, x2_, None} == {x1, x2, None}:
            if count_ == count:
                return pigeonhole(difficulty, plaudits) + '.'
            return 'Count your roots.'

        # sign flips
        if None not in {x1, x2, x1_, x2_} and x1 != 0 and x2 != 0:

            # sign flip in p
            if {x1_, x2_} == {-x1, -x2}:
                return r'''
                    Both your solutions have the wrong sign.
                    You probably forgot the minus sign of $-\frac p2$.
                '''

            # sign flip in q
            if x1_ + x2_ == x1 + x2 and x1_ * x2_ == -x1 * x2:
                return r'You used $+q$ instead of $-q$ under the root.'

        # no cross-check
        for x_ in {x1_, x2_}:
            if x_ is not None and x_ not in {x1, x2}:
                return 'Cross-check your solutions.'

        # no feedback otherwise
        return ''
