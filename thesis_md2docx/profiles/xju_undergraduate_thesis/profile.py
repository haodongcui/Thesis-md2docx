from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...body_rules import BodyParseRules
from ...constants import DEFAULT_COVER_ASSETS_DIR
from ...layout import DocumentLayout, FrontMatterSpec, SectionSpec, StyleBundle
from ...math.converter import MathConverter
from ...media import MediaManager
from ...ooxml.parts import native_sect_pr_xml
from ...styles import BodyRenderProfile, StyleCatalog, StyleRoleMap
from ..base import ThesisProfile
from .body import body_parse_rules, body_style_profile
from .document import build_document as build_profile_document
from .frontmatter import resolve_cover_assets_dir
from .styles import xju_style_bundle, xju_style_catalog, xju_style_roles


@dataclass(frozen=True)
class XjuUndergraduateThesisProfile(ThesisProfile):
    name: str = "xju-undergraduate-thesis"
    display_name: str = "Xinjiang University undergraduate thesis"
    default_cover_assets_dir: Path | None = DEFAULT_COVER_ASSETS_DIR

    def resolve_cover_assets_dir(
        self,
        markdown_path: Path,
        assets_dir: Path | None,
        *,
        use_cover_assets: bool,
    ) -> Path | None:
        return resolve_cover_assets_dir(
            markdown_path,
            assets_dir or self.default_cover_assets_dir,
            use_cover_assets=use_cover_assets,
        )

    def body_style_profile(self) -> BodyRenderProfile:
        return body_style_profile()

    def body_parse_rules(self) -> BodyParseRules:
        return body_parse_rules()

    def document_layout(self) -> DocumentLayout:
        return DocumentLayout(
            cover=SectionSpec(with_header=True, footer_kind="empty", section_type="continuous"),
            front_matter=SectionSpec(
                with_header=True,
                footer_kind="page",
                section_type="nextPage",
                page_number_format="upperRoman",
                page_number_start=1,
            ),
            body_start=SectionSpec(
                with_header=True,
                footer_kind="page",
                page_number_format="decimal",
                page_number_start=1,
            ),
            body_continue=SectionSpec(with_header=True, footer_kind="page"),
        )

    def front_matter_spec(self) -> FrontMatterSpec:
        return FrontMatterSpec(
            cover_info_key="封面信息",
            declaration_key="声明",
            declaration_title="声  明",
            taskbook_key="任务书",
            cn_abstract_key="摘要",
            cn_abstract_title="摘  要",
            cn_keyword_prefix="关键词：",
            en_abstract_key="ABSTRACT",
            en_abstract_title="ABSTRACT",
            en_keyword_prefix="KEY WORDS:",
            toc_title="目  录",
            default_title="新疆大学本科毕业论文",
        )

    def section_from_spec(self, spec: SectionSpec) -> str:
        return native_sect_pr_xml(
            with_header=spec.with_header,
            footer_kind=spec.footer_kind,
            section_type=spec.section_type,
            page_number_format=spec.page_number_format,
            page_number_start=spec.page_number_start,
        )

    def style_catalog(self) -> StyleCatalog:
        return xju_style_catalog()

    def style_roles(self) -> StyleRoleMap:
        return xju_style_roles()

    def style_bundle(self) -> StyleBundle:
        return xju_style_bundle()

    def build_document(
        self,
        text: str,
        *,
        math_converter: MathConverter | None = None,
        reference_anchors: dict[str, str] | None = None,
        markdown_dir: Path | None = None,
        cover_assets_dir: Path | None = None,
        media_manager: MediaManager | None = None,
    ) -> tuple[list[str], str, str]:
        return build_profile_document(
            text,
            thesis_profile=self,
            math_converter=math_converter,
            reference_anchors=reference_anchors,
            markdown_dir=markdown_dir,
            cover_assets_dir=cover_assets_dir,
            media_manager=media_manager,
        )
