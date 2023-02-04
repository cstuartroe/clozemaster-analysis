from dataclasses import dataclass
import math
import os
import time

from bs4 import BeautifulSoup as bs
import requests
from tqdm import tqdm

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
SESSION_ID = os.getenv("SESSION_ID")

HEADERS = {
    "Cookie": f"_clozemaster_session={SESSION_ID}",
    "Time-Zone-Offset-Hours": "0",
    "User-Agent": USER_AGENT,
}


def fetch_tokens(collection_id: int, sentence_id: int, backoff: int = 5):
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
        fetch_tokens(collection_id, sentence_id, backoff=backoff * 2)
        return

    return res.json()["tokens"]


@dataclass
class PageResponse:
    exercises: list[dict]
    per_page: int
    total: int


COURSE_IDS = {
    "ind-eng": "2a500c99-960c-4865-b7d3-af4ec1db60a9",
    "jpn-eng": "203e2a10-8fff-43ce-a25e-e1e2b0fe874b"
}


def get_page(course: str, page: int) -> PageResponse:
    if SESSION_ID is None:
        raise ValueError("Please export a session key.")

    url = f"https://www.clozemaster.com/api/v1/lp/{course}/c/fluency-fast-track-{COURSE_IDS[course]}/ccs?page={page}"
    res = requests.get(
        url=url,
        headers=HEADERS,
    )

    if res.status_code != 200:
        raise RuntimeError(f"Request bounced: {res}")

    content = res.json()
    per_page = content["perPage"]
    total = content["total"]

    return PageResponse(content["collectionClozeSentences"], per_page, total)


def get_all_exercises(course: str) -> list[dict]:
    res = get_page(course, 1)
    exercises = [*res.exercises]

    for page in tqdm(list(range(2, math.ceil(res.total / res.per_page) + 1))):
        exercises += get_page(course, page).exercises

    return exercises


def get_wiktionary_section(word: str, language: str):
    res = requests.get(f"https://en.wiktionary.org/wiki/{word}")
    soup = bs(res.text, "html.parser")

    out = []

    in_language = False
    for child in soup.find("div", {"class": "mw-parser-output"}).children:
        if child.name == "h2":
            if in_language:
                return out
            elif child.span.text == language:
                in_language = True

        if in_language:
            out.append(child)

    return out
