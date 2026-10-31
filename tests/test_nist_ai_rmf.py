from pathlib import Path

import pytest

from ai_governance.errors import IngestError
from ai_governance.nist_ai_rmf import parse_text

FIXTURE = Path(__file__).parent / "fixtures" / "nist_ai_rmf_sample.txt"
DOI = "https://doi.org/10.6028/NIST.AI.100-1"


def parse(text: str):
    return parse_text(text, version="v1", cite=lambda section_id: DOI)


@pytest.fixture(scope="module")
def by_id():
    return {c.section_id: c for c in parse(FIXTURE.read_text(encoding="utf-8"))}


def test_one_chunk_per_subcategory_in_order(by_id):
    assert list(by_id) == ["GOVERN 1.1", "GOVERN 1.2", "GOVERN 4.1", "GOVERN 4.2", "MAP 1.1"]


def test_metadata(by_id):
    chunk = by_id["GOVERN 1.1"]
    assert chunk.id == "nist-ai-rmf:govern-1.1"
    assert chunk.source == "NIST AI RMF 1.0"
    assert chunk.title == "GOVERN 1: Policies are in place."
    assert chunk.url == DOI
    assert chunk.version == "v1"


def test_text_is_statement_without_prefix(by_id):
    assert by_id["GOVERN 1.1"].text == (
        "Legal and regulatory requirements involving AI are understood, managed, and documented."
    )


def test_category_text_on_its_own_line(by_id):
    assert by_id["MAP 1.1"].title == "MAP 1: Context is established."


def test_page_furniture_removed(by_id):
    for chunk in by_id.values():
        for furniture in (
            "Page 2",
            "NIST AI 100-1",
            "Categories Subcategories",
            "Continued",
            "Table",
        ):
            assert furniture not in chunk.text
            assert furniture not in chunk.title


def test_category_overflow_after_page_break(by_id):
    assert by_id["GOVERN 4.1"].text.endswith("minimize potential negative impacts.")
    assert "communicates AI risk" not in by_id["GOVERN 4.1"].text
    title = "GOVERN 4: Organizational teams are committed to a culture that communicates AI risk."
    assert by_id["GOVERN 4.1"].title == title
    assert by_id["GOVERN 4.2"].title == title


def test_function_introduction_skipped(by_id):
    assert by_id["GOVERN 4.2"].text == "Teams use outputs of the MAP function."


def test_last_subcategory_stops_at_end_marker(by_id):
    assert by_id["MAP 1.1"].text.endswith("are understood and documented.")
    assert "Profiles" not in by_id["MAP 1.1"].text


def test_soft_hyphen_rejoined(by_id):
    assert "integrated" in by_id["GOVERN 1.2"].text


def test_compound_hyphen_kept(by_id):
    assert "context-specific laws" in by_id["MAP 1.1"].text


def test_missing_space_restored(by_id):
    assert "the MAP function" in by_id["GOVERN 4.2"].text
    assert "theMAP" not in by_id["GOVERN 4.2"].text


def test_missing_end_marker_raises():
    text = FIXTURE.read_text(encoding="utf-8").replace("6. AI RMF Profiles", "6. Something else")
    with pytest.raises(IngestError, match="6. AI RMF Profiles"):
        parse(text)


def test_missing_start_marker_raises():
    with pytest.raises(IngestError, match="GOVERN 1:"):
        parse("No Core tables here.\n6. AI RMF Profiles\n")
