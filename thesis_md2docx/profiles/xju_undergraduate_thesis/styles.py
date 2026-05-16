from __future__ import annotations

from ...layout import StyleBundle
from ...ooxml.parts import settings_xml
from ...styles import DocumentDefaultsSpec, StyleCatalog, StyleRole, StyleRoleMap, StyleSpec
from ...styles.fonts import FontSpec, FontTableSpec, font_table_xml
from ...styles.numbering import (
    AbstractNumberingSpec,
    NumberingCatalog,
    NumberingInstanceSpec,
    NumberingLevelSpec,
    numbering_xml,
)
from ...styles.ooxml import styles_xml as render_styles_xml
from ...styles.properties import (
    bold,
    bold_complex,
    indent,
    italic,
    justification,
    kern,
    numbering,
    outline_level,
    paragraph_bottom_border,
    run_fonts,
    run_size,
    shading,
    snap_to_grid,
    spacing,
    style_props,
    tab,
    tabs,
    widow_control,
)


STYLE_BODY = "XjuBody"
STYLE_HEADING_1 = "XjuHeading1"
STYLE_HEADING_2 = "XjuHeading2"
STYLE_HEADING_3 = "XjuHeading3"
STYLE_FRONT_HEADING = "XjuFrontHeading"
STYLE_TOC_FIELD = "XjuTocField"
STYLE_CAPTION = "XjuCaption"
STYLE_REFERENCE = "XjuReference"
STYLE_QUOTE = "XjuQuote"
STYLE_CODE_BLOCK = "XjuCodeBlock"
STYLE_MATH_BLOCK = "XjuMathBlock"
STYLE_TABLE_TEXT = "XjuTableText"
STYLE_HEADER = "XjuHeader"
STYLE_FOOTER = "XjuFooter"


def xju_numbering_catalog() -> NumberingCatalog:
    return NumberingCatalog(
        abstract_numbers=(
            AbstractNumberingSpec(
                abstract_num_id=0,
                levels=(
                    NumberingLevelSpec(level=0, text="%1  ", paragraph_style=STYLE_HEADING_1),
                    NumberingLevelSpec(level=1, text="%1.%2", paragraph_style=STYLE_HEADING_2),
                    NumberingLevelSpec(level=2, text="%1.%2.%3", paragraph_style=STYLE_HEADING_3),
                ),
            ),
        ),
        instances=(NumberingInstanceSpec(num_id=1, abstract_num_id=0),),
    )


def xju_numbering_xml() -> str:
    return numbering_xml(xju_numbering_catalog())


def xju_font_table() -> FontTableSpec:
    return FontTableSpec(
        fonts=(
            FontSpec("Times New Roman"),
            FontSpec("宋体", alt_name="SimSun", charset="86", family="auto", pitch="variable"),
            FontSpec("黑体", alt_name="SimHei", charset="86", family="modern", pitch="fixed"),
            FontSpec("楷体_GB2312", alt_name="楷体", charset="86", family="modern", pitch="default"),
            FontSpec("Cambria Math"),
            FontSpec("Courier New"),
            FontSpec("等线", alt_name="DengXian"),
        ),
    )


def xju_font_table_xml() -> str:
    return font_table_xml(xju_font_table())


def xju_style_roles() -> StyleRoleMap:
    return StyleRoleMap(
        {
            StyleRole.BASE_NORMAL: "Normal",
            StyleRole.BODY_TITLE: STYLE_HEADING_1,
            StyleRole.BODY_NORMAL: STYLE_BODY,
            StyleRole.BODY_HEADING_LEVEL1: STYLE_HEADING_1,
            StyleRole.BODY_HEADING_LEVEL2: STYLE_HEADING_2,
            StyleRole.BODY_HEADING_LEVEL3: STYLE_HEADING_3,
            StyleRole.FRONT_HEADING: STYLE_FRONT_HEADING,
            StyleRole.TOC_FIELD: STYLE_TOC_FIELD,
            StyleRole.TOC_LEVEL1: "TOC1",
            StyleRole.TOC_LEVEL2: "TOC2",
            StyleRole.TOC_LEVEL3: "TOC3",
            StyleRole.CAPTION_DEFAULT: STYLE_CAPTION,
            StyleRole.REFERENCE_ITEM: STYLE_REFERENCE,
            StyleRole.QUOTE_BLOCK: STYLE_QUOTE,
            StyleRole.CODE_BLOCK: STYLE_CODE_BLOCK,
            StyleRole.MATH_BLOCK: STYLE_MATH_BLOCK,
            StyleRole.TABLE_CELL: STYLE_TABLE_TEXT,
            StyleRole.HEADER_DEFAULT: STYLE_HEADER,
            StyleRole.FOOTER_DEFAULT: STYLE_FOOTER,
        }
    )


def xju_style_catalog() -> StyleCatalog:
    return StyleCatalog(
        defaults=DocumentDefaultsSpec(
            run_props=style_props(
                run_fonts(ascii="Times New Roman", hansi="Times New Roman", eastasia="宋体"),
                run_size(24),
            )
        ),
        styles=(
            StyleSpec(
                style_id="Normal",
                name="Normal",
                default=True,
                paragraph_props=style_props(widow_control(False), justification("both")),
                run_props=style_props(
                    run_fonts(
                        ascii="Times New Roman",
                        hansi="Times New Roman",
                        eastasia="宋体",
                        complex_script="Times New Roman",
                    ),
                    kern(2),
                    run_size(21, complex_size=24),
                ),
            ),
            StyleSpec(
                style_id=STYLE_BODY,
                name="XJU Body",
                based_on="Normal",
                q_format=True,
                paragraph_props=style_props(
                    widow_control(False),
                    justification("both"),
                    spacing(after=0, line=360),
                    indent(first_line_chars=200, first_line=480),
                ),
                run_props=style_props(
                    run_fonts(ascii="Times New Roman", hansi="Times New Roman", eastasia="宋体"),
                    kern(2),
                    run_size(24),
                ),
            ),
            StyleSpec(
                style_id=STYLE_HEADING_1,
                name="XJU Heading 1",
                based_on="Normal",
                next_style="Normal",
                q_format=True,
                paragraph_props=style_props(
                    "<w:keepNext/>",
                    "<w:keepLines/>",
                    numbering(num_id=1),
                    spacing(before_lines=300, before=720, after_lines=200, after=480, line=288),
                    justification("center"),
                    outline_level(0),
                ),
                run_props=style_props(
                    bold_complex(),
                    snap_to_grid(False),
                    kern(44),
                    run_size(32, complex_size=44),
                ),
            ),
            StyleSpec(
                style_id=STYLE_HEADING_2,
                name="XJU Heading 2",
                based_on=STYLE_HEADING_1,
                next_style="Normal",
                q_format=True,
                paragraph_props=style_props(
                    numbering(level=1),
                    spacing(before_lines=100, before=100, after_lines=50, after=50),
                    justification("both"),
                    outline_level(1),
                ),
                run_props=style_props(bold_complex(False), '<w:sz w:val="30"/>'),
            ),
            StyleSpec(
                style_id=STYLE_HEADING_3,
                name="XJU Heading 3",
                based_on=STYLE_HEADING_2,
                next_style="Normal",
                q_format=True,
                paragraph_props=style_props(
                    numbering(level=2),
                    spacing(before_lines=50, before=50, after_lines=0, after=0),
                    outline_level(2),
                ),
                run_props=style_props(bold_complex(), '<w:sz w:val="28"/>'),
            ),
            StyleSpec(
                style_id=STYLE_FRONT_HEADING,
                name="XJU Front Heading",
                based_on="Normal",
                q_format=True,
                paragraph_props=style_props(
                    justification("center"),
                    spacing(before_lines=300, before=720, after_lines=200, after=480, line=288),
                ),
                run_props=style_props(
                    run_fonts(ascii="黑体", hansi="黑体", eastasia="黑体"),
                    run_size(32),
                ),
            ),
            StyleSpec(
                style_id=STYLE_TOC_FIELD,
                name="XJU TOC Field",
                based_on="Normal",
                paragraph_props=style_props(spacing(after=0, line=288)),
                run_props=style_props(
                    run_fonts(ascii="Times New Roman", hansi="Times New Roman", eastasia="宋体"),
                    run_size(24),
                ),
            ),
            StyleSpec(
                style_id="TOC1",
                name="toc 1",
                based_on="Normal",
                paragraph_props=style_props(
                    tabs(tab("right", 8313, leader="dot")),
                    spacing(after=0, line=288),
                ),
                run_props=style_props(
                    run_fonts(ascii="Times New Roman", hansi="Times New Roman", eastasia="宋体"),
                    run_size(24),
                ),
            ),
            StyleSpec(
                style_id="TOC2",
                name="toc 2",
                based_on="Normal",
                paragraph_props=style_props(
                    tabs(tab("right", 8313, leader="dot")),
                    indent(left=100),
                    spacing(after=0, line=288),
                ),
                run_props=style_props(
                    run_fonts(ascii="Times New Roman", hansi="Times New Roman", eastasia="宋体"),
                    run_size(24),
                ),
            ),
            StyleSpec(
                style_id="TOC3",
                name="toc 3",
                based_on="Normal",
                paragraph_props=style_props(
                    tabs(tab("right", 8313, leader="dot")),
                    indent(left=200),
                    spacing(after=0, line=288),
                ),
                run_props=style_props(
                    run_fonts(ascii="Times New Roman", hansi="Times New Roman", eastasia="宋体"),
                    run_size(24),
                ),
            ),
            StyleSpec(
                style_id=STYLE_HEADER,
                name="XJU Header",
                based_on="Normal",
                paragraph_props=style_props(
                    paragraph_bottom_border(),
                    tabs(tab("center", 4153), tab("right", 8306)),
                    snap_to_grid(False),
                    justification("center"),
                ),
                run_props=style_props(
                    run_fonts(ascii="宋体", hansi="宋体", eastasia="宋体"),
                    run_size(18),
                ),
            ),
            StyleSpec(
                style_id=STYLE_FOOTER,
                name="XJU Footer",
                based_on="Normal",
                paragraph_props=style_props(
                    tabs(tab("center", 4153), tab("right", 8306)),
                    snap_to_grid(False),
                    spacing(line=288),
                    indent(first_line_chars=200, first_line=200),
                    justification("left"),
                ),
                run_props=style_props(
                    run_fonts(ascii="Times New Roman", hansi="Times New Roman", eastasia="宋体"),
                    run_size(18),
                ),
            ),
            StyleSpec(
                style_id=STYLE_CAPTION,
                name="XJU Caption",
                based_on="Normal",
                paragraph_props=style_props(
                    justification("center"),
                    spacing(before_lines=50, before=120, after_lines=50, after=120, line=288),
                    indent(left=0, first_line=0),
                ),
                run_props=style_props(
                    run_fonts(ascii="Times New Roman", hansi="Times New Roman", eastasia="宋体"),
                    bold(),
                    bold_complex(),
                    run_size(21),
                ),
            ),
            StyleSpec(
                style_id=STYLE_REFERENCE,
                name="XJU Reference",
                based_on="Normal",
                paragraph_props=style_props(spacing(line=360)),
                run_props=style_props(
                    run_fonts(ascii="Times New Roman", hansi="Times New Roman", eastasia="宋体"),
                    run_size(21),
                ),
            ),
            StyleSpec(
                style_id=STYLE_QUOTE,
                name="XJU Quote",
                based_on=STYLE_BODY,
                paragraph_props=style_props(
                    indent(left=720),
                    spacing(after=120, line=360),
                ),
                run_props=style_props(italic()),
            ),
            StyleSpec(
                style_id=STYLE_CODE_BLOCK,
                name="XJU Code Block",
                based_on="Normal",
                paragraph_props=style_props(
                    spacing(after=120),
                    shading("clear", "F5F5F5"),
                    outline_level(9),
                ),
                run_props=style_props(
                    run_fonts(ascii="Courier New", hansi="Courier New", eastasia="等线"),
                    run_size(20),
                ),
            ),
            StyleSpec(
                style_id=STYLE_MATH_BLOCK,
                name="XJU Math Block",
                based_on="Normal",
                paragraph_props=style_props(
                    justification("center"),
                    spacing(before=120, after=120, line=360),
                ),
                run_props=style_props(
                    run_fonts(ascii="Cambria Math", hansi="Cambria Math", eastasia="Cambria Math"),
                ),
            ),
            StyleSpec(
                style_id=STYLE_TABLE_TEXT,
                name="XJU Table Text",
                based_on="Normal",
                paragraph_props=style_props(spacing(after=0, line=360)),
                run_props=style_props(
                    run_fonts(ascii="Times New Roman", hansi="Times New Roman", eastasia="宋体"),
                    run_size(21),
                ),
            ),
        ),
    )


def xju_styles_xml() -> str:
    return render_styles_xml(xju_style_catalog())


def xju_style_bundle() -> StyleBundle:
    from .header_footer import empty_footer_xml, empty_header_xml, header_xml, page_footer_xml

    return StyleBundle(
        styles_xml=xju_styles_xml(),
        numbering_xml=xju_numbering_xml(),
        settings_xml=settings_xml(),
        font_table_xml=xju_font_table_xml(),
        header_xml=header_xml(),
        empty_header_xml=empty_header_xml(),
        empty_footer_xml=empty_footer_xml(),
        page_footer_xml=page_footer_xml(),
    )
