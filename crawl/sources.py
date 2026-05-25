"""
crawl/sources.py — All sources for the Programs database crawl.

Source types:
  type: "html"    — default, fetch HTML and strip tags
  type: "reddit"  — fetch Reddit JSON API, convert to text
  type: "telegram"— fetch public Telegram channel (t.me/s/)
"""

UNIVERSITY_SOURCES = [
    {"id": "THU",      "name": "Tsinghua University",          "url": "https://www.tsinghua.edu.cn/gss/Latest_News.htm"},
    {"id": "PKU",      "name": "Peking University",            "url": "https://www.oir.pku.edu.cn/summerschool/"},
    {"id": "FDU",      "name": "Fudan University",             "url": "https://www.fudan.edu.cn/en/"},
    {"id": "SJTU",     "name": "Shanghai Jiao Tong",           "url": "https://en.sjtu.edu.cn/academics/summer-sessions/"},
    {"id": "ZJU",      "name": "Zhejiang University",          "url": "https://www.zju.edu.cn/english/"},
    {"id": "WHU",      "name": "Wuhan University",             "url": "https://en.whu.edu.cn/"},
    {"id": "SYSU",     "name": "Sun Yat-sen University",       "url": "https://iso.sysu.edu.cn/en/"},
    {"id": "NJU",      "name": "Nanjing University",           "url": "https://www.nju.edu.cn/en/"},
    {"id": "BNU",      "name": "Beijing Normal University",    "url": "https://en.bnu.edu.cn/"},
    {"id": "BFSU",     "name": "BFSU",                         "url": "https://en.bfsu.edu.cn/"},
    {"id": "BLCU",     "name": "BLCU",                         "url": "https://www.blcu.edu.cn/"},
    {"id": "XMU",      "name": "Xiamen University",            "url": "https://en.xmu.edu.cn/"},
    {"id": "SCU",      "name": "Sichuan University",           "url": "https://en.scu.edu.cn/"},
    {"id": "HIT",      "name": "Harbin Inst of Technology",    "url": "https://en.hit.edu.cn/"},
    {"id": "TONGJI",   "name": "Tongji University",            "url": "https://en.tongji.edu.cn/"},
    {"id": "RUC",      "name": "Renmin University",            "url": "https://en.ruc.edu.cn/"},
    {"id": "XJTU",     "name": "Xi'an Jiaotong University",   "url": "https://en.xjtu.edu.cn/"},
    {"id": "HUST",     "name": "Huazhong UST",                 "url": "https://english.hust.edu.cn/"},
    {"id": "CUHKSZ",   "name": "CUHK Shenzhen",               "url": "https://www.cuhk.edu.cn/en"},
    {"id": "SUSTC",    "name": "Southern UST",                 "url": "https://www.sustech.edu.cn/en/"},
    {"id": "WESTLAKE", "name": "Westlake University",          "url": "https://en.westlake.edu.cn/admissions/summer_sessions/"},
    {"id": "XJTLU",    "name": "XJTLU",                        "url": "https://www.xjtlu.edu.cn/en/learning-mall/learning-resources/xjtlu-high-school-summer-camp"},
    {"id": "JNU",      "name": "Jinan University",             "url": "https://hwy.jnu.edu.cn/"},
    {"id": "HQU",      "name": "Huaqiao University",           "url": "https://hjw.hqu.edu.cn/"},
    {"id": "BCL",      "name": "Beijing Chinese Language Coll","url": "https://www.bjhwxy.com/"},
    {"id": "NPU",      "name": "Northwestern Polytechnical",   "url": "https://en.nwpu.edu.cn/"},
    {"id": "ECNU",     "name": "East China Normal University", "url": "https://www.ecnu.edu.cn/"},
    {"id": "SCNU",     "name": "South China Normal University","url": "https://en.scnu.edu.cn/"},
    {"id": "BIT",      "name": "Beijing Inst of Tech",         "url": "https://en.bit.edu.cn/"},
    {"id": "DUT",      "name": "Dalian Univ of Technology",    "url": "https://en.dlut.edu.cn/"},
]

GOVERNMENT_SOURCES = [
    {"id": "MOE",          "name": "Ministry of Education China",         "url": "https://en.moe.gov.cn/"},
    {"id": "CSC",          "name": "China Scholarship Council",           "url": "https://www.csc.edu.cn/"},
    {"id": "HANBAN",       "name": "Chinese Intl Education Foundation",   "url": "https://www.chinese.cn/"},
    {"id": "HWJYW",        "name": "China Huawen Education Net",          "url": "https://www.hwjyw.com/"},
    {"id": "CLEF",         "name": "China Huawen Education Foundation",   "url": "https://www.clef.org.cn/"},
    {"id": "STUDYINCHINA", "name": "Study in China Official",             "url": "https://www.studyinchina.com.cn/"},
    {"id": "CAMPUSCHINA",  "name": "Campus China",                        "url": "https://www.campuschina.org/"},
]

INTERNATIONAL_SOURCES = [
    {"id": "CUCAS",      "name": "CUCAS",              "url": "https://www.cucas.edu.cn/"},
    {"id": "CHINAADMIT", "name": "China Admissions",   "url": "https://www.china-admissions.com/"},
    {"id": "GOOVERSEAS", "name": "Go Overseas China",  "url": "https://www.gooverseas.com/study-abroad/china"},
    {"id": "GOABROAD",   "name": "GoAbroad China",     "url": "https://www.goabroad.com/study-abroad/search/china/programs-1"},
    {"id": "YOUTHOP",    "name": "Youth Opportunities","url": "https://www.youthop.com/"},
    {"id": "OPDESK",     "name": "Opportunity Desk",   "url": "https://opportunitydesk.org/"},
    {"id": "CAYAUS",     "name": "CAYAUS",              "url": "https://zh.cayaus.org/"},
    {"id": "CAMPC",      "name": "Camp of China",      "url": "https://www.campofchina.org/"},
]

# ── Reddit — public JSON API, no auth needed ───────────────────────────────────
REDDIT_SOURCES = [
    {"id": "RD_STUDYABROAD",  "name": "Reddit r/studyabroad",         "url": "https://www.reddit.com/r/studyabroad/search.json?q=china+summer+program+scholarship&sort=new&limit=25", "type": "reddit"},
    {"id": "RD_SCHOLARSHIPS", "name": "Reddit r/scholarships",        "url": "https://www.reddit.com/r/scholarships/search.json?q=china+summer+camp&sort=new&limit=25",              "type": "reddit"},
    {"id": "RD_CHINA",        "name": "Reddit r/china programs",      "url": "https://www.reddit.com/r/china/search.json?q=summer+camp+program+international&sort=new&limit=25",     "type": "reddit"},
    {"id": "RD_CHINALANG",    "name": "Reddit r/ChineseLearning",     "url": "https://www.reddit.com/r/ChineseLearning/search.json?q=summer+program+china+scholarship&sort=new&limit=25", "type": "reddit"},
    {"id": "RD_INTLSTUDENTS", "name": "Reddit r/internationalstudents","url": "https://www.reddit.com/r/internationalstudents/search.json?q=china+program+scholarship&sort=new&limit=25", "type": "reddit"},
    {"id": "RD_CSC",          "name": "Reddit CSC Scholarship search", "url": "https://www.reddit.com/search.json?q=CSC+scholarship+china+program+2025+2026&sort=new&limit=25",       "type": "reddit"},
    {"id": "RD_HANBAN",       "name": "Reddit Hanban/Chinese Bridge",  "url": "https://www.reddit.com/search.json?q=hanban+chinese+bridge+scholarship+camp&sort=new&limit=25",         "type": "reddit"},
]

# ── Telegram — public channels accessible via t.me/s/ ─────────────────────────
TELEGRAM_SOURCES = [
    {"id": "TG_CHINASTUDY",   "name": "Telegram China Study",          "url": "https://t.me/s/chinastudy",           "type": "telegram"},
    {"id": "TG_SCHOLARSHIP",  "name": "Telegram Scholarship Channel",  "url": "https://t.me/s/scholarshipopportunity","type": "telegram"},
    {"id": "TG_CHINACAMPS",   "name": "Telegram China Camps",          "url": "https://t.me/s/chinacamps",           "type": "telegram"},
    {"id": "TG_STUDYCHINA",   "name": "Telegram Study in China",       "url": "https://t.me/s/studyinchina2025",     "type": "telegram"},
    {"id": "TG_CSCSCHOLAR",   "name": "Telegram CSC Scholarships",     "url": "https://t.me/s/cscscholarships",      "type": "telegram"},
    {"id": "TG_INTLSCHOLAR",  "name": "Telegram Intl Scholarships",    "url": "https://t.me/s/internationalscholarships", "type": "telegram"},
    {"id": "TG_YOUTHPROG",    "name": "Telegram Youth Programs",       "url": "https://t.me/s/youthprogramsworld",   "type": "telegram"},
]

# ── Chinese social media — public search pages ────────────────────────────────
WEIBO_SOURCES = [
    {"id": "WB_SUMMERCAMP", "name": "Weibo 暑期夏令营",     "url": "https://s.weibo.com/weibo?q=暑期夏令营+留学生+2025&typeall=1&suball=1&timescope=custom:2025-1-1:2026-12-31&Refer=g"},
    {"id": "WB_SCHOLARSHIP","name": "Weibo 中国奖学金",     "url": "https://s.weibo.com/weibo?q=中国政府奖学金+夏令营+2025&typeall=1&suball=1&Refer=g"},
    {"id": "WB_HANBAN",     "name": "Weibo 汉语桥",         "url": "https://s.weibo.com/weibo?q=汉语桥+夏令营+2025+2026&typeall=1&suball=1&Refer=g"},
    {"id": "WB_EXCHANGE",   "name": "Weibo 交流项目",       "url": "https://s.weibo.com/weibo?q=国际交流项目+中国+2025+招募&typeall=1&suball=1&Refer=g"},
    {"id": "WB_INTLSTUD",   "name": "Weibo 留学生项目",     "url": "https://s.weibo.com/weibo?q=留学生+中国+招募+2025+项目&typeall=1&suball=1&Refer=g"},
]

ZHIHU_SOURCES = [
    {"id": "ZH_SUMMERCAMP", "name": "Zhihu 暑期学校",      "url": "https://www.zhihu.com/search?type=content&q=中国暑期学校+2025+留学生"},
    {"id": "ZH_CSC",        "name": "Zhihu CSC奖学金",     "url": "https://www.zhihu.com/search?type=content&q=中国政府奖学金+夏令营+申请"},
    {"id": "ZH_HANBAN",     "name": "Zhihu 汉语桥项目",    "url": "https://www.zhihu.com/search?type=content&q=汉语桥+夏令营+申请+2025"},
    {"id": "ZH_INTLPROG",   "name": "Zhihu 国际交流项目",  "url": "https://www.zhihu.com/search?type=content&q=中国大学+国际项目+summer+program"},
]

BILIBILI_SOURCES = [
    {"id": "BLB_SUMCAMP",   "name": "Bilibili 中国夏令营",  "url": "https://search.bilibili.com/video?keyword=中国暑期夏令营+留学生&order=pubdate"},
    {"id": "BLB_STUDYCN",   "name": "Bilibili 留学中国",    "url": "https://search.bilibili.com/video?keyword=留学中国+奖学金+2025&order=pubdate"},
    {"id": "BLB_HANBAN",    "name": "Bilibili 汉语桥",      "url": "https://search.bilibili.com/video?keyword=汉语桥+夏令营&order=pubdate"},
]

BAIDU_SOURCES = [
    {"id": "BD_TIEBA_STUDY","name": "Baidu Tieba 留学生版",  "url": "https://tieba.baidu.com/f/search/res?ie=utf-8&kw=留学生&qw=暑期+夏令营+2025"},
    {"id": "BD_TIEBA_CAMP", "name": "Baidu Tieba 夏令营版",  "url": "https://tieba.baidu.com/f/search/res?ie=utf-8&kw=夏令营&qw=中国+2025+留学"},
    {"id": "BD_NEWS_CAMP",  "name": "Baidu News 夏令营",     "url": "https://www.baidu.com/s?tn=news&rtt=1&bsst=1&cl=2&wd=中国暑期夏令营+留学生+2025"},
    {"id": "BD_NEWS_CSC",   "name": "Baidu News CSC",        "url": "https://www.baidu.com/s?tn=news&rtt=1&bsst=1&cl=2&wd=中国政府奖学金+夏令营+2025"},
]

# ── Chinese news/edu portals ──────────────────────────────────────────────────
CHINESE_PORTAL_SOURCES = [
    {"id": "SINA_EDU",    "name": "Sina Education",      "url": "https://edu.sina.com.cn/"},
    {"id": "SINA_STUDY",  "name": "Sina Study Abroad",   "url": "https://edu.sina.com.cn/studyabroad/"},
    {"id": "NETEASE_EDU", "name": "NetEase Education",   "url": "https://edu.163.com/special/chineseBridge/"},
    {"id": "SOHU_EDU",    "name": "Sohu Education",      "url": "https://www.sohu.com/c/education"},
    {"id": "TOUTIAO_EDU", "name": "Toutiao 留学",        "url": "https://www.toutiao.com/search/?keyword=中国暑期夏令营+留学生+2025"},
    {"id": "CHINADAILY",  "name": "China Daily Programs", "url": "https://www.chinadaily.com.cn/china/chinastudy.html"},
    {"id": "XINHUA_EDU",  "name": "Xinhua Education",    "url": "http://www.xinhuanet.com/edu/"},
    {"id": "PEOPLE_EDU",  "name": "People's Daily Edu",  "url": "http://edu.people.com.cn/"},
]

# ── International community platforms ────────────────────────────────────────
COMMUNITY_SOURCES = [
    {"id": "SCHOLARSIP_DESK", "name": "Scholarship Desk China",    "url": "https://www.scholarshipdesk.com/?s=china+summer+program"},
    {"id": "SCHOLARS4DEV",    "name": "Scholars4Dev China",        "url": "https://www.scholars4dev.com/?s=china"},
    {"id": "AFTERSCHOOL",     "name": "AfterSchoolAfrica China",   "url": "https://afterscholafrica.com/?s=china+scholarship"},
    {"id": "NOVASCOTIA",      "name": "FindAScholarship China",    "url": "https://www.findascholarship.net/china-scholarships/"},
    {"id": "SCHOLARSHIP_COM", "name": "Scholarship.com China",     "url": "https://www.scholarship.com/scholarships/search/?q=china"},
    {"id": "WEMAKESCHOLARS",  "name": "WeMakeScholars China",      "url": "https://www.wemakescholars.com/scholarship/china"},
    {"id": "MASTERSPORTAL",   "name": "Mastersportal China",       "url": "https://www.mastersportal.eu/search/#q=china-summer-school"},
    {"id": "SUMMERSCHOOLS",   "name": "Summer Schools Info China", "url": "https://www.summerschoolsineurope.eu/?s=china"},
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
    "China youth exchange program 2025 apply",
    "study in China summer program free tuition scholarship",
    "Chinese government scholarship summer 2025 application",
    "China university camp international students 2025",
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
    "中国大学 暑期学校 外国留学生 2025 免费",
    "中国青年 国际交流 招募 2025",
    "小红书 中国夏令营 留学生 2025",
    "微博 汉语桥 夏令营 报名 2025",
]

ALL_SOURCES = (
    UNIVERSITY_SOURCES
    + GOVERNMENT_SOURCES
    + INTERNATIONAL_SOURCES
    + REDDIT_SOURCES
    + TELEGRAM_SOURCES
    + WEIBO_SOURCES
    + ZHIHU_SOURCES
    + BILIBILI_SOURCES
    + BAIDU_SOURCES
    + CHINESE_PORTAL_SOURCES
    + COMMUNITY_SOURCES
)
