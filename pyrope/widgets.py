
import inspect
import numbers

from pyrope import nodes
from pyrope.config import process_score
from pyrope.core import IllPosedError, ValidationError


class NotifyingAttribute:

    def __init__(self, dtype=str):
        self.dtype = dtype

    def __set_name__(self, owner, name):
        self.name = name
        self._name = '_' + name

    def __get__(self, obj, objtype=None):
        return getattr(obj, self._name)

    def __set__(self, obj, value):
        if not isinstance(value, self.dtype):
            raise TypeError(f'{self.name} has to be of type {self.dtype}.')
        setattr(obj, self._name, value)
        self.notify(obj)

    def notify(self, obj):
        value = getattr(obj, self._name)
        obj.notify(obj.__class__, 'attribute', {self.name: value})


class Widget(nodes.Node):

    description = NotifyingAttribute()

    def __init__(self, description=''):
        nodes.Node.__init__(self, None)
        self.observers = []
        self.description = description
        self._value = None
        self._valid = None
        self._the_solution = None
        self._a_solution = None
        self._solution = None
        self._show_solution = False
        self._show_score = False
        self._displayed_score = None
        self._show_max_score = False
        self._displayed_max_score = None
        self._correct = None
        self._show_correct = False

    @property
    def template(self):
        return f'<<#{self.ID}>>'

    def register_observer(self, observer):
        self.observers.append(observer)

    def notify(self, owner, name, value):
        for observer in self.observers:
            observer(self, owner, name, value)

    def observe_attributes(self):
        for _, obj in inspect.getmembers(self.__class__):
            if isinstance(obj, NotifyingAttribute):
                obj.notify(self)

    def new_instance(self):
        kwargs = {}
        for name, obj in inspect.getmembers(self.__class__):
            if isinstance(obj, NotifyingAttribute):
                kwargs[name] = getattr(self, name)
        return self.__class__(**kwargs)

    def validate(self):
        ifield = self
        while ifield.parent is not None and len(ifield.parent.ifields) == 1:
            ifield = ifield.parent
        try:
            # trigger type checking via get mechanism
            ifield.value
        except ValidationError as e:
            e.ifield = ifield
            raise e

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if self._value != value:
            self._value = value
            self.notify(self.__class__, 'attribute', {'value': value})
            try:
                self.validate()
            except ValidationError as e:
                self.valid = False
                self.notify(e.ifield.__class__, 'error', e)
            else:
                self.valid = None if value is None else True

    @property
    def valid(self):
        return self._valid

    @valid.setter
    def valid(self, value):
        self._valid = value
        self.notify(self.__class__, 'attribute', {'valid': value})

    @property
    def the_solution(self):
        return self._the_solution

    @the_solution.setter
    def the_solution(self, value):
        self._the_solution = value
        if value is None:
            return
        if self.solution is not None:
            ifield = self
            while ifield.parent is not None:
                if ifield.parent.parent is None:
                    break
                ifield = ifield.parent
            raise IllPosedError(
                f'Contradicting solutions for input field {ifield.name}.'
            )
        self.solution = value

    @property
    def a_solution(self):
        return self._a_solution

    @a_solution.setter
    def a_solution(self, value):
        self._a_solution = value
        if value is None:
            return
        if self.solution is not None:
            ifield = self
            while ifield.parent is not None:
                if ifield.parent.parent is None:
                    break
                ifield = ifield.parent
            raise IllPosedError(
                f'Contradicting solutions for input field {ifield.name}.'
            )
        self.solution = value

    @property
    def solution(self):
        return self._solution

    @solution.setter
    def solution(self, value):
        self._solution = value
        if self.show_solution is True:
            self.notify(self.__class__, 'attribute', {'solution': value})

    @property
    def show_solution(self):
        return self._show_solution

    @show_solution.setter
    def show_solution(self, value):
        self._show_solution = value
        self.notify(self.__class__, 'attribute', {'show_solution': value})
        if value is True:
            self.notify(
                self.__class__, 'attribute', {'solution': self.solution}
            )

    @property
    def auto_max_score(self):
        ifield = self
        while ifield.parent is not None and len(ifield.parent.ifields) == 1:
            ifield = ifield.parent
        solution = ifield.solution

        # If no maximal score is given, a (not necessarily unique) sample
        # solution must be provided.
        if solution is None:
            while ifield.parent is not None:
                if ifield.parent.parent is None:
                    break
                ifield = ifield.parent
            raise IllPosedError(
                f'Automatic setting of maximal score for {ifield.name} '
                f'needs a sample solution.'
            )

        return float(ifield.compare(solution, solution))

    @property
    def displayed_max_score(self):
        return (
            None if self._displayed_max_score is None
            else process_score(self._displayed_max_score)
        )

    @displayed_max_score.setter
    def displayed_max_score(self, value):
        self._displayed_max_score = value
        if self.show_max_score is True:
            self.notify(
                self.__class__, 'attribute',
                {'displayed_max_score': self.displayed_max_score}
            )

    @property
    def show_max_score(self):
        return self._show_max_score

    @show_max_score.setter
    def show_max_score(self, value):
        self._show_max_score = value
        self.notify(self.__class__, 'attribute', {'show_max_score': value})
        if value is True:
            self.notify(
                self.__class__, 'attribute',
                {'displayed_max_score': self.displayed_max_score}
            )

    @property
    def auto_score(self):
        ifield = self
        while ifield.parent is not None and len(ifield.parent.ifields) == 1:
            ifield = ifield.parent
        the_solution = ifield.the_solution

        # If no score is given, a unique sample solution must be provided.
        if the_solution is None:
            while ifield.parent is not None:
                if ifield.parent.parent is None:
                    break
                ifield = ifield.parent
            raise IllPosedError(
                f'Automatic scoring for {ifield.name} '
                f'needs a unique sample solution.'
            )

        # Empty or invalid input fields are scored with 0 points.
        try:
            value = ifield.value
        except ValidationError:
            self.correct = False
            return 0.0
        if value is None:
            self.correct = False
            return 0.0

        # If no score, but a unique sample solution is given, the input field
        # is scored by comparing it to this sample solution.
        score = float(ifield.compare(value, the_solution))

        if score == self.auto_max_score:
            self.correct = True
        else:
            self.correct = False

        return score

    @property
    def displayed_score(self):
        return (
            None if self._displayed_score is None
            else process_score(self._displayed_score)
        )

    @displayed_score.setter
    def displayed_score(self, value):
        self._displayed_score = value
        if self.show_score is True:
            self.notify(
                self.__class__, 'attribute',
                {'displayed_score': self.displayed_score}
            )

    @property
    def show_score(self):
        return self._show_score

    @show_score.setter
    def show_score(self, value):
        self._show_score = value
        self.notify(self.__class__, 'attribute', {'show_score': value})
        if value is True:
            self.notify(
                self.__class__, 'attribute',
                {'displayed_score': self.displayed_score}
            )

    @property
    def correct(self):
        return self._correct

    @correct.setter
    def correct(self, value):
        self._correct = value
        if self.show_correct is True:
            self.notify(self.__class__, 'attribute', {'correct': self.correct})

    @property
    def show_correct(self):
        return self._show_correct

    @show_correct.setter
    def show_correct(self, value):
        self._show_correct = value
        self.notify(self.__class__, 'attribute', {'show_correct': value})
        if value is True:
            self.notify(self.__class__, 'attribute', {'correct': self.correct})


class Checkbox(Widget):

    checked = NotifyingAttribute(dtype=bool)

    def __init__(self, checked=False, description=''):
        Widget.__init__(self, description=description)
        self._value = checked
        self.checked = checked


class Dropdown(Widget):

    options = NotifyingAttribute(dtype=tuple)

    def __init__(self, *args, description=''):
        Widget.__init__(self, description=description)
        self.options = args


class RadioButtons(Widget):

    options = NotifyingAttribute(dtype=tuple)
    vertical = NotifyingAttribute(dtype=bool)

    def __init__(self, *args, description='', vertical=True):
        Widget.__init__(self, description=description)
        self.options = args
        self.vertical = vertical


class Slider(Widget):

    label_position = NotifyingAttribute()
    maximum = NotifyingAttribute(dtype=numbers.Real)
    minimum = NotifyingAttribute(dtype=numbers.Real)
    step = NotifyingAttribute(dtype=numbers.Real)
    width = NotifyingAttribute(dtype=int)

    def __init__(
            self, minimum, maximum, description='', label_position='right',
            step=1, width=25
    ):
        Widget.__init__(self, description=description)
        if label_position not in ('left', 'right', 'neither'):
            raise ValueError(
                "'label_position' has to be either left, right or neither."
            )
        self.label_position = label_position
        self.maximum = maximum
        self.minimum = minimum
        self.step = step
        self.width = width


class Text(Widget):

    placeholder = NotifyingAttribute()
    width = NotifyingAttribute(dtype=int)

    def __init__(self, description='', placeholder='', width=20):
        Widget.__init__(self, description=description)
        self.placeholder = placeholder
        self.width = width


class Textarea(Text):

    height = NotifyingAttribute(dtype=int)

    def __init__(self, description='', height=4, placeholder='', width=50):
        Text.__init__(
            self, description=description, placeholder=placeholder, width=width
        )
        self.height = height


class WidgetFactory:

    mapping = {}

    def __call__(self, abstract_widget, *args):
        if self.mapping == {}:
            return abstract_widget
        widget = self.mapping[type(abstract_widget)]
        return widget(abstract_widget, *args)
