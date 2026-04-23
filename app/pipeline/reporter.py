from __future__ import annotations

from collections import Counter

from app.models import ExtractionResult


class ReportBuilder:
    def build(self, results: list[ExtractionResult], skipped_items: list[str]) -> str:
        total_chunks = len(results)
        total_sources = len({(r.source_type, r.source_id) for r in results})
        sentiments = Counter(result.sentiment for result in results)
        entities = Counter(entity for result in results for entity in result.entities)
        questions = [q for result in results for q in result.questions]

        lines = [
            "LLM INTEGRATION & DATA PIPELINE - AGGREGATED SUMMARY",
            "=" * 58,
            f"Total processed sources: {total_sources}",
            f"Total processed chunks: {total_chunks}",
            f"Skipped inputs: {len(skipped_items)}",
            "",
            "Sentiment distribution:",
        ]
        for label in ["positive", "neutral", "negative"]:
            lines.append(f"- {label}: {sentiments.get(label, 0)}")

        lines.extend([
            "",
            "Top entities across all inputs:",
        ])
        for entity, count in entities.most_common(10):
            lines.append(f"- {entity}: {count}")

        lines.extend([
            "",
            "Representative questions raised by the corpus:",
        ])
        for question in questions[:10]:
            lines.append(f"- {question}")

        if skipped_items:
            lines.extend([
                "",
                "Skipped inputs:",
            ])
            for item in skipped_items:
                lines.append(f"- {item}")

        return "\n".join(lines) + "\n"
