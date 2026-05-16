from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ParagraphBlock:
    text: str


@dataclass(frozen=True)
class HeadingBlock:
    raw_level: int
    text: str

    @property
    def level(self) -> int:
        return min(self.raw_level, 3)


@dataclass(frozen=True)
class CodeBlock:
    text: str


@dataclass(frozen=True)
class MathBlock:
    text: str


@dataclass(frozen=True)
class ImageBlock:
    target: str
    alt_text: str
    raw_text: str


@dataclass(frozen=True)
class FigureRowBlock:
    images: tuple[ImageBlock, ...]
    raw_lines: tuple[str, ...]


@dataclass(frozen=True)
class TableBlock:
    rows: tuple[tuple["TableCell", ...], ...]
    options: Mapping[str, str] | None = None


@dataclass(frozen=True)
class TableCell:
    text: str
    colspan: int = 1
    rowspan: int = 1
    header: bool = False
    align: str | None = None


@dataclass(frozen=True)
class PageBreakBlock:
    before_heading_level: int | None = None


@dataclass(frozen=True)
class TableSplitBlock:
    spec: str


@dataclass(frozen=True)
class QuoteBlock:
    text: str


Block = (
    ParagraphBlock
    | HeadingBlock
    | CodeBlock
    | MathBlock
    | ImageBlock
    | FigureRowBlock
    | TableBlock
    | PageBreakBlock
    | TableSplitBlock
    | QuoteBlock
)
