from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

from thesis_md2docx.exporter import write_docx


GOLDEN_DOCX_PART_HASHES = {
    "[Content_Types].xml": "65dd97bf5812129aa57d18f0597ed4413819b252cc4d08b402b939d5d8840597",
    "_rels/.rels": "f2ee5d069d316d080de4513502475fc76cbd64a7c536cf2420faad30a053aaae",
    "docProps/app.xml": "fce1d0ca26f687eabbc9465481916002bebe2b7e31cfc53c83967485475b98fc",
    "word/_rels/document.xml.rels": "0f4b26c2cd5cd48821c5749b9f1a59c9b53cb99eaae11114a50ebdda7017e001",
    "word/document.xml": "059a40da81df0f55e6dc7dccd9a1aecff96a3ad8266b5e161de041b6202fbc47",
    "word/styles.xml": "97fc664286ea43ef093d35f1b6d8034c9a5457a48982ff3a0c4ab40a0e31d0d9",
    "word/numbering.xml": "518b400dc1f44d7285a3fa090f826666b7d34f9631de95b3e0e142cbe74a5298",
    "word/settings.xml": "818538b4906badd3b42a2ab7881629d900267cf13f3de9c99d124eeabbb7479e",
    "word/fontTable.xml": "f04114bfe1870c72ebda9679ff939660c8c34149fa973fa82901a89f4e3cea3b",
    "word/header1.xml": "0b4a9430cdcbfc302091fe43bfc2aed69247c19c19eee28cb99fa58385cf1092",
    "word/footer1.xml": "2e2134c75e0675ca2c6ff58d3234368df476a896e173869a2d0989a251774ff2",
    "word/footer2.xml": "67cbd25e3a795d9df3082a972d0c9a4488a15585fdf725cfc62ad90778700ac5",
}


def _part_hash(docx_path: Path, part_name: str) -> str:
    with ZipFile(docx_path) as zf:
        return sha256(zf.read(part_name)).hexdigest()


def test_xju_example_docx_matches_golden_ooxml_parts(tmp_path: Path) -> None:
    output_path = tmp_path / "thesis-demo.docx"
    write_docx(
        Path("example/thesis-demo.md"),
        output_path,
        enable_formula_conversion=False,
        profile="xju-undergraduate-thesis",
    )

    with ZipFile(output_path) as zf:
        names = set(zf.namelist())

    for part_name, expected_hash in GOLDEN_DOCX_PART_HASHES.items():
        assert part_name in names
        assert _part_hash(output_path, part_name) == expected_hash, part_name
