# Plan Review

- **Reviewer:** Natalie Boehne
- **Date:** 2026-10-18
- **Decision:** Approved

## Escalated (needs your decision)

### GOV-4 (major): Exclusions beyond recitals are unstated
- **Why escalated:** scope change. Both resolving options either widen what's out of scope or add content, and the guardrails reserve that for the human.
- **Reviewer position:** The plan leaves out much more than recitals, without saying so. On the NIST side that's Part 1 (definitions, AI actors, Section 3's trustworthy characteristics), the function introductions, Profiles, and appendices. On the EU side it's chapter and section headings (articles sit inside chapter/section containers whose titles are outside the article divs) and footnote text. Failure: "What are NIST's characteristics of trustworthy AI?" or "What does Chapter III cover?" has no chunk that answers it, so retrieval returns nothing or cites GOVERN 1.2 as if it defined the characteristics.
- **Author position:** Agree the exclusions should be explicit. Bringing NIST Part 1 into scope means new chunking rules for prose sections, which is a separate piece of work.
- **Options:**
  - **A)** Document the exclusions in proposal.md's out-of-scope paragraph, with their effect: eval questions on those topics are marked out of scope for now. No spec change.
  - **B)** A, plus add each EU article's chapter/section path to its chunk (for example "Chapter III > Section 1"), as a new metadata field. Small spec and parser change in this change.
  - **C)** B, plus chunk NIST Part 1 sections (for example Section 3, one chunk per trustworthy characteristic). Larger, and it adds a third set of parsing rules.
- **Author recommendation:** A now, and list B and C as candidate follow-up changes, letting the eval set decide which gaps matter. This keeps the first change small.
- **Decision:**
  - A now, add B and C to changes for follow up. 
## Summary

Rounds run: 3
Reviewer passes: R1: 4 (default model), R2: 4 (smaller model), R3: 1 (smaller model). 9 total, against 12 for the uncapped loop.
Skipped personas: None (all four `applies_when` match this change)
`openspec validate add-document-ingestion --strict`: passes after the last edit.

| Persona | Fixed | Withdrawn | Escalated | Noted |
|---|---|---|---|---|
| Senior engineer (SE) | 13 | 0 | 0 | 1 |
| Test / QA (QA) | 8 | 0 | 0 | 1 |
| Security (SEC) | 5 | 0 | 0 | 2 |
| Governance (GOV) | 6 | 0 | 1 | 2 |
| **Total (39)** | **32** | **0** | **1** | **6** |

Biggest catch: the NIST parsing rules in the original design would have put the wrong text in 5 of the 72 chunks. The last subcategory of each function absorbed the next section's introduction (MANAGE 4.3 absorbed the rest of the document), and the GOVERN 4 category text leaked into GOVERN 4.1. The count check would still have passed. Three reviewers found this independently. The fix was prototyped against the real PDF before round 2.

## Findings ledger

| ID | Severity | Persona | Finding | Rounds | Outcome | Resolution |
|---|---|---|---|---|---|---|
| SE-1 | blocker | SE | NIST: last subcategory of each function absorbs the next section's intro | 2 | Fixed | Region markers and section-heading stop rule (D5 steps 1, 3); spec scenario on 4 endings |
| SE-2 | blocker | SE | NIST: category statement split by a page break; tail leaks into GOVERN 4.1, title truncated | 2 | Fixed | Category-overflow rule (D5 steps 4, 6); spec scenario on the real GOVERN 4 case |
| SE-3 | major | SE | "End of the Core tables" undefined; MANAGE 4.3 absorbs the rest of the document | 2 | Fixed | Required end marker `6. AI RMF Profiles`; IngestError if missing; spec scenario |
| SE-4 | major | SE | U+00A0 in EU headings → "Article\xa06" ≠ "Article 6" | 2 | Fixed | One `clean()` for every field; spec forbids U+00A0 |
| SE-5 | minor | SE | Hyphen rejoin breaks real compounds | 2 | Fixed | Keep-hyphen rule; spec scenario |
| SE-6 | minor | SE | IngestError location (import cycle) and which exceptions get wrapped | 2 | Fixed | `errors.py`; D3 lists the wrapped exceptions |
| SE-7 | minor | SE | `main` return contract unclear | 2 | Fixed | `main(argv) -> int` (D7) |
| SE-8 | minor | SE | Suite red between tasks 6.1 and 6.2 | 2 | Fixed | Smoke-test update merged into 6.1 |
| SE-9 | minor | SE | 5.3 check deferred; network tests' data location unclear | 2 | Fixed | 5.3 has its own network check; session-scoped download fixture |
| SE-10 | minor | SE | EU vs NIST disagree on whether text repeats the heading | 2 | Fixed | Spec: text excludes heading and title for both |
| SE-11 | minor | SE | Relative `data/` default writes outside the gitignored path when run elsewhere | 2 | Fixed | Spec: relative to the cwd; README says run from the repo root; `--data-dir` |
| SE-12 | nit | SE | Expected counts live in the wrong module | 1 | Noted | Fixed anyway: `expected_counts` on `Source` |
| SE-13 | minor | SE | (R2, from the SE-4 fix) `clean()` on "every field" would strip paragraph breaks | 2 | Fixed | `clean()` per block, title, and section_id; join afterward; 4.2 asserts "\n\n" |
| SE-14 | minor | SE | (R2, from the SE-5 fix) KEEP_HYPHEN had 4 unused prefixes | 2 | Fixed | Reduced to `{"context"}` |
| QA-1 | major | QA | Same NIST boundary failures; fixture doesn't model the real layout | 2 | Fixed | As SE-1/2; fixture modeled on the real layout (5.1) |
| QA-2 | major | QA | "context-specific"/"context-relevant" lose their hyphen | 2 | Fixed | As SE-5; network asserts |
| QA-3 | major | QA | Offline end-to-end test impossible (hard-coded counts, pinned hashes, PDF-only input) | 2 | Fixed | `Source` carries `parse` and `expected_counts`; fixture Sources; offline end-to-end tests (6.2) |
| QA-4 | minor | QA | NBSP handling unspecified | 2 | Fixed | As SE-4; fixture includes U+00A0 |
| QA-5 | minor | QA | url, version, and title not pinned to exact strings | 2 | Fixed | Exact strings in spec scenarios |
| QA-6 | minor | QA | Network tests check counts only, not exact IDs, order, fields, or recitals | 2 | Fixed | 7.1 expanded; recital check defined |
| QA-7 | minor | QA | Determinism never tested in CI | 2 | Fixed | Offline determinism test (6.2) |
| QA-8 | minor | QA | Missing edge cases: partial cache, empty body, interruption, output-unchanged wording | 2 | Fixed | Four spec scenarios added. Empty body = download failure (SEC-3's framing; QA agreed in R2) |
| QA-9 | nit | QA | Network tests may download repeatedly | 1 | Noted | Fixed anyway: session-scoped fixture |
| SEC-1 | minor | SEC | EU download over plain HTTP | 2 | Fixed | https start URL; the publisher's redirect to http is followed; checksum documented as the integrity control. Redirect rewriting rebutted, and SEC accepted |
| SEC-2 | minor | SEC | No download size cap | 2 | Fixed | `max_bytes` with chunked read and abort. Overall deadline rebutted (Ctrl-C is clean), and SEC accepted |
| SEC-3 | minor | SEC | 202/empty body misreported as an upstream change | 2 | Fixed | Only 200 with a non-empty body is accepted |
| SEC-4 | minor | SEC | No User-Agent specified | 2 | Fixed | Descriptive UA, no personal data |
| SEC-5 | minor | SEC | Temp file naming and cleanup unspecified | 2 | Fixed | `mkstemp` + `finally` |
| SEC-6 | nit | SEC | Verify-then-reopen gap | 1 | Noted | Fixed anyway: bytes read once, hashed, then parsed |
| SEC-7 | nit | SEC | Dependency notes (pypdf version, soupsieve) | 1 | Noted | Fixed anyway: D10 and task 1.1 |
| GOV-1 | major | GOV | Same NIST table-end failure | 2 | Fixed | As SE-1 |
| GOV-2 | major | GOV | GOVERN 4 overflow; page-break scenario had no real case | 2 | Fixed | As SE-2; scenario rewritten around the real case |
| GOV-3 | major | GOV | Compound hyphens misquote NIST | 2 | Fixed | As SE-5 |
| GOV-4 | major | GOV | Exclusions beyond recitals unstated | 1 | Escalated | See above |
| GOV-5 | minor | GOV | NBSP in section_id and title | 2 | Fixed | As SE-4 |
| GOV-6 | minor | GOV | `version` string not pinned or not explicit about "original text" | 2 | Fixed | Exact strings pinned |
| GOV-7 | minor | GOV | URLs point at the whole document | 2 | Fixed | EU provision anchors plus browser check (7.3); NIST DOI. `#page=N` rebutted for now, and GOV accepted |
| GOV-8 | nit | GOV | Footnote text dropped silently; source typos | 1 | Noted | Fixed anyway: Non-Goals state both |
| GOV-9 | nit | GOV | "theMAP" extraction artifact | 1 | Noted | Fixed anyway: repair rule and spec scenario |

## Changes made during review

- **specs/source-documents/spec.md:** User-Agent (SEC-4); verified bytes = parsed bytes (SEC-6); "chunks.jsonl unchanged" wording (QA-8d); partial-cache scenario (QA-8a); only 200 with a non-empty body, size limit, and empty/oversized/interrupted scenarios (SEC-2, SEC-3, QA-8b/c); data directory relative to the cwd (SE-11).
- **specs/document-chunking/spec.md:** exact section_id sequences (QA-6); NIST "statement only" with the table-end and GOVERN 4 overflow scenarios (SE-1/2/3, QA-1, GOV-1/2); exact url/version/title strings and the annex scenario (QA-5, GOV-6/7); clean-text rules (U+00A0, headings excluded, typos kept) (SE-4, SE-10, GOV-5/8); new "NIST PDF text repair" requirement (QA-2, SE-5, GOV-3/9); output order (QA-6); missing-end-marker scenario (SE-3).
- **design.md:** Context rewritten with the layout facts; D1 https and the checksum as integrity control (SEC-1); D2 `Source` gains `parse`, `max_bytes`, `expected_counts`, UA, pinned strings (QA-3, SE-12, SEC-2/4); D3 status/size/temp-file/exception handling (SEC-2/3/5/6, SE-6); D4 `clean()` per block (SE-4, SE-13); D5 rewritten as a state machine (SE-1/2/3, SE-14, GOV-9); D7 `-> int` and `--data-dir` (SE-7, SE-11); D8 `errors.py` (SE-6); D9 fixtures, offline end-to-end tests, session fixture (QA-3/7/9, SE-9); D10 dependency notes (SEC-7); Risks updated.
- **tasks.md:** 1.1 records versions (SEC-7); 2.1 errors.py; 3.1–3.3 new download cases (SEC, QA-8); 4.1–4.2 NBSP, anchors, "\n\n" (QA-4, GOV-7, SE-13); 5.1–5.3 layout-faithful fixture and own check (QA-1, SE-9); 6.1 merged with the smoke test (SE-8); 6.2 offline end-to-end tests (QA-3/7); 6.3 run from the repo root (SE-11); 7.1 expanded (QA-6 and others); 7.3 anchor browser check (GOV-7).
- **proposal.md:** after the review, at the human's direction (option A for GOV-4): out-of-scope exclusions and their effect stated, pointing to the follow-up change `add-framework-context` (options B and C).

## Round log

### Round 1
Four independent reviews raised 39 findings (2 blocker, 9 major, 22 minor, 6 nit). Three personas found the NIST boundary problem independently. The author prototyped the new rules on the real PDF, and everything the spec now pins was confirmed (72 = 19/18/22/13; correct endings for GOVERN 4.1, 6.2, MAP 5.2, MEASURE 4.3, MANAGE 4.3; exact GOVERN 1 and 4 titles; both compounds; no furniture). The author fixed 35, partly rebutted 3 (SEC-1 redirect rewrite, SEC-2 overall deadline, GOV-7 NIST page anchors), and escalated GOV-4.

### Round 2
All 4 personas re-reviewed with a smaller model, using the ledger and the diff. Every round-1 finding was marked Resolved, including the three partial rebuttals. QA accepted SEC-3's framing for empty bodies. GOV agreed GOV-4 is a scope decision. SE raised SE-13 and SE-14 about round-2 edits. The author fixed both.

### Round 3
Only SE had open findings, so 1 pass. SE-13 and SE-14 were Resolved, with no new findings. Loop closed.

## Noted for later

- NIST chunk urls could add `#page=N` once the parser tracks pages (GOV, SE).
- Check cached-file size against `max_bytes` before reading it (SEC).
- The category-overflow rule (D5 step 6) rests on this PDF's layout. Network tests pin it only through the endings they check. A test that no NIST chunk contains any category statement text would pin it fully (SE).
- How task 3.2 simulates an interruption (for example a mocked stream raising `KeyboardInterrupt`) is an implementation detail (QA).
- Whether EU provision anchors survive the ELI redirect is tracked in task 7.3 (QA, GOV).

## Checked (human)
- [x] Escalated findings each have a Decision
- [x] Changes made during review match `git diff` and nothing in scope was dropped
- [x] Every requirement has at least one WHEN/THEN scenario specific enough to write a test from
- [x] Tasks include a final review group
