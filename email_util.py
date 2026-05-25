"""
email_util.py — Unified email sender.
Uses Resend API (HTTPS) if RESEND_API_KEY is set, otherwise falls back to Gmail SMTP.
Railway blocks outbound SMTP, so Resend is required on Railway.
"""
import os, smtplib
import requests as _req
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(subject: str, body_text: str = "", body_html: str = "") -> bool:
    notify_to = os.environ.get("NOTIFY_EMAIL", os.environ.get("GMAIL_USER", ""))
    if not notify_to:
        print("[Email] No NOTIFY_EMAIL set — skipping")
        return False

    resend_key = os.environ.get("RESEND_API_KEY", "")
    if resend_key:
        return _send_via_resend(resend_key, notify_to, subject, body_text, body_html)
    return _send_via_smtp(notify_to, subject, body_text, body_html)


def _send_via_resend(api_key: str, to: str, subject: str, body_text: str, body_html: str) -> bool:
    from_addr = os.environ.get("RESEND_FROM", "China Programs <onboarding@resend.dev>")
    payload = {"from": from_addr, "to": [to], "subject": subject}
    if body_html:
        payload["html"] = body_html
    if body_text:
        payload["text"] = body_text
    try:
        resp = _req.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=15,
        )
        if resp.status_code in (200, 201):
            print(f"[Email] Sent via Resend to {to}")
            return True
        print(f"[Email] Resend error {resp.status_code}: {resp.text[:200]}")
        return False
    except Exception as e:
        print(f"[Email] Resend exception: {e}")
        return False


def _send_via_smtp(to: str, subject: str, body_text: str, body_html: str) -> bool:
    user = os.environ.get("GMAIL_USER", "")
    pw   = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not user or not pw:
        print("[Email] No SMTP credentials — skipping")
        return False
    if body_html:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(body_text or "", "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))
    else:
        msg = MIMEText(body_text, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"]    = user
    msg["To"]      = to
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as s:
            s.starttls()
            s.login(user, pw)
            s.sendmail(user, [to], msg.as_string())
        print(f"[Email] Sent via SMTP to {to}")
        return True
    except Exception as e:
        print(f"[Email] SMTP error: {e}")
        return False
