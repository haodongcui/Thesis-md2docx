from __future__ import annotations

from thesis_md2docx.main import main


def test_direct_export_writes_docx_to_output_dir(tmp_path) -> None:
    status = main(
        [
            "example/thesis-demo.md",
            "--out",
            str(tmp_path),
            "--no-formula-conversion",
        ]
    )

    assert status == 0
    assert (tmp_path / "thesis-demo.docx").is_file()


def test_direct_pages_requires_pdf(capsys) -> None:
    status = main(["example/thesis-demo.md", "--pages"])

    captured = capsys.readouterr()
    assert status == 1
    assert "--pages requires --pdf" in captured.err


def test_profiles_alias_lists_registered_profiles(capsys) -> None:
    status = main(["profiles"])

    captured = capsys.readouterr()
    assert status == 0
    assert "xju-undergraduate-thesis" in captured.out


def test_backends_alias_lists_pdf_backends(capsys) -> None:
    status = main(["backends"])

    captured = capsys.readouterr()
    assert status == 0
    assert "word" in captured.out
    assert "libreoffice" in captured.out
    assert "auto" in captured.out
