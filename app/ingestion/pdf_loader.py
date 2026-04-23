from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from app.models import InputDocument


class PdfLoader:
    def load(self, file_path: str) -> InputDocument:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        reader = PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return InputDocument(
            source_type="file",
            source_name=path.name,
            source_id=str(path.resolve()),
            raw_text=text,
        )
