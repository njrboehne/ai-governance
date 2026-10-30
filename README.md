# ai-governance

Question answering over AI governance frameworks, starting with the NIST AI Risk Management Framework and the EU AI Act. Every answer cites the specific sections it draws on, and an evaluation set measures how well retrieval performs.

**Status:** in progress. Document ingestion works; retrieval and evaluation are not built yet.

## Goals

- Answer questions about NIST AI RMF and the EU AI Act, citing the source sections.
- Measure retrieval quality (precision and recall) against a hand-labeled question set.
- Write a spec for each behavior before building it.

## Setup

Requires [uv](https://docs.astral.sh/uv/). uv installs Python 3.12 if you don't have it.

```bash
git clone https://github.com/njrboehne/ai-governance.git
cd ai-governance
uv sync
```

## Usage

Run commands from the repository root, so the output lands in the ignored `data/` folder.

```bash
uv run ai-governance ingest
```

This downloads both source documents into `data/raw/`, checks each against a pinned SHA-256 checksum, and writes one chunk per section to `data/chunks.jsonl` (198 chunks: 113 articles and 13 annexes of the EU AI Act, and 72 NIST AI RMF subcategories). Later runs reuse the cached files without a network call. Add `--refresh` to download them again.

Tests run offline by default. To also run the tests that download the real documents:

```bash
uv run pytest -m network
```

## License

MIT. See [LICENSE](LICENSE).
