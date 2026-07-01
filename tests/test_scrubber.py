import pytest

from app.services.privacy.restorer import restore
from app.services.privacy.scrubber import PIIScrubber


@pytest.fixture
def scrubber() -> PIIScrubber:
    return PIIScrubber(spacy_enabled=False)


@pytest.mark.parametrize(
    "text,expected_types",
    [
        ("El RUT del empleado es 12.345.678-9", ["rut"]),
        ("El RUT es 12345678-9", ["rut"]),
        ("El RUT es 9.876.543-K", ["rut"]),
        ("Contacto: usuario@empresa.cl", ["email"]),
        ("Llame al +56 9 8765 4321", ["phone"]),
        ("Llame al +56987654321", ["phone"]),
        ("RUT 12.345.678-9 y email test@demo.com", ["email", "rut"]),
        ("Sin PII aquí", []),
    ],
)
def test_scrub_detects_types(
    scrubber: PIIScrubber, text: str, expected_types: list[str]
) -> None:
    _, _, detected = scrubber.scrub(text)
    assert detected == expected_types


@pytest.mark.parametrize(
    "pii_value",
    [
        "12.345.678-9",
        "12345678-9",
        "9.876.543-K",
        "usuario@empresa.cl",
        "nombre.apellido@corporacion.com",
        "+56 9 8765 4321",
        "+56987654321",
    ],
)
def test_scrub_removes_pii(scrubber: PIIScrubber, pii_value: str) -> None:
    text = f"Dato sensible: {pii_value} en el documento."
    clean, token_map, _ = scrubber.scrub(text)
    assert pii_value not in clean
    assert len(token_map) == 1


def test_round_trip_restoration(scrubber: PIIScrubber) -> None:
    text = "El empleado 12.345.678-9 envió mail a user@empresa.cl el lunes."
    clean, token_map, detected = scrubber.scrub(text)

    assert "12.345.678-9" not in clean
    assert "user@empresa.cl" not in clean
    assert "rut" in detected
    assert "email" in detected

    restored = restore(clean, token_map)
    assert restored == text


def test_scrub_no_pii(scrubber: PIIScrubber) -> None:
    text = "El sistema procesa documentos internos de la empresa."
    clean, token_map, detected = scrubber.scrub(text)
    assert clean == text
    assert token_map == {}
    assert detected == []


def test_markers_are_readable_and_typed(scrubber: PIIScrubber) -> None:
    text = "RUT 12.345.678-9 y otro 9.876.543-K, correo a@b.cl, fono +56 9 8765 4321"
    clean, token_map, _ = scrubber.scrub(text)
    # Marcadores legibles por tipo e índice, no UUIDs.
    assert "[RUT_1]" in clean
    assert "[RUT_2]" in clean
    assert "[CORREO_1]" in clean
    assert "[TELEFONO_1]" in clean
    # El mapa apunta cada marcador a su valor original.
    assert token_map["RUT_1"] == "12.345.678-9"
    assert token_map["CORREO_1"] == "a@b.cl"


def test_duplicate_pii_values_single_token(scrubber: PIIScrubber) -> None:
    text = "RUT 12.345.678-9 repetido: 12.345.678-9"
    clean, token_map, _ = scrubber.scrub(text)
    # Same RUT → same token → only one entry in map
    assert len(token_map) == 1
    tokens_in_text = [t for t in token_map if f"[{t}]" in clean]
    assert len(tokens_in_text) == 1
