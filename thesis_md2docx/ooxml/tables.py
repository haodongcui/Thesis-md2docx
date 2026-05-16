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


def table_cell_xml(
    text: str,
    *,
    width: int,
    style: str,
    align: str,
    font_size: int,
    bold: bool = False,
    bottom_border: bool = False,
    top_border: bool = False,
    bottom_border_size: int = 8,
    top_border_size: int = 8,
    grid_span: int | None = None,
    vmerge: str | None = None,
    preserve_breaks: bool = False,
    math_converter: MathConverter | None = None,
    reference_anchors: dict[str, str] | None = None,
) -> str:
    p = paragraph_with_inline_math_xml(
        text,
        style=style,
        align=align,
        ppr_extra=spacing_xml(line=360, after=0),
        preserve_breaks=preserve_breaks,
        run_kwargs={"bold": bold, "size": font_size},
        math_converter=math_converter,
        reference_anchors=reference_anchors,
    )
    tc_pr_parts = ["<w:tcPr>", f'<w:tcW w:w="{width}" w:type="dxa"/>']
    tc_pr_parts.append('<w:vAlign w:val="center"/>')
    if grid_span and grid_span > 1:
        tc_pr_parts.append(f'<w:gridSpan w:val="{grid_span}"/>')
    if vmerge == "restart":
        tc_pr_parts.append('<w:vMerge w:val="restart"/>')
    elif vmerge == "continue":
        tc_pr_parts.append("<w:vMerge/>")
    if bottom_border or top_border:
        tc_pr_parts.append(
            "<w:tcBorders>"
        )
        if top_border:
            tc_pr_parts.append(f'<w:top w:val="single" w:sz="{top_border_size}" w:space="0" w:color="auto"/>')
        if bottom_border:
            tc_pr_parts.append(
                f'<w:bottom w:val="single" w:sz="{bottom_border_size}" w:space="0" w:color="auto"/>'
            )
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
    caption_bold = parse_bool_option(options, "caption_bold", default=True)
    header_bold = parse_bool_option(options, "header_bold", default=True)
    header_top_border = parse_bool_option(options, "header_top_border", default=True)
    cant_split = parse_bool_option(options, "cant_split", default=False)
    repeat_header_rows = parse_int_option(options, "repeat_header_rows")
    row_height = parse_int_option(options, "row_height")
    row_heights = parse_widths_option(options.get("row_heights") if options else None)
    row_height_rule = options.get("row_height_rule", "") if options else ""
    cant_split_rows = set(parse_widths_option(options.get("cant_split_rows") if options else None) or [])
    cell_margins = parse_widths_option(options.get("cell_margins") if options else None, expected_count=4)
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
        caption_cell = table_cell_xml(
            caption_text,
            width=sum(col_widths),
            style=cell_style,
            align="center",
            font_size=table_font_size,
            bold=caption_bold,
            bottom_border=True,
            bottom_border_size=top_border_size,
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
                style=cell_style,
                align="center",
                font_size=table_font_size,
                bold=True,
                vmerge="restart",
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
                    style=cell_style,
                    align="center",
                    font_size=table_font_size,
                    bold=True,
                    grid_span=span,
                    math_converter=math_converter,
                    reference_anchors=reference_anchors,
                )
            )
            col_offset += span
        top_cells.append(
            table_cell_xml(
                grouped_header["avg"],
                width=col_widths[-1],
                style=cell_style,
                align="center",
                font_size=table_font_size,
                bold=True,
                vmerge="restart",
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
                style=cell_style,
                align="center",
                font_size=table_font_size,
                vmerge="continue",
                bottom_border=True,
                bottom_border_size=mid_border_size,
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
                        style=cell_style,
                        align="center",
                        font_size=table_font_size,
                        bold=True,
                        bottom_border=True,
                        bottom_border_size=mid_border_size,
                        math_converter=math_converter,
                        reference_anchors=reference_anchors,
                    )
                )
                col_offset += 1
        second_cells.append(
            table_cell_xml(
                "",
                width=col_widths[-1],
                style=cell_style,
                align="center",
                font_size=table_font_size,
                vmerge="continue",
                bottom_border=True,
                bottom_border_size=mid_border_size,
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
        active_rowspans: dict[int, int] = {}
        for r_idx, row in enumerate(rows):
            cells = []
            col_idx = 0
            row_is_header = any(cell.header for cell in row) if has_header_flags else r_idx == 0

            def append_rowspan_continuations() -> None:
                nonlocal col_idx
                while col_idx in active_rowspans:
                    cells.append(
                        table_cell_xml(
                            "",
                            width=col_widths[col_idx],
                            style=cell_style,
                            align="center",
                            font_size=table_font_size,
                            vmerge="continue",
                            bottom_border=row_is_header,
                            bottom_border_size=mid_border_size,
                            math_converter=math_converter,
                            reference_anchors=reference_anchors,
                        )
                    )
                    remaining = active_rowspans[col_idx] - 1
                    if remaining <= 0:
                        del active_rowspans[col_idx]
                    else:
                        active_rowspans[col_idx] = remaining
                    col_idx += 1

            for cell in row:
                append_rowspan_continuations()
                cell_text = cell.text.strip()
                cell_is_header = cell.header if has_header_flags else r_idx == 0
                if cell_is_header:
                    display_text = " ".join(cell_text.split()) if plain_header_layout else format_table_header_text(cell_text)
                else:
                    display_text = cell_text
                span_width = sum(col_widths[col_idx : col_idx + cell.colspan])
                cells.append(
                    table_cell_xml(
                        display_text,
                        width=span_width,
                        style=cell_style,
                        align=cell.align or "center",
                        font_size=table_font_size,
                        bold=cell_is_header and header_bold,
                        bottom_border=cell_is_header,
                        top_border=cell_is_header and header_top_border and r_idx == 0 and not caption_text,
                        bottom_border_size=mid_border_size,
                        top_border_size=top_border_size,
                        grid_span=cell.colspan if cell.colspan > 1 else None,
                        vmerge="restart" if cell.rowspan > 1 else None,
                        preserve_breaks=cell_is_header and "\n" in display_text,
                        math_converter=math_converter,
                        reference_anchors=reference_anchors,
                    )
                )
                if cell.rowspan > 1:
                    active_rowspans[col_idx] = cell.rowspan - 1
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
                    style=cell_style,
                    align="center",
                    font_size=table_font_size,
                    bold=r_idx == 0 and not grouped_header,
                    bottom_border=r_idx == 0 and not grouped_header,
                    preserve_breaks=r_idx == 0 and not grouped_header and "\n" in display_text,
                    math_converter=math_converter,
                    reference_anchors=reference_anchors,
                )
            )
        row_output_idx = len(trs)
        repeated_header = row_output_idx < repeat_header_rows if repeat_header_rows is not None else False
        trs.append(f"<w:tr>{row_pr_xml(row_output_idx, header=repeated_header)}{''.join(cells)}</w:tr>")
    return f"<w:tbl>{tbl_pr}{tbl_grid}{''.join(trs)}</w:tbl>"
