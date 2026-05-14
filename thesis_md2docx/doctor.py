from __future__ import annotations

import importlib.util
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from .constants import (
    COVER_EMBLEM_NAME,
    COVER_WORDMARK_NAME,
    DEFAULT_COVER_ASSETS_DIR,
    LATEX2OMML_NODE_DIR,
    LATEX2OMML_NODE_REQUIRED_MODULES,
    LATEX2OMML_NODE_SCRIPT,
)
from .layout import validate_front_matter_plan
from .pdf.main import run_doctor as run_pdf_doctor
from .profiles import DEFAULT_PROFILE_NAME, get_profile, profile_names
from .styles import validate_body_render_profile, validate_style_catalog


def _print_check(ok: bool, message: str) -> bool:
    stream = sys.stdout if ok else sys.stderr
    prefix = "[ok]" if ok else "[fail]"
    print(f"{prefix} {message}", file=stream)
    return ok


def _print_warn(message: str) -> None:
    print(f"[warn] {message}")


def _command_version(command: list[str]) -> str | None:
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = (result.stdout or "").strip().splitlines()
    if result.returncode == 0 and output:
        return output[0]
    return None


def _check_python() -> int:
    print("Core Markdown-to-DOCX environment check")
    print()
    status = 0

    version = platform.python_version()
    if sys.version_info >= (3, 10):
        _print_check(True, f"Python: {version} ({sys.executable})")
    else:
        _print_check(False, f"Python >= 3.10 is recommended; found {version} ({sys.executable})")
        status = 1

    pip_version = _command_version([sys.executable, "-m", "pip", "--version"])
    if pip_version:
        _print_check(True, f"pip: {pip_version}")
    else:
        _print_warn(
            "pip is not available for this Python; install python3-pip or use an environment that has pip"
        )

    if importlib.util.find_spec("PIL") is not None:
        try:
            from PIL import Image

            _print_check(True, f"Pillow: {Image.__version__}")
        except Exception as exc:  # pragma: no cover - defensive diagnostic only
            _print_check(False, f"Pillow import failed: {exc}")
            status = 1
    else:
        _print_check(False, "Pillow is not installed; run: python -m pip install -r requirements.txt")
        status = 1

    return status


def _check_profiles() -> int:
    status = 0
    names = profile_names()
    if names:
        _print_check(True, f"profiles: {', '.join(names)}")
    else:
        _print_check(False, "no thesis profiles are registered")
        status = 1

    try:
        profile = get_profile(DEFAULT_PROFILE_NAME)
        _print_check(True, f"default profile: {profile.name}")
        catalog = profile.style_catalog()
        roles = profile.style_roles()
        front_issues = validate_front_matter_plan(profile.front_matter_spec(), profile.front_matter_plan())
        missing_roles = roles.missing_roles(profile.required_style_roles())
        issues = validate_style_catalog(catalog, roles)
        body_issues = validate_body_render_profile(profile.body_style_profile(), catalog)
        if front_issues:
            for issue in front_issues:
                _print_check(False, f"profile front matter issue: {issue.message}")
            status = 1
        if missing_roles:
            for role in missing_roles:
                _print_check(False, f"profile missing required style role: {role}")
            status = 1
        if issues:
            for issue in issues:
                _print_check(False, f"profile style issue: {issue.message}")
            status = 1
        if body_issues:
            for issue in body_issues:
                _print_check(False, f"profile body render issue: {issue.message}")
            status = 1
        if not front_issues and not missing_roles and not issues and not body_issues:
            _print_check(True, f"profile styles: {len(catalog.styles)} styles")
        else:
            _print_warn("profile style checks failed; fix the profile before exporting production DOCX files")
    except ValueError as exc:
        _print_check(False, str(exc))
        status = 1

    return status


def _check_cover_assets() -> int:
    status = 0
    if not DEFAULT_COVER_ASSETS_DIR.is_dir():
        _print_check(False, f"default cover asset directory not found: {DEFAULT_COVER_ASSETS_DIR}")
        return 1

    _print_check(True, f"default cover asset directory: {DEFAULT_COVER_ASSETS_DIR}")
    for filename in [COVER_EMBLEM_NAME, COVER_WORDMARK_NAME]:
        path = DEFAULT_COVER_ASSETS_DIR / filename
        if path.is_file():
            _print_check(True, f"cover asset: {filename}")
        else:
            _print_check(False, f"cover asset missing: {path}")
            status = 1
    return status


def _check_formula_converter() -> int:
    status = 0
    print()
    print("Formula conversion check")
    print()

    if LATEX2OMML_NODE_SCRIPT.is_file():
        _print_check(True, f"converter script: {LATEX2OMML_NODE_SCRIPT}")
    else:
        _print_check(False, f"converter script missing: {LATEX2OMML_NODE_SCRIPT}")
        status = 1

    node = shutil.which("node")
    if node:
        version = _command_version([node, "--version"])
        suffix = f" ({version})" if version else ""
        _print_check(True, f"node: {node}{suffix}")
    else:
        _print_warn("node not found; formulas will be kept as LaTeX text unless --no-formula-conversion is used")

    npm = shutil.which("npm")
    if npm:
        version = _command_version([npm, "--version"])
        suffix = f" ({version})" if version else ""
        _print_check(True, f"npm: {npm}{suffix}")
    else:
        _print_warn("npm not found; cannot install optional formula converter dependencies")

    missing = [path for path in LATEX2OMML_NODE_REQUIRED_MODULES if not path.exists()]
    if missing:
        _print_warn(
            "formula converter dependencies are not installed; run: "
            f"cd {LATEX2OMML_NODE_DIR} && npm install"
        )
        for path in missing:
            _print_warn(f"missing module: {path.relative_to(LATEX2OMML_NODE_DIR)}")
    else:
        _print_check(True, "formula converter dependencies installed")

    return status


def _check_preview_tools() -> int:
    print()
    print("Optional preview tools")
    print()

    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        version = _command_version([pdftoppm, "-v"])
        suffix = f" ({version})" if version else ""
        _print_check(True, f"pdftoppm: {pdftoppm}{suffix}")
    else:
        _print_warn("pdftoppm not found; install poppler-utils if you want to render PDF pages to PNG")

    return 0


def run_doctor(backend: str = "none") -> int:
    statuses = [
        _check_python(),
        _check_profiles(),
        _check_cover_assets(),
        _check_formula_converter(),
        _check_preview_tools(),
    ]

    normalized_backend = backend.strip().lower()
    if normalized_backend != "none":
        print()
        statuses.append(run_pdf_doctor(normalized_backend))
    else:
        print()
        _print_warn("PDF backend check skipped; pass --backend word, --backend libreoffice, or --backend auto")
    return 0 if all(status == 0 for status in statuses) else 1
