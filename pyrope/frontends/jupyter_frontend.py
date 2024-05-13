
from base64 import b64encode
from functools import cached_property
from uuid import uuid4
import warnings

from ipykernel.comm import Comm
from IPython import get_ipython
from IPython.display import display, HTML, Javascript
from ipywidgets import widgets as ipy_widgets
import matplotlib.pyplot as plt
from nbconvert.filters.pandoc import convert_pandoc

from pyrope import config
from pyrope.formatters import TemplateFormatter
from pyrope.messages import (
    ChangeWidgetAttribute, CreateWidget, ExerciseAttribute, RenderTemplate,
    Submit, WaitingForSubmission, WidgetValidationError
)


def base64(obj):
    # Stringify objects and encode these strings with base64 before they are
    # inserted into a JavaScript snippet to avoid invalid JavaScript syntax
    # because of special characters etc.
    return b64encode(bytes(str(obj), 'utf-8')).decode('utf-8')


class JupyterFrontend:

    def __init__(self, widget_factory=None):
        if widget_factory is None:
            self.widget_factory = JupyterHtmlWidgetFactory()
        self.debug = False
        self.format = TemplateFormatter.format

        self.answers = {}
        self.hints = []
        self.parameters = {}
        self.max_total_score = None
        self.total_score = None
        self.runner = None
        self.widgets = {}

        # Get the IPython instance.
        self.ipy = get_ipython()

        # Load .css file for jupyter frontend styles.
        filepath = config.jupyter_frontend_css
        try:
            with open(filepath, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            warnings.warn(
                f'.css file for jupyter frontend styles not found: '
                f'{filepath}'
            )
        else:
            display(HTML(f'<style>\n{content}\n</style>'))

    def set_runner(self, runner):
        self.runner = runner
        self.runner.register_observer(self.observer)

    def formatter(self, template, allow_widgets=False, **kwargs):
        parameters = self.parameters
        template = self.format_ofields(template, **(parameters | kwargs))
        if allow_widgets:
            template = self.format(template, **self.widgets)
        template = self.markdown_to_html(template)
        return template

    def format_ofields(self, template, **kwargs):
        ofields = {}
        for name, ofield in kwargs.items():

            # Otherwise strings are rendered with '' or "".
            if not isinstance(ofield, str):
                ofield = self.ipython_format(ofield)

            # All output fields should be inline elements with no line breaks.
            ofield = ofield.replace('\n', '').strip()

            ofields[name] = ofield

        return self.format(template, **ofields)

    def ipython_format(self, obj):
        supported_mimetypes = [
            'text/html',
            'text/latex',
            'text/markdown',
            'image/png',
            'image/jpeg',
            'image/gif',
            'image/svg+xml',
            'text/plain',
        ]
        format = self.ipy.display_formatter.format
        format_dict, metadata = format(obj)

        # Check format_dict for one of the supported mimetypes in the specified
        # order and break the loop immediately after a representation is found.
        for mimetype in supported_mimetypes:
            representation = format_dict.get(mimetype, None)
            if representation is not None:
                match mimetype:
                    case 'image/png' | 'image/jpeg' | 'image/gif':
                        metadata = metadata.get(mimetype, {})
                        width = metadata.get('width', '')
                        height = metadata.get('height', '')
                        alt = metadata.get('alt', '')
                        return (
                            '<span class="pyrope">'
                            f'<img src="data:{mimetype};base64,'
                            f'{representation}" width="{width}" '
                            f'height="{height}" alt="{alt}">'
                            '</span>'
                        )
                    case 'text/html':
                        return (
                            '<span class="pyrope">'
                            f'{representation}'
                            '</span>'
                        )
                    case _:
                        return representation

        return repr(obj)

    def markdown_to_html(self, template):
        # Use basic markdown variant and add extensions used
        # by jupyter notebook manually.
        # documentation: https://pandoc.org/MANUAL.html
        markdown_extensions = [
            'markdown_strict',
            'backtick_code_blocks',
            'escaped_line_breaks',  # So that escaped line breaks are rendered.
            'pipe_tables',
            'strikeout',
            'task_lists',
            'tex_math_dollars',
        ]

        template = convert_pandoc(
            template, '+'.join(markdown_extensions), 'html',
            extra_args=[
                '--highlight-style=pygments',
                '--mathjax',
                '--wrap=none',  # Pandoc must not wrap text automatically.
            ]
        )

        return f'<div class="pyrope">{template}</div>'

    def render_preamble(self, preamble):
        display(JupyterSeparator())
        if preamble:
            display(HTML(self.formatter(preamble)))
            display(JupyterSeparator())

    def render_problem(self, template):
        display(HTML(self.formatter(template, allow_widgets=True)))

        # Prevent matplotlib from rendering a plot directly after an
        # exercise's preamble and problem are rendered.
        plt.close(fig='all')

    def render_feedback(self, feedback):
        feedback = self.formatter(feedback, **self.answers)
        display(Javascript(
            f'PyRope.set_inner_html(\'{self.submit_section.feedback_div_ID}\','
            f' \'{base64(feedback)}\')'
        ))
        score_string = ''
        if self.total_score is not None and self.max_total_score is not None:
            percentage = round(
                (self.total_score / self.max_total_score) * 100, 2
            )
            score_string = (
                f'Total Score: {self.total_score}/{self.max_total_score} '
                f'({percentage}%)'
            )
        elif self.total_score is not None:
            score_string = f'Total Score: {self.total_score}'
        elif self.max_total_score is not None:
            score_string = (
                f'Total Maximal Score: {self.max_total_score}'
            )
        display(Javascript(
            f'PyRope.set_inner_html(\'{self.submit_section.score_div_ID}\', '
            f'\'{base64(score_string)}\')'
        ))

        # Prevent matplotlib from rendering a plot directly after an
        # exercise's feedback is rendered. It is important to call plt.close
        # again because render_feedback is called asynchronously via the
        # submit button.
        plt.close(fig='all')

    def get_answers(self):
        self.submit, self.submit_anyway = True, False
        display(self.submit_section)

    def observer(self, msg):
        if isinstance(msg, ExerciseAttribute):
            if msg.attribute_name == 'debug':
                self.debug = msg.attribute_value
                self.submit_section = JupyterSubmitSection(frontend=self)

        with self.submit_section.debug:
            print(msg)

        if isinstance(msg, ExerciseAttribute):
            match msg.attribute_name:
                case 'parameters':
                    self.parameters = msg.attribute_value
                case 'hints':
                    self.hints = msg.attribute_value
                    self.submit_section.update_hint_btn()
                case 'answers':
                    self.answers = msg.attribute_value
                case 'max_total_score':
                    self.max_total_score = msg.attribute_value
                case 'total_score':
                    self.total_score = msg.attribute_value
        elif isinstance(msg, RenderTemplate):
            match msg.template_type:
                case 'preamble':
                    self.render_preamble(msg.template)
                case 'problem':
                    self.render_problem(msg.template)
                case 'feedback':
                    self.render_feedback(msg.template)
        elif isinstance(msg, CreateWidget):
            self.widgets[f'#{msg.widget_id}'] = self.widget_factory(
                msg.widget_type, self, msg.widget_id
            )
        elif isinstance(msg, WaitingForSubmission):
            self.get_answers()
        elif isinstance(msg, ChangeWidgetAttribute):
            widget = self.widgets[f'#{msg.widget_id}']
            if msg.attribute_name == 'value':
                self.submit_anyway = False
                self.submit_section.submit_btn.description = 'Submit'
            elif msg.attribute_name == 'valid' and msg.attribute_value is True:
                widget.change_hover_text(widget.description)
            setattr(widget, msg.attribute_name, msg.attribute_value)
        elif isinstance(msg, WidgetValidationError):
            widget = self.widgets[f'#{msg.widget_id}']
            widget.change_hover_text(msg.error)

    def notify(self, msg):
        self.runner.observer(msg)

    def disable_widgets(self):
        for widget in self.widgets.values():
            widget.disabled = True
        self.submit_section.disable_widgets()

    def display_widget_scores(self, show=True):
        for widget in self.widgets.values():
            widget.display_score(show=show)

    def display_widget_solutions(self, show=True):
        for widget in self.widgets.values():
            widget.display_solution(show=show)

    def display_widget_correct(self, show=True):
        for widget in self.widgets.values():
            widget.display_correct(show=show)


def escape_markdown(s):
    # cf. https://github.com/mattcone/markdown-guide/blob/master/_basic-syntax/escaping-characters.md  # noqa
    characters = (
        '\\', '`', '*', '_', '{', '}', '[', ']', '<', '>', '(', ')', '#',
        '+', '-', '.', '!', '|'
    )
    translation = str.maketrans({char: '\\' + char for char in characters})
    return s.translate(translation)


class JupyterSeparator(ipy_widgets.HTML):

    def __init__(self):
        super().__init__('<hr class="pyrope">')


class JupyterSubmitSection(ipy_widgets.VBox):

    def __init__(self, frontend):
        self.frontend = frontend
        self.submit_output = JupyterSubmitOutput(frontend)
        self.debug = JupyterDebugOutput()
        self.show_solutions = False
        self.feedback_div_ID = f'id_{uuid4().hex}'
        self.score_div_ID = f'id_{uuid4().hex}'

        if self.frontend.debug:
            btn_box = ipy_widgets.HBox((
                self.submit_btn, self.hint_btn, self.debug.clear_btn,
                self.solution_btn
            ))
        else:
            btn_box = ipy_widgets.HBox((self.submit_btn,))

        vspace = ipy_widgets.Box(layout={'height': '15px'})
        result = ipy_widgets.HTML(
            f'<div data-pyrope-id="{self.feedback_div_ID}" '
            f'class="pyrope feedback"></div>'
            f'<div data-pyrope-id="{self.score_div_ID}" '
            f'class="pyrope score"></div>'
        )
        children = (btn_box, vspace, self.submit_output, result)

        if self.frontend.debug:
            children += (JupyterSeparator(), vspace, self.debug, vspace)

        children += (JupyterSeparator(),)

        super().__init__(children)

    @cached_property
    def solution_btn(self):
        btn = ipy_widgets.Button(description='Show Solutions')

        def show(btn):
            self.show_solutions = True
            btn.description = 'Hide Solutions'
            self.frontend.display_widget_solutions(show=True)
            btn.on_click(show, remove=True)
            btn.on_click(hide)

        def hide(btn):
            self.show_solutions = False
            btn.description = 'Show Solutions'
            self.frontend.display_widget_solutions(show=False)
            btn.on_click(hide, remove=True)
            btn.on_click(show)

        btn.on_click(show)

        return btn

    @cached_property
    def hint_btn(self):
        btn = ipy_widgets.Button(description='Next Hint')

        def print_hint(_):
            hint = self.frontend.hints.pop(0)
            self.submit_output.print_template(hint)
            self.update_hint_btn()

        btn.on_click(print_hint)

        return btn

    def update_hint_btn(self):
        if len(self.frontend.hints) == 0:
            self.hint_btn.description = 'No Hints'
            self.hint_btn.disabled = True

    @cached_property
    def submit_btn(self):
        btn = ipy_widgets.Button(description='Submit')

        def finish_exercise():
            self.frontend.notify(Submit(self.frontend.__class__))
            self.frontend.disable_widgets()
            if not self.show_solutions:
                self.solution_btn.click()
            self.frontend.display_widget_scores()
            self.frontend.display_widget_correct()

        def f(btn):
            invalid_widgets = [
                widget for widget in self.frontend.widgets.values()
                if widget.valid == 'invalid'
            ]
            empty_widgets = [
                widget for widget in self.frontend.widgets.values()
                if widget.value is None or widget.value == ''
            ]

            if invalid_widgets or empty_widgets:
                self.submit, self.submit_anyway = False, True
                if invalid_widgets:
                    self.submit_output.print_template(
                        'There are invalid input fields.'
                    )
                if empty_widgets:
                    self.submit_output.print_template(
                        'There are empty input fields.'
                    )
            else:
                self.submit = True

            if self.submit_anyway:
                btn.description = 'Submit anyway?'
                btn.on_click(f, remove=True)
                btn.on_click(f_anyway)

            if self.submit:
                finish_exercise()

        def f_anyway(btn):
            if self.submit_anyway:
                finish_exercise()
            else:
                btn.on_click(f_anyway, remove=True)
                btn.on_click(f)
                f(btn)

        btn.on_click(f)

        return btn

    @property
    def submit(self):
        return self.frontend.submit

    @submit.setter
    def submit(self, value):
        if value is True:
            self.frontend.submit = True
        else:
            self.frontend.submit = False

    @property
    def submit_anyway(self):
        return self.frontend.submit_anyway

    @submit_anyway.setter
    def submit_anyway(self, value):
        if value is True:
            self.frontend.submit_anyway = True
        else:
            self.frontend.submit_anyway = False

    def disable_widgets(self):
        for widget in (
                self.submit_btn, self.hint_btn, self.solution_btn,
                self.debug.clear_btn
        ):
            widget.disabled = True


class JupyterSubmitOutput(ipy_widgets.HTML):

    def __init__(self, frontend):
        self.frontend = frontend
        self.div_ID = f'id_{uuid4().hex}'
        super().__init__(
            f'<div data-pyrope-id="{self.div_ID}" '
            f'class="pyrope submit-output"></div>'
        )

    def print_template(self, s):
        # frontend.formatter wraps 's' in a div element.
        child = self.frontend.formatter(s)
        display(Javascript(
            f'PyRope.append_child("{self.div_ID}", "{base64(child)}")'
        ))


class JupyterDebugOutput(ipy_widgets.Output):

    def __init__(self):
        super().__init__(layout={'border': '1px solid black'})
        self.append_stdout('Debug Messages:\n')

    @cached_property
    def clear_btn(self):
        btn = ipy_widgets.Button(description='Clear Debug')

        def f(_):
            self.clear_output()
            with self:
                print('Debug Messages:')
        btn.on_click(f)

        return btn


class JupyterWidgetResultSpan:

    def __init__(self):
        self.score_ID = f'id_{uuid4().hex}'
        self.solution_ID = f'id_{uuid4().hex}'
        self._score = ''
        self._solution = ''

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, value):
        self._score = str(value)
        display(Javascript(
            f'PyRope.set_inner_html(\'{self.score_ID}\', '
            f'\'{base64(self._score)}\')'
        ))

    @property
    def solution(self):
        return self._solution

    @solution.setter
    def solution(self, value):
        self._solution = str(value)
        display(Javascript(
            f'PyRope.set_inner_html(\'{self.solution_ID}\', '
            f'\'{base64(self._solution)}\')'
        ))

    def __str__(self):
        return (
            f'<span data-pyrope-id="{self.solution_ID}" '
            f'class="pyrope solution"></span>'
            f'<span data-pyrope-id="{self.score_ID}" '
            f'class="pyrope score"></span>'
        )


class JupyterHtmlWidget:

    def __init__(self, frontend, widget_id=None):
        self.ipy = get_ipython()
        self.frontend = frontend
        self.result_span = JupyterWidgetResultSpan()
        self.displayed_max_score = None
        self.displayed_score = None
        self.info = ''
        self.solution = ''
        self.correct = None
        self._description = ''
        self._disabled = False
        self._valid = 'valid'
        self._value = None

        if widget_id is not None:
            self.ID = f'id_{widget_id.hex}'
        else:
            self.ID = f'id_{uuid4().hex}'
        self.widget_id = widget_id

        display(Javascript(
            f'PyRope.create_widget_comm("{self.ID}");'
        ))
        self.comm = Comm(target_name=self.ID)

        def comm_target(comm, _):
            @comm.on_msg
            def receive(msg):
                self.value = msg['content']['data']['value']

        self.ipy.kernel.comm_manager.register_target(self.ID, comm_target)

    def __init_subclass__(cls):
        sub_cls_str = cls.__str__

        def new_str(self):
            return sub_cls_str(self) + str(self.result_span)

        cls.__str__ = new_str

    @property
    def description(self):
        if self._description == '':
            return self.info
        else:
            return self._description

    @description.setter
    def description(self, value):
        self._description = value

    @property
    def disabled(self):
        return self._disabled

    @disabled.setter
    def disabled(self, value):
        if value is True:
            self._disabled = True
        else:
            self._disabled = False
        self.comm.send({'disabled': self._disabled})

    @property
    def valid(self):
        return self._valid

    @valid.setter
    def valid(self, value):
        mapping = {
            True: 'valid',
            False: 'invalid',
            None: 'valid',
        }
        self._valid = mapping.get(value, '')
        self.comm.send({'className': f'pyrope {self._valid}'})

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if self._value != value:
            self._value = value
            self.comm.send({'value': self._value}, {'sync': True})
            self.frontend.notify(ChangeWidgetAttribute(
                self.__class__, self.widget_id, 'value', self._value
            ))

    def change_hover_text(self, text):
        self.comm.send({'title': str(text)})

    def display_score(self, show=True):
        if show:
            score_string = ''
            if (
                self.displayed_score is not None
                and self.displayed_max_score is not None
            ):
                score_string = '{}/{}'.format(
                    self.displayed_score, self.displayed_max_score
                )
            elif self.displayed_score is not None:
                score_string = f'{self.displayed_score}/?'
            elif self.displayed_max_score is not None:
                score_string = f'?/{self.displayed_max_score}'
            self.result_span.score = score_string
        else:
            self.result_span.score = ''

    def display_solution(self, show=True):
        if show and self.solution is not None:
            self.result_span.solution = self.solution
        else:
            self.result_span.solution = ''

    def display_correct(self, show=True):
        if show:
            mapping = {
                True: 'valid',
                False: 'invalid',
                None: '',
            }
            css_class = mapping.get(self.correct, '')
        else:
            css_class = ''
        self.comm.send({'className': f'pyrope {css_class}'})


class JupyterHtmlCheckbox(JupyterHtmlWidget):

    def __init__(self, *args):
        JupyterHtmlWidget.__init__(self, *args)
        self.checked = False

    def __str__(self):
        return (
            f'<input type="checkbox" data-pyrope-id="{self.ID}" '
            f'class="pyrope {self.valid}" '
            f'title="{self.description}" '
            f'{"checked " if self.checked else ""}'
            f'onclick="PyRope.send(\'{self.ID}\', this.checked)">'
        )

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if self._value != value:
            self._value = value
            self.comm.send({'checked': self._value}, {'sync': True})
            self.frontend.notify(ChangeWidgetAttribute(
                self.__class__, self.widget_id, 'value', self._value
            ))

    def display_solution(self, show=True):
        pass


class JupyterHtmlDropdown(JupyterHtmlWidget):

    def __init__(self, *args):
        JupyterHtmlWidget.__init__(self, *args)
        self.options = ()

    def __str__(self):
        html_options = ''.join([
            f'<option value="{option}">{escape_markdown(str(option))}</option>'
            for option in self.options
        ])
        html_options = (
                '<option value="" selected disabled hidden></option>' +
                html_options
        )
        return (
            f'<select data-pyrope-id="{self.ID}" '
            f'class="pyrope {self.valid}" '
            f'title="{self.description}" '
            f'onchange="PyRope.send(\'{self.ID}\', '
            f'this.options[this.selectedIndex].value)">'
            f'{html_options}'
            f'</select>'
        )


class _JupyterHtmlRadioButton(JupyterHtmlWidget):

    def __init__(self, group_ID, option):
        JupyterHtmlWidget.__init__(self, None, None)
        self.group_ID = group_ID
        self.option = option
        self.times_rendered = 0

    def __str__(self):
        return (
            f'<input type="radio" data-pyrope-id="{self.ID}" '
            f'class="pyrope {self.valid}" '
            f'name="{self.group_ID}_{self.times_rendered}" '
            f'title="{self.description}" '
            f'value="{self.option}" '
            f'onchange="PyRope.send(\'{self.group_ID}\', this.value); '
            f'PyRope.send(\'{self.ID}\', this.checked);">'
            f'<label class="pyrope">{escape_markdown(str(self.option))}'
            f'</label>'
        )

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.comm.send({'checked': value}, {'sync': True})


class JupyterHtmlRadioButtons(JupyterHtmlWidget):

    def __init__(self, *args):
        self.radio_buttons = []
        JupyterHtmlWidget.__init__(self, *args)
        self._options = ()
        self._correct = None
        self.times_rendered = 0
        self.vertical = False

    def __str__(self):
        self.times_rendered += 1
        for btn in self.radio_buttons:
            btn.times_rendered = self.times_rendered
        if self.vertical:
            table = ''.join([
                f'<tr><td>{btn}</td></tr>'
                for btn in self.radio_buttons
            ])
            return f'<table class="pyrope"><tbody>{table}</tbody></table>'
        else:
            return (
                '<span style="display: inline-block; width: 20px;"></span>'
                .join([str(btn) for btn in self.radio_buttons])
            )

    @property
    def correct(self):
        return self._correct

    @correct.setter
    def correct(self, value):
        self._correct = value
        for btn in self.radio_buttons:
            btn.correct = value

    @property
    def disabled(self):
        if self.radio_buttons:
            return self.radio_buttons[0].disabled
        else:
            return self._disabled

    @disabled.setter
    def disabled(self, value):
        for btn in self.radio_buttons:
            btn.disabled = value

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, value):
        self._options = value
        self.radio_buttons = [
            _JupyterHtmlRadioButton(self.ID, option)
            for option in self._options
        ]
        for btn in self.radio_buttons:
            btn.description = self.description

    @property
    def valid(self):
        if self.radio_buttons:
            return self.radio_buttons[0].valid
        else:
            return self._valid

    @valid.setter
    def valid(self, value):
        for btn in self.radio_buttons:
            btn.valid = value

    def change_hover_text(self, text):
        for btn in self.radio_buttons:
            btn.change_hover_text(text)

    def display_correct(self, show=True):
        for btn in self.radio_buttons:
            btn.display_correct()


class JupyterHtmlSlider(JupyterHtmlWidget):

    def __init__(self, *args):
        JupyterHtmlWidget.__init__(self, *args)
        self.label_ID = f'id_{uuid4().hex}'
        self.label_position = 'right'
        self.maximum = 100
        self.minimum = 0
        self.step = 1
        self.width = 25

    def __str__(self):
        label = (
            f'<label data-pyrope-id="{self.label_ID}" class="pyrope"></label>'
        )
        return (
            f'{label if self.label_position == "left" else ""}'
            f'<input type="range" data-pyrope-id="{self.ID}" '
            f'class="pyrope {self.valid}" '
            f'title="{self.description}" '
            f'min="{self.minimum}" max="{self.maximum}" step="{self.step}" '
            f'style="width: {self.width}%;" '
            f'oninput="PyRope.update_slider_label(\'{self.label_ID}\', '
            f'this.value)" '
            f'onmouseup="PyRope.send(\'{self.ID}\', this.value)" '
            f'ontouchend="PyRope.send(\'{self.ID}\', this.value)">'
            f'{label if self.label_position == "right" else ""}'
        )


class JupyterHtmlText(JupyterHtmlWidget):

    def __init__(self, *args):
        JupyterHtmlWidget.__init__(self, *args)
        self.placeholder = ''
        self.width = 20

    def __str__(self):
        return (
            f'<input type="text" data-pyrope-id="{self.ID}" '
            f'class="pyrope {self.valid}" '
            f'title="{self.description}" '
            f'placeholder="{self.placeholder}" '
            f'style="width: {self.width}ch;" '
            f'oninput="PyRope.send(\'{self.ID}\', this.value)">'
        )


class JupyterHtmlTextarea(JupyterHtmlText):

    def __init__(self, *args):
        JupyterHtmlText.__init__(self, *args)
        self.height = 4

    def __str__(self):
        return (
            f'<textarea data-pyrope-id="{self.ID}" '
            f'class="pyrope {self.valid}" '
            f'title="{self.description}" '
            f'placeholder="{self.placeholder}" '
            f'style="width: {self.width}ch;" '
            f'rows="{self.height}" '
            f'oninput="PyRope.send(\'{self.ID}\', this.value)">'
            '</textarea>'
        )


class JupyterHtmlWidgetFactory:

    mapping = {
        'Checkbox': JupyterHtmlCheckbox,
        'Dropdown': JupyterHtmlDropdown,
        'RadioButtons': JupyterHtmlRadioButtons,
        'Slider': JupyterHtmlSlider,
        'Text': JupyterHtmlText,
        'Textarea': JupyterHtmlTextarea,
    }

    def __call__(self, widget_type, frontend, widget_id=None):
        return self.mapping.get(widget_type, JupyterHtmlText)(
            frontend, widget_id
        )
