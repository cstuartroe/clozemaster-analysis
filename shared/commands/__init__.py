from .commands import (
    reload_sentences,
    containing,
    played_pattern,
    print_most_common,
    coverage,
    to_play_histogram,
    new_items,
    sample_sentences,
)
from .survey import survey
from .zipf import zipf

COMMANDS = {
    'reload': reload_sentences,
    'common': print_most_common,
    'survey': survey,
    'contain': containing,
    'played': played_pattern,
    'to_play': to_play_histogram,
    "coverage": coverage,
    "zipf": zipf,
    "new": new_items,
    'sample': sample_sentences,
}
