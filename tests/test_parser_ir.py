from __future__ import annotations

from thesis_md2docx.ir import (
    BlankBlock,
    FigureRowBlock,
    HeadingBlock,
    ImageBlock,
    MathBlock,
    ParagraphBlock,
    TableBlock,
    TableSplitBlock,
)
from thesis_md2docx.builders.document import build_document_elements
from thesis_md2docx.profiles.xju_undergraduate_thesis.body import body_style_profile
from thesis_md2docx.parser import parse_body_blocks
from thesis_md2docx.profiles.xju_undergraduate_thesis.body import body_parse_rules


def test_parse_body_blocks_builds_document_ir() -> None:
    text = """# 1 绪论
<!-- thesis-p: style=none align=center line=360 first_line=0 run=none -->
第一行
第二行

<!-- thesis-table-split: 2 -->

表 1-1 示例表

| 列A | 列B |
| --- | --- |
| a | b |

![示例图](img/demo.png){width_emu=1200 height_emu=800 crop_bottom=7802 p_style=af9 align=none line=360 before=120 after=120 keep_next=false}

:::figure-row
![A](img/a.png)
![B](img/b.png)
:::

$$
x + y
$$

$$ {image=img/formula.wmf image_alt="公式 1-1" image_mode=vml width_emu=750570 height_emu=284480 first_line=3840 first_line_chars=1600 position=-32 include_shapetype=true}
q = k_d H^x
$$
"""

    blocks = parse_body_blocks(text, rules=body_parse_rules())

    assert isinstance(blocks[0], HeadingBlock)
    assert blocks[0].raw_level == 1
    assert blocks[0].text == "1 绪论"

    assert isinstance(blocks[1], ParagraphBlock)
    assert blocks[1].text == "第一行第二行"
    assert blocks[1].options == {
        "style": "none",
        "align": "center",
        "line": "360",
        "first_line": "0",
        "run": "none",
    }

    assert isinstance(blocks[2], TableSplitBlock)
    assert blocks[2].spec == "2"

    assert isinstance(blocks[3], ParagraphBlock)
    assert blocks[3].text == "表 1-1 示例表"

    assert isinstance(blocks[4], TableBlock)
    assert [[cell.text for cell in row] for row in blocks[4].rows] == [["列A", "列B"], ["a", "b"]]

    assert isinstance(blocks[5], ImageBlock)
    assert blocks[5].target == "img/demo.png"
    assert blocks[5].alt_text == "示例图"
    assert blocks[5].width_emu == 1200
    assert blocks[5].height_emu == 800
    assert blocks[5].crop_bottom == 7802
    assert blocks[5].options == {
        "width_emu": "1200",
        "height_emu": "800",
        "crop_bottom": "7802",
        "p_style": "af9",
        "align": "none",
        "line": "360",
        "before": "120",
        "after": "120",
        "keep_next": "false",
    }

    assert isinstance(blocks[6], FigureRowBlock)
    assert [image.target for image in blocks[6].images] == ["img/a.png", "img/b.png"]

    assert isinstance(blocks[7], MathBlock)
    assert blocks[7].text == "x + y"

    assert isinstance(blocks[8], MathBlock)
    assert blocks[8].text == "q = k_d H^x"
    assert blocks[8].image == "img/formula.wmf"
    assert blocks[8].image_alt == "公式 1-1"
    assert blocks[8].image_width_emu == 750570
    assert blocks[8].image_height_emu == 284480
    assert blocks[8].image_mode == "vml"
    assert blocks[8].image_first_line == 3840
    assert blocks[8].image_first_line_chars == 1600
    assert blocks[8].image_position == -32
    assert blocks[8].image_include_shapetype


def test_parse_body_blocks_preserves_explicit_markdown_line_breaks() -> None:
    text = "第一行  \n第二行\\\n第三行\n第四行"

    blocks = parse_body_blocks(text, rules=body_parse_rules())

    assert len(blocks) == 1
    assert isinstance(blocks[0], ParagraphBlock)
    assert blocks[0].text == "第一行\n第二行\n第三行第四行"


def test_parse_body_blocks_supports_explicit_blank_paragraphs() -> None:
    text = "表后文字\n\n<!-- thesis-blank: line=360 count=2 -->\n\n样例："

    blocks = parse_body_blocks(text, rules=body_parse_rules())

    assert len(blocks) == 3
    assert isinstance(blocks[1], BlankBlock)
    assert blocks[1].options == {"line": "360", "count": "2"}

    elements, _, _ = build_document_elements(
        text,
        profile=body_style_profile(),
        rules=body_parse_rules(),
        treat_first_heading_as_title=False,
    )

    blank_elements = [element for element in elements if element == '<w:p><w:pPr><w:spacing w:line="360" w:lineRule="auto"/></w:pPr></w:p>']
    assert len(blank_elements) == 2


def test_parse_body_blocks_supports_rich_table_options_and_spans() -> None:
    text = """::: table {caption="表 1-2 方弯管内流动最大速度比较" width=8529 width_type=dxa widths=2251,1546,1548,1547,1637 top_border=18 bottom_border=18 header_rows=2}
| 项目 {rowspan=2 continue_left=44 continue_first_line=1764 continue_first_line_chars=840} | 层流 {colspan=2} | 紊流 {colspan=2} |
| 0°截面 {bold_cs=false} | 90°截面 | 0°截面 | 90°截面 |
| 理论值 | 0.04 {style=10 font_size=21 font_size_cs=false first_line=omit} | 0.03 | 1.30 | 1.25 |
:::
"""

    blocks = parse_body_blocks(text, rules=body_parse_rules())

    assert len(blocks) == 1
    assert isinstance(blocks[0], TableBlock)
    assert blocks[0].options["caption"] == "表 1-2 方弯管内流动最大速度比较"
    assert blocks[0].options["width"] == "8529"
    assert blocks[0].options["width_type"] == "dxa"
    assert blocks[0].rows[0][0].text == "项目"
    assert blocks[0].rows[0][0].header
    assert blocks[0].rows[0][0].rowspan == 2
    assert blocks[0].rows[0][0].continue_left == 44
    assert blocks[0].rows[0][0].continue_first_line == 1764
    assert blocks[0].rows[0][0].continue_first_line_chars == 840
    assert blocks[0].rows[0][1].text == "层流"
    assert blocks[0].rows[0][1].colspan == 2
    assert blocks[0].rows[1][0].header
    assert blocks[0].rows[1][0].bold_cs is False
    assert not blocks[0].rows[2][0].header
    assert blocks[0].rows[2][1].style == "10"
    assert blocks[0].rows[2][1].font_size == 21
    assert blocks[0].rows[2][1].font_size_cs is False
    assert blocks[0].rows[2][1].omit_first_line


def test_xju_acknowledgement_heading_uses_page_break_not_section_break() -> None:
    elements, has_sections, _ = build_document_elements(
        """# 参考文献
[1] 示例.

---

# 致谢
致谢正文。

---

# 附录
附录正文。
""",
        profile=body_style_profile(),
        rules=body_parse_rules(),
        treat_first_heading_as_title=False,
    )

    acknowledgement_index = next(i for i, element in enumerate(elements) if "致  谢" in element)
    appendix_index = next(i for i, element in enumerate(elements) if "附  录" in element)

    assert has_sections
    assert "<w:br w:type=\"page\"/>" in elements[acknowledgement_index - 1]
    assert "<w:sectPr>" not in elements[acknowledgement_index - 1]
    assert "<w:sectPr>" in elements[appendix_index - 1]
