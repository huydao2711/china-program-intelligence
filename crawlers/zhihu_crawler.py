"""
crawlers/zhihu_crawler.py
Crawl Zhihu for participant experiences, reviews, Q&A about programs.
High-value for: real participant outcomes, hidden costs, acceptance rates.
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
    UA_CHROME_DESKTOP, CRAWL_DELAY_MIN, CRAWL_DELAY_MAX,
    MAX_RETRIES, REQUEST_TIMEOUT, CONTENT_PREVIEW_LEN
)

OUT_DIR = DATA_DIR / "zhihu"
CACHE_DIR = ARCHIVE_DIR / "cache" / "zhihu"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

ZHIHU_SEARCH = "https://www.zhihu.com/search?type=content&q={query}&range=year"
ZHIHU_HEADERS = {
    "User-Agent": UA_CHROME_DESKTOP,
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.zhihu.com/",
    "Cookie": os.environ.get("ZHIHU_COOKIE", ""),
}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

ZHIHU_QUERIES = [
    "寻根之旅夏令营 真实体验",
    "海外华裔青少年暑期项目 申请攻略",
    "北京华文学院 AI培训班 怎么样",
    "中国政府资助 海外华裔 夏令营 评价",
    "overseas Chinese summer camp review 2025 2026",
    "华文教师研习班 经验分享",
    "暨南大学 海外华裔 夏令营 录取",
    "清华暑期学校 海外学生 申请经验",
    "西湖大学 国际夏令营 怎么申请",
    "XJTLU AI夏令营 经验",
    "China summer program 海外华人 推荐",
    "华裔二代 寻根 中国 体验 真实感受",
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

def _fetch(url: str) -> str | None:
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers=ZHIHU_HEADERS)
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=SSL_CTX) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(random.uniform(2, 6))
            else:
                print(f"[Zhihu] Fetch failed: {url} — {e}")
    return None

def _parse_zhihu_results(html: str, query: str) -> list[dict]:
    results = []

    # Zhihu search results contain JSON-LD or structured data
    # Try to extract from __NEXT_DATA__ script tag
    next_data_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>([\s\S]*?)</script>', html)
    if next_data_match:
        try:
            data = json.loads(next_data_match.group(1))
            # Navigate to search results
            search_results = (data.get("props", {})
                               .get("pageProps", {})
                               .get("initialState", {})
                               .get("entities", {}))
            # Process answer entities
            for key, val in (search_results.get("answers", {}) or {}).items():
                results.append({
                    "type": "answer",
                    "id": key,
                    "content": str(val.get("content", ""))[:CONTENT_PREVIEW_LEN],
                    "upvotes": val.get("voteupCount", 0),
                    "author": val.get("author", {}).get("name", ""),
                    "url": f"https://www.zhihu.com/question/{val.get('question', {}).get('id', '')}/answer/{key}",
                    "created_at": val.get("createdTime", ""),
                })
            for key, val in (search_results.get("articles", {}) or {}).items():
                results.append({
                    "type": "article",
                    "id": key,
                    "title": val.get("title", ""),
                    "content": str(val.get("excerpt", ""))[:CONTENT_PREVIEW_LEN],
                    "upvotes": val.get("voteupCount", 0),
                    "author": val.get("author", {}).get("name", ""),
                    "url": f"https://zhuanlan.zhihu.com/p/{key}",
                    "created_at": val.get("created", ""),
                })
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    # Fallback: regex-based extraction
    if not results:
        # Extract question links
        q_links = re.findall(r'href="(/question/\d+(?:/answer/\d+)?)"', html)
        article_links = re.findall(r'href="(/p/\d+)"', html)
        titles = re.findall(r'<h2[^>]*>([\s\S]*?)</h2>', html)
        titles = [re.sub(r"<[^>]+>", "", t).strip() for t in titles]

        for i, link in enumerate(q_links[:15]):
            results.append({
                "type": "question_answer",
                "id": link,
                "title": titles[i] if i < len(titles) else "",
                "content": "",
                "upvotes": 0,
                "author": "",
                "url": f"https://www.zhihu.com{link}",
                "created_at": "",
            })
        for i, link in enumerate(article_links[:10]):
            results.append({
                "type": "article",
                "id": link,
                "title": "",
                "content": "",
                "upvotes": 0,
                "author": "",
                "url": f"https://www.zhihu.com{link}",
                "created_at": "",
            })

    # Enrich with metadata
    for r in results:
        r.update({
            "source": "zhihu",
            "query": query,
            "fetched_at": datetime.now().isoformat(),
        })

    return results

def _analyze_sentiment(text: str) -> str:
    """Simple keyword-based sentiment for program reviews."""
    positive = ["推荐", "很好", "不错", "值得", "棒", "优秀", "精彩", "满意",
                 "recommend", "excellent", "great", "amazing", "worth"]
    negative = ["不推荐", "差", "坑", "浪费", "失望", "虚假", "骗",
                 "not recommend", "waste", "disappointing", "scam"]
    text_lower = text.lower()
    pos = sum(1 for w in positive if w in text_lower)
    neg = sum(1 for w in negative if w in text_lower)
    if pos > neg:
        return "POSITIVE"
    elif neg > pos:
        return "NEGATIVE"
    return "NEUTRAL"


def run_zhihu_crawler() -> dict:
    print("=" * 60)
    print("[Zhihu Crawler] START")
    start = time.time()

    all_results = []
    seen_ids = set()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for query in ZHIHU_QUERIES:
        print(f"[Zhihu] Query: {query}")
        url = ZHIHU_SEARCH.format(query=urllib.parse.quote(query))

        cache_key = f"zhihu_{query}"
        html = _load_cache(cache_key)
        if not html:
            html = _fetch(url)
            if html:
                _save_cache(cache_key, html)

        if not html:
            time.sleep(random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX))
            continue

        results = _parse_zhihu_results(html, query)
        new_results = [r for r in results if r.get("id") not in seen_ids]
        for r in new_results:
            if r.get("id"):
                seen_ids.add(r["id"])
            # Add sentiment
            r["sentiment"] = _analyze_sentiment(r.get("content", "") + r.get("title", ""))

        all_results.extend(new_results)
        print(f"[Zhihu]   {len(new_results)} results")
        time.sleep(random.uniform(CRAWL_DELAY_MIN * 1.5, CRAWL_DELAY_MAX * 1.5))

    # Save
    out_file = OUT_DIR / f"zhihu_{timestamp}.json"
    out_file.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")

    # Update master
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
    positive = sum(1 for r in all_results if r.get("sentiment") == "POSITIVE")
    negative = sum(1 for r in all_results if r.get("sentiment") == "NEGATIVE")
    summary = {
        "total_results": len(all_results),
        "positive_sentiment": positive,
        "negative_sentiment": negative,
        "elapsed_s": elapsed,
        "output_file": str(out_file),
    }
    print(f"[Zhihu Crawler] END — {len(all_results)} results | +{positive} -{negative}")
    return summary


if __name__ == "__main__":
    run_zhihu_crawler()
