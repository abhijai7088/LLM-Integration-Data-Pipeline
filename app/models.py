from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class InputDocument:
    source_type: str
    source_name: str
    source_id: str
    raw_text: str


@dataclass
class ChunkRecord:
    source_type: str
    source_name: str
    source_id: str
    chunk_id: str
    chunk_index: int
    chunk_text: str


@dataclass
class ExtractionResult:
    source_type: str
    source_name: str
    source_id: str
    chunk_id: str
    chunk_index: int
    summary: str
    entities: list[str]
    sentiment: str
    confidence_score: float
    questions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
