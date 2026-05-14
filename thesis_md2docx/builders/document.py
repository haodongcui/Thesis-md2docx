from __future__ import annotations

from pathlib import Path

from ..body_rules import BodyParseRules
from ..constants import *
from ..ir import (
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
    TableSplitBlock,
)
from ..math.converter import MathConverter
from ..media import MediaImage, MediaManager
from ..ooxml.render import (
    figure_row_xml,
    image_paragraph_xml,
    math_paragraph_xml,
    page_break_xml,
    paragraph_with_inline_math_xml,
    paragraph_xml,
    section_break_paragraph_xml,
    table_xml,
)
from ..parser import parse_body_blocks
from ..styles import BodyRenderProfile
from ..table_utils import parse_table_split_spec, split_table_rows


def _require_hook(profile: BodyRenderProfile, name: str):
    hook = getattr(profile, name)
    if hook is None:
        raise ValueError(f"body render profile is missing hook: {name}")
    return hook


def build_document_elements(
    text: str,
    profile: BodyRenderProfile,
    *,
    rules: BodyParseRules | None = None,
    treat_first_heading_as_title: bool = True,
    math_converter: MathConverter | None = None,
    reference_anchors: dict[str, str] | None = None,
    markdown_dir: Path | None = None,
    media_manager: MediaManager | None = None,
) -> tuple[list[str], bool]:
    rules = rules or BodyParseRules()
    blocks = parse_body_blocks(text, rules=rules)
    return build_document_blocks(
        blocks,
        profile,
        rules=rules,
        treat_first_heading_as_title=treat_first_heading_as_title,
        math_converter=math_converter,
        reference_anchors=reference_anchors,
        markdown_dir=markdown_dir,
        media_manager=media_manager,
    )


def build_document_blocks(
    blocks: list[Block],
    profile: BodyRenderProfile,
    *,
    rules: BodyParseRules | None = None,
    treat_first_heading_as_title: bool = True,
    math_converter: MathConverter | None = None,
    reference_anchors: dict[str, str] | None = None,
    markdown_dir: Path | None = None,
    media_manager: MediaManager | None = None,
) -> tuple[list[str], bool]:
    rules = rules or BodyParseRules()
    elements: list[str] = []
    current_top_heading = ""
    in_appendix = False
    current_chapter_number = ""
    current_appendix_index = 0
    formula_counters: dict[str, int] = {}
    page_break_marker = page_break_xml()
    chapter_section_break_count = 0
    pending_table_split: list[int] | None = None
    last_table_caption_text: str | None = None

    heading_builder = _require_hook(profile, "heading_builder")
    acknowledgement_heading_builder = _require_hook(profile, "acknowledgement_heading_builder")
    caption_builder = _require_hook(profile, "caption_builder")
    reference_builder = _require_hook(profile, "reference_builder")
    table_builder = profile.table_builder or table_xml
    appendix_heading_normalizer = _require_hook(profile, "appendix_heading_normalizer")
    appendix_reference_normalizer = _require_hook(profile, "appendix_reference_normalizer")
    section_pr_builder = _require_hook(profile, "section_pr_builder")

    def is_chapter_section_break(element: str) -> bool:
        return "<w:sectPr>" in element and 'w:type w:val="nextPage"' in element

    def append_chapter_page_break() -> None:
        nonlocal chapter_section_break_count
        if elements and elements[-1] != page_break_marker and not is_chapter_section_break(elements[-1]):
            if chapter_section_break_count == 0:
                sect_pr = section_pr_builder(
                    section_type="nextPage",
                    with_header=True,
                    footer_kind="page",
                    page_number_format="decimal",
                    page_number_start=1,
                )
            else:
                sect_pr = section_pr_builder(section_type="nextPage", with_header=True, footer_kind="page")
            elements.append(section_break_paragraph_xml(sect_pr))
            chapter_section_break_count += 1

    def next_formula_number() -> str | None:
        scope = rules.formula_scope(
            in_appendix=in_appendix,
            current_appendix_index=current_appendix_index,
            current_chapter_number=current_chapter_number,
        )
        if not scope:
            return None
        formula_counters[scope] = formula_counters.get(scope, 0) + 1
        return rules.format_formula_number(scope, formula_counters[scope])

    def append_paragraph(paragraph: str) -> None:
        nonlocal last_table_caption_text
        paragraph = paragraph.strip()
        if not paragraph:
            return

        if in_appendix and current_appendix_index > 0:
            paragraph = appendix_reference_normalizer(paragraph, current_appendix_index)

        if rules.is_reference_heading(current_top_heading):
            if rules.should_skip_reference_paragraph(paragraph):
                return
            if rules.is_reference_entry(paragraph):
                elements.append(reference_builder(paragraph, reference_anchors=reference_anchors))
                return

        if rules.is_caption_paragraph(paragraph):
            # Table captions appear immediately above the table they label, so
            # `keepNext` keeps them on the same page as the table when possible.
            # Figure captions appear after the image, so they do not need it.
            keep_next_caption = rules.is_table_caption(paragraph)
            if keep_next_caption:
                last_table_caption_text = paragraph
            caption_style = profile.styles.caption or profile.styles.normal
            elements.append(
                caption_builder(
                    paragraph,
                    style=caption_style,
                    math_converter=math_converter,
                    reference_anchors=reference_anchors,
                    keep_next=keep_next_caption,
                )
            )
            return

        normal_run = profile.normal_run.to_kwargs() if profile.normal_run else None
        normal_paragraph = profile.normal_paragraph
        if normal_run:
            elements.append(
                paragraph_with_inline_math_xml(
                    paragraph,
                    style=profile.styles.normal,
                    ppr_extra=normal_paragraph.ppr_extra,
                    first_line_chars=normal_paragraph.first_line_chars,
                    first_line=normal_paragraph.first_line,
                    run_kwargs=normal_run,
                    math_converter=math_converter,
                    reference_anchors=reference_anchors,
                )
            )
        else:
            elements.append(
                paragraph_with_inline_math_xml(
                    paragraph,
                    style=profile.styles.normal,
                    first_line_chars=normal_paragraph.first_line_chars,
                    first_line=normal_paragraph.first_line,
                    ppr_extra=normal_paragraph.ppr_extra,
                    math_converter=math_converter,
                    reference_anchors=reference_anchors,
                )
            )

    def resolve_image(target: str) -> MediaImage | None:
        image_path = markdown_dir / target if markdown_dir else Path(target)
        return media_manager.register_image(image_path) if media_manager else None

    for block in blocks:
        if isinstance(block, TableSplitBlock):
            pending_table_split = parse_table_split_spec(block.spec)
            continue

        if isinstance(block, FigureRowBlock):
            figure_items = [(resolve_image(image.target), image.alt_text) for image in block.images]
            if figure_items and media_manager is not None:
                figure_xml = figure_row_xml(figure_items, media_manager)
                if figure_xml:
                    elements.append(figure_xml)
            else:
                for raw_line in block.raw_lines:
                    append_paragraph(raw_line)
            continue

        if isinstance(block, ImageBlock):
            item = resolve_image(block.target)
            if item is not None:
                elements.append(image_paragraph_xml(item, media_manager, alt_text=block.alt_text))
            else:
                append_paragraph(block.raw_text)
            continue

        if isinstance(block, PageBreakBlock):
            if block.before_heading_level == 1:
                append_chapter_page_break()
            else:
                elements.append(page_break_xml())
            continue

        if isinstance(block, HeadingBlock):
            raw_level = block.raw_level
            level = block.level
            heading_text = block.text

            if raw_level == 1:
                current_top_heading = heading_text
                if rules.is_appendix_heading(heading_text):
                    in_appendix = True
                    current_appendix_index = 0
                    current_chapter_number = ""
                    continue
                in_appendix = False
                current_chapter_number = rules.extract_chapter_number(heading_text)
            elif rules.is_appendix_heading(current_top_heading):
                in_appendix = True

            if len(elements) == 0 and treat_first_heading_as_title:
                elements.append(paragraph_xml(heading_text, style=profile.styles.title, align="center"))
                continue

            if rules.is_appendix_heading(current_top_heading) and rules.is_appendix_item_heading(raw_level):
                current_appendix_index += 1
                append_chapter_page_break()
                appendix_heading = heading_builder(
                    appendix_heading_normalizer(heading_text, current_appendix_index),
                    1,
                    profile,
                    numbered=False,
                )
                elements.append(appendix_heading)
                continue

            if raw_level == 1:
                append_chapter_page_break()

            is_unnumbered = rules.is_unnumbered_heading(heading_text, in_appendix=in_appendix, level=level)
            display_heading_text = rules.display_heading_text(heading_text)

            caption_style_id = profile.styles.caption or ""
            previous_is_caption = bool(
                caption_style_id and elements and f'w:pStyle w:val="{caption_style_id}"' in elements[-1]
            )
            if rules.is_acknowledgement_heading(heading_text) and raw_level == 1:
                heading_xml = acknowledgement_heading_builder(display_heading_text, profile)
            else:
                heading_xml = heading_builder(
                    display_heading_text,
                    level,
                    profile,
                    numbered=not is_unnumbered,
                    keep_with_next=not previous_is_caption,
                )
            elements.append(heading_xml)
            continue

        if isinstance(block, QuoteBlock):
            elements.append(
                paragraph_xml(
                    block.text,
                    style=profile.styles.quote,
                )
            )
            continue

        if isinstance(block, TableBlock):
            rows = [list(row) for row in block.rows]
            if rows:
                width = len(rows[0])
                normalized = [row[:width] + [""] * max(0, width - len(row)) for row in rows]
                table_chunks = split_table_rows(normalized, pending_table_split or [])
                caption_style = profile.styles.caption or profile.styles.normal
                for chunk_idx, table_chunk in enumerate(table_chunks):
                    if chunk_idx > 0 and last_table_caption_text:
                        elements.append(
                            caption_builder(
                                f"{last_table_caption_text}（续）",
                                style=caption_style,
                                math_converter=math_converter,
                                reference_anchors=reference_anchors,
                                keep_next=True,
                            )
                        )
                    elements.append(
                        table_builder(
                            table_chunk,
                            cell_style=profile.styles.table_cell,
                            math_converter=math_converter,
                            reference_anchors=reference_anchors,
                        )
                    )
                pending_table_split = None
                last_table_caption_text = None
            continue

        if isinstance(block, CodeBlock):
            elements.append(
                paragraph_xml(
                    block.text,
                    style=profile.styles.code,
                    preserve_breaks=True,
                    ppr_extra=profile.code_paragraph.ppr_extra,
                )
            )
            continue

        if isinstance(block, MathBlock):
            elements.append(
                math_paragraph_xml(
                    block.text,
                    style=profile.styles.math,
                    math_converter=math_converter,
                    equation_number=next_formula_number(),
                )
            )
            continue

        if isinstance(block, ParagraphBlock):
            append_paragraph(block.text)

    return elements, chapter_section_break_count > 0
