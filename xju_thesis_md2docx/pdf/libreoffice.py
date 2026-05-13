from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from .common import (
    LIBREOFFICE_BACKEND_DIR,
    PdfError,
    bool_env,
    ensure_input_file,
    is_windows,
    print_check,
    resolve_output_path,
    resolve_path,
    which_any,
)


def _default_windows_soffice_paths() -> list[Path]:
    roots = [
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
    ]
    result: list[Path] = []
    for root in roots:
        if root:
            result.append(Path(root) / "LibreOffice" / "program" / "soffice.exe")
    return result


def find_soffice(raw: str | Path | None = None) -> Path | None:
    if raw:
        return resolve_path(raw)
    env_value = os.environ.get("XJU_LIBREOFFICE_BIN")
    if env_value:
        return resolve_path(env_value)

    found = which_any(["libreoffice", "soffice", "soffice.exe"])
    if found:
        return Path(found).resolve()

    if is_windows():
        for candidate in _default_windows_soffice_paths():
            if candidate.is_file():
                return candidate.resolve()
    return None


def _file_uri(path: Path) -> str:
    return path.resolve().as_uri()


def _base_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    if not is_windows():
        env.setdefault("SAL_USE_VCLPLUGIN", "gen")
    if extra:
        env.update(extra)
    return env


def _run_soffice(args: list[str], log_file: Path, env: dict[str, str]) -> None:
    with log_file.open("a", encoding="utf-8", errors="replace") as log:
        result = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, text=True, env=env)
    if result.returncode != 0:
        raise PdfError(f"LibreOffice command failed ({result.returncode}); see log: {log_file}")


def _write_export_macro(job_dir: Path) -> None:
    macro_template = LIBREOFFICE_BACKEND_DIR / "update_fields_and_export.xba"
    ensure_input_file(macro_template, "LibreOffice export macro template")
    macro_dir = job_dir / "profile" / "user" / "basic" / "Standard"
    macro_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(macro_template, macro_dir / "Module1.xba")


def _font_substitution_pairs() -> list[tuple[str, str]]:
    return [
        ("宋体", "SimSun"),
        ("新宋体", "NSimSun"),
        ("黑体", "SimHei"),
        ("楷体", "KaiTi"),
        ("楷体_GB2312", "KaiTi"),
        ("仿宋", "FangSong"),
        ("等线", "DengXian"),
    ]


def _font_name_map() -> dict[str, str]:
    return dict(_font_substitution_pairs())


def _write_font_substitution_config(profile_dir: Path) -> None:
    if not bool_env("XJU_LIBREOFFICE_DOCX2PDF_FONT_SUBSTITUTION", True):
        return

    user_dir = profile_dir / "user"
    user_dir.mkdir(parents=True, exist_ok=True)
    registry_path = user_dir / "registrymodifications.xcu"

    items = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<oor:items xmlns:oor="http://openoffice.org/2001/registry">',
        '<item oor:path="/org.openoffice.Office.Common/Font/Substitution">',
        '<prop oor:name="Replacement" oor:op="fuse"><value>true</value></prop>',
        "</item>",
    ]
    for idx, (source, target) in enumerate(_font_substitution_pairs()):
        items.extend(
            [
                '<item oor:path="/org.openoffice.Office.Common/Font/Substitution/FontPairs">',
                f'<node oor:name="_xju_{idx}" oor:op="replace">',
                f'<prop oor:name="ReplaceFont" oor:op="fuse"><value>{escape(source)}</value></prop>',
                f'<prop oor:name="SubstituteFont" oor:op="fuse"><value>{escape(target)}</value></prop>',
                '<prop oor:name="Always" oor:op="fuse"><value>true</value></prop>',
                '<prop oor:name="OnScreenOnly" oor:op="fuse"><value>false</value></prop>',
                "</node>",
                "</item>",
            ]
        )
    items.append("</oor:items>")
    registry_path.write_text("\n".join(items) + "\n", encoding="utf-8")


def _rewrite_docx_font_names_for_libreoffice(input_path: Path, output_path: Path) -> None:
    if not bool_env("XJU_LIBREOFFICE_DOCX2PDF_FONT_SUBSTITUTION", True):
        shutil.copy2(input_path, output_path)
        return

    replacements = _font_name_map()
    attr_names = ("ascii", "hAnsi", "eastAsia", "cs", "name", "val")

    def rewrite_xml(text: str) -> str:
        for source, target in replacements.items():
            for attr in attr_names:
                text = text.replace(f'w:{attr}="{source}"', f'w:{attr}="{target}"')
        return text

    with zipfile.ZipFile(input_path, "r") as src, zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename.startswith("word/") and info.filename.endswith(".xml"):
                try:
                    data = rewrite_xml(data.decode("utf-8")).encode("utf-8")
                except UnicodeDecodeError:
                    pass
            dst.writestr(info, data)


def convert(
    input_docx: str | Path,
    output_pdf: str | Path | None = None,
    *,
    soffice: str | Path | None = None,
    tmp_root: str | Path | None = None,
    keep_tmp: bool | None = None,
    update_fields: bool | None = None,
) -> Path:
    keep_tmp = bool_env("XJU_LIBREOFFICE_DOCX2PDF_KEEP_TMP", False) if keep_tmp is None else keep_tmp
    update_fields = (
        bool_env("XJU_LIBREOFFICE_DOCX2PDF_UPDATE_FIELDS", True)
        if update_fields is None
        else update_fields
    )

    soffice_path = find_soffice(soffice)
    if soffice_path is None:
        raise PdfError("LibreOffice executable not found. Install LibreOffice or set XJU_LIBREOFFICE_BIN.")
    if not soffice_path.exists():
        raise PdfError(f"LibreOffice executable not found: {soffice_path}")

    input_path = ensure_input_file(resolve_path(input_docx))
    output_path = resolve_output_path(input_path, output_pdf)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    raw_tmp_root = tmp_root or os.environ.get("XJU_LIBREOFFICE_DOCX2PDF_TMP_ROOT")
    if raw_tmp_root:
        tmp_root_path = resolve_path(raw_tmp_root)
    else:
        tmp_root_path = Path(tempfile.gettempdir()) / "xju_libreoffice_docx2pdf"
    tmp_root_path.mkdir(parents=True, exist_ok=True)

    job_dir = Path(tempfile.mkdtemp(prefix="job-", dir=str(tmp_root_path)))
    log_file = job_dir / "libreoffice.log"
    try:
        job_input = job_dir / "input.docx"
        job_output = job_dir / "input.pdf"
        profile_dir = job_dir / "profile"
        profile_dir.mkdir(parents=True, exist_ok=True)
        _write_font_substitution_config(profile_dir)
        _rewrite_docx_font_names_for_libreoffice(input_path, job_input)

        common_args = [
            str(soffice_path),
            "--headless",
            "--nologo",
            "--nodefault",
            "--nofirststartwizard",
            "--nolockcheck",
            "--norestore",
            f"-env:UserInstallation={_file_uri(profile_dir)}",
        ]

        if update_fields:
            _run_soffice(common_args + ["--terminate_after_init"], log_file, _base_env())
            _write_export_macro(job_dir)
            _run_soffice(
                common_args + ["macro:///Standard.Module1.ExportPdf()"],
                log_file,
                _base_env(
                    {
                        "XJU_LO_INPUT_URL": _file_uri(job_input),
                        "XJU_LO_OUTPUT_URL": _file_uri(job_output),
                    }
                ),
            )
        else:
            _run_soffice(
                common_args
                + [
                    "--convert-to",
                    "pdf:writer_pdf_Export",
                    "--outdir",
                    str(job_dir),
                    str(job_input),
                ],
                log_file,
                _base_env(),
            )

        if not job_output.is_file():
            raise PdfError(f"LibreOffice did not produce input.pdf; see log: {log_file}")
        shutil.copy2(job_output, output_path)
    finally:
        if keep_tmp:
            print(f"Temporary files kept at: {job_dir}")
        else:
            shutil.rmtree(job_dir, ignore_errors=True)

    print(f"PDF written to: {output_path}")
    print("Backend: libreoffice")
    return output_path


def doctor() -> int:
    print("libreoffice-docx2pdf environment check")
    print()
    status = 0

    soffice = find_soffice()
    if soffice is None:
        print_check(False, "LibreOffice executable not found in PATH")
        status = 1
    elif not soffice.exists():
        print_check(False, f"LibreOffice executable not found: {soffice}")
        status = 1
    else:
        print_check(True, f"LibreOffice executable: {soffice}")
        try:
            result = subprocess.run(
                [str(soffice), "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            version = (result.stdout or "").strip().splitlines()[0]
            if result.returncode == 0 and version:
                print_check(True, version)
            else:
                print_check(False, "could not read LibreOffice version")
                status = 1
        except OSError as exc:
            print_check(False, f"could not run LibreOffice: {exc}")
            status = 1

    fc_match = which_any(["fc-match"])
    if fc_match:
        print_check(True, f"fontconfig: {fc_match}")
        for font in ["SimSun", "Times New Roman", "Microsoft YaHei", "Noto Serif CJK SC"]:
            result = subprocess.run(
                [fc_match, font],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            match = (result.stdout or "").strip().splitlines()
            if match:
                print_check(True, f"font match for {font}: {match[0]}")
            else:
                print(f"[warn] no font match for {font}")
    elif is_windows():
        print("[warn] fc-match not found; font fallback is managed by Windows/LibreOffice")
    else:
        print("[warn] fc-match not found; cannot inspect font fallback")

    return status
