from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...constants import (
    COVER_EMBLEM_NAME,
    COVER_WORDMARK_NAME,
    DEFAULT_LOCAL_COVER_ASSETS_REL,
    EMU_PER_INCH,
    SIGNATURE_IMAGE_HEIGHT_EMU,
    SIGNATURE_IMAGE_WIDTH_EMU,
)
from ...frontmatter import (
    first_nonempty_value,
    taskbook_display_width,
    taskbook_run_kwargs,
    wrap_taskbook_text,
)
from ...markdown import parse_cover_info, split_cover_title_lines
from ...math.converter import MathConverter
from ...media import MediaImage, MediaManager
from ...ooxml.render import (
    add_page_break_before_paragraph_xml,
    formatted_paragraph_xml,
    image_run_xml,
    paragraph_with_inline_math_xml,
    paragraph_xml,
)
from ...ooxml.xml import indent_xml, run_text_xml, spacing_xml
from .styles import STYLE_BODY, STYLE_FRONT_HEADING


@dataclass(frozen=True)
class CoverFieldSpec:
    source_key: str
    label: str


@dataclass(frozen=True)
class CoverInfoRow:
    label: str
    value: str
    draw_top_border: bool = True


@dataclass(frozen=True)
class TaskbookValueSpec:
    name: str
    taskbook_keys: tuple[str, ...] = ()
    cover_keys: tuple[str, ...] = ()
    default: str = ""

    def resolve(self, task_info: dict[str, str], cover_info: dict[str, str]) -> str:
        values = [task_info.get(key) for key in self.taskbook_keys]
        values.extend(cover_info.get(key) for key in self.cover_keys)
        return first_nonempty_value(*values, default=self.default)


@dataclass(frozen=True)
class DeclarationSignatureSpec:
    author_label: str = "作者签名："
    date_label: str = "签字日期："
    signature_alt: str = "电子签名"
    blank_count_without_image: int = 17
    blank_count_with_image: int = 13

    def blank_count(self, *, has_signature_image: bool) -> int:
        return self.blank_count_with_image if has_signature_image else self.blank_count_without_image


XJU_COVER_FIELDS: tuple[CoverFieldSpec, ...] = (
    CoverFieldSpec("学生姓名", "学生姓名:"),
    CoverFieldSpec("学号", "学    号:"),
    CoverFieldSpec("所属院系", "所属院系:"),
    CoverFieldSpec("专业", "专    业:"),
    CoverFieldSpec("班级", "班    级:"),
    CoverFieldSpec("指导教师", "指导老师:"),
    CoverFieldSpec("日期", "日    期:"),
)


XJU_TASKBOOK_VALUES: tuple[TaskbookValueSpec, ...] = (
    TaskbookValueSpec("college", taskbook_keys=("学院",), cover_keys=("所属院系",)),
    TaskbookValueSpec("class_name", taskbook_keys=("班级",), cover_keys=("班级",)),
    TaskbookValueSpec("student", taskbook_keys=("姓名",), cover_keys=("学生姓名",)),
    TaskbookValueSpec(
        "title",
        taskbook_keys=("毕业论文（设计）题目", "论文题目"),
        cover_keys=("论文题目",),
    ),
    TaskbookValueSpec("year", taskbook_keys=("届",), default="……"),
    TaskbookValueSpec("start_date", taskbook_keys=("工作开始日期", "开始日期")),
    TaskbookValueSpec("end_date", taskbook_keys=("工作结束日期", "结束日期")),
    TaskbookValueSpec("purpose", taskbook_keys=("目的及意义", "题目的目的及意义")),
    TaskbookValueSpec("tasks", taskbook_keys=("主要工作任务", "工作任务")),
    TaskbookValueSpec("teacher", taskbook_keys=("指导教师",), cover_keys=("指导教师",)),
    TaskbookValueSpec("office_head", taskbook_keys=("教研室（系）主任", "教研室主任")),
    TaskbookValueSpec("student_signature", taskbook_keys=("学生签名",)),
    TaskbookValueSpec("accepted_date", taskbook_keys=("接受任务日期", "接受日期")),
)


XJU_DECLARATION_SIGNATURE = DeclarationSignatureSpec()


def _contains_cjk_text(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _xju_english_keyword_example_runs(prefix: str, rest: str, run_kwargs: dict[str, object]) -> list[str] | None:
    if prefix != "英文摘要正文内容下，空一行，左对齐，打印大写的“":
        return None
    expected_rest = (
        "”（小四号Times New Roman加粗），后接冒号，其后每个关键词组的第一个字母大写，"
        "其余为小写，关键词由3～5个组成（小四号Times New Roman），每一关键词之间用分号隔开，"
        "最后一个关键词后无标点符号。例如：Drip irrigation emitter; RP&M; Hydraulics; Labyrinth flow channel"
    )
    if rest != expected_rest:
        return None

    cjk_run = {
        "font_ascii": "宋体",
        "font_hansi": "宋体",
        "font_cs": "宋体",
        "font_hint": "eastAsia",
        "size": 24,
        "size_cs": False,
    }
    hint_run = {**run_kwargs, "font_hint": "eastAsia"}
    no_hint_run = dict(run_kwargs)
    no_hint_run.pop("font_hint", None)

    runs = [
        run_text_xml("英文摘要正文内容下，空一行，左对齐，打印", **cjk_run),
        run_text_xml("大写的", **hint_run),
        run_text_xml("“", bold=True, bold_cs=True, **hint_run),
    ]
    for value, use_hint in (("K", False), ("EY", True), (" W", False), ("ORDS", True)):
        kwargs = dict(run_kwargs)
        if use_hint:
            kwargs["font_hint"] = "eastAsia"
        else:
            kwargs.pop("font_hint", None)
        runs.append(run_text_xml(value, bold=True, bold_cs=True, **kwargs))
    runs.extend(
        [
            run_text_xml("”", **hint_run),
            run_text_xml("（小四号", **cjk_run),
            run_text_xml("Times New Roman", **hint_run),
            run_text_xml("加粗", **hint_run),
            run_text_xml("）", **cjk_run),
            run_text_xml("，", **hint_run),
            run_text_xml("后接冒号，", **cjk_run),
            run_text_xml("其后", **hint_run),
            run_text_xml("每个关键词组的第一个字母大写，其余为小写，", **no_hint_run),
            run_text_xml("关键词由", **cjk_run),
            run_text_xml("3", **cjk_run),
            run_text_xml("～", **cjk_run),
            run_text_xml("5", **cjk_run),
            run_text_xml("个组成（小四号", **cjk_run),
            run_text_xml("Times New Roman", **hint_run),
            run_text_xml("），", **cjk_run),
            run_text_xml("每一关键词之间用分号隔开，最后一个关键词后无标点符号。例如：", **hint_run),
            run_text_xml("Drip irrigation emitter; RP&M; Hydraulics; Labyrinth flow channel", **no_hint_run),
        ]
    )
    return runs


def resolve_taskbook_values(task_info: dict[str, str], cover_info: dict[str, str]) -> dict[str, str]:
    return {spec.name: spec.resolve(task_info, cover_info) for spec in XJU_TASKBOOK_VALUES}


def use_taskbook_cover_fallback(task_info: dict[str, str]) -> bool:
    for key in ("自动补全", "封面自动补全", "使用封面信息"):
        value = task_info.get(key)
        if value is not None:
            return value.strip().lower() not in {"0", "false", "no", "off", "否", "不", "不使用", "关闭"}
    return True


def resolve_cover_assets_dir(markdown_path: Path, assets_dir: Path | None, *, use_cover_assets: bool) -> Path | None:
    if not use_cover_assets:
        return None

    candidates: list[Path] = []
    if assets_dir is not None:
        candidates.append(assets_dir)
    local_assets_dir = markdown_path.parent / DEFAULT_LOCAL_COVER_ASSETS_REL
    if local_assets_dir not in candidates:
        candidates.append(local_assets_dir)

    for candidate in candidates:
        if (candidate / COVER_EMBLEM_NAME).exists() or (candidate / COVER_WORDMARK_NAME).exists():
            return candidate

    return candidates[0] if candidates else None


def cover_logo_group_xml(
    emblem_item: MediaImage | None,
    wordmark_item: MediaImage | None,
    media_manager: MediaManager | None,
) -> str:
    if media_manager is None or emblem_item is None or wordmark_item is None:
        return ""

    docpr_id = media_manager.next_drawing_id()
    emblem_pic_id = media_manager.next_drawing_id()
    wordmark_pic_id = media_manager.next_drawing_id()
    # These coordinates are from the official example's grouped Word drawing.
    # Keeping them as drawing-local EMUs avoids a table-only layout workaround
    # and makes the generated cover closer to the template's object structure.
    return (
        "<w:p><w:r><w:rPr><w:noProof/></w:rPr><w:drawing>"
        '<wp:anchor distT="0" distB="0" distL="114300" distR="114300" '
        'simplePos="0" relativeHeight="251658240" behindDoc="0" locked="0" '
        'layoutInCell="1" allowOverlap="1">'
        '<wp:simplePos x="0" y="0"/>'
        '<wp:positionH relativeFrom="column"><wp:posOffset>925830</wp:posOffset></wp:positionH>'
        '<wp:positionV relativeFrom="paragraph"><wp:posOffset>121285</wp:posOffset></wp:positionV>'
        '<wp:extent cx="3642995" cy="1270000"/>'
        '<wp:effectExtent l="0" t="0" r="0" b="0"/>'
        "<wp:wrapNone/>"
        f'<wp:docPr id="{docpr_id}" name="组合 2"/>'
        "<wp:cNvGraphicFramePr/>"
        "<a:graphic>"
        '<a:graphicData uri="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup">'
        "<wpg:wgp>"
        "<wpg:cNvGrpSpPr/>"
        "<wpg:grpSpPr>"
        '<a:xfrm><a:off x="0" y="0"/><a:ext cx="3642995" cy="1270000"/>'
        '<a:chOff x="4924" y="3838"/><a:chExt cx="5737" cy="2000"/></a:xfrm>'
        "</wpg:grpSpPr>"
        "<pic:pic><pic:nvPicPr>"
        f'<pic:cNvPr id="{emblem_pic_id}" name="图片 1" descr="2019校徽(新)121"/>'
        '<pic:cNvPicPr><a:picLocks noChangeAspect="1"/></pic:cNvPicPr>'
        "</pic:nvPicPr>"
        "<pic:blipFill>"
        f'<a:blip r:embed="{emblem_item.rel_id}" cstate="print">'
        '<a:clrChange><a:clrFrom><a:srgbClr val="FFFFFF"/></a:clrFrom>'
        '<a:clrTo><a:srgbClr val="FFFFFF"><a:alpha val="0"/></a:srgbClr></a:clrTo></a:clrChange>'
        '<a:extLst><a:ext uri="{28A0092B-C50C-407E-A947-70E740481C1C}">'
        '<a14:useLocalDpi val="0"/></a:ext></a:extLst>'
        "</a:blip>"
        "<a:srcRect/><a:stretch><a:fillRect/></a:stretch>"
        "</pic:blipFill>"
        "<pic:spPr>"
        '<a:xfrm><a:off x="4924" y="3868"/><a:ext cx="1859" cy="1859"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln><a:effectLst/>'
        "</pic:spPr></pic:pic>"
        "<pic:pic><pic:nvPicPr>"
        f'<pic:cNvPr id="{wordmark_pic_id}" name="图片 2"/>'
        '<pic:cNvPicPr><a:picLocks noChangeAspect="1"/></pic:cNvPicPr>'
        "</pic:nvPicPr>"
        "<pic:blipFill>"
        f'<a:blip r:embed="{wordmark_item.rel_id}" cstate="print">'
        '<a:clrChange><a:clrFrom><a:srgbClr val="FEFDFD"/></a:clrFrom>'
        '<a:clrTo><a:srgbClr val="FEFDFD"><a:alpha val="0"/></a:srgbClr></a:clrTo></a:clrChange>'
        '<a:extLst><a:ext uri="{28A0092B-C50C-407E-A947-70E740481C1C}">'
        '<a14:useLocalDpi val="0"/></a:ext></a:extLst>'
        "</a:blip>"
        "<a:srcRect/><a:stretch><a:fillRect/></a:stretch>"
        "</pic:blipFill>"
        "<pic:spPr>"
        '<a:xfrm><a:off x="7189" y="3838"/><a:ext cx="3473" cy="2000"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln><a:effectLst/>'
        "</pic:spPr></pic:pic>"
        "</wpg:wgp>"
        "</a:graphicData>"
        "</a:graphic>"
        "</wp:anchor>"
        "</w:drawing></w:r></w:p>"
    )


def cover_info_table_xml(title: str, cover_info: dict[str, str]) -> str:
    title_lines = split_cover_title_lines(title)
    info_rows: list[CoverInfoRow] = []

    if title_lines:
        info_rows.append(CoverInfoRow("论文题目:", title_lines[0], draw_top_border=False))
        for extra_line in title_lines[1:]:
            info_rows.append(CoverInfoRow("", extra_line))

    for field in XJU_COVER_FIELDS:
        value = cover_info.get(field.source_key)
        if value:
            info_rows.append(CoverInfoRow(field.label, value))

    tbl_pr = (
        "<w:tblPr>"
        '<w:tblW w:w="6943" w:type="dxa"/>'
        '<w:jc w:val="center"/>'
        '<w:tblLayout w:type="fixed"/>'
        '<w:tblLook w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:val="04A0"/>'
        "</w:tblPr>"
    )
    tbl_grid = '<w:tblGrid><w:gridCol w:w="1948"/><w:gridCol w:w="4995"/></w:tblGrid>'

    label_run = {
        "font_eastasia": "楷体_GB2312",
        "font_hint": "eastAsia",
        "bold": True,
        "bold_cs": False,
        "size": 32,
    }
    value_run = {
        "font_eastasia": "楷体_GB2312",
        "font_hint": "eastAsia",
        "bold": True,
        "bold_cs": False,
        "size": 32,
    }

    rows_xml: list[str] = []
    for idx, row in enumerate(info_rows):
        label_para = formatted_paragraph_xml(
            row.label,
            align="center" if row.label else None,
            ppr_extra="",
            run_kwargs=label_run,
        )
        value_para = formatted_paragraph_xml(
            row.value,
            align="center",
            ppr_extra="",
            run_kwargs=value_run,
        )
        value_borders = ["<w:tcBorders>"]
        if row.draw_top_border and idx > 0:
            value_borders.append('<w:top w:val="single" w:color="auto" w:sz="4" w:space="0"/>')
        value_borders.append('<w:bottom w:val="single" w:color="auto" w:sz="4" w:space="0"/>')
        value_borders.append("</w:tcBorders>")

        rows_xml.append(
            "<w:tr>"
            '<w:trPr><w:trHeight w:val="680"/></w:trPr>'
            '<w:tc><w:tcPr><w:tcW w:w="1948" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>'
            + label_para
            + "</w:tc>"
            + '<w:tc><w:tcPr><w:tcW w:w="4995" w:type="dxa"/>'
            + "".join(value_borders)
            + '<w:vAlign w:val="center"/></w:tcPr>'
            + value_para
            + "</w:tc>"
            + "</w:tr>"
        )

    return f"<w:tbl>{tbl_pr}{tbl_grid}{''.join(rows_xml)}</w:tbl>"


def build_cover_elements(
    title: str,
    cover_info: dict[str, str],
    *,
    cover_assets_dir: Path | None = None,
    media_manager: MediaManager | None = None,
) -> list[str]:
    elements: list[str] = []
    title_run = {
        "font_ascii": "黑体",
        "font_hansi": "宋体",
        "font_eastasia": "黑体",
        "font_hint": "eastAsia",
    }

    elements.append(
        formatted_paragraph_xml(
            "",
            align="center",
            ppr_extra=spacing_xml(line=600, line_rule="exact"),
            run_kwargs={**title_run, "bold": True, "size": 52},
        )
    )
    elements.append(
        paragraph_xml(
            align="center",
            ppr_extra=spacing_xml(line=600, line_rule="exact"),
            runs=[
                run_text_xml("新疆大学本科毕业论文", **title_run, bold=True, size=52),
                run_text_xml("(", **title_run, bold=True, size=52),
                run_text_xml("设计", **title_run, bold=True, size=52),
                run_text_xml(")", **title_run, bold=True, size=52),
            ],
        )
    )

    emblem_item = None
    wordmark_item = None
    if cover_assets_dir is not None and media_manager is not None:
        emblem_item = media_manager.register_image(cover_assets_dir / COVER_EMBLEM_NAME)
        wordmark_item = media_manager.register_image(cover_assets_dir / COVER_WORDMARK_NAME)

    logo_group = cover_logo_group_xml(emblem_item, wordmark_item, media_manager)
    if logo_group:
        elements.extend("<w:p/>" for _ in range(3))
        elements.append(logo_group)
        elements.extend("<w:p/>" for _ in range(15))
    else:
        elements.append(paragraph_xml(" ", ppr_extra=spacing_xml(after=0, line=480)))
        elements.append(paragraph_xml(" ", ppr_extra=spacing_xml(after=0, line=860, line_rule="atLeast")))
        for _ in range(8):
            elements.append(paragraph_xml(" ", ppr_extra=spacing_xml(after=132, line=360)))

    elements.append(cover_info_table_xml(title, cover_info))

    return elements


def build_front_heading(
    text: str,
    *,
    english: bool = False,
    toc: bool = False,
    statement: bool = False,
    page_break_before: bool = False,
) -> str:
    if toc:
        paragraph = paragraph_xml(
            style="afa",
            ppr_extra=spacing_xml(line=240),
            runs=[
                run_text_xml(
                    "目",
                    font_ascii="黑体",
                    font_hansi="黑体",
                    font_eastasia="黑体",
                    font_cs="黑体",
                    font_hint="eastAsia",
                    size_cs=False,
                ),
                run_text_xml(
                    "  ",
                    font_ascii="黑体",
                    font_hansi="黑体",
                    font_eastasia="黑体",
                    font_cs="黑体",
                    font_hint="eastAsia",
                    size_cs=False,
                ),
                run_text_xml(
                    "录",
                    font_ascii="黑体",
                    font_hansi="黑体",
                    font_eastasia="黑体",
                    font_cs="黑体",
                    font_hint="eastAsia",
                    size_cs=False,
                ),
            ],
        )
        return add_page_break_before_paragraph_xml(paragraph) if page_break_before else paragraph

    if statement:
        run_kwargs = {
            "font_ascii": "黑体",
            "font_hansi": "黑体",
            "font_eastasia": "黑体",
            "font_hint": "eastAsia",
            "size": 32,
        }
        ppr_extra = (
            '<w:snapToGrid w:val="0"/>'
            + spacing_xml(
                before_lines=100,
                before=240,
                after_lines=200,
                after=480,
            )
            + '<w:rPr><w:rFonts w:ascii="黑体" w:hAnsi="黑体" w:eastAsia="黑体" w:hint="eastAsia"/>'
            '<w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr>'
        )
    elif english:
        run_kwargs = {
            "size": 32,
        }
        ppr_extra = (
            spacing_xml(before_lines=300, before=720, after_lines=200, after=480)
            + '<w:rPr><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr>'
        )
    else:
        run_kwargs = {
            "font_ascii": "黑体",
            "font_hansi": "黑体",
            "font_eastasia": "黑体",
            "font_hint": "eastAsia",
            "size": 32,
        }
        ppr_extra = (
            '<w:snapToGrid w:val="0"/>'
            + spacing_xml(
                before_lines=300,
                before=720,
                after_lines=200,
                after=480,
            )
            + '<w:rPr><w:rFonts w:ascii="黑体" w:hAnsi="黑体" w:eastAsia="黑体" w:hint="eastAsia"/>'
            '<w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr>'
        )

    if page_break_before and not statement:
        if english:
            ppr_extra = (
                spacing_xml(before_lines=300, before=720, after_lines=200, after=480)
                + '<w:rPr><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr>'
            )
        else:
            ppr_extra = (
                '<w:snapToGrid w:val="0"/>'
                + spacing_xml(
                    before_lines=300,
                    before=720,
                    after_lines=200,
                    after=480,
                )
                + '<w:rPr><w:rFonts w:ascii="黑体" w:hAnsi="黑体" w:eastAsia="黑体" w:hint="eastAsia"/>'
                '<w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr>'
            )

    if not english and "  " in text:
        runs = [
            run_text_xml(part, **run_kwargs)
            for part in (text[0], text[1:-1], text[-1])
            if part
        ]
        paragraph = paragraph_xml(
            align="center",
            ppr_extra=ppr_extra,
            runs=runs,
        )
    else:
        if english and text == "ABSTRACT":
            paragraph = paragraph_xml(
                align="center",
                ppr_extra=ppr_extra,
                runs=[
                    run_text_xml("ABSTRAC", **run_kwargs),
                    run_text_xml("T", font_hint="eastAsia", **run_kwargs),
                ],
            )
        else:
            paragraph = formatted_paragraph_xml(
                text,
                align="center",
                ppr_extra=ppr_extra,
                run_kwargs=run_kwargs,
            )
    return add_page_break_before_paragraph_xml(paragraph) if page_break_before else paragraph


def build_body_paragraph(
    text: str,
    *,
    english: bool = False,
    math_converter: MathConverter | None = None,
    reference_anchors: dict[str, str] | None = None,
) -> str:
    if english:
        run_kwargs = {
            "size": 24,
            "size_cs": False,
        }
        if _contains_cjk_text(text):
            run_kwargs["font_hint"] = "eastAsia"
        paragraph_mark = '<w:rPr><w:sz w:val="24"/></w:rPr>'
    else:
        run_kwargs = {
            "font_ascii": "宋体",
            "font_hansi": "宋体",
            "font_cs": "宋体",
            "font_hint": "eastAsia",
            "size": 24,
            "size_cs": False,
        }
        paragraph_mark = (
            '<w:rPr><w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:cs="宋体"/>'
            '<w:sz w:val="24"/></w:rPr>'
        )
    ppr_extra = spacing_xml(line=360) + paragraph_mark

    if not english and "**关 键 词**" in text:
        prefix, rest = text.split("**关 键 词**", 1)
        keyword_runs = [
            run_text_xml(
                value,
                bold=True,
                font_ascii="宋体",
                font_hansi="宋体",
                font_cs="黑体",
                font_hint="eastAsia",
                size=24,
                size_cs=False,
            )
            for value in ("关", " ", "键", " ", "词")
        ]
        runs = [
            run_text_xml(prefix, **run_kwargs),
            *keyword_runs,
            run_text_xml(rest, **run_kwargs),
        ]
        return paragraph_xml(
            runs=runs,
            ppr_extra=ppr_extra,
            first_line_chars=200,
            first_line=480,
        )

    if english and "**KEY WORDS**" in text:
        prefix, rest = text.split("**KEY WORDS**", 1)
        runs = _xju_english_keyword_example_runs(prefix, rest, run_kwargs)
        if runs is None:
            runs = [run_text_xml(prefix, **run_kwargs)]
            for value, use_hint in (("K", False), ("EY", True), (" W", False), ("ORDS", True)):
                kwargs = dict(run_kwargs)
                if use_hint:
                    kwargs["font_hint"] = "eastAsia"
                else:
                    kwargs.pop("font_hint", None)
                runs.append(run_text_xml(value, bold=True, bold_cs=True, **kwargs))
            for idx, part in enumerate(rest.split("\n")):
                if idx:
                    runs.append("<w:r><w:br/></w:r>")
                if part:
                    runs.append(run_text_xml(part, **run_kwargs))
        return paragraph_xml(
            runs=runs,
            ppr_extra=ppr_extra,
            first_line_chars=200,
            first_line=480,
        )

    return paragraph_with_inline_math_xml(
        text,
        ppr_extra=ppr_extra,
        first_line_chars=200,
        first_line=480,
        preserve_breaks=True,
        run_kwargs=run_kwargs,
        math_converter=math_converter,
        reference_anchors=reference_anchors,
    )


def build_keyword_paragraph(keywords: str, *, english: bool = False) -> str | None:
    if not keywords:
        return None
    if english:
        runs = [
            run_text_xml(
                "K",
                bold=True,
                size=24,
                size_cs=False,
            ),
            run_text_xml(
                "EY",
                bold=True,
                font_hint="eastAsia",
                size=24,
                size_cs=False,
            ),
            run_text_xml(
                " W",
                bold=True,
                size=24,
                size_cs=False,
            ),
            run_text_xml(
                "ORDS",
                bold=True,
                font_hint="eastAsia",
                size=24,
                size_cs=False,
            ),
            run_text_xml(
                ": ",
                bold=True,
                font_hint="eastAsia",
            ),
        ]
        if keywords == "Xxxx; Xxxx; Xxxx; Xxxx":
            for value in ("X", "xxx", "; ", "Xxxx", "; ", "Xx", "xx", "; ", "Xxxx"):
                runs.append(
                    run_text_xml(
                        value,
                        font_hint="eastAsia",
                        size=24,
                        size_cs=False,
                    )
                )
        else:
            runs.append(
                run_text_xml(
                    keywords,
                    font_hint="eastAsia",
                    size=24,
                    size_cs=False,
                )
            )
    else:
        keyword_prefix_runs = [
            run_text_xml(
                value,
                bold=True,
                font_ascii="宋体",
                font_hansi="宋体",
                font_cs="黑体" if value != "：" else "宋体",
                font_hint="eastAsia",
                size=24,
                size_cs=False,
            )
            for value in ("关", " ", "键", " ", "词", "：")
        ]
        runs = [
            *keyword_prefix_runs,
            run_text_xml(
                keywords,
                font_ascii="宋体",
                font_hansi="宋体",
                font_cs="宋体",
                font_hint="eastAsia",
                size=24,
                size_cs=False,
            ),
        ]
    ppr_extra = spacing_xml(line=360)
    if not english:
        ppr_extra += '<w:rPr><w:sz w:val="24"/></w:rPr>'
    return paragraph_xml(runs=runs, ppr_extra=ppr_extra)


def build_blank_paragraph(*, style: str = STYLE_BODY, line: int = 360, run_size: int | None = None) -> str:
    if run_size is None:
        return paragraph_xml(" ", style=style, ppr_extra=spacing_xml(line=line))
    return formatted_paragraph_xml(
        " ",
        style=style,
        ppr_extra=spacing_xml(line=line),
        run_kwargs={
            "font_ascii": "Times New Roman",
            "font_hansi": "Times New Roman",
            "font_eastasia": "宋体",
            "size": run_size,
        },
    )


def build_statement_body_paragraph(
    text: str,
    *,
    math_converter: MathConverter | None = None,
    reference_anchors: dict[str, str] | None = None,
) -> str:
    run_kwargs = {
        "font_ascii": "Times New Roman",
        "font_hansi": "Times New Roman",
        "font_eastasia": "宋体",
        "size": 28,
    }
    return paragraph_with_inline_math_xml(
        text,
        style=STYLE_BODY,
        ppr_extra=spacing_xml(line=360),
        first_line_chars=200,
        first_line=560,
        run_kwargs=run_kwargs,
        math_converter=math_converter,
        reference_anchors=reference_anchors,
    )


def build_statement_signature_paragraph(
    label: str,
    value: str = "",
    *,
    is_date: bool = False,
    signature_image: MediaImage | None = None,
    media_manager: MediaManager | None = None,
    signature_alt: str = "电子签名",
) -> str:
    normalized = value.strip().strip("_").strip()
    if not normalized:
        normalized = "   年   月   日" if is_date else "\u00a0" * 7
    run_kwargs = {
        "font_ascii": "宋体",
        "font_hansi": "宋体",
        "font_eastasia": "宋体",
        "size": 28,
    }
    ppr_extra = spacing_xml(line=360)
    if not is_date:
        ppr_extra += indent_xml(right=280)
    if signature_image is not None and media_manager is not None:
        runs = [
            run_text_xml(label, **run_kwargs),
            image_run_xml(
                signature_image,
                docpr_id=media_manager.next_drawing_id(),
                alt_text=signature_alt,
                width_emu=SIGNATURE_IMAGE_WIDTH_EMU,
                height_emu=SIGNATURE_IMAGE_HEIGHT_EMU,
            ),
        ]
        return paragraph_xml(runs=runs, align="right", ppr_extra=ppr_extra)
    return formatted_paragraph_xml(
        f"{label}{normalized}",
        align="right",
        ppr_extra=ppr_extra,
        run_kwargs=run_kwargs,
    )


def taskbook_paragraph_rpr(*, underline: bool = False, bold: bool = False, size: int = 24) -> str:
    parts = ['<w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:cs="宋体"/>']
    if bold:
        parts.append("<w:b/>")
    parts.append(f'<w:sz w:val="{size}"/>')
    if size != 24:
        parts.append(f'<w:szCs w:val="{size}"/>')
    if underline:
        parts.append('<w:u w:val="single"/>')
    return f"<w:rPr>{''.join(parts)}</w:rPr>"


def taskbook_underlined_run(value: str = "", *, width: int = 24) -> str:
    text = value.strip()
    padding = " " * max(2, width - taskbook_display_width(text))
    return run_text_xml(text + padding, underline=True, **taskbook_run_kwargs())


def taskbook_line_xml(
    runs: list[str],
    *,
    spacing: str | None = None,
    align: str | None = None,
    snap_to_grid: bool = False,
    ppr_rpr: str = "",
) -> str:
    ppr_extra = ""
    if snap_to_grid:
        ppr_extra += '<w:snapToGrid w:val="0"/>'
    ppr_extra += spacing if spacing is not None else spacing_xml(line=360)
    ppr_extra += ppr_rpr
    return paragraph_xml(
        runs=runs,
        align=align,
        ppr_extra=ppr_extra,
    )


def taskbook_fill_line_xml(value: str, *, width: int = 70, paragraph_underline: bool = True) -> str:
    if not value.strip():
        return taskbook_line_xml(
            [taskbook_underlined_run(value, width=width)],
            spacing=spacing_xml(line=360),
            ppr_rpr=taskbook_paragraph_rpr(underline=paragraph_underline),
        )
    return taskbook_line_xml(
        [taskbook_underlined_run(value, width=width)],
        spacing=spacing_xml(line=360),
    )


def is_taskbook_blank_date(value: str) -> bool:
    normalized = " ".join(value.strip().split())
    return normalized in {"", "年 月 日"}


def taskbook_blank_date_runs() -> list[str]:
    body_run = taskbook_run_kwargs()
    return [
        run_text_xml("  ", underline=True, **body_run),
        run_text_xml("  ", underline=True, **taskbook_run_kwargs(bold=True)),
        run_text_xml("年", **body_run),
        run_text_xml("   ", underline=True, **body_run),
        run_text_xml("月", **body_run),
        run_text_xml("   ", underline=True, **body_run),
    ]


def taskbook_date_runs(value: str) -> list[str]:
    if is_taskbook_blank_date(value):
        return taskbook_blank_date_runs()
    return [taskbook_underlined_run(value, width=11)]


def build_taskbook_elements(taskbook_text: str, cover_info: dict[str, str]) -> list[str]:
    task_info = parse_cover_info(taskbook_text)
    fallback_cover_info = cover_info if use_taskbook_cover_fallback(task_info) else {}
    values = resolve_taskbook_values(task_info, fallback_cover_info)

    body_run = taskbook_run_kwargs()
    title_run = {**taskbook_run_kwargs(bold=True, size=44), "bold_cs": False}
    note_run = taskbook_run_kwargs(size=21)

    elements: list[str] = []
    elements.append(
        formatted_paragraph_xml(
            "新 疆 大 学",
            align="center",
            ppr_extra=spacing_xml(line=360),
            run_kwargs=title_run,
        )
    )
    elements.append(
        formatted_paragraph_xml(
            f"本科毕业论文（设计）任务书（{values['year']}届）",
            align="center",
            ppr_extra="",
            run_kwargs=title_run,
        )
    )
    elements.append(paragraph_xml("", ppr_extra=spacing_xml(line=620)))
    elements.append(
        taskbook_line_xml(
            [
                run_text_xml("学院：", **body_run),
                taskbook_underlined_run(values["college"], width=25),
                run_text_xml(" 班级：", **body_run),
                taskbook_underlined_run(values["class_name"], width=27),
            ]
        )
    )
    elements.append(
        taskbook_line_xml(
            [
                run_text_xml("姓名：", **body_run),
                taskbook_underlined_run(values["student"], width=25),
            ]
        )
    )
    elements.append(
        taskbook_line_xml(
            [
                run_text_xml("毕业论文（设计）题目：", **body_run),
                taskbook_underlined_run(values["title"], width=36),
            ]
        )
    )
    elements.append(
        taskbook_line_xml(
            [
                run_text_xml("毕业设计(论文)工作自", **body_run),
                *taskbook_date_runs(values["start_date"]),
                run_text_xml("日起至", **body_run),
                *taskbook_date_runs(values["end_date"]),
                run_text_xml("日止", **body_run),
            ]
        )
    )
    elements.append(
        formatted_paragraph_xml(
            "毕业设计(论文)题目的目的及意义",
            ppr_extra='<w:snapToGrid w:val="0"/>' + taskbook_paragraph_rpr(),
            run_kwargs=body_run,
        )
    )
    purpose_line_count = 3 if values["purpose"] else 6
    purpose_lines = wrap_taskbook_text(values["purpose"], max_lines=purpose_line_count)
    for index, line in enumerate(purpose_lines):
        elements.append(taskbook_fill_line_xml(line, width=70, paragraph_underline=index < len(purpose_lines) - 1))
    elements.append(
        formatted_paragraph_xml(
            "毕业设计(论文)的主要工作任务",
            ppr_extra='<w:snapToGrid w:val="0"/>' + taskbook_paragraph_rpr(),
            run_kwargs=body_run,
        )
    )
    task_line_count = 4 if values["tasks"] else 6
    task_lines = wrap_taskbook_text(values["tasks"], max_lines=task_line_count)
    for index, line in enumerate(task_lines):
        elements.append(taskbook_fill_line_xml(line, width=70, paragraph_underline=index < len(task_lines) - 1))
    elements.append(paragraph_xml("", ppr_extra='<w:snapToGrid w:val="0"/>' + spacing_xml(line=360) + taskbook_paragraph_rpr()))
    elements.append(
        taskbook_line_xml(
            [run_text_xml("指   导   教  师：", **body_run), taskbook_underlined_run(values["teacher"], width=52)],
            snap_to_grid=True,
            ppr_rpr=taskbook_paragraph_rpr(underline=True),
        )
    )
    elements.append(
        taskbook_line_xml(
            [
                run_text_xml("教研室（系）主任：", **body_run),
                taskbook_underlined_run(values["office_head"], width=52),
            ],
            snap_to_grid=True,
            ppr_rpr=taskbook_paragraph_rpr(),
        )
    )
    elements.append(
        taskbook_line_xml(
            [
                run_text_xml("学   生   签  名：", **body_run),
                taskbook_underlined_run(values["student_signature"], width=52),
            ],
            snap_to_grid=True,
            ppr_rpr=taskbook_paragraph_rpr(),
        )
    )
    elements.append(
        taskbook_line_xml(
            [
                run_text_xml("接受毕业论文(设计)任务日期：", **body_run),
                run_text_xml(" ", **body_run),
                taskbook_underlined_run(values["accepted_date"], width=40),
                run_text_xml(" ", **body_run),
            ],
            snap_to_grid=True,
            ppr_rpr=taskbook_paragraph_rpr(),
        )
    )
    elements.append(paragraph_xml("", ppr_extra=spacing_xml(line=961)))
    elements.append(formatted_paragraph_xml("（注：本任务书由指导教师填写）", ppr_extra="", run_kwargs=note_run))
    return elements
