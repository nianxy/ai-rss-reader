import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import get_settings

settings = get_settings()


class EmailService:
    def send_html(self, subject: str, html: str) -> None:
        if not (settings.smtp_host and settings.email_from and settings.email_to):
            return

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.email_from
        msg['To'] = settings.email_to
        msg.attach(MIMEText(html, 'html', 'utf-8'))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.email_from, [settings.email_to], msg.as_string())
