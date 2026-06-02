from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import date
from app.config import settings


def _score_badge(score: int) -> str:
    if score >= 85:
        return f'<span style="background:#22c55e;color:white;padding:2px 8px;border-radius:4px;font-size:12px;">{score}</span>'
    if score >= 70:
        return f'<span style="background:#f59e0b;color:white;padding:2px 8px;border-radius:4px;font-size:12px;">{score}</span>'
    return f'<span style="background:#6b7280;color:white;padding:2px 8px;border-radius:4px;font-size:12px;">{score}</span>'


def build_email_html(jobs: list[dict]) -> str:
    today = date.today().strftime("%B %d, %Y")
    rows = ""
    for job in jobs:
        badge = _score_badge(job["score"])
        rows += f"""
        <tr>
          <td style="padding:12px 8px;border-bottom:1px solid #e5e7eb;">
            <a href="{job['url']}" style="font-weight:600;color:#1d4ed8;text-decoration:none;">{job['title']}</a><br>
            <span style="color:#6b7280;font-size:13px;">{job['company']} · {job['location']}</span>
          </td>
          <td style="padding:12px 8px;border-bottom:1px solid #e5e7eb;text-align:center;">{badge}</td>
          <td style="padding:12px 8px;border-bottom:1px solid #e5e7eb;font-size:13px;color:#374151;">{job['score_reason']}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<body style="font-family:sans-serif;background:#f9fafb;padding:24px;">
  <div style="max-width:800px;margin:0 auto;background:white;border-radius:8px;padding:32px;box-shadow:0 1px 3px rgba(0,0,0,0.1);">
    <h1 style="font-size:22px;color:#111827;margin-bottom:4px;">Job Digest — {today}</h1>
    <p style="color:#6b7280;margin-bottom:24px;">Found <strong>{len(jobs)}</strong> relevant positions</p>
    <table style="width:100%;border-collapse:collapse;">
      <thead>
        <tr style="background:#f3f4f6;">
          <th style="padding:10px 8px;text-align:left;font-size:13px;color:#6b7280;">Position</th>
          <th style="padding:10px 8px;text-align:center;font-size:13px;color:#6b7280;">Score</th>
          <th style="padding:10px 8px;text-align:left;font-size:13px;color:#6b7280;">Why relevant</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    <p style="margin-top:24px;font-size:12px;color:#9ca3af;">
      Powered by HR Partner Agent · <a href="https://hr-partner.onrender.com">View dashboard</a>
    </p>
  </div>
</body>
</html>"""


def send_digest(jobs: list[dict]):
    if not jobs:
        print("[emailer] No jobs to send")
        return

    html = build_email_html(jobs)
    today = date.today().strftime("%B %d, %Y")

    message = Mail(
        from_email=settings.email_from,
        to_emails=settings.email_to,
        subject=f"Job Digest {today} — {len(jobs)} new positions",
        html_content=html,
    )

    try:
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        response = sg.send(message)
        print(f"[emailer] Sent to {settings.email_to}, status {response.status_code}")
    except Exception as e:
        print(f"[emailer] Send failed: {e}")
