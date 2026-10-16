# Proposal

## Why

Every later feature (retrieval, cited answers, the eval set) depends on having the two source documents as clean, citable chunks. The documents need to be fetched and split in a way that is repeatable and checkable before any search work starts, because a retrieval score means nothing if the chunks underneath it can change silently.

## What Changes

- Add an `ai-governance ingest` command that downloads the EU AI Act and NIST AI RMF 1.0 into the gitignored `data/` directory and writes one chunk file.
- EU AI Act (Regulation (EU) 2024/1689): fetched as the official XHTML from the EU Publications Office. One chunk per article (113) and one per annex (13). Recitals are excluded.
- NIST AI RMF 1.0 (NIST AI 100-1): fetched as the official PDF. One chunk per subcategory (72, e.g. GOVERN 1.1).
- Each chunk carries citation metadata: `source`, `section_id`, `title`, `url`, `version`, plus a stable `id` and the `text`.
- Downloads are cached. Each file is checked against a pinned SHA-256 checksum, and the command re-downloads only when given `--refresh`. If a source changes upstream, the command stops and reports it instead of quietly producing different chunks.
- New runtime dependencies: `pypdf` (PDF text) and `beautifulsoup4` (XHTML parsing).

Out of scope: embeddings, search, answering questions, and the eval set. Each will be its own change. Splitting chunks smaller than an article or subcategory is deferred until the eval set shows it is needed.

Also out of scope, deliberately, because only the units listed above are chunked:
- **NIST AI 100-1:** Part 1 (definitions, AI actors, and Section 3's characteristics of trustworthy AI), the introductions to each function, Profiles, and the appendices.
- **EU AI Act:** recitals, chapter and section headings (articles are not tagged with the chapter they belong to), and footnote text (markers stay in the text).

Effect: questions about these topics (for example "What are NIST's characteristics of trustworthy AI?" or "What does Chapter III cover?") have no chunk to answer them. The eval set should mark such questions out of scope until they are covered. The follow-up change `add-framework-context` will add NIST Part 1 chunks and EU chapter/section context.

## Capabilities

### New Capabilities

- `source-documents`: getting the official source files onto disk: where they come from, caching, checksum verification, refresh, and failure behavior.
- `document-chunking`: turning the source files into citable chunks: chunk boundaries, metadata, text cleanup, output format, and determinism.

### Modified Capabilities

None. There are no existing specs.

## Impact

- New code under `src/ai_governance/` and a new `ingest` subcommand on the existing `ai-governance` entry point.
- `pyproject.toml` and `uv.lock`: two runtime dependencies and a pytest marker for tests that need the network.
- `data/` gets `data/raw/` (downloaded files) and `data/chunks.jsonl` (output). Both are already gitignored.
- README: a usage section for `ingest`.
- CI keeps running offline. Tests that download the real documents are opt-in.
