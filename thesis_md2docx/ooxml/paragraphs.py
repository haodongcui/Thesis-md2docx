from __future__ import annotations

from ..constants import BODY_TEXT_CENTER_TWIPS, BODY_TEXT_WIDTH_TWIPS, INLINE_CITATION_PATTERN
from ..inline import split_inline_code, split_inline_math
from ..math.converter import MathConverter
from ..toc import TocEntry
from .text import citation_text_runs, inline_code_run_xml, text_runs
from .xml import (
    bookmark_end_xml,
    bookmark_start_xml,
    field_char_run_xml,
    indent_xml,
    instr_text_run_xml,
    run_text_xml,
    spacing_xml,
    tab_run_xml,
    xml_text,
)


def paragraph_with_inline_math_xml(
    text: str,
    *,
    style: str | None = None,
    align: str | None = None,
    ppr_extra: str = "",
    first_line_chars: int | None = None,
    first_line: int | None = None,
    left: int | None = None,
    preserve_breaks: bool = False,
    run_kwargs: dict[str, object] | None = None,
    math_converter: MathConverter | None = None,
    reference_anchors: dict[str, str] | None = None,
) -> str:
    code_segments = split_inline_code(text)
    has_code = any(kind == "code" for kind, _ in code_segments)
    has_math = any(
        kind == "math"
        for segment_kind, segment_text in code_segments
        if segment_kind == "text"
        for kind, _ in split_inline_math(segment_text)
    )
    has_citation = any(
        bool(reference_anchors) and bool(INLINE_CITATION_PATTERN.search(segment_text))
        for segment_kind, segment_text in code_segments
        if segment_kind == "text"
    )
    if not has_code and not has_math and not has_citation:
        return formatted_paragraph_xml(
            text,
            style=style,
            align=align,
            ppr_extra=ppr_extra,
            first_line_chars=first_line_chars,
            first_line=first_line,
            left=left,
            preserve_breaks=preserve_breaks,
            run_kwargs=run_kwargs,
        )

    run_kwargs = run_kwargs or {}
    runs: list[str] = []
    code_size = int(run_kwargs.get("size")) if run_kwargs.get("size") else None
    for segment_kind, segment_text in code_segments:
        if segment_kind == "code":
            runs.append(inline_code_run_xml(segment_text, size=code_size))
            continue
        for kind, value in split_inline_math(segment_text):
            if kind == "text":
                runs.extend(citation_text_runs(value, run_kwargs=run_kwargs, reference_anchors=reference_anchors))
                continue
            omml = math_converter.get(value, display_mode=False) if math_converter else None
            if omml:
                runs.append(omml)
            else:
                runs.append(run_text_xml(f"${value}$", **run_kwargs))

    return paragraph_xml(
        style=style,
        align=align,
        runs=runs,
        ppr_extra=ppr_extra,
        first_line_chars=first_line_chars,
        first_line=first_line,
        left=left,
    )


def math_paragraph_xml(
    latex: str,
    *,
    style: str | None = None,
    align: str | None = None,
    math_converter: MathConverter | None = None,
    equation_number: str | None = None,
) -> str:
    # Give display equations a bit more breathing room than normal body text and
    # disable document-grid snapping so taller formulas are not visually cramped.
    math_ppr_extra = '<w:snapToGrid w:val="0"/>' + spacing_xml(before=120, after=120, line=360)
    if equation_number:
        math_ppr_extra += (
            "<w:tabs>"
            f'<w:tab w:val="center" w:pos="{BODY_TEXT_CENTER_TWIPS}"/>'
            f'<w:tab w:val="right" w:pos="{BODY_TEXT_WIDTH_TWIPS}"/>'
            "</w:tabs>"
        )
        runs: list[str] = [tab_run_xml()]
        if math_converter:
            omml = math_converter.get(latex, display_mode=True)
            if omml:
                runs.append(omml)
            else:
                runs.append(run_text_xml(latex))
        else:
            runs.append(run_text_xml(latex))
        runs.append(tab_run_xml())
        runs.append(
            run_text_xml(
                equation_number,
                font_ascii="Times New Roman",
                font_hansi="Times New Roman",
                font_eastasia="宋体",
                size=24,
            )
        )
        return paragraph_xml(
            style=style,
            align=align,
            runs=runs,
            ppr_extra=math_ppr_extra,
            first_line_chars=0,
            first_line=0,
        )
    if math_converter:
        omml = math_converter.get(latex, display_mode=True)
        if omml:
            return paragraph_xml(style=style, align=align or "center", runs=[omml], ppr_extra=math_ppr_extra)
    return paragraph_xml(latex, style=style, align=align or "center", ppr_extra=math_ppr_extra)


def paragraph_xml(
    text: str | None = None,
    *,
    style: str | None = None,
    align: str | None = None,
    preserve_breaks: bool = False,
    runs: list[str] | None = None,
    ppr_extra: str = "",
    first_line_chars: int | None = None,
    first_line: int | None = None,
    left: int | None = None,
) -> str:
    ppr: list[str] = []
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    if align:
        ppr.append(f'<w:jc w:val="{align}"/>')
    indent = indent_xml(first_line_chars=first_line_chars, first_line=first_line, left=left)
    if indent:
        ppr.append(indent)
    if ppr_extra:
        ppr.append(ppr_extra)
    ppr_xml = f"<w:pPr>{''.join(ppr)}</w:pPr>" if ppr else ""

    if runs is None:
        value = text or ""
        if preserve_breaks and "\n" in value:
            body = "".join(text_runs(value, preserve_breaks=True))
        else:
            body = f"<w:r>{xml_text(value)}</w:r>"
    else:
        body = "".join(runs)
    return f"<w:p>{ppr_xml}{body}</w:p>"


def formatted_paragraph_xml(
    text: str,
    *,
    style: str | None = None,
    align: str | None = None,
    ppr_extra: str = "",
    first_line_chars: int | None = None,
    first_line: int | None = None,
    left: int | None = None,
    run_kwargs: dict[str, object] | None = None,
    preserve_breaks: bool = False,
) -> str:
    runs = text_runs(text, run_kwargs=run_kwargs, preserve_breaks=preserve_breaks)
    return paragraph_xml(
        style=style,
        align=align,
        runs=runs,
        ppr_extra=ppr_extra,
        first_line_chars=first_line_chars,
        first_line=first_line,
        left=left,
    )


def page_break_xml() -> str:
    spacer = spacing_xml(before=0, after=0, line=1, line_rule="exact")
    return f'<w:p><w:pPr>{spacer}</w:pPr><w:r><w:br w:type="page"/></w:r></w:p>'


def add_page_break_before_paragraph_xml(paragraph: str) -> str:
    if "<w:pPr>" in paragraph:
        return paragraph.replace("<w:pPr>", "<w:pPr><w:pageBreakBefore/>", 1)
    return paragraph.replace("<w:p>", "<w:p><w:pPr><w:pageBreakBefore/></w:pPr>", 1)


def section_break_paragraph_xml(sect_pr: str) -> str:
    spacer = spacing_xml(before=0, after=0, line=1, line_rule="exact")
    return f"<w:p><w:pPr>{spacer}{sect_pr}</w:pPr></w:p>"


def add_section_to_paragraph_xml(paragraph: str, sect_pr: str) -> str:
    if "</w:pPr>" in paragraph:
        return paragraph.replace("</w:pPr>", f"{sect_pr}</w:pPr>", 1)
    return paragraph.replace("<w:p>", f"<w:p><w:pPr>{sect_pr}</w:pPr>", 1)


def toc_field_paragraph_xml(*, style: str | None = None) -> str:
    runs = [
        field_char_run_xml("begin", dirty=True),
        instr_text_run_xml('TOC \\o "1-3" \\h \\u '),
        field_char_run_xml("separate"),
        run_text_xml(" ", size=24),
        field_char_run_xml("end"),
    ]
    return paragraph_xml(
        runs=runs,
        style=style,
        ppr_extra=spacing_xml(line=288),
    )


def bookmark_paragraph_xml(paragraph: str, *, bookmark_id: int, anchor: str) -> str:
    bookmark_start = bookmark_start_xml(bookmark_id, anchor)
    bookmark_end = bookmark_end_xml(bookmark_id)
    insert_at = paragraph.find("<w:r")
    if insert_at == -1:
        insert_at = paragraph.find("</w:p>")
    if insert_at == -1:
        return paragraph
    paragraph = paragraph[:insert_at] + bookmark_start + paragraph[insert_at:]
    close_at = paragraph.rfind("</w:p>")
    if close_at == -1:
        return paragraph
    return paragraph[:close_at] + bookmark_end + paragraph[close_at:]


def _toc_style_for_level(level: int, styles: dict[int, str] | None) -> str | None:
    if not styles:
        return None
    return styles.get(level)


def toc_cache_entry_paragraph_xml(
    entry: TocEntry,
    *,
    first: bool = False,
    close_field: bool = False,
    toc_field_style: str | None = None,
    toc_level_styles: dict[int, str] | None = None,
    tab_pos: int = 8303,
) -> str:
    style = _toc_style_for_level(entry.level, toc_level_styles)
    ppr_extra = (
        f'<w:tabs><w:tab w:val="right" w:leader="dot" w:pos="{tab_pos}"/></w:tabs>'
        + spacing_xml(line=288)
    )
    if entry.level == 2:
        ppr_extra += indent_xml(left=210)
    elif entry.level >= 3:
        ppr_extra += indent_xml(left=420)

    runs: list[str] = []
    if first:
        runs.append(field_char_run_xml("begin", dirty=True))
        runs.append(instr_text_run_xml('TOC \\o "1-3" \\h \\u '))
        runs.append(field_char_run_xml("separate"))

    runs.append(f'<w:hyperlink w:anchor="{entry.anchor}" w:history="1">')
    runs.extend(text_runs(entry.text))
    runs.append(tab_run_xml())
    runs.append(field_char_run_xml("begin"))
    runs.append(instr_text_run_xml(f" PAGEREF {entry.anchor} \\h "))
    runs.append(field_char_run_xml("separate"))
    runs.append(run_text_xml("1"))
    runs.append(field_char_run_xml("end"))
    runs.append("</w:hyperlink>")
    if close_field:
        runs.append(field_char_run_xml("end"))

    return paragraph_xml(
        style=style or toc_field_style,
        runs=runs,
        ppr_extra=ppr_extra,
    )


def toc_cache_end_paragraph_xml() -> str:
    return paragraph_xml(runs=[field_char_run_xml("end")], ppr_extra=spacing_xml(line=288))
