# ai-governance

Question answering over AI governance frameworks, starting with the NIST AI Risk Management Framework and the EU AI Act. Every answer cites the specific sections it draws on, and an evaluation set measures how well retrieval performs.

**Status:** in progress. The project scaffold is in place; retrieval and evaluation are not built yet.

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
uv run ai-governance
```

Source documents are downloaded at runtime into `data/`, which is not committed.

## License

MIT. See [LICENSE](LICENSE).
