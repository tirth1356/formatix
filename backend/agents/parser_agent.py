"""
Parser Agent: Extract raw text and structural information.
No LLM required. Supports DOCX, PDF, TXT.
"""
from pathlib import Path
import sys

# Allow importing from parent
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.docx_parser import parse_docx
from utils.pdf_parser import parse_pdf
from utils.txt_parser import parse_txt


class ParserAgent:
    def __init__(self):
        self.supported = {".docx", ".pdf", ".txt"}

    def parse(self, file_path: str) -> dict:
        """Dispatch by extension. Returns parsed_document JSON shape."""
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix not in self.supported:
            raise ValueError(f"Unsupported format: {suffix}. Use DOCX, PDF, or TXT.")
        if suffix == ".docx":
            return parse_docx(file_path)
        if suffix == ".pdf":
            return parse_pdf(file_path)
        return parse_txt(file_path)
