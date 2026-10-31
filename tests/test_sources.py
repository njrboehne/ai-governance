import hashlib
import io
import re
import urllib.error
from dataclasses import replace

import pytest

from ai_governance import sources
from ai_governance.errors import IngestError
from ai_governance.sources import EU_AI_ACT, NIST_AI_RMF, SOURCES, fetch

BODY = b"<html>source document</html>"


def make_source(body: bytes = BODY, **overrides):
    defaults = dict(
        name="Test Source",
        download_url="https://example.org/doc",
        filename="doc.xhtml",
        sha256=hashlib.sha256(body).hexdigest(),
        max_bytes=1024,
    )
    return replace(EU_AI_ACT, **(defaults | overrides))


class FakeResponse(io.BytesIO):
    def __init__(self, body: bytes, status: int = 200):
        super().__init__(body)
        self.status = status


def serve(monkeypatch, body: bytes = BODY, status: int = 200):
    """Replace urlopen with one that answers every request with `body`, recording the calls."""
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        return FakeResponse(body, status)

    monkeypatch.setattr(sources, "urlopen", fake_urlopen)
    return calls


def fail_with(monkeypatch, error: BaseException):
    def fake_urlopen(request, timeout):
        raise error

    monkeypatch.setattr(sources, "urlopen", fake_urlopen)


def files_in(raw_dir):
    return sorted(p.name for p in raw_dir.iterdir()) if raw_dir.exists() else []


# 3.1 Source records


def test_both_records_present():
    assert [s.name for s in SOURCES] == ["EU AI Act", "NIST AI RMF 1.0"]


@pytest.mark.parametrize("source", SOURCES, ids=lambda s: s.name)
def test_records_pin_a_sha256(source):
    assert re.fullmatch(r"[0-9a-f]{64}", source.sha256)


@pytest.mark.parametrize("source", SOURCES, ids=lambda s: s.name)
def test_headers_identify_the_project_not_a_person(source):
    assert source.headers["User-Agent"].startswith("ai-governance/")
    assert "@" not in " ".join(source.headers.values())


def test_citation_urls():
    assert EU_AI_ACT.cite("art_6") == "http://data.europa.eu/eli/reg/2024/1689/oj#art_6"
    assert NIST_AI_RMF.cite("GOVERN 1.1") == "https://doi.org/10.6028/NIST.AI.100-1"


def test_expected_counts_total_198():
    assert sum(sum(s.expected_counts.values()) for s in SOURCES) == 198


def test_chunks_use_the_record_version_and_citation():
    source = replace(EU_AI_ACT, version="test version", cite=lambda anchor: f"cite:{anchor}")
    xhtml = b'<div id="art_1"><p class="oj-ti-art">Article 1</p><p class="oj-sti-art">T</p></div>'
    [chunk] = source.chunks(xhtml)
    assert (chunk.version, chunk.url) == ("test version", "cite:art_1")


# 3.2 Fetch and verify


def test_matching_download_is_saved(tmp_path, monkeypatch):
    serve(monkeypatch)
    data, status = fetch(make_source(), tmp_path)
    assert (data, status) == (BODY, "downloaded")
    assert (tmp_path / "doc.xhtml").read_bytes() == BODY
    assert files_in(tmp_path) == ["doc.xhtml"]


def test_mismatch_raises_with_both_hashes_and_keeps_cached_file(tmp_path, monkeypatch):
    (tmp_path / "doc.xhtml").write_bytes(BODY)
    changed = b"<html>changed upstream</html>"
    serve(monkeypatch, body=changed)
    with pytest.raises(IngestError) as exc:
        fetch(make_source(), tmp_path, refresh=True)
    message = str(exc.value)
    assert "Test Source" in message
    assert hashlib.sha256(BODY).hexdigest() in message
    assert hashlib.sha256(changed).hexdigest() in message
    assert (tmp_path / "doc.xhtml").read_bytes() == BODY
    assert files_in(tmp_path) == ["doc.xhtml"]


@pytest.mark.parametrize(
    "error",
    [
        urllib.error.URLError("no route to host"),
        urllib.error.HTTPError("https://example.org/doc", 503, "Unavailable", {}, None),
        TimeoutError("timed out"),
    ],
    ids=["network", "http-503", "timeout"],
)
def test_network_errors_raise_and_leave_no_file(tmp_path, monkeypatch, error):
    fail_with(monkeypatch, error)
    with pytest.raises(IngestError, match="Test Source: download failed"):
        fetch(make_source(), tmp_path)
    assert files_in(tmp_path) == []


def test_http_503_names_the_status(tmp_path, monkeypatch):
    fail_with(monkeypatch, urllib.error.HTTPError("u", 503, "Unavailable", {}, None))
    with pytest.raises(IngestError, match="HTTP 503"):
        fetch(make_source(), tmp_path)


def test_202_is_a_failure(tmp_path, monkeypatch):
    serve(monkeypatch, body=b"", status=202)
    with pytest.raises(IngestError, match="HTTP 202"):
        fetch(make_source(), tmp_path)
    assert files_in(tmp_path) == []


def test_empty_body_is_a_download_failure_not_a_mismatch(tmp_path, monkeypatch):
    serve(monkeypatch, body=b"")
    with pytest.raises(IngestError, match="empty response"):
        fetch(make_source(), tmp_path)
    assert files_in(tmp_path) == []


def test_oversized_body_is_stopped(tmp_path, monkeypatch):
    big = b"x" * 2048
    serve(monkeypatch, body=big)
    with pytest.raises(IngestError, match="larger than 1024 bytes"):
        fetch(make_source(body=big), tmp_path)
    assert files_in(tmp_path) == []


def test_interrupted_download_leaves_no_file(tmp_path, monkeypatch):
    class InterruptedResponse(FakeResponse):
        def read(self, size=-1):
            raise KeyboardInterrupt

    monkeypatch.setattr(sources, "urlopen", lambda request, timeout: InterruptedResponse(BODY))
    with pytest.raises(KeyboardInterrupt):
        fetch(make_source(), tmp_path)
    assert files_in(tmp_path) == []


def test_interrupted_save_leaves_no_temp_file(tmp_path, monkeypatch):
    serve(monkeypatch)

    def interrupt(src, dst):
        raise KeyboardInterrupt

    monkeypatch.setattr("ai_governance.chunks.os.replace", interrupt)
    with pytest.raises(KeyboardInterrupt):
        fetch(make_source(), tmp_path)
    assert files_in(tmp_path) == []


def test_unwritable_raw_dir_raises_ingest_error(tmp_path, monkeypatch):
    serve(monkeypatch)
    (tmp_path / "raw").write_text("a file where the directory should be")
    with pytest.raises(IngestError, match="Test Source: cannot save"):
        fetch(make_source(), tmp_path / "raw")


# 3.3 Cache reuse and refresh


def test_valid_cache_makes_no_network_call(tmp_path, monkeypatch):
    (tmp_path / "doc.xhtml").write_bytes(BODY)
    calls = serve(monkeypatch)
    assert fetch(make_source(), tmp_path) == (BODY, "cached")
    assert calls == []


def test_partial_cache_downloads_only_the_missing_source(tmp_path, monkeypatch):
    cached = make_source(filename="cached.xhtml", download_url="https://example.org/cached")
    missing = make_source(filename="missing.xhtml", download_url="https://example.org/missing")
    (tmp_path / "cached.xhtml").write_bytes(BODY)
    calls = serve(monkeypatch)
    assert fetch(cached, tmp_path)[1] == "cached"
    assert fetch(missing, tmp_path)[1] == "downloaded"
    assert calls == ["https://example.org/missing"]


def test_corrupt_cache_raises_with_refresh_hint(tmp_path, monkeypatch):
    (tmp_path / "doc.xhtml").write_bytes(b"corrupted")
    calls = serve(monkeypatch)
    with pytest.raises(IngestError, match="--refresh"):
        fetch(make_source(), tmp_path)
    assert calls == []


def test_unreadable_cache_raises_ingest_error(tmp_path, monkeypatch):
    (tmp_path / "doc.xhtml").mkdir()
    with pytest.raises(IngestError, match="Test Source: cannot read cached file"):
        fetch(make_source(), tmp_path)


def test_refresh_downloads_again(tmp_path, monkeypatch):
    (tmp_path / "doc.xhtml").write_bytes(BODY)
    calls = serve(monkeypatch)
    assert fetch(make_source(), tmp_path, refresh=True) == (BODY, "downloaded")
    assert calls == ["https://example.org/doc"]
