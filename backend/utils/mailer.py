"""Outgoing email seam.

With SMTP_HOST set, mail is sent via SMTP. Without it the message is only logged, so
development and tests work with no mail provider.
TODO(email): drop in SMTP_* (or Supabase/Resend/SES) credentials in backend/.env.
"""
import smtplib
from email.message import EmailMessage

from flask import current_app


def send_email(to, subject, body):
    cfg = current_app.config
    host = cfg.get('SMTP_HOST')
    if not host:
        current_app.logger.info('[mail disabled] to=%s subject=%s\n%s', to, subject, body)
        return False
    msg = EmailMessage()
    msg['From'] = cfg.get('MAIL_FROM') or 'SaverAI <no-reply@saverai.local>'
    msg['To'] = to
    msg['Subject'] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(host, int(cfg.get('SMTP_PORT') or 587), timeout=15) as s:
            s.starttls()
            if cfg.get('SMTP_USER'):
                s.login(cfg['SMTP_USER'], cfg.get('SMTP_PASSWORD', ''))
            s.send_message(msg)
        return True
    except (OSError, smtplib.SMTPException) as exc:
        current_app.logger.error('Email send failed: %s', exc)
        return False
