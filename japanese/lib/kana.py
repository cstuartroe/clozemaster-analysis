import re

import regex

from .ctypes import CharacterType


HIRAGANA_TABLE = {
    '': 'あいうえお', 'k': 'かきくけこ', 's': 'さしすせそ', 't': 'たちつてと', 'n': 'なにぬねの',
    'h': 'はひふへほ', 'm': 'まみむめも', 'y': 'や ゆ よ', 'r': 'らりるれろ', 'w': 'わゐ ゑを',
    'g': 'がぎぐげご', 'z': 'ざじずぜぞ', 'd': 'だぢづでど', 'b': 'ばびぶべぼ', 'p': 'ぱぴぷぺぽ',
    '-': 'ぁ  ぇ ', '-y': 'ゃ ゅ ょ',
}

KATAKANA_TABLE = {
    '': 'アイウエオ', 'k': 'カキクケコ', 's': 'サシスセソ', 't': 'タチツテト', 'n': 'ナニヌネノ',
    'h': 'ハヒフヘホ', 'm': 'マミムメモ', 'y': 'ヤ ユ ヨ', 'r': 'ラリルレロ', 'w': 'ワヰ ヱヲ',
    'g': 'ガギグゲゴ', 'z': 'ザジズゼゾ', 'd': 'ダヂヅデド', 'b': 'バビブベボ', 'p': 'パピプペポ',
    '-': 'ァィゥェォ', '-y': 'ャ ュ ョ', 'v': '  ヴ  '
}

VOWELS = 'aiueo'


def phonemic_kana_table(table) -> dict[str, str]:
    return {
        kana: c + VOWELS[i]
        for c, kanas in table.items()
        for i, kana in enumerate(kanas)
        if kana != ' '
    }


TRANSCRIPTION_REPLACEMENTS = {
    'hu': 'fu',
    'tu': 'tsu',
    'du': 'zu',
    'si': 'shi',
    'ti': 'chi',
    'di': 'ji',
    'zi': 'ji',
}


def replace_table(table) -> dict[str, str]:
    return {
        k: TRANSCRIPTION_REPLACEMENTS.get(v, v)
        for k, v in table.items()
    }


PHONEMIC_HIRAGANA_TRANSCRIPTIONS: dict[str, str] = {
    **phonemic_kana_table(HIRAGANA_TABLE),
    'ん': 'N',
    'っ': 'Q',
}


HIRAGANA_TRANSCRIPTIONS: dict[str, str] = replace_table(PHONEMIC_HIRAGANA_TRANSCRIPTIONS)


KATAKANA_TRANSCRIPTIONS: dict[str, str] = replace_table({
    **phonemic_kana_table(KATAKANA_TABLE),
    'ン': 'N',
    'ッ': 'Q',
    'ー': 'chōonpu',
})


def phonemic_transcribe_hiragana(s: str) -> str:
    out = ''
    for c in s:
        t = PHONEMIC_HIRAGANA_TRANSCRIPTIONS[c]
        prev = out[-1] if out else None
        if t[0] == '-':
            if t[1] == 'y':
                assert prev == 'i'
                out = out[:-1] + t[1:]
            else:
                raise ValueError(f"Unknown continuation character: {s}")
        else:
            if t[0] in 'aiueo' and prev == 'N':
                out += '\''
            elif out and prev == 'Q':
                assert t[0] in 'ksctp'
                out = out[:-1] + t[0]

            out += t

    return out


def parse_onset(transription: str) -> tuple[str, str]:
    onset = re.match('[kgsztdcjnhfpbmyrw]*', transription).group()
    return onset, transription[len(onset):]


ROMAJI_MORAS_TO_HIRAGANA = {
    v: k
    for k, v in HIRAGANA_TRANSCRIPTIONS.items()
    if k not in 'づぢ'
}
for cons in 'szth':
    i_syll = cons + 'i'
    if i_syll in TRANSCRIPTION_REPLACEMENTS:
        i_syll = TRANSCRIPTION_REPLACEMENTS[i_syll]
        onset_romaji = i_syll[:-1]
    else:
        onset_romaji = cons + 'y'

    for kana, vowel in zip(HIRAGANA_TABLE['-y'], VOWELS):
        if kana == ' ':
            continue
        ROMAJI_MORAS_TO_HIRAGANA[onset_romaji + vowel] = ROMAJI_MORAS_TO_HIRAGANA[i_syll] + kana


def romaji_coda_to_hiragana(c: str) -> str:
    if c == 'n':
        return ROMAJI_MORAS_TO_HIRAGANA['N']
    elif c in 'kstp':
        return ROMAJI_MORAS_TO_HIRAGANA['Q']
    else:
        raise ValueError(f"Malformed coda: {c}")


LONG_VOWELS = {
    'ā': 'a',
    'ē': 'e',
    'ī': 'i',
    'ō': 'o',
    'ū': 'u',
}


def romaji_to_hiragana(romaji: str) -> str:
    match = regex.fullmatch("(([kgsztdcjnhfpbmyrw]*)[aeiouāēīōū])+([nkstp]?)", romaji)
    if not match:
        raise ValueError(f"Malformatted romaji: {romaji}")

    out = ''
    for syllable in match.captures(1):
        if syllable[-1] in LONG_VOWELS:
            short_vowel = LONG_VOWELS[syllable[-1]]
            out += romaji_to_hiragana(syllable[:-1] + short_vowel) + ROMAJI_MORAS_TO_HIRAGANA[short_vowel]
        elif syllable in ROMAJI_MORAS_TO_HIRAGANA:
            out += ROMAJI_MORAS_TO_HIRAGANA[syllable]
        elif syllable[1:] in ROMAJI_MORAS_TO_HIRAGANA:
            out += romaji_coda_to_hiragana(syllable[0]) + ROMAJI_MORAS_TO_HIRAGANA[syllable[1:]]
        else:
            raise ValueError(f"Malformatted syllable: {syllable}")
    if match.group(3):
        out += romaji_coda_to_hiragana(match.group(3))

    return out


TRANSCRIPTIONS: dict[CharacterType, dict[str, str]] = {
    CharacterType.HIRAGANA: HIRAGANA_TRANSCRIPTIONS,
    CharacterType.KATAKANA: KATAKANA_TRANSCRIPTIONS,
}


LONG_O_CHARS = 'おう'
ZU_CHARS = 'ずづ'
JI_CHARS = 'じぢ'


def match_conforming(prefix: str, word: str) -> tuple[str, bool]:
    if len(prefix) > len(word):
        return prefix, False

    conformed_prefix = ''
    for pc, wc in zip(prefix, word):
        if pc == wc:
            pass

        elif pc in LONG_O_CHARS and wc in LONG_O_CHARS and conformed_prefix and HIRAGANA_TRANSCRIPTIONS[conformed_prefix[-1]].endswith('o'):
            pass

        elif pc in ZU_CHARS and wc in ZU_CHARS:
            pass

        elif pc in JI_CHARS and wc in JI_CHARS:
            pass

        else:
            return prefix, False

        conformed_prefix += wc

    if conformed_prefix != prefix:
        print(f"Conformed prefix: {prefix} {word} > {conformed_prefix}")

    return conformed_prefix, True
