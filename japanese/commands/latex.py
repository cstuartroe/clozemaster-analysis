import argparse

from shared.commands.base import command, with_words
from japanese.lib.ctypes import CharacterType
from japanese.lib.exercise_list import JapaneseExerciseList

LATEX_TEMPLATE = r"""
\documentclass{article}
\usepackage{CJKutf8}

\title{Most common Kanji in Clozemaster}
\date{}

\setlength\parindent{24pt}

\begin{document}

\maketitle

%s

\end{document}
"""


CJK_FONT = "min"


@with_words
@command
def latex(el: JapaneseExerciseList, namespace: argparse.Namespace):
    most_common_kanji = sorted(
        el.character_counts(namespace.words)[CharacterType.KANJI].items(),
        key=lambda x: x[1],
        reverse=True,
    )

    content = ""

    for character, count in most_common_kanji:
        content += (
            f"\\begin{{CJK}}{{UTF8}}{{{CJK_FONT}}}"
            f"\\section{{{character}}}"
            "\\end{CJK}\n\n"
            f"{count} occurrences\n\n"
            "\\bigskip\n\n"
        )

        for reading, exercises in el.readings_by_character[character][::-1]:
            content += (
                f"\\noindent \\begin{{CJK}}{{UTF8}}{{{CJK_FONT}}}"
                f"{reading.kanji}　【{reading.kana}】"
                "\\end{CJK}\n"
                f"{len(exercises)} occurrence{'s' if len(exercises) > 1 else ''}\n\n"
                "\\bigskip\n\n"
            )

            exercise = exercises[0]

            content += (
                f"\\begin{{CJK}}{{UTF8}}{{{CJK_FONT}}}"
                f"{exercise.pronunciation}"
                "\\end{CJK}\n\n"
                f"{exercise.translation}\n\n"
                "\\bigskip\n\n"
            )

    print(LATEX_TEMPLATE % content)
