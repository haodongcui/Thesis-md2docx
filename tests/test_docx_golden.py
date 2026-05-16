from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

from thesis_md2docx.exporter import write_docx


GOLDEN_DOCX_PART_HASHES = {
    "[Content_Types].xml": "e24a2dc38cbdc1b8b97174a7bfa3d94f7344cfa838eccf045bb3bfb30315ebc2",
    "_rels/.rels": "f2ee5d069d316d080de4513502475fc76cbd64a7c536cf2420faad30a053aaae",
    "docProps/app.xml": "fce1d0ca26f687eabbc9465481916002bebe2b7e31cfc53c83967485475b98fc",
    "word/_rels/document.xml.rels": "0b085468b60ffb986f83f6a2472a05a1f8a1991c36e923d30c488a67845d4e8c",
    "word/document.xml": "e06fac9874b870961bae8bb31616ebecf6365e754c2da53244d01d2d8dfc4a44",
    "word/styles.xml": "1e43ea76518c226f37fbd926c63673211ac9e224d0f90b4271f62d4c89c85eb2",
    "word/numbering.xml": "518b400dc1f44d7285a3fa090f826666b7d34f9631de95b3e0e142cbe74a5298",
    "word/settings.xml": "818538b4906badd3b42a2ab7881629d900267cf13f3de9c99d124eeabbb7479e",
    "word/fontTable.xml": "f04114bfe1870c72ebda9679ff939660c8c34149fa973fa82901a89f4e3cea3b",
    "word/header1.xml": "0b4a9430cdcbfc302091fe43bfc2aed69247c19c19eee28cb99fa58385cf1092",
    "word/header2.xml": "619c6194a3415515b3c5145badfe7e35d75cd3de154631632a9bec1fb7ecc48d",
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
