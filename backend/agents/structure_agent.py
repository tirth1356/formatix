"""
Structure Agent: Detect manuscript structure using phi3 (or Groq in cloud).
Extracts title, authors, abstract, sections, tables, figures, citations, references.

FIXES:
- Filters out page-marker pseudo-sections ("Page 1", \subsubsection{Page 2}, etc.)
  that PDF extraction inserts into raw_sections — these caused real body content to
  get labelled with "Page N" headings and never matched by the IEEE section matcher.
- Content from page-marker sections is re-attached to the last real section instead
  of being silently dropped.
- Smarter section detection: regex-based fallback when LLM truncates or fails
- Better handling of raw_sections injection (preserves headings + content faithfully)
- Validates & normalises all fields (no empty dicts, no None cascades)
- Added word count tracking per section for formatting hints
- Detects citation format (numeric vs. author-year) from raw text
- Improved JSON extraction: handles multi-line edge cases
- Problem statement detection is more robust
- Authors now cleaned (removes emails, affiliations, numbering)
"""
import json
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


SYSTEM_STRUCTURE = """You are an expert at analyzing academic manuscripts. Extract structure only. Respond with valid JSON only — no markdown fences, no explanation, no preamble."""

PROMPT_STRUCTURE = """Analyze the academic manuscript text below and extract its full structure.

Return a SINGLE JSON object with EXACTLY these keys (use empty strings or empty arrays if a field is not found — NEVER omit a key):

- "title": string — the manuscript title (not the journal name)
- "authors": array of strings — author full names only, no affiliations or emails
- "affiliation": string — the institution/affiliation associated with the authors
- "course_info": object with keys:
    - "course": string (e.g., "English 101")
    - "instructor": string (e.g., "Dr. Smith")
    - "date": string (e.g., "7 March 2026")
- "abstract": string — full abstract text
- "keywords": array of strings — keywords if listed
- "problem_statement": string — 1–2 sentence problem statement extracted from Introduction
- "important_text": array of strings — 3–5 key claims, findings, or highlights
- "sections": array of objects, each with:
    - "heading": string (exact heading text)
    - "level": integer (1=major, 2=sub, 3=sub-sub)
    - "content": string (full text of the section)
    - "word_count": integer
- "tables": array of strings — one entry per detected table (caption or first row)
- "figures": array of strings — figure captions or labels
- "citations": array of strings — all in-text citations like (Author, 2020) or [1] or [1,2,3]
- "citation_format": string — detected format: "author-year", "numeric", "numeric-superscript", or "unknown"
- "references": array of strings — each full reference entry as a separate string
- "word_count_total": integer — estimated total word count of the manuscript

Manuscript text (first 6000 chars):
---
{text}
---

Return ONLY the JSON object. Absolutely no markdown. No text outside the JSON."""


# Standard section headings across styles — used for regex-based fallback detection
KNOWN_SECTION_HEADINGS = [
    r"abstract",
    r"introduction",
    r"background(?: and related work)?",
    r"related work",
    r"literature review",
    r"methodology|methods|materials and methods",
    r"experimental(?: setup)?",
    r"results(?: and discussion)?",
    r"discussion",
    r"conclusion(s)?",
    r"future work",
    r"acknowledgements?",
    r"references?|bibliography|works cited",
    r"appendix(?:es)?",
    r"supplementary(?: material)?",
]

_SECTION_PATTERN = re.compile(
    r'^(?:(?:[IVX]+\.?|[0-9]+\.)\s+)?(' + '|'.join(KNOWN_SECTION_HEADINGS) + r')\s*$',
    re.IGNORECASE | re.MULTILINE,
)

_CITATION_NUMERIC      = re.compile(r'\[(\d+(?:,\s*\d+)*)\]')
_CITATION_AUTHOR_YEAR  = re.compile(
    r'\(([A-Z][a-zA-Z\-]+(?:\s+et\s+al\.?)?,?\s+\d{4}[a-z]?(?:;\s*[A-Z][a-zA-Z\-]+.*?)?)\)'
)
_CITATION_SUPERSCRIPT  = re.compile(r'(?<=[a-z\.\,\)])(\d+(?:,\d+)*)')

# Patterns that identify a heading as a page-marker / LaTeX artefact
_PAGE_MARKER_PATTERNS = [
    re.compile(r'^\s*page\s*\d+\s*$', re.IGNORECASE),
    re.compile(r'^\\subsubsection\{page\s*\d+\}$', re.IGNORECASE),
    re.compile(r'^\[page\s*\d+\]$', re.IGNORECASE),
    re.compile(r'^subsubsection\{page\s*\d+\}$', re.IGNORECASE),
]


def _is_page_marker_heading(heading: str) -> bool:
    h = (heading or "").strip()
    return any(p.match(h) for p in _PAGE_MARKER_PATTERNS)


def _merge_page_marker_sections(raw_sections: list) -> list:
    """
    Walk raw_sections; when a "Page N" pseudo-section is encountered:
    - Its content is appended to the last real section's content.
    - The pseudo-section itself is discarded.

    This preserves all body text that a PDF extractor emitted under page-marker
    headings while keeping the section list clean for downstream matching.
    """
    merged: list = []
    for s in raw_sections:
        heading = (s.get("heading") or "").strip()
        if _is_page_marker_heading(heading):
            content = (s.get("content") or "").strip()
            if content and merged:
                # Append to previous real section
                prev_content = (merged[-1].get("content") or "").strip()
                merged[-1]["content"] = (prev_content + "\n\n" + content).strip()
                # Update word count
                merged[-1]["word_count"] = len(merged[-1]["content"].split())
            # Drop the page-marker section itself
        else:
            merged.append(dict(s))
    return merged


class StructureAgent:
    def __init__(self, llm_generate_fn):
        self.llm = llm_generate_fn

    async def analyze(self, parsed: dict, use_cloud: bool, model_fast: str) -> dict:
        raw_text = (parsed.get("text") or "")
        text_for_llm = raw_text[:6000]

        prompt = PROMPT_STRUCTURE.format(text=text_for_llm)
        
        # Try to call LLM; on failure, gracefully use raw_sections fallback
        out = {}
        try:
            if use_cloud:
                raw = await self.llm("cloud", model_fast, prompt, SYSTEM_STRUCTURE)
            else:
                raw = await self.llm("ollama", model_fast, prompt, SYSTEM_STRUCTURE)
            out = self._parse_json(raw)
        except Exception as e:
            # LLM failed (rate limit, timeout, etc.) — log it and continue with fallback
            print(f"[StructureAgent] LLM failed, using raw_sections fallback: {e}")

        out = self._validate_and_fill(out)

        # Always inject raw sections from parser to prevent LLM truncation
        raw_sections = parsed.get("raw_sections", [])
        if raw_sections:
            # ── KEY FIX: merge page-marker content into real sections ──────
            clean_sections = _merge_page_marker_sections(raw_sections)
            out["sections"] = [self._normalize_section(s) for s in clean_sections]
        elif not out.get("sections"):
            # Fallback: detect sections from raw text using regex
            out["sections"] = self._detect_sections_regex(raw_text)

        # Detect citation format from raw text if LLM missed it
        if out.get("citation_format", "unknown") == "unknown":
            out["citation_format"] = self._detect_citation_format(raw_text)

        # Fill citations from raw text if LLM missed them
        if not out.get("citations"):
            out["citations"] = self._extract_citations(raw_text, out["citation_format"])

        # Compute total word count
        out["word_count_total"] = len(raw_text.split()) if raw_text else 0

        # Clean author names
        out["authors"] = [self._clean_author(a) for a in out.get("authors", []) if a.strip()]

        return out

    # ------------------------------------------------------------------ #
    # Parsing & validation
    # ------------------------------------------------------------------ #

    def _parse_json(self, raw: str) -> dict:
        text = raw.strip()

        # Strip markdown fences
        for fence in ("```json", "```"):
            if fence in text:
                start = text.find(fence) + len(fence)
                end   = text.find("```", start)
                text  = text[start:end].strip() if end > start else text[start:].strip()
                break

        # Extract first complete {...} block
        brace_start = text.find("{")
        brace_end   = text.rfind("}")
        if brace_start != -1 and brace_end > brace_start:
            text = text[brace_start:brace_end + 1]

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}

    def _validate_and_fill(self, out: dict) -> dict:
        """Ensure all required keys exist with correct types."""
        defaults = {
            "title":            "",
            "authors":          [],
            "affiliation":      "",
            "course_info":      {"course": "", "instructor": "", "date": ""},
            "abstract":         "",
            "keywords":         [],
            "problem_statement": "",
            "important_text":   [],
            "sections":         [],
            "tables":           [],
            "figures":          [],
            "citations":        [],
            "citation_format":  "unknown",
            "references":       [],
            "word_count_total": 0,
        }
        for key, default in defaults.items():
            if key not in out or out[key] is None:
                out[key] = default
            if isinstance(default, list) and not isinstance(out[key], list):
                out[key] = [out[key]] if out[key] else []
            if isinstance(default, str) and not isinstance(out[key], str):
                out[key] = str(out[key]) if out[key] else ""
            if isinstance(default, int) and not isinstance(out[key], int):
                try:
                    out[key] = int(out[key])
                except (TypeError, ValueError):
                    out[key] = 0

        valid_formats = {"author-year", "numeric", "numeric-superscript", "unknown"}
        if out["citation_format"] not in valid_formats:
            out["citation_format"] = "unknown"

        return out

    def _normalize_section(self, s: dict) -> dict:
        """Normalise a raw_section dict to the standard schema.
        Also try to detect section headings from content if heading is empty."""
        content = s.get("content", "")
        heading = str(s.get("heading", "")).strip()
        
        # If heading is empty but content exists, try to extract from first line
        if not heading and content:
            first_line = content.split('\n')[0].strip()
            # Check if first line looks like a section heading
            # (e.g., "I. INTRODUCTION", "1. METHODS", "BACKGROUND AND RELATED WORK")
            if len(first_line) < 150 and (
                first_line.isupper() or 
                re.match(r'^[IVX\d]+[\.\:]\s+', first_line, re.IGNORECASE) or
                re.match(r'^(?:section|chapter|part)\s+', first_line, re.IGNORECASE)
            ):
                heading = first_line
                # Remove the heading from content
                content = '\n'.join(content.split('\n')[1:]).strip()
        
        return {
            "heading":    heading or "Untitled Section",
            "level":      int(s.get("level", 1)),
            "content":    str(content).strip(),
            "word_count": len(content.split()) if content else 0,
        }

    # ------------------------------------------------------------------ #
    # Regex-based fallback section detection
    # ------------------------------------------------------------------ #

    def _detect_sections_regex(self, text: str) -> list:
        """Detect sections from raw text using multiple strategies."""
        if not text:
            return []
        
        sections = []
        
        # Strategy 1: Standard pattern matching (Roman/Arabic numerals)
        matches = list(_SECTION_PATTERN.finditer(text))
        if matches:
            for i, match in enumerate(matches):
                heading = match.group(0).strip()
                start = match.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                content = text[start:end].strip()
                if content:
                    sections.append({
                        "heading": heading,
                        "level": self._guess_heading_level(heading),
                        "content": content,
                        "word_count": len(content.split()),
                    })
        
        # Strategy 2: If no sections found by pattern, try smart splitting
        if not sections:
            sections = self._detect_sections_by_heuristics(text)
        
        return sections

    def _detect_sections_by_heuristics(self, text: str) -> list:
        """
        Detect sections from unstructured text using heuristics:
        - All-caps lines that look like headings
        - Lines starting with numbers/roman numerals
        - Academic section keywords (Introduction, Methods, etc.)
        """
        lines = text.split('\n')
        sections = []
        current_heading = ""
        current_content = []
        
        academic_keywords = {
            'abstract', 'introduction', 'background', 'related', 'methodology', 'method',
            'results', 'discussion', 'conclusion', 'future', 'references', 'acknowledgment',
            'application', 'ethical', 'evaluation', 'implementation', 'framework',
        }
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            # Check if this line looks like a section heading
            is_potential_heading = False
            
            # All caps and contains academic keyword
            if stripped.isupper() and any(kw in stripped.lower() for kw in academic_keywords):
                is_potential_heading = True
            
            # Starts with roman/arabic numeral pattern
            if re.match(r'^[IVX\d]+[\.\:]\s+', stripped, re.IGNORECASE):
                is_potential_heading = True
            
            # Short title-case line with academic keyword
            if (stripped.istitle() and len(stripped) < 100 and 
                any(kw in stripped.lower() for kw in academic_keywords)):
                is_potential_heading = True
            
            if is_potential_heading and current_heading:
                # Save previous section
                content = '\n'.join(current_content).strip()
                if content:
                    sections.append({
                        "heading": current_heading,
                        "level": 1,
                        "content": content,
                        "word_count": len(content.split()),
                    })
                current_heading = stripped
                current_content = []
            elif is_potential_heading and not current_heading:
                # First heading
                current_heading = stripped
                current_content = []
            elif current_heading:
                # Add to current section
                current_content.append(stripped)
        
        # Save last section
        if current_heading and current_content:
            content = '\n'.join(current_content).strip()
            if content:
                sections.append({
                    "heading": current_heading,
                    "level": 1,
                    "content": content,
                    "word_count": len(content.split()),
                })
        
        return sections

    def _guess_heading_level(self, heading: str) -> int:
        h = heading.lower()
        if any(h.startswith(major) for major in (
            "abstract", "introduction", "method", "result",
            "discussion", "conclusion", "references", "bibliography", "works cited",
        )):
            return 1
        if re.match(r'^[0-9]+\.[0-9]+', h):
            return 2
        return 1

    # ------------------------------------------------------------------ #
    # Citation helpers
    # ------------------------------------------------------------------ #

    def _detect_citation_format(self, text: str) -> str:
        numeric_hits     = len(_CITATION_NUMERIC.findall(text))
        author_year_hits = len(_CITATION_AUTHOR_YEAR.findall(text))

        if numeric_hits > author_year_hits and numeric_hits > 2:
            return "numeric"
        if author_year_hits > numeric_hits and author_year_hits > 2:
            return "author-year"
        if numeric_hits > 2:
            return "numeric"
        return "unknown"

    def _extract_citations(self, text: str, fmt: str) -> list:
        if fmt == "numeric":
            raw   = _CITATION_NUMERIC.findall(text)
            cites = set()
            for r in raw:
                for n in r.split(","):
                    cites.add(f"[{n.strip()}]")
            return sorted(cites, key=lambda x: int(re.search(r'\d+', x).group()))
        elif fmt == "author-year":
            raw = _CITATION_AUTHOR_YEAR.findall(text)
            return list(dict.fromkeys(f"({r})" for r in raw))
        return []

    # ------------------------------------------------------------------ #
    # Author cleaning
    # ------------------------------------------------------------------ #

    def _clean_author(self, name: str) -> str:
        """Remove emails, affiliation numbers, asterisks from author names."""
        name = re.sub(r'\S+@\S+\.\S+', '', name)
        name = re.sub(r'[\d,\*\†\‡]+$', '', name.strip())
        name = re.sub(r'^\d+\.\s*', '', name.strip())
        return name.strip()