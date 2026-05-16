from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .constants import (
    DEFAULT_DPI,
    EMU_PER_INCH,
    IMAGE_CONTENT_TYPES,
    MAX_IMAGE_HEIGHT_IN,
    MAX_IMAGE_WIDTH_IN,
)

try:
    from PIL import Image
except ImportError:  # pragma: no cover - optional dependency in some environments
    Image = None


@dataclass
class MediaImage:
    source_path: Path
    filename: str
    part_name: str
    rel_id: str
    content_type: str
    width_emu: int
    height_emu: int


class MediaManager:
    def __init__(self, *, starting_rid: int = 2, starting_image_index: int = 1) -> None:
        self.starting_rid = starting_rid
        self.next_rid = starting_rid
        self.next_image_index = starting_image_index
        self.next_docpr_id = 1
        self.images: list[MediaImage] = []
        self.by_path: dict[Path, MediaImage] = {}
        self.temp_dirs: list[Path] = []

    def register_image(self, source_path: Path) -> MediaImage | None:
        resolved = source_path.resolve()
        if resolved in self.by_path:
            return self.by_path[resolved]
        if not resolved.exists() or not resolved.is_file():
            return None

        suffix = resolved.suffix.lower().lstrip(".")
        content_type = IMAGE_CONTENT_TYPES.get(suffix)
        if not content_type:
            return None

        width_emu, height_emu = image_extent_emu(resolved)
        rel_id = f"rId{self.next_rid}"
        self.next_rid += 1
        filename = f"image{self.next_image_index}{resolved.suffix.lower()}"
        self.next_image_index += 1
        item = MediaImage(
            source_path=resolved,
            filename=filename,
            part_name=f"media/{filename}",
            rel_id=rel_id,
            content_type=content_type,
            width_emu=width_emu,
            height_emu=height_emu,
        )
        self.images.append(item)
        self.by_path[resolved] = item
        return item

    def next_drawing_id(self) -> int:
        current = self.next_docpr_id
        self.next_docpr_id += 1
        return current

    def image_extensions(self) -> set[str]:
        return {item.filename.rsplit(".", 1)[-1].lower() for item in self.images if "." in item.filename}

    def register_temp_dir(self, path: Path) -> None:
        self.temp_dirs.append(path)

    def cleanup_temp_dirs(self) -> None:
        for path in self.temp_dirs:
            shutil.rmtree(path, ignore_errors=True)
        self.temp_dirs.clear()


def image_extent_emu(path: Path) -> tuple[int, int]:
    default_width = int(MAX_IMAGE_WIDTH_IN * EMU_PER_INCH)
    default_height = int(3.8 * EMU_PER_INCH)
    if Image is None:
        return default_width, default_height

    try:
        with Image.open(path) as img:
            width_px, height_px = img.size
            dpi_info = img.info.get("dpi", (DEFAULT_DPI, DEFAULT_DPI))
    except Exception:
        return default_width, default_height

    if width_px <= 0 or height_px <= 0:
        return default_width, default_height

    try:
        dpi_x = float(dpi_info[0]) if dpi_info and dpi_info[0] else DEFAULT_DPI
        dpi_y = float(dpi_info[1]) if dpi_info and len(dpi_info) > 1 and dpi_info[1] else dpi_x
    except (TypeError, ValueError):
        dpi_x = dpi_y = DEFAULT_DPI

    dpi_x = dpi_x if dpi_x > 1 else DEFAULT_DPI
    dpi_y = dpi_y if dpi_y > 1 else DEFAULT_DPI

    width_emu = int(width_px / dpi_x * EMU_PER_INCH)
    height_emu = int(height_px / dpi_y * EMU_PER_INCH)

    max_width_emu = int(MAX_IMAGE_WIDTH_IN * EMU_PER_INCH)
    max_height_emu = int(MAX_IMAGE_HEIGHT_IN * EMU_PER_INCH)
    scale = min(
        1.0,
        max_width_emu / width_emu if width_emu else 1.0,
        max_height_emu / height_emu if height_emu else 1.0,
    )
    width_emu = max(1, int(width_emu * scale))
    height_emu = max(1, int(height_emu * scale))
    return width_emu, height_emu


def fit_extent_emu(
    width_emu: int,
    height_emu: int,
    *,
    max_width_emu: int,
    max_height_emu: int,
) -> tuple[int, int]:
    if width_emu <= 0 or height_emu <= 0:
        return max_width_emu, max_height_emu
    scale = min(
        1.0,
        max_width_emu / width_emu if width_emu else 1.0,
        max_height_emu / height_emu if height_emu else 1.0,
    )
    return max(1, int(width_emu * scale)), max(1, int(height_emu * scale))
