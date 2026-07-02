# Business Rules & Technical Reference

**School Agenda Automation** · Version 1.0 · June 2026

---

## Table of Contents

1. [Overview](#1-overview)
2. [Environment & Stack](#2-environment--stack)
3. [Credentials & Configuration](#3-credentials--configuration)
4. [Week Range Selection Logic](#4-week-range-selection-logic)
5. [Portal Structure & Navigation](#5-portal-structure--navigation)
6. [Report URL Construction](#6-report-url-construction)
7. [Workflow A — Weekly Agenda PDF](#7-workflow-a--weekly-agenda-pdf)
8. [Workflow B — English Supplement](#8-workflow-b--english-supplement)
9. [Command-Line Usage](#9-command-line-usage)
10. [Consumer Readiness Checklist](#10-consumer-readiness-checklist)
11. [Known Constraints & Assumptions](#11-known-constraints--assumptions)

---

## 1. Overview

This project automates the weekly retrieval and processing of a student's school agenda from the Colegio Bilingüe La Academia student portal (`cbla.school-access.com`). It eliminates a fully manual weekly routine that previously involved logging in, navigating to the report, printing, copying English course content, translating it, formatting a document, and printing again.

The automation is implemented as a Python script using Playwright for browser automation and DeepL for translation. It produces two outputs: a PDF of the full weekly agenda, and a formatted Word document containing only the English course assignments translated to Spanish.

> **Design principle:** This project intentionally does not use an AI agent. The task is fully deterministic — no judgment or reasoning is required at runtime. Browser automation and a translation API are the correct tools, chosen by applying the delegation principle from Anthropic's Claude Code 101 course.

---

## 2. Environment & Stack

| Item                | Value                                          |
| ------------------- | ---------------------------------------------- |
| Operating system    | Windows 10/11                                  |
| Python version      | 3.12.10                                        |
| Editor              | Visual Studio Code                             |
| Browser automation  | Playwright (Chromium)                          |
| Translation API     | DeepL API Free tier                            |
| Document generation | python-docx                                    |
| Virtual environment | `venv/` inside project root                    |
| Project root        | `C:\Projects\Python_Learning\school-agenda`    |
| Output directory    | `output\` (created automatically on first run) |

### 2.1 Project File Structure

```
school-agenda/
├── docs/
│   ├── BUSINESS_RULES.md       ← this file
│   └── business_rules.docx     ← Word version
├── output/
│   ├── weekly_agenda.pdf
│   └── english_supplement_es.docx
├── venv/
├── main.py                     ← entry point, argument parsing
├── utils.py                    ← credentials, date logic, login, URL construction
├── workflow_a.py               ← agenda PDF retrieval
├── workflow_b.py               ← English extraction, translation, document generation
├── requirements.txt
├── .env                        ← credentials (never committed)
└── .env.example                ← template
```

---

## 3. Credentials & Configuration

All sensitive values are stored in a `.env` file and loaded at runtime using `python-dotenv`. They are never hardcoded in source files.

| Variable        | Description                                      |
| --------------- | ------------------------------------------------ |
| `SCHOOL_USER`   | Student portal username (fixed, does not change) |
| `SCHOOL_PASS`   | Student portal password (fixed, does not change) |
| `DEEPL_API_KEY` | DeepL API Free tier key for Spanish translation  |

> If any required environment variable is missing, the script raises an `EnvironmentError` immediately with a descriptive message before attempting any browser interaction.

---

## 4. Week Range Selection Logic

The script automatically determines which school week to fetch based on the day of execution. The school agenda covers Monday through Friday.

| Day of execution      | Behavior               |
| --------------------- | ---------------------- |
| Monday (weekday 0)    | Fetch **current** week |
| Tuesday (weekday 1)   | Fetch **current** week |
| Wednesday (weekday 2) | Fetch **current** week |
| Thursday (weekday 3)  | Fetch **current** week |
| Friday (weekday 4)    | Fetch **next** week    |
| Saturday (weekday 5)  | Fetch **next** week    |
| Sunday (weekday 6)    | Fetch **next** week    |

**Implementation:** if `weekday >= 4`, calculate days until next Monday (`7 − weekday`) and add to today's date. Otherwise subtract `weekday` from today to get the current Monday. Friday is always `Monday + 4 days`.

> **Example:** running on Saturday June 27, 2026 → weekday = 5 → days until Monday = 2 → fetches the June 29 – July 3 agenda.

---

## 5. Portal Structure & Navigation

### 5.1 Frame Architecture

The portal uses a nested frame structure:

```
https://cbla.school-access.com/Schoolaccess.asp          ← outer shell (no form elements)
└── iframe: ./schoolaccess_internet/
    ├── frame name="Menu"       → Menu_principal.asp
    └── frame name="Principal"  → Login_inicial.asp  ← login form lives here
```

The script navigates directly to `https://cbla.school-access.com/schoolaccess_internet/` and targets the inner frame using `page.frame(name="Principal")` before interacting with form fields.

> Targeting the outer shell URL causes timeouts because the form elements are not in the main frame.

### 5.2 Login Form Selectors

| Element        | Selector                                 |
| -------------- | ---------------------------------------- |
| Username field | `input[name='usuario']`                  |
| Password field | `input[name='contrasena']`               |
| Submit button  | `input[name='Button_DoLogin']`           |
| Form action    | `login_inicial.asp?ccsForm=Login` (POST) |

### 5.3 Navigation to Weekly Report

After login, the script clicks the following links inside the `Principal` frame in order:

1. `"Asignaciones"` — main navigation link
2. `"VER ASIGNACIONES SEMANALES"` — sub-navigation link

> The portal is in Spanish. Navigation text must match exactly as shown.

---

## 6. Report URL Construction

The report URL is constructed directly from the computed week range — no link-hunting or text matching is needed.

**Base URL:**

```
http://cbla.school-access.com/schoolaccess_reports/std/std_rep_asignaciones_semanal.asp
```

**Query parameters:**

| Parameter      | Description                                                       |
| -------------- | ----------------------------------------------------------------- |
| `mes`          | Month number of Monday — no leading zero (e.g. `6`)               |
| `anio`         | 4-digit year of Monday (e.g. `2026`)                              |
| `codigo_grupo` | Fixed value: `431` (student's class group code)                   |
| `fecha_inicio` | Monday in `M/D/YYYY` format — no leading zeros (e.g. `6/29/2026`) |
| `fecha_fin`    | Friday in `M/D/YYYY` format — no leading zeros (e.g. `7/3/2026`)  |

**Example URL:**

```
http://cbla.school-access.com/schoolaccess_reports/std/std_rep_asignaciones_semanal.asp
  ?mes=6&anio=2026&codigo_grupo=431&fecha_inicio=6%2F29%2F2026&fecha_fin=7%2F3%2F2026
```

> Windows date formatting uses `%#m` and `%#d` (not `%-m` / `%-d` which are Linux-only) to suppress leading zeros in `strftime` calls.

---

## 7. Workflow A — Weekly Agenda PDF

### 7.1 Purpose

Automates retrieval of the full weekly agenda and opens it in Microsoft Edge for manual review and printing.

### 7.2 Steps

1. Load credentials from `.env`
2. Launch Chromium (`headless=True` in production)
3. Navigate to `https://cbla.school-access.com/schoolaccess_internet/`
4. Target the `Principal` frame, wait for the username field
5. Fill username, password, click submit, wait for `networkidle`
6. Construct the report URL from the computed week range
7. Navigate directly to the report URL
8. Save the page as PDF (`print_background=True`, `format=Letter`)
9. Open the PDF in Microsoft Edge using `subprocess.Popen` (non-blocking)
10. Close the browser

### 7.3 Output

| Item      | Value                                      |
| --------- | ------------------------------------------ |
| File      | `output\weekly_agenda.pdf`                 |
| Format    | US Letter, color, print background enabled |
| Opened in | Microsoft Edge for manual review           |

> The script does not print automatically. The user reviews the PDF in Edge and decides whether to print, preserving manual control over paper and printer settings.

---

## 8. Workflow B — English Supplement

### 8.1 Purpose

Extracts English course assignments from the weekly report, translates them to Spanish, and generates a formatted Word document grouped by weekday.

### 8.2 English Subjects Extracted

The following subjects are identified by their uppercase English names in the report:

- `GRAMMAR`
- `READING`
- `SPELLING`
- `ORAL`
- `SCIENCE`

> All other subjects appear in Spanish (e.g. `MATEMÁTICAS`, `ESPAÑOL`) and are ignored.

### 8.3 Report HTML Structure

```
tr.GroupCaption   ← day header, e.g. "lunes, junio 08, 2026"
tr.Row
  td[0]           ← subject name (e.g. GRAMMAR)
  td[1]           ← Asignación Tipo (e.g. Reminder, Exam, Homework)
  td[2]           ← full assignment description
tr.Row
  ...
tr.GroupCaption   ← next day header
...
```

### 8.4 Steps

1. Load credentials and DeepL API key from `.env`
2. Launch Chromium, log in (same as Workflow A)
3. Navigate to the report URL
4. Iterate all `tr.Row` and `tr.GroupCaption` elements, tracking the current day
5. For each English subject row: capture day, `Asignación Tipo`, and description
6. Translate each description to Spanish (`ES`) via DeepL — `Asignación Tipo` is passed through unchanged
7. Reorganize entries by day using the Spanish weekday sort order
8. Build a formatted `.docx` document
9. Open the document in Microsoft Edge for review
10. Close the browser

### 8.5 Day Sort Order

Days are sorted using a fixed Spanish weekday list:

| Index | Day       |
| ----- | --------- |
| 0     | lunes     |
| 1     | martes    |
| 2     | miércoles |
| 3     | jueves    |
| 4     | viernes   |

> The sort matches on whether the day name appears anywhere in the `GroupCaption` text, so full strings like `"lunes, junio 08, 2026"` are matched correctly.

### 8.6 Document Format

```
Title: "Tareas de Inglés — Semana Actual"  (centered, H1)

── [day divider] ──────────────────────────────
Lunes, junio 08, 2026  (H2)

  Grammar  [Reminder]
  Description text...

  Spelling  [Reminder]
  Description text...

── [day divider] ──────────────────────────────
Martes, junio 09, 2026  (H2)
  ...
```

### 8.7 Assignment Type Emphasis Rules

Assignment types are matched case-insensitively. Emphasized types render in **red bold**.

| Type                                  | Rendering                     |
| ------------------------------------- | ----------------------------- |
| `exam` / `examen`                     | 🔴 Red bold — high priority   |
| `homework` / `tarea`                  | 🔴 Red bold — take-home work  |
| `practice` / `práctica` / `prácticas` | 🔴 Red bold — graded practice |
| `test` / `quiz`                       | 🔴 Red bold — assessed work   |
| `reminder` / `recordatorio`           | Normal — gray italic brackets |

> To add or remove emphasis types, update the `EMPHASIS_TIPOS` set in `workflow_b.py`. All values must be lowercase strings.

### 8.8 Output

| Item      | Value                                      |
| --------- | ------------------------------------------ |
| File      | `output\english_supplement_es.docx`        |
| Language  | Spanish (ES) — all descriptions translated |
| Opened in | Microsoft Edge for manual review           |

---

## 9. Command-Line Usage

```bash
python main.py        # run both workflows
python main.py --a    # Workflow A only (agenda PDF)
python main.py --b    # Workflow B only (English supplement)
```

---

## 10. Consumer Readiness Checklist

| Item                                               | Status     |
| -------------------------------------------------- | ---------- |
| `headless=True` in both workflows                  | ✅ Done    |
| Error handling + desktop notifications             | ⏳ Pending |
| Logging to `agenda.log`                            | ⏳ Pending |
| Graceful handling when report is not yet published | ⏳ Pending |
| Windows Task Scheduler setup                       | ⏳ Pending |
| Dependency pinning (`pip freeze`)                  | ⏳ Pending |

### Recommended Task Scheduler Settings

| Setting   | Value                                                               |
| --------- | ------------------------------------------------------------------- |
| Trigger   | Weekly — every Friday at 8:00 PM                                    |
| Program   | `C:\Projects\Python_Learning\school-agenda\venv\Scripts\python.exe` |
| Arguments | `main.py`                                                           |
| Start in  | `C:\Projects\Python_Learning\school-agenda`                         |

> Running on Friday evening ensures the script applies the Friday → next week rule and fetches the upcoming week's agenda, ready for weekend review.

---

## 11. Known Constraints & Assumptions

- `codigo_grupo=431` is hardcoded. If the student changes class or year, this must be updated in `utils.py`.
- The portal must be reachable at runtime. No offline fallback exists.
- DeepL API Free tier allows 500,000 characters/month. Typical weekly usage is ~2,000–3,000 characters (~1% of the limit).
- Output files are opened in Microsoft Edge. Edge must be installed at one of the two standard paths checked in the code.
- Portal navigation text (`"Asignaciones"`, `"VER ASIGNACIONES SEMANALES"`) must remain unchanged. If the portal is updated, selectors may need revision.
- Windows-specific `strftime` formatting (`%#m`, `%#d`) is used to suppress leading zeros. This must be changed to `%-m`, `%-d` on Linux or macOS.
