"""
monitor/sources.py — Website + Sogou source crawling.
Python port of Sources.gs
"""

import re, time, hashlib
from datetime import datetime
from urllib.parse import unquote, quote

import requests

from .config import WEBSITE_SOURCES, PROGRAM_KEYWORDS, DEADLINE_KEYWORDS, MONITOR_CONFIG


def _get(url: str, desktop: bool = True) -> str | None:
    ua = MONITOR_CONFIG["DESKTOP_UA"] if desktop else MONITOR_CONFIG["MOBILE_UA"]
    try:
        resp = requests.get(url, headers={
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }, timeout=15, allow_redirects=True)
        if resp.status_code == 200:
            return resp.text
        print(f"[Sources] HTTP {resp.status_code}: {url[:70]}")
    except Exception as e:
        print(f"[Sources] Fetch error {url[:60]}: {e}")
    return None


def _strip_html(html: str) -> str:
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    html = re.sub(r"<style[\s\S]*?</style>",   " ", html, flags=re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html).strip()


def _short_hash(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()[:10]


def _analyze(text: str) -> dict:
    lower = text.lower()
    keywords_found = [kw for kw in PROGRAM_KEYWORDS if kw.lower() in lower]
    has_program = any(kw in lower for kw in [
        "培训", "研习班", "夏令营", "暑期", "招生", "program", "camp", "summer", "enrollment", "寻根"
    ])
    has_deadline = any(kw.lower() in lower for kw in DEADLINE_KEYWORDS)
    return {"keywords_found": keywords_found, "has_program": has_program, "has_deadline": has_deadline}


def _extract_title(html: str) -> str:
    m = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', html, re.I)
    if m:
        return m.group(1).strip()
    m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
    if m:
        return m.group(1).strip()
    m = re.search(r"<h1[^>]*>([\s\S]{3,120}?)</h1>", html, re.I)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return ""


# ── Website source (fingerprint-based change detection) ───────────────────────

def fetch_website_source(source: dict, fingerprint_store: dict) -> dict | None:
    print(f"[Sources] → {source['short']}: {source['url'][:60]}")
    html = _get(source["url"])
    if not html:
        return None

    title   = _extract_title(html)
    text    = _strip_html(html)
    preview = text[:400]
    fp      = _short_hash(text[:2000])
    analysis = _analyze(title + " " + text[:2000])

    relevant = len(analysis["keywords_found"]) >= 2 or analysis["has_deadline"]
    last_fp  = fingerprint_store.get(source["id"], "")
    is_new   = relevant and (fp != last_fp)

    if is_new:
        fingerprint_store[source["id"]] = fp

    return {
        "sourceType":    "Website",
        "accountId":     source["id"],
        "accountName":   source["name"],
        "accountShort":  source["short"],
        "region":        source["region"],
        "title":         title,
        "publishDate":   datetime.now().strftime("%Y-%m-%d"),
        "url":           source["url"],
        "articleId":     _short_hash(source["url"]),
        "content":       preview,
        "hasProgram":    analysis["has_program"],
        "hasDeadline":   analysis["has_deadline"],
        "keywordsFound": analysis["keywords_found"],
        "priority":      "URGENT" if analysis["has_deadline"] else "NORMAL",
        "status":        "NEW" if is_new else "NO_CHANGE",
        "isNew":         is_new,
    }


# ── Sogou search (always returns fresh links) ─────────────────────────────────

def fetch_sogou_source(source: dict) -> list:
    print(f"[Sources] → {source['short']} (Sogou)")
    html = _get(source["url"])
    if not html:
        return []

    results = []
    title_matches   = list(re.finditer(r'<a[^>]+uigs="article_title_\d+"[^>]+href="([^"]+)"[^>]*>([\s\S]*?)</a>', html))
    account_matches = list(re.finditer(r'<span class="account"[^>]*>([\s\S]*?)</span>', html))
    date_matches    = list(re.finditer(r'<span class="s2"[^>]*>([\s\S]*?)</span>', html))
    wx_links        = list(re.finditer(r'url=([^&"\']+mp\.weixin\.qq\.com[^&"\' ]+)', html))

    for i, m in enumerate(title_matches[:8]):
        raw_title  = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        sogou_href = m.group(1)
        account    = account_matches[i].group(1) if i < len(account_matches) else source["short"]
        account    = re.sub(r"<[^>]+>", "", account).strip()
        date_str   = date_matches[i].group(1) if i < len(date_matches) else ""
        date_str   = re.sub(r"<[^>]+>", "", date_str).strip()

        final_url = sogou_href
        if i < len(wx_links):
            try:
                final_url = unquote(wx_links[i].group(1))
            except Exception:
                pass

        art_m = re.search(r"mp\.weixin\.qq\.com/s/([A-Za-z0-9_-]+)", final_url)
        article_id = art_m.group(1) if art_m else _short_hash(final_url)

        analysis = _analyze(raw_title)
        results.append({
            "sourceType":    "Sogou",
            "accountId":     source["id"],
            "accountName":   account or source["name"],
            "accountShort":  source["short"],
            "region":        source["region"],
            "title":         raw_title,
            "publishDate":   date_str,
            "url":           final_url,
            "articleId":     article_id,
            "content":       f"[via Sogou: {source['short']}] {raw_title}"[:300],
            "hasProgram":    analysis["has_program"],
            "hasDeadline":   analysis["has_deadline"],
            "keywordsFound": analysis["keywords_found"],
            "priority":      "URGENT" if analysis["has_deadline"] else "NORMAL",
            "status":        "NEW",
            "isNew":         True,
        })

    print(f"[Sources] {source['short']}: {len(results)} articles")
    return results


# ── Public: run all web sources ───────────────────────────────────────────────

def fetch_all_web_sources(seen_ids: set, fingerprint_store: dict) -> list:
    all_new = []

    for source in WEBSITE_SOURCES:
        try:
            if source["category"] == "sogou_search":
                articles = fetch_sogou_source(source)
                for a in articles:
                    if a["articleId"] not in seen_ids and a["url"] not in seen_ids:
                        all_new.append(a)
                        seen_ids.add(a["articleId"])
                        seen_ids.add(a["url"])
            else:
                result = fetch_website_source(source, fingerprint_store)
                if result and result["isNew"]:
                    all_new.append(result)
            time.sleep(1.2)
        except Exception as e:
            print(f"[Sources] Error on {source['short']}: {e}")

    print(f"[Sources] Total new from web: {len(all_new)}")
    return all_new
