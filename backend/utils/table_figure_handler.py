"""
table_figure_handler.py
━━━━━━━━━━━━━━━━━━━━━━
Convert extracted tables and figures to LaTeX format for IEEE documents.

Handles:
  - Pipe-separated text tables → LaTeX tabular environment
  - Table captions and numbering
  - Figure references and captions
  - Integration with ieee_latex_generator
"""
import re
from typing import List, Tuple, Optional


def parse_pipe_table(table_text: str) -> List[List[str]]:
    """
    Parse a pipe-separated table format into a 2D list.
    
    Input format:
        Header1 | Header2 | Header3
        Row1Col1 | Row1Col2 | Row1Col3
        Row2Col1 | Row2Col2 | Row2Col3
    
    Returns:
        List[List[str]] where each inner list is a row
    """
    rows = []
    for line in table_text.strip().split('\n'):
        line = line.strip()
        if line:
            cells = [cell.strip() for cell in line.split('|')]
            rows.append(cells)
    return rows


def rows_to_latex_table(rows: List[List[str]], caption: str = "", label: str = "") -> str:
    r"""
    Convert 2D list of row data to LaTeX table environment.
    
    Args:
        rows: List of rows, each row is list of cells
        caption: Table caption text
        label: LaTeX label for \label{} command
    
    Returns:
        Complete LaTeX table environment as string
    """
    if not rows or not rows[0]:
        return ""
    
    num_cols = len(rows[0])
    
    # Escape special LaTeX characters in cells
    def escape_cell(text):
        text = str(text).replace('\\', r'\textbackslash{}')
        text = text.replace('&', r'\&')
        text = text.replace('%', r'\%')
        text = text.replace('$', r'\$')
        text = text.replace('#', r'\#')
        text = text.replace('_', r'\_')
        text = text.replace('{', r'\{')
        text = text.replace('}', r'\}')
        text = text.replace('~', r'\textasciitilde{}')
        text = text.replace('^', r'\textasciicircum{}')
        return text
    
    lines: List[str] = []
    lines.append(r"\begin{table}[!h]")
    lines.append(r"\centering")
    
    # Generate caption and label
    if caption:
        lines.append(f"\\caption{{{escape_cell(caption)}}}")
    
    if label:
        safe_label = label.lower()
        safe_label = re.sub(r'[^a-z0-9_:\-]', '', safe_label)
        lines.append(f"\\label{{tab:{safe_label}}}")
    
    # Table environment with proper column specs
    col_spec = 'l' * num_cols  # left-aligned by default
    lines.append(f"\\begin{{tabular}}{{|{col_spec}|}}")
    lines.append(r"\hline")
    
    # Write rows
    for i, row in enumerate(rows):
        # Pad row to match column count
        while len(row) < num_cols:
            row.append("")
        
        escaped_cells = [escape_cell(cell) for cell in row[:num_cols]]
        line = " & ".join(escaped_cells)
        lines.append(f"{line} \\\\")
        
        # Add horizontal line after header (first row)
        if i == 0:
            lines.append(r"\hline")
    
    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")
    lines.append("")
    
    return "\n".join(lines)


def extract_table_caption_and_content(table_section_content: str) -> Tuple[str, List[List[str]]]:
    """
    Extract caption and table data from a [Table] section.
    
    Expects format:
        [optional caption line]
        table_row_1
        table_row_2
        ...
    
    Returns:
        (caption: str, rows: List[List[str]])
    """
    lines = table_section_content.strip().split('\n')
    
    if not lines:
        return ("", [])
    
    # First line might be caption (no pipe) or table data
    caption = ""
    table_lines = []
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        if '|' in line_stripped:
            # This is table data
            table_lines = lines[i:]
            break
        elif line_stripped and not caption:
            # First non-pipe line is caption
            caption = line_stripped
    
    if not table_lines:
        # No pipe found, might all be captions or plain text
        return ("\n".join(lines[:1]) if lines else "", [])
    
    table_text = "\n".join(table_lines)
    rows = parse_pipe_table(table_text)
    
    return (caption, rows)


def text_table_to_latex(table_section_content: str, table_number: int = 1) -> str:
    """
    Convert a complete [Table] section to LaTeX table environment.
    
    Args:
        table_section_content: Full content from a [Table] section
        table_number: Numeric ID for table numbering (Table I, Table II, etc.)
    
    Returns:
        Complete LaTeX table environment
    """
    caption, rows = extract_table_caption_and_content(table_section_content)
    
    if not rows:
        return ""
    
    # Use Roman numerals for table numbering (IEEE style)
    roman_num = _int_to_roman(table_number)
    full_caption = f"Table {roman_num}" + (f": {caption}" if caption else "")
    
    label = f"table_{table_number}"
    
    return rows_to_latex_table(rows, caption=full_caption, label=label)


def _int_to_roman(num: int) -> str:
    """Convert integer to Roman numerals (1→I, 2→II, etc.)."""
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
    ]
    syms = [
        "M", "CM", "D", "CD",
        "C", "XC", "L", "XL",
        "X", "IX", "V", "IV",
        "I"
    ]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syms[i]
            num -= val[i]
        i += 1
    return roman_num


def create_figure_reference(caption: str, figure_number: int = 1, image_path: Optional[str] = None) -> str:
    """
    Create a LaTeX figure environment with caption.
    
    Args:
        caption: Figure caption text
        figure_number: Numeric ID for figure numbering
        image_path: Optional path to image file (relative to tex file)
    
    Returns:
        LaTeX figure environment as string
    """
    roman_num = _int_to_roman(figure_number)
    
    lines: List[str] = []
    lines.append(r"\begin{figure}[!h]")
    lines.append(r"\centering")
    
    if image_path:
        # Escape backslashes in path for LaTeX
        safe_path = image_path.replace('\\', '/')
        lines.append(f"\\includegraphics[width=0.9\\columnwidth]{{{safe_path}}}")
    else:
        # Placeholder for missing image
        lines.append(r"\fbox{\parbox{0.9\columnwidth}{\centering") 
        lines.append(r"[Image not embedded]")
        lines.append(r"}}")
    
    lines.append("")
    safe_caption = caption.replace('$', r'\$').replace('#', r'\#')
    lines.append(f"\\caption{{Fig. {roman_num}: {safe_caption}}}")
    lines.append(f"\\label{{fig:{figure_number}}}")
    lines.append(r"\end{figure}")
    lines.append("")
    
    return "\n".join(lines)


def detect_and_convert_tables(sections: List[dict]) -> Tuple[List[dict], int]:
    """
    Detection and convert all [Table] sections to LaTeX tables.
    
    Args:
        sections: List of section dicts from structure
    
    Returns:
        (updated_sections: List[dict], table_count: int)
    """
    updated_sections = []
    table_count = 0
    
    for section in sections:
        heading = section.get("heading", "").strip()
        
        if heading == "[Table]":
            table_count += 1
            content = section.get("content", "")
            latex_table = text_table_to_latex(content, table_count)
            
            # Replace content with LaTeX table
            updated_section = section.copy()
            updated_section["content"] = latex_table
            updated_section["is_table"] = True
            updated_sections.append(updated_section)
        else:
            updated_sections.append(section)
    
    return (updated_sections, table_count)


def detect_and_convert_figures(sections: List[dict], figure_data: Optional[List[dict]] = None) -> Tuple[List[dict], int]:
    """
    Detect and convert figure references to LaTeX figures.
    
    Args:
        sections: List of section dicts from structure
        figure_data: Optional list of figure dicts with 'caption', 'path' keys
    
    Returns:
        (updated_sections: List[dict], figure_count: int)
    """
    figure_count = 0
    updated_sections = []
    
    if not figure_data:
        figure_data = []
    
    for section in sections:
        heading = section.get("heading", "").strip()
        
        if heading == "[Figure]":
            figure_count += 1
            content = section.get("content", "")
            
            # Try to extract caption from content
            caption = content if content else f"Figure {figure_count}"
            
            # Look up figure data if available
            image_path = None
            if figure_count <= len(figure_data):
                fig_info = figure_data[figure_count - 1]
                caption = fig_info.get("caption", caption)
                image_path = fig_info.get("path")
            
            latex_figure = create_figure_reference(caption, figure_number=figure_count, image_path=image_path)
            
            updated_section = section.copy()
            updated_section["content"] = latex_figure
            updated_section["is_figure"] = True
            updated_sections.append(updated_section)
        else:
            updated_sections.append(section)
    
    return (updated_sections, figure_count)
