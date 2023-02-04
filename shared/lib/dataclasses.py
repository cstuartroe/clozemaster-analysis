import sys
from dataclasses import dataclass, asdict
from functools import cached_property, cache
import json
import os
import re
from typing import Optional, Callable

from tqdm import tqdm

from .networking import fetch_tokens, get_all_exercises


@dataclass
class Token:
    text: str
    lemma: str
    pos: str


TOKENS_FILE = "tokens.json"


class _TokenManager:
    def __init__(self):
        if os.path.isfile(TOKENS_FILE):
            with open(TOKENS_FILE, "r") as fh:
                tokens_json = json.load(fh)
        else:
            tokens_json = {}

        self.tokens: dict[int, dict[int, list[Token]]] = {
            int(collection_id): {
                int(sentence_id): list(map(lambda d: Token(**d), tokens))
                for sentence_id, tokens in sentences.items()
            }
            for collection_id, sentences in tokens_json.items()
        }

        self.unsaved_sentences: int = 0

    def get_tokens(self, collection_id: int, sentence_id: int) -> list[Token]:
        if collection_id not in self.tokens:
            self.tokens[collection_id] = {}

        if sentence_id not in self.tokens[collection_id]:
            self.tokens[collection_id][sentence_id] = [
                Token(text=t["text"], lemma=t["lemma"]["text"], pos=t["posTag"]["label"])
                for t in fetch_tokens(collection_id, sentence_id)
            ]

            self.unsaved_sentences += 1
            if self.unsaved_sentences >= 100:
                self.write()

        return self.tokens[collection_id][sentence_id]

    def write(self):
        tokens_json = {
            str(collection_id): {
                str(sentence_id): list(map(asdict, tokens))
                for sentence_id, tokens in sentences.items()
            }
            for collection_id, sentences in self.tokens.items()
        }

        with open(TOKENS_FILE, "w") as fh:
            json.dump(tokens_json, fh, indent=2, sort_keys=True)

        self.unsaved_sentences = 0


TokenManager = _TokenManager()


@dataclass
class Exercise:
    alternativeAnswers: list
    audioRecordingUrl: None
    clozeSentenceId: int
    collectionId: int
    commentsCount: int
    difficulty: None
    easinessFactor: None
    favorited: None
    hint: str
    id: int
    idiom: None
    ignored: None
    level: int
    moderated: bool
    multipleChoiceOptions: list
    nextReview: None
    notes: str
    nsfw: None
    numIgnored: int
    numIncorrect: int
    numPlayed: int
    pronunciation: str
    repetitionInterval: None
    sourceName: str
    sourceUrl: str
    tatoebaId: int
    text: str
    tokensCount: None
    translation: str
    transliteration: None
    ttsAudioUrl: str
    copyUrl: str
    tokensUrl: str
    url: str
    clozeSentenceTokensUrl: str
    clozeSentenceUrl: str
    _tokens: Optional[list[Token]] = None

    @cached_property
    def word(self):
        m = re.search("\{\{([^}]+)}}", self.text)

        if m is None:
            raise ValueError

        return m.group(1)

    @cached_property
    def sentence(self):
        return self.text.replace("{{", "").replace("}}", "")

    @cached_property
    def tokens(self) -> list[Token]:
        if self._tokens is None:
            self._tokens = TokenManager.get_tokens(self.collectionId, self.id)

        return self._tokens

    def string(self, word: bool):
        return self.word if word else self.sentence

    def __hash__(self):
        return hash(self.id)


def all_exercises(course: str, force_reload: bool = False) -> list[Exercise]:
    os.makedirs("exercises", exist_ok=True)

    course_file = f"exercises/{course}.json"

    if force_reload or not os.path.exists(course_file):
        exercises = [
            Exercise(**d)
            for d in get_all_exercises(course)
        ]

        with open(course_file, "w") as fh:
            json.dump(
                {
                    "exercises": [
                        asdict(e)
                        for e in exercises
                    ],
                },
                fh,
                indent=2
            )

    else:
        with open(course_file, "r") as fh:
            exercises = [
                Exercise(**d)
                for d in json.load(fh)["exercises"]
            ]

    return exercises


@dataclass
class ExerciseList:
    exercises: list[Exercise]

    def __hash__(self):
        return id(self)

    @cache
    def characters(self, words: bool, case: bool) -> dict[str, list[Exercise]]:
        out: dict[str, list[Exercise]] = {}
        for e in self.exercises:
            for c in e.string(words):
                if not case:
                    c = c.lower()
                if c not in out:
                    out[c] = []
                out[c].append(e)
        return out

    @cached_property
    def lemmas(self) -> dict[str, list[Exercise]]:
        out: dict[str, list[Exercise]] = {}

        for e in tqdm(self.exercises):
            for t in e.tokens:
                if t.lemma not in out:
                    out[t.lemma] = []
                out[t.lemma].append(e)

        TokenManager.write()

        if None in out:
            del out[None]

        return out

    def get_collection_getters(self, words: bool, case: bool) -> dict[str, Callable[[], dict[str, list[Exercise]]]]:
        return {
            "LEMMAS": lambda: self.lemmas,
            "CHARACTERS": lambda: self.characters(words, case)
        }

    def get_counts(self, collection_type: str, words: bool, case: bool) -> dict[str, list[Exercise]]:
        collection_type = collection_type.upper()
        collection_getters = self.get_collection_getters(words, case)
        if collection_type not in collection_getters:
            print(f"Invalid collection type (choices: {', '.join(collection_getters.keys())})")
            sys.exit(1)
        return collection_getters[collection_type]()

