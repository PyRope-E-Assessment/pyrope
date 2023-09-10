
import ast
from copy import deepcopy
from fractions import Fraction
from functools import cached_property
import sympy
import tokenize
from uuid import uuid4

import numpy as np

from pyrope import config, widgets
from pyrope.core import ValidationError
from pyrope.dtypes import (
     BoolType, ComplexType, DictType, EquationType, ExpressionType, IntType,
     ListType, MatrixType, OneOfType, RationalType, RealType, SetType,
     StringType, TupleType, TypeChecked, VectorType
)
from pyrope.formatters import TemplateFormatter


class Node:

    dtype = None
    value = TypeChecked()

    a_solution = TypeChecked()
    the_solution = TypeChecked()
    solution = TypeChecked()

    def __init__(self, template, **ifields):
        self.ID = uuid4()
        self.parent = None
        ifields = {
            name: ifield.clone() for name, ifield in ifields.items()
        }

        for name, ifield in ifields.items():
            if not isinstance(ifield, Node):
                raise TypeError(
                    f'Input field {name} must be a Node subclass instance.'
                )
        names = tuple(
            name
            for _, name, _ in TemplateFormatter.parse(template or '')
            if name is not None
        )
        for name in ifields:
            if name in names:
                ifields[name].parent = self
            else:
                raise KeyError(f"Missing input field '{name}' in template.")

        if template is not None:
            self.template = template
        # order dict entries according to input field order in template
        self.ifields = {
            name: ifields[name] for name in names if name in ifields
        }
        self.ofields = names - ifields.keys()
        self._displayed_score = None

    def __str__(self):
        return TemplateFormatter.format(self.template, **self.ifields)

    def __repr__(self):
        cls = self.__class__
        return f'<{cls.__module__}.{cls.__name__} ID="{self.ID}">'

    @cached_property
    def name(self):
        if self.parent is None:
            return ''
        keys = list(self.parent.ifields.keys())
        values = list(self.parent.ifields.values())
        return keys[values.index(self)]

    @property
    def auto_max_score(self):
        return sum([
            ifield.auto_max_score
            for ifield in self.ifields.values()
        ])

    @property
    def displayed_max_score(self):
        return None

    @displayed_max_score.setter
    def displayed_max_score(self, value):
        # TODO: configure the max score distribution
        *all_but_last, last = self.ifields.keys()
        for name in all_but_last:
            self.ifields[name].displayed_max_score = None
        self.ifields[last].displayed_max_score = value

    @property
    def auto_score(self):
        return sum([
            ifield.auto_score
            for ifield in self.ifields.values()
        ])

    @property
    def displayed_score(self):
        return None

    @displayed_score.setter
    def displayed_score(self, value):
        # TODO: configure the score distribution
        *all_but_last, last = self.ifields.keys()
        for name in all_but_last:
            self.ifields[name].displayed_score = None
        self.ifields[last].displayed_score = value

    def assemble(self, **ifields):
        if len(self.ifields) != 1:
            raise NotImplementedError(
                f'No way how to assemble value of class '
                f'{self.__class__.__name__} from subfield values.'
            )
        return list(ifields.values())[0]

    def disassemble(self, value):
        if len(self.ifields) != 1:
            raise NotImplementedError(
                f'No way how to disassemble value '
                f'of class {self.__class__.__name__} into subfield values.'
            )
        return {list(self.ifields.keys())[0]: value}

    def cast(self, value):
        if self.dtype is None:
            return value
        return self.dtype.cast(value)

    def check_type(self, value):
        if self.dtype is None:
            return
        try:
            self.dtype.check_type(value)
        except ValidationError as e:
            e.ifield = self
            raise e

    def normalize(self, value):
        if self.dtype is None:
            return value
        return self.dtype.normalize(value)

    def compare(self, LHS, RHS):
        if self.dtype is None:
            return LHS == RHS
        return self.dtype.compare(LHS, RHS)

    def clone(self):
        clone = deepcopy(self)
        self.reset_IDs()
        return clone

    def reset_IDs(self):
        self.ID = uuid4()
        for ifield in self.ifields.values():
            ifield.reset_IDs()

    @cached_property
    def widgets(self):
        if self.ifields == {} and self.parent is not None:
            return (self,)
        widgets = tuple(self.ifields[name].widgets for name in self.ifields)
        return sum(widgets, ())

    @cached_property
    def info(self):
        ifield = self
        while ifield.parent is not None \
                and ifield.parent.parent is not None \
                and len(ifield.parent.ifields) == 1:
            ifield = ifield.parent
        return ifield.dtype.info


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

    def __init__(self, widget=None):
        if widget is None:
            widget = widgets.Checkbox()
        self.dtype = BoolType()
        Node.__init__(self, '<<_>>', _=widget)

    def assemble(self, _):
        if _ == '':
            return None
        return _


class Complex(Node):

    def __init__(self, elementwise=True, i_on_the='right', widget=None):
        if widget is None:
            widget = widgets.Text()
        self.dtype = ComplexType()
        if elementwise is True:
            _ = ElementwiseComplex(i_on_the=i_on_the, widget=widget)
        else:
            _ = Parser(widget, dtype=self.dtype)
        Node.__init__(self, '<<_>>', _=_)


class ElementwiseComplex(Node):

    def __init__(self, i_on_the='right', widget=None):
        if widget is None:
            widget_a = widgets.Text()
            widget_b = widgets.Text()
        else:
            widget_a = widget
            widget_b = widget.new_instance()
        self.dtype = ComplexType()
        if i_on_the == 'right':
            template = '<<a>> + <<b>> i'
        elif i_on_the == 'left':
            template = '<<a>> + i <<b>>'
        else:
            raise ValueError("Parameter 'i_on_the' must be 'left' or 'right'.")
        Node.__init__(
            self, template, a=Real(widget=widget_a), b=Real(widget=widget_b)
        )

    def assemble(self, **ifields):
        return ifields['a'] + ifields['b'] * 1j

    def disassemble(self, z):
        return {'a': z.real, 'b': z.imag}


class Dict(Node):

    def __init__(self, count=None, widget=None):
        if widget is None:
            widget = widgets.Text()
        self.dtype = DictType(count=count)
        Node.__init__(self, '<<_>>', _=Parser(widget, dtype=self.dtype))


class Expression(Node):

    def __init__(self, symbols=None, widget=None, **kwargs):
        if widget is None:
            widget = widgets.Text()
        self.dtype = ExpressionType(symbols=symbols)
        Node.__init__(self, '<<_>>', _=widget)
        if 'transformations' not in kwargs:
            kwargs['transformations'] = tuple(
                getattr(sympy.parsing.sympy_parser, transformation)
                for transformation in config.transformations
            )
        self.kwargs = kwargs

    def assemble(self, _):
        if _ == '':
            return None
        try:
            expr = sympy.parse_expr(_, **self.kwargs)
        except (SyntaxError, TypeError, tokenize.TokenError) as e:
            raise ValidationError(e)
        return expr

    def disassemble(self, value):
        return {'_': str(value)}


class Equation(Expression):

    def __init__(self, symbols=None, widget=None, **kwargs):
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

    def __init__(self, minimum=None, maximum=None, widget=None):
        self.dtype = IntType(minimum, maximum)
        if widget is None:
            if minimum is not None and maximum is not None:
                widget = widgets.Slider(minimum, maximum)
            else:
                widget = widgets.Text()
        Node.__init__(self, '<<_>>', _=Parser(widget, dtype=self.dtype))


class Matrix(Node):

    def __init__(self, widget=None, **kwargs):
        self.dtype = MatrixType(**kwargs)
        if widget is None:
            widget = widgets.Text()
        Node.__init__(self, '<<_>>', _=widget)

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


class _Vector(Matrix):

    def __init__(self, widget=None, **kwargs):
        self.dtype = VectorType(**kwargs)
        if widget is None:
            widget = widgets.Text()
        Node.__init__(self, '<<_>>', _=widget)


class ColumnVector(_Vector):

    def __init__(self, **kwargs):
        _Vector.__init__(self, orientation='column', **kwargs)


class RowVector(_Vector):

    def __init__(self, **kwargs):
        _Vector.__init__(self, orientation='row', **kwargs)


Vector = ColumnVector


class Natural(Int):

    def __init__(self, with_zero=True, widget=None):
        if not isinstance(with_zero, bool):
            raise ValueError("'with_zero' must be boolean.")
        minimum = 0
        if not with_zero:
            minimum = 1
        Int.__init__(self, minimum=minimum, widget=widget)


class OneOf(Node):

    def __init__(self, *args, widget=None):
        self.dtype = OneOfType(options=args)
        if widget is None:
            if len(args) <= 5:
                widget = widgets.RadioButtons(*args)
            else:
                widget = widgets.Dropdown(*args)
        Node.__init__(self, '<<_>>', _=Parser(widget, dtype=self.dtype))


class Rational(Node):

    def __init__(self, elementwise=True, widget=None):
        if widget is None:
            widget = widgets.Text()
        self.elementwise = elementwise
        self.dtype = RationalType()
        if self.elementwise is True:
            _ = ElementwiseRational(widget=widget)
        else:
            _ = widget
        Node.__init__(self, '<<_>>', _=_)

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

    def __init__(self, widget=None):
        if widget is None:
            widget_a = widgets.Text()
            widget_b = widgets.Text()
        else:
            widget_a = widget
            widget_b = widget.new_instance()
        self.dtype = RationalType()
        Node.__init__(
            self, '<<a>> / <<b>>', a=Int(widget=widget_a),
            b=Int(widget=widget_b)
        )

    def assemble(self, **ifields):
        return Fraction(ifields['a'], ifields['b'])

    def disassemble(self, q):
        return {'a': q.numerator, 'b': q.denominator}


class Real(Node):

    def __init__(self, widget=None):
        if widget is None:
            widget = widgets.Text()
        self.dtype = RealType()
        Node.__init__(self, '<<_>>', _=Parser(widget, dtype=self.dtype))


class Set(Node):

    def __init__(self, count=None, compare='equality', widget=None):
        if widget is None:
            widget = widgets.Text()
        self.dtype = SetType(count=count, compare=compare)
        Node.__init__(self, '<<_>>', _=Parser(widget, dtype=self.dtype))


class String(Node):

    def __init__(self, strip=False, widget=None):
        if widget is None:
            widget = widgets.Text()
        self.dtype = StringType(strip)
        Node.__init__(self, '<<_>>', _=widget)


class Tuple(Node):

    dtype = TupleType

    def __init__(self, count=None, widget=None):
        if widget is None:
            widget = widgets.Text()
        self.dtype = self.dtype(count=count)
        Node.__init__(self, '<<_>>', _=Parser(widget, dtype=self.dtype))


class List(Tuple):

    dtype = ListType
