from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from xml.sax.saxutils import escape


class XmlProperty(Protocol):
    def xml(self) -> str:
        ...


StyleProperty = XmlProperty | str


def style_props(*properties: StyleProperty) -> tuple[str, ...]:
    return tuple(prop.xml() if hasattr(prop, "xml") else prop for prop in properties)


@dataclass(frozen=True)
class ToggleProperty:
    name: str
    value: bool = True

    def xml(self) -> str:
        if self.value:
            return f"<w:{self.name}/>"
        return f'<w:{self.name} w:val="0"/>'


@dataclass(frozen=True)
class RunFontsProperty:
    ascii: str | None = None
    hansi: str | None = None
    eastasia: str | None = None
    complex_script: str | None = None

    def xml(self) -> str:
        attrs: list[str] = []
        if self.ascii is not None:
            attrs.append(f'w:ascii="{escape(self.ascii)}"')
        if self.hansi is not None:
            attrs.append(f'w:hAnsi="{escape(self.hansi)}"')
        if self.eastasia is not None:
            attrs.append(f'w:eastAsia="{escape(self.eastasia)}"')
        if self.complex_script is not None:
            attrs.append(f'w:cs="{escape(self.complex_script)}"')
        return f"<w:rFonts {' '.join(attrs)}/>"


@dataclass(frozen=True)
class RunSizeProperty:
    size: int
    complex_size: int | None = None

    def xml(self) -> str:
        complex_size = self.size if self.complex_size is None else self.complex_size
        return f'<w:sz w:val="{self.size}"/><w:szCs w:val="{complex_size}"/>'


@dataclass(frozen=True)
class KernProperty:
    value: int

    def xml(self) -> str:
        return f'<w:kern w:val="{self.value}"/>'


@dataclass(frozen=True)
class JustificationProperty:
    value: str

    def xml(self) -> str:
        return f'<w:jc w:val="{escape(self.value)}"/>'


@dataclass(frozen=True)
class SpacingProperty:
    before_lines: int | None = None
    before: int | None = None
    after_lines: int | None = None
    after: int | None = None
    line: int | None = None
    line_rule: str = "auto"

    def xml(self) -> str:
        attrs: list[str] = []
        if self.before_lines is not None:
            attrs.append(f'w:beforeLines="{self.before_lines}"')
        if self.before is not None:
            attrs.append(f'w:before="{self.before}"')
        if self.after_lines is not None:
            attrs.append(f'w:afterLines="{self.after_lines}"')
        if self.after is not None:
            attrs.append(f'w:after="{self.after}"')
        if self.line is not None:
            attrs.append(f'w:line="{self.line}"')
            attrs.append(f'w:lineRule="{escape(self.line_rule)}"')
        return f"<w:spacing {' '.join(attrs)}/>"


@dataclass(frozen=True)
class IndentProperty:
    left: int | None = None
    first_line_chars: int | None = None
    first_line: int | None = None
    hanging: int | None = None

    def xml(self) -> str:
        attrs: list[str] = []
        if self.left is not None:
            attrs.append(f'w:left="{self.left}"')
        if self.first_line_chars is not None:
            attrs.append(f'w:firstLineChars="{self.first_line_chars}"')
        if self.first_line is not None:
            attrs.append(f'w:firstLine="{self.first_line}"')
        if self.hanging is not None:
            attrs.append(f'w:hanging="{self.hanging}"')
        return f"<w:ind {' '.join(attrs)}/>"


@dataclass(frozen=True)
class NumberingProperty:
    level: int | None = None
    num_id: int | None = None

    def xml(self) -> str:
        body: list[str] = []
        if self.level is not None:
            body.append(f'<w:ilvl w:val="{self.level}"/>')
        if self.num_id is not None:
            body.append(f'<w:numId w:val="{self.num_id}"/>')
        return f"<w:numPr>{''.join(body)}</w:numPr>"


@dataclass(frozen=True)
class OutlineLevelProperty:
    value: int

    def xml(self) -> str:
        return f'<w:outlineLvl w:val="{self.value}"/>'


@dataclass(frozen=True)
class TabStopProperty:
    value: str
    position: int
    leader: str | None = None

    def xml(self) -> str:
        attrs = [f'w:val="{escape(self.value)}"']
        if self.leader is not None:
            attrs.append(f'w:leader="{escape(self.leader)}"')
        attrs.append(f'w:pos="{self.position}"')
        return f"<w:tab {' '.join(attrs)}/>"


@dataclass(frozen=True)
class TabsProperty:
    stops: tuple[TabStopProperty, ...]

    def xml(self) -> str:
        return f"<w:tabs>{''.join(stop.xml() for stop in self.stops)}</w:tabs>"


@dataclass(frozen=True)
class ParagraphBottomBorderProperty:
    value: str = "single"
    size: int = 6
    space: int = 1
    color: str = "auto"

    def xml(self) -> str:
        return (
            "<w:pBdr>"
            f'<w:bottom w:val="{escape(self.value)}" w:sz="{self.size}" '
            f'w:space="{self.space}" w:color="{escape(self.color)}"/>'
            "</w:pBdr>"
        )


@dataclass(frozen=True)
class ShadingProperty:
    value: str
    fill: str

    def xml(self) -> str:
        return f'<w:shd w:val="{escape(self.value)}" w:fill="{escape(self.fill)}"/>'


def toggle(name: str, value: bool = True) -> ToggleProperty:
    return ToggleProperty(name, value)


def run_fonts(
    *,
    ascii: str | None = None,
    hansi: str | None = None,
    eastasia: str | None = None,
    complex_script: str | None = None,
) -> RunFontsProperty:
    return RunFontsProperty(ascii=ascii, hansi=hansi, eastasia=eastasia, complex_script=complex_script)


def run_size(size: int, *, complex_size: int | None = None) -> RunSizeProperty:
    return RunSizeProperty(size=size, complex_size=complex_size)


def kern(value: int) -> KernProperty:
    return KernProperty(value)


def bold(value: bool = True) -> ToggleProperty:
    return toggle("b", value)


def bold_complex(value: bool = True) -> ToggleProperty:
    return toggle("bCs", value)


def italic(value: bool = True) -> ToggleProperty:
    return toggle("i", value)


def snap_to_grid(value: bool = True) -> ToggleProperty:
    return toggle("snapToGrid", value)


def widow_control(value: bool = True) -> ToggleProperty:
    return toggle("widowControl", value)


def justification(value: str) -> JustificationProperty:
    return JustificationProperty(value)


def spacing(
    *,
    before_lines: int | None = None,
    before: int | None = None,
    after_lines: int | None = None,
    after: int | None = None,
    line: int | None = None,
    line_rule: str = "auto",
) -> SpacingProperty:
    return SpacingProperty(
        before_lines=before_lines,
        before=before,
        after_lines=after_lines,
        after=after,
        line=line,
        line_rule=line_rule,
    )


def indent(
    *,
    left: int | None = None,
    first_line_chars: int | None = None,
    first_line: int | None = None,
    hanging: int | None = None,
) -> IndentProperty:
    return IndentProperty(left=left, first_line_chars=first_line_chars, first_line=first_line, hanging=hanging)


def numbering(*, level: int | None = None, num_id: int | None = None) -> NumberingProperty:
    return NumberingProperty(level=level, num_id=num_id)


def outline_level(value: int) -> OutlineLevelProperty:
    return OutlineLevelProperty(value)


def tab(value: str, position: int, *, leader: str | None = None) -> TabStopProperty:
    return TabStopProperty(value=value, position=position, leader=leader)


def tabs(*stops: TabStopProperty) -> TabsProperty:
    return TabsProperty(stops)


def paragraph_bottom_border(
    *,
    value: str = "single",
    size: int = 6,
    space: int = 1,
    color: str = "auto",
) -> ParagraphBottomBorderProperty:
    return ParagraphBottomBorderProperty(value=value, size=size, space=space, color=color)


def shading(value: str, fill: str) -> ShadingProperty:
    return ShadingProperty(value=value, fill=fill)
