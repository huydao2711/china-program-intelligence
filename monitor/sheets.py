"""
monitor/sheets.py — Google Sheets integration via gspread.
Replaces Sheets.gs. Uses a Service Account for auth.

Env vars needed:
  GOOGLE_SERVICE_ACCOUNT_JSON  — full JSON content of service account key
  GOOGLE_SHEET_NAME            — sheet name (default: "WeChat Monitor Log")

If GOOGLE_SERVICE_ACCOUNT_JSON is not set, all functions are no-ops and
the system falls back to email-only output.
"""

import os, json
from datetime import datetime

from .config import SHEET_HEADERS, PROGRAM_DEADLINES, MONITOR_CONFIG

_gc   = None  # gspread client
_sheet = None  # Log sheet handle
_fp_sheet = None  # Fingerprints sheet handle


def _client():
    global _gc
    if _gc:
        return _gc
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not sa_json:
        return None
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        info = json.loads(sa_json)
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        _gc = gspread.authorize(creds)
        return _gc
    except Exception as e:
        print(f"[Sheets] Auth error: {e}")
        return None


def get_or_create_sheet():
    """Return the Log sheet handle, creating spreadsheet/sheet if needed."""
    global _sheet
    if _sheet:
        return _sheet

    gc = _client()
    if not gc:
        print("[Sheets] No service account — Sheets disabled")
        return None

    sheet_name = os.environ.get("GOOGLE_SHEET_NAME", MONITOR_CONFIG["SHEET_NAME"])
    try:
        try:
            ss = gc.open(sheet_name)
        except Exception:
            ss = gc.create(sheet_name)
            print(f"[Sheets] Created spreadsheet: {sheet_name}")

        try:
            ws = ss.worksheet("Log")
        except Exception:
            ws = ss.add_worksheet("Log", rows=5000, cols=len(SHEET_HEADERS))
            ws.append_row(SHEET_HEADERS)
            ws.format("1", {"backgroundColor": {"red": 0.1, "green": 0.14, "blue": 0.49},
                            "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True}})
            print("[Sheets] Initialized Log sheet")

        _sheet = ws
        return ws
    except Exception as e:
        print(f"[Sheets] get_or_create error: {e}")
        return None


def get_seen_ids(sheet) -> set:
    """Read all existing Article IDs (col I) and URLs (col H) from sheet."""
    if not sheet:
        return set()
    try:
        all_vals = sheet.get_all_values()
        seen = set()
        for row in all_vals[1:]:  # skip header
            if len(row) > 8 and row[8]:
                seen.add(row[8])   # col I: Item ID
            if len(row) > 7 and row[7]:
                seen.add(row[7])   # col H: URL
        return seen
    except Exception as e:
        print(f"[Sheets] get_seen_ids error: {e}")
        return set()


def get_fingerprints(sheet) -> dict:
    """Read fingerprints from 'State' tab: {source_id: fingerprint}."""
    if not sheet:
        return {}
    try:
        ss = sheet.spreadsheet
        try:
            fp_ws = ss.worksheet("State")
        except Exception:
            fp_ws = ss.add_worksheet("State", rows=100, cols=3)
            fp_ws.append_row(["Source ID", "Fingerprint", "Last Checked"])
            return {}
        rows = fp_ws.get_all_values()
        return {row[0]: row[1] for row in rows[1:] if len(row) >= 2 and row[0]}
    except Exception as e:
        print(f"[Sheets] get_fingerprints error: {e}")
        return {}


def save_fingerprints(sheet, fp_store: dict):
    """Write fingerprint store back to 'State' tab."""
    if not sheet or not fp_store:
        return
    try:
        ss = sheet.spreadsheet
        try:
            fp_ws = ss.worksheet("State")
        except Exception:
            fp_ws = ss.add_worksheet("State", rows=100, cols=3)
        fp_ws.clear()
        fp_ws.append_row(["Source ID", "Fingerprint", "Last Checked"])
        now = datetime.now().isoformat()
        for src_id, fp in fp_store.items():
            fp_ws.append_row([src_id, fp, now])
    except Exception as e:
        print(f"[Sheets] save_fingerprints error: {e}")


def _build_row(article: dict) -> list:
    is_urgent = article.get("hasDeadline") or any(
        kw.lower() in " ".join(article.get("keywordsFound", [])).lower()
        for kw in MONITOR_CONFIG["URGENT_KEYWORDS"]
    )
    return [
        datetime.now().isoformat(),
        article.get("sourceType", "WeChat"),
        article.get("accountName", ""),
        article.get("accountShort", ""),
        article.get("region", ""),
        article.get("title", ""),
        article.get("publishDate", ""),
        article.get("url", ""),
        article.get("articleId", ""),
        (article.get("content") or article.get("digest") or "")[:300],
        "TRUE" if article.get("hasProgram") else "FALSE",
        "TRUE" if article.get("hasDeadline") else "FALSE",
        ", ".join(article.get("keywordsFound") or []),
        "URGENT" if is_urgent else "NORMAL",
        article.get("status", "NEW"),
        "",  # Notes — manual
    ]


def append_articles(sheet, articles: list) -> int:
    if not sheet or not articles:
        return 0
    try:
        rows = [_build_row(a) for a in articles]
        sheet.append_rows(rows, value_input_option="RAW")
        print(f"[Sheets] Wrote {len(rows)} rows")
        return len(rows)
    except Exception as e:
        print(f"[Sheets] append_articles error: {e}")
        return 0


def update_deadlines_tab(sheet):
    """Refresh 'Deadlines' tab with countdown."""
    if not sheet:
        return
    try:
        ss = sheet.spreadsheet
        try:
            dl = ss.worksheet("Deadlines")
            dl.clear()
        except Exception:
            dl = ss.add_worksheet("Deadlines", rows=20, cols=6)

        dl.append_row(["Program", "Deadline", "Days Remaining", "URL", "Status", "Notes"])
        today = datetime.now()
        for d in PROGRAM_DEADLINES:
            from datetime import datetime as dt
            deadline_date = dt.strptime(d["deadline"], "%Y-%m-%d")
            days_left = (deadline_date - today).days
            status = "EXPIRED" if days_left < 0 else ("URGENT" if days_left <= d["days_warn"] else "OK")
            dl.append_row([d["program"], d["deadline"], days_left, d["url"], status, ""])
        print("[Sheets] Deadlines tab updated")
    except Exception as e:
        print(f"[Sheets] update_deadlines_tab error: {e}")


def log_run(sheet, summary: dict):
    """Append run summary to 'Run Log' tab."""
    if not sheet:
        return
    try:
        ss = sheet.spreadsheet
        try:
            rl = ss.worksheet("Run Log")
        except Exception:
            rl = ss.add_worksheet("Run Log", rows=500, cols=6)
            rl.append_row(["Run Time", "New Articles", "Urgent", "Sources Checked", "Email Sent", "Notes"])
        rl.append_row([
            datetime.now().isoformat(),
            summary.get("new_articles", 0),
            summary.get("urgent", 0),
            summary.get("sources_checked", 0),
            "YES" if summary.get("email_sent") else "NO",
            summary.get("notes", ""),
        ])
    except Exception as e:
        print(f"[Sheets] log_run error: {e}")
