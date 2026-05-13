from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import libreoffice, word
from .common import PdfError, is_windows, is_wsl


ConvertFunc = Callable[[argparse.Namespace], Path]
DoctorFunc = Callable[[], int]
AvailableFunc = Callable[[], bool]


@dataclass(frozen=True)
class PdfBackend:
    name: str
    aliases: tuple[str, ...]
    description: str
    convert: ConvertFunc
    doctor: DoctorFunc
    available: AvailableFunc


def word_available() -> bool:
    if not (is_windows() or is_wsl()):
        return False
    ok, _ = word._word_com_check()
    return ok


def libreoffice_available() -> bool:
    found = libreoffice.find_soffice()
    return found is not None and found.exists()


def convert_word(args: argparse.Namespace) -> Path:
    update_fields = None if args.no_update_fields is None else not args.no_update_fields
    return word.convert(
        args.input,
        args.output,
        tmp_root=args.tmp_root,
        vbs_template=args.vbs_template,
        keep_tmp=args.keep_tmp,
        skip_word_check=args.skip_word_check,
        update_fields=update_fields,
    )


def convert_libreoffice(args: argparse.Namespace) -> Path:
    update_fields = None if args.no_update_fields is None else not args.no_update_fields
    return libreoffice.convert(
        args.input,
        args.output,
        soffice=args.soffice,
        tmp_root=args.tmp_root,
        keep_tmp=args.keep_tmp,
        update_fields=update_fields,
    )


BACKENDS: tuple[PdfBackend, ...] = (
    PdfBackend(
        name="word",
        aliases=(),
        description="Windows Microsoft Word COM automation; highest fidelity.",
        convert=convert_word,
        doctor=word.doctor,
        available=word_available,
    ),
    PdfBackend(
        name="libreoffice",
        aliases=("lo",),
        description="LibreOffice headless conversion; portable preview backend.",
        convert=convert_libreoffice,
        doctor=libreoffice.doctor,
        available=libreoffice_available,
    ),
)

BACKEND_BY_NAME: dict[str, PdfBackend] = {}
for backend in BACKENDS:
    BACKEND_BY_NAME[backend.name] = backend
    for alias in backend.aliases:
        BACKEND_BY_NAME[alias] = backend


def backend_names(*, include_auto: bool = True) -> list[str]:
    names = [backend.name for backend in BACKENDS]
    if include_auto:
        names.append("auto")
    return names


def get_backend(name: str) -> PdfBackend:
    normalized = name.strip().lower()
    if normalized == "auto":
        return choose_backend()
    backend = BACKEND_BY_NAME.get(normalized)
    if backend is None:
        raise PdfError(f"unknown backend: {name}")
    return backend


def choose_backend() -> PdfBackend:
    for backend in BACKENDS:
        if backend.available():
            return backend
    raise PdfError("no available DOCX to PDF backend found")
