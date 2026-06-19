"""
Workflow A — Weekly agenda print.
Logs in, finds this week's report, saves it as PDF, and prints it.
"""

import os
import subprocess
import platform
from playwright.sync_api import sync_playwright
from utils import get_credentials, find_weekly_report_url, login

OUTPUT_DIR = "output"
PDF_FILENAME = "weekly_agenda.pdf"


def save_report_as_pdf(page, url: str, output_path: str) -> None:
    """Opens the report and saves it as a PDF."""
    print(f"  → Opening report: {url}")
    page.goto(url)
    page.wait_for_load_state("networkidle")

    page.pdf(
        path=output_path,
        print_background=True,
        format="Letter",
    )
    print(f"  ✓ Saved PDF → {output_path}")


def print_pdf(pdf_path: str) -> None:
    abs_path = os.path.abspath(pdf_path)
    print(f"  → Opening in Edge for review...")

    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]

    edge = next((p for p in edge_paths if os.path.exists(p)), None)
    if not edge:
        raise FileNotFoundError(
            "Edge not found — update the path in print_pdf()")

    subprocess.Popen([edge, abs_path])
    print("  ✓ Opened in Edge")


def run_workflow_a() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, PDF_FILENAME)
    user, password = get_credentials()

    with sync_playwright() as p:
        # set True once confirmed working
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            login(page, user, password)
            report_url = find_weekly_report_url(page)

            if not report_url:
                print("  ✗ Workflow A aborted: no report URL found")
                return

            save_report_as_pdf(page, report_url, output_path)
            print_pdf(output_path)

        finally:
            browser.close()
