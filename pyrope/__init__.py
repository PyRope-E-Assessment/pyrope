
from IPython import get_ipython

from pyrope import config, frontends, nodes, tests, widgets
from pyrope.core import (
    Exercise, ExercisePool, ExerciseRunner, ParametrizedExercise,
    IllPosedError, ValidationError,
)
from pyrope.ipython_extension.magics import PyRopeMagics
from pyrope.logo import logo


__all__ = [
    'config', 'frontends', 'nodes', 'tests', 'widgets',
    'Exercise', 'ExercisePool', 'ExerciseRunner', 'ParametrizedExercise',
    'IllPosedError', 'ValidationError',
    'logo',
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
