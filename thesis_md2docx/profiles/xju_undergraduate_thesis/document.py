from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from ...builders.document import build_document_elements, collect_toc_entries
from ...constants import REL_ID_EMPTY_FOOTER, REL_ID_EMPTY_HEADER
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
    extract_abstract_keyword_blocks,
    parse_cover_info,
    parse_markdown_document,
)
from ...math.converter import MathConverter
from ...media import MediaManager
from ...ooxml.render import (
    add_section_to_paragraph_xml,
    image_run_xml,
    page_break_xml,
    paragraph_xml,
    section_break_paragraph_xml,
    toc_cache_entry_paragraph_xml,
    toc_field_paragraph_xml,
)
from ...ooxml.xml import spacing_xml
from ...ooxml.xml import indent_xml
from ...styles import StyleRole
from ...toc import TocEntry
from ..base import ThesisProfile

A4_WIDTH_TWIPS = 11907
A4_HEIGHT_TWIPS = 16840
A4_WIDTH_EMU = A4_WIDTH_TWIPS * 635
A4_HEIGHT_EMU = A4_HEIGHT_TWIPS * 635
EXTERNAL_TASKBOOK_PDF_KEYS = (
    "任务书PDF",
    "任务书 PDF",
    "外部任务书PDF",
    "外部任务书 PDF",
    "任务书文件",
)
PDF_PAGE_IMAGE_DPI = 300


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
    section_break_after: str | None = None,
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
        if section_break_after:
            elements.append(section_break_paragraph_xml(section_break_after))
        else:
            elements.append(page_break_xml())


def _append_taskbook_page(
    elements: list[str],
    *,
    taskbook: str,
    cover_info: dict[str, str],
) -> tuple[bool, bool]:
    if not taskbook:
        return False, False
    elements.extend(build_taskbook_elements(taskbook, cover_info))
    return True, False


def _taskbook_image_section_xml() -> str:
    return (
        '<w:sectPr><w:type w:val="nextPage"/>'
        f'<w:headerReference w:type="default" r:id="{REL_ID_EMPTY_HEADER}"/>'
        f'<w:footerReference w:type="default" r:id="{REL_ID_EMPTY_FOOTER}"/>'
        '<w:pgNumType w:fmt="upperRoman"/>'
        f'<w:pgSz w:w="{A4_WIDTH_TWIPS}" w:h="{A4_HEIGHT_TWIPS}"/>'
        '<w:pgMar w:top="0" w:right="0" w:bottom="0" w:left="0" '
        'w:header="0" w:footer="0" w:gutter="0"/>'
        '<w:cols w:space="720"/>'
        '<w:docGrid w:linePitch="384"/>'
        '</w:sectPr>'
    )


def _front_matter_continue_section_xml(thesis_profile: ThesisProfile) -> str:
    return thesis_profile.section_pr_xml(
        with_header=True,
        footer_kind="page",
        section_type="nextPage",
        page_number_format="upperRoman",
    )


def _resolve_external_taskbook_pdf(taskbook: str, markdown_dir: Path | None) -> Path | None:
    task_info = parse_cover_info(taskbook)
    raw_path = ""
    for key in EXTERNAL_TASKBOOK_PDF_KEYS:
        raw_path = task_info.get(key, "").strip()
        if raw_path:
            break
    if not raw_path:
        return None
    path = Path(raw_path).expanduser()
    if not path.is_absolute() and markdown_dir is not None:
        path = markdown_dir / path
    path = path.resolve()
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"外部任务书必须使用 PDF 文件：{path}")
    if not path.is_file():
        raise FileNotFoundError(f"外部任务书 PDF 不存在：{path}")
    return path


def _pdf_page_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"-(\d+)\.png$", path.name)
    return (int(match.group(1)) if match else 0, path.name)


def _render_pdf_pages_to_png(pdf_path: Path) -> list[Path]:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("pdftoppm not found; install poppler-utils or add pdftoppm to PATH")
    output_dir = Path(tempfile.mkdtemp(prefix="xju-taskbook-pdf-"))
    output_prefix = output_dir / "page"
    result = subprocess.run(
        [pdftoppm, "-png", "-r", str(PDF_PAGE_IMAGE_DPI), str(pdf_path), str(output_prefix)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stdout or "").strip() or f"pdftoppm exited with {result.returncode}")
    pages = sorted(output_dir.glob("page-*.png"), key=_pdf_page_sort_key)
    if not pages:
        raise RuntimeError(f"未能从外部任务书 PDF 渲染出页面：{pdf_path}")
    return pages


def _taskbook_pdf_page_xml(
    image_item,
    media_manager: MediaManager,
    *,
    page_break_after: bool = False,
    section_after: str | None = None,
) -> str:
    runs = [
        image_run_xml(
            image_item,
            docpr_id=media_manager.next_drawing_id(),
            alt_text=image_item.filename,
            width_emu=A4_WIDTH_EMU,
            height_emu=A4_HEIGHT_EMU,
        )
    ]
    if page_break_after:
        runs.append('<w:r><w:br w:type="page"/></w:r>')
    paragraph = paragraph_xml(
        runs=runs,
        ppr_extra='<w:snapToGrid w:val="0"/>' + spacing_xml(before=0, after=0),
    )
    if section_after:
        paragraph = add_section_to_paragraph_xml(paragraph, section_after)
    return paragraph


def _append_external_taskbook_pdf(
    elements: list[str],
    *,
    pdf_path: Path,
    media_manager: MediaManager | None,
    section_after: str,
) -> tuple[bool, bool]:
    if media_manager is None:
        raise RuntimeError("外部任务书 PDF 需要 media_manager 才能插入 DOCX")
    page_images = _render_pdf_pages_to_png(pdf_path)
    if page_images:
        media_manager.register_temp_dir(page_images[0].parent)
    for index, image_path in enumerate(page_images):
        image_item = media_manager.register_image(image_path)
        if image_item is None:
            raise RuntimeError(f"无法注册外部任务书页面图片：{image_path}")
        is_last = index == len(page_images) - 1
        elements.append(
            _taskbook_pdf_page_xml(
                image_item,
                media_manager,
                page_break_after=not is_last,
                section_after=section_after if is_last else None,
            )
        )
    return True, True


def _append_abstract_page(
    elements: list[str],
    *,
    page: FrontMatterPageSpec,
    text: str,
    page_break_before: bool,
    math_converter: MathConverter | None,
    reference_anchors: dict[str, str] | None,
) -> None:
    paragraphs, keywords, after_keyword = extract_abstract_keyword_blocks(text, page.keyword_prefix)
    if not paragraphs and not keywords and not after_keyword:
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
        elements.append(build_blank_paragraph(line=360 if page.english else 405))
        elements.append(keyword_paragraph)
    for paragraph in after_keyword:
        elements.append(
            build_body_paragraph(
                paragraph,
                english=page.english,
                math_converter=math_converter,
                reference_anchors=reference_anchors,
            )
        )
    if page.page_break_after:
        elements.append(page_break_xml())


def _append_toc_page(
    elements: list[str],
    *,
    thesis_profile: ThesisProfile,
    page: FrontMatterPageSpec,
    front_sect: str,
    toc_entries: list[TocEntry] | None = None,
) -> None:
    elements.append(build_front_heading(page.title, toc=True))
    toc_style = thesis_profile.style_roles().require(StyleRole.TOC_FIELD)
    toc_level_styles = {
        1: thesis_profile.style_roles().require(StyleRole.TOC_LEVEL1),
        2: thesis_profile.style_roles().require(StyleRole.TOC_LEVEL2),
        3: thesis_profile.style_roles().require(StyleRole.TOC_LEVEL3),
    }
    if not toc_entries:
        elements.append(add_section_to_paragraph_xml(toc_field_paragraph_xml(style=toc_style), front_sect))
        return
    for index, entry in enumerate(toc_entries):
        is_last = index == len(toc_entries) - 1
        paragraph = toc_cache_entry_paragraph_xml(
            entry,
            first=index == 0,
            close_field=is_last,
            toc_field_style=toc_style,
            toc_level_styles=toc_level_styles,
        )
        elements.append(paragraph)
    elements.append(
        paragraph_xml(
            style=thesis_profile.style_roles().require(StyleRole.BODY_HEADING_LEVEL1),
            ppr_extra=spacing_xml(line=240) + indent_xml(left=0, first_line=0) + front_sect,
        )
    )


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
    front_continue_sect = _front_matter_continue_section_xml(thesis_profile)
    taskbook_image_sect = _taskbook_image_section_xml()
    body_start_sect = thesis_profile.section_from_spec(layout.body_start)
    body_continue_sect = thesis_profile.section_from_spec(layout.body_continue)
    taskbook_text = front_sections.get(front_spec.taskbook_key or "", "").strip()
    external_taskbook_pdf = _resolve_external_taskbook_pdf(taskbook_text, markdown_dir)

    body_rules = thesis_profile.body_parse_rules()
    toc_entries = collect_toc_entries(
        body_text,
        rules=body_rules,
        appendix_heading_normalizer=profile.appendix_heading_normalizer,
    )

    elements: list[str] = []
    taskbook_added = False
    taskbook_ended_with_section = False
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
                section_break_after=front_sect if external_taskbook_pdf is not None else None,
            )
            continue
        if page.kind == "taskbook":
            if external_taskbook_pdf is not None:
                taskbook_added, taskbook_ended_with_section = _append_external_taskbook_pdf(
                    elements,
                    pdf_path=external_taskbook_pdf,
                    media_manager=media_manager,
                    section_after=taskbook_image_sect,
                )
            else:
                taskbook_added, taskbook_ended_with_section = _append_taskbook_page(
                    elements,
                    taskbook=_front_text(front_sections, page),
                    cover_info=cover_info,
                )
                if taskbook_added:
                    elements.append(page_break_xml())
            continue
        if page.kind == "abstract":
            _append_abstract_page(
                elements,
                page=page,
                text=_front_text(front_sections, page),
                page_break_before=page.page_break_before,
                math_converter=math_converter,
                reference_anchors=reference_anchors,
            )
            continue
        if page.kind == "toc":
            _append_toc_page(
                elements,
                thesis_profile=thesis_profile,
                page=page,
                front_sect=front_continue_sect if taskbook_ended_with_section else front_sect,
                toc_entries=toc_entries,
            )
            continue
    body_elements, body_has_section_breaks, _ = build_document_elements(
        body_text,
        profile=profile,
        rules=body_rules,
        treat_first_heading_as_title=False,
        math_converter=math_converter,
        reference_anchors=reference_anchors,
        markdown_dir=markdown_dir,
        media_manager=media_manager,
    )
    elements.extend(body_elements)
    body_sect = body_continue_sect if body_has_section_breaks else body_start_sect
    return elements, body_sect, thesis_title
