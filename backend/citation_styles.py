"""
Citation styles definitions and formatting utilities.
Supports: IEEE, APA, MLA, Chicago, Vancouver
"""
import re
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

def format_apa_authors(raw_authors):
    if not raw_authors: return ""
    if isinstance(raw_authors, str):
        auth_list = re.split(r'\s+and\s+|,', raw_authors)
    else:
        auth_list = raw_authors
    
    formatted = []
    auth_list = [a.strip() for a in auth_list if a.strip()]
    
    for a in auth_list:
        parts = a.split()
        if not parts: continue
        surname = parts[-1]
        initials = " ".join(f"{p[0]}." for p in parts[:-1])
        formatted.append(f"{surname}, {initials}")
    
    if len(formatted) == 0: return ""
    if len(formatted) == 1: return formatted[0]
    if len(formatted) <= 20:
        return ", ".join(formatted[:-1]) + ", & " + formatted[-1]
    else:
        return ", ".join(formatted[:19]) + ", ... " + formatted[-1]

def apa_journal(d):
    # APA 7: Author, A. A. (Year). Title. Journal, Vol(No), pp-pp. DOI
    authors = format_apa_authors(d.get('authors'))
    year = d.get('year') or ''
    title = d.get('title') or ''
    journal = d.get('journal') or ''
    volume = d.get('volume') or ''
    number = d.get('number') or ''
    pages = d.get('pages') or ''
    doi = d.get('doi') or d.get('url') or ''
    
    if doi and not str(doi).startswith('http'):
        doi = 'https://doi.org/' + str(doi)
        
    cite = f"{authors} ({year}). {title}. _{journal}_"
    if volume:
        cite += f", _{volume}_"
        if number:
            cite += f"({number})"
    if pages:
        cite += f", {pages}."
    else:
        cite += "."
        
    if doi:
        cite += f" {doi}"
    
    return cite.strip()

def mla_journal(d):
    # MLA 9: Surname, First Mid, and First Mid Surname. "Title." Journal, vol. X, no. X, Year, pp. X-X.
    raw_authors = d.get('authors', '')
    if isinstance(raw_authors, str):
        auth_list = re.split(r'\s+and\s+|,', raw_authors)
    else:
        auth_list = raw_authors
    
    formatted = []
    auth_list = [a.strip() for a in auth_list if a.strip()]
    
    for i, a in enumerate(auth_list):
        if i == 0:
            parts = a.split()
            if parts:
                surname = parts[-1]
                given = " ".join(parts[:-1])
                formatted.append(f"{surname}, {given}")
        elif i == 1 and len(auth_list) == 2:
            formatted.append(f"and {a}")
        else:
            if len(auth_list) > 2:
                formatted = [formatted[0] + ", et al."]
                break
            else:
                formatted.append(f"and {a}")
    
    authors_str = " ".join(formatted) if len(auth_list) <= 2 else formatted[0]

    title = d.get('title') or ''
    journal = d.get('journal') or ''
    year = d.get('year') or ''
    volume = d.get('volume') or ''
    number = d.get('number') or ''
    pages = d.get('pages') or ''
    
    cite = f"{authors_str}. \"{title}.\" _{journal}_"
    if volume:
        cite += f", vol. {volume}"
    if number:
        cite += f", no. {number}"
    cite += f", {year}"
    if pages:
        cite += f", pp. {pages}."
    else:
        cite += "."
    return cite

def vancouver_journal(d):
    # Vancouver: Surname FM, Surname FM. Title. Journal. Year;Volume(Issue):Pages.
    def format_name(name):
        parts = name.strip().split()
        if not parts: return ""
        surname = parts[-1]
        initials = "".join(p[0].upper() for p in parts[:-1])
        return f"{surname} {initials}"

    raw_authors = d.get('authors', '')
    if isinstance(raw_authors, str):
        auth_list = re.split(r'\s+and\s+|,', raw_authors)
    else:
        auth_list = raw_authors
    
    formatted_authors = []
    for a in auth_list:
        if a.strip():
            formatted_authors.append(format_name(a.strip()))
    
    authors_str = ", ".join(formatted_authors)
    title = d.get('title') or ''
    journal = d.get('journal') or ''
    year = d.get('year') or ''
    volume = d.get('volume') or ''
    number = d.get('number') or ''
    pages = d.get('pages') or ''
    
    cite = f"{authors_str}. {title}. {journal}. {year}"
    if volume:
        cite += f";{volume}"
        if number:
            cite += f"({number})"
    if pages:
        cite += f":{pages}."
    else:
        cite += "."
    return cite

def chicago_journal(d):
    # Chicago Author-Date: Smith, John A., and Robert T. Lee. 2022. "Title." _Journal_ Volume (Issue): Pages.
    raw_authors = d.get('authors', '')
    if isinstance(raw_authors, str):
        auth_list = re.split(r'\s+and\s+|,', raw_authors)
    else:
        auth_list = raw_authors
    
    formatted_authors = []
    auth_list = [a.strip() for a in auth_list if a.strip()]
    
    for i, a in enumerate(auth_list):
        parts = a.split()
        if not parts: continue
        if i == 0:
            # First author: Last, First Mid
            surname = parts[-1]
            given = " ".join(parts[:-1])
            formatted_authors.append(f"{surname}, {given}")
        else:
            # Other authors: First Mid Last
            formatted_authors.append(a)
    
    if len(formatted_authors) > 1:
        if len(formatted_authors) == 2:
            authors_str = f"{formatted_authors[0]}, and {formatted_authors[1]}"
        else:
            authors_str = ", ".join(formatted_authors[:-1]) + ", and " + formatted_authors[-1]
    else:
        authors_str = formatted_authors[0] if formatted_authors else ""

    year = d.get('year') or ''
    title = d.get('title') or ''
    journal = d.get('journal') or ''
    volume = d.get('volume') or ''
    number = d.get('number') or ''
    pages = d.get('pages') or ''
    
    cite = f"{authors_str}. {year}. \"{title}.\" _{journal}_ {volume}"
    if number:
        cite += f" ({number})"
    if pages:
        cite += f": {pages}."
    else:
        cite += "."
    return cite


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

        "journal":    apa_journal,
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
            "running_head":     False,
        },
    },

    "mla": {
        "name": "MLA",
        "category": "Humanities",
        "layout": "single-column",
        "citation_type": "author-page",

        "journal":    mla_journal,
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
            "title_page":       False,
        },
    },

    "chicago": {
        "name": "Chicago",
        "category": "Publishing",
        "layout": "single-column",
        "citation_type": "author-date",

        "journal":    chicago_journal,
        "conference": "{authors}. {year}. \"{title}.\" In {conference}, {pages}.",
        "book":       "{authors}. {year}. {book_title}. {city}: {publisher}.",
        "website":    "{authors}. {year}. \"{title}.\" {website}. Access {date}. {url}.",

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

        "journal":    vancouver_journal,
        "conference": "{index}. {authors}. {title}. In: {conference}; {year}. p. {pages}.",
        "book":       "{index}. {authors}. {book_title}. {city}: {publisher}; {year}.",
        "website":    "{index}. {author}. {title}. {website} [Internet]. {year} [cited {date}]. Available from: {url}",

        "in_text": "({index})",

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
