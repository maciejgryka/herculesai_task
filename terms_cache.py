import os
import json
import hashlib

from typing import Tuple
from common import Term, TermList, Task, TaskJudgement

CACHE_DIR = "terms_cache"
CACHE_DIR_JUDGEMENT = f"{CACHE_DIR}/judgements"

os.makedirs(CACHE_DIR_JUDGEMENT, exist_ok=True)

def get_terms_data(fname: str) -> Tuple[list[str], TermList] | None:
    if os.path.exists(f"{CACHE_DIR}/{fname}.json"):
        with open(f"{CACHE_DIR}/{fname}.json") as f:
            data = json.load(f)
            terms = TermList(terms=[Term.model_validate(t) for t in data["terms"]])
            return data["paragraphs"], terms
    else:
        return None


def cache_terms(fname: str, paragraphs: list[str], terms: TermList) -> str:
    path = f"{CACHE_DIR}/{fname}.json"
    with open(path, "w") as f:
        data = {
            "paragraphs": paragraphs,
            "terms": [t.model_dump() for t in terms.terms],
        }
        json.dump(data, f)
    return path


def task_judgement_cache_key(task: str, terms: TermList) -> str:
    content = f"{task}\n---\n{terms.model_dump()}"
    return hashlib.sha256(content.encode()).hexdigest()


def cache_judgement(task: Task, terms: TermList, judgement: TaskJudgement) -> str:
    key = task_judgement_cache_key(task.description, terms)
    path = f"{CACHE_DIR}/{key}.json"
    with open(path, "w") as f:
        json.dump(judgement.model_dump(), f)
    return path
