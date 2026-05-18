from __future__ import annotations

from xml.sax.saxutils import escape

from ..constants import EMU_PER_INCH, FIGURE_ROW_MAX_HEIGHT_IN, FIGURE_ROW_MAX_WIDTH_IN
from ..media import MediaImage, MediaManager, fit_extent_emu
from .paragraphs import formatted_paragraph_xml, paragraph_xml
from .xml import indent_xml, spacing_xml


EMU_PER_POINT = 12700
EMU_PER_DXA = 635


def _emu_to_pt(value: int) -> str:
    points = value / EMU_PER_POINT
    if points.is_integer():
        return str(int(points))
    return f"{points:.2f}".rstrip("0").rstrip(".")


VML_IMAGE_SHAPETYPE_XML = (
    '<v:shapetype id="_x0000_t75" coordsize="21600,21600" o:spt="75" '
    'o:preferrelative="t" path="m@4@5l@4@11@9@11@9@5xe" filled="f" stroked="f">'
    '<v:stroke joinstyle="miter"/>'
    "<v:formulas>"
    '<v:f eqn="if lineDrawn pixelLineWidth 0"/>'
    '<v:f eqn="sum @0 1 0"/>'
    '<v:f eqn="sum 0 0 @1"/>'
    '<v:f eqn="prod @2 1 2"/>'
    '<v:f eqn="prod @3 21600 pixelWidth"/>'
    '<v:f eqn="prod @3 21600 pixelHeight"/>'
    '<v:f eqn="sum @0 0 1"/>'
    '<v:f eqn="prod @6 1 2"/>'
    '<v:f eqn="prod @7 21600 pixelWidth"/>'
    '<v:f eqn="sum @8 21600 0"/>'
    '<v:f eqn="prod @7 21600 pixelHeight"/>'
    '<v:f eqn="sum @10 21600 0"/>'
    "</v:formulas>"
    '<v:path o:extrusionok="f" gradientshapeok="t" o:connecttype="rect"/>'
    '<o:lock v:ext="edit" aspectratio="t"/>'
    "</v:shapetype>"
)


def image_run_xml(
    item: MediaImage,
    *,
    docpr_id: int,
    alt_text: str = "",
    width_emu: int | None = None,
    height_emu: int | None = None,
    crop_top: int | None = None,
    crop_right: int | None = None,
    crop_bottom: int | None = None,
    crop_left: int | None = None,
    no_proof: bool = False,
    local_dpi: bool = False,
    print_state: bool = False,
    no_change_arrows: bool = False,
) -> str:
    width_emu = width_emu or item.width_emu
    height_emu = height_emu or item.height_emu
    descr = escape(alt_text or item.filename)
    name = escape(item.filename)
    rpr_xml = '<w:rPr><w:noProof/><w:szCs w:val="24"/></w:rPr>' if no_proof else ""
    cstate_attr = ' cstate="print"' if print_state else ""
    local_dpi_xml = (
        '<a:extLst><a:ext uri="{28A0092B-C50C-407E-A947-70E740481C1C}">'
        '<a14:useLocalDpi val="0"/></a:ext></a:extLst>'
        if local_dpi
        else ""
    )
    pic_locks_xml = (
        '<a:picLocks noChangeAspect="1" noChangeArrowheads="1"/>'
        if no_change_arrows
        else ""
    )
    c_nv_pic_pr_xml = f"<pic:cNvPicPr>{pic_locks_xml}</pic:cNvPicPr>" if pic_locks_xml else "<pic:cNvPicPr/>"
    crop_attrs: list[str] = []
    if crop_top is not None:
        crop_attrs.append(f't="{crop_top}"')
    if crop_right is not None:
        crop_attrs.append(f'r="{crop_right}"')
    if crop_bottom is not None:
        crop_attrs.append(f'b="{crop_bottom}"')
    if crop_left is not None:
        crop_attrs.append(f'l="{crop_left}"')
    if crop_attrs:
        src_rect_xml = f"<a:srcRect {' '.join(crop_attrs)}/>"
    elif local_dpi:
        src_rect_xml = "<a:srcRect/>"
    else:
        src_rect_xml = ""
    fill_style_xml = f"{src_rect_xml}<a:stretch><a:fillRect/></a:stretch>"
    shape_style_xml = (
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln>'
        if local_dpi
        else '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
    )
    return (
        f"<w:r>{rpr_xml}<w:drawing>"
        '<wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{width_emu}" cy="{height_emu}"/>'
        '<wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="{docpr_id}" name="{name}" descr="{descr}"/>'
        '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        "<a:graphic>"
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        "<pic:pic>"
        "<pic:nvPicPr>"
        f'<pic:cNvPr id="{docpr_id}" name="{name}"/>'
        f"{c_nv_pic_pr_xml}"
        "</pic:nvPicPr>"
        "<pic:blipFill>"
        f'<a:blip r:embed="{item.rel_id}"{cstate_attr}>{local_dpi_xml}</a:blip>'
        f"{fill_style_xml}"
        "</pic:blipFill>"
        "<pic:spPr>"
        '<a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{width_emu}" cy="{height_emu}"/></a:xfrm>'
        f"{shape_style_xml}"
        "</pic:spPr>"
        "</pic:pic>"
        "</a:graphicData>"
        "</a:graphic>"
        "</wp:inline>"
        "</w:drawing></w:r>"
    )


def image_paragraph_xml(
    item: MediaImage,
    media_manager: MediaManager,
    *,
    alt_text: str = "",
    width_emu: int | None = None,
    height_emu: int | None = None,
    crop_top: int | None = None,
    crop_right: int | None = None,
    crop_bottom: int | None = None,
    crop_left: int | None = None,
    style: str | None = None,
    align: str | None = "center",
    ppr_extra: str | None = None,
    keep_next: bool = True,
    no_proof: bool = False,
    local_dpi: bool = False,
    print_state: bool = False,
    no_change_arrows: bool = False,
) -> str:
    # `<w:keepNext/>` keeps the image with its following caption paragraph on the
    # same page when feasible, avoiding figure/caption splits across page breaks.
    if width_emu is not None and height_emu is None and item.width_emu > 0:
        height_emu = max(1, int(item.height_emu * width_emu / item.width_emu))
    if height_emu is not None and width_emu is None and item.height_emu > 0:
        width_emu = max(1, int(item.width_emu * height_emu / item.height_emu))
    return paragraph_xml(
        align=align,
        runs=[
            image_run_xml(
                item,
                docpr_id=media_manager.next_drawing_id(),
                alt_text=alt_text,
                width_emu=width_emu,
                height_emu=height_emu,
                crop_top=crop_top,
                crop_right=crop_right,
                crop_bottom=crop_bottom,
                crop_left=crop_left,
                no_proof=no_proof,
                local_dpi=local_dpi,
                print_state=print_state,
                no_change_arrows=no_change_arrows,
            )
        ],
        style=style,
        ppr_extra=(spacing_xml(after=120) if ppr_extra is None else ppr_extra) + ("<w:keepNext/>" if keep_next else ""),
    )


def math_image_paragraph_xml(
    item: MediaImage,
    media_manager: MediaManager,
    *,
    alt_text: str = "",
    width_emu: int | None = None,
    height_emu: int | None = None,
    equation_number: str | None = None,
    style: str | None = None,
    image_mode: str = "drawing",
    first_line: int | None = None,
    first_line_chars: int | None = None,
    position: int | None = None,
    include_shapetype: bool = False,
) -> str:
    if width_emu is not None and height_emu is None and item.width_emu > 0:
        height_emu = max(1, int(item.height_emu * width_emu / item.width_emu))
    if height_emu is not None and width_emu is None and item.height_emu > 0:
        width_emu = max(1, int(item.width_emu * height_emu / item.height_emu))

    normalized_mode = image_mode.lower()
    ppr_extra = spacing_xml(line=360)
    indent = indent_xml(first_line_chars=first_line_chars, first_line=first_line)
    if indent:
        ppr_extra += indent
    ppr_extra += '<w:rPr><w:szCs w:val="24"/></w:rPr>'

    if normalized_mode == "vml":
        runs = [
            vml_image_object_run_xml(
                item,
                shape_id=f"_x0000_i{1024 + media_manager.next_drawing_id()}",
                width_emu=width_emu,
                height_emu=height_emu,
                position=position,
                include_shapetype=include_shapetype,
            )
        ]
    else:
        if first_line is None and first_line_chars is None:
            ppr_extra += '<w:ind w:firstLineChars="1500" w:firstLine="3600"/>'
        runs = [
            image_run_xml(
                item,
                docpr_id=media_manager.next_drawing_id(),
                alt_text=alt_text,
                width_emu=width_emu,
                height_emu=height_emu,
                no_proof=True,
                local_dpi=True,
                print_state=True,
                no_change_arrows=True,
            )
        ]
    if equation_number:
        if normalized_mode == "vml":
            runs.append('<w:r><w:rPr><w:szCs w:val="24"/></w:rPr><w:tab/></w:r>')
            runs.append(f"<w:r><w:rPr><w:szCs w:val=\"24\"/></w:rPr><w:t>{equation_number}</w:t></w:r>")
        else:
            runs.append(
                '<w:r><w:rPr><w:szCs w:val="24"/></w:rPr>'
                '<w:t xml:space="preserve">                       </w:t></w:r>'
            )
            if equation_number.startswith("（") and equation_number.endswith("）") and "-" in equation_number:
                runs.append('<w:r><w:rPr><w:szCs w:val="24"/></w:rPr><w:t>（</w:t></w:r>')
                runs.append(f'<w:r><w:rPr><w:szCs w:val="24"/></w:rPr><w:t>{escape(equation_number[1:-1])}</w:t></w:r>')
                runs.append('<w:r><w:rPr><w:szCs w:val="24"/></w:rPr><w:t>）</w:t></w:r>')
            else:
                runs.append(f"<w:r><w:rPr><w:szCs w:val=\"24\"/></w:rPr><w:t>{escape(equation_number)}</w:t></w:r>")
    return paragraph_xml(
        style=style,
        runs=runs,
        ppr_extra=ppr_extra,
    )


def vml_image_object_run_xml(
    item: MediaImage,
    *,
    shape_id: str,
    width_emu: int | None = None,
    height_emu: int | None = None,
    position: int | None = None,
    include_shapetype: bool = False,
) -> str:
    width_emu = width_emu or item.width_emu
    height_emu = height_emu or item.height_emu
    dxa_orig = max(1, round(width_emu / EMU_PER_DXA))
    dya_orig = max(1, round(height_emu / EMU_PER_DXA))
    position_xml = f'<w:position w:val="{position}"/>' if position is not None else ""
    rpr_xml = f"<w:rPr>{position_xml}<w:szCs w:val=\"24\"/></w:rPr>" if position_xml else ""
    shapetype_xml = VML_IMAGE_SHAPETYPE_XML if include_shapetype else ""
    shape = (
        f'<v:shape id="{escape(shape_id)}" type="#_x0000_t75" '
        f'style="width:{_emu_to_pt(width_emu)}pt;height:{_emu_to_pt(height_emu)}pt" o:ole="">'
        f'<v:imagedata r:id="{item.rel_id}" o:title=""/>'
        "</v:shape>"
    )
    return (
        f"<w:r>{rpr_xml}"
        f'<w:object w:dxaOrig="{dxa_orig}" w:dyaOrig="{dya_orig}">'
        f"{shapetype_xml}{shape}"
        "</w:object></w:r>"
    )


def figure_row_xml(
    items: list[tuple[MediaImage | None, str]],
    media_manager: MediaManager,
) -> str:
    if not items:
        return ""

    col_count = len(items)
    col_width = max(1800, 9000 // col_count)
    max_width_emu = int(FIGURE_ROW_MAX_WIDTH_IN * EMU_PER_INCH)
    max_height_emu = int(FIGURE_ROW_MAX_HEIGHT_IN * EMU_PER_INCH)
    common_height_emu = max_height_emu
    for item, _ in items:
        if item is None or item.width_emu <= 0 or item.height_emu <= 0:
            continue
        height_limit_by_width = int(max_width_emu * item.height_emu / item.width_emu)
        common_height_emu = min(common_height_emu, max(1, height_limit_by_width))
    common_height_emu = max(1, min(common_height_emu, max_height_emu))
    tbl_pr = (
        "<w:tblPr>"
        '<w:tblW w:w="9000" w:type="dxa"/>'
        '<w:jc w:val="center"/>'
        "<w:tblBorders>"
        '<w:top w:val="nil"/>'
        '<w:left w:val="nil"/>'
        '<w:bottom w:val="nil"/>'
        '<w:right w:val="nil"/>'
        '<w:insideH w:val="nil"/>'
        '<w:insideV w:val="nil"/>'
        "</w:tblBorders>"
        "</w:tblPr>"
    )
    tbl_grid = "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{col_width}"/>' for _ in range(col_count)) + "</w:tblGrid>"

    cells: list[str] = []
    for item, alt_text in items:
        body: list[str] = []
        tc_pr = f'<w:tcPr><w:tcW w:w="{col_width}" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>'
        if item is None:
            body.append(
                formatted_paragraph_xml(
                    "图片待补充",
                    align="center",
                    ppr_extra=spacing_xml(after=60),
                    run_kwargs={"italic": True},
                )
            )
        else:
            width_emu = max(1, int(item.width_emu * common_height_emu / item.height_emu))
            height_emu = common_height_emu
            if width_emu > max_width_emu:
                width_emu, height_emu = fit_extent_emu(
                    item.width_emu,
                    item.height_emu,
                    max_width_emu=max_width_emu,
                    max_height_emu=max_height_emu,
                )
            body.append(
                paragraph_xml(
                    align="center",
                    runs=[
                        image_run_xml(
                            item,
                            docpr_id=media_manager.next_drawing_id(),
                            alt_text=alt_text,
                            width_emu=width_emu,
                            height_emu=height_emu,
                        )
                    ],
                    ppr_extra=spacing_xml(after=80),
                )
            )
        if alt_text:
            body.append(paragraph_xml(alt_text, align="center", ppr_extra=spacing_xml(after=0)))
        cells.append(f"<w:tc>{tc_pr}{''.join(body)}</w:tc>")

    # `cantSplit` keeps every image in the side-by-side row on a single page; the
    # outer paragraph following this table is set to `keepNext` so that the row
    # stays adjacent to its caption.
    tr_pr = "<w:trPr><w:cantSplit/></w:trPr>"
    return f"<w:tbl>{tbl_pr}{tbl_grid}<w:tr>{tr_pr}{''.join(cells)}</w:tr></w:tbl>"
