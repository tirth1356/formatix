"""
Citation Engine: Validates in-text citations against the reference list.
Works with all styles produced by RuleExtractionAgent:
  author-year    → (Smith, 2020), (Jones & Lee, 2019)
  numeric        → [1], [2,3], [4-6]
  numeric-superscript → superscript numbers (detected from structure)
  author-page    → (Smith 42), (Jones 100-105)
  author-date    → same as author-year

Produces:
  matched_count       — citations with a found reference
  unmatched_citations — in-text citations with no reference match
  unmatched_references — references never cited in-text
  orphan_count        — alias for len(unmatched_references)
  match_rate          — 0.0-1.0
  details             — per-citation match results
"""
import re
from typing import List, Dict, Any


# ---------------------------------------------------------------------------
# Regex patterns for each citation format
# ---------------------------------------------------------------------------

_NUMERIC_RE            = re.compile(r'\[(\d+(?:[,;\s\-–]+\d+)*)\]')
_AUTHOR_YEAR_RE        = re.compile(
    r'\(([A-Z][a-zA-Z\-]+(?:\s+et\s+al\.?)?,?\s+\d{4}[a-z]?'
    r'(?:;\s*[A-Z][a-zA-Z\-]+.*?)?)\)'
)
_AUTHOR_PAGE_RE        = re.compile(
    r'\(([A-Z][a-zA-Z\-]+(?:\s+et\s+al\.?)?\s+\d+(?:[-–]\d+)?)\)'
)


class CitationEngine:
    """
    Validates citations extracted by StructureAgent against the reference list.
    """

    def __init__(self, citation_style: str = "author-year"):
        """
        citation_style: value from rules["citation_style"]
          e.g. "author-year", "numeric", "numeric-superscript",
               "author-page", "author-date"
        """
        self.citation_style = citation_style.lower().strip()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def validate(
        self,
        structure: dict,
        raw_text: str = "",
    ) -> Dict[str, Any]:
        """
        Cross-reference in-text citations against the reference list.

        Args:
            structure: output from StructureAgent.analyze()
            raw_text:  full manuscript text (used for superscript detection)

        Returns:
            dict with match statistics and problem lists
        """
        citations  = structure.get("citations", [])
        references = structure.get("references", [])
        fmt        = structure.get("citation_format") or self.citation_style

        # Normalise detected format to our canonical names
        fmt = self._normalise_fmt(fmt)

        if fmt in ("numeric", "numeric-superscript"):
            return self._validate_numeric(citations, references)
        if fmt in ("author-year", "author-date"):
            return self._validate_author_year(citations, references)
        if fmt == "author-page":
            return self._validate_author_page(citations, references)

        # Unknown / mixed — attempt best-effort
        return self._validate_best_effort(citations, references)

    # ------------------------------------------------------------------ #
    # Per-format validators
    # ------------------------------------------------------------------ #

    def _validate_numeric(
        self,
        citations: List[str],
        references: List[str],
    ) -> Dict[str, Any]:
        """
        Numeric: [1], [2,3], [4-6]
        Match by ordinal position in reference list.
        """
        total_refs = len(references)
        # Expand all citation numbers
        cited_numbers: set = set()
        for c in citations:
            cited_numbers.update(self._expand_numeric_citation(c))

        valid_numbers   = {n for n in cited_numbers if 1 <= n <= total_refs}
        invalid_numbers = {n for n in cited_numbers if n < 1 or n > total_refs}

        unmatched_cites = [f"[{n}]" for n in sorted(invalid_numbers)]
        # References never cited
        all_ref_numbers = set(range(1, total_refs + 1))
        uncited_numbers = all_ref_numbers - cited_numbers
        unmatched_refs  = [references[n - 1] for n in sorted(uncited_numbers) if n <= total_refs]

        matched = len(valid_numbers)
        total   = len(cited_numbers) or 1

        return {
            "format":               "numeric",
            "matched_count":        matched,
            "unmatched_citations":  unmatched_cites,
            "unmatched_references": unmatched_refs,
            "orphan_count":         len(unmatched_refs),
            "match_rate":           round(matched / total, 3),
            "details":              [
                {"citation": f"[{n}]", "matched": n in valid_numbers,
                 "reference": references[n - 1] if n <= total_refs else None}
                for n in sorted(cited_numbers)
            ],
        }

    def _validate_author_year(
        self,
        citations: List[str],
        references: List[str],
    ) -> Dict[str, Any]:
        """
        Author-year: (Smith, 2020), (Jones & Lee, 2019)
        Match by last name + year lookup in reference strings.
        """
        details: list         = []
        unmatched_cites: list = []
        matched_ref_indices: set = set()

        for raw_cite in citations:
            # Parse out (Author, Year) from the citation string
            parsed = self._parse_author_year(raw_cite)
            if not parsed:
                details.append({"citation": raw_cite, "matched": False, "reference": None})
                unmatched_cites.append(raw_cite)
                continue

            author, year = parsed
            match_idx = self._find_reference_author_year(author, year, references)
            if match_idx is not None:
                matched_ref_indices.add(match_idx)
                details.append({
                    "citation":  raw_cite,
                    "matched":   True,
                    "reference": references[match_idx],
                })
            else:
                details.append({"citation": raw_cite, "matched": False, "reference": None})
                unmatched_cites.append(raw_cite)

        unmatched_refs = [
            references[i]
            for i in range(len(references))
            if i not in matched_ref_indices
        ]
        matched    = sum(1 for d in details if d["matched"])
        total      = len(details) or 1

        return {
            "format":               "author-year",
            "matched_count":        matched,
            "unmatched_citations":  unmatched_cites,
            "unmatched_references": unmatched_refs,
            "orphan_count":         len(unmatched_refs),
            "match_rate":           round(matched / total, 3),
            "details":              details,
        }

    def _validate_author_page(
        self,
        citations: List[str],
        references: List[str],
    ) -> Dict[str, Any]:
        """
        Author-page (MLA): (Smith 42), (Jones 100-105)
        Match by author last name only (page numbers vary).
        """
        details: list         = []
        unmatched_cites: list = []
        matched_ref_indices: set = set()

        for raw_cite in citations:
            m = re.search(r'\(([A-Z][a-zA-Z\-]+)', raw_cite)
            if not m:
                details.append({"citation": raw_cite, "matched": False, "reference": None})
                unmatched_cites.append(raw_cite)
                continue
            last_name = m.group(1).lower()
            match_idx = next(
                (i for i, r in enumerate(references)
                 if last_name in r.lower()),
                None
            )
            if match_idx is not None:
                matched_ref_indices.add(match_idx)
                details.append({"citation": raw_cite, "matched": True, "reference": references[match_idx]})
            else:
                details.append({"citation": raw_cite, "matched": False, "reference": None})
                unmatched_cites.append(raw_cite)

        unmatched_refs = [references[i] for i in range(len(references)) if i not in matched_ref_indices]
        matched = sum(1 for d in details if d["matched"])
        total   = len(details) or 1

        return {
            "format":               "author-page",
            "matched_count":        matched,
            "unmatched_citations":  unmatched_cites,
            "unmatched_references": unmatched_refs,
            "orphan_count":         len(unmatched_refs),
            "match_rate":           round(matched / total, 3),
            "details":              details,
        }

    def _validate_best_effort(
        self,
        citations: List[str],
        references: List[str],
    ) -> Dict[str, Any]:
        """Fallback: attempt numeric then author-year detection."""
        if citations and re.match(r'^\[\d+\]$', citations[0].strip()):
            return self._validate_numeric(citations, references)
        return self._validate_author_year(citations, references)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _normalise_fmt(fmt: str) -> str:
        mapping = {
            "author-date":         "author-year",
            "author_year":         "author-year",
            "authordate":          "author-year",
            "authoryear":          "author-year",
            "numeric-superscript": "numeric-superscript",
            "superscript":         "numeric-superscript",
            "author-page":         "author-page",
            "authorpage":          "author-page",
        }
        return mapping.get(fmt.lower(), fmt.lower())

    @staticmethod
    def _expand_numeric_citation(cite_str: str) -> List[int]:
        """
        Turn "[1,3,5-7]" → [1, 3, 5, 6, 7]
        """
        numbers = []
        # Strip brackets
        inner = re.sub(r'[\[\]]', '', cite_str)
        # Split on commas or semicolons
        for part in re.split(r'[,;]', inner):
            part = part.strip()
            # Range: 5-7 or 5–7
            range_m = re.match(r'(\d+)\s*[-–]\s*(\d+)', part)
            if range_m:
                start, end = int(range_m.group(1)), int(range_m.group(2))
                numbers.extend(range(start, end + 1))
            elif part.isdigit():
                numbers.append(int(part))
        return numbers

    @staticmethod
    def _parse_author_year(cite_str: str):
        """
        Extract (last_name, year) from strings like:
          "(Smith, 2020)", "(Jones & Lee, 2019)", "(Chen et al., 2021)"
        Returns (str, str) or None.
        """
        # Strip outer parens
        inner = re.sub(r'[()]', '', cite_str).strip()
        # Year is 4 digits
        year_m = re.search(r'\b(\d{4}[a-z]?)\b', inner)
        if not year_m:
            return None
        year = year_m.group(1)
        # Author: everything before the year (and comma/ampersand)
        author_part = inner[:year_m.start()].strip().rstrip(',').strip()
        # Take first last name
        first_author = re.split(r'[,;&]|\bet\s+al', author_part)[0].strip()
        # Last token of the name
        tokens = first_author.split()
        last_name = tokens[-1] if tokens else first_author
        return (last_name.lower(), year[:4])  # normalise to 4-digit year

    @staticmethod
    def _find_reference_author_year(
        last_name: str,
        year: str,
        references: List[str],
    ) -> int | None:
        """
        Find index of the reference containing last_name and year.
        """
        for i, ref in enumerate(references):
            ref_lower = ref.lower()
            if last_name in ref_lower and year in ref:
                return i
        # Fuzzy: year only if author very short
        if len(last_name) <= 3:
            for i, ref in enumerate(references):
                if year in ref:
                    return i
        return None