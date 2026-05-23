"""
crawlers/xiaohongshu_crawler.py
Crawl Xiaohongshu (RED) for participant logs, reviews, application sharing.
High-value: real photos, personal experiences, acceptance proof, hidden costs.

Note: XHS requires session cookies. Set XHS_COOKIE environment variable.
Fallback: scrape XHS via Google/Baidu index (no login needed).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

import json, re, time, random, hashlib, ssl
import urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path
from config import (
    DATA_DIR, ARCHIVE_DIR, CACHE_TTL_HOURS,
    UA_CHROME_MOBILE, CRAWL_DELAY_MIN, CRAWL_DELAY_MAX,
    MAX_RETRIES, REQUEST_TIMEOUT, CONTENT_PREVIEW_LEN
)

OUT_DIR = DATA_DIR / "xiaohongshu"
CACHE_DIR = ARCHIVE_DIR / "cache" / "xiaohongshu"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

XHS_COOKIE = os.environ.get("XHS_COOKIE", "")
XHS_SEARCH = "https://www.xiaohongshu.com/search_result?keyword={query}&type=51"
XHS_API    = "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes?keyword={query}&page={page}&page_size=20&note_type=0"

# Fallback: Google/Baidu indexed XHS pages
GOOGLE_XHS = "https://www.google.com/search?q=site:xiaohongshu.com+{query}"
BAIDU_XHS  = "https://www.baidu.com/s?wd=site:xiaohongshu.com+{query}"

XHS_HEADERS = {
    "User-Agent": UA_CHROME_MOBILE,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.xiaohongshu.com/",
    "Cookie": XHS_COOKIE,
    "x-sign": "X",  # Placeholder — real sign requires JS execution
}

BROWSER_HEADERS = {
    "User-Agent": UA_CHROME_MOBILE,
    "Accept": "text/html,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.xiaohongshu.com/",
}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

XHS_QUERIES = [
    "寻根之旅 夏令营 体验",
    "海外华裔青少年 中国游学 2026",
    "北京华文学院 AI培训",
    "暨南大学 海外华裔 暑期",
    "华文教师培训 研习班 心得",
    "overseas Chinese youth China program 经验",
    "中国暑期夏令营 海外华人子女 分享",
    "申请 寻根 夏令营 攻略 2025 2026",
    "AI夏令营 中国 录取 2026",
    "清华暑期 留学生 体验分享",
]


def _cache_path(key: str) -> Path:
    h = hashlib.md5(key.encode()).hexdigest()
    return CACHE_DIR / f"{h}.json"

def _load_cache(key: str):
    p = _cache_path(key)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if (time.time() - data.get("_cached_at", 0)) / 3600 < CACHE_TTL_HOURS:
            return data.get("payload")
    except Exception:
        pass
    return None

def _save_cache(key: str, payload):
    _cache_path(key).write_text(
        json.dumps({"_cached_at": time.time(), "payload": payload},
                   ensure_ascii=False, indent=2), encoding="utf-8")

def _fetch(url: str, headers: dict) -> str | None:
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=SSL_CTX) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(random.uniform(2, 5))
            else:
                print(f"[XHS] Fetch failed: {url[:80]} — {e}")
    return None

def _fetch_via_xhs_api(query: str, page: int = 1) -> list[dict]:
    """Try XHS API (requires valid session cookie)."""
    if not XHS_COOKIE:
        return []
    url = XHS_API.format(query=urllib.parse.quote(query), page=page)
    html = _fetch(url, XHS_HEADERS)
    if not html:
        return []
    try:
        data = json.loads(html)
        notes = data.get("data", {}).get("notes", [])
        results = []
        for note in notes:
            results.append({
                "source": "xiaohongshu",
                "id": note.get("id", ""),
                "title": note.get("display_title", ""),
                "content": note.get("desc", "")[:CONTENT_PREVIEW_LEN],
                "author": note.get("user", {}).get("nickname", ""),
                "likes": note.get("liked_count", 0),
                "comments": note.get("comment_count", 0),
                "url": f"https://www.xiaohongshu.com/explore/{note.get('id','')}",
                "images": [img.get("url", "") for img in note.get("image_list", [])[:3]],
                "type": note.get("type", ""),
                "publish_date": note.get("time", ""),
                "query": query,
                "fetched_at": datetime.now().isoformat(),
            })
        return results
    except (json.JSONDecodeError, KeyError):
        return []

def _fetch_via_baidu_index(query: str) -> list[dict]:
    """Fallback: find XHS content via Baidu search index."""
    search_q = f"site:xiaohongshu.com {query}"
    url = f"https://www.baidu.com/s?wd={urllib.parse.quote(search_q)}&rn=20"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://www.baidu.com/",
    }
    html = _fetch(url, headers)
    if not html:
        return []

    results = []
    # Extract XHS URLs from Baidu results
    xhs_links = re.findall(
        r'href="(https?://(?:www\.)?xiaohongshu\.com/[^"]+)"', html
    )
    titles = re.findall(r'<h3[^>]*>([\s\S]*?)</h3>', html)
    titles = [re.sub(r"<[^>]+>", "", t).strip() for t in titles]

    for i, link in enumerate(xhs_links[:10]):
        note_id_m = re.search(r'/explore/([a-z0-9]+)', link)
        note_id = note_id_m.group(1) if note_id_m else ""
        results.append({
            "source": "xiaohongshu_baidu",
            "id": note_id or link,
            "title": titles[i] if i < len(titles) else "",
            "content": "",
            "author": "",
            "likes": 0,
            "comments": 0,
            "url": link,
            "images": [],
            "type": "note",
            "publish_date": "",
            "query": query,
            "fetched_at": datetime.now().isoformat(),
        })
    return results

def _analyze_note(note: dict) -> dict:
    """Add intelligence tags to each note."""
    text = (note.get("title","") + " " + note.get("content","")).lower()

    tags = []
    if any(w in text for w in ["录取", "通知书", "offer", "accepted"]):
        tags.append("ACCEPTANCE_PROOF")
    if any(w in text for w in ["费用", "花了多少", "cost", "price", "贵", "便宜"]):
        tags.append("COST_INSIGHT")
    if any(w in text for w in ["申请", "攻略", "怎么申请", "how to apply"]):
        tags.append("APPLICATION_GUIDE")
    if any(w in text for w in ["体验", "感受", "真实", "心得", "review", "experience"]):
        tags.append("PARTICIPANT_REVIEW")
    if any(w in text for w in ["推荐", "recommend", "值得", "worth"]):
        tags.append("RECOMMENDATION")

    note["tags"] = tags
    note["engagement_score"] = (
        note.get("likes", 0) * 1 + note.get("comments", 0) * 3
    )
    return note


def run_xiaohongshu_crawler() -> dict:
    print("=" * 60)
    print("[Xiaohongshu Crawler] START")
    if not XHS_COOKIE:
        print("[XHS] No cookie set — using Baidu index fallback only")
    start = time.time()

    all_results = []
    seen_ids = set()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for query in XHS_QUERIES:
        print(f"[XHS] Query: {query}")
        cache_key = f"xhs_{query}"
        cached = _load_cache(cache_key)

        if cached:
            results = cached
        else:
            # Try API first (needs cookie), then Baidu fallback
            results = _fetch_via_xhs_api(query)
            if not results:
                results = _fetch_via_baidu_index(query)
            if results:
                _save_cache(cache_key, results)

        new = [r for r in results if r.get("id") not in seen_ids]
        for r in new:
            if r.get("id"):
                seen_ids.add(r["id"])
            _analyze_note(r)

        all_results.extend(new)
        print(f"[XHS]   {len(new)} results")
        time.sleep(random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX))

    # Sort by engagement
    all_results.sort(key=lambda r: r.get("engagement_score", 0), reverse=True)

    # Save
    out_file = OUT_DIR / f"xhs_{timestamp}.json"
    out_file.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")

    master = OUT_DIR / "all_results.json"
    existing = []
    if master.exists():
        try:
            existing = json.loads(master.read_text(encoding="utf-8"))
        except Exception:
            pass
    existing_ids = {r.get("id") for r in existing}
    new_only = [r for r in all_results if r.get("id") not in existing_ids]
    master.write_text(json.dumps(existing + new_only, ensure_ascii=False, indent=2),
                      encoding="utf-8")

    elapsed = round(time.time() - start, 1)
    summary = {
        "total_results": len(all_results),
        "with_acceptance_proof": sum(1 for r in all_results if "ACCEPTANCE_PROOF" in r.get("tags", [])),
        "with_cost_insight": sum(1 for r in all_results if "COST_INSIGHT" in r.get("tags", [])),
        "top_engagement": all_results[0].get("engagement_score", 0) if all_results else 0,
        "elapsed_s": elapsed,
        "output_file": str(out_file),
    }
    print(f"[XHS Crawler] END — {len(all_results)} results in {elapsed}s")
    return summary


if __name__ == "__main__":
    run_xiaohongshu_crawler()
