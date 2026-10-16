# Spec Delta

## Purpose

Splits the verified source documents into chunks that each match one citable unit (an EU AI Act article or annex, or a NIST AI RMF subcategory) and carry the metadata needed to cite them.

## ADDED Requirements

### Requirement: EU AI Act chunk boundaries
The system SHALL produce exactly one chunk per EU AI Act article and one chunk per annex. Recitals SHALL NOT be chunked.

#### Scenario: Articles and annexes are chunked
- **WHEN** ingest runs on the verified EU AI Act file
- **THEN** the article chunks' `section_id` values are exactly "Article 1" through "Article 113", each once, in order
- **AND** the annex chunks' `section_id` values are exactly "Annex I" through "Annex XIII", each once, in order

#### Scenario: Recitals are excluded
- **WHEN** ingest runs on the verified EU AI Act file
- **THEN** no chunk's text contains the whitespace-normalized full text of any recital

### Requirement: NIST AI RMF chunk boundaries
The system SHALL produce exactly one chunk per NIST AI RMF Core subcategory, identified by its function and number (for example "GOVERN 1.1"). A chunk's text SHALL be that subcategory's statement only: never function introductions, later sections, or category text.

#### Scenario: Subcategories are chunked
- **WHEN** ingest runs on the verified NIST AI RMF file
- **THEN** there are 72 chunks: 19 GOVERN, 18 MAP, 22 MEASURE, and 13 MANAGE

#### Scenario: Last subcategory of each function stops at its statement
- **WHEN** the chunks for GOVERN 6.2, MAP 5.2, MEASURE 4.3, and MANAGE 4.3 are produced
- **THEN** each chunk's text ends with the final sentence of that subcategory's statement (MANAGE 4.3 ends with "followed and documented.")
- **AND** none contains a section heading such as "5.2 Map" or "6. AI RMF Profiles"

#### Scenario: Category text across a page break stays with the category
- **WHEN** the GOVERN 4 category statement continues onto the next page after GOVERN 4.1
- **THEN** the GOVERN 4.1 chunk text ends with "minimize potential negative impacts." and does not contain "communicates AI risk"
- **AND** the GOVERN 4.1–4.3 chunks' `title` is "GOVERN 4: Organizational teams are committed to a culture that considers and communicates AI risk."

### Requirement: Citation metadata
Every chunk SHALL include `id`, `source`, `section_id`, `title`, `url`, `version`, and `text`, all as non-empty strings. `id` SHALL be unique and stay the same across runs. `url` SHALL point to the provision where the source supports it.

#### Scenario: EU AI Act article metadata
- **WHEN** the chunk for Article 6 is produced
- **THEN** `source` is "EU AI Act", `section_id` is "Article 6", `title` is "Classification rules for high-risk AI systems"
- **AND** `url` is "http://data.europa.eu/eli/reg/2024/1689/oj#art_6"
- **AND** `version` is "OJ L, 2024/1689, 12.7.2024 (original text, not consolidated)"

#### Scenario: EU AI Act annex metadata
- **WHEN** the chunk for Annex III is produced
- **THEN** `section_id` is "Annex III", `title` is "High-risk AI systems referred to in Article 6(2)", and `url` ends with "#anx_III"

#### Scenario: NIST subcategory metadata
- **WHEN** the chunk for GOVERN 1.1 is produced
- **THEN** `source` is "NIST AI RMF 1.0", `section_id` is "GOVERN 1.1"
- **AND** `title` is "GOVERN 1: Policies, processes, procedures, and practices across the organization related to the mapping, measuring, and managing of AI risks are in place, transparent, and implemented effectively."
- **AND** `url` is "https://doi.org/10.6028/NIST.AI.100-1" and `version` is "NIST AI 100-1, January 2023 (AI RMF 1.0)"

#### Scenario: IDs are unique
- **WHEN** ingest completes
- **THEN** no two chunks share an `id`

### Requirement: Clean chunk text
Every string field SHALL be plain text with no markup, with non-breaking spaces turned into normal spaces and whitespace runs collapsed. Paragraph breaks in `text` SHALL be kept. `text` SHALL NOT repeat the heading or title, which live in `section_id` and `title`. Source wording, including typos, is kept as published.

#### Scenario: No markup or non-breaking spaces
- **WHEN** any chunk is produced
- **THEN** no field contains HTML tags, HTML entities, or U+00A0

#### Scenario: Text excludes headings
- **WHEN** the Article 6 and GOVERN 1.1 chunks are produced
- **THEN** the Article 6 text does not start with "Article 6" and the GOVERN 1.1 text does not start with "GOVERN 1.1"

### Requirement: NIST PDF text repair
Text from the NIST PDF SHALL have words split by line-break hyphens rejoined, except known hyphenated compounds, which keep their hyphen. Page headers, page numbers, and table labels SHALL be removed. A space lost before a function name SHALL be restored.

#### Scenario: Soft hyphen rejoined
- **WHEN** the PDF text for GOVERN 1.2 contains "inte-" at a line end followed by "grated"
- **THEN** the chunk text contains "integrated"

#### Scenario: Compound hyphen kept
- **WHEN** the PDF text breaks "context-specific" (MAP 1.1) and "context-relevant" (MEASURE 4.3) across lines
- **THEN** the chunk texts contain "context-specific" and "context-relevant"

#### Scenario: Page furniture removed
- **WHEN** any NIST chunk is produced
- **THEN** its text contains none of "Page <n>", "NIST AI 100-1 AI RMF 1.0", "Categories Subcategories", "Continued on next page", or "Table <n>:" lines

#### Scenario: Missing space restored
- **WHEN** the MEASURE 2.6 chunk is produced
- **THEN** its text contains "the MAP function" and not "theMAP"

### Requirement: Chunk output file
The system SHALL write all chunks to `chunks.jsonl` in the data directory, one JSON object per line, ordered as EU AI Act articles, then annexes, then NIST subcategories in document order. The file SHALL be replaced only on a fully successful run.

#### Scenario: Output written
- **WHEN** ingest completes successfully
- **THEN** `chunks.jsonl` contains 198 lines in that order, each a valid JSON object with the seven fields
- **AND** the command reports the number of chunks per source

### Requirement: Deterministic output
Running ingest twice on the same verified source files SHALL produce byte-identical `chunks.jsonl`.

#### Scenario: Repeat run
- **WHEN** ingest runs twice on the same source files
- **THEN** both runs produce identical `chunks.jsonl` files

### Requirement: Unexpected structure fails loudly
If a source yields a different number of chunks than expected for that source, or an expected structural marker is missing, the system SHALL exit with a non-zero status, report what was expected and found, and leave any existing `chunks.jsonl` unchanged.

#### Scenario: Parser finds the wrong number of sections
- **WHEN** parsing a source produces a chunk count other than the expected count
- **THEN** the command exits with a non-zero status naming the source and both counts
- **AND** any existing `chunks.jsonl` is byte-identical to before

#### Scenario: End of the NIST Core is not found
- **WHEN** the NIST text has no "6. AI RMF Profiles" heading after the Core tables
- **THEN** the command exits with a non-zero status naming the missing marker
