from __future__ import annotations

from thesis_md2docx.layout import DocxPackageParts, validate_front_matter_plan
from thesis_md2docx.profiles.xju_undergraduate_thesis import XjuUndergraduateThesisProfile
from thesis_md2docx.profiles.xju_undergraduate_thesis.styles import xju_style_catalog, xju_style_roles
from thesis_md2docx.styles import BodyRenderProfile, StyleRole, validate_body_render_profile, validate_style_catalog


def test_xju_profile_exposes_front_matter_and_layout_specs() -> None:
    profile = XjuUndergraduateThesisProfile()
    front = profile.front_matter_spec()
    plan = profile.front_matter_plan()
    layout = profile.document_layout()

    assert front.cover_info_key == "封面信息"
    assert front.declaration_key == "声明"
    assert front.taskbook_key == "任务书"
    assert front.cn_abstract_key == "摘要"
    assert front.en_abstract_key == "ABSTRACT"
    assert front.toc_title == "目  录"

    assert [page.kind for page in plan.pages] == [
        "cover",
        "declaration",
        "taskbook",
        "abstract",
        "abstract",
        "toc",
    ]
    assert plan.pages[1].source_key == "声明"
    assert plan.pages[1].page_break_after is True
    assert plan.pages[3].title == "摘  要"
    assert plan.pages[3].keyword_prefix == "关键词："
    assert plan.pages[4].title == "ABSTRACT"
    assert plan.pages[4].english is True
    assert plan.by_kind("abstract") == (plan.pages[3], plan.pages[4])
    assert validate_front_matter_plan(front, plan) == ()

    assert layout.cover.footer_kind == "empty"
    assert layout.cover.section_type == "oddPage"
    assert layout.front_matter.page_number_format == "upperRoman"
    assert layout.front_matter.page_number_start == 1
    assert layout.body_start.page_number_format == "decimal"
    assert layout.body_start.page_number_start == 1


def test_xju_profile_exposes_docx_parts_and_style_bundle() -> None:
    profile = XjuUndergraduateThesisProfile()

    assert profile.package_parts() == DocxPackageParts()

    bundle = profile.style_bundle()
    assert "XJU Body" in bundle.styles_xml
    assert "<w:numbering" in bundle.numbering_xml
    assert "<w:settings" in bundle.settings_xml
    assert "新疆大学本科毕业论文（设计）" in bundle.header_xml


def test_xju_style_roles_point_to_declared_word_styles() -> None:
    profile = XjuUndergraduateThesisProfile()
    catalog = profile.style_catalog()
    roles = profile.style_roles()

    assert roles.require(StyleRole.BODY_NORMAL) == "XjuBody"
    assert roles.require(StyleRole.BODY_HEADING_LEVEL1) == "XjuHeading1"
    assert roles.require(StyleRole.REFERENCE_ITEM) == "XjuReference"
    assert roles.missing_roles(profile.required_style_roles()) == ()
    assert roles.missing_styles(catalog) == ()
    assert xju_style_catalog() == catalog
    assert xju_style_roles() == roles
    assert validate_style_catalog(catalog, roles) == ()


def test_xju_body_render_profile_is_typed_and_validated() -> None:
    profile = XjuUndergraduateThesisProfile()
    body_profile = profile.body_style_profile()

    assert isinstance(body_profile, BodyRenderProfile)
    assert body_profile.styles.normal == "XjuBody"
    assert body_profile.styles.heading1 == "XjuHeading1"
    assert body_profile.styles.table_cell == "XjuTableText"
    assert body_profile.normal_paragraph.first_line_chars == 200
    assert body_profile.normal_run is not None
    assert body_profile.normal_run.to_kwargs()["font_eastasia"] == "宋体"
    assert body_profile.missing_hooks() == ()
    assert validate_body_render_profile(body_profile, profile.style_catalog()) == ()
