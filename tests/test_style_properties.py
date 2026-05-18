from __future__ import annotations

from pathlib import Path

from thesis_md2docx.media import MediaImage, MediaManager
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
from thesis_md2docx.ooxml.text import text_runs
from thesis_md2docx.profiles.xju_undergraduate_thesis.body import figure_image_paragraph_xml, special_body_paragraph_xml
from thesis_md2docx.profiles.xju_undergraduate_thesis.styles import (
    xju_font_table,
    xju_font_table_xml,
    xju_numbering_catalog,
    xju_numbering_xml,
    xju_styles_xml,
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


def test_text_runs_support_word_symbol_tokens() -> None:
    runs = text_runs(
        "0{{sym:Times New Roman:0000}}截面 *V{{sub:max}}*/m{{sup:-3}}",
        run_kwargs={"bold_cs": False},
    )

    assert runs == [
        "<w:r><w:t>0</w:t></w:r>",
        '<w:r><w:sym w:font="Times New Roman" w:char="0000"/></w:r>',
        '<w:r><w:t xml:space="preserve">截面 </w:t></w:r>',
        '<w:r><w:rPr><w:i/><w:iCs/></w:rPr><w:t>V</w:t></w:r>',
        '<w:r><w:rPr><w:i/><w:iCs/><w:vertAlign w:val="subscript"/></w:rPr><w:t>max</w:t></w:r>',
        "<w:r><w:t>/m</w:t></w:r>",
        '<w:r><w:rPr><w:vertAlign w:val="superscript"/></w:rPr><w:t>-3</w:t></w:r>',
    ]


def test_xju_numbering_and_font_table_are_structured_specs() -> None:
    numbering = xju_numbering_catalog()
    font_table = xju_font_table()

    assert numbering.abstract_numbers[0].levels[0].text == "%1  "
    assert numbering.instances[0].num_id == 1
    assert font_table.fonts[1].name == "宋体"
    assert font_table.fonts[1].alt_name == "SimSun"
    assert '<w:lvlText w:val="%1.%2.%3"/>' in xju_numbering_xml()
    assert '<w:font w:name="等线"><w:altName w:val="DengXian"/></w:font>' in xju_font_table_xml()


def test_xju_styles_include_reference_template_caption_styles() -> None:
    styles = xju_styles_xml()

    assert '<w:style w:type="paragraph" w:styleId="af9">' in styles
    assert '<w:name w:val="图表题注"/>' in styles
    assert '<w:style w:type="character" w:styleId="af5">' in styles


def test_xju_special_body_labels_match_reference_paragraph_marks() -> None:
    table_label = special_body_paragraph_xml("表：")
    formula_label = special_body_paragraph_xml("公式：")
    example_label = special_body_paragraph_xml("范例：")

    assert table_label is not None
    assert '<w:ind w:firstLine="482"/>' in table_label
    assert '<w:rPr><w:b/><w:sz w:val="24"/></w:rPr>' in table_label
    assert "<w:bCs/>" not in table_label

    assert formula_label is not None
    assert '<w:ind w:firstLineChars="200" w:firstLine="482"/>' in formula_label
    assert '<w:rPr><w:b/><w:sz w:val="24"/></w:rPr>' in formula_label

    assert example_label is not None
    assert '<w:ind w:firstLine="480"/>' in example_label
    assert '<w:rPr><w:sz w:val="24"/></w:rPr>' in example_label


def test_xju_figure_image_paragraph_options_are_explicit() -> None:
    item = MediaImage(
        source_path=Path("figure.jpeg"),
        filename="image1.jpeg",
        part_name="media/image1.jpeg",
        rel_id="rId1",
        content_type="image/jpeg",
        width_emu=100,
        height_emu=100,
    )
    xml = figure_image_paragraph_xml(
        item,
        MediaManager(),
        options={"p_style": "af9", "align": "none", "line": "360", "before": "120", "after": "120", "keep_next": "false"},
    )

    assert '<w:pStyle w:val="af9"/>' in xml
    assert '<w:jc ' not in xml
    assert '<w:spacing w:before="120" w:after="120" w:line="360" w:lineRule="auto"/>' in xml
    assert "<w:keepNext/>" not in xml
