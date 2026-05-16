from __future__ import annotations

import re
from xml.sax.saxutils import escape

from ...body_rules import BodyParseRules
from ...ooxml.parts import native_sect_pr_xml
from ...ooxml.render import (
    paragraph_with_inline_math_xml,
    paragraph_xml,
    reference_bookmark_id,
    reference_bookmark_name,
    text_runs,
)
from ...ooxml.tables import table_xml
from ...ooxml.xml import indent_xml, run_text_xml, spacing_xml
from ...styles import BodyRenderProfile, BodyStyleRefs, ParagraphFormatSpec, RunFormatSpec, StyleRole
from .styles import STYLE_REFERENCE, xju_style_roles


FIGURE_ROW_START_PATTERN = re.compile(r"^:::\s*figure-row\s*$")
FIGURE_ROW_END_PATTERN = re.compile(r"^:::\s*$")
TABLE_SPLIT_COMMENT_PATTERN = re.compile(
    r"^<!--\s*thesis-table-split\s*:\s*(?P<spec>\d+(?:\s*,\s*\d+)*)\s*-->\s*$"
)
CAPTION_PATTERN = re.compile(
    r"^[图表]\s*(?:附录\d+-)?(?:[A-Z]|\d+)(?:[-.]\d+)*(?:\([a-zA-Z]\))?\s+"
)
CHAPTER_NUMBER_PATTERN = re.compile(r"^(\d+)\b")
REFERENCE_ENTRY_PATTERN = re.compile(r"^\[\d+\]")


def body_parse_rules() -> BodyParseRules:
    return BodyParseRules(
        reference_heading="参考文献",
        acknowledgement_heading="致谢",
        acknowledgement_display_text="致  谢",
        appendix_heading="附录",
        appendix_display_text="附  录",
        appendix_formula_scope_prefix="附录",
        unnumbered_headings=frozenset({"参考文献", "致谢", "附录"}),
        skip_reference_paragraph_prefixes=("说明：",),
        reference_entry_pattern=REFERENCE_ENTRY_PATTERN,
        caption_pattern=CAPTION_PATTERN,
        table_caption_prefixes=("表",),
        table_split_pattern=TABLE_SPLIT_COMMENT_PATTERN,
        figure_row_start_pattern=FIGURE_ROW_START_PATTERN,
        figure_row_end_pattern=FIGURE_ROW_END_PATTERN,
        chapter_number_pattern=CHAPTER_NUMBER_PATTERN,
    )


def normalize_appendix_heading(text: str, appendix_index: int) -> str:
    cleaned = re.sub(r"^附录\s*[A-Z0-9]+\s*", "", text).strip()
    if cleaned:
        return f"附录{appendix_index} {cleaned}"
    return f"附录{appendix_index}"


def normalize_appendix_references(text: str, appendix_index: int) -> str:
    def replace_heading(match: re.Match[str]) -> str:
        prefix = match.group(1)
        item_no = match.group(2)
        return f"{prefix} 附录{appendix_index}-{item_no}"

    return re.sub(r"([图表])\s*[A-Z]-(\d+)", replace_heading, text)


def strip_heading_prefix(text: str) -> str:
    stripped = re.sub(r"^\d+(?:\.\d+)*\s+", "", text).strip()
    return stripped or text.strip()


def heading_paragraph_xml(
    text: str,
    level: int,
    profile: BodyRenderProfile,
    *,
    numbered: bool = True,
    keep_with_next: bool = True,
) -> str:
    if level == 1:
        style = profile.styles.heading1
    elif level == 2:
        style = profile.styles.heading2
    else:
        style = profile.styles.heading3

    if numbered:
        heading_text = strip_heading_prefix(text) if profile.strip_heading_numbers else text.strip()
        if level == 2:
            ppr_extra = (
                ("<w:keepNext/><w:keepLines/>" if keep_with_next else "")
                + spacing_xml(before=240, after=120, line=360)
                + indent_xml(left=0, first_line=0)
            )
            return paragraph_xml(heading_text, style=style, align="left", ppr_extra=ppr_extra)
        if level == 1:
            ppr_extra = spacing_xml(line=240) + indent_xml(left=0, first_line=0)
        else:
            ppr_extra = (
                ("<w:keepNext/><w:keepLines/>" if keep_with_next else "")
                + spacing_xml(before=120, line=360)
                + indent_xml(left=0, first_line_chars=200, first_line=560)
            )
            return paragraph_xml(heading_text, style=style, align="left", ppr_extra=ppr_extra)
        return paragraph_xml(heading_text, style=style, ppr_extra=ppr_extra)

    ppr_extra = '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>'
    if level == 1:
        ppr_extra += spacing_xml(line=240)
    elif level == 3:
        ppr_extra += (
            ("<w:keepNext/><w:keepLines/>" if keep_with_next else "")
            + spacing_xml(before=120, line=360)
            + indent_xml(left=0, first_line_chars=200, first_line=560)
        )
        return paragraph_xml(text.strip(), style=style, align="left", ppr_extra=ppr_extra)
    return paragraph_xml(text.strip(), style=style, ppr_extra=ppr_extra)


def acknowledgement_heading_paragraph_xml(text: str, profile: BodyRenderProfile) -> str:
    style = profile.styles.heading1
    ppr_extra = (
        '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>'
        '<w:snapToGrid w:val="0"/>'
        + spacing_xml(line=240)
    )
    return paragraph_xml(text.strip(), style=style, ppr_extra=ppr_extra)


def caption_paragraph_xml(
    text: str,
    *,
    style: str | None = None,
    english: bool = False,
    math_converter=None,
    reference_anchors: dict[str, str] | None = None,
    keep_next: bool = False,
) -> str:
    run_kwargs = {
        "font_ascii": "Times New Roman",
        "font_hansi": "Times New Roman",
        "font_eastasia": "Times New Roman" if english else "宋体",
        "size": 21,
        "bold": True,
    }
    ppr_extra = spacing_xml(line=360, before=120, after=120) + indent_xml(left=0, first_line=0)
    if keep_next:
        ppr_extra += "<w:keepNext/>"
    return paragraph_with_inline_math_xml(
        text,
        style=style,
        align="center",
        ppr_extra=ppr_extra,
        run_kwargs=run_kwargs,
        math_converter=math_converter,
        reference_anchors=reference_anchors,
    )


def reference_paragraph_xml(text: str, reference_anchors: dict[str, str] | None = None) -> str:
    run_kwargs = {
        "font_ascii": "Times New Roman",
        "font_hansi": "Times New Roman",
        "font_eastasia": "宋体",
        "size": 21,
    }
    match = re.match(r"^\[(\d+)\]\s*(.*)$", text)
    if not match:
        return paragraph_with_inline_math_xml(
            text,
            style=STYLE_REFERENCE,
            ppr_extra=spacing_xml(line=360) + indent_xml(left=420, hanging=420),
            run_kwargs=run_kwargs,
            reference_anchors=reference_anchors,
        )

    ref_id, rest = match.groups()
    anchor = reference_anchors.get(ref_id, reference_bookmark_name(ref_id)) if reference_anchors else reference_bookmark_name(ref_id)
    bookmark_id = reference_bookmark_id(ref_id)
    runs = [
        f'<w:bookmarkStart w:id="{bookmark_id}" w:name="{escape(anchor)}"/>',
        run_text_xml(f"[{ref_id}] ", **run_kwargs),
        f'<w:bookmarkEnd w:id="{bookmark_id}"/>',
    ]
    if rest:
        runs.extend(text_runs(rest, run_kwargs=run_kwargs))
    return paragraph_xml(
        style=STYLE_REFERENCE,
        runs=runs,
        ppr_extra=spacing_xml(line=360) + indent_xml(left=420, hanging=420),
    )


def body_style_profile() -> BodyRenderProfile:
    styles = xju_style_roles()
    return BodyRenderProfile(
        styles=BodyStyleRefs(
            title=styles.require(StyleRole.BODY_TITLE),
            heading1=styles.require(StyleRole.BODY_HEADING_LEVEL1),
            heading2=styles.require(StyleRole.BODY_HEADING_LEVEL2),
            heading3=styles.require(StyleRole.BODY_HEADING_LEVEL3),
            normal=styles.require(StyleRole.BODY_NORMAL),
            quote=styles.require(StyleRole.QUOTE_BLOCK),
            code=styles.require(StyleRole.CODE_BLOCK),
            math=styles.require(StyleRole.MATH_BLOCK),
            table_cell=styles.require(StyleRole.TABLE_CELL),
            caption=styles.require(StyleRole.CAPTION_DEFAULT),
        ),
        normal_paragraph=ParagraphFormatSpec(
            ppr_extra='<w:widowControl w:val="0"/>' + spacing_xml(line=360),
            first_line_chars=200,
            first_line=480,
        ),
        normal_run=RunFormatSpec(
            font_ascii="Times New Roman",
            font_hansi="Times New Roman",
            font_eastasia="宋体",
            size=24,
        ),
        code_paragraph=ParagraphFormatSpec(ppr_extra='<w:outlineLvl w:val="9"/>'),
        strip_heading_numbers=True,
        heading_builder=heading_paragraph_xml,
        acknowledgement_heading_builder=acknowledgement_heading_paragraph_xml,
        caption_builder=caption_paragraph_xml,
        reference_builder=reference_paragraph_xml,
        table_builder=table_xml,
        appendix_heading_normalizer=normalize_appendix_heading,
        appendix_reference_normalizer=normalize_appendix_references,
        section_pr_builder=native_sect_pr_xml,
    )
