# ai-governance

An open-source AI policy-vs-practice checker. It compares an engineering team's specifications (OpenSpec specs, ADRs and design docs that live next to the code) against the NIST AI Risk Management Framework and the EU AI Act, and flags gaps. Every finding cites the framework section and the source file.

Built with AI assistance, spec-first with [OpenSpec](https://github.com/Fission-AI/OpenSpec). It complements compliance platforms such as Vanta and Drata by focusing on AI-specific evidence; it does not replace them.

**Status:** in progress. Framework ingestion works. The checker, its LLM judge and the evaluation set are not built yet.

## Goals

- Check specs, ADRs and design docs against NIST AI RMF and the EU AI Act, citing the framework section and the source file and line for every finding.
- Report framework items whose evidence lives outside specs (training records, production logs) as "not checkable from specs" rather than as gaps.
- Keep the LLM judge pluggable: a free mock backend for tests and CI, with local (Ollama) and bring-your-own-key API backends later.
- Measure finding accuracy (precision and recall) against a hand-labeled fictional sample app.
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

This downloads both source documents into `data/raw/`, checks each against a pinned SHA-256 checksum, and writes one chunk per citable framework section to `data/chunks.jsonl` (198 chunks: 113 articles and 13 annexes of the EU AI Act, and 72 NIST AI RMF subcategories). Later runs reuse the cached files without a network call. Add `--refresh` to download them again, for example after a framework update (the pinned checksums will then need a reviewed update). The checker will read these chunks.

Tests run offline by default. To also run the tests that download the real documents:

```bash
uv run pytest -m network
```

## License

MIT. See [LICENSE](LICENSE).
