"""Parse plain TXT files."""
from pathlib import Path


def parse_txt(file_path: str) -> dict:
    """
    Extract text from a TXT file.
    Returns dict with type, text, pages (estimated), raw_sections.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"TXT not found: {file_path}")

    text = path.read_text(encoding="utf-8", errors="replace")
    # Build raw_sections from paragraphs
    raw_sections = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        raw_sections.append({"heading": "", "level": 0, "content": block})

    if not raw_sections and text.strip():
        raw_sections = [{"heading": "", "level": 0, "content": text.strip()}]

    pages = max(1, len(text) // 3000)

    return {
        "type": "parsed_document",
        "text": text,
        "pages": pages,
        "raw_sections": raw_sections,
    }
