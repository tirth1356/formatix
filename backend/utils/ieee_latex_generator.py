"""
ieee_latex_generator.py
━━━━━━━━━━━━━━━━━━━━━━━
Generate a compilable IEEE-format LaTeX (.tex) file from a structured
manuscript dict (output of StructureAgent).

FIXED vs previous version:
- Same robust _match_ieee_section() logic as docx_formatter so "Literature
  Review", "I. INTRODUCTION", "Results and Discussion", etc. all map
  correctly to their canonical IEEE slots.
- Page-marker pseudo-sections ("Page 1", \subsubsection{Page 2}) are filtered
  before processing, and their content is merged into the preceding real section.
- Content is NEVER replaced by a placeholder comment unless the section is
  genuinely absent from the source document.
- When two source sections match the same canonical slot, their content is
  merged (appended) rather than the second being silently dropped.
- Extras (non-standard sections) are inserted after Related Work.
- _references() uses \begin{thebibliography} — no biblatex dependency.
"""
import re
from pathlib import Path
from typing import List, Optional

from utils.table_figure_handler import detect_and_convert_tables, detect_and_convert_figures


# ─────────────────────────────────────────────────────────────────────────────
# Standard IEEE section skeleton
# ─────────────────────────────────────────────────────────────────────────────

IEEE_STANDARD_SECTIONS: List[str] = [
    "Introduction",
    "Related Work",
    "Methodology",
    "Results",
    "Discussion",
    "Conclusion",
    "Acknowledgment",
]

# ─────────────────────────────────────────────────────────────────────────────
# IEEE section synonym map (normalised variant → canonical label)
# ─────────────────────────────────────────────────────────────────────────────

_IEEE_SYNONYMS: dict = {
    "introduction": "Introduction",
    "intro": "Introduction",
    "relatedwork": "Related Work",
    "literaturereview": "Related Work",
    "backgroundandrelatedwork": "Related Work",
    "background": "Related Work",
    "priorwork": "Related Work",
    "relatedworks": "Related Work",
    "previouswork": "Related Work",
    "methodology": "Methodology",
    "methods": "Methodology",
    "method": "Methodology",
    "proposedmethod": "Methodology",
    "approach": "Methodology",
    "system": "Methodology",
    "systemdesign": "Methodology",
    "experimentalsetup": "Methodology",
    "experimentsetup": "Methodology",
    "materialsandmethods": "Methodology",
    "experimentalmethodology": "Methodology",
    "results": "Results",
    "resultsanddiscussion": "Results",
    "resultsanddiscussions": "Results",
    "experimentalresults": "Results",
    "evaluation": "Results",
    "experiments": "Results",
    "performance": "Results",
    "discussion": "Discussion",
    "discussions": "Discussion",
    "analysisanddiscussion": "Discussion",
    "conclusion": "Conclusion",
    "conclusions": "Conclusion",
    "conclusionandfuturework": "Conclusion",
    "summaryandfuturework": "Conclusion",
    "summary": "Conclusion",
    "acknowledgment": "Acknowledgment",
    "acknowledgments": "Acknowledgment",
    "acknowledgement": "Acknowledgment",
    "acknowledgements": "Acknowledgment",
}

_SKIP_NORM_KEYS = {
    "abstract", "references", "bibliography", "workscited", "referencelist",
}

_PAGE_MARKER_PATTERNS = [
    re.compile(r'^\s*page\s*\d+\s*$', re.IGNORECASE),
    re.compile(r'^\\subsubsection\{page\s*\d+\}$', re.IGNORECASE),
    re.compile(r'^\[page\s*\d+\]$', re.IGNORECASE),
    re.compile(r'^subsubsection\{page\s*\d+\}$', re.IGNORECASE),
]


def _is_page_marker(heading: str) -> bool:
    h = (heading or "").strip()
    return any(p.match(h) for p in _PAGE_MARKER_PATTERNS)


def _norm(h: str) -> str:
    return re.sub(r'[^a-z0-9]', '', (h or '').lower())


def _norm_strip_prefix(h: str) -> str:
    s = (h or '').strip()
    s = re.sub(r'^(?:[IVXLCDM]+\.?|[0-9]+(?:\.[0-9]+)*\.?)\s*', '', s, flags=re.IGNORECASE)
    return _norm(s)


def _match_ieee_section(heading: str) -> Optional[str]:
    """
    Match a heading string to a canonical IEEE section label.
    Returns canonical label or None.
    """
    if not heading:
        return None

    n  = _norm(heading)
    np = _norm_strip_prefix(heading)

    # 1. Direct synonym lookup
    if n in _IEEE_SYNONYMS:
        return _IEEE_SYNONYMS[n]
    if np in _IEEE_SYNONYMS:
        return _IEEE_SYNONYMS[np]

    # 2. Partial match against canonical names
    for canonical in IEEE_STANDARD_SECTIONS:
        cn = _norm(canonical)
        if len(cn) >= 4 and (cn in n or cn in np):
            return canonical
        if len(n) >= 4 and n in cn:
            return canonical
        if len(np) >= 4 and np in cn:
            return canonical

    return None


def _merge_page_markers(sections: list) -> list:
    """Merge page-marker pseudo-sections into the preceding real section."""
    merged: list = []
    for s in sections:
        heading = (s.get("heading") or "").strip()
        if _is_page_marker(heading):
            content = (s.get("content") or "").strip()
            if content and merged:
                prev_content = (merged[-1].get("content") or "").strip()
                merged[-1] = dict(merged[-1])
                merged[-1]["content"] = (prev_content + "\n\n" + content).strip()
        else:
            merged.append(dict(s))
    return merged


# ─────────────────────────────────────────────────────────────────────────────
# Unicode → LaTeX
# ─────────────────────────────────────────────────────────────────────────────

_UNICODE_TO_LATEX = [
    ('β', r'$\beta$'),   ('α', r'$\alpha$'),  ('γ', r'$\gamma$'),  ('δ', r'$\delta$'),
    ('Δ', r'$\Delta$'),  ('θ', r'$\theta$'),  ('Θ', r'$\Theta$'),  ('λ', r'$\lambda$'),
    ('μ', r'$\mu$'),     ('σ', r'$\sigma$'),  ('Σ', r'$\Sigma$'),  ('π', r'$\pi$'),
    ('Π', r'$\Pi$'),     ('ω', r'$\omega$'),  ('Ω', r'$\Omega$'),
    ('∼', r'$\sim$'),    ('≈', r'$\approx$'), ('≠', r'$\neq$'),    ('≥', r'$\geq$'),
    ('≤', r'$\leq$'),    ('±', r'$\pm$'),     ('×', r'$\times$'),  ('÷', r'$\div$'),
    ('→', r'$\rightarrow$'), ('←', r'$\leftarrow$'), ('⇒', r'$\Rightarrow$'),
    ('∞', r'$\infty$'),  ('∂', r'$\partial$'), ('∇', r'$\nabla$'),
    ('∑', r'$\sum$'),    ('∏', r'$\prod$'),   ('∫', r'$\int$'),    ('√', r'$\sqrt{\ }$'),
    ('°', r'$^\circ$'),  ('′', "'"),           ('″', "''"),          ('…', r'\ldots'),
]

_LATEX_ESCAPE_MAP = [
    ('\\',  r'\textbackslash{}'),
    ('&',   r'\&'),
    ('%',   r'\%'),
    ('$',   r'\$'),
    ('#',   r'\#'),
    ('_',   r'\_'),
    ('{',   r'\{'),
    ('}',   r'\}'),
    ('~',   r'\textasciitilde{}'),
    ('^',   r'\textasciicircum{}'),
    ('\u2014', '---'),
    ('\u2013', '--'),
    ('\u2019', "'"),
    ('\u2018', '`'),
    ('\u201c', "``"),
    ('\u201d', "''"),
]


def _tex(text: str) -> str:
    if not text:
        return ""
    result = str(text)
    result = result.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
    result = result.replace('\ufeff', '')
    for char, replacement in _UNICODE_TO_LATEX:
        result = result.replace(char, replacement)
    result = result.replace('\\', r'\textbackslash{}')
    for char, replacement in _LATEX_ESCAPE_MAP[1:]:
        result = result.replace(char, replacement)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Generator
# ─────────────────────────────────────────────────────────────────────────────

class IEEELatexGenerator:
    """Generates a properly structured IEEE LaTeX document."""

    def __init__(self, llm_generate_fn=None):
        self.llm = llm_generate_fn

    def generate(
        self,
        structure: dict,
        output_path: Optional[str] = None,
        affiliation: Optional[str] = None,
        email: Optional[str] = None,
    ) -> str:
        title      = structure.get("title", "Untitled")
        authors    = structure.get("authors", [])
        abstract   = structure.get("abstract", "")
        keywords   = structure.get("keywords", [])
        sections   = structure.get("sections", [])
        references = structure.get("references", [])

        # ── Pre-process: remove page markers, merge their content ──────────
        sections = _merge_page_markers(sections)

        # ── Convert [Table] / [Figure] sections to LaTeX environments ─────
        sections, _tc = detect_and_convert_tables(sections)
        sections, _fc = detect_and_convert_figures(sections)

        parts: List[str] = []
        parts.append(self._preamble())
        parts.append(self._begin_document(title, authors, affiliation, email))
        parts.append(self._abstract_block(abstract, keywords))
        parts.append(self._body(sections))
        parts.append(self._acknowledgment(sections))
        parts.append(self._references(references))
        parts.append(r"\end{document}" + "\n")

        source = "\n".join(p for p in parts if p)

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_text(source, encoding="utf-8")

        return source

    # ─────────────────────────────────────────────────────────────────────────
    # Preamble
    # ─────────────────────────────────────────────────────────────────────────

    def _preamble(self) -> str:
        return r"""\documentclass[10pt,conference]{IEEEtran}

% ── Core packages ────────────────────────────────────────────────────────────
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{times}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{cite}
\usepackage{url}
\usepackage{hyperref}
\usepackage{booktabs}
\usepackage{array}
\usepackage{balance}

% ── Hyperref setup ───────────────────────────────────────────────────────────
\hypersetup{
  colorlinks = true,
  linkcolor  = black,
  citecolor  = black,
  urlcolor   = blue,
}

\IEEEoverridecommandlockouts
"""

    # ─────────────────────────────────────────────────────────────────────────
    # Title + author block
    # ─────────────────────────────────────────────────────────────────────────

    def _begin_document(
        self,
        title: str,
        authors: List[str],
        affiliation: Optional[str],
        email: Optional[str],
    ) -> str:
        lines: List[str] = [r"\begin{document}", ""]
        lines.append(f"\\title{{{_tex(title)}}}")
        lines.append("")

        if authors:
            author_blocks: List[str] = []
            for author in authors:
                aff_line = _tex(affiliation) if affiliation else "Institution Name"
                block = (
                    f"\\IEEEauthorblockN{{{_tex(author)}}}\n"
                    f"\\IEEEauthorblockA{{\\textit{{{aff_line}}}}}"
                )
                if email:
                    block = (
                        f"\\IEEEauthorblockN{{{_tex(author)}}}\n"
                        f"\\IEEEauthorblockA{{\\textit{{{aff_line}}}\\\\{_tex(email)}}}"
                    )
                author_blocks.append(block)

            author_str = " \\and\n".join(author_blocks)
            lines.append(f"\\author{{\n{author_str}\n}}")
        else:
            lines.append(r"\author{\IEEEauthorblockN{Author Name}\IEEEauthorblockA{\textit{Institution}}}")

        lines.append("")
        lines.append(r"\maketitle")
        lines.append("")
        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────────────
    # Abstract + Index Terms
    # ─────────────────────────────────────────────────────────────────────────

    def _abstract_block(self, abstract: str, keywords: List[str]) -> str:
        lines: List[str] = []
        if abstract:
            lines.append(r"\begin{abstract}")
            lines.append(_tex(abstract.strip()))
            lines.append(r"\end{abstract}")
            lines.append("")
        if keywords:
            kw_str = ", ".join(_tex(k.lower()) for k in keywords)
            lines.append(r"\begin{IEEEkeywords}")
            lines.append(kw_str)
            lines.append(r"\end{IEEEkeywords}")
            lines.append("")
        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────────────
    # Body sections
    # ─────────────────────────────────────────────────────────────────────────

    def _build_canonical_map(self, sections: List[dict]):
        """
        Build:
          canonical_map  — canonical_label → merged section dict
          extra_sections — sections not matched to any canonical slot
        """
        canonical_map: dict  = {}
        extra_sections: list = []

        for s in sections:
            heading = (s.get("heading") or "").strip()
            content = (s.get("content") or "").strip()

            nk = _norm_strip_prefix(heading)
            if nk in _SKIP_NORM_KEYS or _norm(heading) in _SKIP_NORM_KEYS:
                continue
            # Skip acknowledgment (handled separately)
            if nk in ("acknowledgment", "acknowledgments", "acknowledgement", "acknowledgements"):
                continue

            canonical = _match_ieee_section(heading)
            if canonical:
                existing = canonical_map.get(canonical)
                if existing is None:
                    canonical_map[canonical] = dict(s)
                else:
                    # Merge content
                    existing_content = (existing.get("content") or "").strip()
                    if existing_content and content:
                        merged = dict(existing)
                        merged["content"] = existing_content + "\n\n" + content
                        canonical_map[canonical] = merged
                    elif content and not existing_content:
                        canonical_map[canonical] = dict(s)
                    # else: existing has content, new one is empty — keep existing
            else:
                extra_sections.append(s)

        return canonical_map, extra_sections

    def _body(self, sections: List[dict]) -> str:
        """
        Render body sections preserving original document structure.
        If document already has well-structured sections with content,
        use them as-is rather than forcing into IEEE canonical order.
        """
        # Check if sections have real content (not just headings)
        sections_with_content = [s for s in sections if (s.get("content") or "").strip()]
        
        # If the document has many non-empty sections, preserve original structure
        # Otherwise, use canonical IEEE mapping
        if len(sections_with_content) >= 4:
            # Document is well-structured — preserve its original order
            return self._render_sections_as_is(sections)
        else:
            # Document is sparse — use canonical IEEE template
            return self._render_canonical_ieee_structure(sections)

    def _render_sections_as_is(self, sections: List[dict]) -> str:
        """Render sections in their original order, preserving all content and structure."""
        lines: List[str] = []
        
        for sec in sections:
            heading = (sec.get("heading") or "Untitled").strip()
            content = (sec.get("content") or "").strip()
            level = int(sec.get("level", 1))
            
            # Skip empty sections and special markers
            if not content or _is_page_marker(heading):
                continue
                
            # Skip references/bibliography (handled separately)
            if _norm(heading) in {"references", "bibliography", "workscited", "referencelist"}:
                continue
            
            # Choose LaTeX section command based on level
            if level == 1:
                cmd = r"\section"
            elif level == 2:
                cmd = r"\subsection"
            else:
                cmd = r"\subsubsection"
            
            lines.append(f"{cmd}{{{_tex(heading)}}}")
            lines.append(r"\label{sec:" + _norm(heading) + "}")
            lines.append("")
            
            if content:
                if content.startswith(r"\begin{"):
                    lines.append(content)
                else:
                    is_intro = _norm(heading) == "introduction"
                    lines.extend(self._render_content(content, is_first_section=is_intro))
            
            lines.append("")
        
        return "\n".join(lines)

    def _render_canonical_ieee_structure(self, sections: List[dict]) -> str:
        """Render sections using rigid IEEE canonical structure (original logic)."""
        canonical_map, extra_sections = self._build_canonical_map(sections)

        # Standard section order (skip Abstract and Acknowledgment)
        skip_in_body = {"abstract", "acknowledgment", "acknowledgments",
                        "acknowledgement", "acknowledgements",
                        "references", "bibliography", "workscited"}

        standard_body = [h for h in IEEE_STANDARD_SECTIONS
                         if _norm(h) not in skip_in_body]

        lines: List[str] = []
        extras_inserted  = False

        for label in standard_body:
            sec     = canonical_map.get(label)
            content = (sec.get("content") or "").strip() if sec else ""
            is_placeholder = not content

            lines.append(f"\\section{{{_tex(label)}}}")
            lines.append(r"\label{sec:" + _norm(label) + "}")
            lines.append("")

            if content:
                # Check if content is pre-rendered LaTeX (tables/figures)
                if content.startswith(r"\begin{"):
                    lines.append(content)
                else:
                    lines.extend(self._render_content(content, is_first_section=(label == "Introduction")))
            else:
                # Only emit a placeholder comment when truly no content
                lines.append(f"% TODO: Add {label} content here.")
                lines.append("")

            # Insert extra sections after Related Work
            if label == "Related Work" and not extras_inserted:
                for extra in extra_sections:
                    extra_content = (extra.get("content") or "").strip()
                    if extra_content:
                        lines.extend(self._render_section(extra))
                extras_inserted = True

        if not extras_inserted:
            for extra in extra_sections:
                extra_content = (extra.get("content") or "").strip()
                if extra_content:
                    lines.extend(self._render_section(extra))

        return "\n".join(lines)

    def _render_section(self, sec: dict) -> List[str]:
        heading = (sec.get("heading") or "Untitled").strip()
        content = (sec.get("content") or "").strip()
        level   = int(sec.get("level", 1))
        cmd     = r"\section" if level == 1 else (r"\subsection" if level == 2 else r"\subsubsection")
        lines   = [f"{cmd}{{{_tex(heading)}}}", ""]
        if content:
            if content.startswith(r"\begin{"):
                lines.append(content)
            else:
                lines.extend(self._render_content(content))
        return lines

    def _render_content(self, content: str, is_first_section: bool = False) -> List[str]:
        paras  = [p.strip() for p in re.split(r'\n{2,}', content) if p.strip()]
        lines: List[str] = []
        for i, para in enumerate(paras):
            text = " ".join(l.strip() for l in para.splitlines() if l.strip())
            text = _tex(text)
            if i == 0 and is_first_section and len(text) > 2:
                first_char = text[0]
                rest       = text[1:]
                space_idx  = rest.find(' ')
                if space_idx > 0:
                    first_word = rest[:space_idx]
                    remainder  = rest[space_idx:]
                    text = f"\\IEEEPARstart{{{first_char}}}{{{first_word}}}{remainder}"
                else:
                    text = f"\\IEEEPARstart{{{first_char}}}{{{rest}}}"
            lines.append(text)
            lines.append("")
        return lines

    # ─────────────────────────────────────────────────────────────────────────
    # Acknowledgment
    # ─────────────────────────────────────────────────────────────────────────

    def _acknowledgment(self, sections: List[dict]) -> str:
        ack_keys = {"acknowledgment", "acknowledgments", "acknowledgement", "acknowledgements"}
        ack_sec  = next(
            (s for s in sections if _norm(s.get("heading", "")) in ack_keys),
            None,
        )
        content = (ack_sec.get("content") or "").strip() if ack_sec else ""

        lines = [r"\section*{Acknowledgment}", ""]
        if content:
            lines.extend(self._render_content(content))
        else:
            lines.append(r"% Acknowledge funding sources, institutional support, and contributors.")
            lines.append(r"% IEEE style: do not use Dr., Prof., or Mr. here.")
            lines.append("")
        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────────────
    # References
    # ─────────────────────────────────────────────────────────────────────────

    def _references(self, references: List[str]) -> str:
        if not references:
            return ""

        width_hint = len(str(len(references)))
        width_str  = "9" * width_hint

        lines = [
            r"\balance",
            "",
            f"\\begin{{thebibliography}}{{{width_str}}}",
            "",
        ]

        for i, ref in enumerate(references, start=1):
            ref_text = ref.strip()
            ref_text = re.sub(r'^\[\d+\]\s*', '', ref_text)
            ref_text = re.sub(r'^\d+\.\s*', '', ref_text)
            lines.append(f"\\bibitem{{ref{i}}}")
            lines.append(_tex(ref_text))
            lines.append("")

        lines.append(r"\end{thebibliography}")
        lines.append("")
        return "\n".join(lines)