# Spec Delta

## Purpose

Gets the official EU AI Act and NIST AI RMF source files onto local disk, verified against known checksums, so every downstream step works from the exact same bytes.

## ADDED Requirements

### Requirement: Official sources
The system SHALL obtain the EU AI Act (Regulation (EU) 2024/1689) as the English XHTML published by the EU Publications Office, and NIST AI RMF 1.0 (NIST AI 100-1) as the PDF published by NIST.

#### Scenario: First run downloads both sources
- **WHEN** the user runs `ai-governance ingest` and `data/raw/` holds neither file
- **THEN** both files are downloaded into `data/raw/`
- **AND** the command reports each file as downloaded

### Requirement: Checksum verification
Each source SHALL have a pinned SHA-256 checksum. The system SHALL verify every file against its checksum before using it, whether the file was just downloaded or was already cached.

#### Scenario: Downloaded file matches
- **WHEN** a downloaded file's SHA-256 equals the pinned checksum
- **THEN** the file is saved to `data/raw/` and used for chunking

#### Scenario: Downloaded file does not match
- **WHEN** a downloaded file's SHA-256 differs from the pinned checksum
- **THEN** the command exits with a non-zero status
- **AND** the message names the source and shows the expected and actual checksums
- **AND** the mismatched file is not saved over any existing cached file
- **AND** no chunk file is written

#### Scenario: Cached file is corrupted
- **WHEN** a cached file in `data/raw/` does not match its pinned checksum
- **THEN** the command exits with a non-zero status and a message suggesting `--refresh`

### Requirement: Cached files are reused
When a verified copy of a source is already in `data/raw/`, the system SHALL use it without making a network request.

#### Scenario: Second run is offline
- **WHEN** the user runs `ai-governance ingest` and both cached files match their checksums
- **THEN** no network request is made
- **AND** the command reports each file as cached

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
A failed download SHALL stop the command with a non-zero status and a message naming the source. It SHALL NOT leave a partial file in `data/raw/`.

#### Scenario: Network error
- **WHEN** a download fails because of a network error or a non-success HTTP status
- **THEN** the command exits with a non-zero status naming the source that failed
- **AND** no partial file for that source exists in `data/raw/`

### Requirement: Source files stay out of version control
Downloaded files SHALL be written only under `data/`, which is gitignored.

#### Scenario: Repository stays clean after ingest
- **WHEN** `ai-governance ingest` completes
- **THEN** `git status` shows no new tracked or untracked files outside ignored paths
