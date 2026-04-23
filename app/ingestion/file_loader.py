from __future__ import annotations

from pathlib import Path

from app.models import InputDocument


class FileLoader:
    def load(self, file_path: str) -> InputDocument:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        text = path.read_text(encoding="utf-8", errors="ignore")
        return InputDocument(
            source_type="file",
            source_name=path.name,
            source_id=str(path.resolve()),
            raw_text=text,
        )
