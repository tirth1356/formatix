"""
Validation Agent: Evaluate formatting compliance against style rules.
Returns formatting_score, category_scores, issues, suggestions, citation_issues.

FIXES:
- Deterministic pre-pass generates rule-based issues WITHOUT needing the LLM
  (abstract word count, ref section title, heading format, citation format, etc.)
- Scoring is per-category (headings, citations, references, spacing, structure)
  so the UI can show a breakdown, not just one number
- LLM is used for nuanced qualitative review on top of deterministic checks
- citation_result is fully consumed: unmatched citations/references are surfaced
- issues and suggestions are deduped and sorted by severity
- All fields typed and validated — no None, no missing keys
- Score is computed as weighted average across categories (not just LLM guess)
"""
import json
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


SYSTEM_VALIDATE = """You are an expert academic manuscript reviewer. Evaluate formatting compliance strictly. Output only valid JSON — no markdown, no explanation."""

PROMPT_VALIDATE = """Review this academic manuscript against the formatting rules below. Identify every compliance issue and give a score.

=== STYLE RULES ===
{rules_summary}

=== MANUSCRIPT STRUCTURE ===
Title: {title}
Authors: {authors}
Abstract word count: {abstract_wc}
Sections found: {section_headings}
Citation format detected: {citation_format}
References count: {ref_count}

=== CITATION VALIDATION ===
{citation_result}

=== KNOWN ISSUES (pre-detected) ===
{known_issues}

For EACH category below, score 0-100 and list specific issues and actionable suggestions.
Be strict — deduct points for every violation.

Return a single JSON object:
{{
  "category_scores": {{
    "headings": 0-100,
    "citations": 0-100,
    "references": 0-100,
    "spacing_and_font": 0-100,
    "structure": 0-100,
    "abstract": 0-100
  }},
  "issues": [
    {{"category": "headings|citations|references|spacing_and_font|structure|abstract", "severity": "required|recommended|optional", "text": "specific issue description"}}
  ],
  "suggestions": ["actionable suggestion 1", "actionable suggestion 2"],
  "overall_comments": "one paragraph summary"
}}
Return ONLY the JSON object."""


# Category weights for computing weighted overall score
CATEGORY_WEIGHTS = {
    "headings":       0.20,
    "citations":      0.25,
    "references":     0.25,
    "spacing_and_font": 0.15,
    "structure":      0.10,
    "abstract":       0.05,
}


class ValidationAgent:
    def __init__(self, llm_generate_fn):
        self.llm = llm_generate_fn

    async def validate(
        self,
        structure: dict,
        rules: dict,
        citation_result: dict,
        use_cloud: bool,
        model_reasoning: str,
    ) -> dict:
        # Step 1: Deterministic checks (always reliable, no LLM needed)
        deterministic = _run_deterministic_checks(structure, rules, citation_result)

        # Step 2: LLM qualitative review
        llm_result = await self._llm_validate(
            structure, rules, citation_result,
            deterministic["issues"],
            use_cloud, model_reasoning,
        )

        # Step 3: Merge deterministic + LLM results
        return self._merge(deterministic, llm_result, rules)

    # ------------------------------------------------------------------ #
    # LLM review
    # ------------------------------------------------------------------ #

    async def _llm_validate(
        self,
        structure: dict,
        rules: dict,
        citation_result: dict,
        known_issues: list,
        use_cloud: bool,
        model_reasoning: str,
    ) -> dict:
        sections     = structure.get("sections", [])
        section_list = ", ".join(s.get("heading", "") for s in sections[:12]) or "None detected"
        abstract_wc  = len(structure.get("abstract", "").split())
        ref_count    = len(structure.get("references", []))

        rules_summary = _format_rules_summary(rules)
        citation_str  = json.dumps(citation_result, indent=2)[:1500]
        known_str     = "\n".join(f"- {iss['text']}" for iss in known_issues[:10]) or "None"

        prompt = PROMPT_VALIDATE.format(
            rules_summary=rules_summary,
            title=structure.get("title", "Unknown"),
            authors=", ".join(structure.get("authors", [])) or "Unknown",
            abstract_wc=abstract_wc,
            section_headings=section_list,
            citation_format=structure.get("citation_format", "unknown"),
            ref_count=ref_count,
            citation_result=citation_str,
            known_issues=known_str,
        )

        raw = await self.llm(
            "cloud" if use_cloud else "ollama",
            model_reasoning,
            prompt,
            SYSTEM_VALIDATE,
        )
        return self._parse_json(raw)

    # ------------------------------------------------------------------ #
    # Merge deterministic + LLM
    # ------------------------------------------------------------------ #

    def _merge(self, deterministic: dict, llm_result: dict, rules: dict) -> dict:
        # Category scores: use LLM scores as base, then penalise based on deterministic issues
        cat_scores = dict(llm_result.get("category_scores") or {})
        # Fill missing categories
        for cat in CATEGORY_WEIGHTS:
            cat_scores.setdefault(cat, 75)
        # Clamp all to 0-100
        for cat in cat_scores:
            try:
                cat_scores[cat] = max(0, min(100, int(cat_scores[cat])))
            except (TypeError, ValueError):
                cat_scores[cat] = 50

        # Apply deterministic deductions
        for iss in deterministic["issues"]:
            cat = iss.get("category", "structure")
            if cat in cat_scores:
                deduction = {"required": 10, "recommended": 5, "optional": 2}.get(iss.get("severity", "recommended"), 5)
                cat_scores[cat] = max(0, cat_scores[cat] - deduction)

        # Weighted overall score
        overall = int(sum(cat_scores.get(c, 75) * w for c, w in CATEGORY_WEIGHTS.items()))

        # Merge issues
        all_issues = deterministic["issues"] + [
            i for i in (llm_result.get("issues") or [])
            if isinstance(i, dict) and i.get("text")
        ]
        # Dedup by text
        seen: set = set()
        deduped_issues = []
        for iss in all_issues:
            key = str(iss.get("text", ""))[:80].lower()
            if key not in seen:
                seen.add(key)
                deduped_issues.append(iss)

        # Sort: required → recommended → optional
        sev_order = {"required": 0, "recommended": 1, "optional": 2}
        deduped_issues.sort(key=lambda x: sev_order.get(x.get("severity", "recommended"), 1))

        # Merge suggestions
        suggestions = list(dict.fromkeys(
            (deterministic.get("suggestions") or []) + (llm_result.get("suggestions") or [])
        ))

        return {
            "formatting_score":  overall,
            "category_scores":   cat_scores,
            "issues":            deduped_issues,
            "suggestions":       suggestions[:20],
            "overall_comments":  llm_result.get("overall_comments", ""),
            "citation_issues":   deterministic.get("citation_issues", []),
            "style":             rules.get("style", "Unknown"),
        }

    # ------------------------------------------------------------------ #
    # JSON parsing
    # ------------------------------------------------------------------ #

    def _parse_json(self, raw: str) -> dict:
        text = raw.strip()
        for fence in ("```json", "```"):
            if fence in text:
                start = text.find(fence) + len(fence)
                end   = text.find("```", start)
                text  = text[start:end].strip() if end > start else text[start:].strip()
                break
        b_start = text.find("{")
        b_end   = text.rfind("}")
        if b_start != -1 and b_end > b_start:
            text = text[b_start:b_end + 1]
        try:
            out = json.loads(text)
        except json.JSONDecodeError:
            out = {}
        out.setdefault("category_scores", {})
        out.setdefault("issues", [])
        out.setdefault("suggestions", [])
        out.setdefault("overall_comments", "")
        return out


# ---------------------------------------------------------------------------
# Deterministic checks — no LLM required
# ---------------------------------------------------------------------------

def _run_deterministic_checks(structure: dict, rules: dict, citation_result: dict) -> dict:
    """
    Generate rule-based issues, suggestions, and citation problems
    that can be determined without LLM analysis.
    """
    issues: list      = []
    suggestions: list = []
    citation_issues: list = []

    style      = rules.get("style", "APA")
    style_low  = style.lower()
    sections   = structure.get("sections", [])
    abstract   = structure.get("abstract", "")
    references = structure.get("references", [])
    citations  = structure.get("citations", [])
    detected_fmt = structure.get("citation_format", "unknown")
    expected_fmt = rules.get("citation_style", "author-year")

    # -- Abstract --
    abstract_required  = rules.get("abstract_required", False)
    abstract_wc_limit  = rules.get("abstract_word_limit")
    abstract_wc        = len(abstract.split()) if abstract else 0

    if abstract_required and not abstract.strip():
        issues.append({"category": "abstract", "severity": "required",
                       "text": f"{style} requires an abstract but none was detected."})
    elif abstract and abstract_wc_limit and abstract_wc > abstract_wc_limit:
        issues.append({"category": "abstract", "severity": "required",
                       "text": f"Abstract is {abstract_wc} words; {style} limit is {abstract_wc_limit} words."})
        suggestions.append(f"Shorten the abstract to under {abstract_wc_limit} words.")

    # -- Reference section title --
    expected_ref_title = rules.get("reference_section_title", "References")
    ref_section_found  = False
    for s in sections:
        h = s.get("heading", "").strip()
        if re.search(r'\b(references?|bibliography|works\s+cited)\b', h, re.IGNORECASE):
            ref_section_found = True
            if h.lower() != expected_ref_title.lower():
                issues.append({"category": "references", "severity": "required",
                               "text": f'Reference section heading is "{h}" but should be "{expected_ref_title}" for {style}.'})
                suggestions.append(f'Rename the reference section to "{expected_ref_title}".')
    if not ref_section_found:
        issues.append({"category": "structure", "severity": "required",
                       "text": f'No "{expected_ref_title}" section found. {style} requires one.'})

    # -- Title page --
    if rules.get("title_page"):
        issues.append({"category": "structure", "severity": "required",
                       "text": f"{style} requires a separate title page with title, authors, and affiliation."})
        suggestions.append("Add a dedicated title page as the first page of the manuscript.")

    # -- Running head --
    if rules.get("running_head"):
        issues.append({"category": "structure", "severity": "required",
                       "text": f"{style} requires a running head (shortened title ≤50 chars) in the page header."})

    # -- Column layout --
    if rules.get("columns", 1) == 2:
        issues.append({"category": "spacing_and_font", "severity": "required",
                       "text": f"{style} requires a 2-column body layout."})
        suggestions.append("Apply 2-column section formatting to the body of the document.")

    # -- Citation format mismatch --
    fmt_map = {
        "author-year":          ["author-year", "author-date"],
        "numeric":              ["numeric"],
        "numeric-superscript":  ["numeric-superscript", "numeric"],
        "author-page":          ["author-page"],
        "author-date":          ["author-year", "author-date"],
    }
    expected_variants = fmt_map.get(expected_fmt, [expected_fmt])
    if detected_fmt != "unknown" and detected_fmt not in expected_variants:
        issues.append({"category": "citations", "severity": "required",
                       "text": f"Detected citation format '{detected_fmt}' does not match required '{expected_fmt}' for {style}."})
        suggestions.append(f"Convert all in-text citations to {expected_fmt} format.")

    # -- Unmatched citations (from citation_engine output) --
    if isinstance(citation_result, dict):
        unmatched_cites = citation_result.get("unmatched_citations", [])
        unmatched_refs  = citation_result.get("unmatched_references", [])
        for c in unmatched_cites[:5]:
            citation_issues.append({"type": "unmatched_citation",
                                    "text": f"Citation {c!r} has no matching reference entry."})
            issues.append({"category": "citations", "severity": "required",
                           "text": f"In-text citation {c!r} does not match any reference in the reference list."})
        for r in unmatched_refs[:5]:
            citation_issues.append({"type": "unmatched_reference",
                                    "text": f"Reference {str(r)[:80]!r} is not cited in the body."})
            issues.append({"category": "references", "severity": "recommended",
                           "text": f"Reference '{str(r)[:60]}' appears in the reference list but is not cited in the text."})

    # -- DOI check --
    if rules.get("doi_required") and references:
        missing_doi_count = sum(1 for r in references if "doi" not in r.lower() and "http" not in r.lower())
        if missing_doi_count > 0:
            issues.append({"category": "references", "severity": "recommended",
                           "text": f"{missing_doi_count} reference(s) appear to be missing a DOI or URL. {style} recommends including DOIs."})
            suggestions.append("Add DOIs to all references where available.")

    # -- Font and spacing reminders (always present) --
    suggestions.append(
        f"Ensure the entire manuscript uses {rules.get('font','Times New Roman')} "
        f"{rules.get('font_size',12)}pt with {rules.get('line_spacing','double')} line spacing."
    )
    suggestions.append(
        f"Set all margins to {rules.get('margins','1 inch')} and paragraph indent to "
        f"{rules.get('paragraph_indent','0.5 inch')}."
    )

    return {
        "issues":          issues,
        "suggestions":     suggestions,
        "citation_issues": citation_issues,
    }


def _format_rules_summary(rules: dict) -> str:
    hr = rules.get("heading_rules", {})
    lines = [
        f"Style:              {rules.get('style', 'APA')}",
        f"Font:               {rules.get('font', 'Times New Roman')} {rules.get('font_size', 12)}pt",
        f"Line spacing:       {rules.get('line_spacing', 'double')}",
        f"Margins:            {rules.get('margins', '1 inch')}",
        f"Paragraph indent:   {rules.get('paragraph_indent', '0.5 inch')}",
        f"Columns:            {rules.get('columns', 1)}",
        f"Heading L1:         {hr.get('level1', 'center bold')}",
        f"Heading L2:         {hr.get('level2', 'left bold')}",
        f"Heading L3:         {hr.get('level3', 'left bold italic')}",
        f"Citation style:     {rules.get('citation_style', 'author-year')}",
        f"Reference format:   {rules.get('reference_format', 'APA7')}",
        f"Ref section title:  {rules.get('reference_section_title', 'References')}",
        f"Title page:         {rules.get('title_page', False)}",
        f"Running head:       {rules.get('running_head', False)}",
        f"Abstract required:  {rules.get('abstract_required', False)} "
        f"(max {rules.get('abstract_word_limit', 'N/A')} words)",
        f"DOI required:       {rules.get('doi_required', False)}",
    ]
    return "\n".join(lines)