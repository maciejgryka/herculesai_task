import json

import docx
from openai import OpenAI


def docx_path_to_paragraphs(file_path) -> list[str]:
    return [
        paragraph.text.strip()
        for paragraph in docx.Document(file_path).paragraphs
        if paragraph.text
    ]


def text_to_terms(text: list[str]) -> list[dict]:
    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a helpful and meticulous legal assistant."},
            {"role": "user", "content": f"""
                You are provided with a contract text containing various terms and constraints. Extract all key terms from the document and structure them in a eJSON format. Terms may be related to different sections and subsections of the document, which should be reflected in the JSON. If the contract contains multiple sectioms (e.g. main contract and then some amendments or appendices) make sure to include the complete section reference in the section key. It's possible that a section contains multiple terms, in which case they should be listed separately. Terms may be related to different sections and subsections of the contract.

                ```json
                {{
                    "document_description": "Software Development Agreement",
                    "parties": ["Company A", "Company B"],
                    "terms": [
                        {{
                            "section": "1.1",
                            "name": "type of services",
                            "description": "the contractor shall provide the client with a software development services",
                        }},
                        {{
                            "section": "1.1",
                            "name": "involvement of third parties",
                            "description": "the contractor may involve third parties in the performance of the services",
                        }},
                        {{
                            "section": "amendment, 3.2",
                            "name": "payment terms",
                            "description": "the client shall pay the contractor a fee of $1000",
                        }},
                    ]
                }}
                ```

                The document is given below as a list of lines extracted from a .docx file. Some sections might span multiple paragraphs, make sure to join them correctly.


                ```
                {text}
                ```
                """
            }
        ]
    )

    data = json.loads(completion.choices[0].message.content)
    return data["terms"]


if __name__ == '__main__':
    file_path = 'data/Contract + Amendment example v3 .docx'
    text_content = docx_path_to_paragraphs(file_path)
    terms = text_to_terms(text_content)
    for term in terms:
        print(f"{term['section']}: {term['name']} - {term['description']}\n---")
