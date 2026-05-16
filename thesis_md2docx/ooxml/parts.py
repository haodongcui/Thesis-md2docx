from __future__ import annotations

import datetime as dt
from xml.sax.saxutils import escape

from ..constants import *
from ..media import MediaManager


def native_sect_pr_xml(
    *,
    with_header: bool = False,
    footer_kind: str | None = None,
    section_type: str | None = None,
    page_number_format: str | None = None,
    page_number_start: int | None = None,
) -> str:
    parts = ["<w:sectPr>"]
    if section_type:
        parts.append(f'<w:type w:val="{section_type}"/>')
    if with_header:
        parts.append(f'<w:headerReference w:type="default" r:id="{REL_ID_HEADER}"/>')
    if footer_kind == "empty":
        parts.append(f'<w:footerReference w:type="default" r:id="{REL_ID_EMPTY_FOOTER}"/>')
    elif footer_kind == "page":
        parts.append(f'<w:footerReference w:type="default" r:id="{REL_ID_PAGE_FOOTER}"/>')
    if page_number_format or page_number_start is not None:
        attrs: list[str] = []
        if page_number_format:
            attrs.append(f'w:fmt="{page_number_format}"')
        if page_number_start is not None:
            attrs.append(f'w:start="{page_number_start}"')
        parts.append(f"<w:pgNumType {' '.join(attrs)}/>")
    parts.append('<w:pgSz w:w="11907" w:h="16840"/>')
    parts.append(
        '<w:pgMar w:top="1440" w:right="1797" w:bottom="1440" '
        'w:left="1797" w:header="850" w:footer="992" w:gutter="0"/>'
    )
    parts.append('<w:cols w:space="720"/>')
    parts.append('<w:docGrid w:linePitch="384"/>')
    parts.append("</w:sectPr>")
    return "".join(parts)


def default_sect_pr_xml() -> str:
    return native_sect_pr_xml(with_header=True, footer_kind="page", page_number_format="decimal", page_number_start=1)


def document_xml(elements: list[str], sect_pr: str | None = None) -> str:
    sect_pr = sect_pr or default_sect_pr_xml()
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W_NS}" xmlns:r="{R_NS}" xmlns:m="{M_NS}" xmlns:wp="{WP_NS}" xmlns:a="{A_NS}" xmlns:pic="{PIC_NS}">'
        f"<w:body>{''.join(elements)}{sect_pr}</w:body>"
        "</w:document>"
    )


def content_types_xml(image_extensions: set[str] | None = None) -> str:
    defaults = [
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
    ]
    for ext in sorted(image_extensions or set()):
        content_type = IMAGE_CONTENT_TYPES.get(ext)
        if content_type:
            defaults.append(f'<Default Extension="{ext}" ContentType="{content_type}"/>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        f'{"".join(defaults)}'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
        '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
        '<Override PartName="/word/fontTable.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"/>'
        '<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
        '<Override PartName="/word/header2.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
        '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
        '<Override PartName="/word/footer2.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        "</Types>"
    )


def rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        "</Relationships>"
    )


def document_rels_xml(media_manager: MediaManager | None = None) -> str:
    relationships = [
        f'<Relationship Id="{REL_ID_STYLES}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>',
        f'<Relationship Id="{REL_ID_NUMBERING}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>',
        f'<Relationship Id="{REL_ID_SETTINGS}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>',
        f'<Relationship Id="{REL_ID_FONT_TABLE}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable" Target="fontTable.xml"/>',
        f'<Relationship Id="{REL_ID_HEADER}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>',
        f'<Relationship Id="{REL_ID_EMPTY_FOOTER}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>',
        f'<Relationship Id="{REL_ID_PAGE_FOOTER}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer2.xml"/>',
        f'<Relationship Id="{REL_ID_EMPTY_HEADER}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header2.xml"/>',
    ]
    if media_manager:
        for item in media_manager.images:
            relationships.append(
                f'<Relationship Id="{item.rel_id}" Type="{IMAGE_REL_TYPE}" Target="{item.part_name}"/>'
            )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f'{"".join(relationships)}'
        "</Relationships>"
    )


def settings_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:settings xmlns:w="{W_NS}">'
        '<w:updateFields w:val="true"/>'
        '<w:zoom w:percent="100"/>'
        "<w:bordersDoNotSurroundHeader/>"
        "<w:bordersDoNotSurroundFooter/>"
        '<w:defaultTabStop w:val="420"/>'
        '<w:drawingGridHorizontalSpacing w:val="105"/>'
        '<w:drawingGridVerticalSpacing w:val="156"/>'
        '<w:displayHorizontalDrawingGridEvery w:val="0"/>'
        '<w:displayVerticalDrawingGridEvery w:val="2"/>'
        '<w:characterSpacingControl w:val="compressPunctuation"/>'
        '<w:themeFontLang w:val="en-US" w:eastAsia="zh-CN"/>'
        "<w:compat>"
        "<w:spaceForUL/>"
        "<w:balanceSingleByteDoubleByteWidth/>"
        "<w:doNotLeaveBackslashAlone/>"
        "<w:ulTrailSpace/>"
        "<w:doNotExpandShiftReturn/>"
        "<w:adjustLineHeightInTable/>"
        "<w:useFELayout/>"
        '<w:compatSetting w:name="compatibilityMode" '
        'w:uri="http://schemas.microsoft.com/office/word" w:val="15"/>'
        '<w:compatSetting w:name="overrideTableStyleFontSizeAndJustification" '
        'w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
        '<w:compatSetting w:name="enableOpenTypeFeatures" '
        'w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
        '<w:compatSetting w:name="doNotFlipMirrorIndents" '
        'w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
        '<w:compatSetting w:name="differentiateMultirowTableHeaders" '
        'w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
        "</w:compat>"
        "</w:settings>"
    )


def core_xml(title: str) -> str:
    created = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<cp:coreProperties xmlns:cp="{CP_NS}" xmlns:dc="{DC_NS}" xmlns:dcterms="{DCTERMS_NS}" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="{XSI_NS}">'
        f"<dc:title>{escape(title)}</dc:title>"
        "<dc:creator>Codex</dc:creator>"
        "<cp:lastModifiedBy>Codex</cp:lastModifiedBy>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>'
        "</cp:coreProperties>"
    )


def app_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="{VT_NS}">'
        "<Application>Codex</Application>"
        "</Properties>"
    )
