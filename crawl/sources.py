"""
crawl/sources.py — All sources for the Programs database crawl.
"""

UNIVERSITY_SOURCES = [
    # ── Top universities with known summer/exchange programs ──
    {"id": "THU",   "name": "Tsinghua University",          "url": "https://www.tsinghua.edu.cn/gss/Latest_News.htm"},
    {"id": "PKU",   "name": "Peking University",             "url": "https://www.oir.pku.edu.cn/summerschool/"},
    {"id": "FDU",   "name": "Fudan University",              "url": "https://www.fudan.edu.cn/en/"},
    {"id": "SJTU",  "name": "Shanghai Jiao Tong",            "url": "https://en.sjtu.edu.cn/academics/summer-sessions/"},
    {"id": "ZJU",   "name": "Zhejiang University",           "url": "https://www.zju.edu.cn/english/"},
    {"id": "WHU",   "name": "Wuhan University",              "url": "https://en.whu.edu.cn/"},
    {"id": "SYSU",  "name": "Sun Yat-sen University",        "url": "https://iso.sysu.edu.cn/en/"},
    {"id": "NJU",   "name": "Nanjing University",            "url": "https://www.nju.edu.cn/en/"},
    {"id": "BNU",   "name": "Beijing Normal University",     "url": "https://en.bnu.edu.cn/"},
    {"id": "BFSU",  "name": "BFSU",                          "url": "https://en.bfsu.edu.cn/"},
    {"id": "BLCU",  "name": "BLCU",                          "url": "https://www.blcu.edu.cn/"},
    {"id": "XMU",   "name": "Xiamen University",             "url": "https://en.xmu.edu.cn/"},
    {"id": "SCU",   "name": "Sichuan University",            "url": "https://en.scu.edu.cn/"},
    {"id": "HIT",   "name": "Harbin Institute of Technology", "url": "https://en.hit.edu.cn/"},
    {"id": "TONGJI","name": "Tongji University",             "url": "https://en.tongji.edu.cn/"},
    {"id": "RUC",   "name": "Renmin University",             "url": "https://en.ruc.edu.cn/"},
    {"id": "XJTU",  "name": "Xi'an Jiaotong University",    "url": "https://en.xjtu.edu.cn/"},
    {"id": "HUST",  "name": "Huazhong Univ of Sci & Tech",  "url": "https://english.hust.edu.cn/"},
    {"id": "CUHKSZ","name": "CUHK Shenzhen",                "url": "https://www.cuhk.edu.cn/en"},
    {"id": "SUSTC", "name": "Southern Univ Sci & Tech",     "url": "https://www.sustech.edu.cn/en/"},
    {"id": "WESTLAKE","name": "Westlake University",         "url": "https://en.westlake.edu.cn/admissions/summer_sessions/"},
    {"id": "XJTLU", "name": "XJTLU",                        "url": "https://www.xjtlu.edu.cn/en/learning-mall/learning-resources/xjtlu-high-school-summer-camp"},
    {"id": "JNU",   "name": "Jinan University",              "url": "https://hwy.jnu.edu.cn/"},
    {"id": "HQU",   "name": "Huaqiao University",            "url": "https://hjw.hqu.edu.cn/"},
    {"id": "BCL",   "name": "Beijing Chinese Language Coll", "url": "https://www.bjhwxy.com/"},
    {"id": "NPU",   "name": "Northwestern Polytechnical",   "url": "https://en.nwpu.edu.cn/"},
    {"id": "ECNU",  "name": "East China Normal University",  "url": "https://www.ecnu.edu.cn/"},
    {"id": "SCNU",  "name": "South China Normal University", "url": "https://en.scnu.edu.cn/"},
    {"id": "BIT",   "name": "Beijing Institute of Tech",    "url": "https://en.bit.edu.cn/"},
    {"id": "DUT",   "name": "Dalian Univ of Technology",    "url": "https://en.dlut.edu.cn/"},
]

GOVERNMENT_SOURCES = [
    {"id": "MOE",   "name": "Ministry of Education China",  "url": "https://en.moe.gov.cn/"},
    {"id": "CSC",   "name": "China Scholarship Council",    "url": "https://www.csc.edu.cn/"},
    {"id": "HANBAN","name": "Chinese International Education Foundation", "url": "https://www.chinese.cn/"},
    {"id": "HWJYW", "name": "China Huawen Education Net",   "url": "https://www.hwjyw.com/"},
    {"id": "CLEF",  "name": "China Huawen Education Foundation", "url": "https://www.clef.org.cn/"},
    {"id": "STUDYINCHINA", "name": "Study in China Official", "url": "https://www.studyinchina.com.cn/"},
    {"id": "CAMPUSCHINA",  "name": "Campus China",          "url": "https://www.campuschina.org/"},
]

INTERNATIONAL_SOURCES = [
    {"id": "CUCAS",      "name": "CUCAS",             "url": "https://www.cucas.edu.cn/"},
    {"id": "CHINAADMIT", "name": "China Admissions",  "url": "https://www.china-admissions.com/"},
    {"id": "GOOVERSEAS", "name": "Go Overseas China", "url": "https://www.gooverseas.com/study-abroad/china"},
    {"id": "GOABROAD",   "name": "GoAbroad China",    "url": "https://www.goabroad.com/study-abroad/search/china/programs-1"},
    {"id": "YOUTHOP",    "name": "Youth Opportunities","url": "https://www.youthop.com/"},
    {"id": "OPDESK",     "name": "Opportunity Desk",  "url": "https://opportunitydesk.org/"},
    {"id": "CAYAUS",     "name": "CAYAUS",             "url": "https://zh.cayaus.org/"},
    {"id": "CAMPC",      "name": "Camp of China",     "url": "https://www.campofchina.org/"},
]

SEARCH_QUERIES_EN = [
    "China summer camp fully funded international students 2025 2026",
    "Chinese university international summer program 2025",
    "China cultural exchange program teachers 2025 2026",
    "Hanban Chinese bridge summer camp 2025 2026",
    "CSC scholarship short term program 2025",
    "Belt and Road exchange program students 2025",
    "China immersion program international 2025",
    "Confucius Institute summer program 2025",
]

SEARCH_QUERIES_ZH = [
    "中国 国际暑期学校 2025 2026 留学生",
    "中国 夏令营 海外华裔 2025 2026 报名",
    "汉语桥 夏令营 2025 2026 申请",
    "国际教师交流项目 中国 2025",
    "中国政府奖学金 短期 2025",
    "一带一路 交流项目 2025",
    "海外华文教师 培训 2025 2026",
    "国际暑期研学 中国大学 2025",
]

ALL_SOURCES = UNIVERSITY_SOURCES + GOVERNMENT_SOURCES + INTERNATIONAL_SOURCES
