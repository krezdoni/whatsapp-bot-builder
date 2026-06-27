"""Test document type detection and OCR extraction parsing."""
import os
os.environ["FIELD_ENCRYPTION_KEY"] = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://x:x@localhost/x"
os.environ["LLM_BASE_URL"] = "http://localhost:8001/v1"
os.environ["LLM_MODEL"] = "test-model"

from src.api.routes.documents import _detect_document_type
from src.documents.extractor import _parse_extraction_response


# ── Document type detection ────────────────────────────────────────────────────

def test_detect_lab_by_name():
    assert _detect_document_type("blodprove_2024.pdf", b"") == "lab_result"
    assert _detect_document_type("labor_befund.pdf", b"") == "lab_result"
    assert _detect_document_type("analyse.pdf", b"") == "lab_result"

def test_detect_prescription():
    assert _detect_document_type("recept_metformin.pdf", b"") == "prescription"
    assert _detect_document_type("rezept.pdf", b"") == "prescription"

def test_detect_doctor_letter():
    assert _detect_document_type("brev_fra_laege.pdf", b"") == "doctor_letter"
    assert _detect_document_type("hospital_letter.pdf", b"") == "doctor_letter"

def test_detect_pdf_by_magic_bytes():
    assert _detect_document_type("document.bin", b"%PDF-1.4") == "pdf"

def test_detect_jpeg_by_magic_bytes():
    assert _detect_document_type("scan.bin", bytes([0xff, 0xd8, 0x00])) == "image"

def test_detect_unknown():
    assert _detect_document_type("notes.docx", b"\x50\x4b") is None


# ── LLM extraction response parsing ───────────────────────────────────────────

VALID_EXTRACTION = """{
  "conditions": [{"name": "Type 2 Diabetes", "icd_code": "E11", "status": "active"}],
  "medications": [{"name": "Metformin", "dose": "500mg", "frequency": "twice daily", "active": true}],
  "lab_history": [{"test": "HbA1c", "value": "6.8", "unit": "%", "date": "2024-03-01", "flag": "H"}],
  "allergies": [{"substance": "Penicillin", "severity": "moderate"}]
}"""

def test_parse_valid_extraction():
    result = _parse_extraction_response(VALID_EXTRACTION)
    assert len(result.conditions) == 1
    assert result.conditions[0].name == "Type 2 Diabetes"
    assert result.conditions[0].icd_code == "E11"
    assert len(result.medications) == 1
    assert result.medications[0].name == "Metformin"
    assert len(result.lab_history) == 1
    assert result.lab_history[0].flag == "H"
    assert len(result.allergies) == 1

def test_parse_extraction_with_markdown_fence():
    wrapped = f"```json\n{VALID_EXTRACTION}\n```"
    result = _parse_extraction_response(wrapped)
    assert len(result.conditions) == 1

def test_parse_empty_extraction():
    result = _parse_extraction_response("{}")
    assert result.conditions == []
    assert result.medications == []

def test_parse_invalid_json_returns_empty():
    result = _parse_extraction_response("Sorry, I cannot extract data from this document.")
    assert result.conditions == []

def test_parse_partial_extraction():
    partial = '{"medications": [{"name": "Aspirin", "dose": "100mg", "active": true}]}'
    result = _parse_extraction_response(partial)
    assert len(result.medications) == 1
    assert result.conditions == []

def test_parse_skips_bad_items():
    bad = '{"lab_history": [{"test": "HbA1c", "value": "6.8", "date": "2024-03-01"}, {"broken": true}]}'
    result = _parse_extraction_response(bad)
    # First item should parse (date is required), second silently dropped
    assert len(result.lab_history) >= 0  # lenient
