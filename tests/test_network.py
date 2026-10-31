"""Checks against the real, pinned source documents. Run with `uv run pytest -m network`."""

import json
import re
from dataclasses import fields

import pytest
from bs4 import BeautifulSoup

from ai_governance.chunks import Chunk, write_jsonl
from ai_governance.eu_ai_act import clean
from ai_governance.nist_ai_rmf import extract_text
from ai_governance.sources import EU_AI_ACT, SOURCES

pytestmark = pytest.mark.network

ROMAN = "I II III IV V VI VII VIII IX X XI XII XIII".split()
FURNITURE = [
    re.compile(r"\bPage \d+\b"),
    re.compile(r"NIST AI 100-1 AI RMF 1\.0"),
    re.compile(r"Categories Subcategories"),
    re.compile(r"Continued on next page"),
    re.compile(r"^Table \d+:", flags=re.MULTILINE),
]


@pytest.fixture(scope="module")
def chunks(source_bytes):
    return [c for source in SOURCES for c in source.chunks(source_bytes[source.name])]


@pytest.fixture(scope="module")
def by_section(chunks):
    return {c.section_id: c for c in chunks}


def test_nist_pdf_extracts_72_subcategory_lines(source_bytes):
    text = extract_text(source_bytes["NIST AI RMF 1.0"])
    lines = re.findall(r"^(?:GOVERN|MAP|MEASURE|MANAGE) \d+\.\d+:", text, flags=re.MULTILINE)
    assert len(lines) == 72


def test_eu_section_ids_in_order(chunks):
    eu = [c.section_id for c in chunks if c.source == "EU AI Act"]
    assert eu == [f"Article {n}" for n in range(1, 114)] + [f"Annex {r}" for r in ROMAN]


def test_nist_subcategory_counts(chunks):
    nist = [c.section_id.split()[0] for c in chunks if c.source == "NIST AI RMF 1.0"]
    assert [nist.count(f) for f in ("GOVERN", "MAP", "MEASURE", "MANAGE")] == [19, 18, 22, 13]


def test_output_file_has_198_lines_in_order(chunks, tmp_path):
    path = tmp_path / "chunks.jsonl"
    write_jsonl(chunks, path)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 198
    kinds = [row["section_id"].split()[0] for row in rows]
    assert kinds[:113] == ["Article"] * 113
    assert kinds[113:126] == ["Annex"] * 13
    assert kinds[126:] == [c.section_id.split()[0] for c in chunks[126:]]
    assert set(kinds[126:]) == {"GOVERN", "MAP", "MEASURE", "MANAGE"}
    assert all(list(row) == [f.name for f in fields(Chunk)] for row in rows)


def test_all_fields_are_non_empty_strings(chunks):
    for c in chunks:
        for f in fields(Chunk):
            value = getattr(c, f.name)
            assert isinstance(value, str) and value, (c.section_id, f.name)


def test_no_markup_or_non_breaking_spaces(chunks):
    for c in chunks:
        for f in fields(Chunk):
            value = getattr(c, f.name)
            assert not re.search(r"<[a-zA-Z/]|&#?\w+;| ", value), (c.section_id, f.name)


def test_ids_are_unique(chunks):
    assert len({c.id for c in chunks}) == len(chunks)


def test_article_6_metadata(by_section):
    c = by_section["Article 6"]
    assert c.source == "EU AI Act"
    assert c.title == "Classification rules for high-risk AI systems"
    assert c.url == "http://data.europa.eu/eli/reg/2024/1689/oj#art_6"
    assert c.version == "OJ L, 2024/1689, 12.7.2024 (original text, not consolidated)"
    assert not c.text.startswith("Article 6")


def test_annex_iii_metadata(by_section):
    c = by_section["Annex III"]
    assert c.title == "High-risk AI systems referred to in Article 6(2)"
    assert c.url.endswith("#anx_III")


def test_govern_1_1_metadata(by_section):
    c = by_section["GOVERN 1.1"]
    assert c.source == "NIST AI RMF 1.0"
    assert c.title == (
        "GOVERN 1: Policies, processes, procedures, and practices across the organization "
        "related to the mapping, measuring, and managing of AI risks are in place, "
        "transparent, and implemented effectively."
    )
    assert c.url == "https://doi.org/10.6028/NIST.AI.100-1"
    assert c.version == "NIST AI 100-1, January 2023 (AI RMF 1.0)"
    assert not c.text.startswith("GOVERN 1.1")


def test_govern_4_category_overflow(by_section):
    title = (
        "GOVERN 4: Organizational teams are committed to a culture that considers "
        "and communicates AI risk."
    )
    assert [by_section[f"GOVERN 4.{n}"].title for n in (1, 2, 3)] == [title] * 3
    text = by_section["GOVERN 4.1"].text
    assert text.endswith("minimize potential negative impacts.")
    assert "communicates AI risk" not in text


@pytest.mark.parametrize(
    ("section_id", "ending"),
    [
        ("GOVERN 6.2", "deemed to be high-risk."),
        ("MAP 5.2", "are in place and documented."),
        ("MEASURE 4.3", "are identified and documented."),
        ("MANAGE 4.3", "followed and documented."),
    ],
)
def test_last_subcategory_of_each_function_stops_at_its_statement(by_section, section_id, ending):
    text = by_section[section_id].text
    assert text.endswith(ending)
    for heading in ("5.2 Map", "5.3 Measure", "5.4 Manage", "6. AI RMF Profiles"):
        assert heading not in text


@pytest.mark.parametrize(
    ("section_id", "phrase"),
    [
        ("GOVERN 1.2", "integrated"),
        ("MAP 1.1", "context-specific"),
        ("MEASURE 4.3", "context-relevant"),
        ("MEASURE 2.6", "the MAP function"),
    ],
)
def test_pdf_text_repairs(by_section, section_id, phrase):
    assert phrase in by_section[section_id].text


def test_missing_space_before_function_name_restored(by_section):
    assert "theMAP" not in by_section["MEASURE 2.6"].text


def test_no_page_furniture_in_nist_chunks(chunks):
    for c in chunks:
        if c.source == "NIST AI RMF 1.0":
            for pattern in FURNITURE:
                assert not pattern.search(c.text), (c.section_id, pattern.pattern)


def test_no_recital_text_in_any_chunk(source_bytes, chunks):
    soup = BeautifulSoup(source_bytes[EU_AI_ACT.name], "html.parser")
    recitals = [clean(div.find_all("td")[-1].get_text()) for div in soup.select('div[id^="rct_"]')]
    assert len(recitals) == 180
    texts = [clean(c.text) for c in chunks]
    for recital in recitals:
        assert not any(recital in text for text in texts), recital[:60]
