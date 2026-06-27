import io


def extract_text(content: bytes, filename: str) -> str:
    """Extract plain text from PDF, Word (.docx), Excel (.xlsx) or text bytes."""
    name = filename.lower()
    if name.endswith(".pdf"):
        return _extract_pdf(content)
    if name.endswith(".docx"):
        return _extract_docx(content)
    if name.endswith(".xlsx"):
        return _extract_xlsx(content)
    return content.decode("utf-8", errors="replace")


def _extract_pdf(content: bytes) -> str:
    from pypdf import PdfReader  # type: ignore[import-untyped]

    reader = PdfReader(io.BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def _extract_docx(content: bytes) -> str:
    from docx import Document  # type: ignore[import-untyped]

    doc = Document(io.BytesIO(content))
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    # Include table cell text (contracts/invoices often use tables).
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n\n".join(parts)


def _extract_xlsx(content: bytes) -> str:
    from openpyxl import load_workbook  # type: ignore[import-untyped]

    wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    parts: list[str] = []
    for sheet in wb.worksheets:
        rows: list[str] = []
        for row in sheet.iter_rows(values_only=True):
            cells = [str(c).strip() for c in row if c is not None and str(c).strip()]
            if cells:
                rows.append(" | ".join(cells))
        if rows:
            # Prefix each sheet so multi-tab books keep context.
            parts.append(f"=== Hoja: {sheet.title} ===\n" + "\n".join(rows))
    wb.close()
    return "\n\n".join(parts)
