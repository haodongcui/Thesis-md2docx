from __future__ import annotations

import argparse
import math
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


@dataclass(frozen=True)
class PageDiff:
    page: int
    reference_size: tuple[int, int] | None
    candidate_size: tuple[int, int] | None
    changed_pixels: int | None
    total_pixels: int | None
    changed_ratio: float | None
    mean_abs_diff: float | None
    rms_diff: float | None
    bbox: tuple[int, int, int, int] | None
    diff_path: Path | None
    note: str | None = None


@dataclass(frozen=True)
class PdfDiff:
    reference: Path
    candidate: Path
    dpi: int
    pages: tuple[PageDiff, ...]

    @property
    def changed_pages(self) -> int:
        return sum(
            1
            for page in self.pages
            if page.changed_pixels not in (None, 0) or page.reference_size != page.candidate_size or page.note
        )

    @property
    def total_changed_pixels(self) -> int:
        return sum(page.changed_pixels or 0 for page in self.pages)

    @property
    def total_pixels(self) -> int:
        return sum(page.total_pixels or 0 for page in self.pages)

    @property
    def changed_ratio(self) -> float:
        total = self.total_pixels
        return self.total_changed_pixels / total if total else 0.0


def _page_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"-(\d+)\.png$", path.name)
    if not match:
        return (10**9, path.name)
    return (int(match.group(1)), path.name)


def render_pdf_to_images(pdf_path: Path, output_dir: Path, *, dpi: int, prefix: str = "page") -> list[Path]:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise ValueError("pdftoppm not found; install poppler-utils or add pdftoppm to PATH")
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in output_dir.glob(f"{prefix}-*.png"):
        path.unlink()
    subprocess.run(
        [pdftoppm, "-png", "-r", str(dpi), str(pdf_path), str(output_dir / prefix)],
        check=True,
    )
    return sorted(output_dir.glob(f"{prefix}-*.png"), key=_page_sort_key)


def _rgb_with_white_canvas(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    rgb = image.convert("RGB")
    if rgb.size == size:
        return rgb
    canvas = Image.new("RGB", size, "white")
    canvas.paste(rgb, (0, 0))
    return canvas


def _nonzero_diff_mask(diff: Image.Image) -> Image.Image:
    channels = diff.split()
    mask = channels[0]
    for channel in channels[1:]:
        mask = ImageChops.lighter(mask, channel)
    return mask.point(lambda value: 255 if value else 0, mode="L")


def _amplified_diff_image(diff: Image.Image) -> Image.Image:
    mask = _nonzero_diff_mask(diff)
    heat = Image.new("RGB", diff.size, "white")
    red = Image.new("RGB", diff.size, (255, 0, 0))
    heat.paste(red, mask=mask)
    return heat


def compare_page_images(
    reference_image: Path,
    candidate_image: Path,
    *,
    page: int,
    diff_path: Path | None = None,
) -> PageDiff:
    with Image.open(reference_image) as ref_raw, Image.open(candidate_image) as cand_raw:
        reference_size = ref_raw.size
        candidate_size = cand_raw.size
        width = max(ref_raw.width, cand_raw.width)
        height = max(ref_raw.height, cand_raw.height)
        size = (width, height)
        ref = _rgb_with_white_canvas(ref_raw, size)
        cand = _rgb_with_white_canvas(cand_raw, size)

    diff = ImageChops.difference(ref, cand)
    mask = _nonzero_diff_mask(diff)
    bbox = diff.getbbox()
    histogram = mask.histogram()
    changed_pixels = histogram[255]
    total_pixels = width * height
    stat = ImageStat.Stat(diff)
    channel_count = len(stat.mean) or 1
    mean_abs_diff = sum(stat.mean) / channel_count
    rms_diff = math.sqrt(sum(value * value for value in stat.rms) / channel_count)

    saved_diff: Path | None = None
    if diff_path is not None and changed_pixels:
        diff_path.parent.mkdir(parents=True, exist_ok=True)
        _amplified_diff_image(diff).save(diff_path)
        saved_diff = diff_path

    return PageDiff(
        page=page,
        reference_size=reference_size,
        candidate_size=candidate_size,
        changed_pixels=changed_pixels,
        total_pixels=total_pixels,
        changed_ratio=changed_pixels / total_pixels if total_pixels else 0.0,
        mean_abs_diff=mean_abs_diff,
        rms_diff=rms_diff,
        bbox=bbox,
        diff_path=saved_diff,
    )


def compare_pdf(
    reference_pdf: Path,
    candidate_pdf: Path,
    *,
    dpi: int = 144,
    diff_dir: Path | None = None,
    keep_rendered: Path | None = None,
) -> PdfDiff:
    reference_pdf = Path(reference_pdf)
    candidate_pdf = Path(candidate_pdf)
    if not reference_pdf.is_file():
        raise ValueError(f"Reference PDF not found: {reference_pdf}")
    if not candidate_pdf.is_file():
        raise ValueError(f"Candidate PDF not found: {candidate_pdf}")
    if diff_dir:
        diff_dir.mkdir(parents=True, exist_ok=True)
        for path in diff_dir.glob("page-*.png"):
            path.unlink()

    with tempfile.TemporaryDirectory(prefix="thesis-pdf-compare-") as tmp:
        tmp_dir = Path(tmp)
        ref_dir = tmp_dir / "reference"
        cand_dir = tmp_dir / "candidate"
        ref_pages = render_pdf_to_images(reference_pdf, ref_dir, dpi=dpi, prefix="page")
        cand_pages = render_pdf_to_images(candidate_pdf, cand_dir, dpi=dpi, prefix="page")
        if keep_rendered:
            keep_rendered.mkdir(parents=True, exist_ok=True)
            ref_keep = keep_rendered / "reference"
            cand_keep = keep_rendered / "candidate"
            ref_keep.mkdir(parents=True, exist_ok=True)
            cand_keep.mkdir(parents=True, exist_ok=True)
            for path in ref_keep.glob("page-*.png"):
                path.unlink()
            for path in cand_keep.glob("page-*.png"):
                path.unlink()
            for page_path in ref_pages:
                shutil.copy2(page_path, ref_keep / page_path.name)
            for page_path in cand_pages:
                shutil.copy2(page_path, cand_keep / page_path.name)

        pages: list[PageDiff] = []
        max_pages = max(len(ref_pages), len(cand_pages))
        for index in range(max_pages):
            page_number = index + 1
            ref_page = ref_pages[index] if index < len(ref_pages) else None
            cand_page = cand_pages[index] if index < len(cand_pages) else None
            if ref_page is None or cand_page is None:
                pages.append(
                    PageDiff(
                        page=page_number,
                        reference_size=None,
                        candidate_size=None,
                        changed_pixels=None,
                        total_pixels=None,
                        changed_ratio=None,
                        mean_abs_diff=None,
                        rms_diff=None,
                        bbox=None,
                        diff_path=None,
                        note="missing reference page" if ref_page is None else "missing candidate page",
                    )
                )
                continue
            page_diff_path = diff_dir / f"page-{page_number}.png" if diff_dir else None
            pages.append(compare_page_images(ref_page, cand_page, page=page_number, diff_path=page_diff_path))

    return PdfDiff(reference=reference_pdf, candidate=candidate_pdf, dpi=dpi, pages=tuple(pages))


def _format_ratio(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.6%}"


def _format_float(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.4f}"


def _format_size(size: tuple[int, int] | None) -> str:
    if size is None:
        return "-"
    return f"{size[0]}x{size[1]}"


def pdf_diff_report(diff: PdfDiff) -> str:
    lines: list[str] = []
    lines.append("# PDF Pixel Audit")
    lines.append("")
    lines.append(f"- Reference: `{diff.reference}`")
    lines.append(f"- Candidate: `{diff.candidate}`")
    lines.append(f"- DPI: {diff.dpi}")
    lines.append(f"- Pages: {len(diff.pages)}")
    lines.append(f"- Changed pages: {diff.changed_pages}")
    lines.append(f"- Changed pixels: {diff.total_changed_pixels}/{diff.total_pixels} ({_format_ratio(diff.changed_ratio)})")
    lines.append("")
    lines.append("## Page Summary")
    lines.append("")
    lines.append("| Page | Ref size | Cand size | Changed | Ratio | Mean | RMS | BBox | Diff | Note |")
    lines.append("| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |")
    for page in diff.pages:
        diff_link = f"`{page.diff_path}`" if page.diff_path else ""
        bbox = str(page.bbox) if page.bbox else ""
        changed = "-" if page.changed_pixels is None else str(page.changed_pixels)
        lines.append(
            "| "
            f"{page.page} | "
            f"{_format_size(page.reference_size)} | "
            f"{_format_size(page.candidate_size)} | "
            f"{changed} | "
            f"{_format_ratio(page.changed_ratio)} | "
            f"{_format_float(page.mean_abs_diff)} | "
            f"{_format_float(page.rms_diff)} | "
            f"{bbox} | "
            f"{diff_link} | "
            f"{page.note or ''} |"
        )
    lines.append("")
    return "\n".join(lines)


def add_compare_pdf_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("compare-pdf", help="compare rendered PDF pages pixel by pixel")
    parser.add_argument("reference", type=Path, help="Reference PDF path.")
    parser.add_argument("candidate", type=Path, help="Candidate PDF path.")
    parser.add_argument("--dpi", type=int, default=144, help="Rasterization DPI. Defaults to 144.")
    parser.add_argument("--out", type=Path, default=None, help="Write markdown report to this path.")
    parser.add_argument(
        "--diff-dir",
        type=Path,
        default=None,
        help="Write changed-page heatmap PNG files to this directory.",
    )
    parser.add_argument(
        "--keep-rendered",
        type=Path,
        default=None,
        help="Keep rasterized reference/candidate page images under this directory.",
    )


def run_compare_pdf(args: argparse.Namespace) -> int:
    result = compare_pdf(
        args.reference,
        args.candidate,
        dpi=args.dpi,
        diff_dir=args.diff_dir,
        keep_rendered=args.keep_rendered,
    )
    report = pdf_diff_report(result)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
        print(f"PDF audit written to: {args.out}")
    else:
        print(report)
    return 0
