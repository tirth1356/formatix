"""Parse PDF files using pdfplumber; optional PyMuPDF fallback."""
from pathlib import Path
import pdfplumber

try:
    import fitz  # PyMuPDF (optional)
except ImportError:
    fitz = None


def parse_pdf(file_path: str) -> dict:
    """
    Extract raw text and structural information from a PDF file.
    Uses pdfplumber for text; PyMuPDF for page count and fallback.
    Returns dict with type, text, pages, raw_sections.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    text_parts = []
    raw_sections = []

    with pdfplumber.open(file_path) as pdf:
        pages_count = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
                # Treat each page as a raw section for simplicity
                raw_sections.append({
                    "heading": f"Page {i + 1}",
                    "level": 0,
                    "content": page_text.strip(),
                })

    full_text = "\n\n".join(text_parts) if text_parts else ""

    # If pdfplumber got nothing and PyMuPDF is available, try it
    if not full_text.strip() and fitz is not None:
        doc = fitz.open(file_path)
        pages_count = len(doc)
        for i in range(pages_count):
            page = doc[i]
            page_text = page.get_text()
            if page_text:
                text_parts.append(page_text)
                raw_sections.append({
                    "heading": f"Page {i + 1}",
                    "level": 0,
                    "content": page_text.strip(),
                })
        full_text = "\n\n".join(text_parts)
        doc.close()

    return {
        "type": "parsed_document",
        "text": full_text,
        "pages": pages_count,
        "raw_sections": raw_sections,
    }
