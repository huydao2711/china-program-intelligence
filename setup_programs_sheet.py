"""
setup_programs_sheet.py — Create the Programs master database sheet.
Run once to initialize structure. Safe to re-run (clears and rebuilds).
"""
import json
import gspread
from google.oauth2.service_account import Credentials

with open('../railway-monitor-497207-11b94d1a89af.json') as f:
    sa_info = json.load(f)

scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_info(sa_info, scopes=scopes)
gc = gspread.authorize(creds)
ss = gc.open_by_key('1o7NL2nPmJ8g1w7XeWscEwP62wbWbe7W6eBJ00LQWZRk')

# ── Remove old Programs sheet if exists ────────────────────────────────────────
for ws in ss.worksheets():
    if ws.title == 'Programs':
        ss.del_worksheet(ws)
        print('Deleted old Programs sheet')

ws = ss.add_worksheet('Programs', rows=2000, cols=52)
print('Created Programs sheet')

# ── Column definitions ─────────────────────────────────────────────────────────
# (header, width_px)
COLUMNS = [
    # ── Core Info (A-M) ──
    ("Program Name (EN)",       220),
    ("Chinese Name",            200),
    ("Organization",            180),
    ("Program Type",            140),
    ("Country Eligibility",     140),
    ("Online/Offline",           90),
    ("City",                    100),
    ("Province",                110),
    ("Duration",                100),
    ("Start Date",               95),
    ("End Date",                 95),
    ("Last Active Year",         90),
    ("Recurring?",               80),
    # ── Eligibility (N-R) ──
    ("Target Group",            130),
    ("Age Requirement",         110),
    ("Language Req",            110),
    ("HSK Requirement",         110),
    ("Degree Requirement",      130),
    # ── Financial (S-X) ──
    ("Fully Funded?",            90),
    ("Scholarship Amount",      130),
    ("Tuition Covered?",         95),
    ("Accommodation?",           95),
    ("Flight Covered?",          95),
    ("Stipend?",                 80),
    # ── Application (Y-AD) ──
    ("Deadline",                100),
    ("Application Link",        200),
    ("Official Website",        200),
    ("Contact Email",           170),
    ("WeChat Account",          140),
    ("Contact Person",          130),
    # ── Details (AE-AJ) ──
    ("Program Description",     300),
    ("Activities",              200),
    ("Exchange Type",           120),
    ("Internship?",              80),
    ("Certificate?",             80),
    ("Credits Transfer?",        95),
    # ── Metadata (AK-AQ) ──
    ("Source URL",              220),
    ("Platform Source",         130),
    ("Scraped Date",            100),
    ("Confidence Score",         95),
    ("Duplicate Check",          95),
    ("Still Active?",            90),
    ("Notes",                   200),
    # ── Personal Tracking (AR-AX) ──
    ("Applied?",                 75),
    ("Followed?",                75),
    ("Contacted?",               80),
    ("Response Status",         120),
    ("Interview Status",        120),
    ("Priority Level",           95),
    ("Personal Notes",          200),
]

headers = [c[0] for c in COLUMNS]
widths  = [c[1] for c in COLUMNS]

# ── Write headers ──────────────────────────────────────────────────────────────
ws.append_row(headers)
print(f'Wrote {len(headers)} column headers')

# ── Colors ────────────────────────────────────────────────────────────────────
HEADER_BG = {"red": 0.10, "green": 0.14, "blue": 0.49}
HEADER_FG = {"red": 1.0,  "green": 1.0,  "blue": 1.0}

# Section header colors
CORE_BG    = {"red": 0.20, "green": 0.40, "blue": 0.75}   # blue
ELIG_BG    = {"red": 0.30, "green": 0.60, "blue": 0.40}   # green
FIN_BG     = {"red": 0.75, "green": 0.50, "blue": 0.20}   # orange
APP_BG     = {"red": 0.55, "green": 0.25, "blue": 0.65}   # purple
DET_BG     = {"red": 0.25, "green": 0.55, "blue": 0.65}   # teal
META_BG    = {"red": 0.50, "green": 0.50, "blue": 0.50}   # grey
TRACK_BG   = {"red": 0.65, "green": 0.30, "blue": 0.30}   # dark red

WHITE_FG   = {"red": 1.0, "green": 1.0, "blue": 1.0}

# Row conditional colors
GREEN_BG   = {"red": 0.85, "green": 0.97, "blue": 0.85}   # fully funded
YELLOW_BG  = {"red": 1.0,  "green": 0.97, "blue": 0.80}   # partial
RED_BG     = {"red": 1.0,  "green": 0.88, "blue": 0.86}   # inactive

sid = ws.id
n   = len(headers)

# Section column ranges (0-indexed)
SECTIONS = [
    ("CORE INFO",        0,  12,  CORE_BG),
    ("ELIGIBILITY",     13,  17,  ELIG_BG),
    ("FINANCIAL",       18,  23,  FIN_BG),
    ("APPLICATION",     24,  29,  APP_BG),
    ("DETAILS",         30,  35,  DET_BG),
    ("METADATA",        36,  42,  META_BG),
    ("TRACKING",        43,  50,  TRACK_BG),
]

# ── Format header row with section colors ─────────────────────────────────────
def col_letter(i):
    """0-indexed column to A1 letter."""
    letters = ''
    i += 1
    while i > 0:
        i, r = divmod(i - 1, 26)
        letters = chr(65 + r) + letters
    return letters

requests_list = []

# Column widths
for i, px in enumerate(widths):
    requests_list.append({
        "updateDimensionProperties": {
            "range": {"sheetId": sid, "dimension": "COLUMNS",
                      "startIndex": i, "endIndex": i + 1},
            "properties": {"pixelSize": px},
            "fields": "pixelSize",
        }
    })

# Freeze row 1 + col A
requests_list.append({
    "updateSheetProperties": {
        "properties": {"sheetId": sid,
                       "gridProperties": {"frozenRowCount": 1, "frozenColumnCount": 1}},
        "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
    }
})

# Section colors on header row
for _, start, end, color in SECTIONS:
    requests_list.append({
        "repeatCell": {
            "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1,
                      "startColumnIndex": start, "endColumnIndex": end + 1},
            "cell": {"userEnteredFormat": {
                "backgroundColor": color,
                "textFormat": {"foregroundColor": WHITE_FG, "bold": True, "fontSize": 10},
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
            }},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)",
        }
    })

# Conditional formatting: Fully Funded = YES → green rows (col S = index 18)
requests_list.append({
    "addConditionalFormatRule": {
        "rule": {
            "ranges": [{"sheetId": sid, "startRowIndex": 1, "endRowIndex": 2000,
                        "startColumnIndex": 0, "endColumnIndex": n}],
            "booleanRule": {
                "condition": {"type": "CUSTOM_FORMULA",
                              "values": [{"userEnteredValue": '=$S2="Yes"'}]},
                "format": {"backgroundColor": GREEN_BG},
            },
        }, "index": 0,
    }
})

# Conditional formatting: Still Active = No → red rows (col AR = index 41)
requests_list.append({
    "addConditionalFormatRule": {
        "rule": {
            "ranges": [{"sheetId": sid, "startRowIndex": 1, "endRowIndex": 2000,
                        "startColumnIndex": 0, "endColumnIndex": n}],
            "booleanRule": {
                "condition": {"type": "CUSTOM_FORMULA",
                              "values": [{"userEnteredValue": '=$AP2="No"'}]},
                "format": {"backgroundColor": RED_BG},
            },
        }, "index": 1,
    }
})

# Conditional formatting: Fully Funded = Partial → yellow
requests_list.append({
    "addConditionalFormatRule": {
        "rule": {
            "ranges": [{"sheetId": sid, "startRowIndex": 1, "endRowIndex": 2000,
                        "startColumnIndex": 0, "endColumnIndex": n}],
            "booleanRule": {
                "condition": {"type": "CUSTOM_FORMULA",
                              "values": [{"userEnteredValue": '=$S2="Partial"'}]},
                "format": {"backgroundColor": YELLOW_BG},
            },
        }, "index": 2,
    }
})

# Row height for header
requests_list.append({
    "updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "ROWS",
                  "startIndex": 0, "endIndex": 1},
        "properties": {"pixelSize": 40},
        "fields": "pixelSize",
    }
})

ss.batch_update({"requests": requests_list})
print('Formatting applied')

# ── Add filter on header row ───────────────────────────────────────────────────
ws.set_basic_filter(1, 1, 1, len(headers))
print('Filter added')

# ── Add a second row as section labels ────────────────────────────────────────
section_row = [''] * len(headers)
for label, start, end, _ in SECTIONS:
    section_row[start] = f'── {label} ──'
ws.insert_row(section_row, index=2)

# Color the section label row
label_requests = []
for _, start, end, color in SECTIONS:
    lighter = {k: min(1.0, v + 0.25) for k, v in color.items()}
    label_requests.append({
        "repeatCell": {
            "range": {"sheetId": sid, "startRowIndex": 1, "endRowIndex": 2,
                      "startColumnIndex": start, "endColumnIndex": end + 1},
            "cell": {"userEnteredFormat": {
                "backgroundColor": lighter,
                "textFormat": {"bold": True, "italic": True, "fontSize": 9,
                               "foregroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2}},
            }},
            "fields": "userEnteredFormat(backgroundColor,textFormat)",
        }
    })
# Freeze 2 rows
label_requests.append({
    "updateSheetProperties": {
        "properties": {"sheetId": sid,
                       "gridProperties": {"frozenRowCount": 2, "frozenColumnCount": 1}},
        "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
    }
})
ss.batch_update({"requests": label_requests})
print('Section labels added')

print(f'\n✅ Programs sheet ready: {ss.url}')
print(f'   {len(headers)} columns, conditional formatting, filters, frozen rows')
