from pathlib import Path
import io
import os

MAX_BYTES = int(os.getenv("MAX_UPLOAD_MB", "5")) * 1024 * 1024


def extract_document(filename: str, data: bytes) -> tuple[str, list[dict]]:
    if not data:
        raise ValueError("The document is empty.")
    if len(data) > MAX_BYTES:
        raise ValueError("Files must be 5 MB or smaller.")
    ext = Path(filename).suffix.lower()
    pages = []
    if ext == ".txt":
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("TXT must use UTF-8 encoding.") from exc
        pages = [{"page_number": None, "text": text}]
    elif ext == ".pdf":
        try:
            import pymupdf
            doc = pymupdf.open(stream=data, filetype="pdf")
            pages = [{"page_number": i + 1, "text": p.get_text()} for i, p in enumerate(doc)]
        except Exception as exc:
            raise ValueError("This PDF could not be read. Check that it is a valid digital PDF.") from exc
        if not any(p["text"].strip() for p in pages):
            raise ValueError("No selectable text was found. This PDF may require OCR; OCR is not performed.")
    elif ext == ".docx":
        try:
            from docx import Document
            doc = Document(io.BytesIO(data))
            bits = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                bits.extend(" | ".join(cell.text for cell in row.cells) for row in table.rows)
            pages = [{"page_number": None, "text": "\n".join(bits)}]
        except Exception as exc:
            raise ValueError("This DOCX could not be read.") from exc
    else:
        raise ValueError("Supported formats are PDF, DOCX, and TXT.")
    text = "\n\n".join(p["text"].strip() for p in pages if p["text"].strip())
    return text, pages


def segment(text: str) -> list[dict]:
    import re
    chunks = re.split(r"(?m)(?=^\s*(?:\d+(?:\.\d+)*(?:[.)]\s+|\s+[A-Z][A-Za-z])|ARTICLE\s+\w+|SECTION\s+\w+))", text)
    chunks = [c.strip() for c in chunks if c.strip()]
    if not chunks:
        return []
    if len(chunks) == 1 and len(chunks[0]) > 1800:
        chunks = [p.strip() for p in re.split(r"\n\s*\n", chunks[0]) if p.strip()]
    return [{"id": f"CLAUSE-{i:03d}", "heading": (c.splitlines()[0][:100] if c else f"Section {i}"), "text": c, "page_number": None, "source_offset": text.find(c)} for i, c in enumerate(chunks, 1)]
