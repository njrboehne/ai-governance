"""NIST AI RMF 1.0 PDF -> text -> one chunk per Core subcategory."""

import io
import re
from collections.abc import Callable

import pypdf

from .chunks import Chunk
from .errors import IngestError

SOURCE = "NIST AI RMF 1.0"

FUNCTIONS = "GOVERN|MAP|MEASURE|MANAGE"
START = "GOVERN 1:"
END = re.compile(r"^6\. AI RMF Profiles")
CATEGORY = re.compile(rf"^((?:{FUNCTIONS}) \d+):\s*(.*)$")
SUBCATEGORY = re.compile(rf"^((?:{FUNCTIONS}) \d+\.\d+):\s*(.*)$")
SECTION_HEADING = re.compile(r"^\d+(\.\d+)?\.? [A-Z]")
FURNITURE = re.compile(
    r"^(Categories Subcategories|Continued on next page|Page \d+"
    r"|NIST AI 100-1 AI RMF 1\.0|Table \d+: .*)$"
)
# The only compound the Core breaks at a line end. Add entries only when a pinned source needs them.
KEEP_HYPHEN = {"context"}


def parse(data: bytes, *, version: str, cite: Callable[[str], str]) -> list[Chunk]:
    return parse_text(extract_text(data), version=version, cite=cite)


def extract_text(data: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() for page in reader.pages)


def parse_text(text: str, *, version: str, cite: Callable[[str], str]) -> list[Chunk]:
    """Walk the Core tables line by line, collecting category and subcategory statements."""
    lines = _core_region(text.splitlines())
    categories: dict[str, list[str]] = {}
    subcategories: list[tuple[str, str, list[str]]] = []
    category = ""
    statement: list[str] = []  # where the next plain line goes
    skipping = False

    for line in lines:
        if FURNITURE.match(line):
            # A page break. Until the next subcategory, lines continue the category
            # statement (GOVERN 4's tail lands after GOVERN 4.1 on the next page).
            statement = categories[category]
        elif m := SUBCATEGORY.match(line):
            statement = [m[2]]
            subcategories.append((m[1], category, statement))
            skipping = False
        elif m := CATEGORY.match(line):
            category = m[1]
            statement = categories[category] = [m[2]] if m[2] else []
            skipping = False
        elif SECTION_HEADING.match(line):
            # A function introduction follows; skip it until the next table.
            skipping = True
        elif not skipping:
            statement.append(line)

    return [
        Chunk(
            id=f"nist-ai-rmf:{section_id.lower().replace(' ', '-')}",
            source=SOURCE,
            section_id=section_id,
            title=f"{category}: {repair(categories[category])}",
            url=cite(section_id),
            version=version,
            text=repair(statement),
        )
        for section_id, category, statement in subcategories
    ]


def _core_region(lines: list[str]) -> list[str]:
    start = next((i for i, line in enumerate(lines) if line.startswith(START)), None)
    if start is None:
        raise IngestError(f"{SOURCE}: start marker {START!r} not found")
    end = next((i for i in range(start, len(lines)) if END.match(lines[i])), None)
    if end is None:
        raise IngestError(f"{SOURCE}: end marker '6. AI RMF Profiles' not found")
    return lines[start:end]


def repair(lines: list[str]) -> str:
    """Rejoin line-break hyphens, restore a space lost before a function name, collapse spaces."""
    text = re.sub(r"(\w+)-\n(?=[a-z])", _rejoin, "\n".join(lines))
    text = re.sub(rf"(?<=[a-z])(?={FUNCTIONS})", " ", text)
    return " ".join(text.split())


def _rejoin(m: re.Match) -> str:
    word = m[1]
    return f"{word}-" if word in KEEP_HYPHEN else word
