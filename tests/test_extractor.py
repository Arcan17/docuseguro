"""Tests para la extracción de texto (PDF/Word/txt)."""
import io

from docx import Document

from app.services.ingestion.extractor import extract_text


def test_extract_txt() -> None:
    text = extract_text("Hola mundo".encode(), "nota.txt")
    assert text == "Hola mundo"


def test_extract_docx_paragraphs() -> None:
    doc = Document()
    doc.add_paragraph("Contrato de arrendamiento")
    doc.add_paragraph("Arrendatario: Juan Pérez")
    buf = io.BytesIO()
    doc.save(buf)

    text = extract_text(buf.getvalue(), "contrato.docx")
    assert "Contrato de arrendamiento" in text
    assert "Arrendatario: Juan Pérez" in text


def test_extract_docx_tables() -> None:
    doc = Document()
    table = doc.add_table(rows=2, cols=2)
    table.rows[0].cells[0].text = "Concepto"
    table.rows[0].cells[1].text = "Monto"
    table.rows[1].cells[0].text = "Renta"
    table.rows[1].cells[1].text = "$650.000"
    buf = io.BytesIO()
    doc.save(buf)

    text = extract_text(buf.getvalue(), "balance.docx")
    assert "Concepto | Monto" in text
    assert "Renta | $650.000" in text
