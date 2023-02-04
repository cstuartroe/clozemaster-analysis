from enum import Enum


class CharacterType(Enum):
    ASCII = "ASCII"
    JPUNCT = "CJK punctuation"
    HIRAGANA = "hiragana"
    KATAKANA = "katakana"
    KANJI = "kanji"
    FULLWIDTH = "fullwidth ASCII"
    SPECIAL = "special"
    OTHER = "other"


def ctype(c: str) -> CharacterType:
    o = ord(c)

    if c in "々ヶヵ・":
        return CharacterType.SPECIAL

    if 0x3000 <= o <= 0x303F:
        return CharacterType.JPUNCT

    if 0x3040 <= o <= 0x309F:
        return CharacterType.HIRAGANA

    if 0x30A0 <= o <= 0x30FF:
        return CharacterType.KATAKANA

    if 0x4E00 <= o <= 0x9FFF:
        return CharacterType.KANJI

    if 0xFF00 <= o <= 0xFF5F:
        return CharacterType.FULLWIDTH

    if o <= 0x007F:
        return CharacterType.ASCII

    return CharacterType.OTHER
