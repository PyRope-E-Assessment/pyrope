
import inspect
import itertools
import unittest

import matplotlib.pyplot as plt

from pyrope import config, core, nodes
from pyrope.formatters import TemplateFormatter


class TestExercise(unittest.TestCase):

    def __init__(self, exercises, method_name):
        unittest.TestCase.__init__(self, method_name)
        try:
            iter(exercises)
        except TypeError:
            exercises = (exercises,)
        self.exercises = exercises

    @staticmethod
    def with_all_exercises(test):
        def wrapped_test(self):
            for exercise in self.exercises:
                with self.subTest(exercise=exercise.__class__):
                    test(self, exercise)
        return wrapped_test

    @with_all_exercises
    def test_parameters_method(self, exercise):
        """
        All arguments of the 'parameters' method of an exercise must have
        default values.
        """
        signature = inspect.signature(exercise.parameters)
        for par in signature.parameters.values():
            self.assertIsNot(
                par.default, inspect.Parameter.empty,
                f"Argument '{par}' of 'parameters' must have a default value."
            )

    @with_all_exercises
    def test_hints_method_name(self, exercise):
        '''
        An exercise must not implement a method called 'hint' to explicitly
        point out that the method to implement custom hints is called 'hints'.
        '''
        self.assertFalse(
            hasattr(exercise, 'hint'),
            "Do not implement a 'hint' method. Use 'hints' instead."
        )

    @with_all_exercises
    def test_solution_method_name(self, exercise):
        '''
        An exercise must not implement a method called 'solution', to avoid
        ambiguity: Solutions are provided via the 'the_solution' method if
        they are unique or via 'a_solution' if not.
        '''
        self.assertFalse(
            hasattr(exercise, 'solution'),
            "Do not implement a 'solution' method. Use 'the_solution' "
            "instead if the solution is unique or 'a_solution' if not."
        )

    @with_all_exercises
    def test_scores_method_name(self, exercise):
        '''
        An exercise must not implement a method called 'score' to explicitly
        point out that the method to implement custom scores is called
        'scores'.
        '''
        self.assertFalse(
            hasattr(exercise, 'score'),
            "Do not implement a 'score' method. Use 'scores' to implement "
            "custom scores."
        )

    @with_all_exercises
    def test_parameter_names_are_stable(self, exercise):
        '''
        The set of parameter names defined by an exercise through its
        parameters method needs to be same over different runs to keep
        exercises consistent.
        '''
        names = set(core.ParametrizedExercise(exercise).parameters.keys())
        for _ in range(config.maximum_test_repetitions):
            pexercise = core.ParametrizedExercise(exercise)
            names_ = set(pexercise.parameters.keys())
            self.assertEqual(
                names, names_,
                f"The keys of the dictionary returned by an exercise's "
                f"parameters method must not change over different runs, got "
                f"{names} and {names_} as parameter names."
            )

    @with_all_exercises
    def test_ifield_names_are_stable(self, exercise):
        '''
        The set of input field names defined by an exercise through its problem
        method needs to be the same over different runs to keep exercises
        consistent.
        '''
        names = set(core.ParametrizedExercise(exercise).ifields.keys())
        for _ in range(config.maximum_test_repetitions):
            pexercise = core.ParametrizedExercise(exercise)
            names_ = set(pexercise.ifields.keys())
            self.assertEqual(
                names, names_,
                f"The names of the input fields defined by an exercise's "
                f"problem method must not change over different runs, got "
                f"{names} and {names_} as input field names."
            )

    @with_all_exercises
    def test_maximal_total_score_is_stable(self, exercise):
        '''
        The maximal total score of an exercise is calculated by inserting the
        sample solution. The sample solution depends on the exercise's
        parameters which could be randomized. Therefore, the maximal total
        score has to be same over different runs of an exercise.
        '''
        max_total_score = core.ParametrizedExercise(exercise).max_total_score
        for _ in range(config.maximum_test_repetitions):
            pexercise = core.ParametrizedExercise(exercise)
            self.assertEqual(
                max_total_score, pexercise.max_total_score,
                f"The maximal total score must not change over different "
                f"runs of an exercise, got {max_total_score} and "
                f"{pexercise.max_total_score} as a maximal total score."
            )


class TestParametrizedExercise(unittest.TestCase):

    def __init__(self, pexercises, method_name):
        unittest.TestCase.__init__(self, method_name)
        try:
            iter(pexercises)
        except TypeError:
            pexercises = (pexercises,)
        self.pexercises = pexercises

    @classmethod
    def tearDownClass(cls):
        # Prevent matplotlib from rendering plots after testing.
        plt.close()

    @staticmethod
    def with_all_pexercises(test):
        def wrapped_test(self):
            for pexercise in self.pexercises:
                with self.subTest(exercise=pexercise.exercise.__class__):
                    test(self, pexercise)
        return wrapped_test

    @with_all_pexercises
    def test_preamble_method(self, pexercise):
        '''
        The preamble must be a string. Its output fields must be in the
        exercise's parameters.
        '''
        preamble = pexercise.exercise.preamble
        if callable(preamble):
            preamble = pexercise.apply(preamble, pexercise.parameters)
        self.assertIsInstance(
            preamble, str,
            f"The 'preamble' method must return a string, not an instance of "
            f"{preamble.__class__}."
        )
        ofields = {
            ofield for _, ofield, _ in TemplateFormatter.parse(preamble)
            if ofield is not None
        }
        for ofield in ofields:
            self.assertIn(
                ofield, pexercise.parameters,
                f"There is no parameter for output field '{ofield}' in the "
                f"preamble string."
            )

    @with_all_pexercises
    def test_parameters_method(self, pexercise):
        '''
        If implemented, the 'parameters' method of an exercise must return a
        dictionary. Its keys must be strings, as they name the input fields.
        '''
        parameters = pexercise.parameters
        self.assertIsInstance(
            parameters, dict,
            "The 'parameters' method must return a dictionary."
        )
        for key in parameters.keys():
            self.assertIsInstance(
                key, str,
                f"The dictionary returned by the 'parameters' method "
                f"must be keyed with strings (got {type(key)})."
            )

    @with_all_pexercises
    def test_hints_method(self, pexercise):
        '''
        The hints method has to return a string or an iterable object yielding
        only strings.
        '''
        hints = pexercise.apply(
            pexercise.exercise.hints, pexercise.parameters
        )
        if isinstance(hints, str):
            return
        try:
            hints = iter(hints)
        except TypeError:
            raise TypeError(
                f"The 'hints' method has to return a string or an iterable "
                f"object, got {type(hints)}."
            )
        for hint in hints:
            self.assertIsInstance(
                hint, str,
                f"If 'hints' returns an iterable object, all elements have to "
                f"be strings, got {type(hint)}."
            )

    @with_all_pexercises
    def test_problem_method(self, pexercise):
        '''
        A problem must be an instance of class 'Problem'.
        '''
        problem = pexercise.apply(
            pexercise.exercise.problem, pexercise.parameters
        )
        self.assertIsInstance(
            problem, nodes.Problem,
            f"The 'problem' method must return an instance of {nodes.Problem},"
            f" not of {problem.__class__}."
        )

    @with_all_pexercises
    def test_feedback_method(self, pexercise):
        '''
        A feedback must be a string. Its output fields must be in the
        exercise's parameters or in the answers.
        '''
        kwargs = pexercise.parameters | pexercise.dummy_input
        feedback = pexercise.apply(
            pexercise.exercise.feedback, kwargs
        )
        self.assertIsInstance(
            feedback, str,
            f"The 'feedback' method must return a string, not an instance "
            f"of {feedback.__class__}."
        )
        ofields = {
            ofield for _, ofield, _ in TemplateFormatter.parse(feedback)
            if ofield is not None
        }
        for ofield in ofields:
            self.assertIn(
                ofield, kwargs,
                f"There is no parameter or answer for output field '{ofield}' "
                f"in the feedback string."
            )

    @with_all_pexercises
    def test_metadata(self, pexercise):
        '''
        Metadata are either strings, tuples of strings or None. In case of
        'taxonomy' the strings have to be part of Bloom's taxonomy levels
        specified in Exercise.__taxonomy_levels__.
        '''
        for name, annotation in core.Exercise.__annotations__.items():
            value = getattr(pexercise.exercise, name)
            if value is None:
                continue
            self.assertIsInstance(
                value, annotation,
                f"Metadata '{name}' has to be a {annotation}, got "
                f"{type(value)}."
            )
            # TODO: make this a warning
            if isinstance(tuple(), annotation) and isinstance(value, str):
                self.assertNotIn(
                    ',', value,
                    f"Multiple values for '{name}' have to be listed as a "
                    f"tuple, not inside a string."
                )
            if isinstance(value, tuple):
                for item in value:
                    self.assertIsInstance(
                        item, str,
                        f"Metadata '{name}' has to be a string or a tuple of "
                        f"strings."
                    )
            if name == 'taxonomy':
                if isinstance(value, str):
                    value = (value,)
                for item in value:
                    self.assertIn(
                        item, core.Exercise.__taxonomy_levels__,
                        f"{item} is not a valid level in Bloom's taxonomy."
                    )

    @with_all_pexercises
    def test_solution_values(self, pexercise):
        '''
        None is only a valid solution if 'treat_none_manually' is set to True.
        Otherwise, it is not possible to determine if None is an intended
        solution or was simply not given. Empty strings are treated the same
        way as None because they are cast to None.
        '''
        for name, solution in pexercise.solution.items():
            if pexercise.ifields[name].treat_none_manually is False:
                self.assertIsNotNone(
                    solution,
                    f"None and empty strings are only valid solutions if "
                    f"'treat_none_manually' is set to True. Found None or '' "
                    f" as a/the solution with 'treat_none_manually=False' for "
                    f"input field {name}."
                )

    @with_all_pexercises
    def test_score_weights(self, pexercise):
        '''
        Scores can be weighted via the key word argument 'weights' of the
        Exercise class. Input fields can be weighted either all the same or
        individually. 'weights' needs to be an integer, a float or a
        dictionary. In case of a dictionary, a key is the name if an input
        field and a value is the corresponding weight in form of an integer or
        a float.
        '''
        weights = pexercise.exercise.weights
        score_output = pexercise.apply(
            pexercise.exercise.scores,
            pexercise.parameters | pexercise.dummy_input
        )

        self.assertIsInstance(
            weights, core.float_types + (dict,),
            f"'weights' has to be an integer, a float or a dictionary, got "
            f"{type(weights)}."
        )
        if (
            isinstance(score_output, core.float_types) and
            len(pexercise.ifields) > 1
        ):
            self.assertIsInstance(
                weights, core.float_types,
                "It is only possible to weight scores of input fields "
                "individually if the score method returns an input-field-wise "
                "scoring."
            )
        if isinstance(weights, core.float_types):
            self.assertGreater(
                weights, 0.0,
                f"Score weights have to be greater than 0, got {weights}."
            )
        if isinstance(weights, dict):
            for name, weight in weights.items():
                self.assertIn(
                    name, pexercise.ifields.keys(),
                    f"Cannot weight score. There is no input field named "
                    f"'{name}'."
                )
                self.assertIsInstance(
                    weight, core.float_types,
                    f"All score weights have to be either an integer or a "
                    f"float, got {type(weight)}."
                )
                self.assertGreater(
                    weight, 0.0,
                    f"All score weights have to be greater than 0, got "
                    f"{weight}."
                )

    @with_all_pexercises
    def test_maximal_total_score_is_positive(self, pexercise):
        '''
        The maximal total score should be positive.
        '''
        self.assertGreater(
            pexercise.max_total_score, 0.0,
            'The maximal total score is not positive.'
        )

    @with_all_pexercises
    def test_maximal_scores_are_positive(self, pexercise):
        '''
        The maximal input field scores should be positive.
        '''
        max_scores = pexercise.max_scores
        if None in max_scores.values():
            return
        for ifield, score in max_scores.items():
            self.assertGreater(
                score, 0.0,
                f'The maximal score for input field {ifield} is not positive.'
            )

    @with_all_pexercises
    def test_no_score_for_empty_inputs(self, pexercise):
        '''
        If all input fields are empty and treat None automatically, the total
        score should be zero.
        '''
        if pexercise.ifields == {}:
            return
        if any([
            ifield.treat_none_manually
            for ifield in pexercise.ifields.values()
        ]):
            return
        pexercise.answers = {
            name: None
            for name in pexercise.ifields
        }
        self.assertEqual(
            pexercise.total_score, 0.0,
            'The total score for empty input fields is not zero.'
        )

    @with_all_pexercises
    def test_maximal_scores_for_sample_solution(self, pexercise):
        '''
        A sample solution should get maximal input field scores.
        '''
        answers = pexercise.solution
        for value in answers.values():
            if value is None:
                return
        pexercise.answers = answers
        max_scores = pexercise.max_scores
        scores = pexercise.scores
        for ifield in pexercise.ifields:
            if scores[ifield]:
                self.assertEqual(
                    scores[ifield], max_scores[ifield],
                    f'The sample solution for input field {ifield} does not '
                    f'get maximal score.'
                )

    @with_all_pexercises
    def test_maximal_total_score_for_sample_solution(self, pexercise):
        '''
        A sample solution should get maximal total score.
        '''
        answers = pexercise.solution
        for value in answers.values():
            if value is None:
                return
        pexercise.answers = answers
        self.assertEqual(
            pexercise.total_score, pexercise.max_total_score,
            'The sample solution does not get maximal total score.'
        )

    # TODO: should only raise a warning
    @with_all_pexercises
    def test_treat_none_manually_keyword(self, pexercise):
        '''
        If score returns a scalar or a tuple and the exercise has more than two
        input fields then None cannot be treated automatically. In these cases
        'treat_none_manually' should be set to True to make it explicit.
        '''
        exercise = pexercise.exercise

        output = pexercise.apply(
            exercise.scores,
            pexercise.parameters | pexercise.dummy_input
        )

        if (
            isinstance(output, core.float_types + (tuple,)) and
            len(pexercise.ifields) >= 2
        ):
            for name, ifield in pexercise.ifields.items():
                self.assertTrue(
                    ifield.treat_none_manually,
                    f"'treat_none_manually' of input field {name} should be "
                    f"set to True because in this scoring case it cannot be "
                    f"handled automatically."
                )

    @staticmethod
    def with_all_pexercises_and_all_inputs(test):
        def wrapped_test(self):
            k = config.maximum_test_repetitions
            for pexercise in self.pexercises:
                exercise_class = pexercise.exercise.__class__
                input_generator = pexercise.input_generator()
                for input_data in itertools.islice(input_generator, 0, k):
                    pexercise.answers = input_data
                    with self.subTest(exercise=exercise_class,
                                      input=input_data):
                        test(self, pexercise)
        return wrapped_test

    @with_all_pexercises_and_all_inputs
    def test_total_score_is_nonnegative(self, pexercise):
        '''
        The total score should not be negative.
        '''
        self.assertGreaterEqual(
            pexercise.total_score, 0.0,
            'The maximal total score is negative.'
        )

    @with_all_pexercises_and_all_inputs
    def test_total_score_is_less_equal_maximal_total_score(self, pexercise):
        '''
        The total score should be less or equal the maximal total score.
        '''
        self.assertLessEqual(
            pexercise.total_score, pexercise.max_total_score,
            'The total score is greater than the maximal total score.'
        )

    @with_all_pexercises_and_all_inputs
    def test_scores_are_nonnegative(self, pexercise):
        '''
        The input field scores should not be negative.
        '''
        # Note that either all or none of the input fields are scored.
        if None in pexercise.scores.values():
            return
        for ifield, score in pexercise.scores.items():
            self.assertGreaterEqual(
                score, 0.0,
                f'The score for input field {ifield} is negative.'
            )

    @with_all_pexercises_and_all_inputs
    def test_scores_are_less_equal_maximal_scores(self, pexercise):
        '''
        For each input field the score should be less or equal the maximal
        score.
        '''
        # Note that either all or none of the input fields are scored.
        if None in pexercise.scores.values():
            return
        for ifield in pexercise.ifields:
            self.assertLessEqual(
                pexercise.scores[ifield], pexercise.max_scores[ifield],
                f'The score for input field {ifield} is greater than the '
                f'maximal score.'
            )

    @with_all_pexercises_and_all_inputs
    def test_score_sum_is_not_greater_total_score(self, pexercise):
        '''
        The total score is equal to the sum of all input field scores if the
        input fields are scored individually.
        '''
        # TODO: This should be a framework test and not a test for users.
        # Note that either all or none of the input fields are scored.
        score_output = pexercise.apply(
            pexercise.exercise.scores,
            pexercise.parameters | pexercise.dummy_input
        )
        scores = pexercise.scores.values()
        if isinstance(score_output, dict) or len(pexercise.ifields) == 1:
            self.assertEqual(
                sum(scores), pexercise.total_score,
                'The sum of the input field scores is not equal to the '
                'total score.'
            )

    @with_all_pexercises_and_all_inputs
    def test_score_method_return_values(self, pexercise):
        '''
        The score method of an exercise can return the scores for the answers
        in several formats:
            - A scalar value which is interpreted as the total score. Valid
              data types are bool, int, float, numpy.bool_, numpy.integer,
              numpy.floating. Booleans are converted to 0 or 1.
            - A tuple where the first value is interpreted as the total score
              and the second one as the maximal total score. Its elements have
              to match a type from above.
            - A dictionary with input field names as keys and scalar values or
              tuples as values. The input field names have to be strings. In
              case of a tuple the first value is interpreted as the score and
              the second one as the maximal score of the input field specified
              in the key.
        The type of the returned score must not change over different runs to
        keep exercises consistent.
        '''
        exercise = pexercise.exercise

        output = pexercise.apply(
            exercise.scores,
            pexercise.parameters | pexercise.dummy_input
        )
        for _ in range(config.maximum_test_repetitions):
            output_ = pexercise.apply(
                exercise.scores,
                pexercise.parameters | pexercise.dummy_input
            )
            self.assertEqual(
                type(output), type(output_),
                f"The scores method must return the same type over different "
                f"runs of an exercise, got {type(output)} and {type(output_)}."
            )

        if isinstance(output, dict) or len(pexercise.ifields) == 1:
            for answer in pexercise.answers.values():
                if answer is None:
                    return

        try:
            scores = pexercise.apply(
                exercise.scores,
                pexercise.parameters | pexercise.answers
            )
        except BaseException as e:
            if None in pexercise.answers.values():
                raise e.__class__(
                    f'It seems empty input fields in exercise '
                    f'{pexercise.exercise} are not properly treated.'
                ) from e
            raise e

        if scores is None:
            return
        if isinstance(scores, core.float_types):
            return
        if isinstance(scores, tuple):
            self.assertEqual(
                len(scores), 2,
                f'The tuple returned by the score method of exercise '
                f'{exercise} must consist of exactly two elements (got '
                f'{len(scores)}).'
            )
            for score in scores:
                self.assertIsInstance(
                    score, core.float_types,
                    f'The two elements in the tuple returned by the score '
                    f'method of exercise {exercise} must be integers or '
                    f'floats (got {type(score)}).'
                )
            self.assertLessEqual(
                scores[0], scores[1],
                f"The score ({scores[0]}) for exercise {exercise} "
                f"exceeds the maximal score ({scores[1]})."
            )
            return
        self.assertIsInstance(
            scores, dict,
            f'If implemented, the score method of exercise {exercise} must '
            f'return an integer, a float or a dictionary (got '
            f'{type(scores)}).'
        )
        for name, score in scores.items():
            self.assertIsInstance(
                name, str,
                f'The dictionary returned by the score method of exercise '
                f'{exercise} must be keyed with strings (got {type(name)}.'
            )
            self.assertIn(
                name, pexercise.ifields.keys(),
                f"The score method of exercise {exercise} scores a "
                f"non-existent input field '{name}'."
            )
            if isinstance(score, core.float_types):
                continue
            self.assertIsInstance(
                score, tuple,
                f"The score for input field '{name}' in exercise must be an "
                f"integer or a float (got {type(scores)})."
            )
            self.assertEqual(
                len(score), 2,
                f"The score tuple for input field '{name}' in exercise "
                f"{exercise} must consist of exactly two elements (got "
                f"{len(score)})."
            )
            for component in score:
                self.assertIsInstance(
                    component, core.float_types,
                    f"The two elements in the score tuple for input field "
                    f"'{name}' in exercise {exercise} must be integers or "
                    f"floats (got {type(component)})."
                )
            self.assertLessEqual(
                score[0], score[1],
                f"The score ({score[0]}) for input field '{name}' in "
                f"exercise {exercise} exceeds the maximal score ({score[1]})."
            )

    @with_all_pexercises_and_all_inputs
    def test_feedback_with_inputs(self, pexercise):
        '''
        Test if inputs (especially None values) raise an exception in the
        feedback method.
        '''
        pexercise.feedback
