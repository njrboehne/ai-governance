import json
import os
import tempfile
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from .errors import IngestError


@dataclass(frozen=True)
class Chunk:
    id: str
    source: str
    section_id: str
    title: str
    url: str
    version: str
    text: str


def kind(chunk: Chunk) -> str:
    """The chunk's kind for counting: "Article 6" -> "article", "GOVERN 1.1" -> "govern"."""
    return chunk.section_id.split()[0].lower()


def check_counts(source: str, chunks: list[Chunk], expected: dict[str, int]) -> None:
    """Raise IngestError unless the chunks match the expected count for each kind."""
    found = dict(Counter(kind(c) for c in chunks))
    if found != expected:
        raise IngestError(
            f"{source}: expected {_format_counts(expected)} chunks, found {_format_counts(found)}"
        )


def _format_counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "none"


def write_jsonl(chunks: list[Chunk], path: Path) -> None:
    """Write one JSON object per line, replacing `path` only once the whole file is written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            for chunk in chunks:
                f.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
