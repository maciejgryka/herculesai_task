import os
import json
import urllib

from fastcore.parallel import threaded
from fasthtml.common import *

from common import Task, TaskJudgement, Term, TermList
from analysis import docx_path_to_paragraphs, text_to_terms, read_tasks, validate_task
from terms_cache import CACHE_DIR, CACHE_DIR_JUDGEMENT, cache_terms, get_terms_data, cache_judgement, get_cached_judgement, task_judgement_cache_key


DEBUG = os.environ.get("DEBUG", "0") == "1"

hdrs = (HighlightJS(langs=["javascript"]),)
app, rt = fast_app(debug=DEBUG, live=DEBUG, hdrs=hdrs)


def code(text, wrap=True):
    wrap = "white-space: pre-wrap;" if wrap else ""
    return Pre(Code(text, style=f"{wrap}"))


@app.get("/")
def terms(r: Request):
    content = ""
    if "fname" in r.query_params:
        fname = r.query_params["fname"]
        if get_terms_data(fname) is None:
            content = "No data found for this file."
        else:
            content = terms_or_spinner(r.query_params["fname"])
    else:
        content = Form(
            Input(name="uf", placeholder="Choose contract file (.docx)", type="file"),
            Button("Submit", type="submit"),
            id="upload-form",
            post="upload",
            hx_swap="outerHTML",
        )
    return Titled("Terms", content,)


def get_fname(uf: UploadFile) -> str:
    return uf.filename or uf.file.name


@threaded
def process_and_cache(uf: UploadFile):
    fname = get_fname(uf)
    paragraphs = docx_path_to_paragraphs(uf.file)
    terms = text_to_terms(paragraphs)
    cache_terms(fname, paragraphs, terms)


def term_table(terms: TermList):
    return Table(
        Tr(Th("Section"), Th("Name"), Th("Description")),
        *[
            Tr(
                Td(term.section),
                Td(term.name),
                Td(term.description)
            )
            for term in terms.terms
        ],
    )


def terms_or_spinner(fname):
    terms_data = get_terms_data(fname)
    if terms_data is None:
        return Div(
            "Analyzing...",
            id=f"terms-{fname}",
            hx_post=f"/terms/{fname}",
            hx_trigger="every 1s",
            hx_swap="outerHTML",
        )

    paragraphs, terms = terms_data
    paragraphs = "\n".join(paragraphs)

    return Div(
        Div(
            H3("Original Contract"),
            Pre(paragraphs, style="white-space: pre-wrap; padding: 1rem;"),
            style="margin-top: 1rem; margin-bottom: 2rem; max-height: 300px; overflow: scroll;",
        ),
        Div(
            H3("Extracted Terms"),
            A("Download JSON", href=f"/{fname}.json"),
            A(Button("Validate task list"), href=f"/validate/{fname}", style="float: right"),
            term_table(terms),
        ),
    )


@app.post("/terms/{fname}")
def get(fname: str):
    return terms_or_spinner(fname)


# For the JSON files
@app.get("/{fname:path}.json")
def static(fname: str):
    return FileResponse(f"{CACHE_DIR}/{fname}.json")


@app.post("/upload")
async def upload(uf: UploadFile):
    if not uf.filename.endswith(".docx"):
        return "Invalid file type, expected .docx"

    fname = get_fname(uf)
    process_and_cache(uf)
    return terms_or_spinner(fname)


@app.get("/validate/{terms_fname}")
def validate(terms_fname: str):
    return Titled("Tasks", Form(
        Input(name="uf", placeholder="Choose a task file (.xslx)", type="file"),
        Hidden(terms_fname),
        Button("Submit", type="submit"),
        id="upload-form",
        hx_post=f"/upload_tasks/{terms_fname}",
        hx_swap="outerHTML",
    ))


def task_table(terms_fname: str, tasks: list[Task]):
    def validate_button(fname, task):
        return Button("Validate", hx_post=f"/validate/{fname}/{task.description}/{task.amount}", hx_swap="outerHTML")

    return Table(
        Tr(Th("Description"), Th("Amount"), Th("Status")),
        *[
            Tr(
                Td(task.description),
                Td(task.amount),
                Td(validate_button(terms_fname, task)),
            )
            for task in tasks
        ],
    )

def display_judgement(task_hash:str):
    judgement = get_cached_judgement(task_hash)
    if judgement is not None:
        print("cached judgement found")
        ambiguity = ""
        if judgement.ambiguous:
            ambiguity = P("Ambiguous, please verify", style="color: orange;")
        return Div(
            H5("Valid" if judgement.is_valid else "Invalid"),
            ambiguity,
            P(judgement.explanation)
        )
    else:
        print("cached judgement not found")
        fname = f"{CACHE_DIR}/{task_hash}.json"
        return Div("Analyzing...", id=f'jgd-{task_hash}',
                   hx_post=f"/judgement/{task_hash}",
                   hx_trigger='every 1s', hx_swap='outerHTML')


@app.post("/judgement/{task_hash}")
def get(task_hash: str): return display_judgement(task_hash)


@threaded
def generate_and_save_judgement(task: Task, terms: TermList):
    task_hash = task_judgement_cache_key(task.description, terms)
    if get_cached_judgement(task_hash) is not None:
        return
    judgement = validate_task(task, terms)
    cache_judgement(task, terms, judgement)


@app.post("/validate/{terms_fname}/{task_description}/{task_amount}")
def validate_single_task(terms_fname: str, task_description: str, task_amount: str):
    task_description = urllib.parse.unquote(task_description)
    task_amount = urllib.parse.unquote(task_amount)

    term_data = get_terms_data(terms_fname)
    if term_data is None:
        return "No data found for this file."

    _, terms = term_data
    task = Task(description=task_description, amount=task_amount)
    task_hash = task_judgement_cache_key(task.description, terms)
    judgement = get_cached_judgement(task_hash)
    generate_and_save_judgement(task, terms)
    # judgement = validate_task(task, terms)
    # cache_judgement(task, terms, judgement)
    return display_judgement(task_hash)


@app.post("/upload_tasks/{terms_fname}")
async def upload_tasks(terms_fname: str, uf: UploadFile):
    if not uf.filename.endswith(".xlsx"):
        return "Invalid file type, expected .xlsx"

    fname = get_fname(uf)
    tasks = read_tasks(uf.file)
    return task_table(terms_fname, tasks)


serve()
