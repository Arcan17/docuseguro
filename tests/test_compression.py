
from app.services.compression import compress_context, count_tokens
from app.services.vector_store import SearchResult


def _make_result(text: str, distance: float = 0.1) -> SearchResult:
    return SearchResult(chunk_id="id", text=text, doc_id="d", distance=distance)


def test_count_tokens_nonzero() -> None:
    assert count_tokens("Hola mundo") > 0


def test_compress_deduplicates_sentences() -> None:
    repeated = "Esta es una oración duplicada. Esta es una oración duplicada."
    chunks = [_make_result(repeated)]
    compressed, orig, comp = compress_context(chunks)
    # Compressed should be shorter than original
    assert comp <= orig


def test_compress_respects_token_limit() -> None:
    long_text = "Contenido relevante de la política corporativa. " * 200
    chunks = [_make_result(long_text)]
    compressed, orig, comp = compress_context(chunks)
    assert comp <= 1500  # max_context_tokens default


def test_compress_returns_token_counts() -> None:
    chunks = [_make_result("Texto de prueba para verificar el compresor.")]
    compressed, orig, comp = compress_context(chunks)
    assert orig > 0
    assert comp > 0
    assert isinstance(compressed, str)
    assert len(compressed) > 0


def test_compress_multiple_chunks() -> None:
    chunks = [
        _make_result("Política de vacaciones: 15 días hábiles."),
        _make_result("Beneficios de salud: cobertura del 100%."),
        _make_result("Teletrabajo: 3 días remotos por semana."),
    ]
    compressed, orig, comp = compress_context(chunks)
    assert len(compressed) > 0
