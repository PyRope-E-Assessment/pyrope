
import abc
import argparse
import collections
from functools import cached_property
import glob
import importlib
import inspect
import itertools
import os
from pathlib import Path
import sys
import textwrap
import unittest

from IPython import get_ipython
import numpy

from pyrope import frontends, tests
from pyrope.config import process_total_score
from pyrope.errors import IllPosedError
from pyrope.messages import (
    ChangeWidgetAttribute, CreateWidget, ExerciseAttribute, RenderTemplate,
    Submit, WaitingForSubmission
)


float_types = (bool, int, float, numpy.bool_, numpy.int_, numpy.float_)


class Exercise(abc.ABC):

    def __init_subclass__(cls):
        cls.__init__ = Exercise.__init__

    def __init__(self, weights=None, **kwargs):
        if weights is None:
            weights = 1.0
        self.weights = weights
        self.kwargs = kwargs

    @property
    def dir(self):
        module = sys.modules[self.__module__]
        try:
            file = module.__file__
        except AttributeError:
            return Path.cwd()
        return Path(file).parent

    def run(self, debug=False):
        runner = ExerciseRunner(self, debug=debug)
        if get_ipython() is not None:
            frontend = frontends.JupyterFrontend()
        else:
            frontend = frontends.ConsoleFrontend()
        runner.set_frontend(frontend)
        frontend.set_runner(runner)
        runner.run()

    def preamble(self):
        return ''

    def parameters(self):
        return {}

    @abc.abstractmethod
    def problem(self):
        ...

    def the_solution(self):
        return None

    def a_solution(self):
        return None

    def hint(self):
        return None

    def validate(self):
        return None

    def score(self):
        return None

    def feedback(self):
        return ''

    def test_cases(self):
        test_loader = unittest.TestLoader()
        method_names = test_loader.getTestCaseNames(tests.TestExercise)
        for method_name in method_names:
            yield tests.TestExercise(self, method_name)
        pexercise = ParametrizedExercise(self)
        yield from pexercise.test_cases()

    def test(self, runner=unittest.TextTestRunner()):
        suite = unittest.TestSuite(self.test_cases())
        runner.run(suite)


class ParametrizedExercise:

    def __init__(self, exercise, global_parameters={}):
        self.exercise = exercise
        self.global_parameters = global_parameters
        self._total_score = None
        self._max_total_score = None

    @staticmethod
    def apply(func, d):
        signature = inspect.signature(func)
        kwargs = {}
        for par in signature.parameters.values():
            if par.name in d:
                kwargs[par.name] = d[par.name]
            elif par.default is inspect.Parameter.empty:
                raise IllPosedError(f'Missing parameter: {par.name}.')
        return func(**kwargs)

    @cached_property
    def parameters(self):
        kwargs = self.global_parameters | self.exercise.kwargs
        pars = self.apply(self.exercise.parameters, kwargs)
        if pars is None:
            pars = {}
        return pars

    @cached_property
    def model(self):
        model = self.apply(self.exercise.problem, self.parameters)
        for ofield in model.ofields:
            if ofield not in self.parameters:
                raise IllPosedError(
                    f"No parameter for output field '{ofield}'."
                )
        return model

    @cached_property
    def template(self):
        return textwrap.dedent(str(self.model))

    @cached_property
    def preamble(self):
        preamble = self.exercise.preamble
        if callable(preamble):
            preamble = self.apply(preamble, self.parameters)
        return textwrap.dedent(preamble)

    @cached_property
    def ifields(self):
        return self.model.ifields

    @cached_property
    def widgets(self):
        return self.model.widgets

    @cached_property
    def the_solution(self):
        explicit = self.apply(self.exercise.the_solution, self.parameters)
        if explicit is None:
            explicit = {}
        elif not isinstance(explicit, dict):
            if len(self.ifields) != 1:
                raise IllPosedError(
                    'Unless there is only a single input field, '
                    'the solution must be a dictionary.'
                )
            names = list(self.ifields.keys())
            explicit = {names[0]: explicit}

        # implicit solutions from underscore naming convention
        implicit = {
            ifield: self.parameters[ifield[:-1]]
            for ifield in self.ifields
            if ifield.endswith('_')
            if ifield[:-1] in self.parameters
            if ifield not in explicit
        }

        solution = explicit | implicit

        self.model.the_solution = solution
        return {
            name: ifield.the_solution
            for name, ifield in self.model.ifields.items()
        }

    @cached_property
    def a_solution(self):
        solution = self.apply(self.exercise.a_solution, self.parameters)
        if solution is None:
            solution = {}
        elif not isinstance(solution, dict):
            if len(self.ifields) != 1:
                raise IllPosedError(
                    'Unless there is only a single input field, '
                    'a solution must be a dictionary.'
                )
            names = list(self.ifields.keys())
            solution = {names[0]: solution}
        self.model.a_solution = solution
        return {
            name: ifield.a_solution
            for name, ifield in self.model.ifields.items()
        }

    @property
    def solution(self):
        # trigger solutions via getter
        self.the_solution
        self.a_solution
        return {
            name: ifield.solution
            for name, ifield in self.model.ifields.items()
        }

    @cached_property
    def trivial_input(self):
        return {
            name: ifield.dtype.trivial_value()
            for name, ifield in self.ifields.items()
        }

    @cached_property
    def dummy_input(self):
        return {
            name: ifield.dtype.dummy_value()
            for name, ifield in self.ifields.items()
        }

    @property
    def answers(self):
        return self.model.answers

    @answers.setter
    def answers(self, answers):
        self.model.value = answers

    @cached_property
    def score_weights(self):
        weights = self.exercise.weights
        if isinstance(weights, float_types):
            weights = float(weights)
            if len(self.ifields) == 0:
                return {None: weights}
            return {name: weights for name in self.ifields.keys()}
        weights = weights.copy()
        for name in self.ifields.keys():
            if name not in weights.keys():
                weights[name] = 1.0
            else:
                weights[name] = float(weights[name])
        return weights

    @cached_property
    def max_scores(self):
        solution = self.solution
        scores = self.apply(
            self.exercise.score, self.parameters | self.dummy_input
        )
        if scores is None or isinstance(scores, float_types):
            for name, value in solution.items():
                if value is None:
                    raise IllPosedError(
                        f"Unable to determine maximal score for "
                        f"input field '{name}'."
                    )
        if scores is None:
            max_scores = {
                name: float(ifield.auto_max_score) * self.score_weights[name]
                for name, ifield in self.ifields.items()
            }
            self._max_total_score = sum(max_scores.values())
            for name, ifield in self.ifields.items():
                ifield.displayed_max_score = max_scores[name]
            return max_scores
        if isinstance(scores, tuple):
            self._max_total_score = (
                float(scores[1]) * list(self.score_weights.values())[0]
            )
            if len(self.ifields) == 1:
                name = list(self.ifields.keys())[0]
                ifield = list(self.ifields.values())[0]
                ifield.displayed_max_score = self._max_total_score
                return {name: self._max_total_score}
            return {name: None for name in self.ifields}

        answer = {
            name: self.dummy_input[name]
            if value is None else value
            for name, value in solution.items()
        }
        max_scores = self.apply(
            self.exercise.score, self.parameters | answer
        )
        for name, value in solution.items():
            if value is None and name in max_scores:
                max_scores[name] = None
        if isinstance(scores, float_types):
            self._max_total_score = (
                float(max_scores) * list(self.score_weights.values())[0]
            )
            if len(self.ifields) == 1:
                name = list(self.ifields.keys())[0]
                ifield = list(self.ifields.values())[0]
                ifield.displayed_max_score = self._max_total_score
                return {name: self._max_total_score}
            return {name: None for name in self.ifields}
        if isinstance(scores, dict):
            max_scores = {
                name: max_scores[name]
                if name in max_scores else None
                for name in self.ifields
            }
            for name, value in max_scores.items():
                if isinstance(value, float_types):
                    max_scores[name] = float(value)
                elif isinstance(value, tuple):
                    max_scores[name] = float(value[1])
                elif value is None or solution[name] is None:
                    max_scores[name] = self.ifields[name].auto_max_score
                max_scores[name] *= self.score_weights[name]
                self.ifields[name].displayed_max_score = max_scores[name]
            self._max_total_score = sum(max_scores.values())
            return max_scores
        raise IllPosedError(
            'If implemented, the score method must return a number, a pair '
            'of numbers or a dictionary with values of this type, where '
            'number is either an int or a float.'
        )

    @property
    def scores(self):
        self.solution
        output = self.apply(
            self.exercise.score, self.parameters | self.dummy_input
        )
        answers = self.answers
        fill_values = {
            name: self.dummy_input[name]
            for name, answer in answers.items()
            if answer is None and not self.ifields[name].treat_none_manually
        }
        if isinstance(output, dict)\
                or (output is not None and len(self.ifields) == 1):
            answers |= fill_values
        scores = self.apply(
            self.exercise.score, self.parameters | answers
        )
        if isinstance(output, dict):
            for name in fill_values:
                if name not in scores:
                    continue
                elif isinstance(scores[name], tuple):
                    scores[name] = (0.0, scores[name][1])
                else:
                    scores[name] = 0.0
        if output is not None and len(self.ifields) == 1:
            for name in fill_values:
                if isinstance(output, tuple):
                    scores = {name: (0.0, scores[1])}
                else:
                    scores = {name: 0.0}
        no_scores = {name: None for name in self.ifields}
        if scores is None:
            scores = no_scores
        names = list(self.ifields.keys())
        ifields = list(self.ifields.values())
        if isinstance(scores, float_types):
            self._total_score = (
                float(scores) * list(self.score_weights.values())[0]
            )
            if len(names) == 1:
                ifields[0].displayed_score = self._total_score
                return {names[0]: self._total_score}
            return no_scores
        if isinstance(scores, tuple):
            self._total_score = (
                float(scores[0]) * list(self.score_weights.values())[0]
            )
            if len(names) == 1:
                ifields[0].displayed_score = self._total_score
                return {names[0]: self._total_score}
            return no_scores
        for name, ifield in self.model.ifields.items():
            if name not in scores:
                scores[name] = None
            if scores[name] is None:
                scores[name] = ifield.auto_score
            if isinstance(scores[name], tuple):
                scores[name] = scores[name][0]
            scores[name] = float(scores[name]) * self.score_weights[name]
            ifield.displayed_score = scores[name]
        self._total_score = sum([
            scores[name][0]
            if isinstance(scores[name], tuple) else scores[name]
            for name in self.ifields.keys()
        ])
        return scores

    @property
    def total_score(self):
        self.scores  # trigger total score computation
        return self._total_score

    @property
    def max_total_score(self):
        self.max_scores  # trigger maximal total score computation
        return self._max_total_score

    @property
    def correct(self):
        max_scores = self.max_scores
        scores = self.scores
        correct = {}
        for name, ifield in self.ifields.items():
            if (
                ifield.correct is None and
                scores[name] is not None and
                max_scores[name] is not None
            ):
                if scores[name] == max_scores[name]:
                    correct[name] = True
                else:
                    correct[name] = False
                ifield.correct = correct[name]
            else:
                correct[name] = ifield.correct
        return correct

    @property
    def feedback(self):
        kwargs = self.parameters | self.answers
        feedback = self.apply(self.exercise.feedback, kwargs)
        return textwrap.dedent(feedback)

    @cached_property
    def input_generator(self):
        answers = [
            self.trivial_input,
            self.dummy_input,
            self.solution,
        ]
        keys = self.ifields.keys()
        factors = []
        for key in keys:
            factor = [None]
            for answer in answers:
                if answer[key] is not None:
                    factor.append(answer[key])
            factors.append(factor)

        def generator():
            for values in itertools.product(*factors):
                yield dict(zip(keys, values))

        return generator

    def test_cases(self):
        test_loader = unittest.TestLoader()
        method_names = test_loader.getTestCaseNames(
            tests.TestParametrizedExercise
        )
        for method_name in method_names:
            yield tests.TestParametrizedExercise(self, method_name)


class ExerciseRunner:

    def __init__(self, exercise, debug=False, global_parameters={}):
        self.debug = debug
        self.observers = []
        self.pexercise = ParametrizedExercise(exercise, global_parameters)
        self.sender = exercise.__class__
        self.widget_id_mapping = {
            widget.ID: widget for widget in self.pexercise.widgets
        }

    # TODO: enforce order of steps
    def run(self):
        self.notify(ExerciseAttribute(self.sender, 'debug', self.debug))
        self.notify(ExerciseAttribute(
            self.sender, 'parameters', self.pexercise.parameters
        ))
        self.notify(RenderTemplate(
            self.sender, 'preamble', self.pexercise.preamble
        ))
        for widget in self.pexercise.widgets:
            self.notify(CreateWidget(
                self.sender, widget.ID, widget.__class__.__name__
            ))
            widget.observe_attributes()
            self.notify(ChangeWidgetAttribute(
                self.sender, widget.ID, 'info', widget.info
            ))
        self.notify(RenderTemplate(
            self.sender, 'problem', self.pexercise.template
        ))
        if self.debug:
            self.publish_solutions()
        self.notify(WaitingForSubmission(self.sender))

    def finish(self):
        if not self.debug:
            self.publish_solutions()
        self.notify(ExerciseAttribute(
            self.sender, 'answers', self.pexercise.answers
        ))
        self.notify(ExerciseAttribute(
            self.sender, 'max_total_score',
            process_total_score(self.pexercise.max_total_score)
        ))
        self.notify(ExerciseAttribute(
            self.sender, 'total_score',
            process_total_score(self.pexercise.total_score)
        ))
        self.pexercise.correct
        for widget in self.pexercise.model.widgets:
            widget.show_max_score = True
            widget.show_score = True
            widget.show_correct = True
        self.notify(RenderTemplate(
            self.sender, 'feedback', self.pexercise.feedback
        ))

    def publish_solutions(self):
        self.pexercise.solution
        for widget in self.pexercise.model.widgets:
            widget.show_solution = True

    def set_frontend(self, frontend):
        self.frontend = frontend

    def register_observer(self, observer):
        self.observers.append(observer)
        for widget in self.pexercise.widgets:
            widget.register_observer(observer)

    def notify(self, msg):
        for observer in self.observers:
            observer(msg)

    def observer(self, msg):
        if isinstance(msg, ChangeWidgetAttribute):
            if msg.attribute_name == 'value':
                widget = self.widget_id_mapping[msg.widget_id]
                widget.value = msg.attribute_value
        elif isinstance(msg, Submit):
            self.finish()

    @property
    def exercise_dir(self):
        return self.pexercise.exercise.dir


class ExercisePool(collections.UserList):

    def add_exercise(self, exercise):
        self.data.append(exercise)

    def add_exercises_from_pool(self, pool):
        self.data.extend(pool)

    def add_exercises_from_module(self, module):
        # Calling the '__dir__' method instead of the 'dir' built-in
        # avoids alphabetical sorting of the exercises added to the pool.
        for name in module.__dir__():
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, Exercise):
                if not inspect.isabstract(obj):
                    self.data.append(obj())

    def add_exercises_from_file(self, filepattern):
        filepaths = glob.glob(filepattern, recursive=True)
        for filepath in filepaths:
            dirname, filename = os.path.split(filepath)
            modulename, ext = os.path.splitext(filename)
            if ext != '.py':
                raise TypeError(
                    f'File "{filepath}" does not seem to be a python script.'
                )
            sys.path.insert(0, dirname)
            importlib.invalidate_caches()
            if modulename in sys.modules:
                module = sys.modules[modulename]
                importlib.reload(module)
            else:
                module = importlib.import_module(modulename)
            self.add_exercises_from_module(module)


class CLIParser:

    def __init__(self, *args, default_frontend='jupyter', **kwargs):
        self._parser = argparse.ArgumentParser(*args, **kwargs)
        subparsers = self._parser.add_subparsers(
            dest='subcommand',
            required=True,
            help='subcommands'
        )

        run_parser = subparsers.add_parser(
            'run',
            help='start an interactive exercise session'
        )
        run_parser.add_argument(
            'patterns',
            nargs='*',
            type=str,
            help='pattern for python scripts with exercise definitions',
            metavar='pattern',
        )
        run_parser.add_argument(
            '--frontend',
            default=default_frontend,
            choices={'console', 'jupyter'},
            help='exercises renderer',
        )
        run_parser.add_argument(
            '--path',
            default=os.getcwd(),
            help='location to store files'
        )
        run_parser.add_argument(
            '--debug',
            default=False,
            action='store_true',
            help='enables debug mode for the frontend',
        )

        test_parser = subparsers.add_parser(
            'test',
            help='run automated unit tests on exercises'
        )
        test_parser.add_argument(
            'patterns',
            nargs='*',
            type=str,
            help='pattern for python scripts with exercise definitions',
            metavar='pattern',
        )

    def parse_args(self, args=None, namespace=None):
        return self._parser.parse_args(args=args, namespace=namespace)
