import os
import json

from typing import Tuple
from common import Term, TermList

CACHE_DIR = "terms_cache"


def get_terms_data(fname: str) -> Tuple[list[str], TermList] | None:
    if os.path.exists(f"{CACHE_DIR}/{fname}.json"):
        with open(f"{CACHE_DIR}/{fname}.json") as f:
            data = json.load(f)
            terms = TermList(terms=[Term.model_validate(t) for t in data["terms"]])
            return data["paragraphs"], terms
    else:
        return None


def cache_result(fname: str, paragraphs: list[str], terms: TermList) -> str:
    path = f"{CACHE_DIR}/{fname}.json"
    with open(path, "w") as f:
        data = {
            "paragraphs": paragraphs,
            "terms": [t.model_dump() for t in terms.terms],
        }
        json.dump(data, f)
    return path
