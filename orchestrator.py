"""
orchestrator.py — Master runner for China Program Intelligence Platform

Usage:
  python orchestrator.py              # Full pipeline
  python orchestrator.py --quick      # Weixin only (fastest)
  python orchestrator.py --crawl      # Crawl only, no analysis
  python orchestrator.py --analyze    # Analyze only (uses cached data)
  python orchestrator.py --report     # Report generation only

Sources crawled:
  Weixin/WeChat · Baidu · Zhihu · Xiaohongshu · University websites

Agents run:
  ecosystem_agent · trend_agent · prediction_agent · report_agent
"""
import sys, os, argparse, time, json
sys.stdout.reconfigure(encoding="utf-8")

# Load .env file when running locally (Railway sets env vars directly)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from datetime import datetime
from pathlib import Path

# ── Import crawlers ───────────────────────────────────────────────────────────
from crawlers.weixin_crawler     import run_weixin_crawler
from crawlers.baidu_crawler      import run_baidu_crawler
from crawlers.zhihu_crawler      import run_zhihu_crawler
from crawlers.xiaohongshu_crawler import run_xiaohongshu_crawler
from crawlers.university_crawler  import run_university_crawler

# ── Import agents ─────────────────────────────────────────────────────────────
from agents.ecosystem_agent import run_ecosystem_agent

from config import LOGS_DIR, REPORTS_DIR, VIZ_DIR

LOGS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def run_pipeline(mode: str = "full") -> dict:
    start_time = time.time()
    log(f"=== CHINA PROGRAM INTELLIGENCE PLATFORM START (mode={mode}) ===")

    results = {
        "started_at": datetime.now().isoformat(),
        "mode": mode,
        "crawl_results": {},
        "agent_results": {},
    }

    # ── PHASE 1: CRAWLING ─────────────────────────────────────────────────────
    if mode in ("full", "quick", "crawl"):
        log("PHASE 1: Crawling")

        log("→ WeChat/Weixin crawler")
        try:
            results["crawl_results"]["weixin"] = run_weixin_crawler(
                fetch_content=True,
                keyword_search=(mode != "quick"),
                keyword_pages=2 if mode == "full" else 1
            )
        except Exception as e:
            log(f"  WeChat FAILED: {e}")
            results["crawl_results"]["weixin"] = {"error": str(e)}

        if mode != "quick":
            log("→ Baidu crawler")
            try:
                results["crawl_results"]["baidu"] = run_baidu_crawler(pages_per_query=2)
            except Exception as e:
                log(f"  Baidu FAILED: {e}")
                results["crawl_results"]["baidu"] = {"error": str(e)}

            log("→ Zhihu crawler")
            try:
                results["crawl_results"]["zhihu"] = run_zhihu_crawler()
            except Exception as e:
                log(f"  Zhihu FAILED: {e}")
                results["crawl_results"]["zhihu"] = {"error": str(e)}

            log("→ Xiaohongshu crawler")
            try:
                results["crawl_results"]["xiaohongshu"] = run_xiaohongshu_crawler()
            except Exception as e:
                log(f"  XHS FAILED: {e}")
                results["crawl_results"]["xiaohongshu"] = {"error": str(e)}

            log("→ University crawler")
            try:
                results["crawl_results"]["university"] = run_university_crawler()
            except Exception as e:
                log(f"  University FAILED: {e}")
                results["crawl_results"]["university"] = {"error": str(e)}

    # ── PHASE 2: ANALYSIS AGENTS ──────────────────────────────────────────────
    if mode in ("full", "analyze"):
        log("PHASE 2: Analysis Agents")

        log("→ Ecosystem mapping agent")
        try:
            results["agent_results"]["ecosystem"] = run_ecosystem_agent()
        except Exception as e:
            log(f"  Ecosystem FAILED: {e}")
            results["agent_results"]["ecosystem"] = {"error": str(e)}

        # Trend agent (use existing script from wechat-analysis if available)
        log("→ Trend agent")
        try:
            trend_results = _run_trend_analysis()
            results["agent_results"]["trend"] = trend_results
        except Exception as e:
            log(f"  Trend FAILED: {e}")
            results["agent_results"]["trend"] = {"error": str(e)}

    # ── PHASE 3: REPORT GENERATION ────────────────────────────────────────────
    if mode in ("full", "analyze", "report"):
        log("PHASE 3: Report Generation")
        try:
            report_file = _generate_master_report(results)
            results["report_file"] = report_file
            log(f"→ Master report: {report_file}")
        except Exception as e:
            log(f"  Report FAILED: {e}")

    # ── SUMMARY ───────────────────────────────────────────────────────────────
    elapsed = round(time.time() - start_time, 1)
    results["elapsed_s"] = elapsed
    results["completed_at"] = datetime.now().isoformat()

    # Save run summary
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = LOGS_DIR / f"run_{ts}.json"
    summary_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    log(f"=== PIPELINE COMPLETE in {elapsed}s ===")
    _print_summary(results)

    # Send email report (Railway: env vars set in dashboard; local: .env file)
    if os.environ.get("GMAIL_APP_PASSWORD"):
        log("→ Sending email report...")
        from notifier import send_report_email
        send_report_email(results, report_file=results.get("report_file"))
    else:
        log("→ GMAIL_APP_PASSWORD not set — skipping email (set in Railway Variables)")

    return results


def _run_trend_analysis() -> dict:
    """Simple trend analysis from aggregated crawled data."""
    from config import DATA_DIR

    total_new = 0
    sources_active = []

    for source in ["weixin", "baidu", "zhihu", "xiaohongshu", "university"]:
        master = DATA_DIR / source / "all_results.json"
        if not master.exists():
            continue
        try:
            data = json.loads(master.read_text(encoding="utf-8"))
            total_new += len(data)
            sources_active.append(source)
        except Exception:
            pass

    # Count by program type
    program_type_counts = {}
    weixin_file = DATA_DIR / "weixin" / "all_articles.json"
    if weixin_file.exists():
        try:
            articles = json.loads(weixin_file.read_text(encoding="utf-8"))
            for a in articles:
                for kw in a.get("keywords_found", []):
                    program_type_counts[kw] = program_type_counts.get(kw, 0) + 1
        except Exception:
            pass

    top_keywords = sorted(program_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total_records": total_new,
        "active_sources": sources_active,
        "top_keywords": top_keywords,
    }


def _generate_master_report(results: dict) -> str:
    """Generate comprehensive markdown intelligence report."""
    now = datetime.now()
    ts = now.strftime("%Y-%m-%d")

    crawl = results.get("crawl_results", {})
    agents = results.get("agent_results", {})
    ecosystem = agents.get("ecosystem", {})
    trend = agents.get("trend", {})

    weixin_new = crawl.get("weixin", {}).get("new_articles", "N/A")
    baidu_new  = crawl.get("baidu", {}).get("total_results", "N/A")
    zhihu_new  = crawl.get("zhihu", {}).get("total_results", "N/A")
    xhs_new    = crawl.get("xiaohongshu", {}).get("total_results", "N/A")
    univ_new   = crawl.get("university", {}).get("pages_crawled", "N/A")

    report = f"""# China Program Intelligence — Master Report
**Generated:** {ts}
**Mode:** {results.get('mode', 'full')}
**Runtime:** {results.get('elapsed_s', '?')}s

---

## Crawl Summary

| Source | Records Found | Status |
|--------|--------------|--------|
| WeChat/Weixin | {weixin_new} | {'✓' if 'error' not in crawl.get('weixin',{}) else '✗'} |
| Baidu | {baidu_new} | {'✓' if 'error' not in crawl.get('baidu',{}) else '✗'} |
| Zhihu | {zhihu_new} | {'✓' if 'error' not in crawl.get('zhihu',{}) else '✗'} |
| Xiaohongshu | {xhs_new} | {'✓' if 'error' not in crawl.get('xiaohongshu',{}) else '✗'} |
| University | {univ_new} pages | {'✓' if 'error' not in crawl.get('university',{}) else '✗'} |

---

## Ecosystem Map

- **Nodes:** {ecosystem.get('nodes', '?')} organizations/programs
- **Edges:** {ecosystem.get('edges', '?')} relationships
- **Top Influencer:** {ecosystem.get('top_influencer', '?')}
- **Graph:** [ecosystem_full_2026.mmd](../visualizations/ecosystem_full_2026.mmd)

---

## WeChat Account Network

### Confirmed Accounts (Active Monitoring)

| Account | BIZ | Region | Programs |
|---------|-----|--------|----------|
| 加拿大华文学校联合总会 (FCSC) | MzkxNTM0Njg4MQ== | North America | 华文教师研习班, 校长研习班 |
| 北京华文学院 (BCL) | MjM5NjY0MTk5NQ== | China | AI华文教育培训班, 华文教师研习班 |

### Pending Accounts (BIZ Not Confirmed)

| Account | Region | Intelligence Gap |
|---------|--------|-----------------|
| 中国华文教育发展中心 (CHDEC) | China | **CRITICAL** — main orchestrator, no verified public account found |
| 暨南大学华文学院 | China | BIZ unknown |
| 华侨大学华文教育处 | China | BIZ unknown |
| 香港教育交流中心 | HK | Found publishing 寻根之旅 2026 |
| 全美华裔青少年协会 (CAYAUS) | North America | BIZ unknown |
| 欧洲华文教育联合总会 (EFCSA) | Europe | BIZ unknown |
| 澳大利亚华文学校联合会 | Oceania | BIZ unknown |
| 马来西亚华校董事联合会总会 | SE Asia | BIZ unknown |

> **Priority Action:** Find 中国华文教育发展中心's WeChat BIZ code — they are the primary organizer of all government-backed programs but have no verifiable public subscription account. May operate as service account or under alternate name.

---

## Program Monitoring Status

| Program | Organizer | Status | Next Deadline |
|---------|-----------|--------|--------------|
| AI华文教育培训班 (P006) | 北京华文学院 | ACTIVE | 2026-06-30 |
| 华文教师研习班 (P003) Canada | FCSC | ACTIVE | 2026-05-31 |
| 寻根之旅夏令营 (P001) | 暨南大学 | ACTIVE | Unknown |
| Tsinghua GenAI SS | 清华大学 | ACTIVE | Rolling |
| XJTLU AI Camp | 西交利物浦 | ACTIVE | Unknown |

---

## Social Intelligence (Zhihu + XHS)

- **Zhihu records:** {zhihu_new}
- **XHS records:** {xhs_new}
- **Top keywords:** {', '.join([k for k, _ in (trend.get('top_keywords') or [])[:5]])}

---

## Data Files

| File | Description |
|------|-------------|
| extracted_data/weixin/all_articles.json | All WeChat articles |
| extracted_data/baidu/all_results.json | Baidu search results |
| extracted_data/zhihu/all_results.json | Zhihu Q&A and articles |
| extracted_data/xiaohongshu/all_results.json | XHS participant notes |
| extracted_data/university/all_results.json | University program pages |
| ecosystem_mapping/knowledge_graph.json | Full relationship graph |
| visualizations/ecosystem_full_2026.mmd | Mermaid ecosystem diagram |

---

## Next Actions

1. **Find CHDEC WeChat BIZ** — search within WeChat app for "中国华文教育发展中心"
2. **Monitor P006 deadline** — AI华文教育培训班 deadline 2026-06-30 (within 38 days)
3. **Add XHS cookie** — set `XHS_COOKIE` env var to enable direct XHS API access
4. **Expand Sogou search** — current accounts searched: {len([a for a in __import__('config').WEIXIN_ACCOUNTS if a['status']=='PENDING'])} pending accounts

---
*Generated by China Program Intelligence Platform v2.0*
*{ts}*
"""

    report_file = REPORTS_DIR / f"master_report_{now.strftime('%Y%m%d')}.md"
    report_file.write_text(report, encoding="utf-8")
    return str(report_file)


def _print_summary(results: dict):
    print()
    print("─" * 50)
    print("PIPELINE SUMMARY")
    print("─" * 50)
    crawl = results.get("crawl_results", {})
    for source, data in crawl.items():
        if "error" in data:
            print(f"  {source:20s} ✗ FAILED: {data['error'][:50]}")
        else:
            count = data.get("new_articles") or data.get("total_results") or data.get("pages_crawled", 0)
            print(f"  {source:20s} ✓ {count} records")
    print(f"  Total runtime: {results.get('elapsed_s', '?')}s")
    print("─" * 50)


# ── CLI Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="China Program Intelligence Platform")
    parser.add_argument("--mode", choices=["full", "quick", "crawl", "analyze", "report"],
                        default="full", help="Pipeline mode")
    parser.add_argument("--quick", action="store_true", help="Quick mode (WeChat only)")
    parser.add_argument("--crawl", action="store_true", help="Crawl only")
    parser.add_argument("--analyze", action="store_true", help="Analyze only")
    parser.add_argument("--report", action="store_true", help="Report only")
    args = parser.parse_args()

    mode = args.mode
    if args.quick:   mode = "quick"
    if args.crawl:   mode = "crawl"
    if args.analyze: mode = "analyze"
    if args.report:  mode = "report"

    run_pipeline(mode=mode)
