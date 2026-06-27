"""Test messaging abstraction layer — webhook parsing and adapter interface."""
import os
import time
os.environ["FIELD_ENCRYPTION_KEY"] = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://x:x@localhost/x"
os.environ["THREEMA_GATEWAY_ID"] = "*TESTID"
os.environ["THREEMA_GATEWAY_SECRET"] = "test-secret-threema"
os.environ["SINCH_APP_ID"] = "test-sinch-id"
os.environ["SINCH_APP_SECRET"] = "test-sinch-secret"

from src.messaging.threema import ThreemaAdapter
from src.messaging.whatsapp import WhatsAppAdapter
from src.messaging.base import MessageProvider


def test_threema_parse_inbound():
    adapter = ThreemaAdapter()
    payload = {
        "from": "*ABC123",
        "text": "What does my HbA1c result mean?",
        "date": 1700000000,
        "secret": "test-secret-threema",
    }
    msg = adapter.parse_inbound(payload)
    assert msg.provider == MessageProvider.threema
    assert msg.sender_id == "*ABC123"
    assert msg.text == "What does my HbA1c result mean?"
    assert msg.timestamp == 1700000000.0


def test_threema_verify_webhook_valid():
    import json
    adapter = ThreemaAdapter()
    payload = json.dumps({"secret": "test-secret-threema", "from": "*X", "text": "hi"}).encode()
    assert adapter.verify_webhook(payload, {}) is True


def test_threema_verify_webhook_invalid():
    import json
    adapter = ThreemaAdapter()
    payload = json.dumps({"secret": "wrong-secret", "from": "*X", "text": "hi"}).encode()
    assert adapter.verify_webhook(payload, {}) is False


def test_whatsapp_parse_inbound():
    adapter = WhatsAppAdapter()
    payload = {
        "contact_id": "+4512345678",
        "contact_message": {
            "text_message": {"text": "Hej, hvad betyder mit blodtryk?"}
        },
        "accept_time": "2024-01-15T10:30:00Z",
    }
    msg = adapter.parse_inbound(payload)
    assert msg.provider == MessageProvider.whatsapp
    assert msg.sender_id == "+4512345678"
    assert "blodtryk" in msg.text


def test_adapter_interface_threema():
    adapter = ThreemaAdapter()
    assert adapter.provider == MessageProvider.threema
    assert callable(adapter.send_message)
    assert callable(adapter.parse_inbound)
    assert callable(adapter.verify_webhook)


def test_adapter_interface_whatsapp():
    adapter = WhatsAppAdapter()
    assert adapter.provider == MessageProvider.whatsapp
