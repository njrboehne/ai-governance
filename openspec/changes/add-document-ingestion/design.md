# Design

## Context

The package is a stub: `ai_governance.main()` prints a status line, and there are no runtime dependencies. See proposal.md for motivation and specs/ for the required behavior.

Both sources were probed on 2026-10-16 before writing this design:

- **EU AI Act.** EUR-Lex (`eur-lex.europa.eu`, including the ELI URLs) answers scripted requests with HTTP 202 and an empty body. That is a bot challenge, not the document. The Publications Office content API at `http://publications.europa.eu/resource/celex/32024R1689`, requested with `Accept: application/xhtml+xml` and `Accept-Language: eng`, returns the official XHTML (about 1.26 MB). Two downloads were byte-identical. In the markup, each article is a `div` with `id="art_N"` (113 of them), each annex has `id="anx_<roman>"` (13), and each recital has `id="rct_N"` (180). Article headings use `p.oj-ti-art` ("Article 6") and titles use `p.oj-sti-art`.
- **NIST AI RMF.** `https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf` (48 pages, about 1.9 MB) downloads directly. pypdf finds all 72 subcategories as lines starting `FUNCTION N.N:`. The extracted text contains line-break hyphenation ("inte-\ngrated") and repeated page furniture ("Page 22", "NIST AI 100-1 AI RMF 1.0", "Categories Subcategories", "Continued on next page", "Table 1: ...").

## Goals / Non-Goals

**Goals:**
- Code is split so each parser can be tested offline on small fixtures.
- CI stays offline and fast.

**Non-Goals:**
- A plugin system for adding more sources. Two sources are listed in code, and a third can be added the same way.
- Paragraph-level citations (for example "Art. 6(2)"). Chunks are article-level for now. The article markup has paragraph `div`s, so this is easy to add later.
- Keeping footnotes or tables as structured data. Their text is kept as plain text.

## Decisions

**1. Download the EU AI Act from the Publications Office, but cite EUR-Lex.**
The download URL is the Cellar endpoint above, because EUR-Lex blocks scripts. The chunk `url` is the ELI link `http://data.europa.eu/eli/reg/2024/1689/oj`, which opens the regulation in a browser.
*Alternatives:* scraping EUR-Lex with browser headers (fragile, and it works around a deliberate block); the PDF (loses the article markup we get for free).

**2. Pin checksums in code.**
A `Source` record holds the name, download URL, request headers, citation URL, version string, filename, and expected SHA-256. Values from the probe:
- EU AI Act: `8f0b656302f9864cc87e040c371f209a9d65ae1a6cecc25ca5eb737e872d721a`
- NIST AI RMF: `7576edb531d9848825814ee88e28b1795d3a84b435b4b797d3670eafdc4a89f1`

Changing a pin is a deliberate, reviewable commit. That's the point: a change in a source shows up in code review instead of as a silent change in eval scores.
*Alternative:* store the hash from the first download in a local manifest. This catches corruption but not upstream changes between machines, and CI and other developers would not share it.

**3. Download with the standard library, write atomically.**
`urllib.request` with a 60-second timeout. The response goes to a temporary file in `data/raw/`, is hashed, and is moved into place with `os.replace` only if the hash matches. On any failure the temporary file is deleted. This meets the "no partial file" and "don't overwrite the cached copy" requirements.
*Alternative:* `httpx`/`requests`. Nicer to use, but an extra dependency for two GET requests.

**4. Parse XHTML with BeautifulSoup and the built-in `html.parser`.**
Select `div[id^="art_"]` and `div[id^="anx_"]`, keeping only top-level ids (`art_6`, not `art_6.tit_1`). Recitals are never selected. For articles, `section_id` comes from `oj-ti-art` and `title` from `oj-sti-art`. For annexes (`div.eli-container`), `section_id` is "Annex <roman>" from the id and `title` is the second `p.oj-doc-ti` (the first is "ANNEX III"). Text is taken block by block: each `p`, except that the cells of a table row are joined with a space, so a numbered point ("1." in one cell, its text in the next) becomes one line. Whitespace is collapsed inside each block, and blocks are joined with blank lines.
*Alternatives:* `lxml` (faster, but a compiled dependency we don't need at this size); regex over HTML (brittle).

**5. NIST: extract text with pypdf, then parse plain text.**
`pypdf.PdfReader` extracts the text of every page. A separate function takes that string and returns chunks, so tests can give it a short text fixture without needing a PDF. Steps:
1. Drop page-furniture lines with a small list of patterns.
2. Rejoin `-\n` breaks where the next line starts with a lowercase letter.
3. Find category lines (`^GOVERN 1:`) and subcategory lines (`^GOVERN 1.1:`). A subcategory's text runs until the next category or subcategory line, or until the end of the Core tables.
4. `title` = the parent category's ID and statement.

*Alternative:* `pdfplumber` table extraction. Better at tables, but heavier, and line-based parsing already finds all 72.

**6. Chunk model and output.**
A frozen `@dataclass Chunk` with the seven spec fields. IDs look like `eu-ai-act:article-6`, `eu-ai-act:annex-iii`, `nist-ai-rmf:govern-1.1`. Output is written with `json.dumps(asdict(c), ensure_ascii=False)` per line to a temporary file, then moved into place with `os.replace`. Expected counts (113, 13, 72) are checked before writing. No timestamps or other per-run data go in the output, so it is deterministic.

**7. CLI with `argparse` subcommands.**
`main(argv: list[str] | None = None)` builds an `ArgumentParser` with an `ingest` subcommand and a `--refresh` flag. With no subcommand it prints help and exits 0. Errors are a small `IngestError` exception that `main` turns into a message on stderr and exit code 1. Taking `argv` as a parameter lets tests call `main(["ingest"])` directly. The existing smoke test is updated to match.

**8. Module layout.**
```
src/ai_governance/
  __init__.py        main() -> cli
  cli.py             argparse, error handling, summary output
  sources.py         Source records, fetch/verify/cache
  chunks.py          Chunk dataclass, JSONL writer, count checks
  eu_ai_act.py       XHTML -> chunks
  nist_ai_rmf.py     PDF -> text -> chunks
tests/
  fixtures/          tiny hand-made XHTML and text samples
```

**9. Testing strategy.**
- Unit tests use fixtures in `tests/fixtures/`: a hand-made XHTML excerpt with two articles, one annex, and one recital, plus a NIST text sample with a hyphen break and a page footer. They are short, so no source documents are committed.
- Download tests use pytest's `monkeypatch` to replace the network call. They cover match, mismatch, corrupt cache, `--refresh`, and network errors, all in a `tmp_path` data directory.
- Full-document tests (exact counts, Article 6 metadata, the GOVERN 1.2 hyphen, determinism) are marked `@pytest.mark.network`. `pyproject.toml` registers the marker and sets `addopts = "-m 'not network'"`, so CI skips them. Run them locally with `uv run pytest -m network`.
- The data directory is a parameter (default `data/`) so tests never touch the real one.

**10. New dependencies.**
`pypdf` (pure Python, maintained, the usual choice for PDF text) and `beautifulsoup4` (the standard HTML parser API). Both are added with `uv add` and locked in `uv.lock`.

## Risks / Trade-offs

- [The Publications Office endpoint changes or starts blocking scripts] → The checksum or HTTP failure shows up immediately with a clear message. The fallback is to download the file by hand into `data/raw/`, since the checksum check still applies.
- [The EU AI Act is amended and a consolidated version is published] → We deliberately pin the original OJ text (`version` says so). Moving to a consolidated version would be its own change, with new pins and maybe new counts.
- [pypdf extraction changes between versions] → The checksum covers the PDF, not the extracted text. The count check and the network-marked tests catch drift, and `uv.lock` pins the pypdf version.
- [NIST page-furniture patterns miss a line] → The page-break scenario has a network test that checks known affected subcategories. New patterns are a one-line fix.
- [Annex III is long for a single chunk] → Acceptable for now, since the proposal defers finer splitting to the eval set.
- [Downloads take a few seconds on first run] → One-time cost, then cached.
