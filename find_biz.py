"""
find_biz.py — Auto-discover __biz for PENDING WeChat accounts.

Chạy LOCAL (không phải Railway) vì Sogou block IP nước ngoài:
    python find_biz.py

Kết quả sẽ in __biz cho từng tài khoản. Copy vào monitor/config.py.
Nếu có WECHAT_COOKIE trong env thì dùng cookie đó (tỷ lệ thành công cao hơn).
"""

import os, re, time
import requests
from urllib.parse import quote

PENDING_ACCOUNTS = [
    {"short": "JNU",      "name": "暨南大学华文学院"},
    {"short": "HQU",      "name": "华侨大学华文教育处"},
    {"short": "HKECE",    "name": "香港教育交流中心"},
    {"short": "CAYAUS",   "name": "全美华裔青少年协会"},
    {"short": "CLEF",     "name": "中国华文教育基金会"},
    {"short": "EFCSA",    "name": "欧洲华文教育联合总会"},
    {"short": "ACCSF",    "name": "澳大利亚华文学校联合会"},
    {"short": "DONGZONG", "name": "马来西亚华校董事联合会总会"},
    # CHDEC already has __biz but missing GH ID
    {"short": "CHDEC",    "name": "中国华文教育发展中心"},
]

MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36 "
    "MicroMessenger/8.0.42.2380(0x28002A58) NetType/WIFI Language/zh_CN"
)

def make_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent":      MOBILE_UA,
        "Accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer":         "https://weixin.sogou.com/",
    })
    cookie = os.environ.get("WECHAT_COOKIE", "")
    if cookie:
        s.headers["Cookie"] = cookie
        print("  [cookie mode]")
    return s


def search_sogou_account(name: str, session) -> str | None:
    """Search Sogou type=1 (account search) and extract __biz from result."""
    url = f"https://weixin.sogou.com/weixin?type=1&query={quote(name)}&ie=utf8"
    try:
        resp = session.get(url, timeout=15)
        html = resp.text

        # Pattern 1: profile_ext URL with __biz
        m = re.search(r'__biz=([A-Za-z0-9+/=]+)', html)
        if m:
            return m.group(1)

        # Pattern 2: encoded __biz in href
        m = re.search(r'__biz%3D([A-Za-z0-9%]+)', html)
        if m:
            from urllib.parse import unquote
            return unquote(m.group(1))

        # Pattern 3: sogou redirect URL contains __biz
        m = re.search(r'biz=([A-Za-z0-9+/=]{10,})', html)
        if m:
            return m.group(1)

    except Exception as e:
        print(f"  Sogou error: {e}")
    return None


def search_wx_profile(name: str, session) -> str | None:
    """Try fetching WeChat profile page directly via name search."""
    # WeChat search page (requires cookie for full results)
    url = f"https://mp.weixin.qq.com/cgi-bin/searchbiz?action=search_biz&query={quote(name)}&count=5&begin=0&f=json"
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            lst = data.get("list", [])
            if lst:
                biz = lst[0].get("fakeid", "")
                if biz:
                    return biz
    except Exception:
        pass
    return None


def main():
    print("=" * 60)
    print("WeChat __biz Auto-Discovery")
    print("=" * 60)
    session = make_session()
    results = {}

    for acct in PENDING_ACCOUNTS:
        short = acct["short"]
        name  = acct["name"]
        print(f"\n[{short}] Searching: {name}")

        biz = search_sogou_account(name, session)
        if biz:
            print(f"  ✅ Found via Sogou account search: {biz}")
        else:
            print(f"  ⚠️  Sogou: not found — trying WeChat MP search...")
            biz = search_wx_profile(name, session)
            if biz:
                print(f"  ✅ Found via WeChat MP search: {biz}")
            else:
                print(f"  ❌ Not found — try manually in WeChat app")

        results[short] = biz or "NOT_FOUND"
        time.sleep(2)

    print("\n" + "=" * 60)
    print("RESULTS — paste vào monitor/config.py:")
    print("=" * 60)
    for short, biz in results.items():
        status = "✅" if biz != "NOT_FOUND" else "❌"
        print(f'  {status}  "{short}": "{biz}"')

    # Auto-patch config.py
    found = {k: v for k, v in results.items() if v != "NOT_FOUND"}
    if found:
        print(f"\n{len(found)} BIZ found. Auto-patching monitor/config.py...")
        _patch_config(found)
    else:
        print("\nNo BIZ found automatically. Please find them manually via WeChat app.")
        print("Steps: WeChat app → search account → open profile → Share → Copy link")
        print("The link contains: ...?__biz=XXXXX&...")


def _patch_config(found: dict):
    config_path = "monitor/config.py"
    with open(config_path, encoding="utf-8") as f:
        content = f.read()

    patched = 0
    for short, biz in found.items():
        # Find the account block and replace empty biz
        pattern = rf'("short":\s*"{re.escape(short)}"[^}}]+?"biz":\s*")(")'
        replacement = rf'\g<1>{biz}\g<2>'
        new_content, n = re.subn(pattern, replacement, content, flags=re.DOTALL)
        if n:
            content = new_content
            patched += 1
            print(f"  ✅ Patched {short}: biz={biz}")
        else:
            print(f"  ⚠️  Could not auto-patch {short} — update manually")

    if patched:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\n✅ Saved {patched} updates to {config_path}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    main()
