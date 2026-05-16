from __future__ import annotations

from thesis_md2docx.ir import (
    FigureRowBlock,
    HeadingBlock,
    ImageBlock,
    MathBlock,
    ParagraphBlock,
    TableBlock,
    TableSplitBlock,
)
from thesis_md2docx.parser import parse_body_blocks
from thesis_md2docx.profiles.xju_undergraduate_thesis.body import body_parse_rules


def test_parse_body_blocks_builds_document_ir() -> None:
    text = """# 1 绪论
第一行
第二行

<!-- thesis-table-split: 2 -->

表 1-1 示例表

| 列A | 列B |
| --- | --- |
| a | b |

![示例图](img/demo.png)

:::figure-row
![A](img/a.png)
![B](img/b.png)
:::

$$
x + y
$$
"""

    blocks = parse_body_blocks(text, rules=body_parse_rules())

    assert isinstance(blocks[0], HeadingBlock)
    assert blocks[0].raw_level == 1
    assert blocks[0].text == "1 绪论"

    assert isinstance(blocks[1], ParagraphBlock)
    assert blocks[1].text == "第一行第二行"

    assert isinstance(blocks[2], TableSplitBlock)
    assert blocks[2].spec == "2"

    assert isinstance(blocks[3], ParagraphBlock)
    assert blocks[3].text == "表 1-1 示例表"

    assert isinstance(blocks[4], TableBlock)
    assert [[cell.text for cell in row] for row in blocks[4].rows] == [["列A", "列B"], ["a", "b"]]

    assert isinstance(blocks[5], ImageBlock)
    assert blocks[5].target == "img/demo.png"
    assert blocks[5].alt_text == "示例图"

    assert isinstance(blocks[6], FigureRowBlock)
    assert [image.target for image in blocks[6].images] == ["img/a.png", "img/b.png"]

    assert isinstance(blocks[7], MathBlock)
    assert blocks[7].text == "x + y"


def test_parse_body_blocks_supports_rich_table_options_and_spans() -> None:
    text = """::: table {caption="表 1-2 方弯管内流动最大速度比较" width=8529 width_type=dxa widths=2251,1546,1548,1547,1637 top_border=18 bottom_border=18 header_rows=2}
| 项目 {rowspan=2} | 层流 {colspan=2} | 紊流 {colspan=2} |
| 0°截面 | 90°截面 | 0°截面 | 90°截面 |
| 理论值 | 0.04 | 0.03 | 1.30 | 1.25 |
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
    assert blocks[0].rows[0][1].text == "层流"
    assert blocks[0].rows[0][1].colspan == 2
    assert blocks[0].rows[1][0].header
    assert not blocks[0].rows[2][0].header
