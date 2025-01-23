
from IPython import get_ipython

from pyrope import config, nodes
from pyrope.core import (
    Exercise, ExercisePool, ExerciseRunner, ParametrizedExercise
)
from pyrope.logo import logo
from pyrope.nodes import *  # noqa: F401, F403
from pyrope.ipython_extension import PyRopeMagics

__all__ = [
    'config',
    'Exercise',
    'ExercisePool',
    'ExerciseRunner',
    'logo',
    'nodes',
    'ParametrizedExercise',
]

__all__ += nodes.__all__


def load_ipython_extension(ipy):
    ipy.register_magics(PyRopeMagics)


# Load PyRope's ipython extension while PyRope gets imported.
if (ipy := get_ipython()) is not None:
    if 'pyrope' not in ipy.magics_manager.magics.get('line'):
        load_ipython_extension(ipy)
