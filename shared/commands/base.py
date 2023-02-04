import argparse
import sys
from typing import Callable

from shared.lib.dataclasses import Exercise, ExerciseList
from japanese.lib.exercise_list import JapaneseExerciseList


def get_language_code():
    return sys.argv[1]


def get_command_name():
    return sys.argv[2]


EXERCISE_LIST_CLASSES = {
    "jpn": JapaneseExerciseList,
    "ind": ExerciseList,
}


def command(func: Callable[[ExerciseList, argparse.Namespace], None]):
    exercise_list_class = EXERCISE_LIST_CLASSES[get_language_code()]

    def wrapped_func(exercises: list[Exercise], parser: argparse.ArgumentParser, unparsed_args: list[str]):
        parser.add_argument('-p', '--playing', action='store_true', help='Limit to sentences which I am playing')
        parser.add_argument('-n', '--num_sentences', type=int, default=None, required=False,
                            help='Number of sentences')
        parser.add_argument('-t', '--threshold', type=int, required=False, default=3,
                            help="Well-tested threshold")

        namespace = parser.parse_args(unparsed_args)

        if namespace.playing:
            if namespace.num_sentences:
                print("Don't pass both --playing and --num_sentences")

            exercises = [
                e for e in exercises
                if e.numPlayed > 0
            ]
        elif namespace.num_sentences:
            exercises = exercises[:namespace.num_sentences]

        func(exercise_list_class(exercises), namespace)

    return wrapped_func


def with_arg(adder: Callable[[argparse.ArgumentParser], None]):
    def command_wrapper(func: Callable[[list[Exercise], argparse.ArgumentParser, list[str]], None]):
        def wrapped_func(exercises: list[Exercise], parser: argparse.ArgumentParser, unparsed_args: list[str]):
            adder(parser)
            func(exercises, parser, unparsed_args)

        return wrapped_func

    return command_wrapper


with_substring = with_arg(lambda parser: parser.add_argument('substring', type=str))
with_limit = with_arg(lambda parser: parser.add_argument('-l', '--limit', type=int, required=False, default=100))
with_words = with_arg(lambda parser: parser.add_argument('-w', '--words', action='store_true'))
with_collection_type = with_arg(lambda parser: parser.add_argument('collection_type', type=str))
with_case = with_arg(lambda parser: parser.add_argument('-c', '--case', action='store_true'))
