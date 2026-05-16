from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
W = f"{{{W_NS}}}"


@dataclass(frozen=True)
class ParagraphSummary:
    index: int
    text: str
    style: str | None
    align: str | None
    spacing: tuple[str | None, str | None, str | None, str | None, str | None, str | None]
    indent: tuple[str | None, str | None, str | None, str | None]
    run: tuple[str | None, str | None, str | None, str | None, str | None, bool]


@dataclass(frozen=True)
class TableSummary:
    index: int
    width: tuple[str | None, str | None]
    columns: tuple[str | None, ...]
    rows: int
    borders: tuple[tuple[str, str | None, str | None], ...]
    first_row: tuple[str, ...]


def _attr(element: ET.Element | None, name: str) -> str | None:
    if element is None:
        return None
    return element.get(W + name)


def _document_root(docx_path: Path) -> ET.Element:
    with ZipFile(docx_path) as zf:
        return ET.fromstring(zf.read("word/document.xml"))


def _text_of(element: ET.Element) -> str:
    return "".join(text.text or "" for text in element.findall(".//w:t", NS))


def _first_run_summary(paragraph: ET.Element) -> tuple[str | None, str | None, str | None, str | None, str | None, bool]:
    for run in paragraph.findall("w:r", NS):
        if not _text_of(run).strip():
            continue
        rpr = run.find("w:rPr", NS)
        if rpr is None:
            return (None, None, None, None, None, False)
        fonts = rpr.find("w:rFonts", NS)
        size = rpr.find("w:sz", NS)
        bold = rpr.find("w:b", NS)
        return (
            _attr(fonts, "ascii"),
            _attr(fonts, "hAnsi"),
            _attr(fonts, "eastAsia"),
            _attr(fonts, "cs"),
            _attr(size, "val"),
            bold is not None and _attr(bold, "val") != "0",
        )
    return (None, None, None, None, None, False)


def paragraph_summaries(docx_path: Path) -> list[ParagraphSummary]:
    root = _document_root(docx_path)
    summaries: list[ParagraphSummary] = []
    for index, paragraph in enumerate(root.findall(".//w:body/w:p", NS)):
        ppr = paragraph.find("w:pPr", NS)
        style = ppr.find("w:pStyle", NS) if ppr is not None else None
        align = ppr.find("w:jc", NS) if ppr is not None else None
        spacing = ppr.find("w:spacing", NS) if ppr is not None else None
        indent = ppr.find("w:ind", NS) if ppr is not None else None
        summaries.append(
            ParagraphSummary(
                index=index,
                text=_text_of(paragraph).strip(),
                style=_attr(style, "val"),
                align=_attr(align, "val"),
                spacing=(
                    _attr(spacing, "before"),
                    _attr(spacing, "beforeLines"),
                    _attr(spacing, "after"),
                    _attr(spacing, "afterLines"),
                    _attr(spacing, "line"),
                    _attr(spacing, "lineRule"),
                ),
                indent=(
                    _attr(indent, "left"),
                    _attr(indent, "firstLine"),
                    _attr(indent, "firstLineChars"),
                    _attr(indent, "hanging"),
                ),
                run=_first_run_summary(paragraph),
            )
        )
    return summaries


def table_summaries(docx_path: Path) -> list[TableSummary]:
    root = _document_root(docx_path)
    summaries: list[TableSummary] = []
    for index, table in enumerate(root.findall(".//w:body/w:tbl", NS), start=1):
        tbl_pr = table.find("w:tblPr", NS)
        tbl_width = tbl_pr.find("w:tblW", NS) if tbl_pr is not None else None
        tbl_borders = tbl_pr.find("w:tblBorders", NS) if tbl_pr is not None else None
        borders: list[tuple[str, str | None, str | None]] = []
        if tbl_borders is not None:
            for name in ("top", "bottom", "left", "right", "insideH", "insideV"):
                border = tbl_borders.find(f"w:{name}", NS)
                borders.append((name, _attr(border, "val"), _attr(border, "sz")))
        grid = table.find("w:tblGrid", NS)
        rows = table.findall("w:tr", NS)
        first_row = rows[0] if rows else None
        summaries.append(
            TableSummary(
                index=index,
                width=(_attr(tbl_width, "w"), _attr(tbl_width, "type")),
                columns=tuple(_attr(column, "w") for column in grid.findall("w:gridCol", NS)) if grid is not None else (),
                rows=len(rows),
                borders=tuple(borders),
                first_row=tuple(_text_of(cell).strip() for cell in first_row.findall("w:tc", NS))
                if first_row is not None
                else (),
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


def compare_docx(reference: Path, candidate: Path, *, queries: list[str]) -> str:
    ref_paragraphs = paragraph_summaries(reference)
    candidate_paragraphs = paragraph_summaries(candidate)
    ref_tables = table_summaries(reference)
    candidate_tables = table_summaries(candidate)
    lines: list[str] = []
    lines.append(f"# DOCX Format Audit")
    lines.append("")
    lines.append(f"- Reference: `{reference}`")
    lines.append(f"- Candidate: `{candidate}`")
    lines.append(f"- Paragraphs: reference={len(ref_paragraphs)}, candidate={len(candidate_paragraphs)}")
    lines.append(f"- Tables: reference={len(ref_tables)}, candidate={len(candidate_tables)}")
    lines.append("")
    lines.append("## Paragraph Checks")
    for query in queries:
        ref = _first_match(ref_paragraphs, query)
        cand = _first_match(candidate_paragraphs, query)
        lines.append(f"### {query}")
        if ref is None or cand is None:
            lines.append(f"- missing: reference={ref is None}, candidate={cand is None}")
            continue
        lines.append(f"- reference index={ref.index}, style={ref.style}, align={ref.align}, spacing={ref.spacing}, indent={ref.indent}, run={ref.run}")
        lines.append(
            f"- candidate index={cand.index}, style={cand.style}, align={cand.align}, spacing={cand.spacing}, indent={cand.indent}, run={cand.run}"
        )
        if (ref.align, ref.spacing, ref.indent, ref.run) != (cand.align, cand.spacing, cand.indent, cand.run):
            lines.append("- status: different")
        else:
            lines.append("- status: same")
    lines.append("")
    lines.append("## Table Checks")
    matched_tables = _match_tables(ref_tables, candidate_tables)
    matched_candidate_indexes = {candidate.index for _, candidate in matched_tables if candidate is not None}
    for idx, (ref, cand) in enumerate(matched_tables, start=1):
        lines.append(f"### Table {idx}: {_table_signature(ref)}")
        if cand is None:
            lines.append("- missing: candidate=True")
            continue
        lines.append(f"- reference width={ref.width}, cols={ref.columns}, rows={ref.rows}, borders={ref.borders}, first={ref.first_row}")
        lines.append(
            f"- candidate table={cand.index}, width={cand.width}, cols={cand.columns}, rows={cand.rows}, borders={cand.borders}, first={cand.first_row}"
        )
        if (ref.width, ref.columns, ref.rows, ref.borders, ref.first_row) != (
            cand.width,
            cand.columns,
            cand.rows,
            cand.borders,
            cand.first_row,
        ):
            lines.append("- status: different")
        else:
            lines.append("- status: same")
    for candidate in candidate_tables:
        if candidate.index not in matched_candidate_indexes:
            lines.append(f"### Candidate-only Table {candidate.index}: {_table_signature(candidate)}")
            lines.append(
                f"- candidate width={candidate.width}, cols={candidate.columns}, rows={candidate.rows}, borders={candidate.borders}, first={candidate.first_row}"
            )
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
