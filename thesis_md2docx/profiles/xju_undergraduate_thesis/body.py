from __future__ import annotations

import re
from typing import Mapping
from xml.sax.saxutils import escape

from ...body_rules import BodyParseRules
from ...ooxml.parts import native_sect_pr_xml
from ...ooxml.render import (
    image_paragraph_xml,
    paragraph_with_inline_math_xml,
    paragraph_xml,
    reference_bookmark_id,
    reference_bookmark_name,
    text_runs,
)
from ...ooxml.tables import table_xml
from ...ooxml.xml import indent_xml, run_text_xml, spacing_xml
from ...styles import BodyRenderProfile, BodyStyleRefs, ParagraphFormatSpec, RunFormatSpec, StyleRole
from ...table_utils import parse_bool_option, parse_int_option
from .styles import STYLE_FIGURE_IMAGE, STYLE_HEADING_1, STYLE_REFERENCE, xju_style_roles


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
BODY_BOLD_LABELS = frozenset({"图：", "表：", "公式："})
BODY_PLAIN_LABELS = frozenset({"范例：", "样例："})
BODY_LABEL_BOLD_RPR = '<w:rPr><w:b/><w:sz w:val="24"/></w:rPr>'
BODY_LABEL_SIZE_RPR = '<w:rPr><w:sz w:val="24"/></w:rPr>'
REFERENCE_LEFT_TWIPS = 206
REFERENCE_LEFT_CHARS = -94
REFERENCE_HANGING_TWIPS = 403
REFERENCE_PARAGRAPH_RPR = '<w:rPr><w:rFonts w:cs="Times New Roman"/></w:rPr>'
REFERENCE_PPR_EXTRA = (
    spacing_xml(line=360)
    + indent_xml(left_chars=REFERENCE_LEFT_CHARS, left=REFERENCE_LEFT_TWIPS, hanging=REFERENCE_HANGING_TWIPS)
    + REFERENCE_PARAGRAPH_RPR
)
REFERENCE_NOTE_PPR_EXTRA = indent_xml(
    left_chars=REFERENCE_LEFT_CHARS,
    left=REFERENCE_LEFT_TWIPS,
    hanging=REFERENCE_HANGING_TWIPS,
)


def body_parse_rules() -> BodyParseRules:
    return BodyParseRules(
        reference_heading="参考文献",
        acknowledgement_heading="致谢",
        acknowledgement_display_text="致  谢",
        appendix_heading="附录",
        appendix_display_text="附  录",
        appendix_formula_scope_prefix="附录",
        unnumbered_headings=frozenset({"参考文献", "致谢", "附录"}),
        toc_excluded_headings=frozenset({"附录"}),
        toc_exclude_appendix_children=True,
        no_section_break_headings=frozenset({"致谢"}),
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
        if text.strip() == "附  录":
            return paragraph_xml(
                runs=[run_text_xml(text.strip(), size=32, size_cs=32)],
                align="center",
                ppr_extra=spacing_xml(before_lines=200, before=480, after_lines=200, after=480),
            )
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


def chapter_section_break_paragraph_xml(sect_pr: str) -> str:
    return paragraph_xml(
        style=STYLE_HEADING_1,
        ppr_extra=spacing_xml(line=240) + indent_xml(left=0, first_line=0) + sect_pr,
    )


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


def figure_image_paragraph_xml(
    item,
    media_manager,
    *,
    alt_text: str = "",
    width_emu: int | None = None,
    height_emu: int | None = None,
    crop_top: int | None = None,
    crop_right: int | None = None,
    crop_bottom: int | None = None,
    crop_left: int | None = None,
    options: Mapping[str, str] | None = None,
) -> str:
    style = None
    align: str | None = "center"
    ppr_extra = spacing_xml(after=120)
    keep_next = True

    if options:
        style_text = options.get("p_style", options.get("paragraph_style", "")).strip()
        if style_text and style_text.lower() not in {"none", "omit"}:
            style = style_text

        align_text = options.get("align", options.get("jc", "")).strip().lower()
        if align_text in {"none", "omit"}:
            align = None
        elif align_text:
            align = align_text

        spacing_parts = spacing_xml(
            line=parse_int_option(options, "line"),
            before=parse_int_option(options, "before"),
            after=parse_int_option(options, "after"),
            before_lines=parse_int_option(options, "before_lines"),
            after_lines=parse_int_option(options, "after_lines"),
            line_rule=options.get("line_rule", "auto"),
        )
        if spacing_parts:
            ppr_extra = spacing_parts

        mark_style = options.get("mark_style", options.get("ppr_rstyle", "")).strip()
        if mark_style and mark_style.lower() not in {"none", "omit"}:
            ppr_extra += f'<w:rPr><w:rStyle w:val="{escape(mark_style)}"/></w:rPr>'

        if "keep_next" in options:
            keep_next = parse_bool_option(options, "keep_next", default=True)

    return image_paragraph_xml(
        item,
        media_manager,
        alt_text=alt_text,
        width_emu=width_emu,
        height_emu=height_emu,
        crop_top=crop_top,
        crop_right=crop_right,
        crop_bottom=crop_bottom,
        crop_left=crop_left,
        style=style,
        align=align,
        ppr_extra=ppr_extra,
        keep_next=keep_next,
        local_dpi=True,
        no_change_arrows=True,
    )


def reference_paragraph_xml(text: str, reference_anchors: dict[str, str] | None = None) -> str:
    run_kwargs = {
        "font_cs": "Times New Roman",
    }
    match = re.match(r"^\[(\d+)\]\s*(.*)$", text)
    if not match:
        return paragraph_with_inline_math_xml(
            text,
            ppr_extra=REFERENCE_NOTE_PPR_EXTRA,
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
        ppr_extra=REFERENCE_PPR_EXTRA,
    )


def special_body_paragraph_xml(
    text: str,
    *,
    math_converter=None,
    reference_anchors: dict[str, str] | None = None,
) -> str | None:
    stripped = text.strip()
    if stripped in BODY_BOLD_LABELS:
        label_indent = indent_xml(first_line=482) if stripped == "表：" else indent_xml(first_line_chars=200, first_line=482)
        return paragraph_with_inline_math_xml(
            stripped,
            ppr_extra=spacing_xml(line=360) + label_indent + BODY_LABEL_BOLD_RPR,
            run_kwargs={"size": 24, "bold": True, "bold_cs": False, "size_cs": False},
            math_converter=math_converter,
            reference_anchors=reference_anchors,
        )
    if stripped in BODY_PLAIN_LABELS:
        if stripped == "样例：":
            return paragraph_with_inline_math_xml(
                stripped,
                ppr_extra=spacing_xml(line=360) + indent_xml(first_line=480),
                math_converter=math_converter,
                reference_anchors=reference_anchors,
            )
        return paragraph_with_inline_math_xml(
            stripped,
            ppr_extra=spacing_xml(line=360) + indent_xml(first_line=480) + BODY_LABEL_SIZE_RPR,
            run_kwargs={"size": 24, "size_cs": False},
            math_converter=math_converter,
            reference_anchors=reference_anchors,
        )
    return None


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
            image=styles.require(StyleRole.BODY_IMAGE),
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
        code_paragraph=ParagraphFormatSpec(),
        strip_heading_numbers=True,
        heading_builder=heading_paragraph_xml,
        acknowledgement_heading_builder=acknowledgement_heading_paragraph_xml,
        caption_builder=caption_paragraph_xml,
        reference_builder=reference_paragraph_xml,
        special_paragraph_builder=special_body_paragraph_xml,
        image_builder=figure_image_paragraph_xml,
        table_builder=table_xml,
        appendix_heading_normalizer=normalize_appendix_heading,
        appendix_reference_normalizer=normalize_appendix_references,
        section_pr_builder=native_sect_pr_xml,
        chapter_section_break_builder=chapter_section_break_paragraph_xml,
    )
