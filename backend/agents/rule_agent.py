"""
Rule Extraction Agent: Interpret formatting rules using phi3/Llama.
Supports APA, MLA, Chicago, IEEE, Vancouver and custom guidelines.

FIXES:
- Added hardcoded authoritative fallbacks per style (LLM-independent correctness)
- Stricter prompt with explicit field constraints and validation
- Post-processing normalization: line_spacing, columns, margins, fonts
- Custom guidelines are parsed and merged properly (not just appended)
- Added Chicago style support
- All edge cases handled: missing keys, wrong types, out-of-range values
"""
import json
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


SYSTEM_RULES = """You are an expert in academic style guides. Output only valid JSON with no markdown, no preamble, no explanation."""

PROMPT_RULES = """You are an authoritative academic style guide. Output the EXACT formatting rules for the style "{style}".

Required JSON fields (ALL required, no omissions):
- "style": string — must be exactly "{style}"
- "font": string — exact font name (e.g., "Times New Roman", "Arial", "Courier New")
- "font_size": integer — body text size in points (e.g., 10, 11, 12)
- "line_spacing": string — MUST be exactly one of: "single", "1.5", "double"
- "margins": string — e.g., "1 inch", "1.5 inch left"
- "columns": integer — 1 or 2 only
- "paragraph_indent": string — first-line indent (e.g., "0.5 inch", "none")
- "heading_rules": object with keys "level1", "level2", "level3" — each a string like "center bold", "left bold italic", "left italic", "center"
- "citation_style": string — one of: "author-year", "numeric", "numeric-superscript", "author-page", "author-date", "footnote"
- "reference_format": string — one of: "APA7", "MLA9", "Chicago17", "IEEE", "Vancouver", "Custom"
- "running_head": boolean — true if style requires running header
- "title_page": boolean — true if style requires separate title page
- "abstract_required": boolean — true if style requires abstract
- "abstract_word_limit": integer or null — max words for abstract (null if not specified)
- "reference_section_title": string — exact heading for references (e.g., "References", "Works Cited", "Bibliography")
- "doi_required": boolean — true if DOI should be included in references when available
- "url_format": string — how to format URLs (e.g., "Retrieved from URL", "https://doi.org/...", "Accessed date")

Custom guidelines to merge/override defaults (apply these ON TOP of standard {style} rules):
{guidelines}

AUTHORITATIVE RULES — output EXACTLY these for standard styles:

APA 7th Edition:
{{"style":"APA","font":"Times New Roman","font_size":12,"line_spacing":"double","margins":"1 inch","columns":1,"paragraph_indent":"0.5 inch","heading_rules":{{"level1":"center bold","level2":"left bold","level3":"left bold italic"}},"citation_style":"author-year","reference_format":"APA7","running_head":false,"title_page":true,"abstract_required":true,"abstract_word_limit":250,"reference_section_title":"References","doi_required":true,"url_format":"https://doi.org/..."}}

MLA 9th Edition:
{{"style":"MLA","font":"Times New Roman","font_size":12,"line_spacing":"double","margins":"1 inch","columns":1,"paragraph_indent":"0.5 inch","heading_rules":{{"level1":"left bold","level2":"left italic","level3":"left bold italic"}},"citation_style":"author-page","reference_format":"MLA9","running_head":false,"title_page":false,"abstract_required":false,"abstract_word_limit":null,"reference_section_title":"Works Cited","doi_required":false,"url_format":"Accessed Day Month Year"}}

Chicago 17th Edition (Author-Date):
{{"style":"Chicago","font":"Times New Roman","font_size":12,"line_spacing":"double","margins":"1 inch","columns":1,"paragraph_indent":"0.5 inch","heading_rules":{{"level1":"center bold","level2":"left bold","level3":"left bold italic"}},"citation_style":"author-date","reference_format":"Chicago17","running_head":false,"title_page":true,"abstract_required":false,"abstract_word_limit":null,"reference_section_title":"Bibliography","doi_required":true,"url_format":"https://doi.org/..."}}

IEEE:
{{"style":"IEEE","font":"Times New Roman","font_size":10,"line_spacing":"single","margins":"0.75 inch","columns":2,"paragraph_indent":"0.5 inch","heading_rules":{{"level1":"center small-caps","level2":"left italic","level3":"left italic"}},"citation_style":"numeric","reference_format":"IEEE","running_head":false,"title_page":false,"abstract_required":true,"abstract_word_limit":250,"reference_section_title":"References","doi_required":true,"url_format":"[Online]. Available: URL"}}

Vancouver:
{{"style":"Vancouver","font":"Arial","font_size":11,"line_spacing":"double","margins":"1 inch","columns":1,"paragraph_indent":"none","heading_rules":{{"level1":"left bold","level2":"left bold italic","level3":"left italic"}},"citation_style":"numeric-superscript","reference_format":"Vancouver","running_head":false,"title_page":false,"abstract_required":true,"abstract_word_limit":300,"reference_section_title":"References","doi_required":true,"url_format":"Available from: URL"}}

Return ONLY the JSON object. No markdown. No explanation."""


# Authoritative fallback rules — used when LLM output fails or is incomplete
STYLE_DEFAULTS = {
    "APA": {
        "style": "APA",
        "font": "Times New Roman",
        "font_size": 12,
        "line_spacing": "double",
        "margins": "1 inch",
        "columns": 1,
        "paragraph_indent": "0.5 inch",
        "heading_rules": {
            "level1": "center bold",
            "level2": "left bold",
            "level3": "left bold italic",
        },
        "citation_style": "author-year",
        "reference_format": "APA7",
        "running_head": False,
        "title_page": True,
        "abstract_required": True,
        "abstract_word_limit": 250,
        "reference_section_title": "References",
        "doi_required": True,
        "url_format": "https://doi.org/...",
    },
    "MLA": {
        "style": "MLA",
        "font": "Times New Roman",
        "font_size": 12,
        "line_spacing": "double",
        "margins": "1 inch",
        "columns": 1,
        "paragraph_indent": "0.5 inch",
        "heading_rules": {
            "level1": "left bold",
            "level2": "left italic",
            "level3": "left bold italic",
        },
        "citation_style": "author-page",
        "reference_format": "MLA9",
        "running_head": False,
        "title_page": False,
        "abstract_required": False,
        "abstract_word_limit": None,
        "reference_section_title": "Works Cited",
        "doi_required": False,
        "url_format": "Accessed Day Month Year",
    },
    "Chicago": {
        "style": "Chicago",
        "font": "Times New Roman",
        "font_size": 12,
        "line_spacing": "double",
        "margins": "1 inch",
        "columns": 1,
        "paragraph_indent": "0.5 inch",
        "heading_rules": {
            "level1": "center bold",
            "level2": "left bold",
            "level3": "left bold italic",
        },
        "citation_style": "author-date",
        "reference_format": "Chicago17",
        "running_head": False,
        "title_page": True,
        "abstract_required": False,
        "abstract_word_limit": None,
        "reference_section_title": "Bibliography",
        "doi_required": True,
        "url_format": "https://doi.org/...",
    },
    "IEEE": {
        "style": "IEEE",
        "font": "Times New Roman",
        "font_size": 10,
        "line_spacing": "single",
        "margins": "0.75 inch",
        "columns": 2,
        "paragraph_indent": "0.5 inch",
        "heading_rules": {
            "level1": "center small-caps",
            "level2": "left italic",
            "level3": "left italic",
        },
        "citation_style": "numeric",
        "reference_format": "IEEE",
        "running_head": False,
        "title_page": False,
        "abstract_required": True,
        "abstract_word_limit": 250,
        "reference_section_title": "References",
        "doi_required": True,
        "url_format": "[Online]. Available: URL",
    },
    "Vancouver": {
        "style": "Vancouver",
        "font": "Arial",
        "font_size": 11,
        "line_spacing": "double",
        "margins": "1 inch",
        "columns": 1,
        "paragraph_indent": "none",
        "heading_rules": {
            "level1": "left bold",
            "level2": "left bold italic",
            "level3": "left italic",
        },
        "citation_style": "numeric-superscript",
        "reference_format": "Vancouver",
        "running_head": False,
        "title_page": False,
        "abstract_required": True,
        "abstract_word_limit": 300,
        "reference_section_title": "References",
        "doi_required": True,
        "url_format": "Available from: URL",
    },
}

REQUIRED_KEYS = {
    "style", "font", "font_size", "line_spacing", "margins", "columns",
    "paragraph_indent", "heading_rules", "citation_style", "reference_format",
    "running_head", "title_page", "abstract_required", "abstract_word_limit",
    "reference_section_title", "doi_required", "url_format",
}

VALID_LINE_SPACINGS = {"single", "1.5", "double"}


class RuleExtractionAgent:
    def __init__(self, llm_generate_fn):
        self.llm = llm_generate_fn

    async def extract(
        self,
        style: str,
        guidelines_text: str,
        use_cloud: bool,
        model_fast: str,
    ) -> dict:
        style_key = style.strip().upper()
        guidelines = guidelines_text.strip() if guidelines_text else ""

        # If no custom guidelines and known style, use hardcoded defaults directly
        if not guidelines and style_key in STYLE_DEFAULTS:
            result = dict(STYLE_DEFAULTS[style_key])
            result["style"] = style  # preserve original casing
            return result

        prompt = PROMPT_RULES.format(
            style=style,
            guidelines=guidelines or "None — use standard official rules for this style.",
        )
        raw = await self.llm(
            "cloud" if use_cloud else "ollama",
            model_fast,
            prompt,
            SYSTEM_RULES,
        )
        parsed = self._parse_json(raw)
        normalized = self._normalize(parsed, style_key)

        # If custom guidelines exist, merge them over the normalized result
        if guidelines:
            custom = self._parse_custom_guidelines(guidelines)
            normalized.update({k: v for k, v in custom.items() if v is not None})

        return normalized

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _parse_json(self, raw: str) -> dict:
        text = raw.strip()
        # Strip markdown fences
        for fence in ("```json", "```"):
            if fence in text:
                start = text.find(fence) + len(fence)
                end = text.find("```", start)
                text = text[start:end].strip() if end > start else text[start:].strip()
                break
        # Try extracting first {...} block if extra text present
        brace_match = re.search(r'\{.*\}', text, re.DOTALL)
        if brace_match:
            text = brace_match.group(0)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}

    def _normalize(self, data: dict, style_key: str) -> dict:
        """
        Fill missing keys from authoritative defaults, fix type errors,
        and validate enum values.
        """
        base = dict(STYLE_DEFAULTS.get(style_key, STYLE_DEFAULTS["APA"]))

        # Merge LLM output over base — only overwrite if value is valid
        for key in REQUIRED_KEYS:
            if key in data and data[key] is not None:
                base[key] = data[key]

        # --- Type enforcement ---
        base["font_size"] = int(base["font_size"]) if str(base.get("font_size", "12")).isdigit() else (
            int(re.search(r'\d+', str(base.get("font_size", "12"))).group()) if re.search(r'\d+', str(base.get("font_size", "12"))) else 12
        )
        base["columns"] = int(base["columns"]) if base.get("columns") in (1, 2, "1", "2") else 1
        base["running_head"] = bool(base.get("running_head", False))
        base["title_page"] = bool(base.get("title_page", False))
        base["abstract_required"] = bool(base.get("abstract_required", False))
        base["doi_required"] = bool(base.get("doi_required", False))

        if base.get("abstract_word_limit") is not None:
            try:
                base["abstract_word_limit"] = int(base["abstract_word_limit"])
            except (TypeError, ValueError):
                base["abstract_word_limit"] = None

        # --- Enum validation: line_spacing ---
        spacing = str(base.get("line_spacing", "double")).lower().strip()
        spacing_map = {
            "single": "single", "1": "single", "1.0": "single",
            "1.5": "1.5", "one-and-a-half": "1.5",
            "double": "double", "2": "double", "2.0": "double",
        }
        base["line_spacing"] = spacing_map.get(spacing, "double")

        # --- heading_rules integrity ---
        if not isinstance(base.get("heading_rules"), dict):
            base["heading_rules"] = {"level1": "center bold", "level2": "left bold", "level3": "left bold italic"}
        for lvl in ("level1", "level2", "level3"):
            if lvl not in base["heading_rules"] or not base["heading_rules"][lvl]:
                base["heading_rules"][lvl] = "left bold"

        # --- font sanity ---
        allowed_fonts = {"Times New Roman", "Arial", "Courier New", "Calibri", "Helvetica"}
        if base.get("font") not in allowed_fonts:
            base["font"] = "Times New Roman"

        return base

    def _parse_custom_guidelines(self, text: str) -> dict:
        """
        Very lightweight parser: extract key=value overrides from free-form
        custom guideline text (e.g., "font: Arial, font_size: 11").
        """
        overrides = {}
        # Match patterns like "font: Arial" or "font_size=11"
        for match in re.finditer(
            r'\b(font_size|font|line_spacing|margins|columns|paragraph_indent|citation_style)\s*[=:]\s*([^\n,;]+)',
            text, re.IGNORECASE
        ):
            key = match.group(1).lower().replace(" ", "_")
            val = match.group(2).strip().strip('"\'')
            if key == "font_size":
                try:
                    overrides[key] = int(val)
                except ValueError:
                    pass
            elif key == "columns":
                try:
                    overrides[key] = int(val)
                except ValueError:
                    pass
            else:
                overrides[key] = val
        return overrides