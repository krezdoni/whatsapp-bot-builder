"""
Message dispatcher — routes inbound webhooks to the right adapter,
runs the LLM, and sends the reply back through the same channel.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from src.messaging.base import InboundMessage, MessageProvider
from src.messaging.threema import ThreemaAdapter
from src.messaging.whatsapp import WhatsAppAdapter
from src.health_profile.crud import get_profile
from src.health_profile.models import User, Message
from src.llm.client import get_llm_client, ChatMessage
from src.llm.emergency import check_emergency
from src.auth.consent import has_consent
from src.health_profile.models import ConsentType
from src.health_profile.encryption import encrypt_field, decrypt_field
from sqlalchemy import select


_adapters = {
    MessageProvider.threema: ThreemaAdapter,
    MessageProvider.whatsapp: WhatsAppAdapter,
}


async def handle_inbound(
    inbound: InboundMessage,
    db: AsyncSession,
) -> None:
    """
    Full inbound message pipeline:
    1. Look up user by provider + sender_id
    2. Load recent conversation history (last 10 messages)
    3. Load health profile for context injection
    4. Call local LLM
    5. Store both messages (encrypted)
    6. Send reply via same channel
    """
    adapter_cls = _adapters[inbound.provider]
    adapter = adapter_cls()

    # Find user
    user = await _find_user(db, inbound.provider, inbound.sender_id)
    if user is None:
        await adapter.send_message(
            inbound.sender_id,
            "Welcome to your EU Health Companion. Please complete registration at our website first.",
        )
        return

    if not await has_consent(db, user.id, ConsentType.profile_storage):
        await adapter.send_message(
            inbound.sender_id,
            "Your consent is required before we can assist you. Please visit the app to review and accept.",
        )
        return

    # Emergency pre-filter — runs before LLM, must not be bypassed
    emergency_reply = check_emergency(inbound.text)
    if emergency_reply:
        await _store_message(db, user.id, inbound.provider.value, "inbound", inbound.text)
        await _store_message(db, user.id, inbound.provider.value, "outbound", emergency_reply)
        await adapter.send_message(inbound.sender_id, emergency_reply)
        return

    # Load history (last 10 messages)
    history = await _load_history(db, user.id)

    # Load health profile for context
    profile = await get_profile(db, user.id)
    profile_data = profile.model_dump() if profile else None

    # Store inbound message
    await _store_message(db, user.id, inbound.provider.value, "inbound", inbound.text)

    # LLM
    llm = get_llm_client()
    reply = await llm.chat(
        user_message=inbound.text,
        history=history,
        profile_data=profile_data,
    )

    # Store outbound message
    await _store_message(db, user.id, inbound.provider.value, "outbound", reply)

    # Send reply
    await adapter.send_message(inbound.sender_id, reply)


async def _find_user(
    db: AsyncSession, provider: MessageProvider, sender_id: str
) -> User | None:
    result = await db.execute(select(User).where(User.is_deleted == False))
    users = result.scalars().all()
    for user in users:
        if provider == MessageProvider.threema and user.threema_id_enc:
            try:
                if decrypt_field(user.threema_id_enc, user.id) == sender_id:
                    return user
            except Exception:
                pass
        elif provider == MessageProvider.whatsapp and user.phone_number_enc:
            try:
                if decrypt_field(user.phone_number_enc, user.id) == sender_id:
                    return user
            except Exception:
                pass
    return None


async def _load_history(db: AsyncSession, user_id: str) -> list[ChatMessage]:
    result = await db.execute(
        select(Message)
        .where(Message.user_id == user_id)
        .order_by(Message.timestamp.desc())
        .limit(10)
    )
    rows = list(reversed(result.scalars().all()))
    history = []
    for row in rows:
        try:
            text = decrypt_field(row.content_enc, user_id)
            role = "user" if row.direction == "inbound" else "assistant"
            history.append(ChatMessage(role=role, content=text))
        except Exception:
            pass
    return history


async def _store_message(
    db: AsyncSession, user_id: str, provider: str, direction: str, text: str
) -> None:
    msg = Message(
        user_id=user_id,
        direction=direction,
        provider=provider,
        content_enc=encrypt_field(text, user_id),
    )
    db.add(msg)
    await db.flush()
