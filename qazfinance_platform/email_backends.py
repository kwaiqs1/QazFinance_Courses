import json
import logging
import os
import urllib.request
import urllib.error

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class ResendEmailBackend(BaseEmailBackend):
    """
    Django Email Backend, который отправляет письма через Resend API (HTTPS),
    а не через SMTP. Это обходит блокировки SMTP на Railway.
    """

    API_URL = "https://api.resend.com/emails"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = (os.getenv("RESEND_API_KEY") or "").strip()

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        if not self.api_key:
            msg = "RESEND_API_KEY is not set"
            if self.fail_silently:
                logger.error(msg)
                return 0
            raise RuntimeError(msg)

        timeout = int(getattr(settings, "EMAIL_TIMEOUT", 10))
        sent = 0

        for message in email_messages:
            try:
                # Текст письма
                text_body = message.body or ""

                # Если есть HTML-альтернатива — отправим и её
                html_body = None
                if getattr(message, "alternatives", None):
                    for content, mimetype in message.alternatives:
                        if mimetype == "text/html":
                            html_body = content
                            break

                payload = {
                    "from": message.from_email,
                    "to": message.to,
                    "subject": message.subject or "",
                }
                if html_body:
                    payload["html"] = html_body
                    if text_body:
                        payload["text"] = text_body
                else:
                    payload["text"] = text_body

                data = json.dumps(payload).encode("utf-8")

                req = urllib.request.Request(self.API_URL, data=data, method="POST")
                req.add_header("Authorization", f"Bearer {self.api_key}")
                req.add_header("Content-Type", "application/json")

                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    status = getattr(resp, "status", 200)
                    if 200 <= status < 300:
                        sent += 1
                        logger.info("Resend: email sent to=%s subject=%s", message.to, message.subject)
                    else:
                        body = resp.read().decode("utf-8", errors="ignore")
                        err = f"Resend API error: HTTP {status} body={body}"
                        if self.fail_silently:
                            logger.error(err)
                        else:
                            raise RuntimeError(err)

            except Exception as e:
                if self.fail_silently:
                    logger.exception("Resend send failed: %r", e)
                else:
                    raise

        return sent
