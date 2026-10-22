"""The two source documents: where they come from, and fetching them into a verified cache."""

import hashlib
import os
import tempfile
import urllib.error
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from urllib.request import Request, urlopen

from . import eu_ai_act, nist_ai_rmf
from .chunks import Chunk
from .errors import IngestError

USER_AGENT = "ai-governance/0.1 (+https://github.com/njrboehne/ai-governance)"
TIMEOUT_SECONDS = 60
BLOCK_SIZE = 64 * 1024
MB = 1024 * 1024


@dataclass(frozen=True)
class Source:
    name: str
    download_url: str
    headers: dict[str, str]
    cite: Callable[[str], str]
    version: str
    filename: str
    sha256: str
    max_bytes: int
    expected_counts: dict[str, int]
    parse: Callable[[bytes], list[Chunk]]


def _eli_url(anchor: str) -> str:
    return f"http://data.europa.eu/eli/reg/2024/1689/oj#{anchor}"


def _nist_url(anchor: str) -> str:
    return "https://doi.org/10.6028/NIST.AI.100-1"


EU_VERSION = "OJ L, 2024/1689, 12.7.2024 (original text, not consolidated)"
NIST_VERSION = "NIST AI 100-1, January 2023 (AI RMF 1.0)"

EU_AI_ACT = Source(
    name=eu_ai_act.SOURCE,
    download_url="https://publications.europa.eu/resource/celex/32024R1689",
    headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/xhtml+xml",
        "Accept-Language": "eng",
    },
    cite=_eli_url,
    version=EU_VERSION,
    filename="eu-ai-act-2024-1689.xhtml",
    sha256="8f0b656302f9864cc87e040c371f209a9d65ae1a6cecc25ca5eb737e872d721a",
    max_bytes=3 * MB,
    expected_counts={"article": 113, "annex": 13},
    parse=partial(eu_ai_act.parse, version=EU_VERSION, cite=_eli_url),
)

NIST_AI_RMF = Source(
    name=nist_ai_rmf.SOURCE,
    download_url="https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf",
    headers={"User-Agent": USER_AGENT, "Accept": "application/pdf"},
    cite=_nist_url,
    version=NIST_VERSION,
    filename="nist-ai-100-1.pdf",
    sha256="7576edb531d9848825814ee88e28b1795d3a84b435b4b797d3670eafdc4a89f1",
    max_bytes=4 * MB,
    expected_counts={"govern": 19, "map": 18, "measure": 22, "manage": 13},
    parse=partial(nist_ai_rmf.parse, version=NIST_VERSION, url=_nist_url("")),
)

SOURCES = [EU_AI_ACT, NIST_AI_RMF]


def fetch(source: Source, raw_dir: Path, refresh: bool = False) -> tuple[bytes, str]:
    """Return the source's verified bytes and "cached" or "downloaded"."""
    path = raw_dir / source.filename
    if path.exists() and not refresh:
        data = path.read_bytes()
        actual = _sha256(data)
        if actual != source.sha256:
            raise IngestError(
                f"{source.name}: cached file {path} does not match its checksum "
                f"(expected {source.sha256}, got {actual}). "
                "Run with --refresh to download it again."
            )
        return data, "cached"

    data = _download(source)
    actual = _sha256(data)
    if actual != source.sha256:
        raise IngestError(
            f"{source.name}: downloaded file does not match its checksum "
            f"(expected {source.sha256}, got {actual}). The source may have changed upstream; "
            "if it has not, something on the network may be altering it."
        )
    _save(data, path)
    return data, "downloaded"


def _download(source: Source) -> bytes:
    request = Request(source.download_url, headers=source.headers)
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise IngestError(f"{source.name}: download failed with HTTP {response.status}")
            blocks = []
            size = 0
            while block := response.read(BLOCK_SIZE):
                size += len(block)
                if size > source.max_bytes:
                    raise IngestError(
                        f"{source.name}: download is larger than {source.max_bytes} bytes; stopped"
                    )
                blocks.append(block)
    except urllib.error.HTTPError as e:
        raise IngestError(f"{source.name}: download failed with HTTP {e.code}") from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise IngestError(f"{source.name}: download failed: {e}") from e
    if size == 0:
        raise IngestError(f"{source.name}: download failed: empty response")
    return b"".join(blocks)


def _save(data: bytes, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
