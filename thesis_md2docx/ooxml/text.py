from __future__ import annotations

import re
from xml.sax.saxutils import escape

from ..constants import INLINE_CITATION_PATTERN
from ..inline import split_inline_emphasis
from .xml import break_run_xml, run_text_xml, symbol_run_xml, xml_text


INLINE_TOKEN_PATTERN = re.compile(
    r"\{\{(?:(?P<sym>sym):(?P<font>[^:}]+):(?P<char>[0-9A-Fa-f]{1,8})|(?P<sup>sup):(?P<sup_text>[^{}]*?)|(?P<sub>sub):(?P<sub_text>[^{}]*?))\}\}"
)


def _text_and_symbol_runs(text: str, *, run_kwargs: dict[str, object]) -> list[str]:
    runs: list[str] = []
    last = 0
    for match in INLINE_TOKEN_PATTERN.finditer(text):
        if match.start() > last:
            runs.append(run_text_xml(text[last : match.start()], **run_kwargs))
        if match.group("sym"):
            runs.append(
                symbol_run_xml(
                    font=match.group("font").strip(),
                    char=match.group("char").upper(),
                    bold=bool(run_kwargs.get("bold", False)),
                    bold_cs=run_kwargs.get("bold_cs") if "bold_cs" in run_kwargs else None,
                    italic=bool(run_kwargs.get("italic", False)),
                    italic_cs=run_kwargs.get("italic_cs") if "italic_cs" in run_kwargs else None,
                    size=int(run_kwargs["size"]) if run_kwargs.get("size") is not None else None,
                )
            )
        elif match.group("sup"):
            runs.append(run_text_xml(match.group("sup_text"), superscript=True, **run_kwargs))
        else:
            runs.append(run_text_xml(match.group("sub_text"), subscript=True, **run_kwargs))
        last = match.end()
    if last < len(text):
        runs.append(run_text_xml(text[last:], **run_kwargs))
    if not runs:
        runs.append(run_text_xml("", **run_kwargs))
    return runs


def text_runs(text: str, run_kwargs: dict[str, object] | None = None, preserve_breaks: bool = False) -> list[str]:
    run_kwargs = run_kwargs or {}
    if preserve_breaks and "\n" in text:
        parts = text.split("\n")
        runs: list[str] = []
        for idx, part in enumerate(parts):
            runs.extend(text_runs(part, run_kwargs=run_kwargs, preserve_breaks=False))
            if idx != len(parts) - 1:
                runs.append(break_run_xml())
        return runs

    text = text.replace("\\_", "_")
    segments = split_inline_emphasis(text)
    runs: list[str] = []
    for kind, value in segments:
        local_kwargs = dict(run_kwargs)
        if kind == "bold":
            local_kwargs["bold"] = True
        elif kind == "italic":
            local_kwargs["italic"] = True
        runs.extend(_text_and_symbol_runs(value, run_kwargs=local_kwargs))
    return runs


def inline_code_run_xml(text: str, *, size: int | None = None) -> str:
    return run_text_xml(
        text,
        font_ascii="Courier New",
        font_hansi="Courier New",
        font_eastasia="等线",
        size=size,
    )


def reference_bookmark_name(ref_id: str) -> str:
    return f"ref_{ref_id}"


def reference_bookmark_id(ref_id: str) -> int:
    return 1000 + int(ref_id)


def extract_reference_anchors(text: str) -> dict[str, str]:
    anchors: dict[str, str] = {}
    for ref_id in re.findall(r"^\[(\d+)\]\s", text, re.MULTILINE):
        anchors.setdefault(ref_id, reference_bookmark_name(ref_id))
    return anchors


def hyperlink_run_xml(
    text: str,
    anchor: str,
    *,
    run_kwargs: dict[str, object] | None = None,
    superscript: bool = False,
) -> str:
    run_kwargs = dict(run_kwargs or {})
    run_kwargs.pop("bold", None)
    run_kwargs.pop("italic", None)
    rpr: list[str] = []
    fonts: list[str] = []
    if font_ascii := run_kwargs.get("font_ascii"):
        fonts.append(f'w:ascii="{escape(str(font_ascii))}"')
    if font_hansi := run_kwargs.get("font_hansi"):
        fonts.append(f'w:hAnsi="{escape(str(font_hansi))}"')
    if font_eastasia := run_kwargs.get("font_eastasia"):
        fonts.append(f'w:eastAsia="{escape(str(font_eastasia))}"')
    if fonts:
        rpr.append(f"<w:rFonts {' '.join(fonts)}/>")
    if size := run_kwargs.get("size"):
        rpr.append(f'<w:sz w:val="{int(size)}"/><w:szCs w:val="{int(size)}"/>')
    if superscript:
        rpr.append('<w:vertAlign w:val="superscript"/>')
    rpr_xml = f"<w:rPr>{''.join(rpr)}</w:rPr>" if rpr else ""
    return f'<w:hyperlink w:anchor="{escape(anchor)}" w:history="1"><w:r>{rpr_xml}{xml_text(text)}</w:r></w:hyperlink>'


def citation_text_runs(
    text: str,
    *,
    run_kwargs: dict[str, object] | None = None,
    reference_anchors: dict[str, str] | None = None,
) -> list[str]:
    if not reference_anchors:
        return text_runs(text, run_kwargs=run_kwargs)

    runs: list[str] = []
    last = 0
    for match in INLINE_CITATION_PATTERN.finditer(text):
        if match.start() > last:
            runs.extend(text_runs(text[last:match.start()], run_kwargs=run_kwargs))

        ref_ids = re.findall(r"\d+", match.group(1))
        anchor = reference_anchors.get(ref_ids[0]) if ref_ids else None
        if anchor:
            runs.append(
                hyperlink_run_xml(
                    match.group(0),
                    anchor,
                    run_kwargs=run_kwargs,
                    superscript=True,
                )
            )
        else:
            runs.append(run_text_xml(match.group(0), superscript=True, **(run_kwargs or {})))
        last = match.end()

    if last < len(text):
        runs.extend(text_runs(text[last:], run_kwargs=run_kwargs))
    return runs
