# Proposal

## Why

`add-document-ingestion` chunks only EU AI Act articles and annexes and NIST AI RMF subcategories. Questions about framework-level context have no chunk to answer them, for example "What are NIST's characteristics of trustworthy AI?" or "What does Chapter III cover?". This change fills those gaps if the eval set shows they matter.

## What Changes

- **EU AI Act:** add each article's chapter/section path (for example "Chapter III > Section 1") to its chunk as a new metadata field.
- **NIST AI RMF:** add chunks for Part 1, for example one per trustworthy characteristic in Section 3.

Not started until `add-document-ingestion` is archived and the eval set exists. The eval set's out-of-scope questions decide which of the two parts go ahead. Either part may be dropped.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `document-chunking`: a chapter/section path for EU chunks, and new NIST Part 1 chunk types with their own boundaries and metadata.

## Impact

The EU and NIST parsers, the chunk schema (a new field), the expected chunk counts, and the network tests. Existing chunk `id`s stay the same.
