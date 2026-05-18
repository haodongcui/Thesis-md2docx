from __future__ import annotations

from .images import figure_row_xml, image_paragraph_xml, image_run_xml, math_image_paragraph_xml
from .paragraphs import (
    add_page_break_before_paragraph_xml,
    add_section_to_paragraph_xml,
    bookmark_paragraph_xml,
    formatted_paragraph_xml,
    math_paragraph_xml,
    page_break_xml,
    paragraph_with_inline_math_xml,
    paragraph_xml,
    section_break_paragraph_xml,
    toc_cache_end_paragraph_xml,
    toc_cache_entry_paragraph_xml,
    toc_field_paragraph_xml,
)
from .tables import table_cell_xml, table_xml
from .text import (
    citation_text_runs,
    extract_reference_anchors,
    hyperlink_run_xml,
    inline_code_run_xml,
    reference_bookmark_id,
    reference_bookmark_name,
    text_runs,
)
