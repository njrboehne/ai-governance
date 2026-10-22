from pathlib import Path

import pytest

from ai_governance.eu_ai_act import parse

FIXTURE = Path(__file__).parent / "fixtures" / "eu_ai_act_sample.xhtml"
ELI = "http://data.europa.eu/eli/reg/2024/1689/oj"


@pytest.fixture(scope="module")
def chunks():
    return parse(FIXTURE.read_bytes(), version="v1", cite=lambda anchor: f"{ELI}#{anchor}")


@pytest.fixture(scope="module")
def by_id(chunks):
    return {c.section_id: c for c in chunks}


def test_fixture_is_small():
    assert FIXTURE.stat().st_size < 5_000


def test_articles_then_annexes(chunks):
    assert [c.section_id for c in chunks] == ["Article 1", "Article 6", "Annex III"]


def test_article_metadata(by_id):
    chunk = by_id["Article 6"]
    assert chunk.id == "eu-ai-act:article-6"
    assert chunk.source == "EU AI Act"
    assert chunk.title == "Classification rules for high-risk AI systems"
    assert chunk.url == f"{ELI}#art_6"
    assert chunk.version == "v1"


def test_annex_metadata(by_id):
    chunk = by_id["Annex III"]
    assert chunk.id == "eu-ai-act:annex-iii"
    assert chunk.title == "High-risk AI systems referred to in Article 6(2)"
    assert chunk.url == f"{ELI}#anx_III"


def test_source_typos_kept(by_id):
    assert by_id["Article 1"].title == "Subject matter`"


def test_no_markup_or_non_breaking_spaces(chunks):
    for chunk in chunks:
        for value in vars(chunk).values():
            assert "\xa0" not in value
            assert "<" not in value
            assert "&#" not in value


def test_text_excludes_heading_and_title(by_id):
    assert not by_id["Article 6"].text.startswith("Article 6")
    assert "Classification rules" not in by_id["Article 6"].text
    assert "ANNEX III" not in by_id["Annex III"].text


def test_paragraphs_separated_by_blank_lines(by_id):
    assert by_id["Article 1"].text.split("\n\n") == [
        "1. The purpose of this Regulation is to improve the functioning of the internal market.",
        "2. This Regulation lays down:",
        "(a) harmonised rules for the placing on the market of AI systems;",
    ]


def test_numbered_table_row_on_one_line(by_id):
    blocks = by_id["Annex III"].text.split("\n\n")
    assert blocks[1].startswith("1. Biometrics, in so far as their use is permitted")


def test_text_outside_paragraphs_kept(by_id):
    assert by_id["Annex III"].text.endswith(
        "2. Directive 2006/42/EC on machinery (OJ L 157, 9.6.2006, p. 24);"
    )


def test_trailing_punctuation_joins_previous_block(by_id):
    assert by_id["Article 6"].text.endswith("‘3. Quoted paragraph.’;")


def test_recitals_skipped(chunks):
    assert not any("recital" in c.text for c in chunks)
