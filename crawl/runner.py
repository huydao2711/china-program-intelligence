"""
crawl/runner.py — Main crawl runner. Fetches all sources, extracts programs, writes to Sheet.

Usage:
    python -m crawl.runner            # crawl all sources
    python -m crawl.runner --test     # crawl first 5 sources only
"""
import os, re, sys, time, json, hashlib
import requests
from datetime import datetime

from .sources import ALL_SOURCES, SEARCH_QUERIES_EN, SEARCH_QUERIES_ZH
from .extractor import extract_programs, programs_to_rows

DESKTOP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _get(url: str, timeout: int = 20) -> str | None:
    try:
        resp = requests.get(url, headers={
            "User-Agent": DESKTOP_UA,
            "Accept": "text/html,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            return resp.text
        print(f"  HTTP {resp.status_code}: {url[:60]}")
    except Exception as e:
        print(f"  Error {url[:50]}: {e}")
    return None


def _strip_html(html: str) -> str:
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    html = re.sub(r"<style[\s\S]*?</style>",   " ", html, flags=re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html).strip()


def _fingerprint(text: str) -> str:
    return hashlib.md5(text[:3000].encode()).hexdigest()[:12]


def get_sheet():
    import gspread
    from google.oauth2.service_account import Credentials
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not sa_json:
        # Try local file
        local = "../railway-monitor-497207-11b94d1a89af.json"
        if os.path.exists(local):
            with open(local) as f:
                sa_info = json.load(f)
        else:
            print("[Sheet] No credentials found")
            return None
    else:
        sa_info = json.loads(sa_json)

    creds = Credentials.from_service_account_info(sa_info, scopes=[
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ])
    gc = gspread.authorize(creds)
    ss = gc.open_by_key("1o7NL2nPmJ8g1w7XeWscEwP62wbWbe7W6eBJ00LQWZRk")
    try:
        ws = ss.worksheet("Programs")
    except Exception:
        print("[Sheet] Programs sheet not found — run setup_programs_sheet.py first")
        return None
    return ws


def write_to_sheet(ws, programs: list[dict]) -> int:
    if not ws or not programs:
        return 0
    try:
        rows = programs_to_rows(programs)
        ws.append_rows(rows, value_input_option="RAW")
        return len(rows)
    except Exception as e:
        print(f"[Sheet] Write error: {e}")
        return 0


def crawl_source(source: dict) -> list[dict]:
    print(f"\n[{source['id']}] {source['name']}")
    print(f"  URL: {source['url']}")

    html = _get(source["url"])
    if not html:
        raise ConnectionError(f"No response from {source['url']}")

    text = _strip_html(html)
    if len(text) < 200:
        print("  Skipped — too little text")
        return []

    programs = extract_programs(text, source["url"], source["name"])
    print(f"  Extracted: {len(programs)} programs")
    for p in programs:
        name = p.get("program_name_en") or p.get("chinese_name") or "?"
        conf = p.get("confidence", 0)
        print(f"    [{conf:.1f}] {name[:60]}")
    return programs


def run(test_mode: bool = False):
    print("=" * 65)
    print(f"PROGRAMS CRAWL — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 65)

    ws = get_sheet()
    sources = ALL_SOURCES[:5] if test_mode else ALL_SOURCES
    print(f"Sources: {len(sources)} | Test mode: {test_mode}\n")

    all_programs = []
    failed_sources = []

    def _run_pass(source_list: list, pass_label: str):
        still_failed = []
        for i, source in enumerate(source_list, 1):
            print(f"[{pass_label} {i}/{len(source_list)}]", end=" ")
            try:
                programs = crawl_source(source)
                all_programs.extend(programs)
                if ws and programs:
                    written = write_to_sheet(ws, programs)
                    print(f"  -> Wrote {written} rows to Sheet")
            except Exception as e:
                print(f"  ERROR: {e}")
                still_failed.append(source)
            time.sleep(3)
        return still_failed

    # Pass 1: all sources
    failed_sources = _run_pass(sources, "P1")

    # Pass 2: retry sources that had no response (skip ones that returned 0 programs normally)
    if failed_sources and not test_mode:
        print(f"\n--- Retry pass: {len(failed_sources)} failed sources ---\n")
        time.sleep(30)
        failed_sources = _run_pass(failed_sources, "P2")

    # Pass 3: final retry
    if failed_sources and not test_mode:
        print(f"\n--- Final retry: {len(failed_sources)} sources ---\n")
        time.sleep(60)
        _run_pass(failed_sources, "P3")

    print("\n" + "=" * 65)
    print(f"DONE: {len(all_programs)} programs from {len(sources)} sources")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 65)
    return all_programs


if __name__ == "__main__":
    test = "--test" in sys.argv
    # Load env from .env if running locally
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    # Set Gemini key if not in env
    if not os.environ.get("GEMINI_API_KEY"):
        print("Warning: GEMINI_API_KEY not set — extraction disabled")
    run(test_mode=test)
