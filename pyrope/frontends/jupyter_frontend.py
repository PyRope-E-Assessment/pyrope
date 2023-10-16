
from functools import cached_property
import os
from pathlib import Path
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
from pyrope.widgets import (
    Checkbox, Dropdown, RadioButtons, Slider, Text, Textarea, Widget,
    WidgetFactory
)


class JupyterFrontend:

    def __init__(self, widget_factory=None, debug=False):
        if widget_factory is None:
            self.widget_factory = JupyterHtmlWidgetFactory()
        self.debug = debug
        self.format = TemplateFormatter.format

        self.total_max_score = None
        self.total_score = None

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
        self.submit_section = JupyterSubmitSection(frontend=self)
        self.widgets = {
            f'#{widget.ID}': self.widget_factory(widget, self.runner)
            for widget in self.runner.widgets
        }
        self.runner.register_observer(self.observer)

    def formatter(self, template, allow_widgets=False, **kwargs):
        parameters = self.runner.get_parameters()
        template = self.format_ofields(template, **(parameters | kwargs))
        if allow_widgets:
            template = self.format(template, **self.widgets)
        template = self.markdown_to_html(template)
        return template

    def format_ofields(self, template, **kwargs):
        relative_path = os.path.relpath(self.runner.exercise_dir, Path.cwd())
        ofields = {}
        for name, ofield in kwargs.items():

            # Set paths relative to the exercise directory.
            if isinstance(ofield, Path):
                ofield = str(relative_path / ofield)

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
            'hard_line_breaks',  # Preserve linebreaks from the template.
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

        # Remove linebreaks because they have no meaning in HTML.
        template = template.replace('\n', '')
        return f'<div class="pyrope">{template}</div>'

    def render_preamble(self, preamble):
        if preamble:
            display(HTML(self.formatter(preamble)))

    def render_problem(self, template):
        display(HTML(self.formatter(template, allow_widgets=True)))

        # Prevent matplotlib from rendering a plot directly after an
        # exercise is rendered. This also clears the current figure
        # for the next exercise.
        plt.close()

    def render_feedback(self, feedback):
        feedback = self.formatter(feedback, **self.runner.get_answers())
        # Otherwise the following JavaScript snippet could have invalid syntax.
        feedback = feedback.replace("'", r"\'")
        display(Javascript(
            f'PyRope.set_inner_html(\'{self.submit_section.feedback_div_ID}\','
            f' \'{feedback}\')'
        ))
        score_string = ''
        if self.total_score is not None and self.total_max_score is not None:
            percentage = round(
                (self.total_score / self.total_max_score) * 100, 2
            )
            score_string = (
                f'Total Score: {self.total_score}/{self.total_max_score} '
                f'({percentage}%)'
            )
        elif self.total_score is not None:
            score_string = f'Total Score: {self.total_score}'
        elif self.total_max_score is not None:
            score_string = (
                f'Total Maximal Score: {self.total_max_score}'
            )
        display(Javascript(
            f'PyRope.set_inner_html(\'{self.submit_section.score_div_ID}\', '
            f'\'{score_string}\')'
        ))

    def get_answers(self):
        self.submit, self.submit_anyway = True, False
        display(self.submit_section)
        if self.debug:
            self.runner.get_solutions()

    def observer(self, obj, owner, name, value):
        if isinstance(obj, Widget):
            widget = self.widgets[f'#{obj.ID}']
            if name == 'attribute':
                attr_name, attr_value = list(value.items())[0]
                if attr_name == 'value':
                    self.submit_anyway = False
                    self.submit_section.submit_btn.description = 'Submit'
                elif attr_name == 'valid' and attr_value is True:
                    widget.change_hover_text(widget.description)
                setattr(widget, attr_name, attr_value)
            elif name == 'error':
                widget.change_hover_text(value)
        elif name == 'total_max_score':
            self.total_max_score = value
        elif name == 'total_score':
            self.total_score = value

        with self.submit_section.debug:
            if name == 'error':
                print(f'{owner} {value}')
            elif name == 'attribute':
                attr_name, attr_value = list(value.items())[0]
                print(f'{repr(obj)} {attr_name} set to {attr_value}.')
            else:
                print(f'{repr(obj)} {name} set to {value}.')

    def display_error(self, e):
        try:
            with self.submit_section:
                print(e)
        except AttributeError:
            display(e)

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


def escape_markdown(s):
    # cf. https://github.com/mattcone/markdown-guide/blob/master/_basic-syntax/escaping-characters.md  # noqa
    characters = (
        '\\', '`', '*', '_', '{', '}', '[', ']', '<', '>', '(', ')', '#',
        '+', '-', '.', '!', '|'
    )
    translation = str.maketrans({char: '\\' + char for char in characters})
    return s.translate(translation)


class JupyterSubmitSection(ipy_widgets.VBox):

    def __init__(self, frontend):
        self.frontend = frontend
        self.runner = frontend.runner
        self.debug = JupyterDebugOutput()
        self.submit_output = ipy_widgets.Output()
        self.show_solutions = False
        self.feedback_div_ID = f'id_{uuid4().hex}'
        self.score_div_ID = f'id_{uuid4().hex}'

        if self.frontend.debug:
            btn_box = ipy_widgets.HBox((
                self.submit_btn, self.debug.clear_btn, self.solution_btn
            ))
        else:
            btn_box = ipy_widgets.HBox((self.submit_btn,))

        vspace = ipy_widgets.Box(layout={'height': '15px'})
        result = ipy_widgets.HTML(
            f'<div data-pyrope-id="{self.feedback_div_ID}" '
            f'class="pyrope feedback rendered_html"></div>'
            f'<div data-pyrope-id="{self.score_div_ID}" '
            f'class="pyrope score rendered_html"></div>'
        )
        children = (btn_box, vspace, self.submit_output, result)

        if self.frontend.debug:
            children += (vspace, self.debug, vspace)

        children += (ipy_widgets.HTML('<hr class="pyrope">'),)

        super().__init__(children)

    def __enter__(self):
        return self.submit_output.__enter__()

    def __exit__(self, *args):
        return self.submit_output.__exit__(*args)

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
    def submit_btn(self):
        btn = ipy_widgets.Button(description='Submit')

        def f(btn):
            self.submit_output.clear_output()

            if self.runner.invalid_widgets or self.runner.empty_widgets:
                self.submit, self.submit_anyway = False, True
                with self:
                    if self.runner.invalid_widgets:
                        print('There are invalid input fields.')
                    if self.runner.empty_widgets:
                        print('There are empty input fields.')
            else:
                self.submit = True

            if self.submit_anyway:
                btn.description = 'Submit anyway?'
                btn.on_click(f, remove=True)
                btn.on_click(f_anyway)

            if self.submit:
                self.runner.finish()
                self.frontend.disable_widgets()
                if not self.show_solutions:
                    self.solution_btn.click()
                self.frontend.display_widget_scores()

        def f_anyway(btn):
            if self.submit_anyway:
                self.runner.finish()
                self.frontend.disable_widgets()
                if not self.show_solutions:
                    self.solution_btn.click()
                self.frontend.display_widget_scores()
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
                self.submit_btn, self.solution_btn,
                self.debug.clear_btn
        ):
            widget.disabled = True


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
            f'\'{self._score}\')'
        ))

    @property
    def solution(self):
        return self._solution

    @solution.setter
    def solution(self, value):
        self._solution = str(value)
        display(Javascript(
            f'PyRope.set_inner_html(\'{self.solution_ID}\', '
            f'\'{self._solution}\')'
        ))

    def __str__(self):
        return (
            f'<span data-pyrope-id="{self.solution_ID}" '
            f'class="pyrope solution"></span>'
            f'<span data-pyrope-id="{self.score_ID}" '
            f'class="pyrope score"></span>'
        )


class JupyterHtmlWidget:

    def __init__(self, widget, runner):
        self.ipy = get_ipython()
        self.runner = runner
        self.widget = widget
        self.result_span = JupyterWidgetResultSpan()
        self.description = ''
        self.displayed_max_score = None
        self.displayed_score = None
        self.solution = ''
        self._disabled = False
        self._valid = 'valid'
        self._value = None

        if widget is not None:
            self.ID = f'id_{widget.ID.hex}'
        else:
            self.ID = f'id_{uuid4().hex}'

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

    def __setattr__(self, name, value):
        if callable(getattr(self, name, None)):
            # The frontend could observe an attribute name which is identical
            # to a method name. This would cause the setter to override the
            # method with the observed attribute value.
            raise AttributeError(
                f'Cannot set attribute "{name}" because this would override '
                f'the method "{getattr(self, name)}".'
            )
        object.__setattr__(self, name, value)

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
            self.runner.set_widget_value(self.widget, self._value)

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


class JupyterHtmlCheckbox(JupyterHtmlWidget):

    def __init__(self, widget, runner):
        JupyterHtmlWidget.__init__(self, widget, runner)
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
            self.runner.set_widget_value(self.widget, self._value)

    def display_solution(self, show=True):
        pass


class JupyterHtmlDropdown(JupyterHtmlWidget):

    def __init__(self, widget, runner):
        JupyterHtmlWidget.__init__(self, widget, runner)
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
        self.comm.send({'checked': value}, {'sync': True})


class JupyterHtmlRadioButtons(JupyterHtmlWidget):

    def __init__(self, widget, runner):
        self.radio_buttons = []
        JupyterHtmlWidget.__init__(self, widget, runner)
        self._options = ()
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


class JupyterHtmlSlider(JupyterHtmlWidget):

    def __init__(self, widget, runner):
        JupyterHtmlWidget.__init__(self, widget, runner)
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

    def __init__(self, widget, runner):
        JupyterHtmlWidget.__init__(self, widget, runner)
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

    def __init__(self, widget, runner):
        JupyterHtmlText.__init__(self, widget, runner)
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


class JupyterHtmlWidgetFactory(WidgetFactory):

    mapping = {
        Checkbox: JupyterHtmlCheckbox,
        Dropdown: JupyterHtmlDropdown,
        RadioButtons: JupyterHtmlRadioButtons,
        Slider: JupyterHtmlSlider,
        Text: JupyterHtmlText,
        Textarea: JupyterHtmlTextarea,
    }
