from __future__ import annotations

import re

from .body_rules import BodyParseRules
from .constants import IMAGE_PATTERN
from .ir import (
    BlankBlock,
    Block,
    CodeBlock,
    FigureRowBlock,
    HeadingBlock,
    ImageBlock,
    MathBlock,
    PageBreakBlock,
    ParagraphBlock,
    QuoteBlock,
    TableBlock,
    TableCell,
    TableSplitBlock,
)
from .markdown import join_soft_wrapped_lines
from .table_utils import is_table_separator, parse_bool_option, parse_int_option, parse_table_options, parse_table_row


RICH_TABLE_START_PATTERN = re.compile(r"^:::\s*table(?:\s*\{(?P<attrs>.*)\})?\s*$")
RICH_TABLE_END_PATTERN = re.compile(r"^:::\s*$")
IMAGE_ATTR_PATTERN = re.compile(
    r"^!\[(?P<alt>[^\]]*)\]\((?P<target>[^)]+)\)(?:\s*\{(?P<attrs>[^{}]*)\})?$"
)
MATH_START_PATTERN = re.compile(r"^\$\$(?:\s*\{(?P<attrs>[^{}]*)\})?\s*$")
PARAGRAPH_ATTR_PATTERN = re.compile(
    r"^<!--\s*thesis-(?:paragraph|p)\s*:\s*(?P<attrs>.*?)\s*-->\s*$"
)
BLANK_PATTERN = re.compile(r"^<!--\s*thesis-blank(?:\s*:\s*(?P<attrs>.*?))?\s*-->\s*$")


def _table_cells_from_line(line: str, *, header: bool = False) -> tuple[TableCell, ...]:
    return tuple(
        TableCell(
            text=cell.text,
            colspan=cell.colspan,
            rowspan=cell.rowspan,
            header=cell.header or header,
            align=cell.align,
            left=cell.left,
            first_line=cell.first_line,
            first_line_chars=cell.first_line_chars,
            continue_left=cell.continue_left,
            continue_first_line=cell.continue_first_line,
            continue_first_line_chars=cell.continue_first_line_chars,
            bold_cs=cell.bold_cs,
            style=cell.style,
            font_size=cell.font_size,
            font_size_cs=cell.font_size_cs,
            omit_first_line=cell.omit_first_line,
        )
        for cell in parse_table_row(line, header=header)
    )


def _rich_table_rows(table_lines: list[str], options: dict[str, str]) -> list[tuple[TableCell, ...]]:
    data_lines: list[str] = []
    separator_index: int | None = None
    for table_line in table_lines:
        if is_table_separator(table_line):
            if separator_index is None:
                separator_index = len(data_lines)
            continue
        data_lines.append(table_line)

    header_rows_option = parse_int_option(options, "header_rows")
    if header_rows_option is not None:
        header_rows = max(0, header_rows_option)
    elif separator_index is not None:
        header_rows = separator_index
    else:
        header_rows = 1

    return [
        _table_cells_from_line(table_line, header=row_idx < header_rows)
        for row_idx, table_line in enumerate(data_lines)
    ]


def _parse_image_block(line: str) -> ImageBlock | None:
    match = IMAGE_ATTR_PATTERN.match(line.strip())
    if not match:
        return None
    options = parse_table_options(match.group("attrs") or "")
    return ImageBlock(
        target=match.group("target").strip(),
        alt_text=match.group("alt").strip(),
        raw_text=line,
        options=options,
        width_emu=parse_int_option(options, "width_emu"),
        height_emu=parse_int_option(options, "height_emu"),
        crop_top=parse_int_option(options, "crop_top"),
        crop_right=parse_int_option(options, "crop_right"),
        crop_bottom=parse_int_option(options, "crop_bottom"),
        crop_left=parse_int_option(options, "crop_left"),
    )


def _math_block_from_lines(lines: list[str], options: dict[str, str]) -> MathBlock | None:
    math_text = "\n".join(lines).strip("\n")
    if not math_text and "image" not in options:
        return None
    return MathBlock(
        math_text,
        image=options.get("image"),
        image_alt=options.get("image_alt", ""),
        image_width_emu=parse_int_option(options, "width_emu"),
        image_height_emu=parse_int_option(options, "height_emu"),
        image_mode=options.get("image_mode", options.get("image_type", "drawing")),
        image_first_line=parse_int_option(options, "first_line"),
        image_first_line_chars=parse_int_option(options, "first_line_chars"),
        image_position=parse_int_option(options, "position"),
        image_include_shapetype=parse_bool_option(options, "include_shapetype"),
    )


def parse_body_blocks(text: str, *, rules: BodyParseRules | None = None) -> list[Block]:
    rules = rules or BodyParseRules()
    lines = text.splitlines()
    blocks: list[Block] = []
    paragraph_buffer: list[str] = []
    pending_paragraph_options: dict[str, str] | None = None
    i = 0
    in_code = False
    code_lines: list[str] = []
    in_math = False
    math_lines: list[str] = []
    math_options: dict[str, str] = {}

    def flush_paragraph() -> None:
        nonlocal paragraph_buffer, pending_paragraph_options
        if not paragraph_buffer:
            return
        paragraph = join_soft_wrapped_lines(paragraph_buffer).strip()
        paragraph_buffer = []
        if paragraph:
            blocks.append(ParagraphBlock(paragraph, options=pending_paragraph_options))
            pending_paragraph_options = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if in_code:
            if stripped.startswith("```"):
                code_text = "\n".join(code_lines).rstrip("\n")
                if code_text:
                    blocks.append(CodeBlock(code_text))
                in_code = False
                code_lines = []
            else:
                code_lines.append(line.rstrip("\n"))
            i += 1
            continue

        if in_math:
            if stripped == "$$":
                math_block = _math_block_from_lines(math_lines, math_options)
                if math_block is not None:
                    blocks.append(math_block)
                in_math = False
                math_lines = []
                math_options = {}
            else:
                math_lines.append(line.rstrip("\n"))
            i += 1
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            in_code = True
            code_lines = []
            i += 1
            continue

        math_start_match = MATH_START_PATTERN.match(stripped)
        if math_start_match:
            flush_paragraph()
            in_math = True
            math_lines = []
            math_options = parse_table_options(math_start_match.group("attrs") or "")
            i += 1
            continue

        if not stripped:
            flush_paragraph()
            i += 1
            continue

        paragraph_attr_match = PARAGRAPH_ATTR_PATTERN.match(stripped)
        if paragraph_attr_match:
            flush_paragraph()
            pending_paragraph_options = parse_table_options(paragraph_attr_match.group("attrs") or "")
            i += 1
            continue

        blank_match = BLANK_PATTERN.match(stripped)
        if blank_match:
            flush_paragraph()
            blocks.append(BlankBlock(parse_table_options(blank_match.group("attrs") or "")))
            i += 1
            continue

        table_split_spec = rules.table_split_spec(stripped)
        if table_split_spec is not None:
            flush_paragraph()
            blocks.append(TableSplitBlock(table_split_spec))
            i += 1
            continue

        if rules.is_figure_row_start(stripped):
            flush_paragraph()
            i += 1
            figure_items: list[ImageBlock] = []
            raw_block: list[str] = [line]
            while i < len(lines):
                candidate = lines[i]
                candidate_stripped = candidate.strip()
                raw_block.append(candidate)
                if rules.is_figure_row_end(candidate_stripped):
                    break
                if candidate_stripped:
                    image_block = _parse_image_block(candidate_stripped)
                    if image_block is not None:
                        figure_items.append(image_block)
                i += 1
            blocks.append(FigureRowBlock(tuple(figure_items), tuple(raw_block)))
            i += 1
            continue

        rich_table_match = RICH_TABLE_START_PATTERN.match(stripped)
        if rich_table_match:
            flush_paragraph()
            options = parse_table_options(rich_table_match.group("attrs") or "")
            table_lines: list[str] = []
            i += 1
            while i < len(lines):
                candidate = lines[i]
                candidate_stripped = candidate.strip()
                if RICH_TABLE_END_PATTERN.match(candidate_stripped):
                    break
                if candidate_stripped and "|" in candidate:
                    table_lines.append(candidate)
                i += 1
            rows = _rich_table_rows(table_lines, options)
            if rows:
                blocks.append(TableBlock(tuple(rows), options=options))
            i += 1
            continue

        image_block = _parse_image_block(stripped)
        if image_block is not None:
            flush_paragraph()
            blocks.append(image_block)
            i += 1
            continue

        if re.fullmatch(r"-{3,}|\*{3,}", stripped):
            flush_paragraph()
            next_i = i + 1
            while next_i < len(lines) and not lines[next_i].strip():
                next_i += 1
            next_heading_match = re.match(r"^(#{1,6})\s+(.*)$", lines[next_i]) if next_i < len(lines) else None
            before_heading_level = len(next_heading_match.group(1)) if next_heading_match else None
            blocks.append(PageBreakBlock(before_heading_level=before_heading_level))
            i += 1
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading_match:
            flush_paragraph()
            blocks.append(HeadingBlock(raw_level=len(heading_match.group(1)), text=heading_match.group(2).strip()))
            i += 1
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            blocks.append(QuoteBlock(stripped[1:].strip()))
            i += 1
            continue

        if "|" in line and i + 1 < len(lines) and is_table_separator(lines[i + 1]):
            flush_paragraph()
            rows = [_table_cells_from_line(line, header=True)]
            i += 2
            while i < len(lines):
                candidate = lines[i].strip()
                if not candidate or "|" not in candidate:
                    break
                rows.append(_table_cells_from_line(lines[i]))
                i += 1
            blocks.append(TableBlock(tuple(rows)))
            continue

        paragraph_buffer.append(line)
        i += 1

    flush_paragraph()

    if in_code and code_lines:
        blocks.append(CodeBlock("\n".join(code_lines)))
    if in_math and math_lines:
        math_block = _math_block_from_lines(math_lines, math_options)
        if math_block is not None:
            blocks.append(math_block)

    return blocks
