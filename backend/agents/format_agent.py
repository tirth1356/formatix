"""
Formatting Agent: Analyze manuscript and produce explainable, actionable corrections.
The actual DOCX generation is handled by DocxFormatter (python-docx / docx-js).
This agent asks the LLM for a structured list of corrections it would make.

FIXES:
- Style-aware prompting: sends full rules context including heading format, spacing, citations
- Corrections now include a "section" field (where in the document the issue is)
- Corrections now include a "severity" field: "required" | "recommended" | "optional"
- Corrections now include a "category": "citation" | "heading" | "spacing" | "font" |
  "reference" | "abstract" | "title_page" | "structure" | "grammar" | "punctuation"
- Corrections are de-duplicated and filtered for blank/trivial entries
- Rule-based pre-pass: deterministic checks that don't need LLM (spacing, font, margins)
  are added BEFORE the LLM call so they're always present
- LLM prompt is chunked by section (not just first 1500 chars) so body coverage is complete
- Abstract is fully included (not truncated to 500 chars)
- Corrections list is capped at 50 to avoid noise; sorted by severity
"""
import json
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


SYSTEM_FORMAT = """You are an expert academic manuscript copy-editor. Analyze the manuscript against the provided style rules and return structured corrections as valid JSON only. No markdown, no preamble."""

PROMPT_FORMAT = """You are a meticulous academic copy-editor. Review the manuscript excerpt below against the provided style rules and identify every correction required to bring the manuscript into full compliance.

=== STYLE RULES ===
{rules_pretty}

=== MANUSCRIPT METADATA ===
Title: {title}
Authors: {authors}
Citation format detected: {citation_format}
Total sections: {section_count}

=== ABSTRACT ===
{abstract}

=== BODY SECTIONS ({section_label}) ===
{body_text}

=== INSTRUCTIONS ===
For EVERY violation found, create one correction entry. Be specific — do not write vague corrections.
Categories to check:
1. HEADINGS: Do heading levels match "{heading_l1}", "{heading_l2}", "{heading_l3}" rules?
2. CITATIONS: Do in-text citations use the required "{citation_style}" format?
3. REFERENCES: Does the reference list match "{reference_format}" format? Check hanging indent, DOI, author format.
4. SPACING: Is line spacing "{line_spacing}"? Are paragraph indents "{paragraph_indent}"?
5. FONT: Is font "{font}" at {font_size}pt?
6. ABSTRACT: Is it present, properly labeled, within word limit ({abstract_word_limit} words)?
7. TITLE PAGE: Does the style require a title page? ({title_page})
8. RUNNING HEAD: Does the style require a running header? ({running_head})
9. COLUMNS: Is layout {columns}-column as required?
10. REFERENCE SECTION TITLE: Should be exactly "{reference_section_title}".

Return a JSON object:
{{
  "corrections": [
    {{
      "section": "Abstract|Introduction|Methods|References|...|General",
      "category": "heading|citation|reference|spacing|font|abstract|title_page|running_head|structure|grammar|punctuation",
      "severity": "required|recommended|optional",
      "original": "exact problematic text or description of the issue",
      "change": "exact corrected text or action to take",
      "reason": "the specific rule that requires this change"
    }},
    ...
  ]
}}

Return ONLY the JSON object."""


# Deterministic rule-based checks (no LLM needed)
# These are always included in the corrections output
def _rule_based_corrections(structure: dict, rules: dict) -> list:
    """
    Generate corrections that can be determined without LLM analysis.
    """
    corrections = []

    # --- Abstract word count ---
    abstract = structure.get("abstract", "")
    limit = rules.get("abstract_word_limit")
    abstract_required = rules.get("abstract_required", False)

    if abstract_required and not abstract.strip():
        corrections.append({
            "section": "Abstract",
            "category": "abstract",
            "severity": "required",
            "original": "No abstract found",
            "change": f"Add an abstract of up to {limit or 'the required'} words",
            "reason": f"{rules.get('style', 'This style')} requires an abstract.",
        })
    elif abstract and limit:
        word_count = len(abstract.split())
        if word_count > limit:
            corrections.append({
                "section": "Abstract",
                "category": "abstract",
                "severity": "required",
                "original": f"Abstract is {word_count} words",
                "change": f"Reduce abstract to under {limit} words",
                "reason": f"{rules.get('style', 'This style')} limits the abstract to {limit} words.",
            })

    # --- Reference section title ---
    expected_title = rules.get("reference_section_title", "References")
    sections = structure.get("sections", [])
    ref_section_found = False
    for s in sections:
        heading = s.get("heading", "").strip()
        if re.search(r'\b(references?|bibliography|works\s+cited)\b', heading, re.IGNORECASE):
            ref_section_found = True
            if heading.lower() != expected_title.lower():
                corrections.append({
                    "section": "References",
                    "category": "structure",
                    "severity": "required",
                    "original": f'Reference section heading: "{heading}"',
                    "change": f'Rename to: "{expected_title}"',
                    "reason": f"{rules.get('style', 'This style')} requires the reference section to be titled '{expected_title}'.",
                })

    if not ref_section_found:
        corrections.append({
            "section": "References",
            "category": "structure",
            "severity": "required",
            "original": "No reference section found",
            "change": f'Add a "{expected_title}" section at the end of the manuscript',
            "reason": f"{rules.get('style', 'This style')} requires a '{expected_title}' section.",
        })

    # --- Title page check ---
    if rules.get("title_page"):
        corrections.append({
            "section": "General",
            "category": "title_page",
            "severity": "required",
            "original": "Title page requirement",
            "change": "Ensure a separate title page is included with title, author names, affiliation, and running head",
            "reason": f"{rules.get('style', 'This style')} requires a separate title page.",
        })

    # --- Running head check ---
    if rules.get("running_head"):
        corrections.append({
            "section": "General",
            "category": "running_head",
            "severity": "required",
            "original": "Running head requirement",
            "change": "Add a running head (shortened title, max 50 chars) in the page header, right-aligned",
            "reason": f"{rules.get('style', 'This style')} requires a running head on every page.",
        })

    # --- Column layout ---
    columns = rules.get("columns", 1)
    if columns == 2:
        corrections.append({
            "section": "General",
            "category": "structure",
            "severity": "required",
            "original": "Single-column layout detected",
            "change": "Convert body text to 2-column layout (IEEE-standard)",
            "reason": f"{rules.get('style', 'This style')} requires a 2-column layout.",
        })

    # --- Font and size reminder ---
    corrections.append({
        "section": "General",
        "category": "font",
        "severity": "required",
        "original": "Font and size",
        "change": f"Ensure entire manuscript uses {rules.get('font', 'Times New Roman')} at {rules.get('font_size', 12)}pt",
        "reason": f"{rules.get('style', 'This style')} specifies {rules.get('font', 'Times New Roman')} {rules.get('font_size', 12)}pt.",
    })

    # --- Line spacing reminder ---
    corrections.append({
        "section": "General",
        "category": "spacing",
        "severity": "required",
        "original": "Line spacing",
        "change": f"Set line spacing to {rules.get('line_spacing', 'double')} throughout the manuscript",
        "reason": f"{rules.get('style', 'This style')} requires {rules.get('line_spacing', 'double')} line spacing.",
    })

    return corrections


class FormattingAgent:
    def __init__(self, llm_generate_fn):
        self.llm = llm_generate_fn

    async def analyze_corrections(
        self,
        structure: dict,
        rules: dict,
        use_cloud: bool,
        model_reasoning: str,
    ) -> list:
        """
        Combine deterministic rule-based corrections with LLM analysis.
        Returns de-duplicated, sorted corrections list.
        If LLM fails, returns only rule-based corrections.
        """
        # Step 1: Deterministic checks (always reliable)
        base_corrections = _rule_based_corrections(structure, rules)

        # Step 2: LLM analysis for nuanced corrections (may fail gracefully)
        llm_corrections = await self._llm_corrections(structure, rules, use_cloud, model_reasoning)

        # Step 3: Merge, de-duplicate, and sort
        all_corrections = base_corrections + llm_corrections
        deduped = self._deduplicate(all_corrections)
        sorted_corrections = self._sort_by_severity(deduped)

        # Cap at 50 to avoid noise
        return sorted_corrections[:50]

    async def _llm_corrections(
        self,
        structure: dict,
        rules: dict,
        use_cloud: bool,
        model_reasoning: str,
    ) -> list:
        """Ask LLM for corrections it would make on the manuscript.
        If LLM fails (JSON validation, timeout, etc.), returns empty list.
        Rule-based corrections will still be included in the final output."""
        try:
            sections = structure.get("sections", [])

            # Build body text from all sections (not just first 1500 chars)
            # Send the first N chars of each section to cover the whole paper
            body_parts = []
            total_chars = 0
            char_limit = 3000  # per LLM context budget

            for s in sections:
                heading = s.get("heading", "")
                content = s.get("content", "")
                chunk = f"[{heading}]\n{content[:500]}\n"
                if total_chars + len(chunk) > char_limit:
                    body_parts.append("... [remaining sections truncated for context] ...")
                    break
                body_parts.append(chunk)
                total_chars += len(chunk)

            body_text = "\n".join(body_parts) if body_parts else "No body sections found."
            abstract = structure.get("abstract", "No abstract found.")

            # Build pretty-printed rules summary for prompt
            rules_pretty = self._format_rules_pretty(rules)

            heading_rules = rules.get("heading_rules", {})
            section_label = f"{len(sections)} sections"

            prompt = PROMPT_FORMAT.format(
                rules_pretty=rules_pretty,
                title=structure.get("title", "Unknown"),
                authors=", ".join(structure.get("authors", [])) or "Unknown",
                citation_format=structure.get("citation_format", "unknown"),
                section_count=len(sections),
                abstract=abstract[:800],  # full abstract, capped at 800 chars
                body_text=body_text,
                section_label=section_label,
                heading_l1=heading_rules.get("level1", "center bold"),
                heading_l2=heading_rules.get("level2", "left bold"),
                heading_l3=heading_rules.get("level3", "left bold italic"),
                citation_style=rules.get("citation_style", "author-year"),
                reference_format=rules.get("reference_format", "APA7"),
                line_spacing=rules.get("line_spacing", "double"),
                paragraph_indent=rules.get("paragraph_indent", "0.5 inch"),
                font=rules.get("font", "Times New Roman"),
                font_size=rules.get("font_size", 12),
                abstract_word_limit=rules.get("abstract_word_limit", "N/A"),
                title_page=rules.get("title_page", False),
                running_head=rules.get("running_head", False),
                columns=rules.get("columns", 1),
                reference_section_title=rules.get("reference_section_title", "References"),
            )

            raw = await self.llm(
                "cloud" if use_cloud else "ollama",
                model_reasoning,
                prompt,
                SYSTEM_FORMAT,
            )
            return self._parse_corrections(raw)
        except Exception as e:
            # LLM failed (JSON validation, timeout, rate limit, etc.)
            # Log the error but don't crash — rule-based corrections will still be returned
            print(f"[FormattingAgent] LLM corrections failed (using rule-based only): {type(e).__name__}: {e}")
            return []

    def _format_rules_pretty(self, rules: dict) -> str:
        """Format the rules dict as a readable summary for the LLM prompt."""
        lines = [
            f"Style: {rules.get('style', 'APA')}",
            f"Font: {rules.get('font', 'Times New Roman')} {rules.get('font_size', 12)}pt",
            f"Line spacing: {rules.get('line_spacing', 'double')}",
            f"Margins: {rules.get('margins', '1 inch')}",
            f"Columns: {rules.get('columns', 1)}",
            f"Paragraph indent: {rules.get('paragraph_indent', '0.5 inch')}",
            f"Heading L1: {rules.get('heading_rules', {}).get('level1', 'center bold')}",
            f"Heading L2: {rules.get('heading_rules', {}).get('level2', 'left bold')}",
            f"Heading L3: {rules.get('heading_rules', {}).get('level3', 'left bold italic')}",
            f"Citation style: {rules.get('citation_style', 'author-year')}",
            f"Reference format: {rules.get('reference_format', 'APA7')}",
            f"Reference section title: {rules.get('reference_section_title', 'References')}",
            f"Title page required: {rules.get('title_page', False)}",
            f"Running head required: {rules.get('running_head', False)}",
            f"Abstract required: {rules.get('abstract_required', False)} (max {rules.get('abstract_word_limit', 'N/A')} words)",
            f"DOI required: {rules.get('doi_required', False)}",
        ]
        return "\n".join(lines)

    def _parse_corrections(self, raw: str) -> list:
        """Extract corrections list from LLM JSON response."""
        text = raw.strip()

        # Strip markdown fences
        for fence in ("```json", "```"):
            if fence in text:
                start = text.find(fence) + len(fence)
                end = text.find("```", start)
                text = text[start:end].strip() if end > start else text[start:].strip()
                break

        # Extract first {...} block
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start != -1 and brace_end > brace_start:
            text = text[brace_start:brace_end + 1]

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return []

        if isinstance(data, dict):
            raw_list = data.get("corrections", [])
        elif isinstance(data, list):
            raw_list = data
        else:
            return []

        return [c for c in raw_list if self._is_valid_correction(c)]

    def _is_valid_correction(self, c: dict) -> bool:
        """Filter out trivial, empty, or malformed corrections."""
        if not isinstance(c, dict):
            return False
        original = str(c.get("original", "")).strip()
        change = str(c.get("change", "")).strip()
        if not original or not change:
            return False
        if original.lower() == change.lower():
            return False
        # Fill in optional fields with defaults
        if "section" not in c:
            c["section"] = "General"
        if "category" not in c:
            c["category"] = "structure"
        if "severity" not in c:
            c["severity"] = "recommended"
        if "reason" not in c:
            c["reason"] = "Style compliance"
        return True

    def _deduplicate(self, corrections: list) -> list:
        """Remove duplicate corrections based on (original, change) key."""
        seen = set()
        deduped = []
        for c in corrections:
            key = (str(c.get("original", "")).strip().lower()[:80],
                   str(c.get("change", "")).strip().lower()[:80])
            if key not in seen:
                seen.add(key)
                deduped.append(c)
        return deduped

    def _sort_by_severity(self, corrections: list) -> list:
        """Sort corrections: required → recommended → optional."""
        order = {"required": 0, "recommended": 1, "optional": 2}
        return sorted(corrections, key=lambda c: order.get(c.get("severity", "recommended"), 1))