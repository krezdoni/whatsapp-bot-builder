"""
Messaging abstraction layer.

All messaging adapters implement MessagingAdapter.
The rest of the application only calls send_message() and parses InboundMessage —
it never touches provider-specific payloads directly.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class MessageProvider(str, Enum):
    threema = "threema"
    whatsapp = "whatsapp"


@dataclass
class InboundMessage:
    provider: MessageProvider
    sender_id: str        # Threema ID or WhatsApp phone number
    text: str
    timestamp: float      # Unix epoch
    raw: dict = field(default_factory=dict)   # original webhook payload


@dataclass
class OutboundMessage:
    recipient_id: str     # Threema ID or WhatsApp phone number
    text: str
    provider: MessageProvider


class MessagingAdapter(ABC):
    """Base class for all messaging channel adapters."""

    provider: MessageProvider

    @abstractmethod
    async def send_message(self, recipient_id: str, text: str) -> None:
        """Send a text message to the recipient."""

    @abstractmethod
    def parse_inbound(self, payload: dict) -> InboundMessage:
        """Parse a raw webhook payload into a normalised InboundMessage."""

    @abstractmethod
    def verify_webhook(self, payload: bytes, headers: dict) -> bool:
        """Return True if the webhook signature is valid."""
