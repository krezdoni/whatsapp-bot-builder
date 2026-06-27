"""
LLM-based structured extraction from OCR text.

Takes raw OCR text from a health document and asks the local LLM to pull out
structured health profile fields. Returns a partial HealthProfileData that can
be merged into the user's profile via health_profile.crud.merge_fhir_data().
"""
import json
import httpx

from src.config import get_settings
from src.health_profile.schemas import (
    HealthProfileData, Condition, Medication, Allergy,
    Vaccination, LabResult, Appointment
)


EXTRACTION_SYSTEM_PROMPT = """You are a medical document parser. Extract structured health data from the OCR text of a health document.

Return ONLY a valid JSON object with these keys (include only keys that have data):
{
  "conditions": [{"name": "...", "icd_code": "...", "onset_date": "YYYY-MM-DD", "status": "active|inactive"}],
  "medications": [{"name": "...", "dose": "...", "frequency": "...", "active": true}],
  "allergies": [{"substance": "...", "reaction": "...", "severity": "mild|moderate|severe"}],
  "vaccinations": [{"vaccine": "...", "date": "YYYY-MM-DD", "lot": "..."}],
  "lab_history": [{"test": "...", "value": "...", "unit": "...", "reference_range": "...", "date": "YYYY-MM-DD", "flag": "H|L|N"}],
  "appointments": [{"title": "...", "provider": "...", "date": "YYYY-MM-DD"}]
}

Rules:
- Return only JSON, no explanation text
- Only include fields that are clearly present in the document
- For dates use ISO format YYYY-MM-DD; if only year known use YYYY-01-01
- For lab flags: H=high, L=low, N=normal; omit if not indicated
- source field is always "document_upload"
- Do not invent or infer data not present in the document"""


async def extract_health_data_from_ocr(ocr_text: str) -> HealthProfileData:
    """
    Send OCR text to the local LLM and parse the structured response.
    Returns a HealthProfileData (partial — only fields found in the document).
    """
    if not ocr_text.strip():
        return HealthProfileData()

    s = get_settings()
    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": f"Extract health data from this document:\n\n{ocr_text[:8000]}"},
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{s.llm_base_url}/chat/completions",
            json={
                "model": s.llm_model,
                "messages": messages,
                "max_tokens": 2048,
                "temperature": 0.0,  # deterministic for extraction
            },
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()

    return _parse_extraction_response(raw)


def _parse_extraction_response(raw: str) -> HealthProfileData:
    """Parse LLM JSON response into HealthProfileData. Lenient — bad fields are skipped."""
    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return HealthProfileData()

    def safe_list(key, model_cls):
        items = data.get(key, [])
        result = []
        for item in items:
            try:
                item["source"] = "document_upload"
                result.append(model_cls(**item))
            except Exception:
                pass
        return result

    return HealthProfileData(
        conditions=safe_list("conditions", Condition),
        medications=safe_list("medications", Medication),
        allergies=safe_list("allergies", Allergy),
        vaccinations=safe_list("vaccinations", Vaccination),
        lab_history=safe_list("lab_history", LabResult),
        appointments=safe_list("appointments", Appointment),
    )
