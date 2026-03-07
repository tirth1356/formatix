"""
template_scaffolder.py
━━━━━━━━━━━━━━━━━━━━━━
Defines the canonical section flow for every supported academic style and
rebuilds a complete, properly-ordered section list from a broken or
partially-parsed manuscript.

Called by StructureAgent.analyze() after raw_sections is injected.
If the document is missing sections, garbled, or empty, this module
produces the full skeleton that the DocxFormatter and LaTeX generators
will render — so the output always follows the correct academic flow,
not a copy-paste of the broken input.

Supported styles:
  ieee, apa, apa7, mla, chicago, chicago17, vancouver, harvard,
  acs, ama, nlm, springer, elsevier, nature

Usage:
  from utils.template_scaffolder import TemplateScaffolder
  scaffolder = TemplateScaffolder(style="ieee")
  sections   = scaffolder.scaffold(sections_from_parser, structure_dict)
"""

import re
from copy import deepcopy
from typing import List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Canonical section schemas
# Each entry is a dict:
#   heading        — display heading text
#   level          — 1 = top-level, 2 = subsection, 3 = sub-subsection
#   required       — True = always present even if empty (shown as placeholder)
#   placeholder    — instructional text shown when content is missing
#   aliases        — alternative headings that map to this section
# ─────────────────────────────────────────────────────────────────────────────

_SCHEMAS: dict = {

    # ── IEEE Conference / Journal ─────────────────────────────────────────────
    "ieee": [
        {
            "heading":     "Abstract",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Provide a concise summary of the research (150–250 words). "
                "State the problem, proposed approach, key results, and conclusion. "
                "IEEE abstract appears above the two-column body as a single-column block."
            ),
            "aliases":     ["abstract", "summary"],
        },
        {
            "heading":     "Introduction",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Introduce the problem domain and motivate the work. "
                "State the research gap, objectives, and contributions. "
                "End with a paragraph summarising the structure of the paper. "
                "Typical length: 0.5–1 column."
            ),
            "aliases":     ["introduction", "intro"],
        },
        {
            "heading":     "Related Work",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Survey relevant prior work. Group by theme or methodology. "
                "Identify gaps your work addresses. Cite in IEEE numeric format [1]. "
                "Typical length: 0.5–1 column."
            ),
            "aliases":     ["related work", "literature review", "background", "prior work",
                            "state of the art", "related studies"],
        },
        {
            "heading":     "Methodology",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Describe the proposed system, algorithm, or experimental design in detail. "
                "Include block diagrams, pseudocode, or equations as needed. "
                "Subsections A, B, C... for System Model, Algorithm, Implementation. "
                "Must be reproducible from this description alone."
            ),
            "aliases":     ["methodology", "methods", "proposed method", "proposed approach",
                            "system design", "system model", "approach", "materials and methods",
                            "experimental setup", "experimental design", "framework"],
        },
        {
            "heading":     "Results",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Present experimental results objectively. "
                "Use tables and figures (Table I, Fig. 1) to display quantitative data. "
                "Compare against baselines. State statistical significance where applicable."
            ),
            "aliases":     ["results", "experimental results", "evaluation", "performance evaluation",
                            "experiments", "results and analysis"],
        },
        {
            "heading":     "Discussion",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Interpret results in the context of the research questions. "
                "Explain why results are better/worse than baselines. "
                "Discuss limitations, failure cases, and practical implications."
            ),
            "aliases":     ["discussion", "analysis", "results and discussion"],
        },
        {
            "heading":     "Conclusion",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Summarise the key contributions and findings (no new information). "
                "Restate the problem and how it was solved. "
                "Conclude with future work directions."
            ),
            "aliases":     ["conclusion", "conclusions", "concluding remarks", "summary and conclusion"],
        },
        {
            "heading":     "Acknowledgment",
            "level":       1,
            "required":    False,
            "placeholder": (
                "Acknowledge funding sources, institutional support, "
                "and individuals who contributed but are not listed as authors. "
                "IEEE style: do not use 'Dr.', 'Prof.', or 'Mr.' in this section."
            ),
            "aliases":     ["acknowledgment", "acknowledgements", "acknowledgements"],
        },
    ],

    # ── APA 7th Edition ───────────────────────────────────────────────────────
    "apa": [
        {
            "heading":     "Abstract",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Write a single paragraph of 150–250 words. "
                "Cover: research problem, participants/data, methods, results, conclusions. "
                "Do not indent the first line. Include 3–5 keywords below."
            ),
            "aliases":     ["abstract", "summary"],
        },
        {
            "heading":     "Introduction",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Do not label this section 'Introduction' in APA — the title of the paper "
                "serves as the implicit heading. "
                "Introduce the topic, review relevant literature, state the research question "
                "or hypothesis, and explain the significance of the study."
            ),
            "aliases":     ["introduction"],
        },
        {
            "heading":     "Literature Review",
            "level":       1,
            "required":    False,
            "placeholder": (
                "Synthesise prior research relevant to the study. "
                "Use APA in-text citations: (Author, Year). "
                "Organise thematically, not chronologically."
            ),
            "aliases":     ["literature review", "review of literature", "theoretical background",
                            "background", "related work"],
        },
        {
            "heading":     "Method",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Required section in APA empirical papers. "
                "Include subsections: Participants, Materials/Instruments, Procedure, Design. "
                "Provide enough detail for replication."
            ),
            "aliases":     ["method", "methods", "methodology", "research methodology",
                            "research design", "study design"],
        },
        {
            "heading":     "Results",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Report statistical findings without interpretation. "
                "Reference tables and figures (Table 1, Figure 2). "
                "Include effect sizes, confidence intervals, and p-values (APA 7 requirement)."
            ),
            "aliases":     ["results", "findings", "data analysis", "statistical results"],
        },
        {
            "heading":     "Discussion",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Interpret results in relation to hypotheses and prior literature. "
                "Acknowledge limitations. Discuss theoretical and practical implications. "
                "Suggest directions for future research."
            ),
            "aliases":     ["discussion", "discussion and implications"],
        },
        {
            "heading":     "Conclusion",
            "level":       1,
            "required":    False,
            "placeholder": (
                "Optional in APA — discussion may serve as the conclusion. "
                "If included, summarise the study, its contributions, and key takeaways."
            ),
            "aliases":     ["conclusion", "conclusions", "concluding remarks"],
        },
        {
            "heading":     "References",
            "level":       1,
            "required":    True,
            "placeholder": (
                "List all cited works in APA 7th format. "
                "Hanging indent 0.5 in. Double-spaced. "
                "Author, A. A., & Author, B. B. (Year). Title. Journal, volume(issue), pages. "
                "https://doi.org/..."
            ),
            "aliases":     ["references", "reference list", "bibliography"],
        },
    ],

    # ── MLA 9th Edition ───────────────────────────────────────────────────────
    "mla": [
        {
            "heading":     "Introduction",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Introduce the topic and state the thesis. "
                "MLA essays rarely label sections with formal headings — "
                "consider whether section headings are appropriate for your assignment."
            ),
            "aliases":     ["introduction"],
        },
        {
            "heading":     "Background",
            "level":       1,
            "required":    False,
            "placeholder": (
                "Provide context needed to understand the argument. "
                "Cite sources using MLA in-text format: (Author page)."
            ),
            "aliases":     ["background", "context", "historical context"],
        },
        {
            "heading":     "Analysis",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Develop the central argument with evidence from primary and secondary sources. "
                "Integrate quotations smoothly. Every claim should be supported and cited."
            ),
            "aliases":     ["analysis", "body", "argument", "discussion", "main argument",
                            "literary analysis", "textual analysis"],
        },
        {
            "heading":     "Counterargument",
            "level":       1,
            "required":    False,
            "placeholder": (
                "Acknowledge and refute the strongest opposing viewpoint. "
                "This strengthens the overall argument."
            ),
            "aliases":     ["counterargument", "counter argument", "opposing view", "rebuttal"],
        },
        {
            "heading":     "Conclusion",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Restate the thesis in new words. Synthesise (do not summarise) key points. "
                "End with a broader implication or 'so what?' statement."
            ),
            "aliases":     ["conclusion", "conclusions", "concluding remarks"],
        },
        {
            "heading":     "Works Cited",
            "level":       1,
            "required":    True,
            "placeholder": (
                "List all cited works in MLA 9 format, alphabetically by author last name. "
                "Hanging indent 0.5 in. Double-spaced. New page. "
                "Author Last, First. Title. Publisher, Year."
            ),
            "aliases":     ["works cited", "references", "bibliography", "works consulted"],
        },
    ],

    # ── Chicago 17th Edition (Author-Date & Notes-Bibliography) ───────────────
    "chicago": [
        {
            "heading":     "Abstract",
            "level":       1,
            "required":    False,
            "placeholder": (
                "Optional in Chicago style. 150–300 words. "
                "Place after the title page, before the introduction."
            ),
            "aliases":     ["abstract"],
        },
        {
            "heading":     "Introduction",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Introduce the research problem and scholarly context. "
                "State the argument/thesis. "
                "Chicago is common in humanities — situate the work within the field."
            ),
            "aliases":     ["introduction"],
        },
        {
            "heading":     "Literature Review",
            "level":       1,
            "required":    False,
            "placeholder": (
                "Survey existing scholarship. "
                "Use Chicago author-date citations (Author Year) or footnotes. "
                "Identify the gap your work fills."
            ),
            "aliases":     ["literature review", "historiography", "scholarly context",
                            "background", "related work"],
        },
        {
            "heading":     "Methodology",
            "level":       1,
            "required":    False,
            "placeholder": (
                "Describe archival, qualitative, or quantitative methods used. "
                "Explain why these methods are appropriate for the research question."
            ),
            "aliases":     ["methodology", "methods", "research methods", "approach"],
        },
        {
            "heading":     "Analysis",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Present evidence and argument. Subsections with descriptive headings. "
                "Chicago favours interpretive depth over breadth."
            ),
            "aliases":     ["analysis", "discussion", "argument", "findings", "results"],
        },
        {
            "heading":     "Conclusion",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Synthesise the argument. Discuss broader significance. "
                "Point to unanswered questions and future research."
            ),
            "aliases":     ["conclusion", "conclusions", "concluding remarks"],
        },
        {
            "heading":     "Bibliography",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Chicago 17 bibliography entries. New page. Alphabetical order. "
                "Hanging indent 0.5 in. Double-spaced. "
                "Author Last, First. Title. City: Publisher, Year."
            ),
            "aliases":     ["bibliography", "references", "works cited", "reference list"],
        },
    ],

    # ── Vancouver (ICMJE) ─────────────────────────────────────────────────────
    "vancouver": [
        {
            "heading":     "Abstract",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Structured abstract with labelled subheadings: "
                "Background, Objectives, Methods, Results, Conclusions. "
                "Maximum 300 words. No references cited."
            ),
            "aliases":     ["abstract", "structured abstract"],
        },
        {
            "heading":     "Introduction",
            "level":       1,
            "required":    True,
            "placeholder": (
                "State the problem, relevant background from literature (cite numerically [1]), "
                "and the objective or hypothesis of the study."
            ),
            "aliases":     ["introduction"],
        },
        {
            "heading":     "Methods",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Describe study design, participants/subjects, setting, interventions, "
                "outcome measures, and statistical methods. "
                "Sufficient detail for replication and ethical review."
            ),
            "aliases":     ["methods", "materials and methods", "methodology", "patients and methods",
                            "subjects and methods", "study design"],
        },
        {
            "heading":     "Results",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Present findings in logical order. "
                "Supplement text with tables and figures (do not duplicate in both). "
                "Include sample sizes, measures of central tendency, and variability."
            ),
            "aliases":     ["results", "findings"],
        },
        {
            "heading":     "Discussion",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Interpret main findings. Compare with existing literature. "
                "Strengths and limitations of the study. "
                "Clinical/practical implications. Avoid overstatement."
            ),
            "aliases":     ["discussion", "discussion and conclusion"],
        },
        {
            "heading":     "Conclusion",
            "level":       1,
            "required":    True,
            "placeholder": (
                "One short paragraph. State what the study found and its significance. "
                "Avoid repeating abstract."
            ),
            "aliases":     ["conclusion", "conclusions"],
        },
        {
            "heading":     "Acknowledgments",
            "level":       1,
            "required":    False,
            "placeholder": (
                "Acknowledge contributions, funding, and institutional support. "
                "State role of the funding source."
            ),
            "aliases":     ["acknowledgment", "acknowledgements", "acknowledgments"],
        },
        {
            "heading":     "References",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Number consecutively in order first cited in text. "
                "Vancouver format: Author AA, Author BB. Title. Journal Abbrev. "
                "Year;volume(issue):pages. doi:..."
            ),
            "aliases":     ["references", "reference list"],
        },
    ],

    # ── Harvard ───────────────────────────────────────────────────────────────
    "harvard": [
        {
            "heading":     "Abstract",
            "level":       1,
            "required":    True,
            "placeholder": (
                "150–300 word summary of the research question, methods, findings, "
                "and conclusions. Harvard style is used widely in UK/Australian universities."
            ),
            "aliases":     ["abstract"],
        },
        {
            "heading":     "Introduction",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Background, rationale, aims and objectives of the study. "
                "Harvard in-text: (Author Year) or Author (Year)."
            ),
            "aliases":     ["introduction"],
        },
        {
            "heading":     "Literature Review",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Critical synthesis of existing research. "
                "Identify themes, debates, and gaps. "
                "Every claim requires a Harvard citation."
            ),
            "aliases":     ["literature review", "review of literature", "background", "related work"],
        },
        {
            "heading":     "Methodology",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Research philosophy, approach (qualitative/quantitative/mixed), "
                "design, data collection, sampling, and analysis methods. "
                "Justify methodological choices."
            ),
            "aliases":     ["methodology", "methods", "research methodology", "research design"],
        },
        {
            "heading":     "Findings",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Present data collected — tables, themes, or statistical output. "
                "Neutral presentation without interpretation."
            ),
            "aliases":     ["findings", "results", "data", "results and findings"],
        },
        {
            "heading":     "Discussion",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Interpret findings against the literature review. "
                "Answer the research question. Address limitations."
            ),
            "aliases":     ["discussion", "analysis and discussion"],
        },
        {
            "heading":     "Conclusion",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Summary of key findings, contributions, limitations, "
                "and recommendations for practice or further research."
            ),
            "aliases":     ["conclusion", "conclusions"],
        },
        {
            "heading":     "References",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Alphabetical by author last name. Hanging indent. "
                "Author, Initial. (Year) Title. Edition. Place: Publisher."
            ),
            "aliases":     ["references", "reference list", "bibliography"],
        },
    ],

    # ── ACS (American Chemical Society) ──────────────────────────────────────
    "acs": [
        {
            "heading":     "Abstract",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Single paragraph, typically 150–200 words. "
                "Cover the purpose, experimental approach, key results, and significance. "
                "No citations in ACS abstract."
            ),
            "aliases":     ["abstract"],
        },
        {
            "heading":     "Introduction",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Context and significance of the work. Prior art (cited numerically). "
                "State the objective of this study in the final paragraph."
            ),
            "aliases":     ["introduction"],
        },
        {
            "heading":     "Experimental Section",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Materials, reagents (purity, supplier), instruments, and procedures. "
                "Sufficient detail for replication by a trained chemist. "
                "Subsections by compound or procedure class."
            ),
            "aliases":     ["experimental section", "experimental", "materials and methods",
                            "methods", "experimental methods", "synthesis"],
        },
        {
            "heading":     "Results and Discussion",
            "level":       1,
            "required":    True,
            "placeholder": (
                "ACS typically combines results and discussion in one section. "
                "Present data (spectra, yields, kinetics) and interpret immediately. "
                "Reference figures (Figure 1), tables (Table 1), and schemes (Scheme 1)."
            ),
            "aliases":     ["results and discussion", "results & discussion",
                            "results", "discussion", "findings"],
        },
        {
            "heading":     "Conclusion",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Concise summary of the main findings and their broader significance. "
                "Future directions."
            ),
            "aliases":     ["conclusion", "conclusions", "concluding remarks"],
        },
        {
            "heading":     "Acknowledgment",
            "level":       1,
            "required":    False,
            "placeholder": (
                "Funding agencies (grant numbers), beamtime allocations, "
                "and significant technical assistance."
            ),
            "aliases":     ["acknowledgment", "acknowledgements", "acknowledgments"],
        },
        {
            "heading":     "References",
            "level":       1,
            "required":    True,
            "placeholder": (
                "ACS numbered format. Cited in order of appearance. "
                "(1) Author, A. A.; Author, B. B. J. Am. Chem. Soc. Year, volume, pages."
            ),
            "aliases":     ["references", "bibliography"],
        },
    ],

    # ── Springer / LNCS ───────────────────────────────────────────────────────
    "springer": [
        {
            "heading":     "Abstract",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Structured or unstructured abstract, 100–250 words depending on venue. "
                "Springer LNCS: unstructured, ≤150 words. "
                "Springer Nature journals: may require structured abstract."
            ),
            "aliases":     ["abstract"],
        },
        {
            "heading":     "Introduction",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Motivation, problem statement, contributions, and paper outline. "
                "Springer numeric citations [1]."
            ),
            "aliases":     ["introduction"],
        },
        {
            "heading":     "Related Work",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Position the work against the state of the art. "
                "Group related papers thematically. "
                "Can be Section 2 or moved to before Conclusion in shorter papers."
            ),
            "aliases":     ["related work", "background", "literature review", "prior work"],
        },
        {
            "heading":     "Proposed Approach",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Core technical contribution. "
                "Subsections for problem formulation, model/algorithm, theoretical analysis."
            ),
            "aliases":     ["proposed approach", "method", "methodology", "approach",
                            "system", "framework", "model", "algorithm"],
        },
        {
            "heading":     "Experiments",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Setup, datasets, baselines, metrics, and results. "
                "Ablation studies if applicable."
            ),
            "aliases":     ["experiments", "experimental evaluation", "evaluation", "results",
                            "experimental results"],
        },
        {
            "heading":     "Conclusion",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Summary of contributions and results. Future work."
            ),
            "aliases":     ["conclusion", "conclusions", "conclusion and future work"],
        },
        {
            "heading":     "References",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Numbered in order of citation. Springer LNCS format."
            ),
            "aliases":     ["references", "bibliography"],
        },
    ],

    # ── Elsevier (general journal) ────────────────────────────────────────────
    "elsevier": [
        {
            "heading":     "Abstract",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Structured (Background, Objectives, Methods, Results, Conclusions) or "
                "unstructured depending on journal. 200–300 words. "
                "Followed by 3–6 keywords."
            ),
            "aliases":     ["abstract"],
        },
        {
            "heading":     "Introduction",
            "level":       1,
            "required":    True,
            "placeholder": (
                "State the research problem, gaps in current knowledge, "
                "and the aims of the study. Numbered citation format [1]."
            ),
            "aliases":     ["introduction"],
        },
        {
            "heading":     "Materials and Methods",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Ethical approvals, study population, design, data collection instruments, "
                "and statistical analysis plan."
            ),
            "aliases":     ["materials and methods", "methods", "methodology",
                            "patients and methods", "experimental"],
        },
        {
            "heading":     "Results",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Present findings systematically. Tables and figures must be self-explanatory. "
                "Do not interpret here — save that for Discussion."
            ),
            "aliases":     ["results", "findings"],
        },
        {
            "heading":     "Discussion",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Interpret findings in relation to the literature. "
                "Strengths and limitations. Clinical or practical relevance."
            ),
            "aliases":     ["discussion", "results and discussion"],
        },
        {
            "heading":     "Conclusion",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Key conclusions, recommendations, and future directions."
            ),
            "aliases":     ["conclusion", "conclusions"],
        },
        {
            "heading":     "Acknowledgements",
            "level":       1,
            "required":    False,
            "placeholder": (
                "Funding, institutional support, data access."
            ),
            "aliases":     ["acknowledgements", "acknowledgment", "acknowledgments"],
        },
        {
            "heading":     "References",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Numbered in order of citation. Elsevier Harvard or Vancouver "
                "depending on journal. Check journal-specific guide for authors."
            ),
            "aliases":     ["references", "bibliography", "reference list"],
        },
    ],

    # ── Nature ────────────────────────────────────────────────────────────────
    "nature": [
        {
            "heading":     "Abstract",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Unstructured, ≤150 words (Nature) or ≤200 words (Nature Communications). "
                "No citations. Cover: background (1-2 sentences), gap, approach, "
                "main results, broader significance."
            ),
            "aliases":     ["abstract"],
        },
        {
            "heading":     "Introduction",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Background and significance (2–4 paragraphs). "
                "End with a clear statement of what was done and found. "
                "Nature: Introduction is unlabelled (no heading) — "
                "it begins directly after the abstract."
            ),
            "aliases":     ["introduction"],
        },
        {
            "heading":     "Results",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Present results using subheadings (bold, not numbered). "
                "Reference figures and extended data figures. "
                "Typically 4–6 main figures for a Nature paper."
            ),
            "aliases":     ["results", "results and discussion", "findings"],
        },
        {
            "heading":     "Discussion",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Interpret findings, compare to literature, discuss limitations. "
                "Nature: brief and focused, not a repeat of Results."
            ),
            "aliases":     ["discussion"],
        },
        {
            "heading":     "Methods",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Nature publishes Methods at the end of the article (after Discussion). "
                "Detail all experimental, computational, and statistical methods. "
                "Must include a Data availability statement and Code availability statement."
            ),
            "aliases":     ["methods", "online methods", "materials and methods",
                            "experimental methods"],
        },
        {
            "heading":     "Acknowledgements",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Author contributions (CRediT taxonomy required for Nature journals). "
                "Funding. Competing interests statement."
            ),
            "aliases":     ["acknowledgements", "acknowledgment", "acknowledgments",
                            "author contributions"],
        },
        {
            "heading":     "References",
            "level":       1,
            "required":    True,
            "placeholder": (
                "Numbered, superscript in text. Max ~50 (Nature), ~60 (Nature Communications). "
                "Author, A. B. et al. Title. Journal volume, pages (year)."
            ),
            "aliases":     ["references"],
        },
    ],

}

# Style aliases that map to canonical keys
_STYLE_ALIASES: dict = {
    "apa7":        "apa",
    "apa 7":       "apa",
    "chicago17":   "chicago",
    "chicago 17":  "chicago",
    "nlm":         "vancouver",
    "icmje":       "vancouver",
    "lncs":        "springer",
    "nature communications": "nature",
    "nat commun":  "nature",
}


# ─────────────────────────────────────────────────────────────────────────────
# TemplateScaffolder
# ─────────────────────────────────────────────────────────────────────────────

class TemplateScaffolder:
    """
    Guarantees a complete, correctly-ordered section list for any supported
    academic style.

    When called with sections from a broken document, it:
    1. Normalises the incoming sections (heading, level, content, word_count).
    2. Matches each incoming section to the canonical schema using alias lookup.
    3. Inserts placeholder sections for any required (or all) schema entries
       not found in the parsed document.
    4. Preserves any extra author-added sections the parser found.
    5. Returns a clean, ordered list ready for the DOCX/LaTeX formatters.
    """

    def __init__(self, style: str = "ieee"):
        canonical_style = style.lower().strip()
        canonical_style = _STYLE_ALIASES.get(canonical_style, canonical_style)
        self.style   = canonical_style
        self.schema  = _SCHEMAS.get(canonical_style, _SCHEMAS["ieee"])

    def scaffold(
        self,
        sections: List[dict],
        structure: Optional[dict] = None,
        force_all: bool = False,
    ) -> List[dict]:
        """
        Build the full ordered section list.

        Args:
            sections:  list of section dicts from parser/structure agent
            structure: full structure dict (used to recover abstract if missing)
            force_all: if True, insert placeholder for every schema section,
                       not just required ones (useful for completely empty docs)

        Returns:
            Ordered list of section dicts, each with keys:
              heading, level, content, word_count, _placeholder (bool), _style_section (str)
        """
        structure = structure or {}

        # ── Normalise incoming sections ────────────────────────────────────────
        incoming   = [self._normalise(s) for s in (sections or [])]
        # Don't force placeholders - only use actual content from the document
        force_all  = False

        # ── Build alias lookup: normalised alias → schema entry ────────────────
        alias_map: dict = {}
        for entry in self.schema:
            for alias in entry["aliases"]:
                alias_map[self._norm(alias)] = entry

        # ── Match incoming sections to schema entries ──────────────────────────
        schema_headings_norm = {self._norm(e["heading"]) for e in self.schema}

        matched: dict = {}     # schema heading (norm) → best incoming section dict
        extras:  List[dict] = []   # sections not in schema

        for sec in incoming:
            h_norm    = self._norm_heading_for_match(sec["heading"])
            schema_e  = alias_map.get(h_norm)
            if schema_e:
                key = self._norm(schema_e["heading"])
                # Keep the first match, or prefer non-empty over empty
                if key not in matched or (not matched[key]["content"] and sec["content"]):
                    matched[key] = sec
            else:
                # Not a recognised section name — keep as extra
                skip_always = {"references", "bibliography", "workscited", "referencelist"}
                if h_norm not in skip_always:
                    extras.append(sec)

        # ── Build ordered result ───────────────────────────────────────────────
        result: List[dict] = []

        # Track where to insert extras (after Related Work / Literature Review, or before Conclusion)
        extras_insertion_key = self._find_extras_insertion_point()
        extras_inserted      = False

        for entry in self.schema:
            key        = self._norm(entry["heading"])
            existing   = matched.get(key)
            is_refs    = key in {"references", "bibliography", "workscited", "referencelist"}
            is_ack     = key in {"acknowledgment", "acknowledgements", "acknowledgments"}

            # Special case: abstract — may be in structure["abstract"] not sections
            if key == "abstract":
                abstract_text = (
                    (existing["content"] if existing and existing["content"] else None)
                    or structure.get("abstract", "")
                )
                if abstract_text or entry["required"] or force_all:
                    result.append({
                        "heading":       "Abstract",
                        "level":         1,
                        "content":       abstract_text or entry["placeholder"],
                        "word_count":    len(abstract_text.split()) if abstract_text else 0,
                        "_placeholder":  not bool(abstract_text),
                        "_style_section": entry["heading"],
                    })
                continue

            # Special case: reference list — always defer to the references array
            if is_refs:
                # Rendered separately by the formatter from structure["references"]
                continue

            should_include = (
                existing is not None
                or entry["required"]
                or force_all
            )
            if not should_include:
                continue

            if existing:
                section_dict = dict(existing)
                section_dict["_placeholder"]    = not bool(existing.get("content", "").strip())
                section_dict["_style_section"]  = entry["heading"]
                # Normalise heading to canonical name (e.g. "Experimental" → "Experimental Section")
                section_dict["heading"]          = entry["heading"]
            else:
                # Only add placeholder if force_all is True
                if not force_all:
                    continue
                section_dict = {
                    "heading":       entry["heading"],
                    "level":         entry["level"],
                    "content":       entry["placeholder"],
                    "word_count":    0,
                    "_placeholder":  True,
                    "_style_section": entry["heading"],
                }

            result.append(section_dict)

            # Insert extras after the designated insertion point
            if key == extras_insertion_key and not extras_inserted:
                for extra in extras:
                    extra["_placeholder"]   = False
                    extra["_style_section"] = extra.get("heading", "")
                    result.append(extra)
                extras_inserted = True

        # If insertion point never reached, add extras before Acknowledgment
        if not extras_inserted:
            ack_idx = next(
                (i for i, s in enumerate(result)
                 if self._norm(s.get("heading", "")) in {"acknowledgment", "acknowledgements"}),
                len(result),
            )
            for j, extra in enumerate(extras):
                extra["_placeholder"]   = False
                extra["_style_section"] = extra.get("heading", "")
                result.insert(ack_idx + j, extra)

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _norm(text: str) -> str:
        return re.sub(r'[^a-z0-9]', '', text.lower())

    @staticmethod
    def _norm_heading_for_match(text: str) -> str:
        """Strip leading Roman numerals and numbers so 'I. INTRODUCTION' matches alias 'introduction'."""
        if not text:
            return ""
        s = text.strip()
        s = re.sub(r'^(?:[IVXLCDM]+\.?|[0-9]+(?:\.[0-9]+)*\.?)\s*', '', s, flags=re.IGNORECASE).strip()
        return re.sub(r'[^a-z0-9]', '', s.lower())

    @staticmethod
    def _normalise(s: dict) -> dict:
        content = str(s.get("content", "")).strip()
        return {
            "heading":    str(s.get("heading", "Untitled")).strip(),
            "level":      int(s.get("level", 1)),
            "content":    content,
            "word_count": len(content.split()) if content else 0,
        }

    def _find_extras_insertion_point(self) -> str:
        """
        Find the normalised key after which extra sections should be inserted.
        Prefers 'relatedwork' or 'literaturereview'; falls back to first section.
        """
        preferred = ["relatedwork", "literaturereview", "background"]
        schema_norms = [self._norm(e["heading"]) for e in self.schema]
        for p in preferred:
            if p in schema_norms:
                return p
        return schema_norms[0] if schema_norms else ""

    def get_schema_headings(self) -> List[str]:
        """Return the list of canonical heading names for this style."""
        return [e["heading"] for e in self.schema]

    def get_required_headings(self) -> List[str]:
        """Return only the required heading names for this style."""
        return [e["heading"] for e in self.schema if e["required"]]

    @classmethod
    def supported_styles(cls) -> List[str]:
        """Return all supported style keys."""
        return list(_SCHEMAS.keys())