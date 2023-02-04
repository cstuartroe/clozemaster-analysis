from functools import cached_property, cache
from typing import Union

from shared.lib.dataclasses import Exercise, ExerciseList
from japanese.lib.ctypes import CharacterType, ctype
from japanese.lib.kanji import Reading, ReadingsParser

Collectible = Union[str, Reading]
Occurrences = dict[Collectible, list[Exercise]]


class JapaneseExerciseList(ExerciseList):
    @cache
    def character_counts(self, words: bool) -> dict[CharacterType, Occurrences]:
        out: dict[CharacterType, Occurrences] = {
            ct: {}
            for ct in CharacterType
        }

        for e in self.exercises:
            s = e.string(words)
            for c in s:
                ct = ctype(c)
                if c not in out[ct]:
                    out[ct][c] = []
                out[ct][c].append(s)

        return out

    @cache
    def ctype_counts(self, words: bool) -> dict[CharacterType, int]:
        return {
            ct: sum(len(exercises) for exercises in self.character_counts(words)[ct].values())
            for ct in CharacterType
        }

    @cached_property
    def readings(self) -> Occurrences:
        out: dict[Reading, list[Exercise]] = {}

        for e in self.exercises:
            for reading in ReadingsParser(e).parse():
                if reading not in out:
                    out[reading] = []
                out[reading].append(e)

        return out

    @cached_property
    def readings_by_character(self) -> dict[str, list[tuple[Reading, list[Exercise]]]]:
        out: dict[str, list[tuple[Reading, list[Exercise]]]] = {}

        for reading, exercises in self.readings.items():
            for c in reading.kanji:
                if c not in out:
                    out[c] = []
                out[c].append((reading, exercises))

        for l in out.values():
            l.sort(key=lambda x: len(x[1]))

        return out

    def get_collection_getters(self, words: bool, case: bool):
        out = super().get_collection_getters(words, case)
        out["READINGS"] = lambda: self.readings
        for ct in CharacterType:
            out[ct.name] = (lambda _ct: lambda: self.character_counts(words)[_ct])(ct)
        return out
