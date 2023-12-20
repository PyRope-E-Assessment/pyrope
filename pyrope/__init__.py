
from IPython import get_ipython

from pyrope import (
    config, dtypes, errors, examples, formatters, frontends, nodes, tests
)
from pyrope.core import (
    CLIParser, Exercise, ExercisePool, ExerciseRunner, float_types,
    ParametrizedExercise
)
from pyrope.ipython_extension import PyRopeMagics
from pyrope.logo import logo


__all__ = [
    'CLIParser',
    'config',
    'dtypes',
    'errors',
    'examples',
    'Exercise',
    'ExercisePool',
    'ExerciseRunner',
    'float_types',
    'formatters',
    'frontends',
    'logo',
    'nodes',
    'ParametrizedExercise',
    'PyRopeMagics',
    'tests'
]


def load_ipython_extension(ipy):
    ipy.register_magics(PyRopeMagics)


# Load PyRope's ipython extension while PyRope gets imported.
if (ipy := get_ipython()) is not None:
    if 'pyrope' not in ipy.magics_manager.magics.get('line'):
        load_ipython_extension(ipy)


def _jupyter_nbextension_paths():
    return [
        {
            'section': 'notebook',
            'src': 'nbextension',
            'dest': 'pyrope',
            'require': 'pyrope/extension',
        }
    ]
