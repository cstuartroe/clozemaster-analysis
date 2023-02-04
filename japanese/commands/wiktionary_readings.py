import argparse
import os
from tqdm import tqdm

from shared.commands.base import command
from japanese.lib.ctypes import CharacterType, ctype
from japanese.lib.kana import parse_onset, phonemic_transcribe_hiragana
from japanese.lib.kanji import joyo_up_to, wiktionary_readings
from japanese.lib.exercise_list import JapaneseExerciseList


CSV_ONSETS_NO_Y = ("", "k", "g", "s", "z", "t", "d", "n", "h", "b", "m", "y", "r", "w")
CSV_ONSETS = []
for o in CSV_ONSETS_NO_Y:
    CSV_ONSETS.append(o)
    if o not in ("", "d", "y", "w"):
        CSV_ONSETS.append(o + "y")


CSV_FINALS = []
for v in "aiueo":
    for end in ("", "ki", "ku", "ti", "tu", "N"):
        CSV_FINALS.append(v + end)
for diphthong in ["ai", "ei", "ou", "uu", "ui"]:
    i = CSV_FINALS.index(diphthong[0])
    CSV_FINALS.insert(i+1, diphthong)


ONSET_RESPELLINGS = {
    "sy": "sh",
    "zy": "j",
    "ty": "ch",
}


def make_readings_csv(title: str, readings: list[str], separator=','):
    pairs = {}

    for reading in readings:
        onset, final = parse_onset(phonemic_transcribe_hiragana(reading))
        if onset not in CSV_ONSETS or final not in CSV_FINALS:
            print(reading, phonemic_transcribe_hiragana(reading))
        else:
            pairs[(onset, final)] = pairs.get((onset, final), 0) + 1

    content = separator.join(['', *[ONSET_RESPELLINGS.get(o, o) for o in CSV_ONSETS]]) + "\n"
    for final in CSV_FINALS:
        content += final.replace("tu", "tsu").replace("ti", "chi").replace("N", "n")
        for onset in CSV_ONSETS:
            content += separator
            if (onset, final) in pairs:
                content += str(pairs[(onset, final)])
        content += '\n'

    os.makedirs('readings', exist_ok=True)
    with open(f"readings/{title}.csv", "w") as fh:
        fh.write(content)


@command
def all_wiktionary_readings(el: JapaneseExerciseList, _namespace: argparse.Namespace):
    kanji = set()

    for e in el.exercises:
        for c in e.sentence:
            if ctype(c) is CharacterType.KANJI:
                kanji.add(c)

    for c in joyo_up_to(7):
        kanji.add(c)

    readings_by_type = {}
    for c in tqdm(sorted(list(kanji))):
        for reading_type, readings in wiktionary_readings(c).items():
            if reading_type not in readings_by_type:
                readings_by_type[reading_type] = []

            readings_by_type[reading_type] += readings

    for rt in sorted(list(readings_by_type.keys()), key=lambda t: -len(readings_by_type[t])):
        print(rt)

        readings = readings_by_type[rt]

        print(f"{len(readings)} readings")
        print(f"{len(set(readings))} distinct readings")

        if rt.endswith("-on"):
            make_readings_csv(rt, readings)

        print()
