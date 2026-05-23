"""
main.py — Unified entry point for Railway cron job.

Schedule (railway.toml): daily 7AM Vietnam time (00:00 UTC)

Every day:
  - Monitor 27 sources (WeChat + Website + Sogou)
  - Write new articles to Google Sheets (if configured)
  - Send daily digest email

Every Sunday additionally:
  - Run deep intelligence pipeline (Baidu, Zhihu, XHS, University)
  - Send weekly analysis report
"""

import sys, os, time
sys.stdout.reconfigure(encoding="utf-8")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from datetime import datetime

from monitor.wechat  import fetch_all_accounts
from monitor.sources import fetch_all_web_sources
from monitor.sheets  import (
    get_or_create_sheet, get_seen_ids, get_fingerprints,
    save_fingerprints, append_articles, update_deadlines_tab, log_run,
)
from monitor.notifier import send_daily_digest, send_urgent_alert


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ── PHASE 1: Daily Monitor ────────────────────────────────────────────────────

def run_daily_monitor() -> dict:
    log("=== DAILY MONITOR START ===")
    start = time.time()

    # Connect to Google Sheets (optional — falls back to email-only if not configured)
    sheet = get_or_create_sheet()
    seen_ids        = get_seen_ids(sheet)          # read existing URLs/IDs
    fingerprint_store = get_fingerprints(sheet)    # website change detection

    log(f"Seen IDs loaded: {len(seen_ids)}")

    all_new = []

    # WeChat accounts (11)
    log("→ WeChat accounts (11)")
    wechat_articles = fetch_all_accounts(seen_ids)
    for a in wechat_articles:
        if a.get("hasDeadline"):
            send_urgent_alert(a)
        all_new.append(a)

    # Web sources (16: websites + Sogou)
    log("→ Web & Sogou sources (16)")
    web_articles = fetch_all_web_sources(seen_ids, fingerprint_store)
    for a in web_articles:
        if a.get("hasDeadline"):
            send_urgent_alert(a)
        all_new.append(a)

    # Write to Google Sheets
    if sheet:
        written = append_articles(sheet, all_new)
        update_deadlines_tab(sheet)
        save_fingerprints(sheet, fingerprint_store)
        log(f"Wrote {written} rows to Google Sheets")

    # Send daily digest email
    sheet_url = os.environ.get("GOOGLE_SHEET_URL", "")
    email_sent = False
    if all_new:
        email_sent = send_daily_digest(all_new, sheet_url)
    else:
        log("No new content — skipping digest email")

    elapsed = round(time.time() - start, 1)
    urgent  = [a for a in all_new if a.get("hasDeadline")]

    summary = {
        "new_articles":    len(all_new),
        "urgent":          len(urgent),
        "sources_checked": 27,
        "email_sent":      email_sent,
        "notes":           f"{elapsed}s | WeChat:{len(wechat_articles)} Web:{len(web_articles)}",
    }

    if sheet:
        log_run(sheet, summary)

    log(f"=== DAILY MONITOR END — {len(all_new)} new in {elapsed}s ===")
    return summary


# ── PHASE 2: Weekly Intelligence (Sundays only) ───────────────────────────────

def run_weekly_intelligence() -> dict:
    log("=== WEEKLY INTELLIGENCE START ===")
    try:
        from orchestrator import run_pipeline
        results = run_pipeline(mode="full")
        log("=== WEEKLY INTELLIGENCE END ===")
        return results
    except Exception as e:
        log(f"Weekly intelligence failed: {e}")
        return {"error": str(e)}


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    today = datetime.now()
    is_sunday = today.weekday() == 6

    # Always run daily monitor
    monitor_result = run_daily_monitor()

    # Run deep analysis on Sundays
    if is_sunday:
        log("Sunday — running weekly intelligence pipeline")
        run_weekly_intelligence()
    else:
        log(f"Not Sunday ({today.strftime('%A')}) — skipping intelligence pipeline")

    log("All done.")
