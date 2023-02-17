import argparse

from matplotlib import pyplot as plt

from shared.lib.dataclasses import ExerciseList
from .base import command, with_collection_type, with_case, with_words


@with_words
@with_case
@with_collection_type
@command
def zipf(el: ExerciseList, namespace: argparse.Namespace):
    items = [*el.get_counts(namespace.collection_type, words=namespace.words, case=namespace.case).items()]
    items.sort(key=lambda pair: -len(pair[1]))
    data = [(rank + 1, len(exercises)) for rank, (_, exercises) in enumerate(items)]
    plt.plot(*zip(*data))
    plt.yscale('log')
    plt.xscale('log')
    plt.title(f'Zipfiness of {namespace.collection_type}')
    plt.show()
