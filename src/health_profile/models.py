"""
SQLAlchemy ORM models for the health profile layer.
All personal and health fields are stored encrypted (Fernet, per-user keys).
Plain-text columns: non-PHI identifiers only (UUIDs, timestamps, enum flags).
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class MessagingChannel(str, PyEnum):
    threema = "threema"
    whatsapp = "whatsapp"


class ConsentType(str, PyEnum):
    profile_storage = "profile_storage"
    fhir_pull = "fhir_pull"
    document_processing = "document_processing"
    messaging_channel = "messaging_channel"
    whatsapp_meta_exposure = "whatsapp_meta_exposure"


class MessageDirection(str, PyEnum):
    inbound = "inbound"
    outbound = "outbound"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # Encrypted fields stored as text tokens
    phone_number_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    threema_id_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_enc: Mapped[str | None] = mapped_column(Text, nullable=True)

    messaging_channel: Mapped[str] = mapped_column(String(20), nullable=False)
    # FHIR identity tokens (encrypted)
    mitid_sub_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    gematik_sub_enc: Mapped[str | None] = mapped_column(Text, nullable=True)

    # WhatsApp-specific consent fields (non-PHI)
    whatsapp_consent_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    whatsapp_consent_text_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    data_retention_years: Mapped[int] = mapped_column(Integer, default=2)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    scheduled_deletion_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    consents: Mapped[list["UserConsent"]] = relationship(back_populates="user", lazy="select")
    health_profile: Mapped["HealthProfile | None"] = relationship(back_populates="user", uselist=False)
    messages: Mapped[list["Message"]] = relationship(back_populates="user", lazy="select")
    documents: Mapped[list["Document"]] = relationship(back_populates="user", lazy="select")


class UserConsent(Base):
    __tablename__ = "user_consents"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    consent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    consent_text_version: Mapped[str] = mapped_column(String(50), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="consents")


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)

    # All health data encrypted as JSON blobs
    conditions_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    medications_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    allergies_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    providers_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    vaccinations_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    lab_history_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    appointments_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes_enc: Mapped[str | None] = mapped_column(Text, nullable=True)

    fhir_last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="health_profile")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    content_enc: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="messages")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    filename_enc: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ocr_text_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_data_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="documents")
