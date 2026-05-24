"""
monitor/notifier.py — HTML email digest for daily monitor results.
Python port of Email.gs
"""

import os, smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .config import PROGRAM_DEADLINES, MONITOR_CONFIG


def _deadline_rows() -> str:
    today = datetime.now()
    rows = ""
    for d in PROGRAM_DEADLINES:
        deadline_dt = datetime.strptime(d["deadline"], "%Y-%m-%d")
        days_left = (deadline_dt - today).days
        if days_left < 0:
            color = "#9e9e9e"
            badge = "EXPIRED"
        elif days_left <= d["days_warn"]:
            color = "#c62828"
            badge = f"{days_left}d — URGENT"
        else:
            color = "#2e7d32"
            badge = f"{days_left}d"
        rows += (
            f"<tr>"
            f"<td style='padding:8px 12px;border-bottom:1px solid #f0f0f0;font-size:13px;'>{d['program']}</td>"
            f"<td style='padding:8px 12px;border-bottom:1px solid #f0f0f0;font-size:13px;'>{d['deadline']}</td>"
            f"<td style='padding:8px 12px;border-bottom:1px solid #f0f0f0;font-size:13px;"
            f"font-weight:700;color:{color};'>{badge}</td>"
            f"</tr>"
        )
    return rows


def _article_card(a: dict) -> str:
    is_urgent = a.get("hasDeadline")
    bg = "#fff5f5" if is_urgent else "#f0f7ff"
    border = "#e57373" if is_urgent else "#90caf9"
    label = (
        "<span style='background:#c62828;color:#fff;font-size:10px;font-weight:700;"
        "padding:2px 7px;border-radius:10px;margin-left:8px;'>URGENT</span>"
        if is_urgent else ""
    )
    kws = ", ".join(a.get("keywordsFound") or [])
    return f"""
<div style="margin-bottom:12px;background:{bg};border-left:4px solid {border};
            border-radius:6px;padding:14px 16px;">
  <div style="font-size:13px;font-weight:700;color:#1a237e;margin-bottom:4px;">
    {a.get("title","(no title)")} {label}
  </div>
  <div style="font-size:11px;color:#666;margin-bottom:6px;">
    <strong>{a.get("accountShort","")}</strong> &nbsp;·&nbsp;
    {a.get("region","")} &nbsp;·&nbsp;
    {a.get("publishDate","")} &nbsp;·&nbsp;
    <span style="color:#555;">{a.get("sourceType","")}</span>
  </div>
  <div style="font-size:12px;color:#444;margin-bottom:8px;line-height:1.5;">
    {a.get("content","")[:200]}
  </div>
  {"<div style='font-size:11px;color:#666;'>Keywords: " + kws + "</div>" if kws else ""}
  <a href="{a.get('url','#')}" style="display:inline-block;margin-top:8px;font-size:11px;
     color:#1565c0;text-decoration:none;border:1px solid #90caf9;border-radius:4px;
     padding:3px 10px;">查看原文 →</a>
</div>"""


def send_daily_digest(articles: list, sheet_url: str = "") -> bool:
    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")
    notify_to  = os.environ.get("NOTIFY_EMAIL", gmail_user)

    if not gmail_user or not gmail_pass:
        print("[Notifier] Email not configured — skipping digest")
        return False

    now = datetime.now()
    urgent    = [a for a in articles if a.get("hasDeadline")]
    normal    = [a for a in articles if not a.get("hasDeadline")]
    wechat_n  = sum(1 for a in articles if a.get("sourceType") == "WeChat")
    web_n     = sum(1 for a in articles if a.get("sourceType") == "Website")
    sogou_n   = sum(1 for a in articles if a.get("sourceType") == "Sogou")

    urgent_section = ""
    if urgent:
        cards = "".join(_article_card(a) for a in urgent)
        urgent_section = f"""
<div style="margin-bottom:24px;">
  <div style="font-size:13px;font-weight:700;color:#c62828;margin-bottom:10px;
              text-transform:uppercase;letter-spacing:.5px;">
    ⚠️ Có deadline ({len(urgent)} bài)
  </div>
  {cards}
</div>"""

    normal_section = ""
    if normal:
        cards = "".join(_article_card(a) for a in normal[:15])
        normal_section = f"""
<div style="margin-bottom:24px;">
  <div style="font-size:13px;font-weight:700;color:#1565c0;margin-bottom:10px;
              text-transform:uppercase;letter-spacing:.5px;">
    Bài mới ({len(normal)} bài)
  </div>
  {cards}
</div>"""

    sheet_btn = ""
    if sheet_url:
        sheet_btn = (
            f"<a href='{sheet_url}' style='display:inline-block;background:#1a237e;color:#fff;"
            f"text-decoration:none;padding:10px 22px;border-radius:6px;font-size:13px;"
            f"font-weight:700;'>Mở Google Sheet →</a>"
        )

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f6fa;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:660px;margin:20px auto;background:#fff;border-radius:12px;
            overflow:hidden;box-shadow:0 2px 16px rgba(0,0,0,.08);">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#1a237e 0%,#4f6ef7 100%);
              padding:28px 24px;color:#fff;">
    <div style="font-size:11px;opacity:.7;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">
      Daily Monitor — {now.strftime('%d/%m/%Y %H:%M')} (Vietnam)
    </div>
    <div style="font-size:20px;font-weight:800;">WeChat Monitor Report</div>
    <div style="font-size:12px;opacity:.75;margin-top:4px;">
      27 nguồn · WeChat + Website + Sogou
    </div>
  </div>

  <!-- Stats -->
  <div style="display:flex;gap:0;background:#f8f9ff;border-bottom:1px solid #e8eaf0;">
    {"".join(
        f"<div style='flex:1;text-align:center;padding:16px 8px;border-right:1px solid #e8eaf0;'>"
        f"<div style='font-size:22px;font-weight:800;color:{c};'>{v}</div>"
        f"<div style='font-size:11px;color:#888;margin-top:2px;'>{l}</div></div>"
        for l, v, c in [
            ("Tổng mới",   len(articles), "#1a237e"),
            ("Urgent",     len(urgent),   "#c62828"),
            ("WeChat",     wechat_n,      "#4f6ef7"),
            ("Website",    web_n,         "#2e7d32"),
            ("Sogou",      sogou_n,       "#7b1fa2"),
        ]
    )}
  </div>

  <div style="padding:24px;">

    {urgent_section}
    {normal_section}

    <!-- Deadlines -->
    <div style="margin-bottom:24px;">
      <div style="font-size:13px;font-weight:700;color:#e65100;margin-bottom:10px;
                  text-transform:uppercase;letter-spacing:.5px;">
        Deadlines sắp tới
      </div>
      <table style="width:100%;border-collapse:collapse;">
        <tr style="background:#fff3e0;">
          <th style="padding:8px 12px;text-align:left;font-size:11px;border-bottom:2px solid #ffe0b2;">Chương trình</th>
          <th style="padding:8px 12px;text-align:left;font-size:11px;border-bottom:2px solid #ffe0b2;">Deadline</th>
          <th style="padding:8px 12px;text-align:left;font-size:11px;border-bottom:2px solid #ffe0b2;">Còn lại</th>
        </tr>
        {_deadline_rows()}
      </table>
    </div>

    {sheet_btn}
  </div>

  <!-- Footer -->
  <div style="padding:14px 24px;background:#f5f6fa;border-top:1px solid #e8eaf0;
              font-size:11px;color:#9e9e9e;text-align:center;">
    Chạy tự động trên Railway · {now.strftime('%d/%m/%Y')}
  </div>
</div>
</body></html>"""

    subject = (
        f"[Monitor] {now.strftime('%d/%m')} — "
        f"{len(articles)} bài mới"
        + (f" · {len(urgent)} URGENT" if urgent else "")
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = gmail_user
    msg["To"]      = notify_to
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.starttls()
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, notify_to, msg.as_string())
        print(f"[Notifier] Daily digest sent to {notify_to}")
        return True
    except Exception as e:
        print(f"[Notifier] Email failed: {e}")
        return False


def send_urgent_alert(article: dict) -> bool:
    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")
    notify_to  = os.environ.get("NOTIFY_EMAIL", gmail_user)

    if not gmail_user or not gmail_pass:
        return False

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:560px;margin:20px auto;">
  <div style="background:#c62828;color:#fff;padding:16px 20px;border-radius:8px 8px 0 0;">
    <strong>⚠️ URGENT — Deadline detected</strong>
  </div>
  <div style="border:1px solid #e57373;border-top:none;padding:20px;border-radius:0 0 8px 8px;">
    <h3 style="margin:0 0 8px;color:#b71c1c;">{article.get("title","")}</h3>
    <p style="font-size:13px;color:#555;">
      <strong>Source:</strong> {article.get("accountName","")} ({article.get("accountShort","")})<br>
      <strong>Region:</strong> {article.get("region","")}<br>
      <strong>Date:</strong> {article.get("publishDate","")}<br>
      <strong>Keywords:</strong> {", ".join(article.get("keywordsFound") or [])}
    </p>
    <p style="font-size:13px;color:#444;">{article.get("content","")[:300]}</p>
    <a href="{article.get('url','#')}" style="display:inline-block;background:#c62828;color:#fff;
       text-decoration:none;padding:9px 18px;border-radius:5px;font-size:13px;margin-top:8px;">
      查看原文 →
    </a>
  </div>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[URGENT] {article.get('title','')[:60]}"
    msg["From"]    = gmail_user
    msg["To"]      = notify_to
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.starttls()
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, notify_to, msg.as_string())
        return True
    except Exception as e:
        print(f"[Notifier] Urgent alert failed: {e}")
        return False
