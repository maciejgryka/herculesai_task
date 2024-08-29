import docx
from openai import OpenAI
from pydantic import BaseModel


class Term(BaseModel):
    section: str
    name: str
    description: str


class TermList(BaseModel):
    terms: list[Term]


def docx_path_to_paragraphs(file_path) -> list[str]:
    return [
        paragraph.text.strip()
        for paragraph in docx.Document(file_path).paragraphs
        if paragraph.text
    ]


def text_to_terms(text: list[str]) -> list[Term]:
    client = OpenAI()

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        response_format=TermList,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful and meticulous legal assistant.",
            },
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
    return term_list.terms


if __name__ == "__main__":
    file_path = "data/Contract + Amendment example v3 .docx"
    text_content = docx_path_to_paragraphs(file_path)
    terms = text_to_terms(text_content)
    for term in terms:
        print(f"{term.section}: {term.name} - {term.description}\n---")

    # cache the terms in a JSON file
    # for each line item in the CSV file
    # find relevant terms and decide whether the item violates them
