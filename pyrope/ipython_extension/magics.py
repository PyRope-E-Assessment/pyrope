
import shlex
import types
import unittest

from IPython.core.magic import (
    line_magic, Magics, magics_class, needs_local_scope
)

from pyrope import examples, ExercisePool, ExerciseRunner
from pyrope.core import CLIParser
from pyrope.frontends import ConsoleFrontend, JupyterFrontend


@magics_class
class PyRopeMagics(Magics):

    parser = CLIParser(prog='%pyrope')

    @line_magic('pyrope')
    @needs_local_scope
    def cli(self, line, local_ns):
        args = self.parser.parse_args(shlex.split(line))
        pool = ExercisePool()
        if args.patterns:
            for pattern in args.patterns:
                pool.add_exercises_from_file(pattern)
        else:
            notebook = types.ModuleType('notebook')
            notebook.__dict__.update(**local_ns)
            pool.add_exercises_from_module(notebook)
            if len(pool.data) == 0:
                pool.add_exercises_from_module(examples)

        if args.subcommand == 'run':
            for exercise in pool:
                runner = ExerciseRunner(exercise)
                if args.frontend == 'console':
                    frontend = ConsoleFrontend(debug=args.debug)
                else:
                    frontend = JupyterFrontend(debug=args.debug)
                runner.set_frontend(frontend)
                frontend.set_runner(runner)
                runner.run()

        if args.subcommand == 'test':
            test_cases = [
                test_case
                for exercise in pool
                for test_case in exercise.test_cases()
            ]
            suite = unittest.TestSuite(test_cases)
            runner = unittest.TextTestRunner()
            runner.run(suite)
