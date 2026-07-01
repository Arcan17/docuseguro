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

    Works line by line and preserves line structure. This matters for tabular
    documents (invoices, balances) where each line/cell — including short values
    like "$2.000", a folio number or a total — carries meaning and must not be
    dropped or merged into a single blob. We only drop lines that are exact
    duplicates (chunk overlap repeats whole lines) and trim from the end when the
    token budget is exceeded.

    Returns (compressed_text, original_tokens, compressed_tokens).
    """
    raw_text = "\n\n".join(c.text for c in chunks)
    original_tokens = count_tokens(raw_text)

    # Line-level deduplication — keep every non-duplicate line regardless of
    # length, and preserve order so rows/columns stay aligned.
    seen: set[str] = set()
    unique_lines: list[str] = []
    for line in raw_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        normalized = re.sub(r"\s+", " ", stripped.lower())
        if normalized in seen:
            continue
        seen.add(normalized)
        unique_lines.append(stripped)

    # Trim to effective token limit, preserving order.
    limit = settings.effective_context_token_limit
    trimmed: list[str] = []
    token_count = 0
    for line in unique_lines:
        t = count_tokens(line)
        if token_count + t > limit:
            break
        trimmed.append(line)
        token_count += t

    # Preserve line breaks so table structure survives into the prompt.
    compressed = "\n".join(trimmed)
    compressed_tokens = count_tokens(compressed)

    logger.info(
        "compression",
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        saved_pct=round((1 - compressed_tokens / max(original_tokens, 1)) * 100, 1),
    )
    return compressed, original_tokens, compressed_tokens
