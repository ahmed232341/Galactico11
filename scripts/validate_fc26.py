#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from fc26_pipeline import (
    DEFAULT_INTERMEDIATE,
    DEFAULT_VALIDATION_REPORT,
    configure_console,
    log,
    read_json_file,
    validate_players,
    write_json_atomic,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate normalized Galactico11 FC26 player data.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INTERMEDIATE, help="Normalized FC26 player JSON.")
    parser.add_argument("--report", type=Path, default=DEFAULT_VALIDATION_REPORT, help="Validation report JSON.")
    return parser.parse_args()


def main() -> int:
    configure_console()
    args = parse_args()
    input_path = args.input.resolve()
    if not input_path.exists():
        log(f"FATAL ERROR: Input file does not exist: {input_path}")
        return 1

    try:
        players = read_json_file(input_path)
        report = validate_players(players)
        write_json_atomic(args.report.resolve(), report)
        print("FC26 VALIDATION SUMMARY")
        print(f"Total players: {report['total_players']}")
        print(f"Missing names: {len(report.get('missing_names', []))}")
        print(f"Missing nations: {len(report.get('missing_nations', []))}")
        print(f"Missing positions: {len(report.get('missing_positions', []))}")
        print(f"Missing clubs: {len(report.get('missing_clubs', []))}")
        print(f"Missing IoG: {len(report.get('missing_iog', []))}")
        print(f"Duplicate IDs: {len(report.get('duplicate_ids', []))}")
        print("Position distribution:")
        for position, count in report.get("position_distribution", {}).items():
            print(f"  {position}: {count}")
        if report["valid"]:
            log("Validation passed")
        else:
            for error in report["errors"]:
                log(f"VALIDATION ERROR: {error}")
        log(f"Validation report: {args.report.resolve()}")
        return 0 if report["valid"] else 1
    except Exception as exc:
        log(f"FATAL ERROR: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
