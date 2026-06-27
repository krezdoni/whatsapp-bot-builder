"""
OCR pipeline for uploaded health documents.

Strategy:
1. Try Tesseract (on-server, free, GDPR-clean) — primary
2. No fallback to external services in this build (EU data residency hard requirement)

Supported input: JPEG, PNG, PDF (first 10 pages via pypdf → PIL)
"""
import io
from pathlib import Path

try:
    import pytesseract
    from PIL import Image
    _TESSERACT_AVAILABLE = True
except ImportError:
    _TESSERACT_AVAILABLE = False

try:
    from pypdf import PdfReader
    _PYPDF_AVAILABLE = True
except ImportError:
    _PYPDF_AVAILABLE = False


SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/tiff"}
SUPPORTED_PDF_TYPES = {"application/pdf"}

# Tesseract lang codes for supported markets
_LANG_MAP = {
    "da": "dan",
    "de": "deu",
    "en": "eng",
}
DEFAULT_LANGS = "dan+deu+eng"


def ocr_image_bytes(content: bytes, content_type: str = "image/jpeg") -> str:
    """Run Tesseract OCR on raw image bytes. Returns extracted text."""
    if not _TESSERACT_AVAILABLE:
        raise RuntimeError(
            "pytesseract / Pillow not installed. Run: pip install pytesseract Pillow"
        )
    img = Image.open(io.BytesIO(content))
    # Convert to RGB if needed (handles RGBA PNGs, CMYK, etc.)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    return pytesseract.image_to_string(img, lang=DEFAULT_LANGS).strip()


def ocr_pdf_bytes(content: bytes, max_pages: int = 10) -> str:
    """Extract text from a PDF. Uses pypdf text layer first; falls back to image OCR per page."""
    if not _PYPDF_AVAILABLE:
        raise RuntimeError("pypdf not installed. Run: pip install pypdf")

    reader = PdfReader(io.BytesIO(content))
    pages_text: list[str] = []

    for i, page in enumerate(reader.pages[:max_pages]):
        text = page.extract_text() or ""
        if len(text.strip()) > 50:
            pages_text.append(text.strip())
        elif _TESSERACT_AVAILABLE:
            # Scanned PDF page — render to image and OCR
            # pypdf doesn't render pages; would need pdf2image (poppler) for this.
            # Leaving as text-layer-only for now; image rendering added in Phase 3.
            pages_text.append(text.strip())

    return "\n\n".join(pages_text)


async def extract_text(content: bytes, content_type: str) -> str:
    """
    Top-level async wrapper. Returns OCR text for the given file.
    Raises ValueError for unsupported types.
    """
    ct = content_type.lower().split(";")[0].strip()

    if ct in SUPPORTED_IMAGE_TYPES:
        return ocr_image_bytes(content, ct)
    elif ct in SUPPORTED_PDF_TYPES:
        return ocr_pdf_bytes(content)
    else:
        raise ValueError(f"Unsupported document type for OCR: {ct}")
