import argparse
import math

from shared.lib.dataclasses import all_exercises, Exercise, ExerciseList
from shared.commands.base import (
    get_language_code, command, with_substring, with_words, with_limit, with_collection_type, with_case, with_arg)


@command
def reload_sentences(_el: ExerciseList, _namespace: argparse.ArgumentParser):
    exercises = all_exercises(f'{get_language_code()}-eng', force_reload=True)
    print(f"{len(exercises)} sentences downloaded.")


def contains(e: Exercise, q: str, words: bool, case: bool):
    string = e.string(words)
    translation = e.translation
    if not case:
        string = string.lower()
        translation = translation.lower()
        q = q.lower()
    return (q in string) or (q in translation)


@with_case
@with_substring
@with_words
@with_limit
@command
def containing(el: ExerciseList, namespace: argparse.Namespace):
    matching = [
        (i+1, e)
        for i, e in enumerate(el.exercises)
        if contains(e, namespace.substring, namespace.words, namespace.case)
    ]

    for i, e in matching[:namespace.limit]:
        print(f"#{i} {e.text}")
        print(e.pronunciation)
        print(e.tokens)
        print(e.translation)
        print()

    print(f"{len(matching)} exercises matched.")


@command
def played_pattern(el: ExerciseList, _namespace: argparse.Namespace):
    played = 0
    total = 0
    for i, e in enumerate(el.exercises):
        total += 1
        if e.numPlayed == 0:
            c = '_'
        else:
            c = '#'
            played += 1
        print(c, end='')
        if i % 60 == 59:
            print(f" {played}/{total}")

    print()


@with_case
@with_words
@with_collection_type
@with_limit
@command
def print_most_common(el: ExerciseList, namespace: argparse.Namespace):
    occurrences = sorted(
        el.get_counts(namespace.collection_type, namespace.words, namespace.case).items(),
        key=lambda x: len(x[1]),
    )
    limit = min(int(namespace.limit), len(occurrences))

    for i, (collectible, exercises) in enumerate(occurrences[-limit:]):
        print(f"{limit - i:>4} {len(exercises):>4} {collectible}")

    print(f"{len(occurrences)} total {namespace.collection_type} ({len(occurrences)/len(el.exercises):.2f} per exercise)")

    well_tested = [
        (o, exercises)
        for o, exercises in occurrences
        if len(exercises) >= namespace.threshold
    ]
    print(f"{len(well_tested)} well-tested {namespace.collection_type} ({len(well_tested)/len(el.exercises):.2f}"
          f" per exercise)")


def histogram_bar(count: int, cap: int = 100):
    return f"{'#'*min(count, cap)}{str(count) if count > cap else ''}"


@with_case
@with_words
@with_collection_type
@command
def to_play_histogram(el: ExerciseList, namespace: argparse.Namespace):
    played_exercises = type(el)([e for e in el.exercises if e.numPlayed > 0])
    current_counts = played_exercises.get_counts(namespace.collection_type, namespace.words, namespace.case)

    total_counts = el.get_counts(namespace.collection_type, namespace.words, namespace.case)

    played_total_counts = sorted(
        [(k, total_counts[k]) for k in current_counts.keys()],
        key=lambda x: len(x[1]),
    )

    pad = max(map(len, current_counts.keys()))

    for k, exercises in played_total_counts:
        print(f"{k.ljust(pad, '＿')} {histogram_bar(len(exercises))}")

    print(f"{len([k for k, es in current_counts.items() if len(es) >= namespace.threshold])}"
          f"/{len(current_counts)} currently well-tested")
    print(f"{len([k for k in current_counts.keys() if len(total_counts[k]) >= namespace.threshold])}"
          f"/{len(current_counts)} eventually well-tested")


@with_case
@with_words
@with_collection_type
@command
def coverage(el: ExerciseList, namespace: argparse.Namespace):
    all_el = type(el)(all_exercises("jpn-eng"))

    occurrences = el.get_counts(collection_type=namespace.collection_type, words=namespace.words, case=namespace.case)
    all_occurrences = all_el.get_counts(collection_type=namespace.collection_type, words=namespace.words,
                                        case=namespace.case)

    seen_items = set(occurrences.keys())
    well_tested_items = set(item for item, exercises in occurrences.items() if len(exercises) >= namespace.threshold)

    for title, item_set in (('tested', seen_items), ('well-tested', well_tested_items)):
        total_occurrences = 0
        occurrence_coverage = 0

        for item, exercises in all_occurrences.items():
            total_occurrences += len(exercises)
            if item in item_set:
                occurrence_coverage += len(exercises)

        print(f"{occurrence_coverage}/{total_occurrences} ({100*occurrence_coverage/total_occurrences:<.1f}%)"
              f" {namespace.collection_type} usages are among {title} items.")


@with_case
@with_words
@with_collection_type
@with_arg(lambda parser: parser.add_argument('-b', '--bin_size', type=int, required=False, default=60))
@command
def new_items(el: ExerciseList, namespace: argparse.Namespace):
    seen_items = set()
    el.exercises = el.exercises[29:]
    for i in range(math.ceil(len(el.exercises)/namespace.bin_size)):
        day_exercises = type(el)(el.exercises[i*namespace.bin_size:(i+1)*namespace.bin_size])
        day_items = day_exercises.get_counts(collection_type=namespace.collection_type,
                                             words=namespace.words, case=namespace.case).keys()

        new_items = [e for e in day_items if e not in seen_items]
        if all(len(item) == 1 for item in day_items):
            graphic = ''.join(new_items)
        else:
            graphic = histogram_bar(len(new_items))
        print(f"{i+1:<3} {len(new_items):<3} {graphic}")
        seen_items = seen_items | set(day_items)
