from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ParagraphBlock:
    text: str
    options: Mapping[str, str] | None = None


@dataclass(frozen=True)
class BlankBlock:
    options: Mapping[str, str] | None = None


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
    image: str | None = None
    image_alt: str = ""
    image_width_emu: int | None = None
    image_height_emu: int | None = None
    image_mode: str = "drawing"
    image_first_line: int | None = None
    image_first_line_chars: int | None = None
    image_position: int | None = None
    image_include_shapetype: bool = False


@dataclass(frozen=True)
class ImageBlock:
    target: str
    alt_text: str
    raw_text: str
    options: Mapping[str, str] | None = None
    width_emu: int | None = None
    height_emu: int | None = None
    crop_top: int | None = None
    crop_right: int | None = None
    crop_bottom: int | None = None
    crop_left: int | None = None


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
    left: int | None = None
    first_line: int | None = None
    first_line_chars: int | None = None
    continue_left: int | None = None
    continue_first_line: int | None = None
    continue_first_line_chars: int | None = None
    bold_cs: bool | None = None
    style: str | None = None
    font_size: int | None = None
    font_size_cs: int | bool | None = None
    omit_first_line: bool = False


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
    | BlankBlock
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
