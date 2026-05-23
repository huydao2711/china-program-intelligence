"""
crawlers/university_crawler.py
Crawl university websites for summer program / international program pages.
Covers: C9, Project 985, OC Specialists, HK, Singapore, joint intl schools.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

import json, re, time, random, hashlib, ssl
import urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path
from config import (
    DATA_DIR, ARCHIVE_DIR, CACHE_TTL_HOURS, UNIVERSITIES,
    UA_CHROME_DESKTOP, CRAWL_DELAY_MIN, CRAWL_DELAY_MAX,
    MAX_RETRIES, REQUEST_TIMEOUT, CONTENT_PREVIEW_LEN
)

OUT_DIR = DATA_DIR / "university"
CACHE_DIR = ARCHIVE_DIR / "cache" / "university"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": UA_CHROME_DESKTOP,
    "Accept": "text/html,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# Additional program-specific URLs beyond university homepages
PROGRAM_URLS = [
    # Confirmed active programs
    {
        "name": "XJTLU High School AI Camp",
        "url": "https://www.xjtlu.edu.cn/en/study/programmes/high-school-programmes",
        "university": "西交利物浦大学",
        "program_type": "ai_camp",
    },
    {
        "name": "Westlake International Science Camp",
        "url": "https://www.westlake.edu.cn/academics/School_of_Science/summerprogram/",
        "university": "西湖大学",
        "program_type": "stem",
    },
    {
        "name": "Tsinghua Global Summer School",
        "url": "https://www.tsinghua.edu.cn/gss/Latest_News.htm",
        "university": "清华大学",
        "program_type": "university",
    },
    {
        "name": "Tsinghua GenAI Summer School 2026",
        "url": "https://ss.cs.tsinghua.edu.cn/",
        "university": "清华大学",
        "program_type": "ai_camp",
    },
    {
        "name": "NPU International Summer Camp",
        "url": "https://npuinternationalcollege.nwpu.edu.cn/info/1146/11168.htm",
        "university": "西北工业大学",
        "program_type": "university",
    },
    {
        "name": "华侨大学华文教育处",
        "url": "https://hjw.hqu.edu.cn/",
        "university": "华侨大学",
        "program_type": "teacher_training",
    },
    {
        "name": "暨南大学华文学院",
        "url": "https://hwy.jnu.edu.cn/",
        "university": "暨南大学",
        "program_type": "overseas_chinese",
    },
    {
        "name": "北京华文学院官网",
        "url": "https://www.bjhwxy.com/",
        "university": "北京华文学院",
        "program_type": "teacher_training",
    },
    {
        "name": "China Chinese Education Network",
        "url": "https://www.hwjyw.com/",
        "university": "中国华文教育网",
        "program_type": "teacher_training",
    },
    {
        "name": "CAYAUS Summer Camp",
        "url": "https://zh.cayaus.org/%E5%AE%9E%E5%9C%B0%E5%A4%8F%E4%BB%A4%E8%90%A5",
        "university": "全美华裔青少年协会",
        "program_type": "cultural",
    },
    {
        "name": "CAIS Summer Camp",
        "url": "https://mp.weixin.qq.com/s/KDncBcfOjCD5omnP6FucOQ",
        "university": "CAIS",
        "program_type": "cultural",
    },
    {
        "name": "中国华文教育基金会",
        "url": "https://www.clef.org.cn/",
        "university": "中国华文教育基金会",
        "program_type": "teacher_training",
    },
    {
        "name": "ADIA Lab Tsinghua AI Summer School",
        "url": "https://www.adialab.ae/summerschool-2026-china",
        "university": "清华大学 + ADIA Lab",
        "program_type": "ai_camp",
    },
]

# Keywords indicating program content on a page
PROGRAM_PAGE_SIGNALS = [
    "夏令营", "暑期", "招生", "报名", "申请", "summer camp", "program",
    "enrollment", "application", "registration", "overseas", "international",
    "camp", "training", "培训", "workshop", "研习", "海外", "华裔", "华文"
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
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=SSL_CTX) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(random.uniform(1, 3))
            else:
                print(f"[University] Fetch failed: {url[:80]} — {e}")
    return None

def _extract_page_info(html: str, source_meta: dict) -> dict:
    """Extract program-relevant info from a university page."""
    # Title
    title_m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
    title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else ""

    # Strip all HTML tags for content
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()

    # Find program mentions
    keywords_found = [kw for kw in PROGRAM_PAGE_SIGNALS if kw.lower() in text.lower()]

    # Find dates (YYYY-MM-DD or Chinese date patterns)
    dates = re.findall(r"20(?:2[4-9]|3[0-9])[-./年]\d{1,2}[-./月]\d{1,2}", text)
    dates = list(set(dates))[:5]

    # Find deadlines
    deadline_context = []
    for m in re.finditer(r".{0,50}(?:截止|deadline|报名).{0,80}", text, re.IGNORECASE):
        deadline_context.append(m.group(0).strip()[:150])

    # Find registration links
    reg_links = re.findall(
        r'href="([^"]*(?:apply|register|enroll|报名|申请)[^"]*)"',
        html, re.IGNORECASE
    )

    return {
        "source": "university",
        "url": source_meta["url"],
        "university": source_meta["university"],
        "program_name": source_meta["name"],
        "program_type": source_meta["program_type"],
        "page_title": title,
        "content_preview": text[:CONTENT_PREVIEW_LEN],
        "keywords_found": keywords_found,
        "dates_mentioned": dates,
        "deadline_context": deadline_context[:3],
        "registration_links": list(set(reg_links))[:5],
        "has_program_content": len(keywords_found) >= 2,
        "fetched_at": datetime.now().isoformat(),
    }


def run_university_crawler() -> dict:
    print("=" * 60)
    print("[University Crawler] START")
    start = time.time()
    all_results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for prog in PROGRAM_URLS:
        print(f"[University] → {prog['name']}")
        cache_key = f"univ_{prog['url']}"
        cached = _load_cache(cache_key)

        if cached:
            result = cached
        else:
            html = _fetch(prog["url"])
            if not html:
                print(f"[University]   FAILED: {prog['url'][:60]}")
                continue

            # Archive
            raw_dir = ARCHIVE_DIR / "raw_html" / "university"
            raw_dir.mkdir(parents=True, exist_ok=True)
            h = hashlib.md5(prog["url"].encode()).hexdigest()[:8]
            (raw_dir / f"univ_{h}.html").write_text(html, encoding="utf-8")

            result = _extract_page_info(html, prog)
            _save_cache(cache_key, result)

        all_results.append(result)
        kw_count = len(result.get("keywords_found", []))
        print(f"[University]   {kw_count} program keywords found")
        time.sleep(random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX))

    # Filter to pages that have relevant content
    relevant = [r for r in all_results if r.get("has_program_content")]

    # Save all
    out_file = OUT_DIR / f"university_{timestamp}.json"
    out_file.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")

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
        "pages_crawled": len(all_results),
        "pages_with_program_content": len(relevant),
        "pages_with_deadlines": sum(1 for r in all_results if r.get("deadline_context")),
        "universities_covered": len(UNIVERSITIES),
        "elapsed_s": elapsed,
        "output_file": str(out_file),
    }
    print(f"[University Crawler] END — {len(all_results)} pages | {len(relevant)} with program content")
    return summary


if __name__ == "__main__":
    run_university_crawler()
