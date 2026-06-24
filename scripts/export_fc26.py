#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from fc26_pipeline import DEFAULT_EXPORT, DEFAULT_INTERMEDIATE, configure_console, log, read_json_file, validate_players, write_json_atomic


EXPORT_FIELDS = (
    "id", "name", "nation", "club", "position", "positions", "age", "overall", "potential", "iog", "source"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export validated FC26 players for fast Galactico11 runtime loading.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INTERMEDIATE, help="Normalized FC26 player JSON.")
    parser.add_argument("--output", type=Path, default=DEFAULT_EXPORT, help="Runtime FC26 player JSON.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print instead of compact runtime JSON.")
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
        validation = validate_players(players)
        if not validation["valid"]:
            for error in validation["errors"]:
                log(f"EXPORT BLOCKED: {error}")
            return 1

        optimized = [{field: player[field] for field in EXPORT_FIELDS} for player in players]
        optimized.sort(key=lambda player: (-player["overall"], -player["potential"], player["name"].casefold(), player["id"]))
        output_path = args.output.resolve()
        write_json_atomic(output_path, optimized, compact=not args.pretty)
        size_mb = output_path.stat().st_size / (1024 * 1024)
        log(f"Players exported: {len(optimized)}")
        log(f"Optimized file size: {size_mb:.2f} MB")
        log(f"Final export location: {output_path}")
        return 0
    except Exception as exc:
        log(f"FATAL ERROR: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
