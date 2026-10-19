from ai_governance.chunks import Chunk


def test_chunk_fields():
    chunk = Chunk(
        id="eu-ai-act:article-6",
        source="EU AI Act",
        section_id="Article 6",
        title="Classification rules for high-risk AI systems",
        url="http://data.europa.eu/eli/reg/2024/1689/oj#art_6",
        version="OJ L, 2024/1689, 12.7.2024 (original text, not consolidated)",
        text="lorem ipsum",
    )
    assert chunk.id == "eu-ai-act:article-6"
