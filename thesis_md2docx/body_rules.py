from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Pattern


@dataclass(frozen=True)
class BodyParseRules:
    """Profile-level rules used while mapping Markdown blocks to thesis parts."""

    reference_heading: str | None = None
    acknowledgement_heading: str | None = None
    acknowledgement_display_text: str | None = None
    appendix_heading: str | None = None
    appendix_display_text: str | None = None
    appendix_item_level: int = 2
    appendix_child_headings_unnumbered: bool = True
    appendix_formula_scope_prefix: str = "Appendix"
    unnumbered_headings: frozenset[str] = field(default_factory=frozenset)
    skip_reference_paragraph_prefixes: tuple[str, ...] = ()
    reference_entry_pattern: Pattern[str] | None = None
    caption_pattern: Pattern[str] | None = None
    caption_excluded_marks: tuple[str, ...] = ("。", "．")
    table_caption_prefixes: tuple[str, ...] = ()
    table_split_pattern: Pattern[str] | None = None
    table_split_spec_group: str = "spec"
    figure_row_start_pattern: Pattern[str] | None = None
    figure_row_end_pattern: Pattern[str] | None = None
    chapter_number_pattern: Pattern[str] | None = None

    def is_reference_heading(self, text: str) -> bool:
        return self.reference_heading is not None and text == self.reference_heading

    def is_acknowledgement_heading(self, text: str) -> bool:
        return self.acknowledgement_heading is not None and text == self.acknowledgement_heading

    def display_heading_text(self, text: str) -> str:
        if self.is_acknowledgement_heading(text) and self.acknowledgement_display_text:
            return self.acknowledgement_display_text
        if self.is_appendix_heading(text) and self.appendix_display_text:
            return self.appendix_display_text
        return text

    def is_appendix_heading(self, text: str) -> bool:
        return self.appendix_heading is not None and text == self.appendix_heading

    def is_appendix_item_heading(self, raw_level: int) -> bool:
        return self.appendix_heading is not None and raw_level == self.appendix_item_level

    def is_unnumbered_heading(self, text: str, *, in_appendix: bool, level: int) -> bool:
        if text in self.unnumbered_headings:
            return True
        return bool(in_appendix and self.appendix_child_headings_unnumbered and level >= self.appendix_item_level)

    def should_skip_reference_paragraph(self, text: str) -> bool:
        return any(text.startswith(prefix) for prefix in self.skip_reference_paragraph_prefixes)

    def is_reference_entry(self, text: str) -> bool:
        return bool(self.reference_entry_pattern and self.reference_entry_pattern.match(text))

    def is_caption_paragraph(self, text: str) -> bool:
        candidate = text.strip()
        if not self.caption_pattern or not self.caption_pattern.match(candidate):
            return False
        return not any(mark in candidate for mark in self.caption_excluded_marks)

    def is_table_caption(self, text: str) -> bool:
        candidate = text.lstrip()
        return any(candidate.startswith(prefix) for prefix in self.table_caption_prefixes)

    def match_table_split(self, text: str) -> re.Match[str] | None:
        if not self.table_split_pattern:
            return None
        return self.table_split_pattern.match(text)

    def table_split_spec(self, text: str) -> str | None:
        match = self.match_table_split(text)
        if not match:
            return None
        try:
            return match.group(self.table_split_spec_group)
        except IndexError:
            return match.group(1) if match.groups() else None

    def is_figure_row_start(self, text: str) -> bool:
        return bool(self.figure_row_start_pattern and self.figure_row_start_pattern.match(text))

    def is_figure_row_end(self, text: str) -> bool:
        return bool(self.figure_row_end_pattern and self.figure_row_end_pattern.match(text))

    def extract_chapter_number(self, text: str) -> str:
        if not self.chapter_number_pattern:
            return ""
        match = self.chapter_number_pattern.match(text)
        return match.group(1) if match else ""

    def formula_scope(
        self,
        *,
        in_appendix: bool,
        current_appendix_index: int,
        current_chapter_number: str,
    ) -> str | None:
        if in_appendix and current_appendix_index > 0:
            return f"{self.appendix_formula_scope_prefix}{current_appendix_index}"
        return current_chapter_number or None

    def format_formula_number(self, scope: str, number: int) -> str:
        return f"（{scope}-{number}）"
