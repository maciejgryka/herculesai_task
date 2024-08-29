import os
import json

import docx

from fasthtml.common import *

from analysis import Term, text_to_terms


DEBUG = os.environ.get("DEBUG", "0") == "1"

hdrs = (HighlightJS(langs=['javascript']),)
app, rt = fast_app(debug=DEBUG, live=DEBUG, hdrs=hdrs)

terms_cache = {}
cache_dir = "terms_cache"
os.makedirs(cache_dir, exist_ok=True)


def docx_path_to_paragraphs(file_path) -> list[str]:
    return [
        paragraph.text.strip()
        for paragraph in docx.Document(file_path).paragraphs
        if paragraph.text
    ]


def code(text, wrap=True):
    wrap = "white-space: pre-wrap;" if wrap else ""
    return Pre(Code(text, style=f"{wrap}"))


@app.get("/")
def terms():
    return Titled("Terms",
        Form(
            Input(name="uf", placeholder="Enter text here", type="file"),
            Button("Submit", type="submit"),
            id="upload-form",
            post="upload",
            hx_swap="outerHTML"
        ))


def cache_result(fname: str, paragraphs: list[str], terms: list[Term]) -> str:
    path = f"{cache_dir}/{fname}.json"
    with open(path, "w") as f:
        data = {
            "paragraphs": paragraphs,
            "terms": [t.model_dump() for t in terms],
        }
        json.dump(data, f)
    return path


def get_fname(uf: UploadFile) -> str:
    return uf.filename or uf.file.name


@threaded
def process_and_cache(uf: UploadFile):
    fname = get_fname(uf)
    paragraphs = docx_path_to_paragraphs(uf.file)
    terms = text_to_terms(paragraphs)
    cache_result(fname, paragraphs, terms)


def term_table(terms: list[Term]):
    return Table(
        Tr(Th("Section"), Th("Name"), Th("Description")),
        *[Tr(Td(term.section), Td(term.name), Td(term.description)) for term in terms],
    )

def terms_or_spinner(fname):
    if os.path.exists(f"{cache_dir}/{fname}.json"):
        with open(f"{cache_dir}/{fname}.json") as f:
            data = json.load(f)
        paragraphs = "\n".join(data["paragraphs"])
        terms = [Term.model_validate(t) for t in data["terms"]]

        return Div(
            Div(
                H3("Original Contract"),
                Pre(paragraphs, style="white-space: pre-wrap; padding: 1rem;"),
                style="margin-top: 1rem; margin-bottom: 2rem; max-height: 300px; overflow: scroll;"
            ),
            Div(
                H3("Extracted Terms"),
                A("Download JSON", href=f"/{fname}.json"),
                term_table(terms)
            )
        )
    else:
        return Div("Analyzing...", id=f'terms-{fname}',
                   hx_post=f"/terms/{fname}",
                   hx_trigger='every 1s', hx_swap='outerHTML')


@app.post("/terms/{fname}")
def get(fname:str): return terms_or_spinner(fname)

# For the JSON files
@app.get("/{fname:path}.json")
def static(fname:str): return FileResponse(f'{cache_dir}/{fname}.json')

@app.post("/upload")
async def upload(uf:UploadFile):
    if not uf.filename.endswith(".docx"):
        return "Invalid file type, expected .docx"

    fname = get_fname(uf)
    process_and_cache(uf)
    return terms_or_spinner(fname)

serve()
