"""
crawlers/weixin_crawler.py
Crawl WeChat/Weixin: confirmed accounts (BIZ API) + keyword search fallback (Sogou)
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
    UA_WECHAT_MOBILE, CRAWL_DELAY_MIN, CRAWL_DELAY_MAX,
    MAX_RETRIES, REQUEST_TIMEOUT, WEIXIN_ACCOUNTS,
    PROGRAM_KEYWORDS_FLAT, URGENT_KEYWORDS, CONTENT_PREVIEW_LEN
)

OUT_DIR = DATA_DIR / "weixin"
CACHE_DIR = ARCHIVE_DIR / "cache" / "weixin"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SOGOU_ARTICLE_URL = "https://weixin.sogou.com/weixin?type=2&query={query}&tsn=3&page={page}"
WEIXIN_PROFILE_API = "https://mp.weixin.qq.com/mp/profile_ext?action=getmsg&__biz={biz}&f=json&offset={offset}&count=10&is_ok=1"
WEIXIN_ARTICLE_URL = "https://mp.weixin.qq.com/s/{article_id}"

HEADERS_WECHAT = {
    "User-Agent": UA_WECHAT_MOBILE,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://mp.weixin.qq.com/",
}
HEADERS_SOGOU = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://weixin.sogou.com/",
}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


# ── Helpers ───────────────────────────────────────────────────────────────────

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

def _fetch(url: str, headers: dict, retries: int = MAX_RETRIES) -> str | None:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT,
                                        context=SSL_CTX) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX) * (attempt + 1))
            else:
                print(f"[WeChat] Fetch failed after {retries} tries: {url} — {e}")
    return None

def _extract_article_id(url: str) -> str:
    m = re.search(r"mp\.weixin\.qq\.com/s/([A-Za-z0-9_-]+)", url or "")
    return m.group(1) if m else ""

def _load_seen_ids() -> set:
    seen_file = OUT_DIR / "seen_ids.json"
    if seen_file.exists():
        return set(json.loads(seen_file.read_text(encoding="utf-8")))
    return set()

def _save_seen_ids(seen: set):
    seen_file = OUT_DIR / "seen_ids.json"
    seen_file.write_text(json.dumps(sorted(seen), ensure_ascii=False, indent=2),
                         encoding="utf-8")


# ── Content Extraction ────────────────────────────────────────────────────────

def _extract_article_content(html: str) -> dict:
    result = {"title": "", "publish_date": "", "content": "",
              "author": "", "has_program": False, "has_deadline": False,
              "keywords_found": []}

    # Title
    for pattern in [r'var\s+msg_title\s*=\s*"([^"]+)"',
                    r'<meta\s+property="og:title"\s+content="([^"]+)"',
                    r'<title>([^<]+)</title>']:
        m = re.search(pattern, html)
        if m:
            result["title"] = m.group(1).strip()
            break

    # Publish date (Unix timestamp)
    m = re.search(r'var\s+ct\s*=\s*"(\d+)"', html)
    if m:
        result["publish_date"] = datetime.fromtimestamp(int(m.group(1))).strftime("%Y-%m-%d")

    # Author
    m = re.search(r'var\s+nick_name\s*=\s*"([^"]+)"', html)
    if m:
        result["author"] = m.group(1)

    # Body text
    m = re.search(r'<div[^>]+id="js_content"[^>]*>([\s\S]*?)</div>', html)
    if m:
        body = re.sub(r"<[^>]+>", " ", m.group(1))
        body = re.sub(r"\s+", " ", body).strip()
        result["content"] = body[:CONTENT_PREVIEW_LEN]

    # Keyword detection
    text_lower = (result["title"] + " " + result["content"]).lower()
    result["keywords_found"] = [kw for kw in PROGRAM_KEYWORDS_FLAT
                                 if kw.lower() in text_lower]
    program_kws = ["培训", "研习班", "夏令营", "暑期", "招生", "program", "camp", "寻根"]
    result["has_program"] = any(kw.lower() in text_lower for kw in program_kws)
    deadline_kws = ["截止", "deadline", "报名截止", "申请截止", "最后"]
    result["has_deadline"] = any(kw.lower() in text_lower for kw in deadline_kws)

    return result


# ── Account Crawlers ──────────────────────────────────────────────────────────

def fetch_account_via_biz(account: dict, seen_ids: set) -> list[dict]:
    """Fetch recent articles via WeChat profile_ext JSON API."""
    articles = []
    biz = account.get("biz", "")
    if not biz:
        return articles

    cache_key = f"weixin_biz_{biz}"
    cached = _load_cache(cache_key)
    if cached:
        print(f"[WeChat] Cache hit for {account['short']}")
        return [a for a in cached if _extract_article_id(a.get("url","")) not in seen_ids]

    url = WEIXIN_PROFILE_API.format(biz=urllib.parse.quote(biz), offset=0)
    html = _fetch(url, HEADERS_WECHAT)
    if not html:
        return fetch_account_via_html(account, seen_ids)

    try:
        data = json.loads(html)
        if data.get("ret") != 0 or not data.get("msg_list"):
            print(f"[WeChat] API ret={data.get('ret')} for {account['short']} — trying HTML fallback")
            return fetch_account_via_html(account, seen_ids)

        for msg in data["msg_list"]:
            art_url = msg.get("link", "")
            art_id = _extract_article_id(art_url)
            if art_id in seen_ids:
                continue
            articles.append({
                "source": "weixin",
                "account_id": account["id"],
                "account_name": account["name"],
                "account_short": account["short"],
                "region": account["region"],
                "tier": account["tier"],
                "title": msg.get("title", ""),
                "publish_date": datetime.fromtimestamp(msg["datetime"]).strftime("%Y-%m-%d") if msg.get("datetime") else "",
                "url": art_url,
                "article_id": art_id,
                "digest": msg.get("digest", ""),
                "cover": msg.get("cover", ""),
                "content": "",
                "has_program": False,
                "has_deadline": False,
                "keywords_found": [],
                "fetched_at": datetime.now().isoformat(),
            })

        _save_cache(cache_key, articles)
        print(f"[WeChat] {account['short']}: {len(articles)} articles via BIZ API")
    except json.JSONDecodeError:
        print(f"[WeChat] JSON parse error for {account['short']} — trying HTML fallback")
        return fetch_account_via_html(account, seen_ids)

    return articles


def fetch_account_via_html(account: dict, seen_ids: set) -> list[dict]:
    """Fallback: scrape profile HTML page for article links."""
    articles = []
    biz = account.get("biz", "")
    if not biz:
        return articles

    url = f"https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz={urllib.parse.quote(biz)}&scene=124"
    html = _fetch(url, HEADERS_WECHAT)
    if not html:
        return articles

    links = list(set(re.findall(r"https://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+", html)))
    for i, link in enumerate(links[:20]):
        art_id = _extract_article_id(link)
        if art_id in seen_ids:
            continue
        articles.append({
            "source": "weixin",
            "account_id": account["id"],
            "account_name": account["name"],
            "account_short": account["short"],
            "region": account["region"],
            "tier": account["tier"],
            "title": "",
            "publish_date": "",
            "url": link,
            "article_id": art_id,
            "digest": "",
            "cover": "",
            "content": "",
            "has_program": False,
            "has_deadline": False,
            "keywords_found": [],
            "fetched_at": datetime.now().isoformat(),
        })

    print(f"[WeChat HTML] {account['short']}: {len(articles)} links")
    return articles


def fetch_article_content(article: dict) -> dict:
    """Enrich article with full content fetched from article URL."""
    url = article.get("url", "")
    if not url:
        return article

    cache_key = f"weixin_article_{article.get('article_id','')}"
    cached = _load_cache(cache_key)
    if cached:
        article.update(cached)
        return article

    html = _fetch(url, HEADERS_WECHAT)
    if not html:
        return article

    # Archive raw HTML
    if article.get("article_id"):
        raw_dir = ARCHIVE_DIR / "raw_html" / "weixin"
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / f"{article['article_id']}.html").write_text(html, encoding="utf-8")

    content_data = _extract_article_content(html)
    if content_data["title"]:
        article["title"] = content_data["title"]
    if content_data["publish_date"]:
        article["publish_date"] = content_data["publish_date"]
    if content_data["author"]:
        article["account_name"] = content_data["author"]
    article["content"] = content_data["content"]
    article["has_program"] = content_data["has_program"]
    article["has_deadline"] = content_data["has_deadline"]
    article["keywords_found"] = content_data["keywords_found"]

    _save_cache(cache_key, {
        "title": article["title"], "publish_date": article["publish_date"],
        "content": article["content"], "has_program": article["has_program"],
        "has_deadline": article["has_deadline"], "keywords_found": article["keywords_found"],
    })
    return article


# ── Keyword Search via Sogou ──────────────────────────────────────────────────

def search_sogou_for_keywords(keywords: list[str], pages: int = 2) -> list[dict]:
    """Search WeChat articles via Sogou for accounts without BIZ."""
    all_articles = []
    seen_urls = set()

    for kw in keywords:
        for page in range(1, pages + 1):
            url = SOGOU_ARTICLE_URL.format(query=urllib.parse.quote(kw), page=page)
            cache_key = f"sogou_{kw}_{page}"
            cached = _load_cache(cache_key)

            if cached:
                html = cached
            else:
                html = _fetch(url, HEADERS_SOGOU)
                if html:
                    _save_cache(cache_key, html)

            if not html:
                continue

            # Extract article links from Sogou results
            link_pattern = r'https?://mp\.weixin\.qq\.com/s(?:/|\?[^"\'<\s]*)[A-Za-z0-9_=&%.-]+'
            links = re.findall(link_pattern, html)

            # Extract account names from Sogou HTML
            account_names = re.findall(
                r'<span class="account">(.*?)</span>', html, re.DOTALL)
            account_names = [re.sub(r"<[^>]+>", "", n).strip() for n in account_names]

            # Extract titles
            titles = re.findall(
                r'<a[^>]+uigs="article_title_\d+"[^>]*>(.*?)</a>', html, re.DOTALL)
            titles = [re.sub(r"<[^>]+>", "", t).strip() for t in titles]

            for i, link in enumerate(links[:10]):
                clean_link = link.split('"')[0].split("'")[0]
                if clean_link in seen_urls:
                    continue
                seen_urls.add(clean_link)
                art_id = _extract_article_id(clean_link)

                all_articles.append({
                    "source": "weixin_sogou",
                    "account_id": "SOGOU_SEARCH",
                    "account_name": account_names[i] if i < len(account_names) else "",
                    "account_short": "SEARCH",
                    "region": "Unknown",
                    "tier": 99,
                    "title": titles[i] if i < len(titles) else "",
                    "publish_date": "",
                    "url": clean_link,
                    "article_id": art_id,
                    "digest": "",
                    "cover": "",
                    "content": "",
                    "has_program": True,
                    "has_deadline": False,
                    "keywords_found": [kw],
                    "search_keyword": kw,
                    "fetched_at": datetime.now().isoformat(),
                })

            time.sleep(random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX))

    print(f"[Sogou] Found {len(all_articles)} articles via keyword search")
    return all_articles


# ── Main Crawler ──────────────────────────────────────────────────────────────

def run_weixin_crawler(
    fetch_content: bool = True,
    keyword_search: bool = True,
    keyword_pages: int = 2
) -> dict:
    print("=" * 60)
    print("[WeChat Crawler] START")
    start = time.time()

    seen_ids = _load_seen_ids()
    all_articles = []

    # 1. Confirmed BIZ accounts
    confirmed = [a for a in WEIXIN_ACCOUNTS if a["status"] == "CONFIRMED"]
    for account in confirmed:
        print(f"[WeChat] → {account['short']} (BIZ confirmed)")
        articles = fetch_account_via_biz(account, seen_ids)
        all_articles.extend(articles)
        time.sleep(random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX))

    # 2. Pending BIZ — try with tentative BIZ code
    pending_with_biz = [a for a in WEIXIN_ACCOUNTS if a["status"] == "PENDING" and a.get("biz")]
    for account in pending_with_biz:
        print(f"[WeChat] → {account['short']} (BIZ tentative)")
        articles = fetch_account_via_biz(account, seen_ids)
        all_articles.extend(articles)
        time.sleep(random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX))

    # 3. Keyword search for remaining pending accounts
    if keyword_search:
        all_keywords = []
        for account in WEIXIN_ACCOUNTS:
            if account["status"] == "PENDING":
                all_keywords.extend(account.get("keywords", []))
        all_keywords = list(set(all_keywords))
        sogou_articles = search_sogou_for_keywords(all_keywords[:10], pages=keyword_pages)
        # Filter to only new ones
        sogou_new = [a for a in sogou_articles
                     if _extract_article_id(a["url"]) not in seen_ids]
        all_articles.extend(sogou_new)

    # 4. Fetch full content for new articles
    if fetch_content:
        enriched = []
        for i, article in enumerate(all_articles):
            print(f"[WeChat] Fetching content {i+1}/{len(all_articles)}: {article.get('article_id','')}")
            enriched.append(fetch_article_content(article))
            time.sleep(random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX))
        all_articles = enriched

    # 5. Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = OUT_DIR / f"weixin_{timestamp}.json"
    out_file.write_text(json.dumps(all_articles, ensure_ascii=False, indent=2), encoding="utf-8")

    # Update seen IDs
    for a in all_articles:
        aid = _extract_article_id(a.get("url", ""))
        if aid:
            seen_ids.add(aid)
    _save_seen_ids(seen_ids)

    # Update master index
    master = OUT_DIR / "all_articles.json"
    existing = []
    if master.exists():
        try:
            existing = json.loads(master.read_text(encoding="utf-8"))
        except Exception:
            pass
    existing_ids = {_extract_article_id(a.get("url","")) for a in existing}
    new_only = [a for a in all_articles if _extract_article_id(a.get("url","")) not in existing_ids]
    master.write_text(json.dumps(existing + new_only, ensure_ascii=False, indent=2), encoding="utf-8")

    elapsed = round(time.time() - start, 1)
    summary = {
        "new_articles": len(all_articles),
        "urgent": sum(1 for a in all_articles if a.get("has_deadline")),
        "with_program": sum(1 for a in all_articles if a.get("has_program")),
        "elapsed_s": elapsed,
        "output_file": str(out_file),
    }
    print(f"[WeChat Crawler] END — {len(all_articles)} new articles in {elapsed}s")
    return summary


if __name__ == "__main__":
    run_weixin_crawler()
