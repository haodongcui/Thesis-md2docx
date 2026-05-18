from __future__ import annotations

from PIL import Image

from thesis_md2docx.pdf_compare import PdfDiff, compare_page_images, pdf_diff_report


def test_compare_page_images_counts_changed_pixels(tmp_path) -> None:
    reference = tmp_path / "reference.png"
    candidate = tmp_path / "candidate.png"
    diff_path = tmp_path / "diff" / "page-1.png"

    Image.new("RGB", (3, 2), "white").save(reference)
    image = Image.new("RGB", (3, 2), "white")
    image.putpixel((1, 0), (0, 0, 0))
    image.save(candidate)

    result = compare_page_images(reference, candidate, page=1, diff_path=diff_path)

    assert result.reference_size == (3, 2)
    assert result.candidate_size == (3, 2)
    assert result.changed_pixels == 1
    assert result.total_pixels == 6
    assert result.changed_ratio == 1 / 6
    assert result.bbox == (1, 0, 2, 1)
    assert diff_path.is_file()


def test_pdf_diff_report_summarizes_changed_pages(tmp_path) -> None:
    reference = tmp_path / "reference.png"
    candidate = tmp_path / "candidate.png"
    Image.new("RGB", (2, 2), "white").save(reference)
    Image.new("RGB", (3, 2), "white").save(candidate)
    page = compare_page_images(reference, candidate, page=1)
    result = PdfDiff(
        reference=tmp_path / "reference.pdf",
        candidate=tmp_path / "candidate.pdf",
        dpi=144,
        pages=(page,),
    )

    report = pdf_diff_report(result)

    assert "# PDF Pixel Audit" in report
    assert "- Changed pages: 1" in report
    assert "| 1 | 2x2 | 3x2 |" in report
