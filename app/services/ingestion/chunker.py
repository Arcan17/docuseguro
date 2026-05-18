from dataclasses import dataclass

from app.core.config import settings


@dataclass
class Chunk:
    text: str
    index: int
    doc_id: str = ""
    char_start: int = 0


def semantic_chunk(text: str, doc_id: str = "") -> list[Chunk]:
    """Split text into overlapping chunks using recursive character separators."""
    chunk_size = settings.chunk_size
    overlap = settings.chunk_overlap
    separators = ["\n\n", "\n", ". ", " ", ""]

    raw_chunks = _split_recursive(text, chunk_size, overlap, separators)
    return [
        Chunk(text=c, index=i, doc_id=doc_id)
        for i, c in enumerate(raw_chunks)
        if c.strip()
    ]


def _split_recursive(
    text: str, chunk_size: int, overlap: int, separators: list[str]
) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    separator = ""
    for sep in separators:
        if sep in text:
            separator = sep
            break

    if separator == "":
        # Hard split
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks

    splits = text.split(separator)
    chunks: list[str] = []
    current = ""

    for split in splits:
        candidate = current + separator + split if current else split
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # If single split exceeds chunk_size, recurse
            if len(split) > chunk_size:
                sub = _split_recursive(split, chunk_size, overlap, separators[1:])
                chunks.extend(sub)
                current = ""
            else:
                # Start new chunk with overlap from previous
                if chunks:
                    prev_words = chunks[-1].split()
                    overlap_text = " ".join(prev_words[-_word_overlap(overlap):])
                    current = overlap_text + separator + split if overlap_text else split
                else:
                    current = split

    if current:
        chunks.append(current)

    return chunks


def _word_overlap(overlap_chars: int) -> int:
    """Approximate how many trailing words fit in overlap_chars."""
    return max(1, overlap_chars // 6)
