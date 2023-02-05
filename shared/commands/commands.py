import argparse

from shared.lib.dataclasses import all_exercises, Exercise, ExerciseList
from shared.commands.base import (
    get_language_code, command, with_substring, with_words, with_limit, with_collection_type, with_case)


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
        e
        for e in el.exercises
        if contains(e, namespace.substring, namespace.words, namespace.case)
    ]

    for e in matching[:namespace.limit]:
        print(e.text)
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


@command
def to_play_histogram(el: ExerciseList, namespace: argparse.Namespace):
    current_counts = {}
    for e in el.exercises:
        if e.numPlayed == 0:
            continue
        for t in e.tokens:
            current_counts[t.lemma] = current_counts.get(t.lemma, 0) + 1
    del current_counts[None]

    total_counts = {}
    for e in el.exercises:
        for t in e.tokens:
            total_counts[t.lemma] = total_counts.get(t.lemma, 0) + 1
    del total_counts[None]

    played_total_counts = sorted(
        [(l, total_counts[l]) for l in current_counts.keys()],
        key=lambda x: x[1],
    )

    cap = 100
    for lemma, count in played_total_counts:
        print(f"{lemma:＿<6} {'#'*min(count, cap)}{str(count) if count > cap else ''}")

    print(f"{len([l for l, c in current_counts.items() if c >= namespace.threshold])}"
          f"/{len(current_counts)} currently well-tested")
    print(f"{len([l for l in current_counts.keys() if total_counts[l] >= namespace.threshold])}"
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
