"""
monitor/sheets.py — Google Sheets integration via gspread.

Env vars needed:
  GOOGLE_SERVICE_ACCOUNT_JSON  — full JSON content of service account key
  GOOGLE_SHEET_ID              — spreadsheet ID (preferred)
  GOOGLE_SHEET_NAME            — fallback sheet name

If GOOGLE_SERVICE_ACCOUNT_JSON is not set, all functions are no-ops and
the system falls back to email-only output.
"""

import os, json
from datetime import datetime

from .config import SHEET_HEADERS, PROGRAM_DEADLINES, MONITOR_CONFIG

_gc    = None   # gspread client
_sheet = None   # Log worksheet handle

# ── Visual constants ───────────────────────────────────────────────────────────
# Column widths (px) matching SHEET_HEADERS order
_COL_WIDTHS = [80, 70, 70, 300, 100, 80, 110, 95, 180, 350, 220, 140, 150]

_HEADER_BG  = {"red": 0.10, "green": 0.14, "blue": 0.49}   # dark indigo
_HEADER_FG  = {"red": 1.0,  "green": 1.0,  "blue": 1.0}
_URGENT_BG  = {"red": 1.0,  "green": 0.89, "blue": 0.87}   # pale red
_PROGRAM_BG = {"red": 0.88, "green": 0.97, "blue": 0.89}   # pale green


# ── Auth ───────────────────────────────────────────────────────────────────────
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


# ── Formatting helpers ─────────────────────────────────────────────────────────
def _apply_formatting(ss, ws):
    """Apply column widths, frozen row 1, and conditional formatting."""
    try:
        sid = ws.id
        requests = []

        # Column widths
        for i, px in enumerate(_COL_WIDTHS):
            requests.append({
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sid, "dimension": "COLUMNS",
                        "startIndex": i, "endIndex": i + 1,
                    },
                    "properties": {"pixelSize": px},
                    "fields": "pixelSize",
                }
            })

        # Freeze header row
        requests.append({
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sid,
                    "gridProperties": {"frozenRowCount": 1},
                },
                "fields": "gridProperties.frozenRowCount",
            }
        })

        # Conditional format: URGENT rows → pale red  (=$A2="URGENT")
        requests.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": sid,
                        "startRowIndex": 1, "endRowIndex": 5000,
                        "startColumnIndex": 0, "endColumnIndex": len(SHEET_HEADERS),
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": "CUSTOM_FORMULA",
                            "values": [{"userEnteredValue": '=$A2="URGENT"'}],
                        },
                        "format": {"backgroundColor": _URGENT_BG},
                    },
                },
                "index": 0,
            }
        })

        # Conditional format: Program rows → pale green  (=$C2="TRUE")
        requests.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": sid,
                        "startRowIndex": 1, "endRowIndex": 5000,
                        "startColumnIndex": 0, "endColumnIndex": len(SHEET_HEADERS),
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": "CUSTOM_FORMULA",
                            "values": [{"userEnteredValue": '=$C2="TRUE"'}],
                        },
                        "format": {"backgroundColor": _PROGRAM_BG},
                    },
                },
                "index": 1,
            }
        })

        ss.batch_update({"requests": requests})
        print("[Sheets] Formatting applied")
    except Exception as e:
        print(f"[Sheets] Formatting error (non-fatal): {e}")


def _init_header(ws):
    """Write styled header row."""
    ws.append_row(SHEET_HEADERS)
    ws.format("1", {
        "backgroundColor": _HEADER_BG,
        "textFormat": {
            "foregroundColor": _HEADER_FG,
            "bold": True,
            "fontSize": 10,
        },
        "horizontalAlignment": "CENTER",
        "verticalAlignment": "MIDDLE",
    })


# ── Sheet access ───────────────────────────────────────────────────────────────
def get_or_create_sheet():
    """Return the Log worksheet handle, reinitializing headers if schema changed."""
    global _sheet
    if _sheet:
        return _sheet

    gc = _client()
    if not gc:
        print("[Sheets] No service account — Sheets disabled")
        return None

    sheet_id   = os.environ.get("GOOGLE_SHEET_ID", "")
    sheet_name = os.environ.get("GOOGLE_SHEET_NAME", MONITOR_CONFIG["SHEET_NAME"])
    try:
        if sheet_id:
            ss = gc.open_by_key(sheet_id)
            print(f"[Sheets] Opened by ID: {sheet_id[:20]}...")
        else:
            ss = gc.open(sheet_name)

        os.environ["GOOGLE_SHEET_URL"] = ss.url
        print(f"[Sheets] URL: {ss.url}")

        # Get or create Log worksheet
        try:
            ws = ss.worksheet("Log")
            existing_headers = ws.row_values(1)
            if existing_headers != SHEET_HEADERS:
                print("[Sheets] Schema changed — reinitializing Log sheet")
                ws.clear()
                _init_header(ws)
                _apply_formatting(ss, ws)
        except Exception:
            ws = ss.add_worksheet("Log", rows=5000, cols=len(SHEET_HEADERS))
            _init_header(ws)
            _apply_formatting(ss, ws)
            print("[Sheets] Created Log sheet")

        _sheet = ws
        return ws
    except Exception as e:
        print(f"[Sheets] get_or_create error: {e}")
        return None


# ── Deduplication ──────────────────────────────────────────────────────────────
def get_seen_ids(sheet) -> set:
    """Return set of known URLs from col K (index 10) for deduplication."""
    if not sheet:
        return set()
    try:
        all_vals = sheet.get_all_values()
        seen = set()
        for row in all_vals[1:]:        # skip header
            if len(row) > 10 and row[10]:
                seen.add(row[10])       # col K: URL
        return seen
    except Exception as e:
        print(f"[Sheets] get_seen_ids error: {e}")
        return set()


# ── Fingerprints (State tab) ───────────────────────────────────────────────────
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


# ── Row building & sorting ─────────────────────────────────────────────────────
def _is_urgent(article: dict) -> bool:
    kw_text = " ".join(article.get("keywordsFound", [])).lower()
    return bool(article.get("hasDeadline")) or any(
        kw.lower() in kw_text for kw in MONITOR_CONFIG["URGENT_KEYWORDS"]
    )


def _sort_key(article: dict) -> int:
    if _is_urgent(article):
        return 0
    if article.get("hasProgram"):
        return 1
    return 2


def _build_row(article: dict) -> list:
    urgent = _is_urgent(article)
    return [
        "URGENT" if urgent else "NORMAL",                               # A Priority
        "TRUE" if article.get("hasDeadline") else "FALSE",             # B Deadline
        "TRUE" if article.get("hasProgram") else "FALSE",              # C Program
        article.get("title", ""),                                       # D Title
        article.get("accountShort", ""),                                # E Source
        article.get("sourceType", "WeChat"),                            # F Type
        article.get("region", ""),                                      # G Region
        article.get("publishDate", ""),                                 # H Date
        ", ".join(article.get("keywordsFound") or []),                  # I Keywords
        (article.get("content") or article.get("digest") or "")[:300], # J Preview
        article.get("url", ""),                                         # K URL
        datetime.now().strftime("%Y-%m-%d %H:%M"),                      # L Timestamp
        "",                                                              # M Notes
    ]


# ── Write articles ─────────────────────────────────────────────────────────────
def append_articles(sheet, articles: list) -> int:
    """Sort (URGENT first) and append articles to Log sheet."""
    if not sheet or not articles:
        return 0
    try:
        sorted_articles = sorted(articles, key=_sort_key)
        rows = [_build_row(a) for a in sorted_articles]
        sheet.append_rows(rows, value_input_option="RAW")
        print(f"[Sheets] Wrote {len(rows)} rows ({sum(1 for a in sorted_articles if _sort_key(a) == 0)} urgent)")
        return len(rows)
    except Exception as e:
        print(f"[Sheets] append_articles error: {e}")
        return 0


# ── Supporting tabs ────────────────────────────────────────────────────────────
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
            deadline_date = datetime.strptime(d["deadline"], "%Y-%m-%d")
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
