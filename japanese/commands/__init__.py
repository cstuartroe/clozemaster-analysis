from .commands import print_ctype_counts, export_frequencies, print_nonstandard, joyo_stats, kanji_in_order
from .latex import latex
from .wiktionary_readings import all_wiktionary_readings
from .readings_analysis import reading_analysis

COMMANDS = {
    'joyo': joyo_stats,
    'ctypes': print_ctype_counts,
    'nonstandard': print_nonstandard,
    'export': export_frequencies,
    'latex': latex,
    "wiktionary_readings": all_wiktionary_readings,
    'reading_analysis': reading_analysis,
    'kanji_in_order': kanji_in_order,
}
