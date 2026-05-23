"""
notifier.py — Send HTML email report via Gmail SMTP.
Called at the end of orchestrator.py when running on Railway.
"""
import os, smtplib, re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from pathlib import Path


def _md_to_html(md: str) -> str:
    """Minimal Markdown → HTML conversion (no external deps)."""
    lines = md.split("\n")
    html_lines = []
    in_table = False
    in_code  = False

    for line in lines:
        # Code block
        if line.startswith("```"):
            if in_code:
                html_lines.append("</pre></code>")
                in_code = False
            else:
                html_lines.append("<code><pre style='background:#f3f4f6;padding:12px;border-radius:6px;font-size:13px;overflow-x:auto;'>")
                in_code = True
            continue
        if in_code:
            html_lines.append(line.replace("<", "&lt;").replace(">", "&gt;"))
            continue

        # Table
        if "|" in line and line.strip().startswith("|"):
            if not in_table:
                html_lines.append("<table style='border-collapse:collapse;width:100%;margin:12px 0;'>")
                in_table = True
            if re.match(r"^\|[-| ]+\|$", line.strip()):
                continue  # separator row
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            tag = "th" if not any("---" in c for c in cells) else "td"
            style_td = "style='border:1px solid #e5e7eb;padding:8px 12px;font-size:13px;'"
            style_th = "style='border:1px solid #e5e7eb;padding:8px 12px;background:#f9fafb;font-weight:600;font-size:12px;text-align:left;'"
            row = "".join(f"<{tag} {style_th if tag=='th' else style_td}>{c}</{tag}>" for c in cells)
            html_lines.append(f"<tr>{row}</tr>")
            continue
        elif in_table:
            html_lines.append("</table>")
            in_table = False

        # Headings
        if line.startswith("# "):
            html_lines.append(f"<h1 style='color:#1e293b;font-size:22px;margin:24px 0 8px;border-bottom:2px solid #4f6ef7;padding-bottom:8px;'>{line[2:]}</h1>")
        elif line.startswith("## "):
            html_lines.append(f"<h2 style='color:#334155;font-size:17px;margin:20px 0 6px;'>{line[3:]}</h2>")
        elif line.startswith("### "):
            html_lines.append(f"<h3 style='color:#475569;font-size:14px;margin:14px 0 4px;'>{line[4:]}</h3>")
        elif line.startswith("---"):
            html_lines.append("<hr style='border:none;border-top:1px solid #e5e7eb;margin:20px 0;'>")
        elif line.startswith("- ") or line.startswith("* "):
            content = line[2:]
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content)
            html_lines.append(f"<li style='margin:4px 0;font-size:13px;'>{content}</li>")
        elif line.strip() == "":
            html_lines.append("<br>")
        else:
            content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            content = re.sub(r"`(.+?)`", r"<code style='background:#f3f4f6;padding:1px 5px;border-radius:3px;font-size:12px;'>\1</code>", content)
            html_lines.append(f"<p style='margin:4px 0;font-size:13px;line-height:1.6;color:#374151;'>{content}</p>")

    if in_table:
        html_lines.append("</table>")

    return "\n".join(html_lines)


def send_report_email(results: dict, report_file: str = None):
    """
    Build and send the weekly intelligence report email.
    Reads env vars: GMAIL_USER, GMAIL_APP_PASSWORD, NOTIFY_EMAIL.
    """
    gmail_user  = os.environ.get("GMAIL_USER", "")
    gmail_pass  = os.environ.get("GMAIL_APP_PASSWORD", "")
    notify_to   = os.environ.get("NOTIFY_EMAIL", gmail_user)

    if not gmail_user or not gmail_pass:
        print("[Notifier] GMAIL_USER / GMAIL_APP_PASSWORD not set — skipping email")
        return False

    # ── Build stats ───────────────────────────────────────────────────────────
    crawl  = results.get("crawl_results", {})
    agents = results.get("agent_results", {})
    trend  = agents.get("trend", {})
    now    = datetime.now()

    weixin_n = crawl.get("weixin", {}).get("new_articles", 0) or 0
    baidu_n  = crawl.get("baidu",  {}).get("total_results", 0) or 0
    zhihu_n  = crawl.get("zhihu",  {}).get("total_results", 0) or 0
    xhs_n    = crawl.get("xiaohongshu", {}).get("total_results", 0) or 0
    univ_n   = crawl.get("university",  {}).get("pages_crawled", 0) or 0
    total    = weixin_n + baidu_n + zhihu_n + xhs_n + univ_n

    top_kw = ", ".join([k for k, _ in (trend.get("top_keywords") or [])[:6]]) or "—"
    runtime = results.get("elapsed_s", "?")

    # ── Read report markdown if exists ────────────────────────────────────────
    report_html = ""
    if report_file and Path(report_file).exists():
        md = Path(report_file).read_text(encoding="utf-8")
        report_html = _md_to_html(md)

    # ── Compose HTML ──────────────────────────────────────────────────────────
    stat_box = lambda label, val, color: (
        f"<div style='text-align:center;padding:14px 10px;background:{color}20;"
        f"border:1px solid {color}40;border-radius:10px;'>"
        f"<div style='font-size:26px;font-weight:800;color:{color};'>{val}</div>"
        f"<div style='font-size:11px;color:#6b7280;margin-top:2px;'>{label}</div></div>"
    )

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f6fa;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:680px;margin:24px auto;background:#fff;border-radius:14px;
            overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.08);">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#1e3a5f 0%,#4f6ef7 100%);
              padding:32px 28px;color:#fff;">
    <div style="font-size:11px;letter-spacing:1px;opacity:.7;text-transform:uppercase;
                margin-bottom:8px;">
      Weekly Intelligence Report — {now.strftime('%d/%m/%Y')}
    </div>
    <div style="font-size:22px;font-weight:800;margin-bottom:4px;">
      China Program Intelligence
    </div>
    <div style="font-size:13px;opacity:.75;">
      Phân tích sâu · Weixin · Baidu · Zhihu · XHS · Đại học
    </div>
  </div>

  <!-- Stats row -->
  <div style="padding:24px 24px 8px;">
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;">
      {stat_box("WeChat", weixin_n, "#4f6ef7")}
      {stat_box("Baidu",  baidu_n,  "#06b6d4")}
      {stat_box("Zhihu",  zhihu_n,  "#8b5cf6")}
      {stat_box("XHS",    xhs_n,    "#ec4899")}
      {stat_box("ĐH",     univ_n,   "#34b87a")}
    </div>
  </div>

  <!-- Summary bar -->
  <div style="margin:16px 24px;background:#f8faff;border:1px solid #e0e7ff;
              border-radius:10px;padding:14px 18px;display:flex;
              justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
    <div>
      <span style="font-size:22px;font-weight:800;color:#1e3a5f;">{total}</span>
      <span style="font-size:13px;color:#6b7280;margin-left:6px;">records tổng cộng</span>
    </div>
    <div style="font-size:12px;color:#6b7280;">
      Runtime: <strong>{runtime}s</strong> &nbsp;·&nbsp;
      Mode: <strong>{results.get("mode","full")}</strong>
    </div>
  </div>

  <!-- Top keywords -->
  <div style="margin:0 24px 20px;">
    <div style="font-size:12px;color:#6b7280;margin-bottom:8px;font-weight:600;
                text-transform:uppercase;letter-spacing:.5px;">Top Keywords tuần này</div>
    <div style="font-size:13px;color:#374151;background:#fafbff;border:1px solid #e8eaf0;
                border-radius:8px;padding:10px 14px;">{top_kw}</div>
  </div>

  <!-- Source status table -->
  <div style="margin:0 24px 20px;">
    <div style="font-size:12px;color:#6b7280;margin-bottom:8px;font-weight:600;
                text-transform:uppercase;letter-spacing:.5px;">Trạng thái crawlers</div>
    <table style="width:100%;border-collapse:collapse;">
      <tr style="background:#f9fafb;">
        <th style="padding:8px 12px;text-align:left;font-size:12px;border:1px solid #e5e7eb;">Nguồn</th>
        <th style="padding:8px 12px;text-align:left;font-size:12px;border:1px solid #e5e7eb;">Records</th>
        <th style="padding:8px 12px;text-align:left;font-size:12px;border:1px solid #e5e7eb;">Trạng thái</th>
      </tr>
      {"".join([
        f"<tr><td style='padding:7px 12px;font-size:13px;border:1px solid #e5e7eb;'>{src}</td>"
        f"<td style='padding:7px 12px;font-size:13px;border:1px solid #e5e7eb;'>{cnt}</td>"
        f"<td style='padding:7px 12px;font-size:13px;border:1px solid #e5e7eb;'>"
        f"{'<span style=\"color:#16a34a;\">✓ OK</span>' if 'error' not in crawl.get(key,{}) else '<span style=\"color:#dc2626;\">✗ Lỗi</span>'}"
        f"</td></tr>"
        for src, key, cnt in [
            ("WeChat/Weixin", "weixin", weixin_n),
            ("Baidu", "baidu", baidu_n),
            ("Zhihu", "zhihu", zhihu_n),
            ("Xiaohongshu", "xiaohongshu", xhs_n),
            ("Đại học", "university", univ_n),
        ]
      ])}
    </table>
  </div>

  <!-- Full report -->
  {"<div style='margin:0 24px 24px;padding:20px;background:#fafbff;border:1px solid #e8eaf0;border-radius:10px;'><div style='font-size:12px;color:#6b7280;margin-bottom:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;'>Báo cáo đầy đủ</div>" + report_html + "</div>" if report_html else ""}

  <!-- Footer -->
  <div style="padding:16px 24px;background:#f5f6fa;border-top:1px solid #e8eaf0;
              text-align:center;font-size:11px;color:#9ca3af;">
    China Program Intelligence Platform &nbsp;·&nbsp;
    Chạy tự động trên Railway &nbsp;·&nbsp;
    {now.strftime('%d/%m/%Y %H:%M')} UTC
  </div>
</div>
</body>
</html>"""

    # ── Send ─────────────────────────────────────────────────────────────────
    subject = f"[Intelligence] Báo cáo tuần {now.strftime('%d/%m/%Y')} — {total} records"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = gmail_user
    msg["To"]      = notify_to
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, notify_to, msg.as_string())
        print(f"[Notifier] Report sent to {notify_to}")
        return True
    except Exception as e:
        print(f"[Notifier] Email failed: {e}")
        return False
