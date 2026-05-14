from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class DocumentDefaultsSpec:
    run_props: tuple[str, ...] = ()
    paragraph_props: tuple[str, ...] = ()


@dataclass(frozen=True)
class StyleSpec:
    style_id: str
    name: str
    style_type: str = "paragraph"
    default: bool = False
    based_on: str | None = None
    next_style: str | None = None
    q_format: bool = False
    paragraph_props: tuple[str, ...] = ()
    run_props: tuple[str, ...] = ()


@dataclass(frozen=True)
class StyleCatalog:
    defaults: DocumentDefaultsSpec = field(default_factory=DocumentDefaultsSpec)
    styles: tuple[StyleSpec, ...] = ()

    def style_ids(self) -> frozenset[str]:
        return frozenset(style.style_id for style in self.styles)

    def has_style(self, style_id: str) -> bool:
        return style_id in self.style_ids()


@dataclass(frozen=True)
class StyleRoleMap:
    roles: Mapping[str, str] = field(default_factory=dict)

    def get(self, role: str, default: str | None = None) -> str | None:
        return self.roles.get(role, default)

    def require(self, role: str) -> str:
        style_id = self.get(role)
        if style_id is None:
            raise KeyError(f"style role is not defined: {role}")
        return style_id

    def missing_roles(self, required_roles: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(role for role in required_roles if role not in self.roles)

    def missing_styles(self, catalog: StyleCatalog) -> tuple[str, ...]:
        style_ids = catalog.style_ids()
        return tuple(sorted({style_id for style_id in self.roles.values() if style_id not in style_ids}))


@dataclass(frozen=True)
class StyleCatalogIssue:
    message: str


def validate_style_catalog(catalog: StyleCatalog, roles: StyleRoleMap | None = None) -> tuple[StyleCatalogIssue, ...]:
    issues: list[StyleCatalogIssue] = []
    seen: set[str] = set()
    duplicates: set[str] = set()
    for style in catalog.styles:
        if style.style_id in seen:
            duplicates.add(style.style_id)
        seen.add(style.style_id)
    for style_id in sorted(duplicates):
        issues.append(StyleCatalogIssue(f"duplicate style id: {style_id}"))

    style_ids = catalog.style_ids()
    for style in catalog.styles:
        if style.based_on and style.based_on not in style_ids:
            issues.append(StyleCatalogIssue(f"style {style.style_id} is based on missing style: {style.based_on}"))
        if style.next_style and style.next_style not in style_ids:
            issues.append(StyleCatalogIssue(f"style {style.style_id} uses missing next style: {style.next_style}"))

    if roles is not None:
        for role, style_id in sorted(roles.roles.items()):
            if style_id not in style_ids:
                issues.append(StyleCatalogIssue(f"style role {role} points to missing style: {style_id}"))

    return tuple(issues)
