"""
crawlers/baidu_crawler.py
Search Baidu for Chinese internet content about target programs.
Covers: university sites, news, government portals, blogs, forum posts.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

import json, re, time, random, hashlib, ssl
import urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path
from config import (
    DATA_DIR, ARCHIVE_DIR, LOGS_DIR, CACHE_TTL_HOURS,
    UA_CHROME_DESKTOP, CRAWL_DELAY_MIN, CRAWL_DELAY_MAX,
    MAX_RETRIES, REQUEST_TIMEOUT, PROGRAM_KEYWORDS, CONTENT_PREVIEW_LEN
)

OUT_DIR = DATA_DIR / "baidu"
CACHE_DIR = ARCHIVE_DIR / "cache" / "baidu"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BAIDU_SEARCH = "https://www.baidu.com/s?wd={query}&rn=20&pn={pn}"

HEADERS = {
    "User-Agent": UA_CHROME_DESKTOP,
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.baidu.com/",
    "Cookie": "BIDUPSID=placeholder; PSTM=placeholder;",
}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# Build composite search queries from program keywords
SEARCH_QUERIES = [
    "海外华裔青少年夏令营 2026 报名",
    "华文教师研习班 2026 申请",
    "寻根之旅 2026 夏令营",
    "AI华文教育培训班 2026",
    "海外华文学校 teacher training 2026",
    "暑期国际夏令营 中国 2026 报名",
    "中国政府奖学金 海外华人 2026",
    "overseas Chinese youth summer program China 2026",
    "华裔青少年科技创新营 2025 2026",
    "北京华文学院 招生 2026",
    "暨南大学 寻根 海外华裔 2026",
    "全球少年AI创新营 2026",
    "清华大学 暑期学校 overseas 2026",
    "西湖大学 国际夏令营 2026",
    "XJTLU AI camp 2026",
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
        age_h = (time.time() - data.get("_cached_at", 0)) / 3600
        if age_h < CACHE_TTL_HOURS:
            return data.get("payload")
    except Exception:
        pass
    return None

def _save_cache(key: str, payload):
    p = _cache_path(key)
    p.write_text(json.dumps({"_cached_at": time.time(), "payload": payload},
                             ensure_ascii=False, indent=2), encoding="utf-8")

def _fetch(url: str, retries: int = MAX_RETRIES) -> str | None:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=SSL_CTX) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(random.uniform(2, 5) * (attempt + 1))
            else:
                print(f"[Baidu] Fetch failed: {url} — {e}")
    return None

def _parse_baidu_results(html: str, query: str) -> list[dict]:
    """Parse Baidu SERP results from HTML."""
    results = []

    # Extract result blocks
    # Baidu uses <h3 class="c-title..."> for titles and various URL patterns
    blocks = re.findall(
        r'<h3[^>]+class="[^"]*c-title[^"]*"[^>]*>([\s\S]*?)</h3>',
        html, re.IGNORECASE
    )

    # More reliable: extract all result links + snippets
    # Baidu result links pattern
    link_pattern = re.compile(
        r'<a[^>]+href="(https?://[^"]+)"[^>]*>([\s\S]*?)</a>', re.IGNORECASE
    )
    snippet_pattern = re.compile(
        r'<span[^>]+class="[^"]*content-right_[^"]*"[^>]*>([\s\S]*?)</span>',
        re.IGNORECASE
    )

    links = link_pattern.findall(html)
    snippets = snippet_pattern.findall(html)

    seen_urls = set()
    for i, (url, anchor_html) in enumerate(links[:30]):
        # Skip internal Baidu URLs
        if "baidu.com" in url and "link?url=" not in url:
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)

        title = re.sub(r"<[^>]+>", "", anchor_html).strip()
        snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip() if i < len(snippets) else ""

        if not title or len(title) < 4:
            continue

        # Filter: only keep results likely about programs
        text = (title + " " + snippet).lower()
        program_indicators = ["夏令营", "培训", "研习", "寻根", "华文", "海外华裔",
                               "camp", "program", "营", "招生", "报名", "ai",
                               "overseas", "chinese", "youth", "scholarship"]
        if not any(ind in text for ind in program_indicators):
            continue

        # Determine source type
        source_type = "web"
        if "mp.weixin.qq.com" in url:
            source_type = "weixin"
        elif "zhihu.com" in url:
            source_type = "zhihu"
        elif "weibo.com" in url:
            source_type = "weibo"
        elif "xiaohongshu.com" in url or "xhscdn.com" in url:
            source_type = "xiaohongshu"
        elif any(edu in url for edu in [".edu.cn", ".edu.hk", ".edu.sg", ".ac.cn"]):
            source_type = "university"

        results.append({
            "source": f"baidu_{source_type}",
            "query": query,
            "title": title[:200],
            "url": url,
            "snippet": snippet[:300],
            "source_type": source_type,
            "fetched_at": datetime.now().isoformat(),
        })

    return results


def run_baidu_crawler(pages_per_query: int = 2) -> dict:
    print("=" * 60)
    print("[Baidu Crawler] START")
    start = time.time()

    all_results = []
    seen_urls = set()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for query in SEARCH_QUERIES:
        print(f"[Baidu] Query: {query}")

        for page in range(pages_per_query):
            pn = page * 20
            url = BAIDU_SEARCH.format(
                query=urllib.parse.quote(query), pn=pn
            )
            cache_key = f"baidu_{query}_{page}"
            html = _load_cache(cache_key)

            if not html:
                html = _fetch(url)
                if html:
                    _save_cache(cache_key, html)
                    # Archive raw
                    raw_dir = ARCHIVE_DIR / "raw_html" / "baidu"
                    raw_dir.mkdir(parents=True, exist_ok=True)
                    h = hashlib.md5(url.encode()).hexdigest()[:8]
                    (raw_dir / f"baidu_{h}.html").write_text(html, encoding="utf-8")

            if not html:
                continue

            results = _parse_baidu_results(html, query)
            new_results = [r for r in results if r["url"] not in seen_urls]
            for r in new_results:
                seen_urls.add(r["url"])
            all_results.extend(new_results)

            print(f"[Baidu]   Page {page+1}: {len(new_results)} new results")
            time.sleep(random.uniform(CRAWL_DELAY_MIN * 2, CRAWL_DELAY_MAX * 2))

    # Save results
    out_file = OUT_DIR / f"baidu_{timestamp}.json"
    out_file.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")

    # Update master
    master = OUT_DIR / "all_results.json"
    existing = []
    if master.exists():
        try:
            existing = json.loads(master.read_text(encoding="utf-8"))
        except Exception:
            pass
    existing_urls = {r["url"] for r in existing}
    new_only = [r for r in all_results if r["url"] not in existing_urls]
    master.write_text(json.dumps(existing + new_only, ensure_ascii=False, indent=2),
                      encoding="utf-8")

    elapsed = round(time.time() - start, 1)
    summary = {
        "total_results": len(all_results),
        "weixin_found": sum(1 for r in all_results if r["source_type"] == "weixin"),
        "university_found": sum(1 for r in all_results if r["source_type"] == "university"),
        "zhihu_found": sum(1 for r in all_results if r["source_type"] == "zhihu"),
        "elapsed_s": elapsed,
        "output_file": str(out_file),
    }
    print(f"[Baidu Crawler] END — {len(all_results)} results in {elapsed}s")
    print(f"  WeChat: {summary['weixin_found']} | University: {summary['university_found']} | Zhihu: {summary['zhihu_found']}")
    return summary


if __name__ == "__main__":
    run_baidu_crawler()
