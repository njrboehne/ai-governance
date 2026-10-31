# source-documents Specification

## Purpose

Gets the official EU AI Act and NIST AI RMF source files onto local disk, verified against known checksums, so every downstream step works from the exact same bytes.

## Requirements

### Requirement: Official sources
The system SHALL obtain the EU AI Act (Regulation (EU) 2024/1689) as the English XHTML published by the EU Publications Office, and NIST AI RMF 1.0 (NIST AI 100-1) as the PDF published by NIST. Requests SHALL identify the client with a descriptive User-Agent that contains no personal data.

#### Scenario: First run downloads both sources
- **WHEN** the user runs `ai-governance ingest` and the data directory holds neither file
- **THEN** both files are downloaded into `raw/` inside the data directory
- **AND** the command reports each file as downloaded

### Requirement: Checksum verification
Each source SHALL have a pinned SHA-256 checksum. The system SHALL verify every file against its checksum before using it, whether the file was just downloaded or was already cached. The bytes that are verified SHALL be the same bytes that are parsed.

#### Scenario: Downloaded file matches
- **WHEN** a downloaded file's SHA-256 equals the pinned checksum
- **THEN** the file is saved to `raw/` and used for chunking

#### Scenario: Downloaded file does not match
- **WHEN** a downloaded file's SHA-256 differs from the pinned checksum
- **THEN** the command exits with a non-zero status
- **AND** the message names the source and shows the expected and actual checksums
- **AND** the mismatched file is not saved over any existing cached file
- **AND** any existing `chunks.jsonl` is unchanged

#### Scenario: Cached file is corrupted
- **WHEN** a cached file in `raw/` does not match its pinned checksum
- **THEN** the command exits with a non-zero status and a message suggesting `--refresh`
- **AND** any existing `chunks.jsonl` is unchanged

### Requirement: Cached files are reused
When a verified copy of a source is already in `raw/`, the system SHALL use it without making a network request for that source.

#### Scenario: Second run is offline
- **WHEN** the user runs `ai-governance ingest` and both cached files match their checksums
- **THEN** no network request is made
- **AND** the command reports each file as cached

#### Scenario: Partial cache
- **WHEN** one source is cached and valid and the other is missing
- **THEN** only the missing source is downloaded
- **AND** the command reports one file as cached and one as downloaded

### Requirement: Explicit refresh
The system SHALL re-download sources only when the user passes `--refresh`, and the downloaded files SHALL go through the same checksum verification.

#### Scenario: Refresh with unchanged upstream
- **WHEN** the user runs `ai-governance ingest --refresh` and the upstream files still match their checksums
- **THEN** both files are downloaded again and chunking proceeds

#### Scenario: Refresh detects an upstream change
- **WHEN** the user runs `ai-governance ingest --refresh` and an upstream file no longer matches its checksum
- **THEN** the command fails as described in "Downloaded file does not match"
- **AND** the previously cached file remains in place

### Requirement: Download failures
A download SHALL succeed only on HTTP 200 with a non-empty body no larger than that source's size limit. Any other outcome SHALL stop the command with a non-zero status and a message naming the source and the cause, and SHALL leave no partial or temporary file in `raw/`.

#### Scenario: Network error or non-200 status
- **WHEN** a download fails with a network error, a timeout, or any HTTP status other than 200 (including 202)
- **THEN** the command exits with a non-zero status naming the source and the status or error
- **AND** no partial or temporary file for that source exists in `raw/`

#### Scenario: Empty body
- **WHEN** the server answers 200 with an empty body
- **THEN** the command reports a download failure for that source, not a checksum mismatch

#### Scenario: Oversized response
- **WHEN** a response grows past the source's size limit
- **THEN** the download is stopped, reported as a failure for that source, and no file is left in `raw/`

#### Scenario: Interrupted download
- **WHEN** a download is interrupted partway (for example by Ctrl-C)
- **THEN** no partial or temporary file for that source exists in `raw/`

### Requirement: Source files stay out of version control
Downloaded files and output SHALL be written only under the data directory, which defaults to `data/` relative to the current working directory. The README SHALL tell users to run commands from the repository root, where `data/` is gitignored.

#### Scenario: Repository stays clean after ingest
- **WHEN** `ai-governance ingest` completes, run from the repository root
- **THEN** `git status` shows no new tracked or untracked files outside ignored paths
