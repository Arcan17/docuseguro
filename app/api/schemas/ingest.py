from pydantic import BaseModel


class IngestResponse(BaseModel):
    doc_id: int
    filename: str
    chunk_count: int
    status: str
    pii_scrubbed: bool = False
