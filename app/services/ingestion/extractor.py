import io


def extract_text(content: bytes, filename: str) -> str:
    """Extract plain text from PDF or text file bytes."""
    if filename.lower().endswith(".pdf"):
        return _extract_pdf(content)
    return content.decode("utf-8", errors="replace")


def _extract_pdf(content: bytes) -> str:
    from pypdf import PdfReader  # type: ignore[import-untyped]

    reader = PdfReader(io.BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)
