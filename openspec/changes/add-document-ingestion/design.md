# Design

## Context

The package is a stub: `ai_governance.main()` prints a status line, and there are no runtime dependencies. See proposal.md for motivation and specs/ for the required behavior.

Both sources were probed on 2026-10-16 before writing this design:

- **EU AI Act.** EUR-Lex (`eur-lex.europa.eu`, including the ELI URLs) answers scripted requests with HTTP 202 and an empty body. That is a bot challenge, not the document. The Publications Office content API at `https://publications.europa.eu/resource/celex/32024R1689`, requested with `Accept: application/xhtml+xml` and `Accept-Language: eng`, returns 303 to a Cellar URL over plain `http://`, which serves the official XHTML (about 1.26 MB). Two downloads were byte-identical. In the markup, each article is a `div` with `id="art_N"` (113 of them), each annex has `id="anx_<roman>"` (13), and each recital has `id="rct_N"` (180). Article headings use `p.oj-ti-art` ("Article 6") and titles use `p.oj-sti-art`. Headings and text contain non-breaking spaces (U+00A0). Footnote text sits outside the article divs, so only the markers appear inside them.
- **NIST AI RMF.** `https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf` (48 pages, about 1.9 MB) downloads directly. pypdf finds all 72 subcategories as lines starting `FUNCTION N.N:`, under 19 category lines `FUNCTION N:`. The layout matters for parsing:
  - Each function's table ends with a "Categories Subcategories" label, then a numbered section heading ("5.2 Map", "5.3 Measure", "5.4 Manage", "6. AI RMF Profiles") and narrative text before the next table.
  - Category statements come from a narrow left column. They appear as short lines after the `FUNCTION N:` line, and in one case (GOVERN 4) the statement's tail lands after a page break, between GOVERN 4.1 and GOVERN 4.2.
  - There are about 70 line-end hyphens in the tables. Two are real compounds ("context-\nspecific", "context-\nrelevant"), and the rest are soft breaks.
  - Each page break adds furniture lines ("Page 22", "NIST AI 100-1 AI RMF 1.0", "Categories Subcategories", "Continued on next page", "Table 1: ...").
  - One space is lost in extraction ("theMAP function", MEASURE 2.6).

## Goals / Non-Goals

**Goals:**
- Code is split so each parser and the whole pipeline can be tested offline on small fixtures.
- CI stays offline and fast.

**Non-Goals:**
- A plugin system for adding more sources. Two sources are listed in code, and a third can be added the same way.
- Paragraph-level citations (for example "Art. 6(2)"). Chunks are article-level for now. The article markup has paragraph `div`s, so this is easy to add later.
- Footnote text. It lives outside the article divs and is dropped, while markers such as "(57)" stay in the text. Source typos (for example Article 1's title "Subject matter`") are kept as published.

## Decisions

**1. Download the EU AI Act from the Publications Office, but cite EUR-Lex.**
The download starts at the `https://` Cellar URL above, because EUR-Lex blocks scripts. The publisher's redirect goes to plain HTTP, and we follow it rather than rewrite it, since the Cellar HTTPS behavior is undocumented. **The pinned checksum (Decision 2) is the integrity control.** Tampering in transit fails closed as a mismatch. Chunk `url` values use the ELI link with a provision anchor (`http://data.europa.eu/eli/reg/2024/1689/oj#art_6`, `#anx_III`). The anchors match the `id`s in the published markup.
*Alternatives:* scraping EUR-Lex with browser headers (fragile, and it works around a deliberate block); the PDF (loses the article markup); rewriting redirects to HTTPS (unverified endpoint behavior).

**2. Each source is one record holding all of its facts.**
A frozen `Source` dataclass holds: name, download URL, request headers, citation URL builder, version string, filename, expected SHA-256, `max_bytes`, expected chunk counts, and a `parse(bytes) -> list[Chunk]` function. Tests build their own `Source` records from fixture bytes (with checksums computed from those bytes and fixture-sized counts), so the whole pipeline runs offline. Values from the probe:
- EU AI Act: SHA-256 `8f0b656302f9864cc87e040c371f209a9d65ae1a6cecc25ca5eb737e872d721a`, `max_bytes` 3 MB, counts {article: 113, annex: 13}, version "OJ L, 2024/1689, 12.7.2024 (original text, not consolidated)"
- NIST AI RMF: SHA-256 `7576edb531d9848825814ee88e28b1795d3a84b435b4b797d3670eafdc4a89f1`, `max_bytes` 4 MB, counts {subcategory: 72}, url "https://doi.org/10.6028/NIST.AI.100-1", version "NIST AI 100-1, January 2023 (AI RMF 1.0)"

Both send `User-Agent: ai-governance/0.1 (+https://github.com/njrboehne/ai-governance)`. Changing a pin is a deliberate, reviewable commit. That's the point: a change in a source shows up in code review instead of as a silent change in eval scores.
*Alternative:* store the hash from the first download in a local manifest. This catches corruption but not upstream changes between machines.

**3. Download with the standard library, check before saving, write atomically.**
`urllib.request` with a 60-second socket timeout. Only status 200 is accepted (`urlopen` treats 202 as success, so the status is checked explicitly). The body is read in 64 KB blocks into memory, and the download aborts once it passes `max_bytes`. An empty body is a download failure. The bytes are hashed in memory, and only after a match are they written to a `tempfile.mkstemp(dir=raw/)` file and moved into place with `os.replace`. A `finally` block deletes the temporary file on any exception, including `KeyboardInterrupt`. `urllib.error.URLError`, `HTTPError`, `TimeoutError`, and `OSError` are caught and re-raised as `IngestError` naming the source. Cached files are also read once into memory, verified, and those same bytes are passed to the parser.
*Alternative:* `httpx`/`requests`. Nicer to use, but an extra dependency for two GET requests.

**4. Parse XHTML with BeautifulSoup and the built-in `html.parser`.**
Select `div[id^="art_"]` and `div[id^="anx_"]`, keeping only top-level ids (`art_6`, not `art_6.tit_1`). Recitals are never selected. One `clean(s)` helper (`" ".join(s.split())`, which also collapses U+00A0) is applied to `section_id`, `title`, and each text block separately; blocks are joined with blank lines only afterward, so paragraph breaks survive. For articles, `section_id` comes from `oj-ti-art` and `title` from `oj-sti-art`. For annexes (`div.eli-container`), `section_id` is "Annex <roman>" from the id and `title` is the second `p.oj-doc-ti` (the first is "ANNEX III"). `text` excludes the heading and title paragraphs. Each remaining `p` is one block, except that the cells of a table row are joined with a space, so a numbered point ("1." in one cell, its text in the next) becomes one line. Blocks are joined with blank lines.
*Alternatives:* `lxml` (faster, but a compiled dependency we don't need at this size); regex over HTML (brittle).

**5. NIST: extract text with pypdf, then parse plain text in one pass.**
`pypdf.PdfReader(io.BytesIO(data))` extracts every page. A separate `parse_text(str)` does the rest, so tests can feed it a short text fixture. It walks lines with a small state machine:
1. **Region:** start at the first `GOVERN 1:` line and stop at the line matching `^6\. AI RMF Profiles`. If either marker is missing, raise `IngestError`.
2. **Furniture:** a run of lines matching the furniture patterns is a page break. Those lines are dropped, and the parser notes that a page break just happened.
3. **Section headings** (`^\d+(\.\d+)?\.? [A-Z]`, for example "5.2 Map") end the current subcategory and switch to *skip* mode until the next category line, which drops the function introductions.
4. **Category line** `^(GOVERN|MAP|MEASURE|MANAGE) \d+:` starts a category. The lines up to the first subcategory are its statement.
5. **Subcategory line** `^(...) \d+\.\d+:` starts a chunk. The text after the colon and the following lines are its statement.
6. **Category overflow:** lines that come after a page break and before the next subcategory or category line belong to the current category's statement, not the open subcategory. (In this PDF, every page break inside the tables starts on a subcategory or category line, except the GOVERN 4 overflow.)
7. **Repair**, applied to each statement after collection: rejoin `-` + newline + lowercase letter, unless the part before the hyphen is in `KEEP_HYPHEN = {"context"}` (the only compound broken at a line end in the Core; add entries only when a pinned source needs them). Insert a space where a lowercase letter runs into a function name (`theMAP` → `the MAP`). Then apply `clean()`. Each NIST statement is a single paragraph, so collapsing all whitespace is correct here.
8. `title` = `"<category id>: <category statement>"`. `text` = the statement without the `FUNCTION N.N:` prefix.

*Alternatives:* `pdfplumber` table extraction (heavier, and the line rules already cover this PDF); hard-coding the 19 category statements (robust, but duplicates the source). The network tests pin two full titles, so a parsing regression would be caught.

**6. Chunk model and output.**
A frozen `@dataclass Chunk` with the seven spec fields. IDs look like `eu-ai-act:article-6`, `eu-ai-act:annex-iii`, `nist-ai-rmf:govern-1.1`. The count check compares each parsed source against its `Source.expected_counts`. Output is written with `json.dumps(asdict(c), ensure_ascii=False)` per line to a temporary file, then moved into place with `os.replace`. Nothing is written unless every source parsed and passed its checks. No timestamps or other per-run data go in the output, so it is deterministic.

**7. CLI with `argparse` subcommands.**
`main(argv: list[str] | None = None) -> int` builds an `ArgumentParser` with an `ingest` subcommand, `--refresh`, and a hidden `--data-dir` (default `data`, relative to the current directory). With no subcommand it prints help and returns 0. `IngestError` is caught, printed to stderr, and returns 1. The console script and `__main__.py` already pass the return value to `sys.exit`, so no other entry-point code changes.

**8. Module layout.**
```
src/ai_governance/
  __init__.py        main() -> cli.main
  errors.py          IngestError (no imports, so there are no cycles)
  cli.py             argparse, error handling, summary output
  sources.py         Source dataclass, the two records, fetch/verify/cache
  chunks.py          Chunk dataclass, count check, JSONL writer
  eu_ai_act.py       XHTML bytes -> chunks
  nist_ai_rmf.py     PDF bytes -> text -> chunks
tests/
  fixtures/          tiny hand-made XHTML and text samples
```

**9. Testing strategy.**
- **Unit tests** use fixtures in `tests/fixtures/`, modeled on the real layout. The XHTML has two articles (with U+00A0 in headings), one annex with a numbered table row, and one recital. The NIST text has two functions, a section heading and intro text after the first table, a page break with furniture, a category-overflow line after a page break, a soft hyphen, a `context-` compound, and a `theMAP` join.
- **Download tests** use pytest's `monkeypatch` to replace `urlopen`. They cover: match, mismatch (cache untouched, no output), corrupt cache, partial cache, `--refresh`, network error, 202, empty body, oversized body, and an interruption mid-read. Each checks that `raw/` holds no stray files.
- **Offline end-to-end tests** run `main(["ingest", "--data-dir", tmp])` with fixture `Source` records (the NIST record's text extraction is swapped for one that returns the fixture text). They check: the summary output, `chunks.jsonl` contents, a count mismatch returning 1 and leaving a pre-existing `chunks.jsonl` byte-identical, and two runs producing identical bytes.
- **Network tests** (`@pytest.mark.network`) share a session-scoped fixture that downloads both real files once through `sources.py` into `tmp_path_factory`. `pyproject.toml` registers the marker and sets `addopts = "-m 'not network'"`, so CI skips them. Run them locally with `uv run pytest -m network`.

**10. New dependencies.**
`pypdf` (pure Python, maintained, the usual choice for PDF text; install without the `crypto` extra) and `beautifulsoup4` (the standard HTML parser API; pulls in the pure-Python `soupsieve`). Both are added with `uv add` and locked in `uv.lock`. Record the locked versions here when implementing.

## Risks / Trade-offs

- [The Publications Office endpoint changes or starts blocking scripts] → The download fails with the status named, not as a checksum mismatch. The fallback is to download the file by hand into `data/raw/`, since the checksum check still applies.
- [HTTP leg of the EU download can be tampered with] → The checksum fails closed. A persistent mismatch on an unchanged upstream points to the network, and the message says so.
- [The EU AI Act is amended and a consolidated version is published] → We deliberately pin the original OJ text, and `version` says so. Moving to a consolidated version would be its own change.
- [The NIST layout rules are specific to this PDF] → The PDF is pinned by checksum, so the rules only have to fit these bytes. The network tests pin four table endings, the GOVERN 4 overflow, two titles, and both hyphen cases.
- [`KEEP_HYPHEN` is a heuristic] → It holds only `context`, matching every line-end hyphen in the Core tables (2 compounds, about 70 soft breaks). A new source would need its own check.
- [Annex III is long for a single chunk] → Acceptable for now, since the proposal defers finer splitting to the eval set.
- [Running from outside the repo root writes `data/` somewhere not gitignored] → The README says to run from the repo root. `--data-dir` is there for tests.
