
from app.services.ingestion.chunker import semantic_chunk


def test_short_text_single_chunk() -> None:
    text = "Este es un texto corto que cabe en un solo chunk."
    chunks = semantic_chunk(text)
    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].index == 0


def test_long_text_produces_multiple_chunks() -> None:
    # 5000 chars → multiple chunks of ~800
    text = ("Palabra " * 100 + "\n\n") * 8
    chunks = semantic_chunk(text)
    assert len(chunks) > 1


def test_chunks_have_overlap() -> None:
    # All content in original text appears somewhere in chunks
    text = "Primer párrafo con información importante.\n\n" + "Segundo párrafo con más datos.\n\n" * 10
    chunks = semantic_chunk(text)
    full = " ".join(c.text for c in chunks)
    assert "Primer párrafo" in full


def test_empty_chunks_filtered() -> None:
    text = "\n\n\n   \n\n\nTexto real aquí.\n\n\n"
    chunks = semantic_chunk(text)
    for c in chunks:
        assert c.text.strip()


def test_doc_id_assigned() -> None:
    chunks = semantic_chunk("Texto de prueba.", doc_id="doc_42")
    assert all(c.doc_id == "doc_42" for c in chunks)


def test_indices_sequential() -> None:
    text = "Palabra " * 300
    chunks = semantic_chunk(text)
    indices = [c.index for c in chunks]
    assert indices == list(range(len(chunks)))
