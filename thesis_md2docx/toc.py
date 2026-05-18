from __future__ import annotations

from dataclasses import dataclass


TOC_BOOKMARK_ID_START = 5000
TOC_BOOKMARK_NAME_START = 102000000


@dataclass(frozen=True)
class TocEntry:
    level: int
    text: str
    anchor: str
    bookmark_id: int


def make_toc_entry(index: int, *, level: int, text: str) -> TocEntry:
    return TocEntry(
        level=max(1, min(level, 3)),
        text=text,
        anchor=f"_Toc{TOC_BOOKMARK_NAME_START + index}",
        bookmark_id=TOC_BOOKMARK_ID_START + index,
    )
