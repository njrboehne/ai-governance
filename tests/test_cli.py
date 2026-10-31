"""Offline end-to-end runs of `ai-governance ingest` with fixture sources (6.2)."""

import hashlib
import io
import json
from dataclasses import replace
from pathlib import Path

import pytest

from ai_governance import cli, main, nist_ai_rmf, sources
from ai_governance.sources import EU_AI_ACT, NIST_AI_RMF

FIXTURES = Path(__file__).parent / "fixtures"
EU_BODY = (FIXTURES / "eu_ai_act_sample.xhtml").read_bytes()
NIST_BODY = (FIXTURES / "nist_ai_rmf_sample.txt").read_bytes()


def parse_nist_text(data: bytes, **kwargs):
    """The NIST parser with PDF extraction swapped out: the fixture is already text."""
    return nist_ai_rmf.parse_text(data.decode("utf-8"), **kwargs)


FIXTURE_SOURCES = [
    replace(
        EU_AI_ACT,
        download_url="https://example.org/eu.xhtml",
        sha256=hashlib.sha256(EU_BODY).hexdigest(),
        expected_counts={"article": 2, "annex": 1},
    ),
    replace(
        NIST_AI_RMF,
        download_url="https://example.org/nist.pdf",
        sha256=hashlib.sha256(NIST_BODY).hexdigest(),
        expected_counts={"govern": 4, "map": 1},
        parse=parse_nist_text,
    ),
]
BODIES = {"https://example.org/eu.xhtml": EU_BODY, "https://example.org/nist.pdf": NIST_BODY}


class FakeResponse(io.BytesIO):
    status = 200


@pytest.fixture
def downloads(monkeypatch):
    """Use the fixture sources and serve their bodies offline, recording each request."""
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        return FakeResponse(BODIES[request.full_url])

    monkeypatch.setattr(cli, "SOURCES", FIXTURE_SOURCES)
    monkeypatch.setattr(sources, "urlopen", fake_urlopen)
    return calls


def ingest(data_dir: Path) -> int:
    return main(["ingest", "--data-dir", str(data_dir)])


def test_first_run_downloads_writes_chunks_and_reports_counts(tmp_path, downloads, capsys):
    assert ingest(tmp_path) == 0

    out = capsys.readouterr().out
    assert "EU AI Act: downloaded, 3 chunks" in out
    assert "NIST AI RMF 1.0: downloaded, 5 chunks" in out
    lines = (tmp_path / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]
    assert [r["source"] for r in records] == ["EU AI Act"] * 3 + ["NIST AI RMF 1.0"] * 5
    saved = sorted(p.name for p in (tmp_path / "raw").iterdir())
    assert saved == sorted(s.filename for s in FIXTURE_SOURCES)


def test_second_run_is_offline_and_reports_cached(tmp_path, downloads, capsys):
    ingest(tmp_path)
    downloads.clear()
    capsys.readouterr()

    assert ingest(tmp_path) == 0
    assert downloads == []
    out = capsys.readouterr().out
    assert "EU AI Act: cached, 3 chunks" in out
    assert "NIST AI RMF 1.0: cached, 5 chunks" in out


def test_count_mismatch_returns_1_and_keeps_existing_chunks(
    tmp_path, downloads, monkeypatch, capsys
):
    existing = tmp_path / "chunks.jsonl"
    existing.write_bytes(b"previous run\n")
    wrong = [FIXTURE_SOURCES[0], replace(FIXTURE_SOURCES[1], expected_counts={"govern": 72})]
    monkeypatch.setattr(cli, "SOURCES", wrong)

    assert ingest(tmp_path) == 1
    assert "NIST AI RMF 1.0" in capsys.readouterr().err
    assert existing.read_bytes() == b"previous run\n"


@pytest.mark.parametrize(
    ("args", "message"),
    [
        ([], "--refresh"),
        (["--refresh"], "does not match its checksum"),
    ],
    ids=["corrupt-cache", "upstream-changed"],
)
def test_checksum_failure_returns_1_and_keeps_existing_chunks(
    tmp_path, downloads, monkeypatch, capsys, args, message
):
    ingest(tmp_path)
    eu_file = tmp_path / "raw" / FIXTURE_SOURCES[0].filename
    existing = (tmp_path / "chunks.jsonl").read_bytes()
    if args:
        monkeypatch.setitem(BODIES, "https://example.org/eu.xhtml", b"changed upstream")
    else:
        eu_file.write_bytes(b"corrupted")
    cached = eu_file.read_bytes()

    assert main(["ingest", "--data-dir", str(tmp_path), *args]) == 1
    err = capsys.readouterr().err
    assert "EU AI Act" in err and message in err
    assert (tmp_path / "chunks.jsonl").read_bytes() == existing
    assert eu_file.read_bytes() == cached


def test_two_runs_in_separate_dirs_write_identical_bytes(tmp_path, downloads):
    ingest(tmp_path / "a")
    ingest(tmp_path / "b")

    first = (tmp_path / "a" / "chunks.jsonl").read_bytes()
    assert first == (tmp_path / "b" / "chunks.jsonl").read_bytes()
