# Proposal

## Why

`add-document-ingestion` chunks only EU AI Act articles and annexes and NIST AI RMF subcategories. The checker has no framework text for framework-level context, for example NIST's characteristics of trustworthy AI (Part 1, Section 3) or the chapter an EU article sits in (needed to tell whether a high-risk obligation in Chapter III applies). This change fills those gaps if the eval set shows the checker misses findings because of them.

## What Changes

- **EU AI Act:** add each article's chapter/section path (for example "Chapter III > Section 1") to its chunk as a new metadata field.
- **NIST AI RMF:** add chunks for Part 1, for example one per trustworthy characteristic in Section 3.

Not started until `add-document-ingestion` is archived and the eval set exists. Findings the eval set marks out of scope, or gaps the checker misses for lack of this context, decide which of the two parts go ahead. Either part may be dropped.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `document-chunking`: a chapter/section path for EU chunks, and new NIST Part 1 chunk types with their own boundaries and metadata.

## Impact

The EU and NIST parsers, the chunk schema (a new field), the expected chunk counts, and the network tests. Existing chunk `id`s stay the same.
