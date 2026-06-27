"""
Threema Gateway adapter.

Threema is the EU-pure messaging path: no US data touchpoint,
end-to-end encrypted, EU servers only.

Docs: https://gateway.threema.ch/en/developer/api
"""
import hashlib
import hmac
import time
import httpx

from src.messaging.base import InboundMessage, MessageProvider, MessagingAdapter
from src.config import get_settings


THREEMA_GATEWAY_API = "https://msgapi.threema.ch"


class ThreemaAdapter(MessagingAdapter):
    provider = MessageProvider.threema

    def __init__(self):
        s = get_settings()
        self._gateway_id = s.threema_gateway_id
        self._secret = s.threema_gateway_secret

    async def send_message(self, recipient_id: str, text: str) -> None:
        """Send a simple text message via Threema Gateway REST API."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{THREEMA_GATEWAY_API}/send_simple",
                data={
                    "from": self._gateway_id,
                    "to": recipient_id,
                    "secret": self._secret,
                    "text": text,
                },
            )
            resp.raise_for_status()

    def parse_inbound(self, payload: dict) -> InboundMessage:
        """Parse Threema Gateway callback payload."""
        return InboundMessage(
            provider=MessageProvider.threema,
            sender_id=payload.get("from", ""),
            text=payload.get("text", ""),
            timestamp=float(payload.get("date", time.time())),
            raw=payload,
        )

    def verify_webhook(self, payload: bytes, headers: dict) -> bool:
        """Threema Gateway webhooks are verified by checking the shared secret in the payload."""
        # In production: validate the MAC header threema provides.
        # For now we check that the posted secret matches ours.
        import json
        try:
            data = json.loads(payload)
            return data.get("secret") == self._secret
        except Exception:
            return False
