
from copy import deepcopy
from functools import cached_property
from uuid import uuid4

from pyrope.dtypes import TypeChecked
from pyrope.errors import ValidationError
from pyrope.formatters import TemplateFormatter


class Node:

    dtype = None
    value = TypeChecked()

    a_solution = TypeChecked()
    the_solution = TypeChecked()
    solution = TypeChecked()

    def __init__(self, template, ifields, treat_none_manually=False, **kwargs):
        self.ID = uuid4()
        self.parent = None
        ifields = {
            name: ifield.clone() for name, ifield in ifields.items()
        }

        if not isinstance(treat_none_manually, bool):
            raise ValueError("'treat_none_manually' has to be a boolean.")
        self.treat_none_manually = treat_none_manually

        for name, ifield in ifields.items():
            if not isinstance(ifield, Node):
                raise TypeError(
                    f'Input field {name} must be a Node subclass instance.'
                )
        names = tuple(
            name
            for _, name, _ in TemplateFormatter.parse(template)
            if name is not None
        )
        for name in ifields:
            if name in names:
                ifields[name].parent = self
            else:
                raise KeyError(f"Missing input field '{name}' in template.")

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

    @property
    def correct(self):
        correct = [ifield.correct for ifield in self.ifields.values()]
        if None in correct:
            return None
        return all(correct)

    @correct.setter
    def correct(self, value):
        for ifield in self.ifields.values():
            ifield.correct = value

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
