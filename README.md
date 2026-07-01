# School Agenda Automation

A Python automation script that replaces a fully manual weekly routine of 
retrieving and processing my daughter's school agenda from the student portal.

## What it does

**Workflow A** logs into the school portal, navigates to the weekly assignments 
report, saves it as a PDF, and opens it in Edge for review and printing.

**Workflow B** extracts the English course assignments (Grammar, Reading, 
Spelling, Oral, and Science) from the same report, translates them to Spanish 
using the DeepL API, and generates a formatted Word document grouped by weekday — 
with emphasized formatting for exams, tests, and homework.

Both workflows automatically determine the correct week to fetch based on the 
day the script is run: Monday through Thursday fetches the current week, Friday 
through Sunday fetches the following week.

## Stack

- [Playwright](https://playwright.dev/python/) — browser automation
- [DeepL API](https://www.deepl.com/pro-api) — English to Spanish translation
- [python-docx](https://python-docx.readthedocs.io/) — Word document generation
- [python-dotenv](https://pypi.org/project/python-dotenv/) — credential management

## Usage

```bash
python main.py        # run both workflows
python main.py --a    # weekly agenda PDF only
python main.py --b    # English supplement only
```

## Setup

1. Clone the repo and create a virtual environment
2. Run `pip install -r requirements.txt` and `playwright install chromium`
3. Copy `.env.example` to `.env` and fill in your school credentials and DeepL API key
4. Run `python main.py`

See `docs/business_rules.docx` for full documentation of all rules, 
constraints, and configuration options.