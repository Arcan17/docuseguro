"""Tests del restaurador de PII sobre streaming."""
from app.services.privacy.stream_restorer import StreamingRestorer

TOKEN = "abc12345-0000-0000-0000-000000000000"
TM = {TOKEN: "12.345.678-9"}


def _run(chunks: list[str]) -> str:
    r = StreamingRestorer(TM)
    out = "".join(r.feed(c) for c in chunks)
    return out + r.flush()


def test_no_pii_passthrough() -> None:
    assert _run(["Hola ", "mundo"]) == "Hola mundo"


def test_token_in_single_chunk() -> None:
    assert _run([f"El RUT es [{TOKEN}]."]) == "El RUT es 12.345.678-9."


def test_token_split_across_chunks() -> None:
    # El token llega partido en tres pedazos.
    chunks = ["El RUT es [", TOKEN[:10], TOKEN[10:] + "] fin"]
    assert _run(chunks) == "El RUT es 12.345.678-9 fin"


def test_open_bracket_held_until_close() -> None:
    # Mientras no llega el "]", no se emite el token a medias.
    r = StreamingRestorer(TM)
    emitted = r.feed("antes [")
    assert "[" not in emitted  # se retiene
    emitted += r.feed(f"{TOKEN}]")
    emitted += r.flush()
    assert emitted == "antes 12.345.678-9"


def test_unknown_bracket_emitted_asis() -> None:
    assert _run(["ver [nota] al pie"]) == "ver [nota] al pie"
