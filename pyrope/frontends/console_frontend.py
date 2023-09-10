
from pyrope.formatters import TemplateFormatter
from pyrope.widgets import Widget


class ConsoleFrontend:

    def __init__(self, debug=False):
        self.debug = debug

    def set_runner(self, runner):
        self.runner = runner
        self.widget_index = {
            widget: f'{index}' for index, widget in enumerate(runner.widgets)
        }
        runner.register_observer(self.observer)

    def formatter(self, template, **kwargs):
        parameters = self.runner.get_parameters()
        return TemplateFormatter.format(
            template, **(parameters | kwargs)
        )

    def render_preamble(self, preamble):
        print(78 * '-')
        if preamble != '':
            print(self.formatter(preamble))

    def render_problem(self, template):
        fields = {
            f'#{widget.ID}': f'[{index}:____]'
            for widget, index in self.widget_index.items()
        }
        print(self.formatter(template, **fields))
        print(78*'-')

    def render_feedback(self, feedback):
        print(78 * '-')
        if feedback != '':
            print(self.formatter(feedback, **self.runner.get_answers()))
            print(78 * '-')

    def get_answers(self):
        runner = self.runner
        while True:
            for widget in runner.widgets:
                value = widget.value
                if value is None:
                    value = '____'
                value = input(
                    f'[{self.widget_index[widget]}:{value}], '
                    f'{widget.info} >> '
                )
                if value == '':
                    value = None
                runner.set_widget_value(widget, value)
            submit = True
            if runner.empty_widgets:
                print('There are empty input fields.')
                submit = False
            if runner.invalid_widgets:
                print('There are invalid input fields.')
                submit = False
            if submit is False:
                answer = input('Submit? >> ')
                if answer.strip().lower() in ('y', 'yes'):
                    submit = True
            if submit:
                runner.finish()
                break

    def observer(self, obj, owner, name, value):
        if isinstance(obj, Widget):
            origin = f'{self.widget_index[obj]}: <{owner.__name__}>'
            if name == 'error':
                print(f'{origin} {value}')
            elif self.debug:
                print(f'{origin} {name} set to {value}.')
        else:
            print(obj, owner, name, value)

    def display_error(self, e):
        msg = str(e)
        if e.ifield in self.widget_index:
            msg = f'{self.widget_index[e.ifield]}: ' + msg
        print(msg)
