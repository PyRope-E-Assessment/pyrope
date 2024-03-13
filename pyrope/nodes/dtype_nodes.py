
from fractions import Fraction

import sympy

from pyrope import config
from pyrope.dtypes import (
     BoolType, ComplexType, DictType, EquationType, ExpressionType, IntType,
     ListType, MatrixType, OneOfType, PolynomialType, RationalType, RealType,
     SetType, StringType, TupleType, VectorType
)
from pyrope.errors import ValidationError
from pyrope.nodes import Checkbox, Dropdown, Node, RadioButtons, Slider, Text


class Problem(Node):

    dtype = DictType()

    def __init__(self, template, **ifields):
        Node.__init__(self, template, ifields)

    def assemble(self, **ifields):
        return ifields

    def disassemble(self, ifields):
        return ifields

    @property
    def answers(self):
        ifields = {}
        for name in self.ifields:
            try:
                ifields[name] = self.ifields[name].value
            except ValidationError:
                ifields[name] = None
        return ifields

    def compare(self, LHS, RHS):
        return sum(
            ifield.compare(LHS[name], RHS[name])
            for name, ifield in self.ifields.items()
        ) / len(self.ifields)


class Bool(Node):

    def __init__(self, *, widget=Checkbox(), **kwargs):
        self.dtype = BoolType(**kwargs)
        Node.__init__(self, '<<_>>', {'_': widget}, **kwargs)


class Complex(Node):

    def __init__(
        self, *, elementwise=True, i_on_the='right', widget=Text(), **kwargs
    ):
        self.dtype = ComplexType(**kwargs)
        if elementwise is True:
            _ = ElementwiseComplex(
                i_on_the=i_on_the, widget=widget, **kwargs
            )
        else:
            _ = widget
        Node.__init__(self, '<<_>>', {'_': _}, **kwargs)


class ElementwiseComplex(Node):

    def __init__(self, *, i_on_the='right', widget=Text(), **kwargs):
        self.dtype = ComplexType(**kwargs)
        if i_on_the == 'right':
            template = '<<a>> + <<b>> i'
        elif i_on_the == 'left':
            template = '<<a>> + i <<b>>'
        else:
            raise ValueError("Parameter 'i_on_the' must be 'left' or 'right'.")
        Node.__init__(
            self, template, {
                'a': Real(widget=widget, **kwargs),
                'b': Real(widget=widget, **kwargs)
            }, **kwargs
        )

    def assemble(self, **ifields):
        return ifields['a'] + ifields['b'] * 1j

    def disassemble(self, z):
        return {'a': z.real, 'b': z.imag}


class Dict(Node):

    def __init__(self, *, widget=Text(), **kwargs):
        self.dtype = DictType(**kwargs)
        Node.__init__(self, '<<_>>', {'_': widget}, **kwargs)


class Expression(Node):

    def __init__(self, *, widget=Text(), **kwargs):
        self.dtype = ExpressionType(**kwargs)
        Node.__init__(self, '<<_>>', {'_': widget}, **kwargs)


class Equation(Node):

    def __init__(self, *, widget=Text(), **kwargs):
        self.dtype = EquationType(**kwargs)
        Node.__init__(self, '<<_>>', {'_': widget}, **kwargs)


class Int(Node):

    def __init__(self, *, widget=None, **kwargs):
        self.dtype = IntType(**kwargs)
        if widget is None:
            if (
                self.dtype.minimum is not None and
                self.dtype.maximum is not None
            ):
                widget = Slider(self.dtype.minimum, self.dtype.maximum)
            else:
                widget = Text()
        Node.__init__(self, '<<_>>', {'_': widget}, **kwargs)


class Matrix(Node):

    def __init__(self, *, widget=Text(), **kwargs):
        self.dtype = MatrixType(**kwargs)
        Node.__init__(self, '<<_>>', {'_': widget}, **kwargs)


class Vector(Matrix):

    def __init__(self, *, widget=Text(), **kwargs):
        self.dtype = VectorType(**kwargs)
        Node.__init__(self, '<<_>>', {'_': widget}, **kwargs)


class Natural(Int):

    def __init__(self, *, with_zero=True, **kwargs):
        if not isinstance(with_zero, bool):
            raise ValueError("'with_zero' must be boolean.")
        minimum = 0
        if not with_zero:
            minimum = 1
        Int.__init__(self, minimum=minimum, **kwargs)


class OneOf(Node):

    def __init__(self, *args, widget=None, **kwargs):
        self.dtype = OneOfType(options=args)
        if widget is None:
            if len(args) <= config.one_of_maximum_radio_buttons:
                widget = RadioButtons(*args)
            else:
                widget = Dropdown(*args)
        Node.__init__(self, '<<_>>', {'_': widget}, **kwargs)


class Polynomial(Node):

    def __init__(
            self, *, degree=None, elementwise=False, widget=Text(), **kwargs
    ):
        self.dtype = PolynomialType(degree=degree, **kwargs)
        if elementwise is True:
            _ = ElementwisePolynomial(degree, widget=widget, **kwargs)
            Node.__init__(self, '<<_>>', {'_': _}, **kwargs)
        else:
            Node.__init__(self, '<<_>>', {'_': widget}, **kwargs)


class ElementwisePolynomial(Node):

    def __init__(self, degree, *, widget=Text(), **kwargs):
        self.dtype = PolynomialType(degree=degree, elementwise=True, **kwargs)
        self.degree = degree
        if self.degree is None:
            raise ValueError(
                'Cannot render polynomials with an arbitrary degree '
                'elementwise.'
            )
        if len(self.dtype.symbols) >= 2:
            raise NotImplementedError(
                'Cannot render polynomials with more than one symbol '
                'elementwise.'
            )
        self.symbol = next(iter(self.dtype.symbols))
        tokens = [
            f'<<x_{i}>>${self.symbol}^{"{"}{i}{"}"}$'
            for i in range(self.degree, 1, -1)
        ]
        if self.degree >= 1:
            tokens.append(f'<<x_1>>${self.symbol}$')
        tokens.append('<<x_0>>')
        template = ' + '.join(tokens)
        Node.__init__(
            self, template, {
                f'x_{i}': Rational(elementwise=False, widget=widget, **kwargs)
                for i in range(0, self.degree + 1)
            }
        )

    def assemble(self, **ifields):
        return sympy.Poly.from_dict({
            i: ifields[f'x_{i}'] for i in range(0, self.degree + 1)
        }, self.symbol)

    def disassemble(self, value):
        coeffs = value.all_coeffs()[::-1]
        return {
            f'x_{i}': coeffs[i] for i in range(0, self.degree + 1)
        }


class Rational(Node):

    def __init__(self, *, elementwise=True, widget=Text(), **kwargs):
        self.elementwise = elementwise
        self.dtype = RationalType(**kwargs)
        if self.elementwise is True:
            _ = ElementwiseRational(widget=widget, **kwargs)
        else:
            _ = widget
        Node.__init__(self, '<<_>>', {'_': _}, **kwargs)


class ElementwiseRational(Node):

    def __init__(self, *, widget=Text(), **kwargs):
        self.dtype = RationalType(**kwargs)
        Node.__init__(
            self, '<<a>> / <<b>>', {
                'a': Int(widget=widget, **kwargs),
                'b': Natural(widget=widget, with_zero=False, **kwargs)
            }, **kwargs
        )

    def assemble(self, **ifields):
        return Fraction(ifields['a'], ifields['b'])

    def disassemble(self, q):
        return {'a': q.numerator, 'b': q.denominator}


class Real(Node):

    def __init__(self, *, widget=Text(), **kwargs):
        self.dtype = RealType(**kwargs)
        Node.__init__(self, '<<_>>', {'_': widget}, **kwargs)


class Set(Node):

    def __init__(self, *, widget=Text(), **kwargs):
        self.dtype = SetType(**kwargs)
        Node.__init__(self, '<<_>>', {'_': widget}, **kwargs)


class String(Node):

    def __init__(self, *, widget=Text(), **kwargs):
        self.dtype = StringType(**kwargs)
        Node.__init__(self, '<<_>>', {'_': widget}, **kwargs)


class Tuple(Node):

    dtype = TupleType

    def __init__(self, widget=Text(), **kwargs):
        self.dtype = self.dtype(**kwargs)
        Node.__init__(self, '<<_>>', {'_': widget}, **kwargs)


class List(Tuple):

    dtype = ListType
