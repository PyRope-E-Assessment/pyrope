
import ast
from fractions import Fraction
import numpy as np
import sympy
import tokenize

from pyrope import config
from pyrope.core import ValidationError
from pyrope.dtypes import (
     BoolType, ComplexType, DictType, EquationType, ExpressionType, IntType,
     ListType, MatrixType, OneOfType, RationalType, RealType, SetType,
     StringType, TupleType, VectorType
)
from pyrope.nodes import Checkbox, Dropdown, Node, RadioButtons, Slider, Text


class Problem(Node):

    dtype = DictType()

    def __init__(self, template, **ifields):
        Node.__init__(self, template, **ifields)

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


class Parser(Node):

    # c.f. https://docs.python.org/3/library/ast.html#ast.literal_eval
    dtypes = (str, int, float, complex, tuple, list, dict, set, bool)

    def __init__(self, ifield, dtype):
        Node.__init__(self, '<<_>>', _=ifield)
        if dtype.dtype not in self.dtypes:
            raise TypeError(f'Unable to parse data type {dtype.dtype}.')
        self.dtype = dtype

    # c.f. https://bugs.python.org/issue39159
    @staticmethod
    def safe_eval(s):
        if len(s) > config.maximum_input_length:
            raise ValidationError(
                f'Input size {len(s)} '
                f'exceeds limit {config.maximum_input_length}.'
            )
        try:
            expr = ast.literal_eval(s)
        except (MemoryError, SyntaxError, TypeError, ValueError) as e:
            raise ValidationError(e)
        return expr

    def assemble(self, _):
        if not isinstance(_, str) or self.dtype.dtype == str:
            return _
        if _ == '':
            return None
        value = self.safe_eval(_)
        if value is None:
            return _
        return value

    def disassemble(self, value):
        return {'_': str(value)}


class Bool(Node):

    def __init__(self, widget=Checkbox(), treat_none_manually=False):
        self.dtype = BoolType()
        Node.__init__(
            self, '<<_>>', _=widget, treat_none_manually=treat_none_manually
        )

    def assemble(self, _):
        if _ == '':
            return None
        return _


class Complex(Node):

    def __init__(
        self, elementwise=True, i_on_the='right', widget=Text(),
        treat_none_manually=False
    ):
        self.dtype = ComplexType()
        if elementwise is True:
            _ = ElementwiseComplex(
                i_on_the=i_on_the, widget=widget,
                treat_none_manually=treat_none_manually
            )
        else:
            _ = Parser(widget, dtype=self.dtype)
        Node.__init__(
            self, '<<_>>', _=_, treat_none_manually=treat_none_manually
        )


class ElementwiseComplex(Node):

    def __init__(
        self, i_on_the='right', widget=Text(), treat_none_manually=False
    ):
        self.dtype = ComplexType()
        if i_on_the == 'right':
            template = '<<a>> + <<b>> i'
        elif i_on_the == 'left':
            template = '<<a>> + i <<b>>'
        else:
            raise ValueError("Parameter 'i_on_the' must be 'left' or 'right'.")
        Node.__init__(
            self, template, a=Real(widget=widget), b=Real(widget=widget),
            treat_none_manually=treat_none_manually
        )

    def assemble(self, **ifields):
        return ifields['a'] + ifields['b'] * 1j

    def disassemble(self, z):
        return {'a': z.real, 'b': z.imag}


class Dict(Node):

    def __init__(self, count=None, widget=Text(), treat_none_manually=False):
        self.dtype = DictType(count=count)
        Node.__init__(
            self, '<<_>>', _=Parser(widget, dtype=self.dtype),
            treat_none_manually=treat_none_manually
        )


class Expression(Node):

    def __init__(
        self, symbols=None, widget=Text(), treat_none_manually=False,
        transformations=None
    ):
        self.dtype = ExpressionType(symbols=symbols)
        Node.__init__(
            self, '<<_>>', _=widget, treat_none_manually=treat_none_manually
        )
        if transformations is None:
            transformations = tuple(
                getattr(sympy.parsing.sympy_parser, transformation)
                for transformation in config.transformations
            )
        self.transformations = transformations

    def assemble(self, _):
        if _ == '':
            return None
        try:
            expr = sympy.parse_expr(_, transformations=self.transformations)
        except (SyntaxError, TypeError, tokenize.TokenError) as e:
            raise ValidationError(e)
        return expr

    def disassemble(self, value):
        return {'_': sympy.srepr(value)}


class Equation(Expression):

    def __init__(self, symbols=None, widget=Text(), **kwargs):
        Expression.__init__(self, symbols=symbols, widget=widget, **kwargs)
        self.dtype = EquationType(symbols=symbols)

    def assemble(self, _):
        if _ == '':
            return None
        if '=' not in _:
            raise ValidationError('An equation needs an equal sign.')
        if _.count('=') != 1:
            raise ValidationError('Equation contains multiple equal signs.')
        LHS, RHS = _.split('=')
        return Expression.assemble(self, f'Eq({LHS}, {RHS}, evaluate=False)')

    def disassemble(self, value):
        return {'_': f'{value.lhs}={value.rhs}'}


class Int(Node):

    def __init__(
        self, minimum=None, maximum=None, widget=None,
        treat_none_manually=False
    ):
        self.dtype = IntType(minimum, maximum)
        if widget is None:
            if minimum is not None and maximum is not None:
                widget = Slider(minimum, maximum)
            else:
                widget = Text()
        Node.__init__(
            self, '<<_>>', _=Parser(widget, dtype=self.dtype),
            treat_none_manually=treat_none_manually
        )


class Matrix(Node):

    def __init__(self, widget=Text(), treat_none_manually=False, **kwargs):
        self.dtype = MatrixType(**kwargs)
        Node.__init__(
            self, '<<_>>', _=widget, treat_none_manually=treat_none_manually
        )

    def assemble(self, _):
        if _ == '':
            return None
        value = Parser.safe_eval(_)
        try:
            value = np.array(value)
        except ValueError as e:
            raise ValidationError(e)
        return value

    def disassemble(self, value):
        return {'_': str(value.tolist())}


class Vector(Matrix):

    def __init__(self, widget=Text(), treat_none_manually=False, **kwargs):
        self.dtype = VectorType(**kwargs)
        Node.__init__(
            self, '<<_>>', _=widget, treat_none_manually=treat_none_manually
        )


class Natural(Int):

    def __init__(self, with_zero=True, **kwargs):
        if not isinstance(with_zero, bool):
            raise ValueError("'with_zero' must be boolean.")
        minimum = 0
        if not with_zero:
            minimum = 1
        Int.__init__(self, minimum=minimum, **kwargs)


class OneOf(Node):

    def __init__(self, *args, widget=None, treat_none_manually=False):
        self.dtype = OneOfType(options=args)
        if widget is None:
            if len(args) <= config.one_of_maximum_radio_buttons:
                widget = RadioButtons(*args)
            else:
                widget = Dropdown(*args)
        Node.__init__(
            self, '<<_>>', _=Parser(widget, dtype=self.dtype),
            treat_none_manually=treat_none_manually
        )


class Rational(Node):

    def __init__(
        self, elementwise=True, widget=Text(), treat_none_manually=False
    ):
        self.elementwise = elementwise
        self.dtype = RationalType()
        if self.elementwise is True:
            _ = ElementwiseRational(
                widget=widget, treat_none_manually=treat_none_manually
            )
        else:
            _ = widget
        Node.__init__(
            self, '<<_>>', _=_, treat_none_manually=treat_none_manually
        )

    def assemble(self, _):
        if _ == '':
            return None
        try:
            fraction = Fraction(_)
        except (ValueError, TypeError, ZeroDivisionError) as e:
            raise ValidationError(e)
        return fraction

    def disassemble(self, value):
        if self.elementwise:
            return Node.disassemble(self, value)
        return {'_': str(value)}


class ElementwiseRational(Node):

    def __init__(self, widget=Text(), treat_none_manually=False):
        Node.__init__(
            self, '<<a>> / <<b>>', a=Int(widget=widget), b=Int(widget=widget),
            treat_none_manually=treat_none_manually
        )

    def assemble(self, **ifields):
        return Fraction(ifields['a'], ifields['b'])

    def disassemble(self, q):
        return {'a': q.numerator, 'b': q.denominator}


class Real(Node):

    def __init__(self, widget=Text(), treat_none_manually=False):
        self.dtype = RealType()
        Node.__init__(
            self, '<<_>>', _=Parser(widget, dtype=self.dtype),
            treat_none_manually=treat_none_manually
        )


class Set(Node):

    def __init__(
        self, count=None, compare='equality', widget=Text(),
        treat_none_manually=False
    ):
        self.dtype = SetType(count=count, compare=compare)
        Node.__init__(
            self, '<<_>>', _=Parser(widget, dtype=self.dtype),
            treat_none_manually=treat_none_manually
        )


class String(Node):

    def __init__(self, strip=False, widget=Text(), treat_none_manually=False):
        self.dtype = StringType(strip)
        Node.__init__(
            self, '<<_>>', _=widget, treat_none_manually=treat_none_manually
        )


class Tuple(Node):

    dtype = TupleType

    def __init__(self, count=None, widget=Text(), treat_none_manually=False):
        self.dtype = self.dtype(count=count)
        Node.__init__(
            self, '<<_>>', _=Parser(widget, dtype=self.dtype),
            treat_none_manually=treat_none_manually
        )


class List(Tuple):

    dtype = ListType
