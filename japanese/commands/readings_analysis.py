from dataclasses import dataclass

from shared.commands.base import command
from japanese.lib.exercise_list import JapaneseExerciseList

Readings = dict[str, dict[str, int]]


def is_regular_reading(kanji: str, multi_kanji_reading: str, one_kanji_readings: Readings):
    if (kanji == "") is not (multi_kanji_reading == ""):
        print(f"Empty mismatch: {repr(kanji)} {repr(multi_kanji_reading)}")
        return False

    if kanji == "":
        return True

    for logogram in kanji:
        for one_kanji_reading in one_kanji_readings.get(logogram, {}).keys():
            if multi_kanji_reading.startswith(one_kanji_reading):
                if is_regular_reading(kanji[1:], multi_kanji_reading[len(one_kanji_reading):], one_kanji_readings):
                    return True

            if len(one_kanji_reading) > 1 and one_kanji_reading[-1] in "つちくき":
                with_sokuon = one_kanji_reading[:-1] + 'っ'
                if with_sokuon not in one_kanji_readings[logogram] and multi_kanji_reading.startswith(with_sokuon):
                    if is_regular_reading(kanji[1:], multi_kanji_reading[len(with_sokuon):], one_kanji_readings):
                        one_kanji_readings[logogram][with_sokuon] = 0
                        return True

    return False


def add_reading(readings: Readings, kanji: str, reading: str, count: int):
    if kanji not in readings:
        readings[kanji] = {}

    if reading in readings[kanji]:
        raise ValueError(f"Reading already present: {kanji} {reading}")

    readings[kanji][reading] = count


@dataclass
class ReadingsAnalysis:
    el: JapaneseExerciseList

    def __post_init__(self):
        self.one_kanji_readings: Readings = {}
        multi_kanji_readings: Readings = {}

        for (kanji, reading), exercises in self.el.readings.items():
            if len(kanji) == 1:
                add_reading(self.one_kanji_readings, kanji, reading, len(exercises))
            else:
                add_reading(multi_kanji_readings, kanji, reading, len(exercises))

        self.regular_multi_kanji_readings: Readings = {}
        self.irregular_multi_kanji_readings: Readings = {}

        for kanji, readings in multi_kanji_readings.items():
            for reading, count in readings.items():
                if is_regular_reading(kanji, reading, self.one_kanji_readings):
                    add_reading(self.regular_multi_kanji_readings, kanji, reading, count)
                else:
                    add_reading(self.irregular_multi_kanji_readings, kanji, reading, count)


@command
def reading_analysis(el: JapaneseExerciseList, limit: str = '100'):
    analysis = ReadingsAnalysis(el)
    limit = int(limit)

    for name, multi_kanji_readings in (("Regular", analysis.regular_multi_kanji_readings),
                                       ("Irregular", analysis.irregular_multi_kanji_readings)):
        print(f"{name} readings:\n")

        multi_kanji_readings = [
            (kanji, reading, count)
            for kanji, readings in multi_kanji_readings.items()
            for reading, count in readings.items()
        ]
        multi_kanji_readings.sort(key=lambda x: x[2])
        list_limit = min(limit, len(multi_kanji_readings))

        for i, (kanji, reading, count) in enumerate(multi_kanji_readings[-list_limit:]):
            print(f"{list_limit-i:>4} {kanji:＿<4} {reading:＿<6} {count:>4}")
            for logogram in kanji:
                print(f"     - {logogram} {'/'.join(analysis.one_kanji_readings.get(logogram, {}).keys())}")

        print(f"\n{len(multi_kanji_readings)} {name.lower()} readings.\n")
