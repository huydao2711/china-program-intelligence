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
    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "1o7NL2nPmJ8g1w7XeWscEwP62wbWbe7W6eBJ00LQWZRk")
    ss = gc.open_by_key(sheet_id)
    try:
        ws = ss.worksheet("Programs")
    except Exception:
        print("[Sheet] Programs sheet not found — run setup_programs_sheet.py first")
        return None
    return ws


def get_existing_keys(ws) -> set:
    """Read application_link + name keys from Programs sheet for dedup."""
    if not ws:
        return set()
    try:
        all_vals = ws.get_all_values()
        keys = set()
        for row in all_vals[2:]:  # skip 2 header rows
            if len(row) > 25:
                link = row[25].strip()
                name = row[0].strip()
                org  = row[2].strip()
                if link:
                    keys.add(link)
                elif name:
                    keys.add(f"{name}|{org}")
        print(f"[Sheet] Loaded {len(keys)} existing program keys")
        return keys
    except Exception as e:
        print(f"[Sheet] get_existing_keys error: {e}")
        return set()


def _program_key(p: dict) -> str:
    link = (p.get("application_link") or "").strip()
    if link:
        return link
    name = (p.get("program_name_en") or p.get("chinese_name") or "").strip()
    org  = (p.get("organization") or "").strip()
    return f"{name}|{org}" if name else ""


def write_to_sheet(ws, programs: list[dict], existing_keys: set) -> int:
    if not ws or not programs:
        return 0
    try:
        new_programs = []
        for p in programs:
            key = _program_key(p)
            if key and key in existing_keys:
                continue
            new_programs.append(p)
            if key:
                existing_keys.add(key)

        if not new_programs:
            print(f"  -> All {len(programs)} already in sheet (skipped)")
            return 0

        rows = programs_to_rows(new_programs)
        ws.append_rows(rows, value_input_option="RAW")
        skipped = len(programs) - len(new_programs)
        if skipped:
            print(f"  -> Wrote {len(rows)} rows ({skipped} duplicates skipped)")
        return len(rows)
    except Exception as e:
        print(f"[Sheet] Write error: {e}")
        return 0


def _get_set_crawl_log(ws, newly_written: int) -> tuple[int, bool]:
    """
    Accumulate newly_written per 2-hour window in 'Crawl Log' tab.
    Returns (window_total, should_send_email).
    Email triggers at the start of the next window if previous window had new programs.
    """
    if not ws:
        return newly_written, newly_written > 0
    try:
        ss = ws.spreadsheet
        now = datetime.now()
        current_window = (now.hour // 2) * 2  # 0,2,4,6,...,22
        try:
            cl = ss.worksheet("Crawl Log")
        except Exception:
            cl = ss.add_worksheet("Crawl Log", rows=5, cols=3)
            cl.append_row(["window_hour", "count", "updated"])
            cl.append_row([str(current_window), str(newly_written), now.isoformat()])
            return newly_written, False

        rows = cl.get_all_values()
        if len(rows) < 2 or not rows[1][0]:
            cl.update("A1:C1", [["window_hour", "count", "updated"]])
            cl.update("A2:C2", [[str(current_window), str(newly_written), now.isoformat()]])
            return newly_written, False

        stored_window = int(rows[1][0])
        stored_count  = int(rows[1][1] or 0)

        if stored_window == current_window:
            # Same 2h window — accumulate, don't email yet
            new_total = stored_count + newly_written
            cl.update("B2:C2", [[str(new_total), now.isoformat()]])
            return new_total, False
        else:
            # New 2h window started — report previous window, reset counter
            cl.update("A2:C2", [[str(current_window), str(newly_written), now.isoformat()]])
            return stored_count, stored_count > 0
    except Exception as e:
        print(f"[Sheet] crawl_log error: {e}")
        return newly_written, newly_written > 0


def _get_reddit_text(url: str) -> str | None:
    """Fetch Reddit JSON API and convert posts to readable text."""
    try:
        resp = requests.get(url, headers={
            "User-Agent": "china-program-bot/1.0",
            "Accept": "application/json",
        }, timeout=20)
        if resp.status_code != 200:
            print(f"  HTTP {resp.status_code}: {url[:60]}")
            return None
        data = resp.json()
        posts = data.get("data", {}).get("children", [])
        if not posts:
            return None
        lines = []
        for p in posts:
            d = p.get("data", {})
            title = d.get("title", "")
            body  = d.get("selftext", "")[:300]
            sub   = d.get("subreddit_name_prefixed", "")
            lines.append(f"[{sub}] {title}\n{body}")
        return "\n\n".join(lines)
    except Exception as e:
        print(f"  Reddit error: {e}")
        return None


def crawl_source(source: dict) -> list[dict]:
    print(f"\n[{source['id']}] {source['name']}")
    print(f"  URL: {source['url']}")

    src_type = source.get("type", "html")

    if src_type == "reddit":
        text = _get_reddit_text(source["url"])
    else:
        html = _get(source["url"])
        if not html:
            raise ConnectionError(f"No response from {source['url']}")
        text = _strip_html(html)

    if not text or len(text) < 200:
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
    existing_keys = get_existing_keys(ws)
    sources = ALL_SOURCES[:5] if test_mode else ALL_SOURCES
    print(f"Sources: {len(sources)} | Test mode: {test_mode}\n")

    all_programs = []
    failed_sources = []
    sources_done = [0]
    newly_written = [0]  # tracks only rows actually written (not deduped)

    def _run_pass(source_list: list, pass_label: str):
        still_failed = []
        for i, source in enumerate(source_list, 1):
            print(f"[{pass_label} {i}/{len(source_list)}]", end=" ")
            try:
                programs = crawl_source(source)
                all_programs.extend(programs)
                if ws and programs:
                    written = write_to_sheet(ws, programs, existing_keys)
                    newly_written[0] += written
                    print(f"  -> Wrote {written} rows to Sheet")
            except Exception as e:
                print(f"  ERROR: {e}")
                still_failed.append(source)

            sources_done[0] += 1
            # Only send progress email if new programs were actually written
            if not test_mode and sources_done[0] % 20 == 0 and newly_written[0] > 0:
                _send_progress_email(sources_done[0], len(sources), newly_written[0])

            time.sleep(3)
        return still_failed

    # Pass 1: all sources
    failed_sources = _run_pass(sources, "P1")

    # Pass 2: retry sources that had no response
    if failed_sources and not test_mode:
        print(f"\n--- Retry pass: {len(failed_sources)} failed sources ---\n")
        time.sleep(30)
        failed_sources = _run_pass(failed_sources, "P2")

    # Pass 3: final retry
    if failed_sources and not test_mode:
        print(f"\n--- Final retry: {len(failed_sources)} sources ---\n")
        time.sleep(60)
        failed_sources = _run_pass(failed_sources, "P3")

    print("\n" + "=" * 65)
    print(f"DONE: {len(all_programs)} programs found | {newly_written[0]} new written to Sheet")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 65)

    # 2-hour email batching: accumulate in Sheet, send once per 2h window
    window_total, send_now = _get_set_crawl_log(ws, newly_written[0])
    if send_now:
        _send_crawl_done_email(window_total, len(sources), len(failed_sources) if failed_sources else 0)
    elif newly_written[0] > 0:
        print(f"[Crawl] Buffered {newly_written[0]} new — window total: {window_total} (email at next 2h mark)")
    else:
        print("[Crawl] No new programs this run")
    return all_programs


def _send_progress_email(done: int, total: int, programs_so_far: int):
    from email_util import send_email
    sheet_id  = os.environ.get("GOOGLE_SHEET_ID", "")
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}" if sheet_id else ""
    body = (
        f"[China Programs] Crawl progress update\n\n"
        f"Sources done : {done} / {total}\n"
        f"Programs found so far : {programs_so_far}\n"
        f"Time : {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n"
    )
    if sheet_url:
        body += f"\nSheet: {sheet_url}\n"
    send_email(f"[Crawl] {done}/{total} nguồn xong — {programs_so_far} programs", body_text=body)


def _send_crawl_done_email(total_programs: int, total_sources: int, remaining_failed: int):
    from email_util import send_email
    now = datetime.now()
    window_start = (now.hour // 2) * 2
    sheet_id  = os.environ.get("GOOGLE_SHEET_ID", "")
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}" if sheet_id else ""
    body = (
        f"[2-hour summary] {now.strftime('%Y-%m-%d')} {window_start:02d}:00–{(window_start+2)%24:02d}:00 UTC\n\n"
        f"New programs added  : {total_programs}\n"
        f"Sources crawled     : {total_sources}\n"
        f"Sources failed      : {remaining_failed}\n"
        f"Report sent at      : {now.strftime('%H:%M UTC')}\n"
    )
    if sheet_url:
        body += f"\nView Programs sheet:\n{sheet_url}\n"
    send_email(f"[China Programs] +{total_programs} programs mới — {now.strftime('%d/%m %H:%M')}", body_text=body)


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
