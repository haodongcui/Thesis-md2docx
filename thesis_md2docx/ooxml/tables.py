from __future__ import annotations

from typing import Mapping

from ..ir import TableCell
from ..math.converter import MathConverter
from ..table_utils import (
    choose_table_font_size,
    compute_grouped_metric_column_widths,
    compute_table_column_widths,
    expanded_column_count,
    format_table_header_text,
    parse_bool_option,
    parse_int_option,
    parse_grouped_step_header,
    parse_widths_option,
    table_rows_text,
)
from .paragraphs import paragraph_with_inline_math_xml
from .xml import spacing_xml


BorderSpec = tuple[str | None, int | None]


def _parse_border_specs(value: str | None) -> list[BorderSpec] | None:
    if not value:
        return None
    specs: list[BorderSpec] = []
    for raw_part in value.split(","):
        part = raw_part.strip().lower()
        if part in {"", "none", "omit"}:
            specs.append((None, None))
        elif part == "nil":
            specs.append(("nil", None))
        else:
            try:
                specs.append(("single", int(part)))
            except ValueError:
                specs.append((None, None))
    return specs


def _border_for_row(specs: list[BorderSpec] | None, row_idx: int) -> BorderSpec | None:
    if specs is None or row_idx >= len(specs):
        return None
    return specs[row_idx]


def table_cell_xml(
    text: str,
    *,
    width: int | str,
    width_type: str = "dxa",
    style: str | None,
    align: str,
    font_size: int | None,
    font_size_cs: int | bool | None = None,
    bold: bool = False,
    bottom_border: bool = False,
    top_border: bool = False,
    bottom_border_val: str | None = None,
    top_border_val: str | None = None,
    bottom_border_size: int = 8,
    top_border_size: int = 8,
    paragraph_after: int | None = 0,
    paragraph_left: int | None = None,
    paragraph_first_line: int | None = None,
    paragraph_first_line_chars: int | None = None,
    bold_cs: bool | None = None,
    grid_span: int | None = None,
    vmerge: str | None = None,
    preserve_breaks: bool = False,
    math_converter: MathConverter | None = None,
    reference_anchors: dict[str, str] | None = None,
) -> str:
    run_kwargs: dict[str, object] = {}
    if bold:
        run_kwargs["bold"] = True
    if bold_cs is not None:
        run_kwargs["bold_cs"] = bold_cs
    if font_size is not None:
        run_kwargs["size"] = font_size
    if font_size_cs is not None:
        run_kwargs["size_cs"] = font_size_cs
    p = paragraph_with_inline_math_xml(
        text,
        style=style,
        align=align,
        ppr_extra=spacing_xml(line=360, after=paragraph_after),
        left=paragraph_left,
        first_line=paragraph_first_line,
        first_line_chars=paragraph_first_line_chars,
        preserve_breaks=preserve_breaks,
        run_kwargs=run_kwargs,
        math_converter=math_converter,
        reference_anchors=reference_anchors,
    )
    tc_pr_parts = ["<w:tcPr>", f'<w:tcW w:w="{width}" w:type="{width_type}"/>']
    tc_pr_parts.append('<w:vAlign w:val="center"/>')
    if grid_span and grid_span > 1:
        tc_pr_parts.append(f'<w:gridSpan w:val="{grid_span}"/>')
    if vmerge == "restart":
        tc_pr_parts.append('<w:vMerge w:val="restart"/>')
    elif vmerge == "continue":
        tc_pr_parts.append("<w:vMerge/>")
    effective_top_val = top_border_val or ("single" if top_border else None)
    effective_bottom_val = bottom_border_val or ("single" if bottom_border else None)
    if effective_bottom_val or effective_top_val:
        tc_pr_parts.append(
            "<w:tcBorders>"
        )
        if effective_top_val:
            if effective_top_val == "single":
                tc_pr_parts.append(f'<w:top w:val="single" w:sz="{top_border_size}" w:space="0" w:color="auto"/>')
            else:
                tc_pr_parts.append(f'<w:top w:val="{effective_top_val}"/>')
        if effective_bottom_val:
            if effective_bottom_val == "single":
                tc_pr_parts.append(
                    f'<w:bottom w:val="single" w:sz="{bottom_border_size}" w:space="0" w:color="auto"/>'
                )
            else:
                tc_pr_parts.append(f'<w:bottom w:val="{effective_bottom_val}"/>')
        tc_pr_parts.append("</w:tcBorders>")
    tc_pr_parts.append("</w:tcPr>")
    return f"<w:tc>{''.join(tc_pr_parts)}{p}</w:tc>"


def table_xml(
    rows: list[list[TableCell]],
    cell_style: str | None = None,
    *,
    options: Mapping[str, str] | None = None,
    math_converter: MathConverter | None = None,
    reference_anchors: dict[str, str] | None = None,
) -> str:
    cell_style = cell_style or "TableText"
    text_rows = table_rows_text(rows)
    col_count = max(expanded_column_count(rows), 1)
    header_names = [text_rows[0][i].strip() if i < len(text_rows[0]) else "" for i in range(col_count)]
    grouped_header = parse_grouped_step_header(text_rows[0])
    col_widths = (
        compute_grouped_metric_column_widths(col_count)
        if grouped_header
        else compute_table_column_widths(rows, options=options)
    )
    table_font_size = choose_table_font_size(rows)
    top_border_size = parse_int_option(options, "top_border", 12) or 12
    mid_border_size = parse_int_option(options, "mid_border", 8) or 8
    bottom_border_size = parse_int_option(options, "bottom_border", 12) or 12
    table_width = options.get("width", "5000") if options else "5000"
    table_width_type = options.get("width_type", "pct") if options else "pct"
    table_layout = options.get("layout") if options and "layout" in options else ("fixed" if table_width_type == "dxa" else None)
    if table_layout in {"", "none", "omit"}:
        table_layout = None
    table_look = options.get("look", "04A0") if options is not None else "04A0"
    if table_look in {"", "none", "omit"}:
        table_look = None
    caption_text = options.get("caption", "").strip() if options else ""
    cell_style_option = options.get("cell_style") if options and "cell_style" in options else cell_style
    if cell_style_option in {"", "none", "omit"}:
        cell_style_option = None
    font_size_option = options.get("font_size", options.get("cell_font_size", "")) if options else ""
    if font_size_option in {"inherit", "none", "omit"}:
        cell_font_size = None
    elif font_size_option:
        cell_font_size = parse_int_option({"font_size": font_size_option}, "font_size", table_font_size)
    else:
        cell_font_size = table_font_size
    paragraph_after_option = options.get("paragraph_after", "") if options else ""
    paragraph_after = None if paragraph_after_option in {"inherit", "none", "omit"} else parse_int_option(options, "paragraph_after", 0)
    paragraph_left = parse_int_option(options, "paragraph_left")
    paragraph_first_line = parse_int_option(options, "paragraph_first_line")
    paragraph_first_line_chars = parse_int_option(options, "paragraph_first_line_chars")
    caption_bold = parse_bool_option(options, "caption_bold", default=True)
    header_bold = parse_bool_option(options, "header_bold", default=True)
    header_bold_cs = (
        parse_bool_option(options, "header_bold_cs")
        if options is not None and "header_bold_cs" in options
        else None
    )
    body_bold_cs = (
        parse_bool_option(options, "body_bold_cs")
        if options is not None and "body_bold_cs" in options
        else None
    )
    header_top_border = parse_bool_option(options, "header_top_border", default=True)
    header_top_border_size = parse_int_option(options, "header_top_border_size", 12) or 12
    rowspan_restart_bottom_border = parse_bool_option(options, "rowspan_restart_bottom_border", default=True)
    cant_split = parse_bool_option(options, "cant_split", default=False)
    repeat_header_rows = parse_int_option(options, "repeat_header_rows")
    row_height = parse_int_option(options, "row_height")
    row_heights = parse_widths_option(options.get("row_heights") if options else None)
    row_height_rule = options.get("row_height_rule", "") if options else ""
    cant_split_rows = set(parse_widths_option(options.get("cant_split_rows") if options else None) or [])
    cell_margins = parse_widths_option(options.get("cell_margins") if options else None, expected_count=4)
    cell_width_type = options.get("cell_width_type", "dxa") if options else "dxa"
    cell_widths = parse_widths_option(options.get("cell_widths") if options else None, expected_count=col_count)
    row_top_borders = _parse_border_specs(options.get("row_top_borders") if options else None)
    row_bottom_borders = _parse_border_specs(options.get("row_bottom_borders") if options else None)
    has_header_flags = any(cell.header for row in rows for cell in row)
    plain_header_layout = (
        (col_count == 7 and header_names[:2] == ["任务", "条件"])
        or (col_count == 3 and header_names[0] == "方法" and all("平均" in h for h in header_names[1:]))
    )
    tbl_pr_parts = [
        "<w:tblPr>",
        f'<w:tblW w:w="{table_width}" w:type="{table_width_type}"/>',
        '<w:jc w:val="center"/>',
    ]
    if cell_margins is not None:
        top, right, bottom, left = cell_margins
        tbl_pr_parts.extend(
            [
                "<w:tblCellMar>",
                f'<w:top w:w="{top}" w:type="dxa"/>',
                f'<w:right w:w="{right}" w:type="dxa"/>',
                f'<w:bottom w:w="{bottom}" w:type="dxa"/>',
                f'<w:left w:w="{left}" w:type="dxa"/>',
                "</w:tblCellMar>",
            ]
        )
    tbl_pr_parts.extend(
        [
            "<w:tblBorders>",
            f'<w:top w:val="single" w:sz="{top_border_size}" w:space="0" w:color="auto"/>',
            f'<w:bottom w:val="single" w:sz="{bottom_border_size}" w:space="0" w:color="auto"/>',
            "</w:tblBorders>",
        ]
    )
    if table_layout:
        tbl_pr_parts.append(f'<w:tblLayout w:type="{table_layout}"/>')
    if table_look:
        tbl_pr_parts.append(
            f'<w:tblLook w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:val="{table_look}"/>'
        )
    tbl_pr_parts.append("</w:tblPr>")
    tbl_pr = "".join(tbl_pr_parts)
    tbl_grid = "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{col_width}"/>' for col_width in col_widths) + "</w:tblGrid>"

    # Header rows repeat across page breaks; every row carries `cantSplit` so a
    # single row never splits mid-cell, while the table itself can still flow
    # across pages when it is too tall to fit.
    trs = []
    start_row_idx = 0

    def row_pr_xml(row_idx: int, *, header: bool = False, cant_split_row: bool | None = None) -> str:
        parts: list[str] = []
        height = row_heights[row_idx] if row_heights is not None and row_idx < len(row_heights) else row_height
        if height is not None:
            h_rule_attr = f' w:hRule="{row_height_rule}"' if row_height_rule else ""
            parts.append(f'<w:trHeight w:val="{height}"{h_rule_attr}/>')
        effective_cant_split = cant_split if cant_split_row is None else cant_split_row
        if effective_cant_split or row_idx + 1 in cant_split_rows:
            parts.append("<w:cantSplit/>")
        if header:
            parts.append("<w:tblHeader/>")
        return f"<w:trPr>{''.join(parts)}</w:trPr>" if parts else ""

    if caption_text:
        caption_row_idx = len(trs)
        caption_top = _border_for_row(row_top_borders, caption_row_idx)
        caption_bottom = _border_for_row(row_bottom_borders, caption_row_idx)
        caption_cell = table_cell_xml(
            caption_text,
            width=table_width,
            width_type=table_width_type,
            style=cell_style_option,
            align="center",
            font_size=cell_font_size,
            bold=caption_bold,
            top_border_val=caption_top[0] if caption_top else None,
            top_border_size=caption_top[1] or top_border_size if caption_top else top_border_size,
            bottom_border=True if caption_bottom is None else False,
            bottom_border_val=caption_bottom[0] if caption_bottom else None,
            bottom_border_size=caption_bottom[1] or top_border_size if caption_bottom else top_border_size,
            paragraph_after=paragraph_after,
            paragraph_left=None,
            paragraph_first_line=None,
            paragraph_first_line_chars=None,
            grid_span=col_count if col_count > 1 else None,
            math_converter=math_converter,
            reference_anchors=reference_anchors,
        )
        caption_header = repeat_header_rows is not None and caption_row_idx < repeat_header_rows
        trs.append(f"<w:tr>{row_pr_xml(caption_row_idx, header=caption_header)}{caption_cell}</w:tr>")

    if grouped_header:
        top_row_idx = len(trs)
        top_cells = [
            table_cell_xml(
                grouped_header["first"],
                width=col_widths[0],
                style=cell_style_option,
                align="center",
                font_size=cell_font_size,
                bold=True,
                bold_cs=header_bold_cs,
                vmerge="restart",
                paragraph_after=paragraph_after,
                paragraph_left=paragraph_left,
                paragraph_first_line=paragraph_first_line,
                paragraph_first_line_chars=paragraph_first_line_chars,
                math_converter=math_converter,
                reference_anchors=reference_anchors,
            )
        ]
        col_offset = 1
        for task_name, steps in grouped_header["groups"]:
            span = len(steps)
            top_cells.append(
                table_cell_xml(
                    task_name,
                    width=sum(col_widths[col_offset : col_offset + span]),
                    style=cell_style_option,
                    align="center",
                    font_size=cell_font_size,
                    bold=True,
                    bold_cs=header_bold_cs,
                    grid_span=span,
                    paragraph_after=paragraph_after,
                    paragraph_left=paragraph_left,
                    paragraph_first_line=paragraph_first_line,
                    paragraph_first_line_chars=paragraph_first_line_chars,
                    math_converter=math_converter,
                    reference_anchors=reference_anchors,
                )
            )
            col_offset += span
        top_cells.append(
            table_cell_xml(
                grouped_header["avg"],
                width=col_widths[-1],
                style=cell_style_option,
                align="center",
                font_size=cell_font_size,
                bold=True,
                bold_cs=header_bold_cs,
                vmerge="restart",
                paragraph_after=paragraph_after,
                paragraph_left=paragraph_left,
                paragraph_first_line=paragraph_first_line,
                paragraph_first_line_chars=paragraph_first_line_chars,
                math_converter=math_converter,
                reference_anchors=reference_anchors,
            )
        )
        top_header = repeat_header_rows is None or top_row_idx < repeat_header_rows
        trs.append(f"<w:tr>{row_pr_xml(top_row_idx, header=top_header, cant_split_row=cant_split)}{''.join(top_cells)}</w:tr>")

        second_row_idx = len(trs)
        second_cells = [
            table_cell_xml(
                "",
                width=col_widths[0],
                style=cell_style_option,
                align="center",
                font_size=cell_font_size,
                vmerge="continue",
                bottom_border=True,
                bottom_border_size=mid_border_size,
                paragraph_after=paragraph_after,
                paragraph_left=paragraph_left,
                paragraph_first_line=paragraph_first_line,
                paragraph_first_line_chars=paragraph_first_line_chars,
                math_converter=math_converter,
                reference_anchors=reference_anchors,
            )
        ]
        col_offset = 1
        for _, steps in grouped_header["groups"]:
            for step in steps:
                second_cells.append(
                    table_cell_xml(
                        f"k={step}",
                        width=col_widths[col_offset],
                        style=cell_style_option,
                        align="center",
                        font_size=cell_font_size,
                        bold=True,
                        bold_cs=header_bold_cs,
                        bottom_border=True,
                        bottom_border_size=mid_border_size,
                        paragraph_after=paragraph_after,
                        paragraph_left=paragraph_left,
                        paragraph_first_line=paragraph_first_line,
                        paragraph_first_line_chars=paragraph_first_line_chars,
                        math_converter=math_converter,
                        reference_anchors=reference_anchors,
                    )
                )
                col_offset += 1
        second_cells.append(
            table_cell_xml(
                "",
                width=col_widths[-1],
                style=cell_style_option,
                align="center",
                font_size=cell_font_size,
                vmerge="continue",
                bottom_border=True,
                bottom_border_size=mid_border_size,
                paragraph_after=paragraph_after,
                paragraph_left=paragraph_left,
                paragraph_first_line=paragraph_first_line,
                paragraph_first_line_chars=paragraph_first_line_chars,
                math_converter=math_converter,
                reference_anchors=reference_anchors,
            )
        )
        second_header = repeat_header_rows is None or second_row_idx < repeat_header_rows
        trs.append(
            f"<w:tr>{row_pr_xml(second_row_idx, header=second_header, cant_split_row=cant_split)}{''.join(second_cells)}</w:tr>"
        )
        start_row_idx = 1

    if not grouped_header:
        active_rowspans: dict[int, tuple[int, TableCell]] = {}
        for r_idx, row in enumerate(rows):
            cells = []
            col_idx = 0
            row_is_header = any(cell.header for cell in row) if has_header_flags else r_idx == 0

            def append_rowspan_continuations() -> None:
                nonlocal col_idx
                while col_idx in active_rowspans:
                    remaining_count, source_cell = active_rowspans[col_idx]
                    row_output_idx = len(trs)
                    row_bottom = _border_for_row(row_bottom_borders, row_output_idx)
                    cells.append(
                        table_cell_xml(
                            "",
                            width=col_widths[col_idx],
                            style=cell_style_option,
                            align="center",
                            font_size=cell_font_size,
                            vmerge="continue",
                            bottom_border=row_is_header if row_bottom is None else False,
                            bottom_border_val=row_bottom[0] if row_bottom else None,
                            bottom_border_size=(row_bottom[1] if row_bottom and row_bottom[1] is not None else mid_border_size),
                            paragraph_after=paragraph_after,
                            paragraph_left=source_cell.continue_left
                            if source_cell.continue_left is not None
                            else source_cell.left
                            if source_cell.left is not None
                            else paragraph_left,
                            paragraph_first_line=source_cell.continue_first_line
                            if source_cell.continue_first_line is not None
                            else source_cell.first_line
                            if source_cell.first_line is not None
                            else paragraph_first_line,
                            paragraph_first_line_chars=source_cell.continue_first_line_chars
                            if source_cell.continue_first_line_chars is not None
                            else source_cell.first_line_chars
                            if source_cell.first_line_chars is not None
                            else paragraph_first_line_chars,
                            math_converter=math_converter,
                            reference_anchors=reference_anchors,
                        )
                    )
                    remaining = remaining_count - 1
                    if remaining <= 0:
                        del active_rowspans[col_idx]
                    else:
                        active_rowspans[col_idx] = (remaining, source_cell)
                    col_idx += 1

            for cell in row:
                append_rowspan_continuations()
                cell_text = cell.text.strip()
                cell_is_header = cell.header if has_header_flags else r_idx == 0
                row_output_idx = len(trs)
                row_top = _border_for_row(row_top_borders, row_output_idx)
                row_bottom = _border_for_row(row_bottom_borders, row_output_idx)
                if cell_is_header:
                    display_text = " ".join(cell_text.split()) if plain_header_layout else format_table_header_text(cell_text)
                else:
                    display_text = cell_text
                if cell.bold_cs is not None:
                    cell_bold_cs = cell.bold_cs
                elif cell_is_header:
                    cell_bold_cs = header_bold_cs
                else:
                    cell_bold_cs = body_bold_cs
                effective_cell_style = cell.style if cell.style is not None else cell_style_option
                effective_cell_font_size = cell.font_size if cell.font_size is not None else cell_font_size
                cell_first_line = (
                    None
                    if cell.omit_first_line
                    else cell.first_line
                    if cell.first_line is not None
                    else paragraph_first_line
                )
                span_widths = cell_widths if cell_widths is not None else col_widths
                span_width = sum(span_widths[col_idx : col_idx + cell.colspan])
                cells.append(
                    # A vertically merged cell often carries its visible
                    # separator on the final merge row rather than the restart
                    # cell, matching how Word templates commonly encode
                    # complex multi-row headers.
                    table_cell_xml(
                        display_text,
                        width=span_width,
                        width_type=cell_width_type,
                        style=effective_cell_style,
                        align=cell.align or "center",
                        font_size=effective_cell_font_size,
                        font_size_cs=cell.font_size_cs,
                        bold=cell_is_header and header_bold,
                        bold_cs=cell_bold_cs,
                        bottom_border=cell_is_header and (cell.rowspan <= 1 or rowspan_restart_bottom_border)
                        if row_bottom is None
                        else False,
                        top_border=cell_is_header and header_top_border and r_idx == 0 and not caption_text if row_top is None else False,
                        bottom_border_val=row_bottom[0]
                        if row_bottom and (cell.rowspan <= 1 or rowspan_restart_bottom_border)
                        else None,
                        top_border_val=row_top[0] if row_top else None,
                        bottom_border_size=(row_bottom[1] if row_bottom and row_bottom[1] is not None else mid_border_size),
                        top_border_size=(row_top[1] if row_top and row_top[1] is not None else header_top_border_size),
                        paragraph_after=paragraph_after,
                        paragraph_left=cell.left if cell.left is not None else paragraph_left,
                        paragraph_first_line=cell_first_line,
                        paragraph_first_line_chars=cell.first_line_chars
                        if cell.first_line_chars is not None
                        else paragraph_first_line_chars,
                        grid_span=cell.colspan if cell.colspan > 1 else None,
                        vmerge="restart" if cell.rowspan > 1 else None,
                        preserve_breaks=cell_is_header and "\n" in display_text,
                        math_converter=math_converter,
                        reference_anchors=reference_anchors,
                    )
                )
                if cell.rowspan > 1:
                    active_rowspans[col_idx] = (cell.rowspan - 1, cell)
                col_idx += max(1, cell.colspan)
            append_rowspan_continuations()
            row_output_idx = len(trs)
            repeated_header = (
                row_output_idx < repeat_header_rows if repeat_header_rows is not None else row_is_header
            )
            trs.append(f"<w:tr>{row_pr_xml(row_output_idx, header=repeated_header)}{''.join(cells)}</w:tr>")
        return f"<w:tbl>{tbl_pr}{tbl_grid}{''.join(trs)}</w:tbl>"

    for r_idx, row in enumerate(text_rows[start_row_idx:], start=start_row_idx):
        cells = []
        for col_idx, cell in enumerate(row):
            cell_text = cell.strip()
            if r_idx == 0 and not grouped_header:
                display_text = " ".join(cell_text.split()) if plain_header_layout else format_table_header_text(cell_text)
            else:
                display_text = cell_text
            cells.append(
                table_cell_xml(
                    display_text,
                    width=col_widths[col_idx],
                    width_type=cell_width_type,
                    style=cell_style_option,
                    align="center",
                    font_size=cell_font_size,
                    bold=r_idx == 0 and not grouped_header,
                    bottom_border=r_idx == 0 and not grouped_header,
                    paragraph_after=paragraph_after,
                    paragraph_left=paragraph_left,
                    paragraph_first_line=paragraph_first_line,
                    paragraph_first_line_chars=paragraph_first_line_chars,
                    preserve_breaks=r_idx == 0 and not grouped_header and "\n" in display_text,
                    math_converter=math_converter,
                    reference_anchors=reference_anchors,
                )
            )
        row_output_idx = len(trs)
        repeated_header = row_output_idx < repeat_header_rows if repeat_header_rows is not None else False
        trs.append(f"<w:tr>{row_pr_xml(row_output_idx, header=repeated_header)}{''.join(cells)}</w:tr>")
    return f"<w:tbl>{tbl_pr}{tbl_grid}{''.join(trs)}</w:tbl>"
