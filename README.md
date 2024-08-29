# HerculesAI Contract Analysis

## Introduction
This repository contains the solution to the contract analysis task. The original task files are located under `data/`. The code is located under `src/`.

The solution is implemented in Python, using the [OpenAI API](https://platform.openai.com/docs/api-reference/chat/) and [FastHTML](https:/fastht.ml/) to display the results.

## Installation

First, you need to make sure you have [`uv`](https://docs.astral.sh/uv/) installed. If you don't have `uv` yet, but use `asdf`, you can run

```bash
asdf plugin add uv
asdf install
```

and `uv` will be installed for you. Otherwise, please follow the [`uv` installation instructions](https://docs.astral.sh/uv/getting-started/installation/). I decided to use `uv`, because even though it's fairly new, it's _so_ much better than the alternatives and I expect it to become the standard for Python development soon.

You also need to create a `.env` file to store the OpenAI API key. You can do this by running the following command:

```bash
echo "OPENAI_API_KEY=<YOUR_KEY_HERE>" > .env
```

With `uv` installed, you can now run the following to start the webserver

```bash
DEBUG=1 uv run src/herculesai_task/app.py
```

The first time you run it, it might take several seconds to start, because it will create a virtual environment and install the dependencies. Subsequent runs will be much faster.

## UX Walkthrough

Once you have the server running, open http://localhost:5001/ in your browser. You'll see a form to upload a `.docx` contract file. After you submit a file, the server will analyze the contract and display the resulting terms in a table below. The first time you do this, it might take a while depending on the contract size. Subsequent times will be fast, because the server caches the results (run `rm -r terms_cache` if you want to clear the cache).

Once you have the terms extracted, you can inspect them and then click on the "Validate task list" button to go to the next page. Here, you can again choose a file, this time we're expecting an `.xlsx` file containing the task list, as given in the example. After you submit the file, the server will display all the tasks and give you a button to validate each one.

I decided to only run the validation on-demand, individually, because running all the validations on every pageload seemed like an excessive use of the OpenAI API. Further, the "judgements" about the validity of the tasks are also cached. Run `rm -r terms_cache/judgements` if you want to clear just the judgements cache.

## Code Structure

The core logic of analyzing the contract and the tasks can be found in `src/herculesai_task/analysis.py`. In there, `text_to_terms` is responsible for extracting the terms from the contract (assignment #1), and `validate_task` validates a single task (assignment #2).

The entire webserver as well as frontend code is contained in the `app.py` file. The frontend is implemented using FastHTML, which is a Python library that allows you to write HTML in Python. I chose this because it's a very lightweight and quick way to create a web interface, but it' also really powerful. It's still pretty new and unconventional, but I think it's a great choice for small projects like this one.

There are two additional files: `common.py` defines some common classes used throughout the project and `terms_cache.py` is a simple cache implementation that stores the extracted terms and the task judgements.

## Extracting Terms

This was a relatively simple task to achieve when it comes to prompt engineering. After extracting the contents of the `.docx` file, the main difficulty was in how to deal with appendices/amendments. I explored adding a "chapter" field to `Task`, but in the end instructing ChatGPT how to create section numbers appropriately seemed to work well enough.

## Validating Tasks

This was more challenging, because I struggled with deciding how strict the validation should be.

## Bonus: Handling ambiguous cases

## Technical Choices & Trade-offs

I decided to use [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs/), which are fairly new. I think this worked well, but I've heard that using this feature can slightly decrease the model's "intelligence", so it might be worth testing alternatives (either no enforced structure, or the `instructor` library). The quality of the answers, however, seemed satisfactory, so I didn't dig further.

Using the disk for data storage is obviously not a scalable solution and a real database would be better, but I wanted to keep it simple. Migrating to SQLite would be very simple with FastHTML, something like Postgres would take a little more work, but is still completely doable.

### Relevancy checking

In the second assignment many tasks seem unrelated to the main purpose of the given contract (software development). Some are borderline, but I had to make a judgement call about how strict to be when it comes to e.g. training sessions. I chose to err on the side of strictness, which means rejecting most of the tasks given in the example. This seems reasonable to me, but is definitely a judgement call and in a real project I'd seek feedback from stakeholders to make the correct trade-offs.

### Tests & CI/CD

Arguably, I should've used more structured evals, but testing things by hand as I worked with the prompts was sufficient. If I wanted to maintain this project for longer or with other people, proper eval framework would be the first thing I'd add.

Unit tests are also important and I'd add `pytest` and a real test suite for any project that requires maintenance. I'd also add a CI/CD pipeline to run the tests automatically on every commit. I rarely do TDD and for this task I decided to submit before adding tests because I wanted to complete it ASAP. This might be a controversial trade-off, but I'm happy to discuss and defend it in this case.

## Future Improvements

- try to make it work reliably with `gpt-4o-mini` (I tried it and it was clearly wors with the current prompt)
- use a DB as data storage, instead of the disk
- add more tests
