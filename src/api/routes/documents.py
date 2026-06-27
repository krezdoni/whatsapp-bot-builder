"""
Document upload, OCR, and LLM extraction routes.

Supported document types: lab results, doctor letters, prescriptions.
All OCR runs on-server (Tesseract) — no PHI leaves the EU.
Extracted health data is merged into the user's health profile automatically.
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.auth.jwt_handler import get_current_user_id
from src.health_profile.models import Document, ConsentType
from src.health_profile.encryption import encrypt_field, encrypt_json, decrypt_field, decrypt_json
from src.health_profile.schemas import HealthProfileUpdate
from src.health_profile.crud import update_profile
from src.auth.consent import has_consent
from src.documents.ocr import extract_text
from src.documents.extractor import extract_health_data_from_ocr

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/tiff", "application/pdf"
}


class DocumentResponse(BaseModel):
    id: str
    filename: str
    document_type: str | None
    uploaded_at: str
    ocr_complete: bool
    fields_extracted: int


class DocumentListItem(BaseModel):
    id: str
    filename: str
    document_type: str | None
    uploaded_at: str


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    if not await has_consent(db, user_id, ConsentType.document_processing):
        raise HTTPException(
            403,
            "Document processing consent required. "
            "Please grant consent in the app settings first."
        )

    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(415, f"Unsupported file type: {content_type}. Allowed: PDF, JPEG, PNG.")

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(413, "File too large. Maximum 20 MB.")

    doc_type = _detect_document_type(file.filename or "", content)

    # OCR — synchronous for now (fast enough for <5 page docs)
    ocr_text: str | None = None
    extracted_count = 0
    try:
        ocr_text = await extract_text(content, content_type)
    except Exception:
        pass  # OCR failure is non-fatal; document is stored regardless

    # LLM extraction — run in background to avoid blocking the upload response
    doc_id = str(uuid.uuid4())
    doc = Document(
        id=doc_id,
        user_id=user_id,
        filename_enc=encrypt_field(file.filename or "upload", user_id),
        document_type=doc_type,
        ocr_text_enc=encrypt_field(ocr_text, user_id) if ocr_text else None,
    )
    db.add(doc)
    await db.flush()

    if ocr_text:
        background_tasks.add_task(
            _run_extraction_and_merge, doc_id, user_id, ocr_text
        )

    return DocumentResponse(
        id=doc_id,
        filename=file.filename or "upload",
        document_type=doc_type,
        uploaded_at=datetime.utcnow().isoformat(),
        ocr_complete=(ocr_text is not None),
        fields_extracted=extracted_count,
    )


@router.get("", response_model=list[DocumentListItem])
async def list_documents(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document)
        .where(Document.user_id == user_id)
        .order_by(Document.uploaded_at.desc())
        .limit(50)
    )
    docs = result.scalars().all()
    out = []
    for d in docs:
        try:
            filename = decrypt_field(d.filename_enc, user_id)
        except Exception:
            filename = "unknown"
        out.append(DocumentListItem(
            id=d.id,
            filename=filename,
            document_type=d.document_type,
            uploaded_at=d.uploaded_at.isoformat(),
        ))
    return out


async def _run_extraction_and_merge(doc_id: str, user_id: str, ocr_text: str) -> None:
    """Background task: LLM extraction → profile merge → store extracted data on document row."""
    from src.database import AsyncSessionLocal
    from src.health_profile.models import HealthProfileUpdate as _HPU

    async with AsyncSessionLocal() as db:
        try:
            profile_data = await extract_health_data_from_ocr(ocr_text)
            total = (
                len(profile_data.conditions) + len(profile_data.medications) +
                len(profile_data.allergies) + len(profile_data.lab_history) +
                len(profile_data.vaccinations) + len(profile_data.appointments)
            )
            if total > 0:
                update = HealthProfileUpdate(
                    conditions=profile_data.conditions or None,
                    medications=profile_data.medications or None,
                    allergies=profile_data.allergies or None,
                    vaccinations=profile_data.vaccinations or None,
                    lab_history=profile_data.lab_history or None,
                    appointments=profile_data.appointments or None,
                )
                await update_profile(db, user_id, update)

            # Persist extracted data on the document row
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if doc:
                doc.extracted_data_enc = encrypt_json(profile_data.model_dump(), user_id)
            await db.commit()
        except Exception:
            await db.rollback()


def _detect_document_type(filename: str, content: bytes) -> str | None:
    lower = filename.lower()
    if any(kw in lower for kw in ("lab", "blod", "blut", "analyse", "prøve", "labor")):
        return "lab_result"
    if any(kw in lower for kw in ("recept", "prescription", "rezept", "medicin")):
        return "prescription"
    if any(kw in lower for kw in ("brev", "letter", "brief", "rapport", "journal")):
        return "doctor_letter"
    if content[:4] == b"%PDF":
        return "pdf"
    if content[:2] in (b"\xff\xd8", b"\x89P"):
        return "image"
    return None
