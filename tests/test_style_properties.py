from __future__ import annotations

from thesis_md2docx.styles.properties import (
    bold_complex,
    indent,
    justification,
    run_fonts,
    run_size,
    spacing,
    style_props,
    tab,
    tabs,
    widow_control,
)
from thesis_md2docx.profiles.xju_undergraduate_thesis.styles import (
    xju_font_table,
    xju_font_table_xml,
    xju_numbering_catalog,
    xju_numbering_xml,
)


def test_style_property_helpers_render_ooxml_fragments() -> None:
    assert style_props(
        run_fonts(ascii="Times New Roman", hansi="Times New Roman", eastasia="宋体"),
        run_size(24),
    ) == (
        '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体"/>',
        '<w:sz w:val="24"/><w:szCs w:val="24"/>',
    )

    assert style_props(
        widow_control(False),
        justification("both"),
        spacing(after=0, line=360),
        indent(first_line_chars=200, first_line=480),
    ) == (
        '<w:widowControl w:val="0"/>',
        '<w:jc w:val="both"/>',
        '<w:spacing w:after="0" w:line="360" w:lineRule="auto"/>',
        '<w:ind w:firstLineChars="200" w:firstLine="480"/>',
    )


def test_style_property_helpers_preserve_word_specific_details() -> None:
    assert style_props(
        bold_complex(False),
        '<w:sz w:val="30"/>',
        tabs(tab("right", 8313, leader="dot")),
    ) == (
        '<w:bCs w:val="0"/>',
        '<w:sz w:val="30"/>',
        '<w:tabs><w:tab w:val="right" w:leader="dot" w:pos="8313"/></w:tabs>',
    )


def test_xju_numbering_and_font_table_are_structured_specs() -> None:
    numbering = xju_numbering_catalog()
    font_table = xju_font_table()

    assert numbering.abstract_numbers[0].levels[0].text == "%1  "
    assert numbering.instances[0].num_id == 1
    assert font_table.fonts[1].name == "宋体"
    assert font_table.fonts[1].alt_name == "SimSun"
    assert '<w:lvlText w:val="%1.%2.%3"/>' in xju_numbering_xml()
    assert '<w:font w:name="等线"><w:altName w:val="DengXian"/></w:font>' in xju_font_table_xml()
