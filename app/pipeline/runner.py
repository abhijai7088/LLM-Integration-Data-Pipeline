from __future__ import annotations

import logging
from pathlib import Path

from app.config import Settings
from app.ingestion.file_loader import FileLoader
from app.ingestion.pdf_loader import PdfLoader
from app.ingestion.url_loader import UrlLoader
from app.llm.client import LLMClient
from app.models import ChunkRecord, ExtractionResult, InputDocument
from app.preprocessing.cleaner import clean_text
from app.utils.chunking import chunk_text
from app.llm.parser import parse_llm_json


class PipelineRunner:
    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger
        self.file_loader = FileLoader()
        self.pdf_loader = PdfLoader()
        self.url_loader = UrlLoader(timeout_seconds=settings.request_timeout_seconds)
        self.llm_client = LLMClient(settings)
        self.skipped_items: list[str] = []

    def load_inputs(self, files: list[str], urls: list[str]) -> list[InputDocument]:
        documents: list[InputDocument] = []

        for f in files:
            try:
                path = Path(f)
                if path.suffix.lower() == ".pdf":
                    doc = self.pdf_loader.load(f)
                else:
                    doc = self.file_loader.load(f)
                documents.append(doc)
                self.logger.info("Loaded file: %s", f)
            except Exception as exc:
                self.skipped_items.append(f"FILE_FAILED: {f}: {exc}")
                self.logger.exception("Failed to load file %s", f)

        for url in urls:
            try:
                doc = self.url_loader.load(url)
                documents.append(doc)
                self.logger.info("Loaded URL: %s", url)
            except Exception as exc:
                self.skipped_items.append(f"URL_FAILED: {url}: {exc}")
                self.logger.exception("Failed to load URL %s", url)

        return documents

    def build_chunks(self, documents: list[InputDocument]) -> list[ChunkRecord]:
        all_chunks: list[ChunkRecord] = []
        global_count = 0
        for doc in documents:
            cleaned = clean_text(doc.raw_text)
            chunks = chunk_text(cleaned, max_chars=self.settings.max_chars_per_chunk)
            for i, text in enumerate(chunks, start=1):
                global_count += 1
                all_chunks.append(
                    ChunkRecord(
                        source_type=doc.source_type,
                        source_name=doc.source_name,
                        source_id=doc.source_id,
                        chunk_id=f"{doc.source_type}_{global_count}",
                        chunk_index=i,
                        chunk_text=text,
                    )
                )
        return all_chunks

    def run(self, chunks: list[ChunkRecord]) -> list[ExtractionResult]:
        results: list[ExtractionResult] = []
        for chunk in chunks:
            try:
                raw = self.llm_client.extract(chunk.chunk_text)
                parsed = parse_llm_json(raw)
                results.append(
                    ExtractionResult(
                        source_type=chunk.source_type,
                        source_name=chunk.source_name,
                        source_id=chunk.source_id,
                        chunk_id=chunk.chunk_id,
                        chunk_index=chunk.chunk_index,
                        summary=parsed["summary"],
                        entities=parsed["entities"],
                        sentiment=parsed["sentiment"],
                        confidence_score=parsed["confidence_score"],
                        questions=parsed["questions"],
                    )
                )
            except Exception as exc:
                self.skipped_items.append(f"CHUNK_FAILED: {chunk.chunk_id}: {exc}")
                self.logger.error("Failed to process chunk %s", chunk.chunk_id)
        return results
