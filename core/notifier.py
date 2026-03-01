"""Email notification module using pure smtplib."""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from datetime import datetime


def send_digest_email(company_name: str, items: List[dict], recipient_email: str) -> bool:
    """Send digest email for company updates.

    Args:
        company_name: Name of the company
        items: List of items with url, title, published_date, source_label, summary
        recipient_email: Email to send to

    Returns:
        True if email sent successfully
    """
    if not items:
        print(f"No items to send for {company_name}")
        return True

    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    smtp_host = os.getenv("MAIL_SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("MAIL_SMTP_PORT", "587"))

    if not username or not password:
        print("Email credentials not configured in .env")
        return False

    try:
        # Create email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[Monitor] {company_name} - {len(items)} new update(s)"
        msg['From'] = username
        msg['To'] = recipient_email

        # Group items by source label
        items_by_source = {}
        for item in items:
            source = item.get('source_label', 'Unknown')
            if source not in items_by_source:
                items_by_source[source] = []
            items_by_source[source].append(item)

        # Build HTML body
        html_parts = [
            f"<h2>{company_name} - {len(items)} New Update(s)</h2>",
            f"<p><small>Generated at {datetime.utcnow().isoformat()}Z</small></p>",
        ]

        for source_label, source_items in items_by_source.items():
            html_parts.append(f"<h3>{source_label}</h3>")

            for item in source_items:
                url = item.get('url', '#')
                title = item.get('title', 'Untitled')
                pub_date = item.get('published_date', 'Unknown date')
                summary = item.get('summary', 'No summary available')

                html_parts.append(
                    f'<div style="margin-bottom: 20px; border: 1px solid #ddd; padding: 10px;">'
                    f'<h4><a href="{url}">{title}</a></h4>'
                    f'<p><small>Published: {pub_date}</small></p>'
                    f'<p>{summary}</p>'
                    f'<p><small><a href="{url}">Read more →</a></small></p>'
                    f'</div>'
                )

        html_body = "<html><body>" + "".join(html_parts) + "</body></html>"
        part = MIMEText(html_body, 'html')
        msg.attach(part)

        # Send email
        print(f"Connecting to {smtp_host}:{smtp_port}")
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)

        print(f"Email sent successfully to {recipient_email}")
        return True

    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
