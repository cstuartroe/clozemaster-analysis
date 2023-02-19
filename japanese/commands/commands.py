import argparse
import os

from shared.commands.base import command, with_words
from japanese.lib.ctypes import CharacterType, ctype
from japanese.lib.kanji import JOYO, joyo_up_to
from japanese.lib.exercise_list import JapaneseExerciseList


@with_words
@command
def print_ctype_counts(el: JapaneseExerciseList, namespace: argparse.Namespace):
    for t, n in sorted(list(el.ctype_counts(namespace.words).items()), key=lambda x: x[1]):
        print(f"{t.value:<20} {n:>6}")


@with_words
@command
def export_frequencies(el: JapaneseExerciseList, namespace: argparse.Namespace):
    dirname = f'frequency/jpn-eng'
    os.makedirs(dirname, exist_ok=True)
    for ct in CharacterType:
        with open(os.path.join(dirname, f'{ct.value}.txt'), 'w') as fh:
            for w, f in sorted(list(el.character_counts(namespace.words)[ct].items()), key=lambda x: x[1], reverse=True):
                fh.write(f"{w}\t{f}\n")


NORMAL_CTYPES = (CharacterType.KANJI, CharacterType.HIRAGANA, CharacterType.KATAKANA, CharacterType.SPECIAL)


@with_words
@command
def print_nonstandard(el: JapaneseExerciseList, namespace: argparse.Namespace):
    for e in el.exercises:
        s = e.string(namespace.words)
        nonstandard = [c for c in s if ctype(c) not in NORMAL_CTYPES]
        if nonstandard:
            print(s)
            print(','.join(nonstandard))
            print()


@with_words
@command
def joyo_stats(el: JapaneseExerciseList, namespace: argparse.Namespace):
    kanji_counts = {
        k: len(exercises)
        for k, exercises in el.character_counts(namespace.words)[CharacterType.KANJI].items()
    }
    print(f"{len(kanji_counts)} kanji\n")

    for level, kanji_list in JOYO.items():
        cumulayive_joyo = joyo_up_to(level)
        cumulative_included_joyo = [j for j in cumulayive_joyo if j in kanji_counts]
        cumulative_well_tested_joyo = [j for j in cumulayive_joyo if (kanji_counts.get(j, 0) >= namespace.threshold)]

        print(f"{len(cumulative_well_tested_joyo)}/{len(cumulayive_joyo)} "
              f"({len(cumulative_well_tested_joyo)/len(cumulayive_joyo)*100:.1f}%) "
              f"Joyo up to level {level} are well-tested")
        print(f"{len(cumulative_included_joyo)}/{len(cumulayive_joyo)} "
              f"({len(cumulative_included_joyo)/len(cumulayive_joyo)*100:.1f}%) "
              f"Joyo up to level {level} are tested")

        level_included_joyo = [j for j in kanji_list if j in kanji_counts]
        level_well_tested_joyo = sorted([j for j in kanji_list if kanji_counts.get(j, 0) >= namespace.threshold])
        level_poorly_tested_joyo = sorted(list(set(level_included_joyo) - set(level_well_tested_joyo)))
        level_excluded_joyo = sorted([j for j in kanji_list if j not in kanji_counts])

        if len(level_well_tested_joyo) > 0:
            print(f"{len(level_well_tested_joyo)} well tested joyo: {''.join(level_well_tested_joyo)}")
        if len(level_poorly_tested_joyo) > 0:
            print(f"{len(level_poorly_tested_joyo)} poorly tested joyo: {''.join(level_poorly_tested_joyo)}")
        if len(level_excluded_joyo) > 0:
            print(f"{len(level_excluded_joyo)} excluded Joyo: {''.join(level_excluded_joyo)}")

        print()
