from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    id: str
    source: str
    section_id: str
    title: str
    url: str
    version: str
    text: str
