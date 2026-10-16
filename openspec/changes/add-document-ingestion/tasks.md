# Tasks

## 1. Setup

- [ ] 1.1 Add runtime dependencies with `uv add pypdf beautifulsoup4` and verify `uv sync --locked` succeeds and both appear in `uv.lock`
- [ ] 1.2 Register the `network` pytest marker and `addopts = "-m 'not network'"` in `pyproject.toml`, and verify `uv run pytest` still passes the smoke test

## 2. Chunk model and output

- [ ] 2.1 Create `chunks.py` with the frozen `Chunk` dataclass (seven fields) and verify a unit test that builds one and reads its fields
- [ ] 2.2 Add the atomic JSONL writer and the expected-count check, and verify unit tests for: one JSON object per line, field order stable, non-ASCII kept, a count mismatch raises without touching an existing file

## 3. Source download and cache

- [ ] 3.1 Create `sources.py` with the two `Source` records (URLs, headers, citation URL, version, filename, pinned SHA-256 from design.md) and verify a test that both records are present with 64-character hex checksums
- [ ] 3.2 Implement fetch-and-verify with a temporary file, hash check, and `os.replace`, and verify monkeypatched tests: matching download is saved, mismatch raises with both hashes and leaves the existing file, network error/non-2xx leaves no partial file
- [ ] 3.3 Implement cache reuse and `refresh`, and verify monkeypatched tests: a valid cache makes no network call, a corrupt cache raises with a `--refresh` hint, `refresh=True` downloads again

## 4. EU AI Act parser

- [ ] 4.1 Add `tests/fixtures/eu_ai_act_sample.xhtml` (hand-made: two articles, one annex with a numbered table row, one recital) and verify it is under 5 KB
- [ ] 4.2 Implement `eu_ai_act.py` (articles, annexes, title extraction, table-row joining, whitespace cleanup, recitals skipped) and verify fixture tests for `section_id`, `title`, `id`, no markup, numbered point on one line, and no recital text

## 5. NIST AI RMF parser

- [ ] 5.1 Add `tests/fixtures/nist_ai_rmf_sample.txt` (two categories, three subcategories, one hyphen break, one page-footer block between lines of a statement)
- [ ] 5.2 Implement the text-to-chunks function (furniture removal, hyphen rejoin, category/subcategory boundaries, parent-category title) and verify fixture tests for hyphen rejoined, footer removed, statement-only text, and title
- [ ] 5.3 Add the pypdf extraction wrapper and verify it is covered by the network tests in group 7

## 6. CLI

- [ ] 6.1 Create `cli.py` with `main(argv=None)`, the `ingest` subcommand, `--refresh`, a per-source summary, and `IngestError` → stderr + exit 1, then point the `__init__.main` entry point at it. Verify tests: no subcommand prints help and exits 0, a failure exits 1 with the message, a successful run with monkeypatched sources writes the chunk file and prints counts
- [ ] 6.2 Update `tests/test_main.py` for the new no-subcommand behavior and verify `uv run pytest` passes
- [ ] 6.3 Add a "Usage" section to README.md (`uv run ai-governance ingest`, `--refresh`, where output goes, `uv run pytest -m network`) and verify the commands run as written

## 7. Full-document checks

- [ ] 7.1 Add `@pytest.mark.network` tests against the real files: 113 articles + 13 annexes, 72 subcategories split 19/18/22/13, 198 lines total, unique ids, Article 6 and GOVERN 1.1 metadata, "integrated" in GOVERN 1.2, no page furniture in any NIST chunk, no recital text in any chunk. Verify `uv run pytest -m network` passes locally
- [ ] 7.2 Run `uv run ai-governance ingest` twice and verify both runs produce byte-identical `data/chunks.jsonl` (compare with `shasum`), the second run reports both files as cached, and `git status` is clean

## 8. Review

- [ ] 8.1 Every spec scenario has a passing test; scenario → test mapping recorded in review.md
- [ ] 8.2 CI is green on the branch (ruff check, ruff format --check, pytest)
- [ ] 8.3 Diff read end to end; findings and resolutions recorded in review.md
- [ ] 8.4 `openspec validate add-document-ingestion --strict` passes
- [ ] 8.5 Code does nothing the specs don't describe; any extra behavior is either removed or added to the specs
- [ ] 8.6 No source documents, data/, secrets, or .env files in the diff (git status / git diff --stat)
- [ ] 8.7 Any new dependency is justified in design.md and locked in uv.lock
- [ ] 8.8 README updated if setup or usage changed
- [ ] 8.9 If an eval set exists: precision/recall recorded in review.md and not worse than the last archived change. Otherwise note "N/A: no eval set" in review.md
- [ ] 8.10 Implementation-stage review loop (openspec/reviewers/README.md) run and its report is in review.md; every escalated finding has a human Decision. If no personas exist, note "N/A: no personas" in review.md

## Workflow follow-up

- Archive the change after the Review group is complete.
