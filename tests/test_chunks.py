import dataclasses
import json

import pytest

from ai_governance.chunks import Chunk, check_counts, write_jsonl
from ai_governance.errors import IngestError


def test_chunk_fields():
    chunk = Chunk(
        id="eu-ai-act:article-6",
        source="EU AI Act",
        section_id="Article 6",
        title="Classification rules for high-risk AI systems",
        url="http://data.europa.eu/eli/reg/2024/1689/oj#art_6",
        version="OJ L, 2024/1689, 12.7.2024 (original text, not consolidated)",
        text="lorem ipsum",
    )
    assert chunk.id == "eu-ai-act:article-6"


def make_chunk(section_id: str, text: str = "Sample text.") -> Chunk:
    return Chunk(
        id=f"test:{section_id.lower().replace(' ', '-')}",
        source="Test",
        section_id=section_id,
        title="A title",
        url="https://example.org",
        version="v1",
        text=text,
    )


def test_check_counts_passes_on_match():
    chunks = [make_chunk("Article 1"), make_chunk("Article 2"), make_chunk("Annex I")]
    check_counts("EU AI Act", chunks, {"article": 2, "annex": 1})


def test_check_counts_mismatch_names_source_and_both_counts():
    chunks = [make_chunk("Article 1"), make_chunk("Annex I")]
    with pytest.raises(IngestError) as exc:
        check_counts("EU AI Act", chunks, {"article": 2, "annex": 1})
    message = str(exc.value)
    assert "EU AI Act" in message
    assert "annex 1, article 2" in message
    assert "annex 1, article 1" in message


def test_check_counts_counts_nist_by_function():
    chunks = [make_chunk("GOVERN 1.1"), make_chunk("MAP 1.1")]
    with pytest.raises(IngestError):
        check_counts("NIST AI RMF 1.0", chunks, {"govern": 2})


def test_write_jsonl_one_object_per_line_in_field_order(tmp_path):
    path = tmp_path / "chunks.jsonl"
    write_jsonl([make_chunk("Article 1"), make_chunk("Article 2")], path)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert list(json.loads(lines[0])) == [f.name for f in dataclasses.fields(Chunk)]
    assert json.loads(lines[1])["section_id"] == "Article 2"


def test_write_jsonl_keeps_non_ascii(tmp_path):
    path = tmp_path / "chunks.jsonl"
    write_jsonl([make_chunk("Article 1", text="Règlement (UE) 2024/1689 – “AI”")], path)
    assert "Règlement (UE) 2024/1689 – “AI”" in path.read_text(encoding="utf-8")


def test_failed_check_leaves_existing_file_unchanged(tmp_path):
    path = tmp_path / "chunks.jsonl"
    path.write_bytes(b"previous run\n")
    chunks = [make_chunk("Article 1")]
    with pytest.raises(IngestError):
        check_counts("EU AI Act", chunks, {"article": 2})
        write_jsonl(chunks, path)
    assert path.read_bytes() == b"previous run\n"


def test_interrupted_write_leaves_existing_file_and_no_temp(tmp_path, monkeypatch):
    path = tmp_path / "chunks.jsonl"
    path.write_bytes(b"previous run\n")

    def fail(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr("ai_governance.chunks.json.dumps", fail)
    with pytest.raises(KeyboardInterrupt):
        write_jsonl([make_chunk("Article 1")], path)
    assert path.read_bytes() == b"previous run\n"
    assert [p.name for p in tmp_path.iterdir()] == ["chunks.jsonl"]
