import pytest

from ai_governance.sources import SOURCES, fetch


@pytest.fixture(scope="session")
def source_bytes(tmp_path_factory):
    """Download both real sources once per test session (network tests only)."""
    raw_dir = tmp_path_factory.mktemp("raw")
    return {source.name: fetch(source, raw_dir)[0] for source in SOURCES}
