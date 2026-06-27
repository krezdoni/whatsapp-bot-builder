"""Initial schema — users, consents, health profiles, messages, documents

Revision ID: 0001
Revises:
Create Date: 2026-06-27
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("phone_number_enc", sa.Text, nullable=True),
        sa.Column("threema_id_enc", sa.Text, nullable=True),
        sa.Column("email_enc", sa.Text, nullable=True),
        sa.Column("messaging_channel", sa.String(20), nullable=False),
        sa.Column("mitid_sub_enc", sa.Text, nullable=True),
        sa.Column("gematik_sub_enc", sa.Text, nullable=True),
        sa.Column("whatsapp_consent_timestamp", sa.DateTime, nullable=True),
        sa.Column("whatsapp_consent_text_version", sa.String(50), nullable=True),
        sa.Column("data_retention_years", sa.Integer, server_default="2"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("scheduled_deletion_at", sa.DateTime, nullable=True),
        sa.Column("is_deleted", sa.Boolean, server_default="false"),
    )

    op.create_table(
        "user_consents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("consent_type", sa.String(50), nullable=False),
        sa.Column("granted", sa.Boolean, nullable=False),
        sa.Column("consent_text_version", sa.String(50), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("timestamp", sa.DateTime, server_default=sa.text("now()")),
    )
    op.create_index("ix_user_consents_user_id", "user_consents", ["user_id"])
    op.create_index("ix_user_consents_type", "user_consents", ["consent_type"])

    op.create_table(
        "health_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("conditions_enc", sa.Text, nullable=True),
        sa.Column("medications_enc", sa.Text, nullable=True),
        sa.Column("allergies_enc", sa.Text, nullable=True),
        sa.Column("providers_enc", sa.Text, nullable=True),
        sa.Column("vaccinations_enc", sa.Text, nullable=True),
        sa.Column("lab_history_enc", sa.Text, nullable=True),
        sa.Column("appointments_enc", sa.Text, nullable=True),
        sa.Column("notes_enc", sa.Text, nullable=True),
        sa.Column("fhir_last_synced_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()")),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("content_enc", sa.Text, nullable=False),
        sa.Column("timestamp", sa.DateTime, server_default=sa.text("now()")),
    )
    op.create_index("ix_messages_user_id", "messages", ["user_id"])
    op.create_index("ix_messages_timestamp", "messages", ["timestamp"])

    op.create_table(
        "documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("filename_enc", sa.Text, nullable=False),
        sa.Column("document_type", sa.String(50), nullable=True),
        sa.Column("ocr_text_enc", sa.Text, nullable=True),
        sa.Column("extracted_data_enc", sa.Text, nullable=True),
        sa.Column("uploaded_at", sa.DateTime, server_default=sa.text("now()")),
    )
    op.create_index("ix_documents_user_id", "documents", ["user_id"])


def downgrade() -> None:
    op.drop_table("documents")
    op.drop_table("messages")
    op.drop_table("health_profiles")
    op.drop_table("user_consents")
    op.drop_table("users")
