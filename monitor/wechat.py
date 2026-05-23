"""
monitor/wechat.py — WeChat account monitoring.
Python port of WeChat.gs + Sogou fallback.
"""

import os, re, time, json, hashlib
from datetime import datetime
from urllib.parse import quote, unquote

import requests

from .config import MONITOR_CONFIG, PROGRAM_KEYWORDS, DEADLINE_KEYWORDS


def _session():
    s = requests.Session()
    s.headers.update({
        "User-Agent":      MONITOR_CONFIG["MOBILE_UA"],
        "Accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer":         "https://mp.weixin.qq.com/",
    })
    cookie = os.environ.get("WECHAT_COOKIE", "")
    if cookie:
        s.headers["Cookie"] = cookie
        print("[WeChat] Cookie loaded — authenticated mode")
    else:
        print("[WeChat] No cookie — anonymous mode (BIZ API may fail)")
    return s


def _short_id(url: str) -> str:
    m = re.search(r"mp\.weixin\.qq\.com/s/([A-Za-z0-9_-]+)", url)
    if m:
        return m.group(1)
    return hashlib.md5(url.encode()).hexdigest()[:10]


def _analyze(text: str) -> dict:
    lower = text.lower()
    keywords_found = [kw for kw in PROGRAM_KEYWORDS if kw.lower() in lower]
    has_program = any(kw in lower for kw in [
        "培训", "研习班", "夏令营", "暑期", "招生", "program", "camp", "summer", "enrollment", "寻根"
    ])
    has_deadline = any(kw.lower() in lower for kw in DEADLINE_KEYWORDS)
    return {"keywords_found": keywords_found, "has_program": has_program, "has_deadline": has_deadline}


# ── BIZ JSON API ──────────────────────────────────────────────────────────────

def _fetch_via_biz(account: dict, session) -> list:
    url = MONITOR_CONFIG["WECHAT_PROFILE_API"].format(biz=account["biz"], offset=0)
    try:
        resp = session.get(url, timeout=15)
        data = resp.json()
        raw = data.get("general_msg_list", "{}")
        msgs = json.loads(raw) if isinstance(raw, str) else raw
        items = msgs.get("list", [])
    except Exception as e:
        print(f"[WeChat] BIZ API error {account['short']}: {e}")
        return []

    articles = []
    for item in items[:10]:
        comm = item.get("comm_msg_info", {})
        app  = item.get("app_msg_ext_info", {})
        url  = app.get("content_url", "").replace("\\u0026", "&")
        if not url:
            continue
        ts = comm.get("datetime", 0)
        pub_date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else ""
        analysis = _analyze(app.get("title", "") + " " + app.get("digest", ""))
        articles.append({
            "sourceType":    "WeChat",
            "accountId":     account["id"],
            "accountName":   account["name"],
            "accountShort":  account["short"],
            "region":        account["region"],
            "title":         app.get("title", ""),
            "publishDate":   pub_date,
            "url":           url,
            "articleId":     _short_id(url),
            "content":       app.get("digest", "")[:300],
            "hasProgram":    analysis["has_program"],
            "hasDeadline":   analysis["has_deadline"],
            "keywordsFound": analysis["keywords_found"],
            "status":        "NEW",
        })
    return articles


# ── Full article content ──────────────────────────────────────────────────────

def fetch_article_content(url: str, session) -> dict:
    try:
        resp = session.get(url, timeout=15)
        html = resp.text

        # Title
        title = ""
        m = re.search(r"var\s+msg_title\s*=\s*\"([^\"]+)\"", html)
        if m:
            title = m.group(1)
        else:
            m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
            if m:
                title = m.group(1).strip()

        # Publish date
        pub_date = ""
        m = re.search(r"var\s+ct\s*=\s*\"(\d+)\"", html)
        if m:
            pub_date = datetime.fromtimestamp(int(m.group(1))).strftime("%Y-%m-%d")

        # Content
        m = re.search(r'id="js_content"[^>]*>([\s\S]{50,5000}?)</div>', html)
        content = ""
        if m:
            content = re.sub(r"<[^>]+>", " ", m.group(1))
            content = re.sub(r"\s+", " ", content).strip()[:500]

        analysis = _analyze(title + " " + content)
        return {
            "title":         title,
            "publishDate":   pub_date,
            "content":       content,
            "hasProgram":    analysis["has_program"],
            "hasDeadline":   analysis["has_deadline"],
            "keywordsFound": analysis["keywords_found"],
        }
    except Exception as e:
        print(f"[WeChat] Content fetch error: {e}")
        return {"title": "", "publishDate": "", "content": "", "hasProgram": False, "hasDeadline": False, "keywordsFound": []}


# ── Sogou fallback ────────────────────────────────────────────────────────────

def _fetch_via_sogou(account: dict, session) -> list:
    kws = account.get("keywords", [])[:3]
    query = " ".join(kws)
    url = f"https://weixin.sogou.com/weixin?type=2&query={quote(query)}&tsn=3"
    try:
        resp = session.get(url, timeout=15)
        html = resp.text
    except Exception as e:
        print(f"[WeChat] Sogou error {account['short']}: {e}")
        return []

    results = []
    title_matches   = list(re.finditer(r'<a[^>]+uigs="article_title_\d+"[^>]+href="([^"]+)"[^>]*>([\s\S]*?)</a>', html))
    account_matches = list(re.finditer(r'<span class="account"[^>]*>([\s\S]*?)</span>', html))
    date_matches    = list(re.finditer(r'<span class="s2"[^>]*>([\s\S]*?)</span>', html))
    wx_links        = list(re.finditer(r'url=([^&"\']+mp\.weixin\.qq\.com[^&"\' ]+)', html))

    for i, m in enumerate(title_matches[:8]):
        raw_title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        sogou_href = m.group(1)
        acct = account_matches[i].group(1) if i < len(account_matches) else account["short"]
        acct = re.sub(r"<[^>]+>", "", acct).strip()
        date_str = date_matches[i].group(1) if i < len(date_matches) else ""
        date_str = re.sub(r"<[^>]+>", "", date_str).strip()

        final_url = sogou_href
        if i < len(wx_links):
            try:
                final_url = unquote(wx_links[i].group(1))
            except Exception:
                pass

        analysis = _analyze(raw_title)
        results.append({
            "sourceType":    "WeChat",
            "accountId":     account["id"],
            "accountName":   acct or account["name"],
            "accountShort":  account["short"],
            "region":        account["region"],
            "title":         raw_title,
            "publishDate":   date_str,
            "url":           final_url,
            "articleId":     _short_id(final_url),
            "content":       f"[via Sogou: {account['short']}] {raw_title}"[:300],
            "hasProgram":    analysis["has_program"],
            "hasDeadline":   analysis["has_deadline"],
            "keywordsFound": analysis["keywords_found"],
            "status":        "NEW",
        })
    return results


# ── Public: fetch all accounts ────────────────────────────────────────────────

def fetch_all_accounts(seen_ids: set) -> list:
    from .config import ACCOUNTS
    session = _session()
    all_new = []

    for account in ACCOUNTS:
        print(f"[WeChat] Checking {account['short']} ({account['status']})")
        try:
            if account["status"] == "CONFIRMED" and account.get("biz"):
                articles = _fetch_via_biz(account, session)
            else:
                articles = _fetch_via_sogou(account, session)

            for art in articles:
                if art["articleId"] in seen_ids or art["url"] in seen_ids:
                    continue
                # Fetch full content for confirmed accounts
                if account["status"] == "CONFIRMED" and art["url"]:
                    detail = fetch_article_content(art["url"], session)
                    if detail["title"]:
                        art["title"] = detail["title"]
                    if detail["publishDate"]:
                        art["publishDate"] = detail["publishDate"]
                    art["content"]       = detail["content"]
                    art["hasProgram"]    = detail["has_program"]
                    art["hasDeadline"]   = detail["has_deadline"]
                    art["keywordsFound"] = detail["keywords_found"]
                    time.sleep(1.0)

                all_new.append(art)
                seen_ids.add(art["articleId"])
                seen_ids.add(art["url"])

            time.sleep(1.5)
        except Exception as e:
            print(f"[WeChat] Error on {account['short']}: {e}")

    print(f"[WeChat] Total new: {len(all_new)}")
    return all_new
