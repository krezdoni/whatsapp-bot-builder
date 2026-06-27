"""
Document upload, OCR, and LLM extraction routes.
Phase 2 feature — skeleton only in Phase 1.

Supported document types: lab results, doctor letters, prescriptions, insurance cards.
All OCR runs on-server (Tesseract) or EU-region Cloud Vision — no PHI leaves the EU.
"""
import io
import uuid
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.auth.jwt_handler import get_current_user_id
from src.health_profile.models import Document
from src.health_profile.encryption import encrypt_field, encrypt_json
from src.auth.consent import has_consent
from src.health_profile.models import ConsentType

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: str
    filename: str
    document_type: str | None
    uploaded_at: str


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
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

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:  # 20 MB limit
        raise HTTPException(413, "File too large. Maximum 20 MB.")

    doc_type = _detect_document_type(file.filename or "", content)

    # Phase 2: run OCR + LLM extraction here
    # ocr_text = await run_ocr(content, file.content_type)
    # extracted = await llm_extract_health_data(ocr_text)
    ocr_text = None
    extracted = None

    doc_id = str(uuid.uuid4())
    doc = Document(
        id=doc_id,
        user_id=user_id,
        filename_enc=encrypt_field(file.filename or "upload", user_id),
        document_type=doc_type,
        ocr_text_enc=encrypt_field(ocr_text, user_id) if ocr_text else None,
        extracted_data_enc=encrypt_json(extracted, user_id) if extracted else None,
    )
    db.add(doc)
    await db.flush()

    from datetime import datetime
    return DocumentResponse(
        id=doc_id,
        filename=file.filename or "upload",
        document_type=doc_type,
        uploaded_at=datetime.utcnow().isoformat(),
    )


def _detect_document_type(filename: str, content: bytes) -> str | None:
    lower = filename.lower()
    if "lab" in lower or "blod" in lower or "blut" in lower:
        return "lab_result"
    if "recept" in lower or "prescription" in lower or "rezept" in lower:
        return "prescription"
    if "brev" in lower or "letter" in lower or "brief" in lower:
        return "doctor_letter"
    if content[:4] == b"%PDF":
        return "pdf"
    if content[:2] in (b"\xff\xd8", b"\x89P"):  # JPEG or PNG
        return "image"
    return None
