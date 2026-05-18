from __future__ import annotations

import unicodedata

from .constants import IMAGE_PATTERN
from .markdown import join_soft_wrapped_lines, split_plain_paragraphs


def split_statement_content(text: str) -> tuple[list[str], str, str]:
    body_lines: list[str] = []
    author_value = ""
    date_value = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("作者签名："):
            author_value = line.split("：", 1)[1].strip()
            continue
        if line.startswith("签字日期："):
            date_value = line.split("：", 1)[1].strip()
            continue
        body_lines.append(line)
    body_text = "\n".join(body_lines)
    return split_plain_paragraphs(body_text), author_value, date_value


def parse_inline_image_value(value: str) -> tuple[str, str] | None:
    match = IMAGE_PATTERN.match(value.strip())
    if not match:
        return None
    return match.group("alt").strip(), match.group("target").strip()


def first_nonempty_value(*values: str | None, default: str = "") -> str:
    for value in values:
        if value and value.strip():
            return value.strip()
    return default


def wrap_taskbook_text(text: str, *, max_chars: int = 31, max_lines: int = 6) -> list[str]:
    compact = join_soft_wrapped_lines(split_plain_paragraphs(text))
    lines: list[str] = []
    while compact and len(lines) < max_lines:
        lines.append(compact[:max_chars])
        compact = compact[max_chars:].lstrip()
    while len(lines) < max_lines:
        lines.append("")
    return lines


def taskbook_run_kwargs(*, bold: bool = False, size: int = 24) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "font_ascii": "宋体",
        "font_hansi": "宋体",
        "font_cs": "宋体",
        "font_hint": "eastAsia",
        "bold": bold,
        "size": size,
    }
    if size == 24:
        kwargs["size_cs"] = False
    return kwargs


def taskbook_display_width(text: str) -> int:
    width = 0
    for ch in text:
        if unicodedata.east_asian_width(ch) in {"W", "F"}:
            width += 2
        else:
            width += 1
    return width
