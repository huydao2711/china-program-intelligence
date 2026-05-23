"""
config.py — Central configuration for China Program Intelligence Platform
"""

import os
from pathlib import Path

# ── Base Paths ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
CRAWLERS_DIR   = BASE_DIR / "crawlers"
AGENTS_DIR     = BASE_DIR / "agents"
DATA_DIR       = BASE_DIR / "extracted_data"
UNIVERSITY_DB  = BASE_DIR / "university_db"
PROGRAM_DB     = BASE_DIR / "program_db"
SOCIAL_DIR     = BASE_DIR / "social_analysis"
ECOSYSTEM_DIR  = BASE_DIR / "ecosystem_mapping"
PREDICTIONS_DIR= BASE_DIR / "predictions"
VIZ_DIR        = BASE_DIR / "visualizations"
REPORTS_DIR    = BASE_DIR / "reports"
ARCHIVE_DIR    = BASE_DIR / "archives"
LOGS_DIR       = BASE_DIR / "logs"

# ── API Keys (set as environment variables) ───────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ── AI Model ──────────────────────────────────────────────────────────────────
AI_MODEL = "claude-opus-4-7"

# ── Anti-Bot User Agents ──────────────────────────────────────────────────────
UA_WECHAT_MOBILE = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36 "
    "MicroMessenger/8.0.42.2380(0x28002A58) NetType/WIFI Language/zh_CN"
)
UA_CHROME_DESKTOP = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
UA_CHROME_MOBILE = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
)

# ── WeChat Accounts to Monitor ────────────────────────────────────────────────
WEIXIN_ACCOUNTS = [
    # TIER 1 — CONFIRMED BIZ (active)
    {
        "id": "gh_89d74baa0e3c", "biz": "MzkxNTM0Njg4MQ==",
        "name": "加拿大华文学校联合总会 (FCSC Canada)",
        "short": "FCSC", "region": "North America", "tier": 1, "status": "CONFIRMED",
        "programs": ["华文教师研习班", "校长研习班"],
        "keywords": ["报名", "申请", "截止", "通知", "研习班", "培训", "夏令营"]
    },
    {
        "id": "gh_157acda58ca4", "biz": "MjM5NjY0MTk5NQ==",
        "name": "北京华文学院",
        "short": "BCL", "region": "China", "tier": 1, "status": "CONFIRMED",
        "programs": ["AI华文教育培训班", "华文教师研习班"],
        "keywords": ["AI", "人工智能", "培训", "招生", "通知", "报名", "截止"]
    },
    # TIER 2 — BIZ PENDING (use keyword search fallback)
    {
        "id": "PENDING", "biz": "MjM5NTA1NjE3NQ==",  # tentative BIZ from search
        "name": "中国华文教育发展中心 (CHDEC)",
        "short": "CHDEC", "region": "China", "tier": 2, "status": "PENDING",
        "programs": ["ALL"],
        "keywords": ["华文教师", "研习班", "校长", "通知", "招募", "培训班", "报名"]
    },
    {
        "id": "PENDING", "biz": "",
        "name": "暨南大学华文学院",
        "short": "JNU", "region": "China", "tier": 2, "status": "PENDING",
        "programs": ["寻根之旅", "华裔青少年夏令营"],
        "keywords": ["寻根之旅", "夏令营", "华裔", "海外", "报名", "招募", "暑期"]
    },
    {
        "id": "PENDING", "biz": "",
        "name": "华侨大学华文教育处",
        "short": "HQU", "region": "China", "tier": 2, "status": "PENDING",
        "programs": ["华文教师培训", "国际中文教育"],
        "keywords": ["华文教育", "培训", "海外", "教师", "招生", "奖学金"]
    },
    {
        "id": "PENDING", "biz": "",
        "name": "香港教育交流中心",
        "short": "HKECE", "region": "Hong Kong", "tier": 2, "status": "PENDING",
        "programs": ["寻根之旅夏令营"],
        "keywords": ["寻根之旅", "夏令营", "香港", "海外华裔", "报名"]
    },
    # TIER 3 — REGIONAL
    {
        "id": "PENDING", "biz": "",
        "name": "全美华裔青少年协会 (CAYAUS)",
        "short": "CAYAUS", "region": "North America", "tier": 3, "status": "PENDING",
        "programs": ["寻根之旅美国区"],
        "keywords": ["夏令营", "美国", "华裔", "青少年", "报名"]
    },
    {
        "id": "PENDING", "biz": "",
        "name": "欧洲华文教育联合总会 (EFCSA)",
        "short": "EFCSA", "region": "Europe", "tier": 3, "status": "PENDING",
        "programs": ["欧洲华文教师培训"],
        "keywords": ["欧洲", "华文", "教育", "培训", "夏令营", "报名"]
    },
    {
        "id": "PENDING", "biz": "",
        "name": "澳大利亚华文学校联合会",
        "short": "ACCSF", "region": "Oceania", "tier": 3, "status": "PENDING",
        "programs": ["澳洲华文教师培训"],
        "keywords": ["澳大利亚", "华文", "学校", "教育", "培训", "报名"]
    },
    {
        "id": "PENDING", "biz": "",
        "name": "马来西亚华校董事联合会总会 (DONGZONG)",
        "short": "DONGZONG", "region": "Southeast Asia", "tier": 3, "status": "PENDING",
        "programs": ["马来西亚华文教育"],
        "keywords": ["马来西亚", "华文", "董总", "教育", "培训", "奖学金"]
    },
    {
        "id": "PENDING", "biz": "",
        "name": "中国华文教育基金会 (CLEF)",
        "short": "CLEF", "region": "China", "tier": 3, "status": "PENDING",
        "programs": ["华文教育奖学金"],
        "keywords": ["基金会", "奖学金", "资助", "华文教育", "申请"]
    },
]

# ── Program Search Keywords (Chinese + English) ───────────────────────────────
PROGRAM_KEYWORDS = {
    "summer_camp":      ["夏令营", "暑期营", "summer camp", "暑假营", "冬令营"],
    "exchange":         ["交流项目", "exchange program", "国际交流", "文化交流", "访问学者"],
    "youth_innovation": ["青年创新", "youth innovation", "创新营", "创客营", "创新实验"],
    "ai_camp":          ["AI营", "人工智能", "AI camp", "AI夏令营", "机器人", "robotics"],
    "entrepreneurship": ["创业营", "entrepreneurship", "创业训练营", "商业训练营", "startup camp"],
    "university":       ["大学体验", "university immersion", "校园体验", "大学营", "学术营"],
    "leadership":       ["领袖营", "leadership", "领导力", "精英计划", "领导力训练"],
    "scholarship":      ["奖学金营", "scholarship", "奖学金夏令营", "资助项目", "全额资助"],
    "stem":             ["STEM", "科技营", "编程营", "数学营", "科学营", "理工营"],
    "global_talent":    ["全球英才", "global talent", "人才计划", "精英项目", "国际人才"],
    "research":         ["科研实习", "research internship", "实验室项目", "研究项目", "科研营"],
    "overseas_chinese": ["寻根之旅", "华裔", "海外华人", "华文教育", "overseas Chinese"],
    "teacher_training": ["教师培训", "teacher training", "研习班", "教师研修", "师资培训"],
    "cultural":         ["文化体验", "cultural immersion", "文化营", "文化交流", "传统文化"],
}

# ── Target Sources ────────────────────────────────────────────────────────────
SOURCES = {
    "weixin": {
        "enabled": True,
        "base_url": "https://mp.weixin.qq.com",
        "search_url": "https://weixin.sogou.com/weixin?type=2&query={query}&tsn=3",
        "priority": 1,
    },
    "zhihu": {
        "enabled": True,
        "base_url": "https://www.zhihu.com",
        "search_url": "https://www.zhihu.com/search?type=content&q={query}",
        "priority": 2,
    },
    "xiaohongshu": {
        "enabled": True,
        "base_url": "https://www.xiaohongshu.com",
        "search_url": "https://www.xiaohongshu.com/search_result?keyword={query}",
        "priority": 2,
        "note": "Requires session cookie — set XHS_COOKIE env var",
    },
    "weibo": {
        "enabled": True,
        "base_url": "https://weibo.com",
        "search_url": "https://s.weibo.com/weibo?q={query}&rd=realtime&tw=hotweibo",
        "priority": 3,
    },
    "baidu": {
        "enabled": True,
        "base_url": "https://www.baidu.com",
        "search_url": "https://www.baidu.com/s?wd={query}&rn=50",
        "priority": 2,
    },
    "zhihu_article": {
        "enabled": True,
        "search_url": "https://www.zhihu.com/search?type=article&q={query}",
        "priority": 2,
    },
    "university": {
        "enabled": True,
        "priority": 2,
    },
}

# ── University Database Seed ──────────────────────────────────────────────────
UNIVERSITIES = [
    # OC Specialists
    {"name": "暨南大学", "name_en": "Jinan University", "tier": "OC_SPECIALIST",
     "c9": False, "p985": True, "p211": True, "url": "https://www.jnu.edu.cn",
     "programs_url": "https://hwy.jnu.edu.cn", "weixin_biz": ""},
    {"name": "华侨大学", "name_en": "Huaqiao University", "tier": "OC_SPECIALIST",
     "c9": False, "p985": False, "p211": True, "url": "https://www.hqu.edu.cn",
     "programs_url": "https://hjw.hqu.edu.cn", "weixin_biz": ""},
    {"name": "北京华文学院", "name_en": "Beijing Chinese Language College", "tier": "OC_SPECIALIST",
     "c9": False, "p985": False, "p211": False, "url": "https://www.bjhwxy.com",
     "programs_url": "https://www.bjhwxy.com", "weixin_biz": "MjM5NjY0MTk5NQ=="},

    # C9 / Top Elite
    {"name": "清华大学", "name_en": "Tsinghua University", "tier": "C9_ELITE",
     "c9": True, "p985": True, "p211": True, "url": "https://www.tsinghua.edu.cn",
     "programs_url": "https://goglobal.tsinghua.applysquare.net", "weixin_biz": ""},
    {"name": "浙江大学", "name_en": "Zhejiang University", "tier": "C9_ELITE",
     "c9": True, "p985": True, "p211": True, "url": "https://www.zju.edu.cn",
     "programs_url": "", "weixin_biz": ""},
    {"name": "复旦大学", "name_en": "Fudan University", "tier": "C9_ELITE",
     "c9": True, "p985": True, "p211": True, "url": "https://www.fudan.edu.cn",
     "programs_url": "", "weixin_biz": ""},
    {"name": "中国科学技术大学", "name_en": "USTC", "tier": "C9_ELITE",
     "c9": True, "p985": True, "p211": True, "url": "https://www.ustc.edu.cn",
     "programs_url": "", "weixin_biz": ""},
    {"name": "南京大学", "name_en": "Nanjing University", "tier": "C9_ELITE",
     "c9": True, "p985": True, "p211": True, "url": "https://www.nju.edu.cn",
     "programs_url": "", "weixin_biz": ""},

    # Emerging Elite
    {"name": "西湖大学", "name_en": "Westlake University", "tier": "EMERGING_ELITE",
     "c9": False, "p985": False, "p211": False, "url": "https://www.westlake.edu.cn",
     "programs_url": "https://www.westlake.edu.cn/academics/School_of_Science/summerprogram/",
     "weixin_biz": ""},

    # Joint International
    {"name": "西交利物浦大学", "name_en": "XJTLU", "tier": "JOINT_INTL",
     "c9": False, "p985": False, "p211": False, "url": "https://www.xjtlu.edu.cn",
     "programs_url": "https://www.xjtlu.edu.cn/en/study/programmes/high-school-programmes",
     "weixin_biz": ""},
    {"name": "香港大学", "name_en": "University of Hong Kong", "tier": "HK_ELITE",
     "c9": False, "p985": False, "p211": False, "url": "https://www.hku.hk",
     "programs_url": "", "weixin_biz": ""},
    {"name": "香港科技大学", "name_en": "HKUST", "tier": "HK_ELITE",
     "c9": False, "p985": False, "p211": False, "url": "https://www.ust.hk",
     "programs_url": "", "weixin_biz": ""},
    {"name": "新加坡国立大学", "name_en": "NUS", "tier": "SG_ELITE",
     "c9": False, "p985": False, "p211": False, "url": "https://www.nus.edu.sg",
     "programs_url": "", "weixin_biz": ""},
    {"name": "北京航空航天大学", "name_en": "BUAA", "tier": "P985",
     "c9": False, "p985": True, "p211": True, "url": "https://www.buaa.edu.cn",
     "programs_url": "", "weixin_biz": ""},
    {"name": "西北工业大学", "name_en": "NPU", "tier": "P985",
     "c9": False, "p985": True, "p211": True, "url": "https://www.nwpu.edu.cn",
     "programs_url": "https://npuinternationalcollege.nwpu.edu.cn", "weixin_biz": ""},
]

# ── Historical Data Scope ─────────────────────────────────────────────────────
HISTORY_START_YEAR = 2019
HISTORY_END_YEAR   = 2026
FORECAST_END_YEAR  = 2030

# ── Crawl Settings ────────────────────────────────────────────────────────────
CRAWL_DELAY_MIN  = 1.5   # seconds between requests
CRAWL_DELAY_MAX  = 4.0
MAX_RETRIES      = 3
REQUEST_TIMEOUT  = 20
CACHE_TTL_HOURS  = 24    # re-crawl after this many hours
MAX_ARTICLES_PER_ACCOUNT = 50   # articles to scan per account per run
CONTENT_PREVIEW_LEN = 500

# ── Urgency Keywords ─────────────────────────────────────────────────────────
URGENT_KEYWORDS = ["截止", "最后", "deadline", "last day", "报名截止", "即将", "今日", "明日", "urgent"]
PROGRAM_KEYWORDS_FLAT = [kw for kws in PROGRAM_KEYWORDS.values() for kw in kws]

# ── Output Languages ──────────────────────────────────────────────────────────
OUTPUT_LANGUAGES = ["zh", "en", "vi"]   # Chinese, English, Vietnamese
