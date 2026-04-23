from __future__ import annotations

import argparse
from pathlib import Path

from app.config import settings
from app.logger import setup_logger
from app.pipeline.runner import PipelineRunner
from app.pipeline.reporter import ReportBuilder
from app.output.writer import ResultWriter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LLM Integration & Data Pipeline")
    parser.add_argument("--files", nargs="*", default=[], help="Paths to .txt or .pdf files")
    parser.add_argument("--urls", nargs="*", default=[], help="One or more URLs")
    parser.add_argument("--output-dir", default=None, help="Output directory override")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir) if args.output_dir else settings.output_dir
    logger = setup_logger(settings.log_level)
    settings.validate()

    if not args.files and not args.urls:
        raise SystemExit("Provide at least one input via --files or --urls")

    runner = PipelineRunner(settings, logger)
    documents = runner.load_inputs(args.files, args.urls)
    chunks = runner.build_chunks(documents)
    results = runner.run(chunks)

    writer = ResultWriter(output_dir)
    report_builder = ReportBuilder()

    json_path = writer.write_json(results)
    csv_path = writer.write_csv(results)
    report_path = writer.write_report(report_builder.build(results, runner.skipped_items))

    logger.info("Pipeline complete. Outputs saved to: %s", output_dir)
    print(f"Pipeline complete. JSON: {json_path} | CSV: {csv_path} | REPORT: {report_path}")


if __name__ == "__main__":
    main()
