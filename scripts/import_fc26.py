#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from fc26_pipeline import (
    DEFAULT_IMPORT_REPORT,
    DEFAULT_INTERMEDIATE,
    configure_console,
    discover_dataset_dir,
    import_dataset,
    log,
    print_import_summary,
    write_json_atomic,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import FC26 DataHub CSV/JSON files into Galactico11 format.")
    parser.add_argument("--input", type=Path, help="Dataset folder. Auto-detected when omitted.")
    parser.add_argument("--output", type=Path, default=DEFAULT_INTERMEDIATE, help="Intermediate normalized player JSON.")
    parser.add_argument("--report", type=Path, default=DEFAULT_IMPORT_REPORT, help="Detailed import report JSON.")
    return parser.parse_args()


def main() -> int:
    configure_console()
    args = parse_args()
    try:
        dataset_dir = discover_dataset_dir(args.input)
        players, report = import_dataset(dataset_dir)
        write_json_atomic(args.output.resolve(), players)
        write_json_atomic(args.report.resolve(), report)
        print_import_summary(report)
        log(f"Players processed: {report['players_processed']}")
        log(f"Intermediate output: {args.output.resolve()}")
        log(f"Import report: {args.report.resolve()}")
        return 0 if players else 1
    except Exception as exc:
        log(f"FATAL ERROR: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
