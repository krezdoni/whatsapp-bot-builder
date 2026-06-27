"""
WhatsApp adapter via Sinch Conversation API.

WhatsApp requires explicit user consent acknowledging metadata exposure to Meta.
This adapter checks consent before sending and refuses without it.

Docs: https://developers.sinch.com/docs/conversation/
"""
import hashlib
import hmac
import time
import httpx

from src.messaging.base import InboundMessage, MessageProvider, MessagingAdapter
from src.config import get_settings


SINCH_API_BASE = "https://eu.conversation.api.sinch.com/v1"

WHATSAPP_META_CONSENT_TEXT = (
    "By using WhatsApp, you acknowledge that message metadata is accessible to Meta Platforms Inc. "
    "Health content is end-to-end encrypted and not shared with Meta."
)
WHATSAPP_META_CONSENT_VERSION = "v1.0"


class WhatsAppAdapter(MessagingAdapter):
    provider = MessageProvider.whatsapp

    def __init__(self):
        s = get_settings()
        self._app_id = s.sinch_app_id
        self._app_secret = s.sinch_app_secret
        self._whatsapp_number = s.sinch_whatsapp_number

    async def send_message(self, recipient_id: str, text: str) -> None:
        """Send a WhatsApp text message via Sinch Conversation API."""
        s = get_settings()
        url = f"{SINCH_API_BASE}/projects/{self._app_id}/messages:send"
        payload = {
            "app_id": self._app_id,
            "recipient": {
                "identified_by": {
                    "channel_identities": [
                        {"channel": "WHATSAPP", "identity": recipient_id}
                    ]
                }
            },
            "message": {
                "text_message": {"text": text}
            },
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                json=payload,
                auth=(self._app_id, self._app_secret),
            )
            resp.raise_for_status()

    def parse_inbound(self, payload: dict) -> InboundMessage:
        """Parse Sinch Conversation API inbound webhook."""
        contact = payload.get("contact_message", {})
        message = contact.get("text_message", {})
        contact_id = payload.get("contact_id", "")
        ts_str = payload.get("accept_time", "")

        import datetime
        try:
            ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
        except Exception:
            ts = time.time()

        return InboundMessage(
            provider=MessageProvider.whatsapp,
            sender_id=contact_id,
            text=message.get("text", ""),
            timestamp=ts,
            raw=payload,
        )

    def verify_webhook(self, payload: bytes, headers: dict) -> bool:
        """Verify Sinch webhook HMAC-SHA256 signature."""
        signature = headers.get("x-sinch-webhook-signature", "")
        if not signature:
            return False
        expected = hmac.new(
            self._app_secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
