from __future__ import annotations

from dataclasses import dataclass
from xml.sax.saxutils import escape

from ..constants import W_NS


@dataclass(frozen=True)
class FontSpec:
    name: str
    alt_name: str | None = None
    charset: str | None = None
    family: str | None = None
    pitch: str | None = None

    def xml(self) -> str:
        if self.alt_name is None and self.charset is None and self.family is None and self.pitch is None:
            return f'<w:font w:name="{escape(self.name)}"/>'

        body: list[str] = [f'<w:font w:name="{escape(self.name)}">']
        if self.alt_name is not None:
            body.append(f'<w:altName w:val="{escape(self.alt_name)}"/>')
        if self.charset is not None:
            body.append(f'<w:charset w:val="{escape(self.charset)}"/>')
        if self.family is not None:
            body.append(f'<w:family w:val="{escape(self.family)}"/>')
        if self.pitch is not None:
            body.append(f'<w:pitch w:val="{escape(self.pitch)}"/>')
        body.append("</w:font>")
        return "".join(body)


@dataclass(frozen=True)
class FontTableSpec:
    fonts: tuple[FontSpec, ...]


def font_table_xml(spec: FontTableSpec) -> str:
    body = "".join(font.xml() for font in spec.fonts)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:fonts xmlns:w="{W_NS}">{body}</w:fonts>'
    )
