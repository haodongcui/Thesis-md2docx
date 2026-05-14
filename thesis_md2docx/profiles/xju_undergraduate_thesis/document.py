from __future__ import annotations

from pathlib import Path

from ...builders.document import build_document_elements
from .frontmatter import (
    build_blank_paragraph,
    build_body_paragraph,
    build_cover_elements,
    build_front_heading,
    build_keyword_paragraph,
    build_statement_body_paragraph,
    build_statement_signature_paragraph,
    build_taskbook_elements,
    XJU_DECLARATION_SIGNATURE,
)
from ...frontmatter import parse_inline_image_value, split_statement_content
from ...layout import FrontMatterPageSpec
from ...markdown import (
    extract_abstract_and_keywords,
    parse_cover_info,
    parse_markdown_document,
)
from ...math.converter import MathConverter
from ...media import MediaManager
from ...ooxml.render import (
    add_section_to_paragraph_xml,
    page_break_xml,
    toc_field_paragraph_xml,
)
from ...styles import StyleRole
from ..base import ThesisProfile


def _front_text(front_sections: dict[str, str], page: FrontMatterPageSpec) -> str:
    if page.source_key is None:
        return ""
    return front_sections.get(page.source_key, "").strip()


def _append_cover_page(
    elements: list[str],
    *,
    thesis_title: str,
    cover_info: dict[str, str],
    cover_sect: str,
    cover_assets_dir: Path | None,
    media_manager: MediaManager | None,
) -> None:
    elements.extend(
        build_cover_elements(
            thesis_title,
            cover_info,
            cover_assets_dir=cover_assets_dir,
            media_manager=media_manager,
        )
    )
    # Keep the cover and its blank verso page in an empty-footer section. The
    # second page break carries the section properties, so the declaration starts
    # on physical page 3 while Roman numbering still starts at I.
    elements.append(page_break_xml())
    elements.append(add_section_to_paragraph_xml(page_break_xml(), cover_sect))


def _append_declaration_page(
    elements: list[str],
    *,
    page: FrontMatterPageSpec,
    declaration: str,
    math_converter: MathConverter | None,
    reference_anchors: dict[str, str] | None,
    markdown_dir: Path | None,
    media_manager: MediaManager | None,
) -> None:
    if not declaration:
        return
    elements.append(build_front_heading(page.title, statement=True))
    statement_paragraphs, author_value, date_value = split_statement_content(declaration)
    for paragraph in statement_paragraphs:
        elements.append(
            build_statement_body_paragraph(
                paragraph,
                math_converter=math_converter,
                reference_anchors=reference_anchors,
            )
        )
    signature_image = None
    signature_alt = XJU_DECLARATION_SIGNATURE.signature_alt
    inline_signature = parse_inline_image_value(author_value)
    if inline_signature is not None and media_manager is not None and markdown_dir is not None:
        signature_alt, signature_target = inline_signature
        signature_image = media_manager.register_image(markdown_dir / signature_target)
        if signature_image is not None:
            author_value = ""
    for _ in range(XJU_DECLARATION_SIGNATURE.blank_count(has_signature_image=signature_image is not None)):
        elements.append(build_blank_paragraph(run_size=24))
    elements.append(
        build_statement_signature_paragraph(
            XJU_DECLARATION_SIGNATURE.author_label,
            author_value,
            signature_image=signature_image,
            media_manager=media_manager,
            signature_alt=signature_alt or XJU_DECLARATION_SIGNATURE.signature_alt,
        )
    )
    elements.append(
        build_statement_signature_paragraph(XJU_DECLARATION_SIGNATURE.date_label, date_value, is_date=True)
    )
    if page.page_break_after:
        elements.append(page_break_xml())


def _append_taskbook_page(
    elements: list[str],
    *,
    taskbook: str,
    cover_info: dict[str, str],
) -> bool:
    if not taskbook:
        return False
    elements.extend(build_taskbook_elements(taskbook, cover_info))
    return True


def _append_abstract_page(
    elements: list[str],
    *,
    page: FrontMatterPageSpec,
    text: str,
    page_break_before: bool,
    math_converter: MathConverter | None,
    reference_anchors: dict[str, str] | None,
) -> None:
    paragraphs, keywords = extract_abstract_and_keywords(text, page.keyword_prefix)
    if not paragraphs and not keywords:
        return
    elements.append(
        build_front_heading(
            page.title,
            english=page.english,
            page_break_before=page_break_before,
        )
    )
    for paragraph in paragraphs:
        elements.append(
            build_body_paragraph(
                paragraph,
                english=page.english,
                math_converter=math_converter,
                reference_anchors=reference_anchors,
            )
        )
    keyword_paragraph = build_keyword_paragraph(keywords, english=page.english)
    if keyword_paragraph:
        elements.append(build_blank_paragraph())
        elements.append(keyword_paragraph)
    if page.page_break_after:
        elements.append(page_break_xml())


def _append_toc_page(
    elements: list[str],
    *,
    thesis_profile: ThesisProfile,
    page: FrontMatterPageSpec,
    front_sect: str,
) -> None:
    elements.append(build_front_heading(page.title, toc=True))
    toc_style = thesis_profile.style_roles().require(StyleRole.TOC_FIELD)
    elements.append(add_section_to_paragraph_xml(toc_field_paragraph_xml(style=toc_style), front_sect))


def build_document(
    text: str,
    *,
    thesis_profile: ThesisProfile,
    math_converter: MathConverter | None = None,
    reference_anchors: dict[str, str] | None = None,
    markdown_dir: Path | None = None,
    cover_assets_dir: Path | None = None,
    media_manager: MediaManager | None = None,
) -> tuple[list[str], str, str]:
    markdown_title, front_sections, body_text = parse_markdown_document(text)
    front_spec = thesis_profile.front_matter_spec()
    cover_info = parse_cover_info(front_sections.get(front_spec.cover_info_key, ""))
    thesis_title = cover_info.get("论文题目") or markdown_title or front_spec.default_title
    profile = thesis_profile.body_style_profile()
    layout = thesis_profile.document_layout()

    # Keep the cover and its blank verso page in an empty-footer section. The
    # second page break carries the section properties, so the declaration starts
    # on physical page 3 while Roman numbering still starts at I.
    cover_sect = thesis_profile.section_from_spec(layout.cover)
    front_sect = thesis_profile.section_from_spec(layout.front_matter)
    body_start_sect = thesis_profile.section_from_spec(layout.body_start)
    body_continue_sect = thesis_profile.section_from_spec(layout.body_continue)

    elements: list[str] = []
    taskbook_added = False
    for page in thesis_profile.front_matter_plan().pages:
        if page.kind == "cover":
            _append_cover_page(
                elements,
                thesis_title=thesis_title,
                cover_info=cover_info,
                cover_sect=cover_sect,
                cover_assets_dir=cover_assets_dir,
                media_manager=media_manager,
            )
            continue
        if page.kind == "declaration":
            _append_declaration_page(
                elements,
                page=page,
                declaration=_front_text(front_sections, page),
                math_converter=math_converter,
                reference_anchors=reference_anchors,
                markdown_dir=markdown_dir,
                media_manager=media_manager,
            )
            continue
        if page.kind == "taskbook":
            taskbook_added = _append_taskbook_page(
                elements,
                taskbook=_front_text(front_sections, page),
                cover_info=cover_info,
            )
            continue
        if page.kind == "abstract":
            _append_abstract_page(
                elements,
                page=page,
                text=_front_text(front_sections, page),
                page_break_before=(not page.english and taskbook_added) or page.page_break_before,
                math_converter=math_converter,
                reference_anchors=reference_anchors,
            )
            continue
        if page.kind == "toc":
            _append_toc_page(elements, thesis_profile=thesis_profile, page=page, front_sect=front_sect)
            continue

    body_elements, body_has_section_breaks = build_document_elements(
        body_text,
        profile=profile,
        rules=thesis_profile.body_parse_rules(),
        treat_first_heading_as_title=False,
        math_converter=math_converter,
        reference_anchors=reference_anchors,
        markdown_dir=markdown_dir,
        media_manager=media_manager,
    )
    elements.extend(body_elements)
    body_sect = body_continue_sect if body_has_section_breaks else body_start_sect
    return elements, body_sect, thesis_title
