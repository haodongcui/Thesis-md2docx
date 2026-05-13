from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .common import PdfError
from .registry import BACKENDS, backend_names, get_backend


def add_backend_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--tmp-root",
        type=Path,
        default=None,
        help="Temporary root directory used by the selected PDF backend.",
    )
    parser.add_argument(
        "--keep-tmp",
        action="store_true",
        default=None,
        help="Keep temporary files for debugging.",
    )
    parser.add_argument(
        "--no-update-fields",
        action="store_true",
        default=None,
        help="Do not refresh Word/LibreOffice fields before exporting PDF.",
    )
    parser.add_argument(
        "--vbs-template",
        type=Path,
        default=None,
        help="Word backend only: override the bundled VBS export template.",
    )
    parser.add_argument(
        "--skip-word-check",
        action="store_true",
        default=None,
        help="Word backend only: skip the upfront COM availability check.",
    )
    parser.add_argument(
        "--soffice",
        type=Path,
        default=None,
        help="LibreOffice backend only: path to libreoffice/soffice executable.",
    )


def convert_from_args(args: argparse.Namespace) -> Path:
    backend = get_backend(args.backend)
    return backend.convert(args)


def run_doctor(backend: str) -> int:
    normalized = backend.strip().lower()
    if normalized != "auto":
        return get_backend(normalized).doctor()

    statuses: list[int] = []
    for idx, candidate in enumerate(BACKENDS):
        if idx:
            print()
        statuses.append(candidate.doctor())
    return 0 if any(status == 0 for status in statuses) else 1


def build_parser() -> argparse.ArgumentParser:
    backend_help = ", ".join(backend_names())
    parser = argparse.ArgumentParser(
        prog="python -m xju_thesis_md2docx.pdf",
        description="Convert DOCX to PDF with Word or LibreOffice backends.",
        epilog=(
            "Examples:\n"
            "  python -m xju_thesis_md2docx.pdf --backend word thesis.docx thesis.pdf\n"
            "  python -m xju_thesis_md2docx.pdf --backend libreoffice thesis.docx thesis.pdf\n"
            "  python -m xju_thesis_md2docx.pdf doctor --backend auto"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--backend",
        default=os.environ.get("XJU_DOCX2PDF_BACKEND", "word"),
        help=f"PDF backend: {backend_help}. Defaults to $XJU_DOCX2PDF_BACKEND or word.",
    )
    parser.add_argument("--list-backends", action="store_true", help="Print supported backend names.")
    parser.add_argument("input", nargs="?", help="Input DOCX path.")
    parser.add_argument("output", nargs="?", help="Output PDF path. Defaults to input with .pdf suffix.")
    add_backend_options(parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "doctor":
        doctor_parser = argparse.ArgumentParser(prog="python -m xju_thesis_md2docx.pdf doctor")
        doctor_parser.add_argument(
            "--backend",
            default="auto",
            help=f"Backend to check: {', '.join(backend_names())}. Defaults to auto.",
        )
        args = doctor_parser.parse_args(argv[1:])
        return run_doctor(args.backend)

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_backends:
        print("\n".join(backend_names()))
        return 0
    if not args.input:
        parser.print_usage(sys.stderr)
        return 2

    try:
        convert_from_args(args)
    except PdfError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
