"""
Webhook endpoints for inbound messages from Threema and WhatsApp/Sinch.
Also provides a direct chat endpoint for the PWA.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.messaging.base import MessageProvider
from src.messaging.threema import ThreemaAdapter
from src.messaging.whatsapp import WhatsAppAdapter
from src.messaging.dispatcher import handle_inbound
from src.auth.jwt_handler import get_current_user_id
from src.health_profile.crud import get_profile
from src.llm.client import get_llm_client, ChatMessage
from src.health_profile.encryption import encrypt_field, decrypt_field
from src.health_profile.models import Message
from src.llm.emergency import check_emergency
from sqlalchemy import select

router = APIRouter(prefix="/messaging", tags=["messaging"])


@router.post("/webhook/threema")
async def threema_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()
    adapter = ThreemaAdapter()
    if not adapter.verify_webhook(body, dict(request.headers)):
        raise HTTPException(403, "Invalid webhook signature")

    payload = await request.json()
    inbound = adapter.parse_inbound(payload)
    background_tasks.add_task(handle_inbound, inbound, db)
    return {"status": "accepted"}


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()
    adapter = WhatsAppAdapter()
    if not adapter.verify_webhook(body, dict(request.headers)):
        raise HTTPException(403, "Invalid webhook signature")

    payload = await request.json()
    inbound = adapter.parse_inbound(payload)
    background_tasks.add_task(handle_inbound, inbound, db)
    return {"status": "accepted"}


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def pwa_chat(
    body: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Direct chat endpoint for the PWA (no messaging channel needed)."""
    # Emergency pre-filter — must run before LLM
    emergency_reply = check_emergency(body.message)
    if emergency_reply:
        db.add(Message(user_id=user_id, direction="inbound", provider="pwa",
                       content_enc=encrypt_field(body.message, user_id)))
        db.add(Message(user_id=user_id, direction="outbound", provider="pwa",
                       content_enc=encrypt_field(emergency_reply, user_id)))
        await db.flush()
        return ChatResponse(reply=emergency_reply)

    # Load history
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

    # Load health profile
    profile = await get_profile(db, user_id)
    profile_data = profile.model_dump() if profile else None

    # Store inbound
    db.add(Message(
        user_id=user_id,
        direction="inbound",
        provider="pwa",
        content_enc=encrypt_field(body.message, user_id),
    ))
    await db.flush()

    # LLM
    llm = get_llm_client()
    reply = await llm.chat(body.message, history=history, profile_data=profile_data)

    # Store outbound
    db.add(Message(
        user_id=user_id,
        direction="outbound",
        provider="pwa",
        content_enc=encrypt_field(reply, user_id),
    ))
    await db.flush()

    return ChatResponse(reply=reply)


@router.get("/history")
async def get_chat_history(
    limit: int = 20,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Message)
        .where(Message.user_id == user_id)
        .order_by(Message.timestamp.desc())
        .limit(limit)
    )
    rows = list(reversed(result.scalars().all()))
    messages = []
    for row in rows:
        try:
            text = decrypt_field(row.content_enc, user_id)
            messages.append({
                "id": row.id,
                "direction": row.direction,
                "provider": row.provider,
                "text": text,
                "timestamp": row.timestamp.isoformat(),
            })
        except Exception:
            pass
    return {"messages": messages}
