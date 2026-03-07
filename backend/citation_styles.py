"""
Citation styles definitions and formatting utilities.
Supports: IEEE, APA, MLA, Chicago, Vancouver
"""
from typing import Optional

def ieee_journal(data):
    parts = []
    if data.get("authors"):
        parts.append(f'{data["authors"]}')
    if data.get("title"):
        parts.append(f'"{data["title"]},"')
    if data.get("journal"):
        parts.append(data["journal"])
    if data.get("volume"):
        parts.append(f'vol. {data["volume"]}')
    if data.get("number"):
        parts.append(f'no. {data["number"]}')
    if data.get("pages"):
        parts.append(f'pp. {data["pages"]}')
    if data.get("year"):
        parts.append(data["year"])
    citation = ", ".join(parts)
    if data.get("index"):
        citation = f'[{data["index"]}] ' + citation
    return citation + "."

CITATION_STYLES = {

    "ieee": {
        "name": "IEEE",
        "category": "Engineering",
        "layout": "two-column",
        "citation_type": "numbered",

        "journal":    ieee_journal,
        "conference": "[{index}] {authors}, \"{title},\" in {conference}, {year}, pp. {pages}.",
        "book":       "[{index}] {authors}, {book_title}. {city}: {publisher}, {year}.",
        "website":    "[{index}] {author}, \"{title},\" {website}. [Online]. Available: {url}. [Accessed: {date}].",

        "in_text": "[{index}]",

        # Formatting rules applied to the document
        "formatting": {
            "font_family":      "Times New Roman",
            "font_size_pt":     10,
            "line_spacing":     "single",
            "columns":          2,
            "margin_top_cm":    1.9,
            "margin_bottom_cm": 2.54,
            "margin_left_cm":   1.52,
            "margin_right_cm":  1.52,
            "heading_bold":     True,
            "abstract_bold":    True,
            "section_style":    "ROMAN_NUMERALS",  # e.g. I. INTRODUCTION
        },
    },

    "apa": {
        "name": "APA",
        "category": "Social Sciences",
        "layout": "single-column",
        "citation_type": "author-date",

        "journal":    "{authors} ({year}). {title}. {journal}, {volume}({number}), {pages}.",
        "conference": "{authors} ({year}). {title}. In {conference} (pp. {pages}).",
        "book":       "{authors} ({year}). {book_title}. {publisher}.",
        "website":    "{author} ({year}). {title}. {website}. {url}",

        "in_text": "({author_last}, {year})",

        "formatting": {
            "font_family":      "Times New Roman",
            "font_size_pt":     12,
            "line_spacing":     "double",
            "columns":          1,
            "margin_top_cm":    2.54,
            "margin_bottom_cm": 2.54,
            "margin_left_cm":   2.54,
            "margin_right_cm":  2.54,
            "heading_bold":     True,
            "abstract_indent":  False,
            "section_style":    "TITLE_CASE",     # e.g. Introduction
            "title_page":       True,
            "running_head":     True,
        },
    },

    "mla": {
        "name": "MLA",
        "category": "Humanities",
        "layout": "single-column",
        "citation_type": "author-page",

        "journal":    "{authors}. \"{title}.\" {journal}, vol. {volume}, no. {number}, {year}, pp. {pages}.",
        "conference": "{authors}. \"{title}.\" {conference}, {year}, pp. {pages}.",
        "book":       "{authors}. {book_title}. {publisher}, {year}.",
        "website":    "{author}. \"{title}.\" {website}, {date}, {url}.",

        "in_text": "({author_last} {page})",

        "formatting": {
            "font_family":      "Times New Roman",
            "font_size_pt":     12,
            "line_spacing":     "double",
            "columns":          1,
            "margin_top_cm":    2.54,
            "margin_bottom_cm": 2.54,
            "margin_left_cm":   2.54,
            "margin_right_cm":  2.54,
            "heading_bold":     False,
            "indent_first_line_cm": 1.27,
            "works_cited_page": True,
            "section_style":    "TITLE_CASE",
        },
    },

    "chicago": {
        "name": "Chicago",
        "category": "Publishing",
        "layout": "single-column",
        "citation_type": "author-date",

        "journal":    "{authors}. \"{title}.\" {journal} {volume}, no. {number} ({year}): {pages}.",
        "conference": "{authors}. \"{title}.\" In {conference}, {pages}. {year}.",
        "book":       "{authors}. {book_title}. {city}: {publisher}, {year}.",
        "website":    "{author}. \"{title}.\" {website}. Accessed {date}. {url}.",

        "in_text": "({author_last} {year})",

        "formatting": {
            "font_family":      "Times New Roman",
            "font_size_pt":     12,
            "line_spacing":     "double",
            "columns":          1,
            "margin_top_cm":    2.54,
            "margin_bottom_cm": 2.54,
            "margin_left_cm":   3.81,
            "margin_right_cm":  2.54,
            "heading_bold":     True,
            "footnotes":        True,
            "bibliography":     True,
            "section_style":    "TITLE_CASE",
        },
    },

    "vancouver": {
        "name": "Vancouver",
        "category": "Medical",
        "layout": "single-column",
        "citation_type": "numbered",

        "journal":    "{index}. {authors}. {title}. {journal}. {year};{volume}({number}):{pages}.",
        "conference": "{index}. {authors}. {title}. In: {conference}; {year}. p. {pages}.",
        "book":       "{index}. {authors}. {book_title}. {city}: {publisher}; {year}.",
        "website":    "{index}. {author}. {title}. {website} [Internet]. {year} [cited {date}]. Available from: {url}",

        "in_text": "[{index}]",

        "formatting": {
            "font_family":      "Arial",
            "font_size_pt":     12,
            "line_spacing":     "double",
            "columns":          1,
            "margin_top_cm":    2.54,
            "margin_bottom_cm": 2.54,
            "margin_left_cm":   2.54,
            "margin_right_cm":  2.54,
            "heading_bold":     True,
            "section_style":    "TITLE_CASE",
        },
    },
}

# Map frontend card titles to style keys
STYLE_TITLE_MAP = {
    "APA 7th Edition":        "apa",
    "IEEE Standard":          "ieee",
    "MLA 9th Edition":        "mla",
    "Chicago Manual of Style": "chicago",
    "Nature Journal":         "vancouver",   # closest numbered/medical style
    "Vancouver":              "vancouver",
    "Custom Template":        "apa",         # default to APA for custom
}


def resolve_style_key(style: str) -> str:
    """Accept a style key (apa, ieee…) OR a card title and return the normalised key."""
    lower = style.strip().lower()
    if lower in CITATION_STYLES:
        return lower
    # Try title map (case-insensitive)
    for title, key in STYLE_TITLE_MAP.items():
        if title.lower() == lower:
            return key
    raise ValueError(f"Unknown citation style: '{style}'. "
                     f"Supported: {list(CITATION_STYLES.keys())} or card titles: {list(STYLE_TITLE_MAP.keys())}")


def generate_citation(style: str, source_type: str, data: dict) -> str:
    """
    Generate a formatted citation string.

    Args:
        style:       Style key (apa / ieee / mla / chicago / vancouver)
                     OR a frontend card title like 'APA 7th Edition'.
        source_type: journal | conference | book | website
        data:        Dict of template variables (authors, title, year, …)

    Returns:
        Formatted citation string.
    """
    key = resolve_style_key(style)
    style_data = CITATION_STYLES[key]
    template = style_data.get(source_type)
    if not template:
        raise ValueError(f"Source type '{source_type}' not supported for style '{style}'.")
    try:
        if callable(template):
            return template(data)
        return template.format_map(_SafeDict(data))
    except KeyError as e:
        raise ValueError(f"Missing citation field: {e}")


def get_formatting_rules(style: str) -> dict:
    """Return the document formatting rules for a given style."""
    key = resolve_style_key(style)
    info = CITATION_STYLES[key]
    return {
        "style_key":     key,
        "name":          info["name"],
        "category":      info["category"],
        "layout":        info["layout"],
        "citation_type": info["citation_type"],
        "in_text":       info["in_text"],
        "formatting":    info["formatting"],
    }


class _SafeDict(dict):
    """dict subclass that returns '{key}' for missing keys (safe format_map)."""
    def __missing__(self, key):
        return "{" + key + "}"


# ---------------------------------------------------------------------------
# Example / smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample_data = {
        "index": 1,
        "authors": "A. Kumar and B. Patel",
        "author": "A. Kumar",
        "author_last": "Kumar",
        "title": "Deep Learning for Sentiment Analysis",
        "journal": "IEEE Transactions on Neural Networks",
        "conference": "International Conference on AI",
        "book_title": "Deep Learning Applications",
        "volume": "34",
        "number": "2",
        "pages": "123-130",
        "publisher": "Springer",
        "city": "New York",
        "year": "2024",
        "website": "OpenAI Blog",
        "url": "https://openai.com",
        "date": "Mar 6, 2026",
        "page": "45",
    }

    for style_name in CITATION_STYLES:
        cite = generate_citation(style_name, "journal", sample_data)
        rules = get_formatting_rules(style_name)
        print(f"\n{'='*60}")
        print(f"Style : {rules['name']}  ({rules['category']})")
        print(f"Layout: {rules['layout']}  |  Font: {rules['formatting']['font_family']} {rules['formatting']['font_size_pt']}pt")
        print(f"Citation: {cite}")

    # Test card-title resolution
    print("\n--- Card title resolution ---")
    print(generate_citation("APA 7th Edition", "journal", sample_data))
    print(generate_citation("IEEE Standard",   "journal", sample_data))
