"""Checks against the real, pinned source documents. Run with `uv run pytest -m network`."""

import re

import pytest

from ai_governance.nist_ai_rmf import extract_text

pytestmark = pytest.mark.network


def test_nist_pdf_extracts_72_subcategory_lines(source_bytes):
    text = extract_text(source_bytes["NIST AI RMF 1.0"])
    lines = re.findall(r"^(?:GOVERN|MAP|MEASURE|MANAGE) \d+\.\d+:", text, flags=re.MULTILINE)
    assert len(lines) == 72
