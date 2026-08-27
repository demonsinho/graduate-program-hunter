"""Sends the digest email via Gmail SMTP."""
import smtplib
from email.message import EmailMessage


def send_digest(to_addr: str, subject: str, body: str, gmail_user: str, gmail_app_password: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = to_addr
    msg.set_content(body)

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(gmail_user, gmail_app_password)
        smtp.send_message(msg)
