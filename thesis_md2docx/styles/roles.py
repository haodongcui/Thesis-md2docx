from __future__ import annotations


class StyleRole:
    BASE_NORMAL = "base.normal"
    BODY_TITLE = "body.title"
    BODY_NORMAL = "body.normal"
    BODY_HEADING_LEVEL1 = "body.heading.level1"
    BODY_HEADING_LEVEL2 = "body.heading.level2"
    BODY_HEADING_LEVEL3 = "body.heading.level3"
    FRONT_HEADING = "front.heading"
    TOC_FIELD = "toc.field"
    TOC_LEVEL1 = "toc.level1"
    TOC_LEVEL2 = "toc.level2"
    TOC_LEVEL3 = "toc.level3"
    CAPTION_DEFAULT = "caption.default"
    REFERENCE_ITEM = "reference.item"
    QUOTE_BLOCK = "quote.block"
    CODE_BLOCK = "code.block"
    MATH_BLOCK = "math.block"
    TABLE_CELL = "table.cell"
    HEADER_DEFAULT = "header.default"
    FOOTER_DEFAULT = "footer.default"


COMMON_THESIS_STYLE_ROLES: tuple[str, ...] = (
    StyleRole.BASE_NORMAL,
    StyleRole.BODY_TITLE,
    StyleRole.BODY_NORMAL,
    StyleRole.BODY_HEADING_LEVEL1,
    StyleRole.BODY_HEADING_LEVEL2,
    StyleRole.BODY_HEADING_LEVEL3,
    StyleRole.FRONT_HEADING,
    StyleRole.TOC_FIELD,
    StyleRole.TOC_LEVEL1,
    StyleRole.TOC_LEVEL2,
    StyleRole.TOC_LEVEL3,
    StyleRole.CAPTION_DEFAULT,
    StyleRole.REFERENCE_ITEM,
    StyleRole.QUOTE_BLOCK,
    StyleRole.CODE_BLOCK,
    StyleRole.MATH_BLOCK,
    StyleRole.TABLE_CELL,
    StyleRole.HEADER_DEFAULT,
    StyleRole.FOOTER_DEFAULT,
)
