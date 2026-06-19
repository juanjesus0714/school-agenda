"""
Shared utilities: credentials loading, date helpers, browser setup.
"""

import os
from datetime import date, timedelta
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page
from urllib.parse import urlencode

load_dotenv()

# ── Credentials ────────────────────────────────────────────────────────────────


def get_credentials() -> tuple[str, str]:
    user = os.getenv("SCHOOL_USER")
    password = os.getenv("SCHOOL_PASS")
    if not user or not password:
        raise EnvironmentError(
            "SCHOOL_USER and SCHOOL_PASS must be set in .env")
    return user, password


def get_deepl_key() -> str:
    key = os.getenv("DEEPL_API_KEY")
    if not key:
        raise EnvironmentError("DEEPL_API_KEY must be set in .env")
    return key

# ── Date helpers ───────────────────────────────────────────────────────────────


def current_week_range() -> tuple[date, date]:
    """Returns (Monday, Friday) of the current week."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    return monday, friday


def format_week_label(monday: date, friday: date) -> str:
    """Returns a human-readable label like 'June 08 through June 12'."""
    return f"{monday.strftime('%B %d')} through {friday.strftime('%B %d')}"

# ── Browser helpers ────────────────────────────────────────────────────────────


SCHOOL_URL = "https://cbla.school-access.com/schoolaccess_internet/"


def login(page: Page, user: str, password: str) -> None:
    print(f"  → Opening {SCHOOL_URL}")
    page.goto(SCHOOL_URL)

    # The login form lives inside the 'Principal' frame
    frame = page.frame(name="Principal")
    frame.wait_for_selector("input[name='usuario']")

    frame.fill("input[name='usuario']", user)
    frame.fill("input[name='contrasena']", password)
    frame.click("input[name='Button_DoLogin']")
    page.wait_for_load_state("networkidle")
    print("  ✓ Logged in")


REPORT_BASE_URL = (
    "http://cbla.school-access.com/schoolaccess_reports/std/"
    "std_rep_asignaciones_semanal.asp"
)


def find_weekly_report_url(page: Page) -> str:
    """
    Builds the weekly report URL directly from the current week's dates.
    No link-hunting needed — the portal uses predictable query parameters.
    """
    monday, friday = current_week_range()

    params = {
        "mes":          monday.month,
        "anio":         monday.year,
        "codigo_grupo": "431",           # ← your child's group code, stays fixed
        "fecha_inicio": monday.strftime("%#m/%#d/%Y"),  # e.g. 6/8/2026
        "fecha_fin":    friday.strftime("%#m/%#d/%Y"),  # e.g. 6/12/2026
    }

    url = REPORT_BASE_URL + "?" + urlencode(params)
    print(f"  ✓ Report URL: {url}")
    return url
