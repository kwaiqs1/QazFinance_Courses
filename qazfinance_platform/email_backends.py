import json
import logging
import re
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


def _parse_name_email(value: str):
    """
    Parses:
      "Name <email@domain.com>" -> ("Name", "email@domain.com")
      "email@domain.com" -> (None, "email@domain.com")
    """
    if not value:
        return None, None
    m = re.match(r'^\s*(?:"?([^"]*)"?\s*)?<([^>]+)>\s*$', value)
    if m:
        name = (m.group(1) or "").strip() or None
        email = m.group(2).strip()
        return name, email
    return None, value.strip()


class SendGridAPIBackend(BaseEmailBackend):
    """
    Django email backend that sends emails via SendGrid v3 HTTP API.
    Requires env var SENDGRID_API_KEY.
    """

    api_url = "https://api.sendgrid.com/v3/mail/send"

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        api_key = getattr(settings, "SENDGRID_API_KEY", "") or ""
        if not api_key:
            if self.fail_silently:
                return 0
            raise RuntimeError("SENDGRID_API_KEY is not set")

        sent_count = 0

        for message in email_messages:
            try:
                from_name, from_email = _parse_name_email(message.from_email or settings.DEFAULT_FROM_EMAIL)
                if not from_email:
                    raise RuntimeError("DEFAULT_FROM_EMAIL is empty or invalid")

                # content: try HTML alternative first, fallback to text
                html = None
                if getattr(message, "alternatives", None):
                    for alt_body, mimetype in message.alternatives:
                        if mimetype == "text/html":
                            html = alt_body
                            break

                contents = []
                if message.body:
                    contents.append({"type": "text/plain", "value": message.body})
                if html:
                    contents.append({"type": "text/html", "value": html})
                if not contents:
                    contents = [{"type": "text/plain", "value": ""}]

                payload = {
                    "personalizations": [
                        {
                            "to": [{"email": addr} for addr in (message.to or [])],
                            "subject": message.subject or "",
                        }
                    ],
                    "from": {"email": from_email, **({"name": from_name} if from_name else {})},
                    "content": contents,
                }

                data = json.dumps(payload).encode("utf-8")
                req = urlrequest.Request(
                    self.api_url,
                    data=data,
                    method="POST",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )

                with urlrequest.urlopen(req, timeout=getattr(self, "timeout", 10)) as resp:
                    # SendGrid returns 202 Accepted on success
                    if 200 <= resp.status < 300:
                        sent_count += 1
                        logger.info("SendGrid: sent to=%s subject=%s", message.to, message.subject)
                    else:
                        raise RuntimeError(f"SendGrid unexpected status: {resp.status}")

            except HTTPError as e:
                body = ""
                try:
                    body = e.read().decode("utf-8", errors="replace")
                except Exception:
                    pass
                logger.error("SendGrid HTTPError %s %s body=%s", e.code, e.reason, body)
                if not self.fail_silently:
                    raise
            except URLError as e:
                logger.error("SendGrid URLError: %r", e)
                if not self.fail_silently:
                    raise
            except Exception as e:
                logger.error("SendGrid send failed: %r", e)
                if not self.fail_silently:
                    raise

        return sent_count
