import re

import tiktoken

from app.core.config import settings
from app.core.logging import get_logger
from app.services.vector_store import SearchResult

logger = get_logger(__name__)

_tokenizer = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_tokenizer.encode(text))


def compress_context(chunks: list[SearchResult]) -> tuple[str, int, int]:
    """Deduplicate and trim context to fit within token budget.

    Returns (compressed_text, original_tokens, compressed_tokens).
    """
    raw_text = "\n\n".join(c.text for c in chunks)
    original_tokens = count_tokens(raw_text)

    # Sentence-level deduplication
    sentences = _split_sentences(raw_text)
    seen: set[str] = set()
    unique_sentences: list[str] = []
    for s in sentences:
        normalized = re.sub(r"\s+", " ", s.strip().lower())
        if normalized and normalized not in seen and len(normalized) > 10:
            seen.add(normalized)
            unique_sentences.append(s.strip())

    # Trim to effective token limit
    limit = settings.effective_context_token_limit
    trimmed: list[str] = []
    token_count = 0
    for sentence in unique_sentences:
        t = count_tokens(sentence)
        if token_count + t > limit:
            break
        trimmed.append(sentence)
        token_count += t

    compressed = " ".join(trimmed)
    compressed_tokens = count_tokens(compressed)

    logger.info(
        "compression",
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        saved_pct=round((1 - compressed_tokens / max(original_tokens, 1)) * 100, 1),
    )
    return compressed, original_tokens, compressed_tokens


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences using punctuation boundaries."""
    parts = re.split(r"(?<=[.!?])\s+", text)
    result: list[str] = []
    for part in parts:
        lines = part.split("\n")
        result.extend(line for line in lines if line.strip())
    return result
