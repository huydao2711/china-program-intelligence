"""One-time script: create 'Sources' sheet with all 27 monitored sources."""
import json
import gspread
from google.oauth2.service_account import Credentials

with open('../railway-monitor-497207-11b94d1a89af.json') as f:
    sa_info = json.load(f)

scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_info(sa_info, scopes=scopes)
gc = gspread.authorize(creds)
ss = gc.open_by_key('1o7NL2nPmJ8g1w7XeWscEwP62wbWbe7W6eBJ00LQWZRk')

# Remove old Sources sheet if exists
for ws in ss.worksheets():
    if ws.title == 'Sources':
        ss.del_worksheet(ws)
        print('Deleted old Sources sheet')

ws = ss.add_worksheet('Sources', rows=40, cols=8)
print('Created Sources sheet')

HEADERS = ['#', 'Ten to chuc', 'Nen tang', 'URL', 'Dang nhap', 'Phuong phap cao', 'Ty le cao', 'Trang thai / Ghi chu']

ROWS = [
    # ── WeChat ──
    [1,  'FCSC (加拿大华文学校联合总会)',    'WeChat', 'mp.weixin.qq.com  __biz=MzkxNTM0Njg4MQ==', 'Can cookie', 'BIZ API - co BIZ + GH ID',        '0%',   'Can WeChat cookie de mo khoa'],
    [2,  'BCL (北京华文学院)',               'WeChat', 'mp.weixin.qq.com  __biz=MjM5NjY0MTk5NQ==', 'Can cookie', 'BIZ API - co BIZ + GH ID',        '0%',   'Can WeChat cookie de mo khoa'],
    [3,  'CHDEC (中国华文教育发展中心)',      'WeChat', 'mp.weixin.qq.com  __biz=MjM5NTA1NjE3NQ==', 'Can cookie', 'BIZ API - co BIZ, thieu GH ID',   '0%',   'Can WeChat cookie + tim GH ID'],
    [4,  'JNU (暨南大学华文学院)',            'WeChat', 'Chua co BIZ',                              'Khong co BIZ', 'Sogou article search fallback', '0%',   'Can tim __biz qua WeChat search'],
    [5,  'HQU (华侨大学华文教育处)',          'WeChat', 'Chua co BIZ',                              'Khong co BIZ', 'Sogou article search fallback', '0%',   'Can tim __biz qua WeChat search'],
    [6,  'HKECE (香港教育交流中心)',          'WeChat', 'Chua co BIZ',                              'Khong co BIZ', 'Sogou article search fallback', '0%',   'Can tim __biz qua WeChat search'],
    [7,  'CAYAUS (全美华裔青少年协会)',       'WeChat', 'Chua co BIZ',                              'Khong co BIZ', 'Sogou article search fallback', '0%',   'Can tim __biz qua WeChat search'],
    [8,  'CLEF (中国华文教育基金会)',         'WeChat', 'Chua co BIZ',                              'Khong co BIZ', 'Sogou article search fallback', '0%',   'Can tim __biz qua WeChat search'],
    [9,  'EFCSA (欧洲华文教育联合总会)',      'WeChat', 'Chua co BIZ',                              'Khong co BIZ', 'Sogou article search fallback', '0%',   'Can tim __biz qua WeChat search'],
    [10, 'ACCSF (澳大利亚华文学校联合会)',    'WeChat', 'Chua co BIZ',                              'Khong co BIZ', 'Sogou article search fallback', '0%',   'Can tim __biz qua WeChat search'],
    [11, 'DONGZONG (马来西亚华校董事联合会)', 'WeChat', 'Chua co BIZ',                              'Khong co BIZ', 'Sogou article search fallback', '0%',   'Can tim __biz qua WeChat search'],
    # ── Sogou ──
    [12, 'Sogou: 寻根之旅 2026',             'Sogou',  'weixin.sogou.com/weixin?type=2&query=寻根之旅+2026&tsn=3',         'Anonymous', 'Keyword search SERP', '0%', 'IP Railway bi block Sogou'],
    [13, 'Sogou: 华文教师研习班 2026',       'Sogou',  'weixin.sogou.com/weixin?type=2&query=华文教师研习班+2026&tsn=3',   'Anonymous', 'Keyword search SERP', '0%', 'IP Railway bi block Sogou'],
    [14, 'Sogou: AI华文教育 2026',           'Sogou',  'weixin.sogou.com/weixin?type=2&query=AI华文教育+2026&tsn=3',       'Anonymous', 'Keyword search SERP', '0%', 'IP Railway bi block Sogou'],
    [15, 'Sogou: 海外华裔夏令营 2026',       'Sogou',  'weixin.sogou.com/weixin?type=2&query=海外华裔夏令营+2026&tsn=3',   'Anonymous', 'Keyword search SERP', '0%', 'IP Railway bi block Sogou'],
    # ── Website ──
    [16, '中国华文教育网 (HWJYW)',            'Website', 'https://www.hwjyw.com/',                                                          'Khong can', 'HTTP crawl + fingerprint', '~60%', 'Timeout thuong xuyen - server China'],
    [17, '中国华文教育基金会 (CLEF web)',     'Website', 'https://www.clef.org.cn/',                                                        'Khong can', 'HTTP crawl + fingerprint', '~90%', 'OK'],
    [18, '北京华文学院官网 (BCL web)',        'Website', 'https://www.bjhwxy.com/',                                                         'Khong can', 'HTTP crawl + fingerprint', '~90%', 'OK'],
    [19, '暨南大学华文学院 (JNU web)',        'Website', 'https://hwy.jnu.edu.cn/',                                                         'Khong can', 'HTTP crawl + fingerprint', '~90%', 'OK'],
    [20, '华侨大学华文教育处 (HQU web)',      'Website', 'https://hjw.hqu.edu.cn/',                                                         'Khong can', 'HTTP crawl + fingerprint', '~60%', 'Timeout thuong xuyen - server China'],
    [21, '清华全球暑期学校 (THU-GSS)',        'Website', 'https://www.tsinghua.edu.cn/gss/Latest_News.htm',                                 'Khong can', 'HTTP crawl + fingerprint', '~90%', 'OK'],
    [22, '清华 GenAI 暑期学校 (THU-AI)',     'Website', 'https://ss.cs.tsinghua.edu.cn/',                                                   'Khong can', 'HTTP crawl + fingerprint', '~90%', 'OK'],
    [23, '西湖大学国际科学营 (Westlake)',     'Website', 'https://www.westlake.edu.cn/academics/School_of_Science/summerprogram/',          'Khong can', 'HTTP crawl + fingerprint', '0%',   'HTTP 500 - server loi lien tuc'],
    [24, 'XJTLU AI 高中营',                 'Website', 'https://www.xjtlu.edu.cn/en/study/programmes/high-school-programmes',             'Khong can', 'HTTP crawl + fingerprint', '0%',   'HTTP 404 - URL sai, can cap nhat'],
    [25, '西北工业大学夏令营 (NPU)',          'Website', 'https://npuinternationalcollege.nwpu.edu.cn/info/1146/11168.htm',                 'Khong can', 'HTTP crawl + fingerprint', '~40%', 'Timeout nang - server China block IP nuoc ngoai'],
    [26, '全美华裔青少年协会 (CAYAUS web)',   'Website', 'https://zh.cayaus.org/%E5%AE%9E%E5%9C%B0%E5%A4%8F%E4%BB%A4%E8%90%A5',           'Khong can', 'HTTP crawl + fingerprint', '~90%', 'OK'],
    [27, '北美华人寻根夏令营 (CAMPC)',        'Website', 'https://www.campofchina.org/',                                                    'Khong can', 'HTTP crawl + fingerprint', '~90%', 'OK'],
]

ws.append_row(HEADERS)
ws.append_rows(ROWS, value_input_option='RAW')
print(f'Wrote {len(ROWS)} rows')

# ── Formatting ──
sid = ws.id

HEADER_BG  = {'red': 0.10, 'green': 0.14, 'blue': 0.49}
HEADER_FG  = {'red': 1.0,  'green': 1.0,  'blue': 1.0}
WECHAT_BG  = {'red': 0.83, 'green': 0.91, 'blue': 0.98}
SOGOU_BG   = {'red': 1.0,  'green': 0.95, 'blue': 0.80}
WEB_OK_BG  = {'red': 0.88, 'green': 0.97, 'blue': 0.89}
BAD_BG     = {'red': 1.0,  'green': 0.89, 'blue': 0.87}

ws.format('A1:H1', {
    'backgroundColor': HEADER_BG,
    'textFormat': {'foregroundColor': HEADER_FG, 'bold': True, 'fontSize': 10},
    'horizontalAlignment': 'CENTER',
})

def color_rows(start_row, end_row, color):
    return {
        'repeatCell': {
            'range': {
                'sheetId': sid,
                'startRowIndex': start_row,
                'endRowIndex': end_row,
                'startColumnIndex': 0,
                'endColumnIndex': 8,
            },
            'cell': {'userEnteredFormat': {'backgroundColor': color}},
            'fields': 'userEnteredFormat.backgroundColor',
        }
    }

col_widths = [32, 290, 75, 370, 95, 200, 75, 220]
requests = []

for i, px in enumerate(col_widths):
    requests.append({
        'updateDimensionProperties': {
            'range': {'sheetId': sid, 'dimension': 'COLUMNS', 'startIndex': i, 'endIndex': i + 1},
            'properties': {'pixelSize': px},
            'fields': 'pixelSize',
        }
    })

requests.append({
    'updateSheetProperties': {
        'properties': {'sheetId': sid, 'gridProperties': {'frozenRowCount': 1}},
        'fields': 'gridProperties.frozenRowCount',
    }
})

# Platform color bands
requests += [
    color_rows(1, 12, WECHAT_BG),    # rows 2-12: WeChat (11 accounts)
    color_rows(12, 16, SOGOU_BG),    # rows 13-16: Sogou (4 searches)
    color_rows(16, 28, WEB_OK_BG),   # rows 17-28: Website (12 sites)
    # Override broken sites with red
    color_rows(22, 23, BAD_BG),      # row 23: Westlake 500
    color_rows(23, 24, BAD_BG),      # row 24: XJTLU 404
]

ss.batch_update({'requests': requests})
print('Formatting applied')
print('Done -', ss.url)
