from __future__ import annotations

import re
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
DEFAULT_COVER_ASSETS_DIR = TOOL_ROOT / "resources"
DEFAULT_LOCAL_COVER_ASSETS_REL = Path("img/cover-assets")

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
CP_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
DCTERMS_NS = "http://purl.org/dc/terms/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
VT_NS = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"

INLINE_MATH_PATTERN = re.compile(r"(?<!\\)\$(?!\$)(.+?)(?<!\\)\$(?!\$)")
INLINE_CITATION_PATTERN = re.compile(r"\[(\d+(?:\s*(?:[-,，]\s*\d+)*)+)\]")
IMAGE_PATTERN = re.compile(r"^!\[(?P<alt>[^\]]*)\]\((?P<target>[^)]+)\)$")
LATEX2OMML_NODE_DIR = TOOL_ROOT / "math" / "latex2omml_node"
LATEX2OMML_NODE_SCRIPT = LATEX2OMML_NODE_DIR / "convert.js"
LATEX2OMML_NODE_REQUIRED_MODULES = (
    LATEX2OMML_NODE_DIR / "node_modules" / "temml",
    LATEX2OMML_NODE_DIR / "node_modules" / "@hungknguyen" / "mathml2omml",
)
OMML_TEXT_PATTERN = re.compile(r"(<(?:m|w):t\b[^>]*>)(.*?)(</(?:m|w):t>)", re.DOTALL)
OMML_ACCENT_CHAR_MAP = {
    "^": "\u0302",  # combining circumflex accent
    "ˆ": "\u0302",
    "‾": "\u0305",  # combining overline
    "¯": "\u0305",
    "ˉ": "\u0305",
}
COVER_EMBLEM_NAME = "xju-emblem.jpeg"
COVER_WORDMARK_NAME = "xju-wordmark.png"

IMAGE_CONTENT_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "bmp": "image/bmp",
    "wmf": "image/x-wmf",
    "emf": "image/x-emf",
}
IMAGE_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
EMU_PER_INCH = 914400
DEFAULT_DPI = 96
MAX_IMAGE_WIDTH_IN = 5.8
MAX_IMAGE_HEIGHT_IN = 8.0
FIGURE_ROW_MAX_WIDTH_IN = 2.75
FIGURE_ROW_MAX_HEIGHT_IN = 3.2
BODY_TEXT_WIDTH_TWIPS = 8313
BODY_TEXT_CENTER_TWIPS = BODY_TEXT_WIDTH_TWIPS // 2
SIGNATURE_IMAGE_WIDTH_EMU = 1051560
SIGNATURE_IMAGE_HEIGHT_EMU = 494511

REL_ID_STYLES = "rId1"
REL_ID_SETTINGS = "rId2"
REL_ID_FONT_TABLE = "rId3"
REL_ID_HEADER = "rId4"
REL_ID_EMPTY_FOOTER = "rId5"
REL_ID_PAGE_FOOTER = "rId6"
REL_ID_NUMBERING = "rId7"
REL_ID_EMPTY_HEADER = "rId8"
IMAGE_STARTING_RID = 9
