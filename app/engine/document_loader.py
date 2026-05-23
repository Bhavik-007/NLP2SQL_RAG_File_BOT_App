import csv
import io
from dataclasses import dataclass


@dataclass
class DocumentChunk:
    text: str
    metadata: dict


class DocumentLoader:
    def __init__(self, chunk_size: int = 900, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load_file(self, file_name: str, content: bytes) -> list[DocumentChunk]:
        extension = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        text = self._extract_text(extension, content)
        chunks = self._chunk_text(text)

        return [
            DocumentChunk(
                text=chunk,
                metadata={
                    "file_name": file_name,
                    "file_type": extension,
                    "chunk_index": index,
                },
            )
            for index, chunk in enumerate(chunks)
        ]

    def _extract_text(self, extension: str, content: bytes) -> str:
        if extension in {"txt", "md"}:
            return content.decode("utf-8", errors="ignore")

        if extension == "csv":
            return self._extract_csv(content)

        if extension == "pdf":
            return self._extract_pdf(content)

        if extension == "docx":
            return self._extract_docx(content)

        raise ValueError(f"Unsupported file type: {extension}")

    @staticmethod
    def _extract_csv(content: bytes) -> str:
        text = content.decode("utf-8", errors="ignore")
        reader = csv.reader(io.StringIO(text))
        rows = []
        for row in reader:
            rows.append(" | ".join(cell.strip() for cell in row))
        return "\n".join(rows)

    @staticmethod
    def _extract_pdf(content: bytes) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ImportError("Install pypdf to upload PDF files.") from exc

        reader = PdfReader(io.BytesIO(content))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)

    @staticmethod
    def _extract_docx(content: bytes) -> str:
        try:
            from docx import Document
        except ImportError as exc:
            raise ImportError("Install python-docx to upload DOCX files.") from exc

        document = Document(io.BytesIO(content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)

    def _chunk_text(self, text: str) -> list[str]:
        clean_text = " ".join((text or "").split())
        if not clean_text:
            return []

        chunks = []
        start = 0
        while start < len(clean_text):
            end = start + self.chunk_size
            chunks.append(clean_text[start:end])
            if end >= len(clean_text):
                break
            start = max(end - self.chunk_overlap, start + 1)
        return chunks
