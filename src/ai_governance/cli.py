import argparse
import sys
from pathlib import Path

from .chunks import check_counts, write_jsonl
from .errors import IngestError
from .sources import SOURCES, fetch


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-governance")
    commands = parser.add_subparsers(dest="command")
    ingest = commands.add_parser("ingest", help="download the sources and write chunks.jsonl")
    ingest.add_argument("--refresh", action="store_true", help="download again even if cached")
    ingest.add_argument("--data-dir", default="data", help=argparse.SUPPRESS)

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    try:
        _ingest(Path(args.data_dir), args.refresh)
    except IngestError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


def _ingest(data_dir: Path, refresh: bool) -> None:
    all_chunks = []
    lines = []
    for source in SOURCES:
        data, status = fetch(source, data_dir / "raw", refresh)
        chunks = source.chunks(data)
        check_counts(source.name, chunks, source.expected_counts)
        all_chunks.extend(chunks)
        lines.append(f"{source.name}: {status}, {len(chunks)} chunks")

    out = data_dir / "chunks.jsonl"
    try:
        write_jsonl(all_chunks, out)
    except OSError as e:
        raise IngestError(f"cannot write {out}: {e}") from e
    for line in lines:
        print(line)
    print(f"Wrote {len(all_chunks)} chunks to {out}")
