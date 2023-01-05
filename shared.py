from dataclasses import dataclass, asdict
import json
import math
import os
import re
import sys

import requests
from tqdm import tqdm

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
SESSION_ID = os.getenv("SESSION_ID")


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

    def word(self):
        m = re.search("\{\{([^}]+)}}", self.text)

        if m is None:
            raise ValueError

        return m.group(1)

    def sentence(self):
        return self.text.replace("{{", "").replace("}}", "")


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
        headers={
            "Cookie": f"_clozemaster_session={SESSION_ID}",
            "Time-Zone-Offset-Hours": "0",
            "User-Agent": USER_AGENT,
        }
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
