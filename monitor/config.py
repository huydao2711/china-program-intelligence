"""
monitor/config.py — All configuration for the daily WeChat + Web monitor.
Python port of Google Apps Script Config.gs
"""

MONITOR_CONFIG = {
    "EMAIL":       "daohuy27112000@gmail.com",
    "SHEET_NAME":  "WeChat Monitor Log",
    "TRIGGER_HOUR": 7,

    "MOBILE_UA": (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36 "
        "MicroMessenger/8.0.42.2380(0x28002A58) NetType/WIFI Language/zh_CN"
    ),
    "DESKTOP_UA": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),

    "WECHAT_PROFILE_API": (
        "https://mp.weixin.qq.com/mp/profile_ext"
        "?action=getmsg&__biz={biz}&f=json&offset={offset}&count=10&is_ok=1"
    ),

    "URGENT_KEYWORDS": [
        "截止", "最后", "deadline", "last day",
        "报名截止", "即将", "今日", "明日"
    ],
}

# ── WeChat Accounts ────────────────────────────────────────────────────────────
ACCOUNTS = [
    # TIER 1 — Confirmed BIZ
    {
        "id": "gh_89d74baa0e3c", "biz": "MzkxNTM0Njg4MQ==",
        "name": "加拿大华文学校联合总会 (FCSC Canada)", "short": "FCSC",
        "region": "North America", "status": "CONFIRMED", "priority": "HIGH",
        "programs": ["华文教师研习班", "校长研习班"],
        "keywords": ["报名", "申请", "截止", "研习班", "培训", "夏令营", "registration", "deadline"],
    },
    {
        "id": "gh_157acda58ca4", "biz": "MjM5NjY0MTk5NQ==",
        "name": "北京华文学院", "short": "BCL",
        "region": "China", "status": "CONFIRMED", "priority": "HIGH",
        "programs": ["AI华文教育培训班", "华文教师研习班"],
        "keywords": ["AI", "人工智能", "培训", "招生", "通知", "报名", "截止", "研习班"],
    },
    # TIER 2 — BIZ Pending
    {
        "id": "PENDING", "biz": "MjM5NTA1NjE3NQ==",
        "name": "中国华文教育发展中心 (CHDEC)", "short": "CHDEC",
        "region": "China", "status": "PENDING", "priority": "CRITICAL",
        "programs": ["全部项目"],
        "keywords": ["华文教师", "研习班", "校长", "通知", "招募", "培训班", "报名", "选拔"],
    },
    {
        "id": "PENDING", "biz": "MzIxMjg4NDY4Ng==",
        "name": "暨南大学华文学院", "short": "JNU",
        "region": "China", "status": "PENDING", "priority": "HIGH",
        "programs": ["寻根之旅", "华裔青少年夏令营"],
        "keywords": ["寻根之旅", "夏令营", "华裔", "海外", "报名", "招募", "暑期"],
    },
    {
        "id": "PENDING", "biz": "",
        "name": "华侨大学华文教育处", "short": "HQU",
        "region": "China", "status": "PENDING", "priority": "HIGH",
        "programs": ["华文教师培训", "国际中文教育"],
        "keywords": ["华文教育", "培训", "海外", "教师", "招生", "奖学金"],
    },
    {
        "id": "PENDING", "biz": "",
        "name": "香港教育交流中心", "short": "HKECE",
        "region": "Hong Kong", "status": "PENDING", "priority": "MEDIUM",
        "programs": ["寻根之旅夏令营 2026"],
        "keywords": ["寻根之旅", "夏令营", "香港", "海外华裔", "报名"],
    },
    {
        "id": "PENDING", "biz": "",
        "name": "全美华裔青少年协会 (CAYAUS)", "short": "CAYAUS",
        "region": "North America", "status": "PENDING", "priority": "MEDIUM",
        "programs": ["寻根之旅美国区"],
        "keywords": ["夏令营", "美国", "华裔", "青少年", "报名", "camp"],
    },
    {
        "id": "PENDING", "biz": "",
        "name": "中国华文教育基金会 (CLEF)", "short": "CLEF",
        "region": "China", "status": "PENDING", "priority": "MEDIUM",
        "programs": ["华文教育奖学金"],
        "keywords": ["基金会", "奖学金", "资助", "华文教育", "申请"],
    },
    {
        "id": "PENDING", "biz": "",
        "name": "欧洲华文教育联合总会 (EFCSA)", "short": "EFCSA",
        "region": "Europe", "status": "PENDING", "priority": "MEDIUM",
        "programs": ["欧洲华文教师培训"],
        "keywords": ["欧洲", "华文", "教育", "培训", "夏令营", "报名"],
    },
    {
        "id": "PENDING", "biz": "",
        "name": "澳大利亚华文学校联合会", "short": "ACCSF",
        "region": "Oceania", "status": "PENDING", "priority": "MEDIUM",
        "programs": ["澳洲华文教师培训"],
        "keywords": ["澳大利亚", "华文", "学校", "培训", "报名"],
    },
    {
        "id": "PENDING", "biz": "",
        "name": "马来西亚华校董事联合会总会 (DONGZONG)", "short": "DONGZONG",
        "region": "Southeast Asia", "status": "PENDING", "priority": "MEDIUM",
        "programs": ["马来西亚华文教育"],
        "keywords": ["马来西亚", "华文", "董总", "教育", "培训", "奖学金"],
    },
]

# ── Website Sources ────────────────────────────────────────────────────────────
WEBSITE_SOURCES = [
    # Government / OC agencies
    {"id": "WEB_HWJYW",   "name": "中国华文教育网",      "short": "HWJYW",     "region": "China",         "category": "government",    "url": "https://www.hwjyw.com/"},
    {"id": "WEB_CLEF",    "name": "中国华文教育基金会",   "short": "CLEF",      "region": "China",         "category": "government",    "url": "https://www.clef.org.cn/"},
    {"id": "WEB_BCL",     "name": "北京华文学院官网",     "short": "BCL-WEB",   "region": "China",         "category": "oc_university", "url": "https://www.bjhwxy.com/"},
    {"id": "WEB_JNU",     "name": "暨南大学华文学院",     "short": "JNU-WEB",   "region": "China",         "category": "oc_university", "url": "https://hwy.jnu.edu.cn/"},
    {"id": "WEB_HQU",     "name": "华侨大学华文教育处",   "short": "HQU-WEB",   "region": "China",         "category": "oc_university", "url": "https://hjw.hqu.edu.cn/"},
    # Elite universities
    {"id": "WEB_THU_GSS", "name": "清华全球暑期学校",     "short": "THU-GSS",   "region": "China",         "category": "elite_university", "url": "https://www.tsinghua.edu.cn/gss/Latest_News.htm"},
    {"id": "WEB_THU_AI",  "name": "清华GenAI暑期学校",   "short": "THU-AI",    "region": "China",         "category": "elite_university", "url": "https://ss.cs.tsinghua.edu.cn/"},
    {"id": "WEB_WLU",     "name": "西湖大学国际科学营",   "short": "WLU-WEB",   "region": "China",         "category": "elite_university", "url": "https://en.westlake.edu.cn/admissions/summer_sessions/international_science_summer_school/"},
    {"id": "WEB_XJTLU",   "name": "XJTLU AI高中营",      "short": "XJTLU-WEB", "region": "China",         "category": "joint_intl",    "url": "https://www.xjtlu.edu.cn/en/learning-mall/learning-resources/xjtlu-high-school-summer-camp"},
    {"id": "WEB_NPU",     "name": "西北工业大学国际夏令营","short": "NPU-WEB",   "region": "China",         "category": "elite_university", "url": "https://npuinternationalcollege.nwpu.edu.cn/info/1146/11168.htm"},
    # Overseas
    {"id": "WEB_CAYAUS",  "name": "全美华裔青少年协会",   "short": "CAYAUS-WEB","region": "North America", "category": "diaspora",      "url": "https://zh.cayaus.org/%E5%AE%9E%E5%9C%B0%E5%A4%8F%E4%BB%A4%E8%90%A5"},
    {"id": "WEB_CAMPC",   "name": "北美华人寻根夏令营",   "short": "CAMPC",     "region": "North America", "category": "diaspora",      "url": "https://www.campofchina.org/"},
    # Sogou searches
    {"id": "SOGOU_XGZ",   "name": "Sogou: 寻根之旅2026",         "short": "SOGOU-XGZ", "region": "Search", "category": "sogou_search", "url": "https://weixin.sogou.com/weixin?type=2&query=%E5%AF%BB%E6%A0%B9%E4%B9%8B%E6%97%85+2026&tsn=3"},
    {"id": "SOGOU_HW",    "name": "Sogou: 华文教师研习班2026",   "short": "SOGOU-HW",  "region": "Search", "category": "sogou_search", "url": "https://weixin.sogou.com/weixin?type=2&query=%E5%8D%8E%E6%96%87%E6%95%99%E5%B8%88%E7%A0%94%E4%B9%A0%E7%8F%AD+2026&tsn=3"},
    {"id": "SOGOU_AI",    "name": "Sogou: AI华文教育2026",        "short": "SOGOU-AI",  "region": "Search", "category": "sogou_search", "url": "https://weixin.sogou.com/weixin?type=2&query=AI%E5%8D%8E%E6%96%87%E6%95%99%E8%82%B2+2026&tsn=3"},
    {"id": "SOGOU_HZ",    "name": "Sogou: 海外华裔夏令营2026",   "short": "SOGOU-HZ",  "region": "Search", "category": "sogou_search", "url": "https://weixin.sogou.com/weixin?type=2&query=%E6%B5%B7%E5%A4%96%E5%8D%8E%E8%A3%94%E5%A4%8F%E4%BB%A4%E8%90%A5+2026&tsn=3"},
]

# ── Program Deadlines ──────────────────────────────────────────────────────────
PROGRAM_DEADLINES = [
    {"program": "AI华文教育培训班 (P006)",          "deadline": "2026-06-30", "days_warn": 14, "url": "https://mp.weixin.qq.com/s/4hnWcECgsNKcfPfUc2Gb9w"},
    {"program": "华文教师研习班 (P003) — Canada",   "deadline": "2026-05-31", "days_warn": 7,  "url": "https://mp.weixin.qq.com/s/rdvA_QyvbB43lXlCuWlEmg"},
    {"program": "清华全球暑期学校 2026",             "deadline": "2026-06-15", "days_warn": 14, "url": "https://www.tsinghua.edu.cn/gss/Latest_News.htm"},
    {"program": "XJTLU AI高中营 2026",              "deadline": "2026-07-01", "days_warn": 14, "url": "https://www.xjtlu.edu.cn/en/learning-mall/learning-resources/xjtlu-high-school-summer-camp"},
    {"program": "西湖大学国际科学营 2026",           "deadline": "2026-06-20", "days_warn": 14, "url": "https://en.westlake.edu.cn/admissions/summer_sessions/international_science_summer_school/"},
]

# ── Keyword sets ───────────────────────────────────────────────────────────────
PROGRAM_KEYWORDS = [
    "夏令营", "暑期", "招生", "报名", "申请", "截止", "通知", "AI", "人工智能",
    "培训", "研习班", "寻根", "华裔", "华文", "教师", "海外", "奖学金",
    "camp", "summer", "program", "application", "deadline", "registration",
    "open", "international", "overseas", "scholarship", "enrollment",
]

DEADLINE_KEYWORDS = [
    "截止", "最后", "deadline", "last day", "报名截止", "申请截止",
    "即将", "今日", "明日", "closing", "closes", "apply by", "due",
]

SHEET_HEADERS = [
    "Priority",        # A — URGENT / NORMAL (hiển thị đầu tiên)
    "Deadline",        # B — TRUE/FALSE
    "Program",         # C — TRUE/FALSE
    "Title",           # D — tên bài / trang
    "Source",          # E — tên ngắn tổ chức
    "Type",            # F — WeChat / Website / Sogou
    "Region",          # G — khu vực
    "Date",            # H — ngày đăng
    "Keywords",        # I — từ khóa khớp
    "Preview",         # J — tóm tắt nội dung
    "URL",             # K — link gốc
    "Timestamp",       # L — thời điểm ghi
    "Notes",           # M — ghi chú thủ công
]
