"""EU AI Act XHTML -> one chunk per article and per annex."""

import re
from collections.abc import Callable

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from .chunks import Chunk
from .errors import IngestError

SOURCE = "EU AI Act"
SECTION_ID = re.compile(r"^(Article|Annex) [0-9IVXLC]+$")

# Short blocks that number the block after them: "1.", "(a)", "(iii)", "3.1.", "—", "‘(68)".
LABEL = re.compile(r"^‘?(\(\d{1,3}[a-z]?\)|\d{1,3}[a-z]?(\.\d{1,3})*\.|\([a-z]{1,4}\)|—)$")
INLINE = {"a", "b", "br", "em", "i", "span", "strong", "sub", "sup"}


def clean(s: str) -> str:
    """Collapse all whitespace, including U+00A0, to single spaces."""
    return " ".join(s.split())


def parse(data: bytes, *, version: str, cite: Callable[[str], str]) -> list[Chunk]:
    soup = BeautifulSoup(data, "html.parser")
    chunks = []
    for div in _top_level(soup, "art_"):
        heading = _require(div, div.find("p", class_="oj-ti-art"), "p.oj-ti-art")
        title = _require(div, div.find("p", class_="oj-sti-art"), "p.oj-sti-art")
        section_id = clean(heading.get_text())
        chunks.append(_chunk(div, section_id, title, [heading, title], version, cite))
    for div in _top_level(soup, "anx_"):
        titles = div.find_all("p", class_="oj-doc-ti")
        if len(titles) < 2:
            raise IngestError(f"{SOURCE}: {div['id']} has no p.oj-doc-ti title")
        section_id = f"Annex {div['id'].removeprefix('anx_')}"
        chunks.append(_chunk(div, section_id, titles[1], titles[:2], version, cite))
    return chunks


def _require(div: Tag, found: Tag | None, selector: str) -> Tag:
    if found is None:
        raise IngestError(f"{SOURCE}: {div['id']} has no {selector}")
    return found


def _top_level(soup: BeautifulSoup, prefix: str) -> list[Tag]:
    """Divs like `art_6`, skipping nested ids like `art_6.tit_1`."""
    return [d for d in soup.select(f'div[id^="{prefix}"]') if "." not in d["id"]]


def _chunk(
    div: Tag,
    section_id: str,
    title: Tag,
    skip: list[Tag],
    version: str,
    cite: Callable[[str], str],
) -> Chunk:
    if not SECTION_ID.match(section_id):
        raise IngestError(f"{SOURCE}: {div['id']} has an unexpected heading {section_id!r}")
    kind, number = section_id.split()
    return Chunk(
        id=f"eu-ai-act:{kind.lower()}-{number.lower()}",
        source=SOURCE,
        section_id=section_id,
        title=clean(title.get_text()),
        url=cite(div["id"]),
        version=version,
        text="\n\n".join(_join_labels(_blocks(div, skip))),
    )


def _blocks(node: Tag, skip: list[Tag]) -> list[tuple[bool, str]]:
    """Text blocks in document order, as (is_paragraph, text).

    Each `p` is a block, and so is each run of text outside a `p`.
    """
    blocks: list[tuple[bool, str]] = []
    run: list[str] = []

    def flush() -> None:
        text = clean("".join(run))
        run.clear()
        if text:
            blocks.append((False, text))

    for child in node.children:
        if isinstance(child, Comment):
            continue
        if isinstance(child, NavigableString):
            run.append(str(child))
        elif child.name in INLINE:
            run.append(child.get_text())
        elif child.name == "p":
            flush()
            text = clean(child.get_text())
            # By identity: bs4 compares tags by content, so == could skip a look-alike.
            if text and not any(child is s for s in skip):
                blocks.append((True, text))
        else:
            flush()
            blocks.extend(_blocks(child, skip))
    flush()
    return blocks


def _join_labels(blocks: list[tuple[bool, str]]) -> list[str]:
    """Append stray punctuation to the previous block and labels to the next one."""
    out: list[str] = []
    label = ""
    for is_paragraph, text in blocks:
        if not is_paragraph and not label and out and text[0] in ";,.":
            out[-1] += text
        elif LABEL.match(text):
            label = f"{label} {text}".strip()
        else:
            out.append(f"{label} {text}".strip())
            label = ""
    if label:
        out.append(label)
    return out
