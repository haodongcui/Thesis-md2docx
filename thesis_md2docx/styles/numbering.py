from __future__ import annotations

from dataclasses import dataclass
from xml.sax.saxutils import escape

from ..constants import W_NS
from .properties import indent


@dataclass(frozen=True)
class NumberingLevelSpec:
    level: int
    text: str
    paragraph_style: str | None = None
    start: int = 1
    num_format: str = "decimal"
    suffix: str = "space"
    justification: str = "left"
    indent_left: int = 0
    indent_hanging: int = 0

    def xml(self) -> str:
        body = [
            f'<w:lvl w:ilvl="{self.level}">',
            f'<w:start w:val="{self.start}"/>',
            f'<w:numFmt w:val="{escape(self.num_format)}"/>',
        ]
        if self.paragraph_style is not None:
            body.append(f'<w:pStyle w:val="{escape(self.paragraph_style)}"/>')
        body.extend(
            [
                f'<w:suff w:val="{escape(self.suffix)}"/>',
                f'<w:lvlText w:val="{escape(self.text)}"/>',
                f'<w:lvlJc w:val="{escape(self.justification)}"/>',
                f"<w:pPr>{indent(left=self.indent_left, hanging=self.indent_hanging).xml()}</w:pPr>",
                "</w:lvl>",
            ]
        )
        return "".join(body)


@dataclass(frozen=True)
class AbstractNumberingSpec:
    abstract_num_id: int
    levels: tuple[NumberingLevelSpec, ...]
    multi_level_type: str = "multilevel"

    def xml(self) -> str:
        return (
            f'<w:abstractNum w:abstractNumId="{self.abstract_num_id}">'
            f'<w:multiLevelType w:val="{escape(self.multi_level_type)}"/>'
            f'{"".join(level.xml() for level in self.levels)}'
            "</w:abstractNum>"
        )


@dataclass(frozen=True)
class NumberingInstanceSpec:
    num_id: int
    abstract_num_id: int

    def xml(self) -> str:
        return f'<w:num w:numId="{self.num_id}"><w:abstractNumId w:val="{self.abstract_num_id}"/></w:num>'


@dataclass(frozen=True)
class NumberingCatalog:
    abstract_numbers: tuple[AbstractNumberingSpec, ...]
    instances: tuple[NumberingInstanceSpec, ...]


def numbering_xml(catalog: NumberingCatalog) -> str:
    body = "".join(item.xml() for item in catalog.abstract_numbers)
    body += "".join(item.xml() for item in catalog.instances)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:numbering xmlns:w="{W_NS}" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
        'xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" '
        'xmlns:w16se="http://schemas.microsoft.com/office/word/2015/wordml/symex">'
        f"{body}"
        "</w:numbering>"
    )
