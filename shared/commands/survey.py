import argparse

from shared.lib.dataclasses import ExerciseList
from .base import command, with_limit, with_collection_type, with_arg, with_words, with_case


def run_survey(chars: list[str], sample):
    tested = 0
    known = 0
    wrong: list[str] = []

    for i in range(0, len(chars), sample or 1):
        character = chars[i]
        print(character, end='')
        input()

        response = input('Known? (y for yes) ')
        print()

        tested += 1
        if response == 'y':
            known += 1
        else:
            wrong.append(character)

    print(f"{known}/{tested} known ({round(100 * known / tested, 1)}%)")

    if sample == 0 and len(wrong) > 0:
        print()
        run_survey(wrong, 0)


@with_case
@with_words
@with_collection_type
@with_limit
@with_arg(lambda parser: parser.add_argument('-S', '--sample', type=int, required=False, default=1))
@command
def survey(el: ExerciseList, namespace: argparse.Namespace):
    most_common = [
        c for c, count in sorted(
            el.get_counts(namespace.collection_type, words=namespace.words, case=namespace.case).items(),
            key=lambda x: x[1],
            reverse=True,
        )
    ]

    run_survey(most_common[:namespace.limit], namespace.sample)
