from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"w": W_NS, "wp": WP_NS, "a": A_NS, "r": R_NS}
W = f"{{{W_NS}}}"
R = f"{{{R_NS}}}"


@dataclass(frozen=True)
class RunSummary:
    text: str
    fonts: tuple[str | None, str | None, str | None, str | None, str | None]
    size: tuple[str | None, str | None]
    emphasis: tuple[bool, bool, bool, bool, str | None, str | None]
    position: tuple[str | None, str | None]
    color: str | None
    lang: tuple[str | None, str | None, str | None]


@dataclass(frozen=True)
class ParagraphSummary:
    index: int
    text: str
    style: str | None
    align: str | None
    spacing: tuple[str | None, str | None, str | None, str | None, str | None, str | None]
    indent: tuple[str | None, str | None, str | None, str | None]
    numbering: tuple[str | None, str | None]
    controls: tuple[str, ...]
    outline_level: str | None
    run: RunSummary | None


@dataclass(frozen=True)
class CellSummary:
    text: str
    width: tuple[str | None, str | None]
    grid_span: str | None
    vmerge: str | None
    valign: str | None
    margins: tuple[str | None, str | None, str | None, str | None]
    borders: tuple[tuple[str, str | None, str | None], ...]
    paragraph: tuple[str | None, str | None, tuple[str | None, ...], tuple[str | None, ...]]
    run: RunSummary | None


@dataclass(frozen=True)
class RowSummary:
    height: tuple[str | None, str | None]
    flags: tuple[str, ...]
    cells: tuple[CellSummary, ...]


@dataclass(frozen=True)
class TableSummary:
    index: int
    width: tuple[str | None, str | None]
    columns: tuple[str | None, ...]
    rows: tuple[RowSummary, ...]
    borders: tuple[tuple[str, str | None, str | None], ...]
    cell_margins: tuple[str | None, str | None, str | None, str | None]
    layout: str | None
    look: tuple[str | None, str | None, str | None, str | None, str | None] | None
    first_row: tuple[str, ...]


@dataclass(frozen=True)
class SectionSummary:
    index: int
    page_size: tuple[str | None, str | None, str | None]
    margins: tuple[str | None, str | None, str | None, str | None, str | None, str | None, str | None]
    columns: tuple[str | None, str | None]
    section_type: str | None
    headers: tuple[tuple[str | None, str | None], ...]
    footers: tuple[tuple[str | None, str | None], ...]


@dataclass(frozen=True)
class DrawingSummary:
    index: int
    paragraph_index: int
    kind: str
    extent: tuple[str | None, str | None]
    docpr: tuple[str | None, str | None, str | None]
    paragraph_text: str


@dataclass(frozen=True)
class FieldSummary:
    paragraph_index: int
    paragraph_text: str
    instr_texts: tuple[str, ...]
    field_chars: tuple[str | None, ...]


def _attr(element: ET.Element | None, name: str, *, namespace: str | None = W_NS) -> str | None:
    if element is None:
        return None
    if namespace is None:
        return element.get(name)
    return element.get(f"{{{namespace}}}{name}")


def _document_root(docx_path: Path) -> ET.Element:
    with ZipFile(docx_path) as zf:
        return ET.fromstring(zf.read("word/document.xml"))


def _text_of(element: ET.Element) -> str:
    return "".join(text.text or "" for text in element.findall(".//w:t", NS))


def _trim_text(text: str, limit: int = 80) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def _spacing_summary(ppr: ET.Element | None) -> tuple[str | None, str | None, str | None, str | None, str | None, str | None]:
    spacing = ppr.find("w:spacing", NS) if ppr is not None else None
    return (
        _attr(spacing, "before"),
        _attr(spacing, "beforeLines"),
        _attr(spacing, "after"),
        _attr(spacing, "afterLines"),
        _attr(spacing, "line"),
        _attr(spacing, "lineRule"),
    )


def _indent_summary(ppr: ET.Element | None) -> tuple[str | None, str | None, str | None, str | None]:
    indent = ppr.find("w:ind", NS) if ppr is not None else None
    return (
        _attr(indent, "left"),
        _attr(indent, "firstLine"),
        _attr(indent, "firstLineChars"),
        _attr(indent, "hanging"),
    )


def _numbering_summary(ppr: ET.Element | None) -> tuple[str | None, str | None]:
    num_pr = ppr.find("w:numPr", NS) if ppr is not None else None
    ilvl = num_pr.find("w:ilvl", NS) if num_pr is not None else None
    num_id = num_pr.find("w:numId", NS) if num_pr is not None else None
    return (_attr(ilvl, "val"), _attr(num_id, "val"))


def _paragraph_controls(ppr: ET.Element | None) -> tuple[str, ...]:
    if ppr is None:
        return ()
    controls: list[str] = []
    for name in ("keepNext", "keepLines", "pageBreakBefore", "widowControl", "suppressLineNumbers"):
        element = ppr.find(f"w:{name}", NS)
        if element is not None:
            value = _attr(element, "val")
            controls.append(name if value is None else f"{name}={value}")
    return tuple(controls)


def _border_summary(parent: ET.Element | None, child_name: str = "w:tblBorders") -> tuple[tuple[str, str | None, str | None], ...]:
    border_parent = parent.find(child_name, NS) if parent is not None else None
    if border_parent is None:
        return ()
    borders: list[tuple[str, str | None, str | None]] = []
    for name in ("top", "bottom", "left", "right", "insideH", "insideV"):
        border = border_parent.find(f"w:{name}", NS)
        borders.append((name, _attr(border, "val"), _attr(border, "sz")))
    return tuple(borders)


def _cell_margins(parent: ET.Element | None) -> tuple[str | None, str | None, str | None, str | None]:
    margins = parent.find("w:tblCellMar", NS) if parent is not None else None
    return tuple(
        _attr(margins.find(f"w:{name}", NS) if margins is not None else None, "w")
        for name in ("top", "right", "bottom", "left")
    )


def _tc_margins(tc_pr: ET.Element | None) -> tuple[str | None, str | None, str | None, str | None]:
    margins = tc_pr.find("w:tcMar", NS) if tc_pr is not None else None
    return tuple(
        _attr(margins.find(f"w:{name}", NS) if margins is not None else None, "w")
        for name in ("top", "right", "bottom", "left")
    )


def _run_summary(run: ET.Element) -> RunSummary:
    rpr = run.find("w:rPr", NS)
    fonts = rpr.find("w:rFonts", NS) if rpr is not None else None
    size = rpr.find("w:sz", NS) if rpr is not None else None
    size_cs = rpr.find("w:szCs", NS) if rpr is not None else None
    bold = rpr.find("w:b", NS) if rpr is not None else None
    bold_cs = rpr.find("w:bCs", NS) if rpr is not None else None
    italic = rpr.find("w:i", NS) if rpr is not None else None
    italic_cs = rpr.find("w:iCs", NS) if rpr is not None else None
    underline = rpr.find("w:u", NS) if rpr is not None else None
    vert_align = rpr.find("w:vertAlign", NS) if rpr is not None else None
    position = rpr.find("w:position", NS) if rpr is not None else None
    spacing = rpr.find("w:spacing", NS) if rpr is not None else None
    color = rpr.find("w:color", NS) if rpr is not None else None
    lang = rpr.find("w:lang", NS) if rpr is not None else None
    return RunSummary(
        text=_trim_text(_text_of(run), 60),
        fonts=(
            _attr(fonts, "ascii"),
            _attr(fonts, "hAnsi"),
            _attr(fonts, "eastAsia"),
            _attr(fonts, "cs"),
            _attr(fonts, "hint"),
        ),
        size=(_attr(size, "val"), _attr(size_cs, "val")),
        emphasis=(
            bold is not None and _attr(bold, "val") != "0",
            bold_cs is not None and _attr(bold_cs, "val") != "0",
            italic is not None and _attr(italic, "val") != "0",
            italic_cs is not None and _attr(italic_cs, "val") != "0",
            _attr(underline, "val"),
            _attr(vert_align, "val"),
        ),
        position=(_attr(position, "val"), _attr(spacing, "val")),
        color=_attr(color, "val"),
        lang=(_attr(lang, "val"), _attr(lang, "eastAsia"), _attr(lang, "bidi")),
    )


def _first_run_summary(element: ET.Element) -> RunSummary | None:
    for run in element.findall(".//w:r", NS):
        if _text_of(run).strip():
            return _run_summary(run)
    return None


def paragraph_summaries(docx_path: Path) -> list[ParagraphSummary]:
    root = _document_root(docx_path)
    summaries: list[ParagraphSummary] = []
    for index, paragraph in enumerate(root.findall(".//w:body/w:p", NS)):
        ppr = paragraph.find("w:pPr", NS)
        style = ppr.find("w:pStyle", NS) if ppr is not None else None
        align = ppr.find("w:jc", NS) if ppr is not None else None
        outline_level = ppr.find("w:outlineLvl", NS) if ppr is not None else None
        summaries.append(
            ParagraphSummary(
                index=index,
                text=_text_of(paragraph).strip(),
                style=_attr(style, "val"),
                align=_attr(align, "val"),
                spacing=_spacing_summary(ppr),
                indent=_indent_summary(ppr),
                numbering=_numbering_summary(ppr),
                controls=_paragraph_controls(ppr),
                outline_level=_attr(outline_level, "val"),
                run=_first_run_summary(paragraph),
            )
        )
    return summaries


def _cell_summary(cell: ET.Element) -> CellSummary:
    tc_pr = cell.find("w:tcPr", NS)
    width = tc_pr.find("w:tcW", NS) if tc_pr is not None else None
    grid_span = tc_pr.find("w:gridSpan", NS) if tc_pr is not None else None
    vmerge = tc_pr.find("w:vMerge", NS) if tc_pr is not None else None
    valign = tc_pr.find("w:vAlign", NS) if tc_pr is not None else None
    paragraph = cell.find("w:p", NS)
    ppr = paragraph.find("w:pPr", NS) if paragraph is not None else None
    pstyle = ppr.find("w:pStyle", NS) if ppr is not None else None
    align = ppr.find("w:jc", NS) if ppr is not None else None
    return CellSummary(
        text=_trim_text(_text_of(cell)),
        width=(_attr(width, "w"), _attr(width, "type")),
        grid_span=_attr(grid_span, "val"),
        vmerge=_attr(vmerge, "val") if vmerge is not None else None,
        valign=_attr(valign, "val"),
        margins=_tc_margins(tc_pr),
        borders=_border_summary(tc_pr, "w:tcBorders"),
        paragraph=(_attr(pstyle, "val"), _attr(align, "val"), _spacing_summary(ppr), _indent_summary(ppr)),
        run=_first_run_summary(cell),
    )


def _row_summary(row: ET.Element) -> RowSummary:
    tr_pr = row.find("w:trPr", NS)
    height = tr_pr.find("w:trHeight", NS) if tr_pr is not None else None
    flags: list[str] = []
    for name in ("cantSplit", "tblHeader"):
        element = tr_pr.find(f"w:{name}", NS) if tr_pr is not None else None
        if element is not None:
            value = _attr(element, "val")
            flags.append(name if value is None else f"{name}={value}")
    return RowSummary(
        height=(_attr(height, "val"), _attr(height, "hRule")),
        flags=tuple(flags),
        cells=tuple(_cell_summary(cell) for cell in row.findall("w:tc", NS)),
    )


def table_summaries(docx_path: Path) -> list[TableSummary]:
    root = _document_root(docx_path)
    summaries: list[TableSummary] = []
    for index, table in enumerate(root.findall(".//w:body/w:tbl", NS), start=1):
        tbl_pr = table.find("w:tblPr", NS)
        tbl_width = tbl_pr.find("w:tblW", NS) if tbl_pr is not None else None
        grid = table.find("w:tblGrid", NS)
        rows = tuple(_row_summary(row) for row in table.findall("w:tr", NS))
        first_row = rows[0] if rows else None
        tbl_layout = tbl_pr.find("w:tblLayout", NS) if tbl_pr is not None else None
        tbl_look = tbl_pr.find("w:tblLook", NS) if tbl_pr is not None else None
        summaries.append(
            TableSummary(
                index=index,
                width=(_attr(tbl_width, "w"), _attr(tbl_width, "type")),
                columns=tuple(_attr(column, "w") for column in grid.findall("w:gridCol", NS)) if grid is not None else (),
                rows=rows,
                borders=_border_summary(tbl_pr),
                cell_margins=_cell_margins(tbl_pr),
                layout=_attr(tbl_layout, "type"),
                look=(
                    _attr(tbl_look, "firstRow"),
                    _attr(tbl_look, "lastRow"),
                    _attr(tbl_look, "firstColumn"),
                    _attr(tbl_look, "lastColumn"),
                    _attr(tbl_look, "val"),
                )
                if tbl_look is not None
                else None,
                first_row=tuple(cell.text for cell in first_row.cells) if first_row is not None else (),
            )
        )
    return summaries


def section_summaries(docx_path: Path) -> list[SectionSummary]:
    root = _document_root(docx_path)
    summaries: list[SectionSummary] = []
    for index, sect_pr in enumerate(root.findall(".//w:sectPr", NS), start=1):
        page_size = sect_pr.find("w:pgSz", NS)
        page_margins = sect_pr.find("w:pgMar", NS)
        columns = sect_pr.find("w:cols", NS)
        section_type = sect_pr.find("w:type", NS)
        summaries.append(
            SectionSummary(
                index=index,
                page_size=(_attr(page_size, "w"), _attr(page_size, "h"), _attr(page_size, "orient")),
                margins=(
                    _attr(page_margins, "top"),
                    _attr(page_margins, "right"),
                    _attr(page_margins, "bottom"),
                    _attr(page_margins, "left"),
                    _attr(page_margins, "header"),
                    _attr(page_margins, "footer"),
                    _attr(page_margins, "gutter"),
                ),
                columns=(_attr(columns, "num"), _attr(columns, "space")),
                section_type=_attr(section_type, "val"),
                headers=tuple(
                    (_attr(header, "type"), _attr(header, "id", namespace=R_NS))
                    for header in sect_pr.findall("w:headerReference", NS)
                ),
                footers=tuple(
                    (_attr(footer, "type"), _attr(footer, "id", namespace=R_NS))
                    for footer in sect_pr.findall("w:footerReference", NS)
                ),
            )
        )
    return summaries


def drawing_summaries(docx_path: Path) -> list[DrawingSummary]:
    root = _document_root(docx_path)
    summaries: list[DrawingSummary] = []
    for paragraph_index, paragraph in enumerate(root.findall(".//w:body/w:p", NS)):
        paragraph_text = _trim_text(_text_of(paragraph))
        for drawing in paragraph.findall(".//w:drawing", NS):
            inline = drawing.find("wp:inline", NS)
            anchor = drawing.find("wp:anchor", NS)
            container = inline if inline is not None else anchor
            if container is None:
                continue
            extent = container.find("wp:extent", NS)
            docpr = container.find("wp:docPr", NS)
            summaries.append(
                DrawingSummary(
                    index=len(summaries) + 1,
                    paragraph_index=paragraph_index,
                    kind="anchor" if anchor is not None else "inline",
                    extent=(_attr(extent, "cx", namespace=None), _attr(extent, "cy", namespace=None)),
                    docpr=(
                        _attr(docpr, "id", namespace=None),
                        _attr(docpr, "name", namespace=None),
                        _attr(docpr, "descr", namespace=None),
                    ),
                    paragraph_text=paragraph_text,
                )
            )
    return summaries


def field_summaries(docx_path: Path) -> list[FieldSummary]:
    root = _document_root(docx_path)
    summaries: list[FieldSummary] = []
    for paragraph_index, paragraph in enumerate(root.findall(".//w:body/w:p", NS)):
        instr_texts = tuple((node.text or "").strip() for node in paragraph.findall(".//w:instrText", NS))
        field_chars = tuple(_attr(node, "fldCharType") for node in paragraph.findall(".//w:fldChar", NS))
        if instr_texts or field_chars:
            summaries.append(
                FieldSummary(
                    paragraph_index=paragraph_index,
                    paragraph_text=_trim_text(_text_of(paragraph)),
                    instr_texts=tuple(text for text in instr_texts if text),
                    field_chars=field_chars,
                )
            )
    return summaries


def _first_match(paragraphs: list[ParagraphSummary], query: str) -> ParagraphSummary | None:
    for paragraph in paragraphs:
        if paragraph.text == query:
            return paragraph
    for paragraph in paragraphs:
        if query in paragraph.text:
            return paragraph
    return None


def _table_signature(table: TableSummary) -> str:
    nonempty = [cell for cell in table.first_row if cell.strip()]
    if nonempty:
        return "|".join(nonempty)
    return f"#{table.index}"


def _table_core(table: TableSummary) -> tuple[object, ...]:
    return (
        table.width,
        table.columns,
        len(table.rows),
        table.borders,
        table.cell_margins,
        table.layout,
        table.look,
        table.first_row,
    )


def _table_detail(table: TableSummary) -> tuple[RowSummary, ...]:
    return table.rows


def _match_tables(reference_tables: list[TableSummary], candidate_tables: list[TableSummary]) -> list[tuple[TableSummary, TableSummary | None]]:
    unmatched = list(candidate_tables)
    matches: list[tuple[TableSummary, TableSummary | None]] = []
    for ref in reference_tables:
        signature = _table_signature(ref)
        found_idx = next((idx for idx, candidate in enumerate(unmatched) if _table_signature(candidate) == signature), None)
        if found_idx is None:
            found_idx = ref.index - 1 if ref.index - 1 < len(unmatched) else None
        if found_idx is None:
            matches.append((ref, None))
            continue
        matches.append((ref, unmatched.pop(found_idx)))
    return matches


def _status(reference: object, candidate: object) -> str:
    return "same" if reference == candidate else "different"


def _format_section(section: SectionSummary) -> str:
    return (
        f"page={section.page_size}, margins={section.margins}, columns={section.columns}, "
        f"type={section.section_type}, headers={section.headers}, footers={section.footers}"
    )


def _format_paragraph(paragraph: ParagraphSummary) -> str:
    return (
        f"index={paragraph.index}, style={paragraph.style}, align={paragraph.align}, "
        f"spacing={paragraph.spacing}, indent={paragraph.indent}, numbering={paragraph.numbering}, "
        f"controls={paragraph.controls}, outline={paragraph.outline_level}, run={paragraph.run}"
    )


def _format_table(table: TableSummary) -> str:
    row_brief = tuple((row.height, row.flags, len(row.cells)) for row in table.rows[:3])
    first_cells = tuple(table.rows[0].cells[: min(4, len(table.rows[0].cells))]) if table.rows else ()
    return (
        f"width={table.width}, cols={table.columns}, rows={len(table.rows)}, borders={table.borders}, "
        f"cell_margins={table.cell_margins}, layout={table.layout}, look={table.look}, "
        f"first={table.first_row}, first_row_cells={first_cells}, row_brief={row_brief}"
    )


def compare_docx(reference: Path, candidate: Path, *, queries: list[str]) -> str:
    ref_sections = section_summaries(reference)
    candidate_sections = section_summaries(candidate)
    ref_paragraphs = paragraph_summaries(reference)
    candidate_paragraphs = paragraph_summaries(candidate)
    ref_tables = table_summaries(reference)
    candidate_tables = table_summaries(candidate)
    ref_drawings = drawing_summaries(reference)
    candidate_drawings = drawing_summaries(candidate)
    ref_fields = field_summaries(reference)
    candidate_fields = field_summaries(candidate)

    lines: list[str] = []
    lines.append("# DOCX Format Audit")
    lines.append("")
    lines.append(f"- Reference: `{reference}`")
    lines.append(f"- Candidate: `{candidate}`")
    lines.append(f"- Sections: reference={len(ref_sections)}, candidate={len(candidate_sections)}")
    lines.append(f"- Paragraphs: reference={len(ref_paragraphs)}, candidate={len(candidate_paragraphs)}")
    lines.append(f"- Tables: reference={len(ref_tables)}, candidate={len(candidate_tables)}")
    lines.append(f"- Drawings: reference={len(ref_drawings)}, candidate={len(candidate_drawings)}")
    lines.append(f"- Fields: reference={len(ref_fields)}, candidate={len(candidate_fields)}")
    lines.append("")

    lines.append("## Section Checks")
    max_sections = max(len(ref_sections), len(candidate_sections))
    for idx in range(max_sections):
        ref = ref_sections[idx] if idx < len(ref_sections) else None
        cand = candidate_sections[idx] if idx < len(candidate_sections) else None
        lines.append(f"### Section {idx + 1}")
        lines.append(f"- reference: {_format_section(ref) if ref else None}")
        lines.append(f"- candidate: {_format_section(cand) if cand else None}")
        lines.append(f"- status: {_status(ref, cand)}")
    lines.append("")

    lines.append("## Paragraph Checks")
    for query in queries:
        ref = _first_match(ref_paragraphs, query)
        cand = _first_match(candidate_paragraphs, query)
        lines.append(f"### {query}")
        if ref is None or cand is None:
            lines.append(f"- missing: reference={ref is None}, candidate={cand is None}")
            continue
        lines.append(f"- reference {_format_paragraph(ref)}")
        lines.append(f"- candidate {_format_paragraph(cand)}")
        lines.append(
            f"- status: {_status((ref.align, ref.spacing, ref.indent, ref.numbering, ref.controls, ref.outline_level, ref.run), (cand.align, cand.spacing, cand.indent, cand.numbering, cand.controls, cand.outline_level, cand.run))}"
        )
    lines.append("")

    lines.append("## Table Checks")
    matched_tables = _match_tables(ref_tables, candidate_tables)
    matched_candidate_indexes = {candidate.index for _, candidate in matched_tables if candidate is not None}
    for idx, (ref, cand) in enumerate(matched_tables, start=1):
        lines.append(f"### Table {idx}: {_table_signature(ref)}")
        if cand is None:
            lines.append("- missing: candidate=True")
            continue
        lines.append(f"- reference {_format_table(ref)}")
        lines.append(f"- candidate table={cand.index}, {_format_table(cand)}")
        lines.append(f"- core status: {_status(_table_core(ref), _table_core(cand))}")
        lines.append(f"- detail status: {_status(_table_detail(ref), _table_detail(cand))}")
    for candidate_table in candidate_tables:
        if candidate_table.index not in matched_candidate_indexes:
            lines.append(f"### Candidate-only Table {candidate_table.index}: {_table_signature(candidate_table)}")
            lines.append(f"- candidate {_format_table(candidate_table)}")
    lines.append("")

    lines.append("## Drawing Checks")
    for idx in range(max(len(ref_drawings), len(candidate_drawings))):
        ref = ref_drawings[idx] if idx < len(ref_drawings) else None
        cand = candidate_drawings[idx] if idx < len(candidate_drawings) else None
        lines.append(f"- #{idx + 1}: reference={ref}, candidate={cand}, status={_status(ref, cand)}")
    lines.append("")

    lines.append("## Field Checks")
    lines.append(f"- reference: {ref_fields}")
    lines.append(f"- candidate: {candidate_fields}")
    lines.append(f"- status: {_status(ref_fields, candidate_fields)}")
    lines.append("")
    return "\n".join(lines)


def add_compare_docx_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("compare-docx", help="compare key DOCX layout properties")
    parser.add_argument("reference", type=Path, help="Reference DOCX path.")
    parser.add_argument("candidate", type=Path, help="Candidate DOCX path.")
    parser.add_argument(
        "--query",
        action="append",
        default=None,
        help="Paragraph text fragment to compare. Can be repeated.",
    )
    parser.add_argument("--out", type=Path, default=None, help="Write audit markdown report to this path.")


def run_compare_docx(args: argparse.Namespace) -> int:
    queries = args.query or ["新疆大学本科毕业论文", "摘  要", "ABSTRACT", "目  录", "绪论", "参考文献", "致  谢", "附"]
    report = compare_docx(args.reference, args.candidate, queries=queries)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
        print(f"DOCX audit written to: {args.out}")
    else:
        print(report)
    return 0
