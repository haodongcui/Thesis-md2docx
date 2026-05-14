from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .catalog import StyleCatalog


@dataclass(frozen=True)
class RunFormatSpec:
    font_ascii: str | None = None
    font_hansi: str | None = None
    font_eastasia: str | None = None
    size: int | None = None
    bold: bool = False
    italic: bool = False

    def to_kwargs(self) -> dict[str, object]:
        kwargs: dict[str, object] = {}
        if self.font_ascii is not None:
            kwargs["font_ascii"] = self.font_ascii
        if self.font_hansi is not None:
            kwargs["font_hansi"] = self.font_hansi
        if self.font_eastasia is not None:
            kwargs["font_eastasia"] = self.font_eastasia
        if self.size is not None:
            kwargs["size"] = self.size
        if self.bold:
            kwargs["bold"] = True
        if self.italic:
            kwargs["italic"] = True
        return kwargs


@dataclass(frozen=True)
class ParagraphFormatSpec:
    ppr_extra: str = ""
    first_line_chars: int | None = None
    first_line: int | None = None


@dataclass(frozen=True)
class BodyStyleRefs:
    title: str | None = None
    normal: str | None = None
    heading1: str | None = None
    heading2: str | None = None
    heading3: str | None = None
    quote: str | None = None
    code: str | None = None
    math: str | None = None
    caption: str | None = None
    table_cell: str | None = None

    def style_ids(self) -> frozenset[str]:
        return frozenset(
            style_id
            for style_id in (
                self.title,
                self.normal,
                self.heading1,
                self.heading2,
                self.heading3,
                self.quote,
                self.code,
                self.math,
                self.caption,
                self.table_cell,
            )
            if style_id
        )


@dataclass(frozen=True)
class BodyRenderProfile:
    styles: BodyStyleRefs = field(default_factory=BodyStyleRefs)
    normal_paragraph: ParagraphFormatSpec = field(default_factory=ParagraphFormatSpec)
    normal_run: RunFormatSpec | None = None
    code_paragraph: ParagraphFormatSpec = field(default_factory=ParagraphFormatSpec)
    strip_heading_numbers: bool = False
    heading_builder: Callable[..., str] | None = None
    acknowledgement_heading_builder: Callable[..., str] | None = None
    caption_builder: Callable[..., str] | None = None
    reference_builder: Callable[..., str] | None = None
    table_builder: Callable[..., str] | None = None
    appendix_heading_normalizer: Callable[[str, int], str] | None = None
    appendix_reference_normalizer: Callable[[str, int], str] | None = None
    section_pr_builder: Callable[..., str] | None = None

    def missing_styles(self, catalog: StyleCatalog) -> tuple[str, ...]:
        catalog_ids = catalog.style_ids()
        return tuple(sorted(style_id for style_id in self.styles.style_ids() if style_id not in catalog_ids))

    def missing_hooks(self) -> tuple[str, ...]:
        missing: list[str] = []
        for name in (
            "heading_builder",
            "acknowledgement_heading_builder",
            "caption_builder",
            "reference_builder",
            "appendix_heading_normalizer",
            "appendix_reference_normalizer",
            "section_pr_builder",
        ):
            if getattr(self, name) is None:
                missing.append(name)
        return tuple(missing)


@dataclass(frozen=True)
class BodyRenderProfileIssue:
    message: str


def validate_body_render_profile(
    profile: BodyRenderProfile,
    catalog: StyleCatalog,
) -> tuple[BodyRenderProfileIssue, ...]:
    issues: list[BodyRenderProfileIssue] = []
    for style_id in profile.missing_styles(catalog):
        issues.append(BodyRenderProfileIssue(f"body render profile points to missing style: {style_id}"))
    for hook_name in profile.missing_hooks():
        issues.append(BodyRenderProfileIssue(f"body render profile is missing hook: {hook_name}"))
    return tuple(issues)
