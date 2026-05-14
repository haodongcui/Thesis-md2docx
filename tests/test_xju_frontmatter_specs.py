from __future__ import annotations

from thesis_md2docx.profiles.xju_undergraduate_thesis.frontmatter import (
    XJU_COVER_FIELDS,
    XJU_DECLARATION_SIGNATURE,
    XJU_TASKBOOK_VALUES,
    cover_info_table_xml,
    resolve_taskbook_values,
)


def test_xju_cover_field_specs_preserve_template_labels() -> None:
    assert [(field.source_key, field.label) for field in XJU_COVER_FIELDS] == [
        ("学生姓名", "学生姓名:"),
        ("学号", "学    号:"),
        ("所属院系", "所属院系:"),
        ("专业", "专    业:"),
        ("班级", "班    级:"),
        ("指导教师", "指导老师:"),
        ("日期", "日    期:"),
    ]

    xml = cover_info_table_xml("题目", {"学生姓名": "张三", "指导教师": "李四"})
    assert "学生姓名:" in xml
    assert "指导老师:" in xml
    assert "张三" in xml
    assert "李四" in xml


def test_xju_taskbook_value_specs_define_fallback_order() -> None:
    assert [spec.name for spec in XJU_TASKBOOK_VALUES] == [
        "college",
        "class_name",
        "student",
        "title",
        "year",
        "start_date",
        "end_date",
        "purpose",
        "tasks",
        "teacher",
        "office_head",
        "student_signature",
        "accepted_date",
    ]

    values = resolve_taskbook_values(
        {
            "论文题目": "任务书题目",
            "开始日期": "2026-01-01",
            "结束日期": "2026-04-30",
            "教研室主任": "王五",
        },
        {
            "所属院系": "软件学院",
            "班级": "软件2201",
            "学生姓名": "张三",
            "论文题目": "封面题目",
            "指导教师": "李四",
        },
    )

    assert values["college"] == "软件学院"
    assert values["class_name"] == "软件2201"
    assert values["student"] == "张三"
    assert values["title"] == "任务书题目"
    assert values["teacher"] == "李四"
    assert values["office_head"] == "王五"
    assert values["year"] == "……"


def test_xju_declaration_signature_spec_preserves_spacing_rule() -> None:
    assert XJU_DECLARATION_SIGNATURE.author_label == "作者签名："
    assert XJU_DECLARATION_SIGNATURE.date_label == "签字日期："
    assert XJU_DECLARATION_SIGNATURE.signature_alt == "电子签名"
    assert XJU_DECLARATION_SIGNATURE.blank_count(has_signature_image=False) == 14
    assert XJU_DECLARATION_SIGNATURE.blank_count(has_signature_image=True) == 10
