
import abc
import ast
from fractions import Fraction
import numbers
import re
import tokenize

import numpy as np
import sympy

from sympy.core.numbers import Zero, One

from pyrope import config
from pyrope.errors import ValidationError


class TypeChecked:

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        ifields = {
            name: getattr(obj.ifields[name], self.name)
            for name in obj.ifields
        }
        for value in ifields.values():
            if value is None:
                return None
        value = obj.assemble(**ifields)
        value = obj.parse(value)
        if value is None:
            return None
        value = obj.cast(value)
        value = obj.normalize(value)
        obj.check_type(value)
        return value

    def __set__(self, obj, value):
        if value is None:
            for ifield in obj.ifields.values():
                setattr(ifield, self.name, None)
            return
        value = obj.parse(value)
        if value is None:
            return None
        value = obj.cast(value)
        value = obj.normalize(value)
        obj.check_type(value)
        for name, value in obj.disassemble(value).items():
            setattr(obj.ifields[name], self.name, value)


# c.f. https://bugs.python.org/issue39159
def safe_eval_string(s):
    if len(s) > config.maximum_input_length:
        raise ValidationError(
            f'Input size {len(s)} exceeds limit {config.maximum_input_length}.'
        )
    try:
        expr = ast.literal_eval(s)
    except (MemoryError, SyntaxError, TypeError, ValueError) as e:
        raise ValidationError(e)
    if expr is None:
        return s
    return expr


class DType(abc.ABC):

    def __init__(self, **kwargs):
        pass

    def __init_subclass__(cls):
        def validate_trivial_value(f):
            def wrapper(self):
                try:
                    trivial_value = f(self)
                    self.check_type(trivial_value)
                except ValidationError:
                    return None
                else:
                    return trivial_value
            return wrapper
        cls.trivial_value = validate_trivial_value(cls.trivial_value)

        def wrap_parsing(f):
            def wrapper(self, value):
                if isinstance(value, str):
                    if value == '':
                        return None
                    return f(self, value)
                return value
            return wrapper
        cls.parse = wrap_parsing(cls.parse)

    @property
    @abc.abstractmethod
    def dtype(self):
        ...

    @property
    @abc.abstractmethod
    def info(self):
        ...

    @abc.abstractmethod
    def trivial_value(self):
        ...

    @abc.abstractmethod
    def dummy_value(self):
        ...

    def parse(self, value):
        try:
            return safe_eval_string(value)
        except ValidationError:
            raise ValidationError(
                f"Cannot convert '{value}' to {self.dtype.__name__}."
            )

    def cast(self, value):
        return value

    def check_type(self, value):
        if not isinstance(value, self.dtype):
            raise ValidationError(
                f"Bad type: '{self.dtype.__name__}' expected, "
                f"got '{type(value).__name__}'."
            )

    def compare(self, LHS, RHS):
        return LHS == RHS

    def normalize(self, value):
        return value


class BooleanType(DType):

    dtype = bool

    @property
    def info(self):
        return 'a boolean'

    def trivial_value(self):
        return False

    def dummy_value(self):
        return True

    def parse(self, value):
        for bool_repr in config.boolean_representations:
            if value in bool_repr:
                return [False, True][bool_repr.index(value)]
        return value

    def cast(self, value):
        if isinstance(value, np.bool_):
            return value.item()
        return value


class ComplexType(DType):

    dtype = complex

    def __init__(self, rtol=0, atol=0, **kwargs):
        DType.__init__(self, **kwargs)
        if not isinstance(rtol, numbers.Real):
            raise ValueError("'rtol' must be real.")
        if not isinstance(atol, numbers.Real):
            raise ValueError("'atol' must be real.")
        self.tols = dict(rtol=rtol, atol=atol)

    @property
    def info(self):
        return 'a complex number'

    def trivial_value(self):
        return 0j

    def dummy_value(self):
        return 1j

    def parse(self, value):
        value = value.replace('i', 'j')
        value = value.replace(' ', '')
        value = value.replace('*j', 'j')
        try:
            return complex(value)
        except ValueError:
            raise ValidationError(
                "Complex number expected."
            )

    def cast(self, value):
        if isinstance(value, (np.integer, np.floating, np.complexfloating)):
            value = value.item()
        if isinstance(value, (int, float)):
            return complex(value)
        return value

    def compare(self, LHS, RHS):
        return np.isclose(LHS, RHS, **self.tols)


class DictType(DType):

    dtype = dict

    def __init__(self, count=None, **kwargs):
        DType.__init__(self, **kwargs)
        if count is not None:
            if not isinstance(count, int) or count < 0:
                raise ValueError(
                    'Number of dictionary elements must be a non-negative '
                    'integer.'
                )
        self.count = count

    @property
    def info(self):
        if self.count is None:
            return 'a dictionary'
        if self.count == 0:
            return 'an empty dictionary'
        return f'a dictionary with {self.count} elements'

    def trivial_value(self):
        return {}

    def dummy_value(self):
        if self.count is None:
            return {0: True}
        return {i: True for i in range(self.count)}

    def check_type(self, value):
        DType.check_type(self, value)
        if self.count is None:
            return
        if len(value) != self.count:
            raise ValidationError(
                f'Expected dictionary with {self.count} elements, not '
                f'{len(value)}.'
            )


class ExpressionType(DType):

    dtype = sympy.Expr

    def __init__(self, symbols=None, transformations=None, **kwargs):
        DType.__init__(self, **kwargs)
        if symbols is None:
            self.symbols = set()
        else:
            symbols = sympy.symbols(symbols)
            try:
                self.symbols = set(symbols)
            except TypeError:
                self.symbols = {symbols}
        if transformations is None:
            transformations = tuple(
                getattr(sympy.parsing.sympy_parser, transformation)
                for transformation in config.transformations
            )
        self.transformations = transformations

    @property
    def info(self):
        if not self.symbols:
            return 'an expression'
        return f'an expression in {self.symbols}'

    def trivial_value(self):
        return Zero()

    def dummy_value(self):
        return One()

    def parse(self, value):
        try:
            value = sympy.parse_expr(
                value, transformations=self.transformations
            )
        except (SyntaxError, TypeError, tokenize.TokenError) as e:
            raise ValidationError(e)
        e, i = sympy.symbols('e, i')
        if e not in self.symbols:
            value = value.subs(e, sympy.E)
        if i not in self.symbols:
            value = value.subs(i, sympy.I)
        return value

    def cast(self, value):
        if type(value) in (int, Fraction, float, complex):
            value = sympy.parse_expr(str(value))
        return value

    def compare(self, LHS, RHS):
        result = LHS.equals(RHS)
        if result is None:
            return False
        return result

    def check_type(self, value):
        DType.check_type(self, value)
        if not value.free_symbols <= self.symbols:
            if not self.symbols:
                raise ValidationError('Expression without variables expected.')
            else:
                raise ValidationError(
                    f'Expected an expression in {self.symbols}, '
                    f'not in {value.free_symbols}.'
                )


class EquationType(ExpressionType):

    dtype = sympy.Equality

    @property
    def info(self):
        if not self.symbols:
            return 'an equation'
        return f'an equation in {self.symbols}'

    def trivial_value(self):
        return sympy.Equality(Zero(), Zero(), evaluate=False)

    def dummy_value(self):
        return sympy.Equality(One(), Zero(), evaluate=False)

    def parse(self, value):
        if '=' not in value:
            raise ValidationError('An equation needs an equal sign.')
        if value.count('=') != 1:
            raise ValidationError(
                'Equation contains multiple equal signs.'
            )
        LHS, RHS = value.split('=')
        value = f'Eq({LHS}, {RHS}, evaluate=False)'
        return ExpressionType.parse(self, value)

    def check_type(self, value):
        DType.check_type(self, value)
        if not value.free_symbols <= self.symbols:
            if not self.symbols:
                raise ValidationError('Equation without variables expected.')
            else:
                raise ValidationError(
                    f'Expected an equation in {self.symbols}, '
                    f'not in {value.free_symbols}.'
                )


class PolynomialType(ExpressionType):

    dtype = sympy.Poly

    def __init__(self, degree=None, elementwise=False, **kwargs):
        ExpressionType.__init__(self, **kwargs)
        if degree is not None:
            if not isinstance(degree, int) or degree < 0:
                raise ValueError(
                    'Degree of a polynomial must be a non-negative integer.'
                )
        self.degree = degree
        self.elementwise = elementwise

    @property
    def info(self):
        if not self.symbols:
            return 'a constant polynomial'
        else:
            info = f'a polynomial in {self.symbols}'
            if self.degree is not None:
                info = f'{info} of degree {self.degree}'
            return info

    def dummy_value(self):
        value = One()
        if self.degree is None:
            return value
        for i in range(1, self.degree + 1):
            summand = Zero()
            for symbol in self.symbols:
                summand += symbol ** i
            value += summand
        return value

    def cast(self, value):
        if isinstance(value, sympy.Expr):
            if not self.symbols:
                value = value.as_poly(sympy.Symbol('_'))
            value = value.as_poly(*self.symbols)
        return value

    def compare(self, LHS, RHS):
        return ExpressionType.compare(self, LHS.as_expr(), RHS.as_expr())

    def check_type(self, value):
        ExpressionType.check_type(self, value)
        for gen in value.gens:
            if not gen.is_symbol:
                raise ValidationError('Expected a polynomial.')
        if self.degree is not None and value.degree() != self.degree:
            raise ValidationError(
                f'Expected a polynomial of degree {self.degree}, got a '
                f'polynomial of degree {value.degree()}.'
            )
        if self.elementwise is True:
            for coeff in value.all_coeffs():
                if not isinstance(coeff, sympy.Number):
                    raise NotImplementedError(
                        f'All coefficients have to be rational, got {coeff}.'
                    )


class LinearExpressionType(PolynomialType):

    def __init__(self, **kwargs):
        kwargs.pop('degree', None)
        PolynomialType.__init__(self, degree=1, **kwargs)

    @property
    def info(self):
        if not self.symbols:
            return 'a constant linear expression'
        return f'a linear expression in {self.symbols}'

    def check_type(self, value):
        ExpressionType.check_type(self, value)
        for gen in value.gens:
            if not gen.is_symbol:
                raise ValidationError('Expected a linear expression.')
        if value.degree() > self.degree:
            raise ValidationError(
                f'Expected a linear expression, got a polynomial of degree '
                f'{value.degree()}.'
            )
        if self.elementwise is True:
            for coeff in value.all_coeffs():
                if not isinstance(coeff, sympy.Number):
                    raise NotImplementedError(
                        f'All coefficients have to be rational, got {coeff}.'
                    )


class IntType(DType):

    dtype = int

    def __init__(self, minimum=None, maximum=None, **kwargs):
        DType.__init__(self, **kwargs)
        if not (minimum is None or isinstance(minimum, int)):
            raise ValueError('Minimum must be integer or None.')
        if not (maximum is None or isinstance(maximum, int)):
            raise ValueError('Maximum must be integer or None.')
        if minimum is not None and maximum is not None:
            if minimum >= maximum:
                raise ValueError('Minimum must be less than maximum.')
        self.minimum = minimum
        self.maximum = maximum

    @property
    def info(self):
        if self.minimum is None and self.maximum is None:
            return 'an integer'
        if self.maximum is None:
            return f'an integer greater or equal to {self.minimum}'
        if self.minimum is None:
            return f'an integer less or equal to {self.maximum}'
        return f'an integer between {self.minimum} and {self.maximum}'

    def trivial_value(self):
        return 0

    def dummy_value(self):
        if self.minimum is not None:
            return self.minimum
        if self.maximum is not None:
            return self.maximum
        return 1

    def parse(self, value):
        try:
            value = int(value)
        except ValueError:
            raise ValidationError(
                f"Cannot convert '{value}' to an integer."
            )
        return value

    def cast(self, value):
        if isinstance(value, (np.integer, np.floating, np.complexfloating)):
            value = value.item()
        if isinstance(value, float) and int(value) == value:
            return int(value)
        elif isinstance(value, complex):
            real = value.real
            if value.imag == 0 and int(real) == real:
                return int(real)
        return value

    def check_type(self, value):
        DType.check_type(self, value)
        if self.minimum is not None and value < self.minimum:
            raise ValidationError(
                f'Expected an integer greater or equal {self.minimum}, '
                f'got {value}.'
            )
        if self.maximum is not None and value > self.maximum:
            raise ValidationError(
                f'Expected an integer less or equal {self.maximum}, '
                f'got {value}.'
            )


class MatrixType(DType):

    dtype = np.ndarray
    sub_dtypes = (
        numbers.Integral, numbers.Rational, numbers.Real, numbers.Complex,
        numbers.Number
    )

    def __init__(
        self, nrows=None, ncols=None, sub_dtype=numbers.Number,
        compare='elementwise', rtol=0, atol=0, **kwargs
    ):
        DType.__init__(self, **kwargs)
        for dim, n in (('row', nrows), ('column', ncols)):
            if n is None:
                continue
            if not isinstance(n, int):
                raise ValueError(f'Number of {dim}s must be integer.')
            if not n >= 1:
                raise ValueError(
                    f'Number of {dim}s must be positive.'
                )
        if sub_dtype not in self.sub_dtypes:
            raise ValueError(
                f"'sub_dtype' must be one of {self.sub_dtypes}."
            )
        if compare not in ('elementwise', 'equality'):
            raise ValueError("'compare' must be 'elementwise' or 'equality'.")
        if not isinstance(rtol, numbers.Real):
            raise ValueError("'rtol' must be real.")
        if not isinstance(atol, numbers.Real):
            raise ValueError("'atol' must be real.")
        self.nrows = nrows
        self.ncols = ncols
        self.sub_dtype = sub_dtype
        self.comparison = compare
        self.tols = dict(rtol=rtol, atol=atol)

    @property
    def info(self):
        if self.nrows is None and self.ncols is None:
            info = 'a matrix'
        elif self.nrows is None:
            info = f'a matrix with {self.ncols} columns'
        elif self.ncols is None:
            info = f'a matrix with {self.nrows} rows'
        else:
            info = f'a {self.nrows}x{self.ncols} matrix'
        if self.sub_dtype == numbers.Number:
            return info
        return f'{info} of {self.sub_dtype.__name__} numbers'

    def trivial_value(self):
        return np.zeros((1, 1))

    def dummy_value(self):
        nrows = self.nrows
        ncols = self.ncols
        if nrows is None:
            nrows = 1
        if ncols is None:
            ncols = 1
        return np.array(np.zeros((nrows, ncols)))

    def cast(self, value):
        try:
            value = np.array(value)
            if np.all(np.real(value) == value):
                value = np.real(value)
            if np.all(value.astype(int) == value):
                value = value.astype(int)
        except ValueError:
            pass
        return value

    def check_type(self, value):
        DType.check_type(self, value)
        if value.size == 0:
            raise ValidationError('Empty matrix.')
        if len(value.shape) != 2:
            raise ValidationError(
                f'Expected two dimensions, not {len(value.shape)}.'
            )
        if self.nrows is not None and self.nrows != value.shape[0]:
            raise ValidationError(
                f'Expected {self.nrows} rows, not {value.shape[0]}'
            )
        if self.ncols is not None and self.ncols != value.shape[1]:
            raise ValidationError(
                f'Expected {self.ncols} columns, not {value.shape[1]}.'
            )
        for element in value.flat:
            if not isinstance(element, self.sub_dtype):
                raise ValidationError(
                    f'Entries must be {self.sub_dtype.__name__}s.'
                )

    def compare(self, LHS, RHS):
        if LHS.shape != RHS.shape:
            return 0.0
        comparison_matrix = np.isclose(LHS, RHS, **self.tols)
        if self.comparison == 'elementwise':
            return comparison_matrix.sum() / comparison_matrix.size
        if self.comparison == 'equality':
            return comparison_matrix.all()


class OneOfType(DType):

    dtype = None

    def __init__(self, options, **kwargs):
        DType.__init__(self, **kwargs)
        try:
            options = tuple(options)
        except TypeError:
            raise TypeError("'options' must be iterable.")
        if len(options) == 0:
            raise ValueError('No options given.')
        if len(options) == 1:
            raise ValueError('A single option is nonsense.')
        option_dtypes = {type(option) for option in options}
        if len(option_dtypes) != 1:
            raise TypeError(
                f'All options have to be of the same data type. '
                f'Found: {set({dtype.__name__ for dtype in option_dtypes})}.'
            )
        self.dtype = next(iter(option_dtypes))
        self.options = options

    @property
    def info(self):
        return f"one of '{self.options}'"

    def trivial_value(self):
        return self.options[0]

    def dummy_value(self):
        return self.options[-1]

    def parse(self, value):
        if self.dtype == str:
            return value
        return DType.parse(self, value)

    def check_type(self, value):
        DType.check_type(self, value)
        if value not in self.options:
            raise ValidationError(
                f"{value} is not in {self.options}."
            )


class RationalType(DType):

    dtype = Fraction

    @property
    def info(self):
        return 'a rational number'

    def trivial_value(self):
        return Fraction()

    def dummy_value(self):
        return Fraction(1, 2)

    def parse(self, value):
        try:
            return Fraction(value)
        except (ValueError, TypeError, ZeroDivisionError) as e:
            raise ValidationError(e)

    def cast(self, value):
        if isinstance(value, (int, float, sympy.Number)):
            return Fraction(str(value))
        return value


class RealType(DType):

    dtype = float

    def __init__(self, rtol=0, atol=0, **kwargs):
        DType.__init__(self, **kwargs)
        if not isinstance(rtol, numbers.Real):
            raise ValueError("'rtol' must be real.")
        if not isinstance(atol, numbers.Real):
            raise ValueError("'atol' must be real.")
        self.tols = dict(rtol=rtol, atol=atol)

    @property
    def info(self):
        return 'a real number'

    def trivial_value(self):
        return 0.0

    def dummy_value(self):
        return 0.5

    def parse(self, value):
        try:
            value = float(value)
        except ValueError:
            raise ValidationError(f"Cannot convert '{value}' to a float.")
        return value

    def cast(self, value):
        if isinstance(value, (np.integer, np.floating, np.complexfloating)):
            value = value.item()
        if isinstance(value, int):
            return float(value)
        elif isinstance(value, complex) and value.imag == 0:
            return float(value.real)
        return value

    def compare(self, LHS, RHS):
        return np.isclose(LHS, RHS, **self.tols)


class SetType(DType):

    dtype = set

    def __init__(self, count=None, compare='equality', **kwargs):
        DType.__init__(self, **kwargs)
        if count is not None:
            if not isinstance(count, int) or count < 0:
                raise ValueError(
                    'Number of set elements must be a non-negative integer.'
                )
        if compare not in {'equality', 'IoU'}:
            raise ValueError("'compare' must be 'equality' or 'IoU'.")
        self.comparison = compare
        self.count = count

    @property
    def info(self):
        if self.count is None:
            return 'a set'
        if self.count == 0:
            return 'an empty set'
        return f'a set with {self.count} elements'

    def trivial_value(self):
        return set()

    def dummy_value(self):
        if self.count is None:
            return {0}
        return set(range(self.count))

    def cast(self, value):
        if value == {}:
            return set()
        return value

    def check_type(self, value):
        DType.check_type(self, value)
        if self.count is None:
            return
        if len(value) != self.count:
            raise ValidationError(
                f'Expected set with {self.count} elements, not {len(value)}.'
            )

    def compare(self, LHS, RHS):
        if self.comparison == 'equality':
            return LHS == RHS
        if self.comparison == 'IoU':
            intersection = set.intersection(LHS, RHS)
            union = set.union(LHS, RHS)
            if len(union) == 0:
                return 1.0
            return len(intersection) / len(union)


class StringType(DType):

    dtype = str

    def __init__(
        self, ignore_case=False, strip=True, squash_whitespaces=False,
        **kwargs
    ):
        DType.__init__(self, **kwargs)
        self.ignore_case = ignore_case
        self.strip = strip
        self.squash_whitespaces = squash_whitespaces

    @property
    def info(self):
        if self.ignore_case is True:
            return 'a case insensitive string'
        else:
            return 'a string'

    def trivial_value(self):
        return ''

    def dummy_value(self):
        return 'PyRope'

    def parse(self, value):
        return value

    def cast(self, value):
        if isinstance(value, np.str_):
            return value.item()
        return value

    def normalize(self, value):
        if self.ignore_case is True:
            value = value.lower()
        if self.strip is True:
            value = value.strip()
        if self.squash_whitespaces is True:
            value = re.sub(r'\s+', ' ', value)
        return value


class TupleType(DType):

    dtype = tuple

    def __init__(self, count=None, **kwargs):
        DType.__init__(self, **kwargs)
        if count is not None:
            if not isinstance(count, int) or count < 0:
                raise ValueError(
                    f'Number of {self.dtype.__name__} elements must be a '
                    f'non-negative integer.'
                )
        self.count = count

    @property
    def info(self):
        if self.count is None:
            return f'a {self.dtype.__name__}'
        if self.count == 0:
            return f'an empty {self.dtype.__name__}'
        return f'a {self.dtype.__name__} with {self.count} elements'

    def trivial_value(self):
        return tuple()

    def dummy_value(self):
        if self.count is None:
            return (0,)
        return self.count * (0,)

    def cast(self, value):
        if isinstance(value, list):
            return tuple(value)
        return value

    def check_type(self, value):
        DType.check_type(self, value)
        if self.count is None:
            return
        if len(value) != self.count:
            raise ValidationError(
                f'Expected {self.dtype.__name__} with {self.count} elements, '
                f'got {len(value)}.'
            )


class ListType(TupleType):

    dtype = list

    def trivial_value(self):
        return []

    def dummy_value(self):
        if self.count is None:
            return [0]
        return self.count * [0]

    def cast(self, value):
        if isinstance(value, tuple):
            return list(value)
        return value


class VectorType(MatrixType):

    dtype = np.ndarray

    def __init__(self, count=None, orientation='column', **kwargs):
        if orientation not in ('row', 'column'):
            raise ValueError("'orientation' must either be 'column' or 'row'.")
        if count is not None:
            if not isinstance(count, int) or not count >= 1:
                raise ValueError(
                    "'count' must be an integer greater than or equal to 1."
                )
        for kw in ('nrows', 'ncols'):
            if kwargs.pop(kw, None) is not None:
                raise TypeError(
                    f"{self.__class__.__name__}.__init__() got an unexpected "
                    f"keyword argument '{kw}'."
                )
        compare = kwargs.pop('compare', 'elementwise')
        if compare not in ('elementwise', 'equality', 'up_to_multiple'):
            raise ValueError(
                "'compare' must be 'elementwise', 'equality' or "
                "'up_to_multiple'."
            )
        MatrixType.__init__(self, **kwargs)
        self.comparison = compare
        self.count = count
        self.orientation = orientation

    @property
    def info(self):
        if self.count is None:
            info = f'a {self.orientation} vector'
        else:
            info = f'a {self.count}-dimensional {self.orientation} vector'
        if self.sub_dtype == numbers.Number:
            return info
        return f'{info} of {self.sub_dtype.__name__} numbers'

    def trivial_value(self):
        return np.array([0])

    def dummy_value(self):
        if self.count is None:
            return np.array([0])
        return np.array([0] * self.count)

    def normalize(self, value):
        if isinstance(value, self.dtype):
            if (
                len(value.shape) == 2 and (
                    (value.shape[1] == 1 and self.orientation == 'column') or
                    (value.shape[0] == 1 and self.orientation == 'row')
                )
            ):
                value = value.flatten()
            return value

    def check_type(self, value):
        DType.check_type(self, value)
        if len(value.shape) != 1:
            raise ValidationError(
                f'Expected one dimension, not {len(value.shape)}.'
            )
        if self.count is not None and value.size != self.count:
            raise ValidationError(
                f'Expected a vector with {self.count} elements, '
                f'not {value.size}.'
            )
        for element in value:
            if not isinstance(element, self.sub_dtype):
                raise ValidationError(
                    f'Elements must be {self.sub_dtype.__name__}s.'
                )

    def compare(self, LHS, RHS):
        if LHS.shape[0] != RHS.shape[0]:
            return 0.0
        if self.comparison == 'up_to_multiple':
            if not LHS.any() or not RHS.any():
                return (LHS == RHS).all()
            else:
                if np.linalg.matrix_rank([LHS, RHS]) == 1:
                    return 1.0
                else:
                    return 0.0
        else:
            return MatrixType.compare(self, LHS, RHS)
