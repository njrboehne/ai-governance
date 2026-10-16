# Spec Delta

## Purpose

Splits the verified source documents into chunks that each match one citable unit (an EU AI Act article or annex, or a NIST AI RMF subcategory) and carry the metadata needed to cite them.

## ADDED Requirements

### Requirement: EU AI Act chunk boundaries
The system SHALL produce exactly one chunk per EU AI Act article and one chunk per annex. Recitals SHALL NOT be chunked.

#### Scenario: Articles and annexes are chunked
- **WHEN** ingest runs on the verified EU AI Act file
- **THEN** there are 113 article chunks with `section_id` values "Article 1" through "Article 113"
- **AND** there are 13 annex chunks with `section_id` values "Annex I" through "Annex XIII"

#### Scenario: Recitals are excluded
- **WHEN** ingest runs on the verified EU AI Act file
- **THEN** no chunk contains the text of a recital

### Requirement: NIST AI RMF chunk boundaries
The system SHALL produce exactly one chunk per NIST AI RMF Core subcategory, identified by its function and number (for example "GOVERN 1.1").

#### Scenario: Subcategories are chunked
- **WHEN** ingest runs on the verified NIST AI RMF file
- **THEN** there are 72 chunks: 19 GOVERN, 18 MAP, 22 MEASURE, and 13 MANAGE
- **AND** each chunk's text is that subcategory's statement only

### Requirement: Citation metadata
Every chunk SHALL include `id`, `source`, `section_id`, `title`, `url`, `version`, and `text`, all as non-empty strings. `id` SHALL be unique and stay the same across runs.

#### Scenario: EU AI Act article metadata
- **WHEN** the chunk for Article 6 is produced
- **THEN** `source` is "EU AI Act", `section_id` is "Article 6", `title` is "Classification rules for high-risk AI systems"
- **AND** `url` is a public link to the regulation and `version` identifies the Official Journal publication

#### Scenario: NIST subcategory metadata
- **WHEN** the chunk for GOVERN 1.1 is produced
- **THEN** `source` is "NIST AI RMF 1.0", `section_id` is "GOVERN 1.1"
- **AND** `title` is the parent category's ID and statement (GOVERN 1)
- **AND** `url` is a public link to NIST AI 100-1 and `version` identifies that publication

#### Scenario: IDs are unique
- **WHEN** ingest completes
- **THEN** no two chunks share an `id`

### Requirement: Clean chunk text
Chunk text SHALL be plain text with no markup. Whitespace runs SHALL be collapsed and paragraph breaks kept. Text from the NIST PDF SHALL have words split by line-break hyphens rejoined, and page headers, footers, and table labels removed.

#### Scenario: No markup in EU text
- **WHEN** an EU AI Act chunk is produced
- **THEN** its text contains no HTML tags or entities

#### Scenario: Hyphenated word rejoined
- **WHEN** the PDF text for GOVERN 1.2 contains "inte-" at a line end followed by "grated"
- **THEN** the chunk text contains "integrated"

#### Scenario: Page furniture removed
- **WHEN** a NIST subcategory statement crosses a page break
- **THEN** its chunk text contains none of the page header, page number, or "Continued on next page" lines

### Requirement: Chunk output file
The system SHALL write all chunks to `data/chunks.jsonl`, one JSON object per line, ordered as EU AI Act articles, then annexes, then NIST subcategories in document order. The file SHALL be replaced on each successful run.

#### Scenario: Output written
- **WHEN** ingest completes successfully
- **THEN** `data/chunks.jsonl` contains 198 lines, each a valid JSON object with the metadata fields
- **AND** the command reports the number of chunks per source

### Requirement: Deterministic output
Running ingest twice on the same verified source files SHALL produce byte-identical `data/chunks.jsonl`.

#### Scenario: Repeat run
- **WHEN** ingest runs twice without `--refresh`
- **THEN** both runs produce identical `data/chunks.jsonl` files

### Requirement: Unexpected structure fails loudly
If a source yields a different number of chunks than the specification expects, the system SHALL exit with a non-zero status, report expected and actual counts, and leave any existing `data/chunks.jsonl` unchanged.

#### Scenario: Parser finds the wrong number of sections
- **WHEN** parsing a source produces a chunk count other than the expected count
- **THEN** the command exits with a non-zero status naming the source and both counts
- **AND** any existing `data/chunks.jsonl` is unchanged
