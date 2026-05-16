from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SectionSpec:
    with_header: bool = False
    footer_kind: str | None = None
    section_type: str | None = None
    page_number_format: str | None = None
    page_number_start: int | None = None


@dataclass(frozen=True)
class DocumentLayout:
    cover: SectionSpec
    front_matter: SectionSpec
    body_start: SectionSpec
    body_continue: SectionSpec


@dataclass(frozen=True)
class DocxPackageParts:
    content_types: str = "[Content_Types].xml"
    package_rels: str = "_rels/.rels"
    core_props: str = "docProps/core.xml"
    app_props: str = "docProps/app.xml"
    document: str = "word/document.xml"
    styles: str = "word/styles.xml"
    numbering: str = "word/numbering.xml"
    settings: str = "word/settings.xml"
    font_table: str = "word/fontTable.xml"
    header: str = "word/header1.xml"
    empty_header: str = "word/header2.xml"
    empty_footer: str = "word/footer1.xml"
    page_footer: str = "word/footer2.xml"
    document_rels: str = "word/_rels/document.xml.rels"


@dataclass(frozen=True)
class FrontMatterSpec:
    cover_info_key: str
    declaration_key: str | None = None
    declaration_title: str = ""
    taskbook_key: str | None = None
    cn_abstract_key: str | None = None
    cn_abstract_title: str = ""
    cn_keyword_prefix: str = ""
    en_abstract_key: str | None = None
    en_abstract_title: str = ""
    en_keyword_prefix: str = ""
    toc_title: str = ""
    default_title: str = "Untitled"


@dataclass(frozen=True)
class FrontMatterPageSpec:
    kind: str
    source_key: str | None = None
    title: str = ""
    keyword_prefix: str = ""
    english: bool = False
    page_break_before: bool = False
    page_break_after: bool = False


@dataclass(frozen=True)
class FrontMatterPlan:
    pages: tuple[FrontMatterPageSpec, ...]

    def by_kind(self, kind: str) -> tuple[FrontMatterPageSpec, ...]:
        return tuple(page for page in self.pages if page.kind == kind)


@dataclass(frozen=True)
class FrontMatterPlanIssue:
    message: str


def validate_front_matter_plan(
    spec: FrontMatterSpec,
    plan: FrontMatterPlan,
) -> tuple[FrontMatterPlanIssue, ...]:
    issues: list[FrontMatterPlanIssue] = []
    if not plan.pages:
        return (FrontMatterPlanIssue("front matter plan is empty"),)

    if plan.pages[0].kind != "cover":
        issues.append(FrontMatterPlanIssue("front matter plan should start with a cover page"))

    if not plan.by_kind("toc"):
        issues.append(FrontMatterPlanIssue("front matter plan is missing toc page"))

    expected_keys = [
        spec.cover_info_key,
        spec.declaration_key,
        spec.taskbook_key,
        spec.cn_abstract_key,
        spec.en_abstract_key,
    ]
    planned_keys = {page.source_key for page in plan.pages if page.source_key}
    for source_key in expected_keys:
        if source_key and source_key not in planned_keys:
            issues.append(FrontMatterPlanIssue(f"front matter plan is missing source key: {source_key}"))

    for page in plan.pages:
        if page.kind in {"cover", "declaration", "taskbook", "abstract"} and not page.source_key:
            issues.append(FrontMatterPlanIssue(f"front matter {page.kind} page is missing source key"))
        if page.kind == "abstract" and not page.title:
            issues.append(FrontMatterPlanIssue("front matter abstract page is missing title"))

    return tuple(issues)


@dataclass(frozen=True)
class StyleBundle:
    styles_xml: str
    numbering_xml: str
    settings_xml: str
    font_table_xml: str
    header_xml: str
    empty_header_xml: str
    empty_footer_xml: str
    page_footer_xml: str
