
import inspect
import numbers

from pyrope.config import process_score
from pyrope.errors import IllPosedError, ValidationError
from pyrope.messages import ChangeWidgetAttribute, WidgetValidationError
from pyrope.nodes import Node


class NotifyingAttribute:

    def __set_name__(self, owner, name):
        self.name = name
        self._name = '_' + name

    def __get__(self, obj, objtype=None):
        return getattr(obj, self._name)

    def __set__(self, obj, value):
        setattr(obj, self._name, value)
        self.notify(obj)

    def notify(self, obj):
        value = getattr(obj, self._name)
        obj.notify(ChangeWidgetAttribute(
            obj.__class__, obj.ID, self.name, value
        ))


class Widget(Node):

    description = NotifyingAttribute()

    def __init__(self, description=''):
        if not isinstance(description, str):
            raise ValueError("'description' has to be a string.")
        Node.__init__(self, '', {})
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

    @template.setter
    def template(self, value):
        pass

    def register_observer(self, observer):
        self.observers.append(observer)

    def notify(self, msg):
        for observer in self.observers:
            observer(msg)

    def observe_attributes(self):
        for _, obj in inspect.getmembers(self.__class__):
            if isinstance(obj, NotifyingAttribute):
                obj.notify(self)

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
            self.notify(ChangeWidgetAttribute(
                self.__class__, self.ID, 'value', value
            ))
            try:
                self.validate()
            except ValidationError as e:
                self.valid = False
                self.notify(WidgetValidationError(
                    e.ifield.__class__, e, self.ID
                ))
            else:
                self.valid = None if value is None else True

    @property
    def valid(self):
        return self._valid

    @valid.setter
    def valid(self, value):
        self._valid = value
        self.notify(ChangeWidgetAttribute(
            self.__class__, self.ID, 'valid', value
        ))

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
            self.notify(ChangeWidgetAttribute(
                self.__class__, self.ID, 'solution', value
            ))

    @property
    def show_solution(self):
        return self._show_solution

    @show_solution.setter
    def show_solution(self, value):
        self._show_solution = value
        self.notify(ChangeWidgetAttribute(
            self.__class__, self.ID, 'show_solution', value
        ))
        if value is True:
            self.notify(ChangeWidgetAttribute(
                self.__class__, self.ID, 'solution', self.solution
            ))

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
            self.notify(ChangeWidgetAttribute(
                self.__class__, self.ID, 'displayed_max_score',
                self.displayed_score
            ))

    @property
    def show_max_score(self):
        return self._show_max_score

    @show_max_score.setter
    def show_max_score(self, value):
        self._show_max_score = value
        self.notify(ChangeWidgetAttribute(
            self.__class__, self.ID, 'show_max_score', value
        ))
        if value is True:
            self.notify(ChangeWidgetAttribute(
                self.__class__, self.ID, 'displayed_max_score',
                self.displayed_max_score
            ))

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
            self.notify(ChangeWidgetAttribute(
                self.__class__, self.ID, 'displayed_score',
                self.displayed_score
            ))

    @property
    def show_score(self):
        return self._show_score

    @show_score.setter
    def show_score(self, value):
        self._show_score = value
        self.notify(ChangeWidgetAttribute(
            self.__class__, self.ID, 'show_score', value
        ))
        if value is True:
            self.notify(ChangeWidgetAttribute(
                self.__class__, self.ID, 'displayed_score',
                self.displayed_score
            ))

    @property
    def correct(self):
        return self._correct

    @correct.setter
    def correct(self, value):
        self._correct = value
        if self.show_correct is True:
            self.notify(ChangeWidgetAttribute(
                self.__class__, self.ID, 'correct', self.correct
            ))

    @property
    def show_correct(self):
        return self._show_correct

    @show_correct.setter
    def show_correct(self, value):
        self._show_correct = value
        self.notify(ChangeWidgetAttribute(
            self.__class__, self.ID, 'show_correct', value
        ))
        if value is True:
            self.notify(ChangeWidgetAttribute(
                self.__class__, self.ID, 'correct', self.correct
            ))


class Checkbox(Widget):

    checked = NotifyingAttribute()

    def __init__(self, checked=False, **kwargs):
        Widget.__init__(self, **kwargs)
        if not isinstance(checked, bool):
            raise ValueError("'checked' has to be a boolean.")
        self.checked = checked
        self._value = checked


class Dropdown(Widget):

    options = NotifyingAttribute()

    def __init__(self, *args, **kwargs):
        Widget.__init__(self, **kwargs)
        self.options = args


class RadioButtons(Widget):

    options = NotifyingAttribute()
    vertical = NotifyingAttribute()

    def __init__(self, *args, vertical=True, **kwargs):
        Widget.__init__(self, **kwargs)
        if not isinstance(vertical, bool):
            raise ValueError("'vertical' has to be a boolean.")
        self.options = args
        self.vertical = vertical


class Slider(Widget):

    label_position = NotifyingAttribute()
    maximum = NotifyingAttribute()
    minimum = NotifyingAttribute()
    step = NotifyingAttribute()
    width = NotifyingAttribute()

    def __init__(
            self, minimum, maximum, label_position='right', step=1, width=25,
            **kwargs
    ):
        Widget.__init__(self, **kwargs)
        if label_position not in ('left', 'right', 'neither'):
            raise ValueError(
                "'label_position' has to be either left, right or neither."
            )
        if (
            not isinstance(minimum, numbers.Real) or
            not isinstance(maximum, numbers.Real) or
            not minimum <= maximum
        ):
            raise ValueError(
                "'minimum' and 'maximum' have to be real numbers where "
                "'maximum' is greater than or equal to 'minimum'."
            )
        if not isinstance(step, numbers.Real) or step <= 0:
            raise ValueError("'step' has to be a positive real number.")
        if not isinstance(width, int) or not 0 <= width <= 100:
            raise ValueError(
                "'width' has to be an integer greater than or equal to 0 and "
                "less than or equal to 100."
            )
        self.label_position = label_position
        self.maximum = maximum
        self.minimum = minimum
        self.step = step
        self.width = width


class Text(Widget):

    placeholder = NotifyingAttribute()
    width = NotifyingAttribute()

    def __init__(self, placeholder='', width=20, **kwargs):
        Widget.__init__(self, **kwargs)
        if not isinstance(placeholder, str):
            raise ValueError("'placeholder' has to be a string.")
        if not isinstance(width, int) or width < 0:
            raise ValueError(
                "'width' has to be an integer greater than or equal to 0."
            )
        self.placeholder = placeholder
        self.width = width


class Textarea(Text):

    height = NotifyingAttribute()

    def __init__(self, height=4, width=50, **kwargs):
        kwargs['width'] = width
        Text.__init__(self, **kwargs)
        if not isinstance(height, int) or height < 0:
            raise ValueError(
                "'height' has to be an integer greater than or equal to 0."
            )
        self.height = height
