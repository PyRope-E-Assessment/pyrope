
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from pyrope.formatters import TemplateFormatter
from pyrope.messages import (
    ChangeWidgetAttribute, CreateWidget, ExerciseAttribute, RenderTemplate,
    Submit, WaitingForSubmission, WidgetValidationError
)


@dataclass
class ConsoleWidget:

    ID: UUID
    index: int
    info: str = ''
    valid: bool = None
    value: Any = None


class ConsoleFrontend:

    def __init__(self):
        self.answers = {}
        self.debug = False
        self.parameters = {}
        self.runner = None
        self.total_score, self.max_total_score = None, None
        self.widgets = {}

    def set_runner(self, runner):
        self.runner = runner
        runner.register_observer(self.observer)

    def formatter(self, template, **kwargs):
        return TemplateFormatter.format(
            template, **(self.parameters | kwargs)
        )

    def render_preamble(self, preamble):
        print(78 * '-')
        if preamble != '':
            print(self.formatter(preamble))
            print(78 * '-')

    def render_problem(self, template):
        fields = {
            f'#{widget_id}': f'[{widget.index}:____]'
            for widget_id, widget in self.widgets.items()
        }
        print(self.formatter(template, **fields))
        print(78 * '-')

    def render_feedback(self, feedback):
        print(78 * '-')
        if feedback != '':
            print(self.formatter(feedback, **self.answers))
            print(f'Total Score: {self.total_score}/{self.max_total_score}')
            print(78 * '-')

    def get_answers(self):
        while True:
            for widget_id, widget in self.widgets.items():
                value = widget.value
                if value is None:
                    value = '____'
                value = input(
                    f'[{widget.index}:{value}], {widget.info} >> '
                )
                self.notify(ChangeWidgetAttribute(
                    widget.__class__, widget_id, 'value', value
                ))
            submit = True
            if [
                widget for widget in self.widgets.values()
                if widget.valid is False
            ]:
                print('There are invalid input fields.')
                submit = False
            if submit is False:
                answer = input('Submit? >> ')
                if answer.strip().lower() in ('y', 'yes'):
                    submit = True
            if submit is True:
                self.notify(Submit(self.__class__))
                break

    def observer(self, msg):
        if self.debug:
            print(msg)

        if isinstance(msg, RenderTemplate):
            match msg.template_type:
                case 'preamble':
                    self.render_preamble(msg.template)
                case 'problem':
                    self.render_problem(msg.template)
                case 'feedback':
                    self.render_feedback(msg.template)
        elif isinstance(msg, CreateWidget):
            self.widgets[msg.widget_id] = ConsoleWidget(
                msg.widget_id, len(self.widgets)
            )
        elif isinstance(msg, ExerciseAttribute):
            match msg.attribute_name:
                case 'parameters':
                    self.parameters = msg.attribute_value
                case 'answers':
                    self.answers = msg.attribute_value
                case 'total_score':
                    self.total_score = msg.attribute_value
                case 'max_total_score':
                    self.max_total_score = msg.attribute_value
                case 'debug':
                    self.debug = msg.attribute_value
                    if self.debug:
                        print(msg)
        elif isinstance(msg, ChangeWidgetAttribute):
            match msg.attribute_name:
                case 'value':
                    self.widgets[msg.widget_id].value = msg.attribute_value
                case 'valid':
                    self.widgets[msg.widget_id].valid = msg.attribute_value
                case 'info':
                    self.widgets[msg.widget_id].info = msg.attribute_value
        elif isinstance(msg, WaitingForSubmission):
            self.get_answers()
        elif isinstance(msg, WidgetValidationError) and not self.debug:
            print(msg)

    def notify(self, msg):
        self.runner.observer(msg)
