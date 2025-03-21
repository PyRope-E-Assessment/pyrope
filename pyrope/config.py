
import os
import tempfile


# Maximum length for text field input.
#
# This should be set as small as possible for secure input parsing.
maximum_input_length: int = 256


# Transformations for parsing symbolic expressions.
#
# https://docs.sympy.org/latest/modules/parsing.html#parsing-transformations-reference
transformations: tuple[str, ...] = (
    # Splits symbol names for implicit multiplication.
    #
    # Intended to let expressions like xyz be parsed as x*y*z. Does not split
    # Greek character names, so theta will not become t*h*e*t*a. Generally
    # this should be used with implicit_multiplication.
    # 'split_symbols',

    # Makes the multiplication operator optional in most cases.
    #
    # Use this before implicit_application(), otherwise expressions like sin
    # 2x will be parsed as x * sin(2) rather than sin(2*x).
    # 'implicit_multiplication',

    # Makes parentheses optional in some cases for function calls.
    #
    # Use this after implicit_multiplication(), otherwise expressions like sin
    # 2x will be parsed as x * sin(2) rather than sin(2*x).
    # 'implicit_application',

    # Allows functions to be exponentiated, e.g. cos^2(x).
    # 'function_exponentiation',

    # Allows a slightly relaxed syntax.
    #
    # * Parentheses for single-argument method calls are optional.
    # * Multiplication is implicit.
    # * Symbol names can be split (i.e. spaces are not needed between symbols).
    # * Functions can be exponentiated.
    # 'implicit_multiplication_application',

    # Treats XOR, ^, as exponentiation, **.
    'convert_xor',

    # Allows standard notation for factorial.
    'factorial_notation',

    # Inserts calls to Symbol for undefined variables.
    'auto_symbol',

    # Converts numeric literals to use SymPy equivalents.
    'auto_number',

    # Converts floats into Rational. Run AFTER auto_number.
    'rationalize',

    # Allows 0.2[1] notation to represent the repeated decimal 0.2111… (19/90)
    'repeated_decimals',
)


# Maximal number of test repetitions.
#
# Automated exercise tests are repeated with different (faked) user inputs.
# This option limits the maximal number of repetitions in order to restrict
# the testing time.
maximum_test_repetitions: int = 1024


# Valid representations for boolean values.
#
# Valid representations Python's boolean values False and True can be defined
# with this option. A representation pair consists of a value for False
# followed by a value for True.
boolean_representations: tuple[tuple[str, str], ...] = (
    ('0', '1'),
    ('False', 'True'),
    ('false', 'true'),
    ('f', 't'),
    ('Falsch', 'Wahr'),
    ('falsch', 'wahr'),
    ('f', 'w'),
)


# Processing scores.
#
# With the functions 'process_score' and 'process_total_score', one could
# implement another way of processing scores before they are sent to the
# frontend. Maximal (total) scores are also processed by these functions.
def process_score(score: int | float) -> int | float:
    return round(score, 1)

def process_total_score(total_score: int | float) -> int | float:  # noqa
    return round(total_score, 1)


# Default value for maximal rendered radio buttons.
#
# If there are more than 'maximal_radio_buttons' options, then these options
# are rendered as a dropdown instead of radio buttons. This affects 'OneOf' and
# 'MultipleChoice' nodes.
maximal_radio_buttons: int = 5


# Exercise summary items.
#
# Here you can configure what is logged into the history file.
summary_items = (
    'answers',
    'correct',
    'feedback',
    'id',
    'max_scores',
    'max_total_score',
    'metadata',
    'parameters',
    'preamble',
    'scores',
    'solution',
    'started_at',
    'submitted_at',
    'template',
    'total_score',
    'user_name',
)


# Logging.
#
# Configure different logging targets.
# 'exercise_debug':
#   Errors and warnings from PyRope external exercise code and all parameters
#   necessary to fix them.
# 'history':
#   Eternal log file storing all information necessary for statistical purposes
#   and learning analytics, such as score dashboards. NOTE: Exercises which are
#   not stored in a file, e.g. when developed in a Jupyter notebook cell, will
#   not be added to the history.
# 'pyrope':
#   PyRope's internal system messages for debugging.
log_dir: str = os.path.join(tempfile.gettempdir(), 'pyrope')
logging: dict[dict[str: str, ...], ...] = {
    'exercise_debug': {
        'filename': os.path.join(log_dir, 'exercise_debug.log'),
        'level': 'DEBUG',
        'fmt': '%(levelname)s:%(asctime)s %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S',
    },
    'history': {
        'filename': os.path.join(log_dir, 'history.log'),
        'level': 'INFO',
        'fmt': '%(asctime)s %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S',
    },
    'pyrope': {
        'filename': os.path.join(log_dir, 'pyrope.log'),
        'level': 'DEBUG',
        'fmt': '%(levelname)s:%(asctime)s %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S',
    },
}


# Database configuration.
#
# If 'db_file' is an empty string, data is stored in-memory and is deleted when
# the process is shut down. To persist data please specify 'db_file'. Prefix
# one slash to use relative paths and two slashes for absolute paths.
dialect: str = 'sqlite://'
db_file: str = ''
