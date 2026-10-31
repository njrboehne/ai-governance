# Implementation review: add-document-ingestion

## Scenario → test mapping (8.1)

Offline tests run with `uv run pytest`; tests in `test_network.py` run with `uv run pytest -m network` against the real, pinned sources. All 91 pass (69 offline, 22 network).

### source-documents

| Scenario | Tests |
|---|---|
| First run downloads both sources | `test_cli::test_first_run_downloads_writes_chunks_and_reports_counts`; `test_sources::test_headers_identify_the_project_not_a_person` |
| Downloaded file matches | `test_sources::test_matching_download_is_saved` |
| Downloaded file does not match | `test_sources::test_mismatch_raises_with_both_hashes_and_keeps_cached_file`; `test_cli::test_checksum_failure_returns_1_and_keeps_existing_chunks[upstream-changed]` |
| Cached file is corrupted | `test_sources::test_corrupt_cache_raises_with_refresh_hint`; `test_cli::test_checksum_failure_returns_1_and_keeps_existing_chunks[corrupt-cache]` |
| Second run is offline | `test_cli::test_second_run_is_offline_and_reports_cached`; `test_sources::test_valid_cache_makes_no_network_call` |
| Partial cache | `test_sources::test_partial_cache_downloads_only_the_missing_source` |
| Refresh with unchanged upstream | `test_sources::test_refresh_downloads_again` |
| Refresh detects an upstream change | `test_sources::test_mismatch_raises_with_both_hashes_and_keeps_cached_file`; `test_cli::test_checksum_failure_returns_1_and_keeps_existing_chunks[upstream-changed]` |
| Network error or non-200 status | `test_sources::test_network_errors_raise_and_leave_no_file`, `test_http_503_names_the_status`, `test_202_is_a_failure` |
| Empty body | `test_sources::test_empty_body_is_a_download_failure_not_a_mismatch` |
| Oversized response | `test_sources::test_oversized_body_is_stopped` |
| Interrupted download | `test_sources::test_interrupted_download_leaves_no_file`, `test_interrupted_save_leaves_no_temp_file` |
| Repository stays clean after ingest | Manual, task 7.2: `git status` clean after two real runs |

### document-chunking

| Scenario | Tests |
|---|---|
| Articles and annexes are chunked | `test_network::test_eu_section_ids_in_order`; `test_eu_ai_act::test_articles_then_annexes` |
| Recitals are excluded | `test_network::test_no_recital_text_in_any_chunk`; `test_eu_ai_act::test_recitals_skipped` |
| Subcategories are chunked | `test_network::test_nist_subcategory_counts`; `test_nist_ai_rmf::test_one_chunk_per_subcategory_in_order` |
| Last subcategory of each function stops at its statement | `test_network::test_last_subcategory_of_each_function_stops_at_its_statement`; `test_nist_ai_rmf::test_last_subcategory_stops_at_end_marker` |
| Category text across a page break stays with the category | `test_network::test_govern_4_category_overflow`; `test_nist_ai_rmf::test_category_overflow_after_page_break` |
| EU AI Act article metadata | `test_network::test_article_6_metadata`; `test_eu_ai_act::test_article_metadata` |
| EU AI Act annex metadata | `test_network::test_annex_iii_metadata`; `test_eu_ai_act::test_annex_metadata` |
| NIST subcategory metadata | `test_network::test_govern_1_1_metadata`; `test_nist_ai_rmf::test_metadata` |
| IDs are unique | `test_network::test_ids_are_unique` |
| No markup or non-breaking spaces | `test_network::test_no_markup_or_non_breaking_spaces`; `test_eu_ai_act::test_no_markup_or_non_breaking_spaces` |
| Text excludes headings | `test_network::test_article_6_metadata`, `test_govern_1_1_metadata`; `test_eu_ai_act::test_text_excludes_heading_and_title`; `test_nist_ai_rmf::test_text_is_statement_without_prefix` |
| Soft hyphen rejoined | `test_network::test_pdf_text_repairs[GOVERN 1.2-integrated]`; `test_nist_ai_rmf::test_soft_hyphen_rejoined` |
| Compound hyphen kept | `test_network::test_pdf_text_repairs` (MAP 1.1, MEASURE 4.3); `test_nist_ai_rmf::test_compound_hyphen_kept` |
| Page furniture removed | `test_network::test_no_page_furniture_in_nist_chunks`; `test_nist_ai_rmf::test_page_furniture_removed` |
| Missing space restored | `test_network::test_pdf_text_repairs[MEASURE 2.6-the MAP function]`, `test_missing_space_before_function_name_restored`; `test_nist_ai_rmf::test_missing_space_restored` |
| Output written | `test_network::test_output_file_has_198_lines_in_order`; `test_cli::test_first_run_downloads_writes_chunks_and_reports_counts` |
| Repeat run | `test_cli::test_two_runs_in_separate_dirs_write_identical_bytes`; manual, task 7.2 (same SHA-256 on the real sources) |
| Parser finds the wrong number of sections | `test_cli::test_count_mismatch_returns_1_and_keeps_existing_chunks`; `test_chunks::test_check_counts_mismatch_names_source_and_both_counts` |
| End of the NIST Core is not found | `test_nist_ai_rmf::test_missing_end_marker_raises`; `test_main::test_failure_returns_1_with_message` (any `IngestError` exits 1) |

Gaps found and closed during 8.1:
- No test checked that a checksum failure leaves an existing `chunks.jsonl` unchanged. Added `test_cli::test_checksum_failure_returns_1_and_keeps_existing_chunks`.
- "No markup" was checked only on the EU fixture. Added `test_network::test_no_markup_or_non_breaking_spaces` over every field of all 198 real chunks.

## CI (8.2)

Green on draft PR #1 (https://github.com/njrboehne/ai-governance/pull/1), commit 58d27c1: ruff check, ruff format --check, pytest (offline tests).

## Diff read (8.3)

Read `git diff main...HEAD` end to end (source, tests, fixtures, pyproject, README, plan docs). No defects found.

Mid-change senior-engineer pass (after 5.2, 2026-10-22), all resolved:
- SE-1, SE-3, SE-4, SE-5 fixed in 5d26e95: missing EU markers and unexpected headings raise `IngestError`; an unreadable cache or unwritable `raw/` raises `IngestError` instead of a traceback; one shared `atomic_write` for the cache and `chunks.jsonl`; skipped heading tags compared by identity.
- SE-2 fixed in 44e582c (design) and a459d9c: `Source.chunks(data)` passes the record's `version` and `cite` to the parser, so they are defined once.

Noted, no action. The NIST parser relies on three layout rules that hold for the pinned PDF. Each was checked against the real text, and a changed PDF fails its checksum before parsing:
- A page break sends the following lines to the category statement. No subcategory statement in the pinned PDF crosses a page break: all 72 texts and 19 category titles end with a period and hold one statement each.
- A numbered section heading skips text until the next table. In the Core region it matches only "5.2 Map", "5.3 Measure" and "5.4 Manage".
- A line-end hyphen is removed unless the word is in `KEEP_HYPHEN`. All 68 rejoined words in the Core are syllable breaks except "context-", which is kept.

## Checks (8.4–8.8)

- 8.4: `openspec validate add-document-ingestion --strict` passes.
- 8.5: No behavior beyond the specs and design. Extras checked: the hidden `--data-dir` flag and help with no subcommand (design.md, CLI section); `IngestError` for a missing EU heading or title, an unreadable cache and an unwritable `raw/` (covered by "fails loudly" and "Download failures").
- 8.6: The diff has no source documents, `data/`, secrets or `.env` files. The only document-like file is the hand-made 3.3 KB fixture `tests/fixtures/eu_ai_act_sample.xhtml`. `data/` and `.claude/` are ignored.
- 8.7: `pypdf` 6.21.1 and `beautifulsoup4` 4.15.0 (with `soupsieve` 3.0.3) are justified in design.md Decision 10 and locked in `uv.lock`.
- 8.8: README has setup, usage (`ingest`, `--refresh`, output location, run from repo root) and how to run the network tests.
