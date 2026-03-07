"""
latex_generator.py
━━━━━━━━━━━━━━━━━━
Generic LaTeX generator for non-IEEE academic styles.
Produces compilable .tex files for APA, MLA, Chicago, Vancouver.

Uses standard \documentclass{article} with style-appropriate packages.

Usage:
  from utils.latex_generator import LatexGenerator
  gen = LatexGenerator(style="apa")
  tex = gen.generate(structure, output_path="outputs/job/formatted.tex")
"""
import re
from pathlib import Path
from typing import List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# LaTeX escaping (shared with ieee_latex_generator)
# ─────────────────────────────────────────────────────────────────────────────

_UNICODE_TO_LATEX = [
    ('β', r'$\beta$'), ('α', r'$\alpha$'), ('γ', r'$\gamma$'), ('δ', r'$\delta$'),
    ('Δ', r'$\Delta$'), ('θ', r'$\theta$'), ('Θ', r'$\Theta$'), ('λ', r'$\lambda$'),
    ('μ', r'$\mu$'), ('σ', r'$\sigma$'), ('Σ', r'$\Sigma$'), ('π', r'$\pi$'),
    ('Π', r'$\Pi$'), ('ω', r'$\omega$'), ('Ω', r'$\Omega$'),
    ('∼', r'$\sim$'), ('≈', r'$\approx$'), ('≠', r'$\neq$'), ('≥', r'$\geq$'),
    ('≤', r'$\leq$'), ('±', r'$\pm$'), ('×', r'$\times$'), ('÷', r'$\div$'),
    ('→', r'$\rightarrow$'), ('←', r'$\leftarrow$'), ('⇒', r'$\Rightarrow$'),
    ('∞', r'$\infty$'), ('∂', r'$\partial$'), ('∇', r'$\nabla$'),
    ('∑', r'$\sum$'), ('∏', r'$\prod$'), ('∫', r'$\int$'), ('√', r'$\sqrt{\ }$'),
    ('°', r'$^\circ$'), ('′', "'"), ('″', "''"), ('…', r'\ldots'),
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
    for char, replacement in _UNICODE_TO_LATEX:
        result = result.replace(char, replacement)
    result = result.replace('\\', r'\textbackslash{}')
    for char, replacement in _LATEX_ESCAPE_MAP[1:]:
        result = result.replace(char, replacement)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Style-specific configurations
# ─────────────────────────────────────────────────────────────────────────────

STYLE_CONFIG = {
    "apa": {
        "font_size":      "12pt",
        "line_spacing":   r"\doublespacing",
        "ref_title":      "References",
        "ref_cmd":        "\\section*{References}",
        "cite_pkg":       "apacite",
        "bibstyle":       "apacite",
        "indent":         r"\setlength{\parindent}{0.5in}",
        "margin":         "1in",
        "extra_pkgs":     ["setspace", "apacite", "fancyhdr"],
        "heading_style":  "apa",
    },
    "mla": {
        "font_size":      "12pt",
        "line_spacing":   r"\doublespacing",
        "ref_title":      "Works Cited",
        "ref_cmd":        "\\section*{Works Cited}",
        "cite_pkg":       "hanging",
        "bibstyle":       None,
        "indent":         r"\setlength{\parindent}{0.5in}",
        "margin":         "1in",
        "extra_pkgs":     ["setspace", "hanging", "fancyhdr"],
        "heading_style":  "mla",
    },
    "chicago": {
        "font_size":      "12pt",
        "line_spacing":   r"\doublespacing",
        "ref_title":      "Bibliography",
        "ref_cmd":        "\\section*{Bibliography}",
        "cite_pkg":       "biblatex-chicago",
        "bibstyle":       None,
        "indent":         r"\setlength{\parindent}{0.5in}",
        "margin":         "1in",
        "extra_pkgs":     ["setspace", "fancyhdr"],
        "heading_style":  "chicago",
    },
    "vancouver": {
        "font_size":      "11pt",
        "line_spacing":   r"\doublespacing",
        "ref_title":      "References",
        "ref_cmd":        "\\section*{References}",
        "cite_pkg":       None,
        "bibstyle":       None,
        "indent":         r"\setlength{\parindent}{0pt}" + "\n" + r"\setlength{\parskip}{6pt}",
        "margin":         "1in",
        "extra_pkgs":     ["setspace", "fancyhdr", "enumitem"],
        "heading_style":  "vancouver",
    },
}

DEFAULT_CONFIG = STYLE_CONFIG["apa"]


class LatexGenerator:
    """
    Generates a compilable LaTeX document for APA, MLA, Chicago, or Vancouver.
    """

    def __init__(self, style: str = "apa"):
        self.style  = style.lower().strip()
        self.config = STYLE_CONFIG.get(self.style, DEFAULT_CONFIG)

    def generate(
        self,
        structure: dict,
        output_path: Optional[str] = None,
    ) -> str:
        title      = structure.get("title", "Untitled")
        authors    = structure.get("authors", [])
        abstract   = structure.get("abstract", "")
        keywords   = structure.get("keywords", [])
        sections   = structure.get("sections", [])
        references = structure.get("references", [])

        parts: List[str] = []
        parts.append(self._preamble(title))
        parts.append(self._begin_document(title, authors))
        if abstract:
            parts.append(self._abstract_block(abstract, keywords))
        parts.append(self._body(sections))
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

    def _preamble(self, title: str) -> str:
        cfg       = self.config
        font_size = cfg["font_size"]
        extra     = "\n".join(f"\\usepackage{{{p}}}" for p in cfg.get("extra_pkgs", []))

        margin_pkg = f"\\usepackage[margin={cfg['margin']}]{{geometry}}"

        return f"""\\documentclass[{font_size}]{{article}}

% ── Encoding & font ───────────────────────────────────────────────────────────
\\usepackage[T1]{{fontenc}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{times}}

% ── Packages ──────────────────────────────────────────────────────────────────
{margin_pkg}
\\usepackage{{amsmath,amssymb}}
\\usepackage{{graphicx}}
\\usepackage{{hyperref}}
\\usepackage{{booktabs}}
\\usepackage{{url}}
{extra}

% ── Spacing & indent ──────────────────────────────────────────────────────────
{cfg['indent']}
{cfg['line_spacing']}

% ── Hyperref ──────────────────────────────────────────────────────────────────
\\hypersetup{{colorlinks=true,linkcolor=black,citecolor=black,urlcolor=blue}}
"""

    # ─────────────────────────────────────────────────────────────────────────
    # Title block
    # ─────────────────────────────────────────────────────────────────────────

    def _begin_document(self, title: str, authors: List[str]) -> str:
        lines = [r"\begin{document}", ""]

        if self.style == "mla":
            # MLA: no \maketitle — header block is manual
            lines.append(r"% MLA header block (fill in: instructor, course, date)")
            lines.append(r"\noindent Your Name \\")
            lines.append(r"Instructor Name \\")
            lines.append(r"Course Name \\")
            lines.append(r"\today \\[1em]")
            lines.append(f"\\begin{{center}}{_tex(title)}\\end{{center}}")
            lines.append("")
        else:
            lines.append(f"\\title{{{_tex(title)}}}")
            if authors:
                author_str = " \\and ".join(_tex(a) for a in authors)
                lines.append(f"\\author{{{author_str}}}")
            lines.append(r"\date{\today}")
            lines.append(r"\maketitle")
            lines.append("")

        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────────────
    # Abstract
    # ─────────────────────────────────────────────────────────────────────────

    def _abstract_block(self, abstract: str, keywords: List[str]) -> str:
        lines = [r"\begin{abstract}"]
        lines.append(_tex(abstract.strip()))
        lines.append(r"\end{abstract}")
        if keywords:
            kw_str = ", ".join(_tex(k) for k in keywords)
            lines.append(r"\noindent\textbf{Keywords:} " + kw_str + r"\\[1em]")
        lines.append("")
        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────────────
    # Body
    # ─────────────────────────────────────────────────────────────────────────

    def _body(self, sections: List[dict]) -> str:
        lines: List[str] = []
        skip_keys = {"abstract", "references", "bibliography", "workscited",
                     "acknowledgment", "acknowledgements"}
        section_num = 0

        for sec in sections:
            heading = str(sec.get("heading", "")).strip()
            content = str(sec.get("content", "")).strip()
            level   = int(sec.get("level", 1))
            norm    = re.sub(r'[^a-z0-9]', '', heading.lower())
            is_placeholder = sec.get("_placeholder", False)

            if norm in skip_keys:
                continue
            if not heading:
                continue

            # Heading command by level
            if level == 1:
                cmd = r"\section"
            elif level == 2:
                cmd = r"\subsection"
            else:
                cmd = r"\subsubsection"

            lines.append(f"{cmd}{{{_tex(heading)}}}")
            lines.append("")

            # Only output content if it's not a placeholder
            if content and not is_placeholder:
                paras = [p.strip() for p in re.split(r'\n{2,}', content) if p.strip()]
                for para in paras:
                    text = " ".join(l.strip() for l in para.splitlines() if l.strip())
                    lines.append(_tex(text))
                    lines.append("")
            elif is_placeholder:
                # Add a comment indicating this section needs content
                lines.append(r"% TODO: Add content for this section.")
                lines.append("")

        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────────────
    # References
    # ─────────────────────────────────────────────────────────────────────────

    def _references(self, references: List[str]) -> str:
        if not references:
            return ""

        cfg   = self.config
        lines = [cfg["ref_cmd"], ""]

        if self.style == "vancouver":
            # Vancouver: numbered list, no hanging indent
            lines.append(r"\begin{enumerate}[label=\arabic*.]")
            for ref in references:
                ref_text = re.sub(r'^[\[\d\]\.\s]+', '', ref.strip())
                lines.append(f"\\item {_tex(ref_text)}")
            lines.append(r"\end{enumerate}")
        else:
            # APA / MLA / Chicago: hanging indent
            lines.append(r"\begin{hangparas}{0.5in}{1}")
            for ref in references:
                ref_text = ref.strip()
                lines.append(_tex(ref_text) + r"\\[6pt]")
            lines.append(r"\end{hangparas}")

        lines.append("")
        return "\n".join(lines)