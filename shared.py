import time
from dataclasses import dataclass, asdict
import json
import math
import os
import re
import sys
from typing import Optional

import requests
from tqdm import tqdm

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
SESSION_ID = os.getenv("SESSION_ID")

HEADERS = {
    "Cookie": f"_clozemaster_session={SESSION_ID}",
    "Time-Zone-Offset-Hours": "0",
    "User-Agent": USER_AGENT,
}


TOKENS_FILE = "tokens.json"


@dataclass
class Token:
    text: str
    lemma: str
    pos: str


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

    def get_tokens(self, collection_id: int, sentence_id: int) -> list["Token"]:
        if collection_id not in self.tokens:
            self.tokens[collection_id] = {}

        if sentence_id not in self.tokens[collection_id]:
            self.fetch_tokens(collection_id, sentence_id)

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

    def fetch_tokens(self, collection_id: int, sentence_id: int, backoff: int = 5):
        tokens_url = (
            "https://www.clozemaster.com/api/v1/lp/120/tokens?"
            f"collection_id={collection_id}"
            f"&tokenizeable_id={sentence_id}"
            "&tokenizeable_type=CollectionClozeSentence"
        )

        res = requests.get(url=tokens_url, headers=HEADERS)

        if res.status_code == 429:
            print(f"Rate limited fetching tokens, trying again in {backoff} seconds...")
            time.sleep(backoff)
            self.fetch_tokens(collection_id, sentence_id, backoff=backoff*2)
            return

        tokens = [
            Token(text=t["text"], lemma=t["lemma"]["text"], pos=t["posTag"]["label"])
            for t in res.json()["tokens"]
        ]

        self.tokens[collection_id][sentence_id] = tokens

        self.unsaved_sentences += 1
        if self.unsaved_sentences >= 100:
            self.write()


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

    def word(self):
        m = re.search("\{\{([^}]+)}}", self.text)

        if m is None:
            raise ValueError

        return m.group(1)

    def sentence(self):
        return self.text.replace("{{", "").replace("}}", "")

    def tokens(self) -> list[Token]:
        if self._tokens is None:
            self._tokens = TokenManager.get_tokens(self.collectionId, self.id)

        return self._tokens


@dataclass
class PageResponse:
    exercises: list[Exercise]
    per_page: int
    total: int


COURSE_IDS = {
    "ind-eng": "2a500c99-960c-4865-b7d3-af4ec1db60a9",
    "jpn-eng": "203e2a10-8fff-43ce-a25e-e1e2b0fe874b"
}


def get_page(course: str, page: int) -> PageResponse:
    if SESSION_ID is None:
        print("Please export a session key.")
        sys.exit(1)

    url = f"https://www.clozemaster.com/api/v1/lp/{course}/c/fluency-fast-track-{COURSE_IDS[course]}/ccs?page={page}"
    res = requests.get(
        url=url,
        headers=HEADERS,
    )

    if res.status_code != 200:
        raise RuntimeError(f"Request bounced: {res}")

    # print(json.dumps(res.json(), indent=2))
    content = res.json()
    # print(content["page"])
    per_page = content["perPage"]
    total = content["total"]

    exercises = [
        Exercise(**d)
        for d in content["collectionClozeSentences"]
    ]

    return PageResponse(exercises, per_page, total)


def get_all(course: str) -> list[Exercise]:
    res = get_page(course, 1)
    exercises = [*res.exercises]

    for page in tqdm(list(range(2, math.ceil(res.total / res.per_page) + 1))):
        exercises += get_page(course, page).exercises

    return exercises


def all_exercises(course: str, force_reload: bool = False) -> list[Exercise]:
    os.makedirs("exercises", exist_ok=True)

    course_file = f"exercises/{course}.json"

    if force_reload or not os.path.exists(course_file):
        exercises = get_all(course)

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


all_exercises('ind-eng')
