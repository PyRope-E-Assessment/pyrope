
from IPython.display import display
import pyrope_ipywidgets


from pyrope.messages import (
    ChangeWidgetAttribute, CreateWidget, ExerciseAttribute, RenderTemplate,
    WaitingForSubmission, WidgetValidationError
)


class JupyterFrontend:

    def __init__(self, widget_factory=None):
        self.answers = {}
        self.exercise = pyrope_ipywidgets.Exercise(self.notify)
        self.parameters = {}
        self.runner = None
        if widget_factory is None:
            self.widget_factory = JupyterWidgetFactory()
        else:
            self.widget_factory = widget_factory
        self.widgets = {}

    def set_runner(self, runner):
        self.runner = runner
        self.runner.register_observer(self.observer)

    def observer(self, msg):
        with self.exercise.debug_output:
            print(msg)
        if isinstance(msg, ExerciseAttribute):
            match msg.attribute_name:
                case 'answers':
                    self.answers = msg.attribute_value
                    self.exercise.ofields = self.parameters | self.answers
                case 'debug':
                    self.exercise.debug = msg.attribute_value
                case 'hints':
                    self.exercise.hints = msg.attribute_value
                case 'max_total_score':
                    self.exercise.max_total_score = msg.attribute_value
                case 'parameters':
                    self.parameters = msg.attribute_value
                    self.exercise.ofields = self.parameters
                case 'total_score':
                    self.exercise.total_score = msg.attribute_value
        elif isinstance(msg, RenderTemplate):
            match msg.template_type:
                case 'preamble':
                    self.exercise.render_preamble(msg.template)
                case 'problem':
                    self.exercise.widgets = self.widgets
                    self.exercise.render_problem(msg.template)
                case 'feedback':
                    self.exercise.render_feedback(msg.template)
        elif isinstance(msg, CreateWidget):
            widget = self.widget_factory(
                msg.widget_type, msg.widget_id, self.notify
            )
            self.widgets[f'#{msg.widget_id}'] = widget
        elif isinstance(msg, ChangeWidgetAttribute):
            widget = self.widgets[f'#{msg.widget_id}']
            setattr(widget, msg.attribute_name, msg.attribute_value)
        elif isinstance(msg, WidgetValidationError):
            widget = self.widgets[f'#{msg.widget_id}']
            widget.change_hover_text(msg.error.args[0])
        elif isinstance(msg, WaitingForSubmission):
            display(self.exercise)

    def notify(self, msg):
        self.runner.observer(msg)


class JupyterWidgetFactory:

    @staticmethod
    def define_mapping():
        return {
            'Checkbox': pyrope_ipywidgets.Checkbox,
            'RadioButtons': pyrope_ipywidgets.RadioButtons,
            'Slider': pyrope_ipywidgets.Slider,
            'Text': pyrope_ipywidgets.Text,
            'TextArea': pyrope_ipywidgets.TextArea,
        }

    def __call__(self, widget_type, widget_id, notification_callback):
        mapping = self.define_mapping()
        return mapping.get(widget_type, pyrope_ipywidgets.Text)(
            widget_id, notification_callback
        )
