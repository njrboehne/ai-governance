# Tasks

## 1. Setup

- [x] 1.1 Add runtime dependencies with `uv add pypdf beautifulsoup4` (no extras) and verify `uv sync --locked` succeeds and both appear in `uv.lock`; record the locked versions in design.md Decision 10
- [x] 1.2 Register the `network` pytest marker and `addopts = "-m 'not network'"` in `pyproject.toml`, and verify `uv run pytest` still passes the smoke test

## 2. Chunk model and output

- [x] 2.1 Create `errors.py` (`IngestError`) and `chunks.py` with the frozen `Chunk` dataclass (seven fields), and verify a unit test that builds one and reads its fields
- [x] 2.2 Add the per-source count check and the atomic JSONL writer, and verify unit tests for: one JSON object per line, stable field order, non-ASCII kept, a count mismatch raising `IngestError` with the source and both counts while a pre-existing file stays byte-identical

## 3. Source download and cache

- [x] 3.1 Create `sources.py` with the `Source` dataclass and the two records (URLs, User-Agent and Accept headers, citation URL builder, version, filename, pinned SHA-256, `max_bytes`, expected counts from design.md), and verify a test that both records are present with 64-character hex checksums and no personal data in headers
- [x] 3.2 Implement fetch-and-verify (status 200 only, non-empty, chunked read with `max_bytes`, hash in memory, `mkstemp` + `os.replace`, cleanup in `finally`, urllib errors wrapped in `IngestError`), and verify monkeypatched tests for: match saved; mismatch raises with both hashes and leaves the cached file; network error, 202, empty body, oversized body, and an interruption mid-read each leave no file in `raw/`
- [x] 3.3 Implement cache reuse and `refresh` (cached bytes read once, verified, returned for parsing), and verify monkeypatched tests: a valid cache makes no network call, a partial cache downloads only the missing source, a corrupt cache raises with a `--refresh` hint, `refresh=True` downloads again

## 4. EU AI Act parser

- [x] 4.1 Add `tests/fixtures/eu_ai_act_sample.xhtml` (hand-made: two articles with U+00A0 in headings, one annex with a numbered table row and a text-only table cell, one recital) and verify it is under 5 KB
- [x] 4.2 Implement `eu_ai_act.py` (articles, annexes, `clean()` per field and per text block, headings excluded from text, table-row joining, provision-anchor URLs, recitals skipped), and verify fixture tests for exact `section_id`, `title`, `id`, `url`, no markup or U+00A0, text not starting with the heading, a multi-paragraph article keeping "\n\n" between paragraphs, numbered point on one line, and no recital text

## 5. NIST AI RMF parser

- [x] 5.1 Add `tests/fixtures/nist_ai_rmf_sample.txt` modeled on the real layout (two functions; a section heading and intro after the first table; a page break with furniture; a category-overflow line after a page break; a soft hyphen; a `context-` compound; a `theMAP` join; the `6. AI RMF Profiles` end marker)
- [x] 5.2 Implement `parse_text` (region markers, furniture, section-heading skip, category and subcategory lines, category overflow, repair rules, title, prefix removal), and verify fixture tests for each rule, plus a test that a missing end marker raises `IngestError`
- [x] 5.3 Add the pypdf extraction wrapper and verify a network test that extracting the real PDF yields 72 `FUNCTION N.N:` lines

## 6. CLI

- [x] 6.1 Create `cli.py` with `main(argv=None) -> int`, the `ingest` subcommand, `--refresh`, `--data-dir`, a per-source summary, and `IngestError` → stderr + return 1; point `__init__.main` at it; update `tests/test_main.py` for the no-subcommand help. Verify `uv run pytest` passes, including tests for: no subcommand prints help and returns 0, a failure returns 1 with the message
- [x] 6.2 Add offline end-to-end tests with fixture `Source` records, and verify: a successful run writes `chunks.jsonl` and prints counts per source; a count mismatch returns 1 and leaves a pre-existing `chunks.jsonl` byte-identical; two runs in separate temp dirs produce identical bytes
- [x] 6.3 Add a "Usage" section to README.md (run from the repo root, `uv run ai-governance ingest`, `--refresh`, where output goes, `uv run pytest -m network`) and verify the commands run as written

## 7. Full-document checks

- [x] 7.1 Add `@pytest.mark.network` tests using a session-scoped fixture that downloads both files once into `tmp_path_factory`. Assert: `section_id`s exactly "Article 1".."Article 113" and "Annex I".."Annex XIII" in order; 72 subcategories split 19/18/22/13; 198 lines in article → annex → NIST order; all seven fields non-empty strings; unique ids; the exact Article 6, Annex III, and GOVERN 1.1 metadata from the spec; the GOVERN 4 title and GOVERN 4.1 ending; GOVERN 6.2, MAP 5.2, MEASURE 4.3, and MANAGE 4.3 endings; "integrated", "context-specific", "context-relevant", and "the MAP function"; no furniture strings in any NIST chunk; no whitespace-normalized `rct_N` text in any chunk. Verify `uv run pytest -m network` passes locally
- [x] 7.2 Run `uv run ai-governance ingest` twice from the repo root and verify both runs produce byte-identical `data/chunks.jsonl` (compare with `shasum`), the second run reports both files as cached, and `git status` is clean
- [x] 7.3 Open the Article 6 and Annex III chunk `url`s in a browser and verify each lands on that provision; if the anchor doesn't survive the redirect, record it in review.md and raise it before archive

## 8. Review

- [x] 8.1 Every spec scenario has a passing test; scenario → test mapping recorded in review.md
- [x] 8.2 CI is green on the branch (ruff check, ruff format --check, pytest)
- [x] 8.3 Diff read end to end; findings and resolutions recorded in review.md
- [x] 8.4 `openspec validate add-document-ingestion --strict` passes
- [x] 8.5 Code does nothing the specs don't describe; any extra behavior is either removed or added to the specs
- [x] 8.6 No source documents, data/, secrets, or .env files in the diff (git status / git diff --stat)
- [x] 8.7 Any new dependency is justified in design.md and locked in uv.lock
- [x] 8.8 README updated if setup or usage changed

## Workflow follow-up

- Archive the change after the Review group is complete.
