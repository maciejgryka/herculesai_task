# from enum import Enum
import json
from typing import Tuple

import docx
# from pydantic import BaseModel, Field
from fasthtml.xtend import is_
import pandas as pd
from openai import OpenAI
from fastcore.parallel import threaded

from common import TaskStatus, Term, TermList, Task, TaskRelevancy, TaskJudgement
from terms_cache import get_terms_data


def docx_path_to_paragraphs(file_path) -> list[str]:
    return [
        paragraph.text.strip()
        for paragraph in docx.Document(file_path).paragraphs
        if paragraph.text
    ]


def system_message() -> dict[str, str]:
    return  {
        "role": "system",
        "content": "You are a helpful and meticulous legal assistant.",
    }

def text_to_terms(text: list[str]) -> TermList:
    client = OpenAI()

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        response_format=TermList,
        messages=[
            system_message(),
            {
                "role": "user",
                "content": f"""
                You are provided with a contract text containing various terms and constraints. Extract all key terms from the document and structure them in a JSON format. Terms may be related to different sections and subsections of the document, which should be reflected in the JSON. If the contract contains multiple parts (e.g. main contract plus amendments/appendices) make sure to include the complete section reference in the section key (so the `section` key could be e.g. "2.2" or "amendment, 2.2"). It's possible that a section contains multiple terms, in which case they should be listed separately, but have the same `section` key.

                The document is given below as a list of lines extracted from a .docx file. Some sections might span multiple paragraphs, make sure to join them correctly.

                ```
                {text}
                ```
                """,
            },
        ],
    )

    term_list = completion.choices[0].message.parsed
    return term_list


def is_task_relevant(task: Task, terms: TermList) -> Tuple[bool, bool]:
    client = OpenAI()

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        response_format=TaskRelevancy,
        messages=[
            system_message(),
            {
                "role": "user",
                "content": f"""
                    Is the given task is relevant to the objective of the contract?

                    Terms extracted from the contract:
                    ```json
                    {terms.json()}
                    ```

                    The task is: "{task.description}"
                """
            }
        ]
    )
    relevancy = completion.choices[0].message.parsed
    if relevancy is None:
        return False, False
    return relevancy.relevant, relevancy.ambiguous


def validate_task(task: Task, terms: TermList) -> TaskJudgement:
    is_relevant, is_ambiguous = is_task_relevant(task, terms)
    if not is_relevant:
        strength = "seems" if is_ambiguous else "is"
        return TaskJudgement(
            task=task,
            related_terms=TermList(terms=[]),
            explanation=f"The task {strength} not relevant to the main objective of the contract.",
            ambiguous=is_ambiguous,
            task_status=TaskStatus.INVALID,
        )
    client = OpenAI()

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        response_format=TaskJudgement,
        messages=[
            system_message(),
            {
                "role": "user",
                "content": f"""
                Review the task below and the provided contract terms and determine whether it violates any of the terms extracted from the contract. If the task validity is completely clear, mark it accordingly, but if there's any doubt, mark it as ambiguous and guess which validity more likely.

                Terms extracted from the contract:
                ```json
                {terms.json()}
                ```

                The task is:
                ```json
                {task.json()}
                ```

                """
            }
        ]
    )
    judgement = completion.choices[0].message.parsed

    if not judgement:
        raise RuntimeError(f"Invalid response from OpenAI API: {completion}")

    return judgement


def read_tasks(fpath):
    """Read the lines from a CSV file."""
    return [
        Task(description=r["Task Description"], amount=r["Amount"])
        for _, r in pd.read_excel(fpath).iterrows()
    ]


if __name__ == "__main__":
    # file_path = "data/Contract + Amendment example v3 .docx"
    # text_content = docx_path_to_paragraphs(file_path)
    # terms = text_to_terms(text_content)
    # for term in terms:
    #     print(f"{term.section}: {term.name} - {term.description}\n---")

    cached_data = get_terms_data("Contract + Amendment example v3 .docx")
    if not cached_data:
        raise RuntimeError("No cached data found")

    _, terms = cached_data
    tasks = read_tasks("data/Task example v3.xlsx")
    for task in tasks[:5]:
        print(validate_task(task, terms))
        print("---")
