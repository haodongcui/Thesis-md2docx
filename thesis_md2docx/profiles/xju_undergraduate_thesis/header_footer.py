from __future__ import annotations

from ...constants import R_NS, W_NS
from ...ooxml.render import formatted_paragraph_xml, paragraph_xml
from ...ooxml.xml import field_char_run_xml, instr_text_run_xml, run_text_xml
from .styles import STYLE_FOOTER, STYLE_HEADER


def header_xml() -> str:
    ppr_extra = (
        "<w:pBdr>"
        '<w:top w:val="none" w:sz="0" w:space="1" w:color="auto"/>'
        '<w:left w:val="none" w:sz="0" w:space="4" w:color="auto"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="1" w:color="auto"/>'
        '<w:right w:val="none" w:sz="0" w:space="4" w:color="auto"/>'
        "</w:pBdr>"
    )
    paragraph = formatted_paragraph_xml(
        "新疆大学本科毕业论文（设计）",
        style=STYLE_HEADER,
        align="center",
        ppr_extra=ppr_extra,
        run_kwargs={
            "font_ascii": "宋体",
            "font_hansi": "宋体",
            "font_eastasia": "宋体",
            "size": 18,
        },
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:hdr xmlns:w="{W_NS}" xmlns:r="{R_NS}">{paragraph}</w:hdr>'
    )


def empty_footer_xml() -> str:
    paragraph = paragraph_xml("", style=STYLE_FOOTER, first_line=0, first_line_chars=0)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:ftr xmlns:w="{W_NS}" xmlns:r="{R_NS}">{paragraph}</w:ftr>'
    )


def empty_header_xml() -> str:
    paragraph = paragraph_xml("", first_line=0, first_line_chars=0)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:hdr xmlns:w="{W_NS}" xmlns:r="{R_NS}">{paragraph}</w:hdr>'
    )


def page_footer_xml() -> str:
    runs = [
        field_char_run_xml("begin"),
        instr_text_run_xml("PAGE   \\* MERGEFORMAT"),
        field_char_run_xml("separate"),
        run_text_xml(
            "1",
            font_ascii="Times New Roman",
            font_hansi="Times New Roman",
            font_eastasia="宋体",
            size=18,
        ),
        field_char_run_xml("end"),
    ]
    paragraph = paragraph_xml(runs=runs, style=STYLE_FOOTER, align="center", first_line=0, first_line_chars=0)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:ftr xmlns:w="{W_NS}" xmlns:r="{R_NS}">{paragraph}</w:ftr>'
    )
