import argparse
import json
import logging
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "pipeline.yaml"
SRC_DATA_DIR = PROJECT_ROOT / "src" / "data"
DEFAULT_CONFIG = {
    "start_year": 2017,
    "end_year": 2026,
    "years": None,
    "export_format": "json",
    "min_minutes_played": 900,
    "paths": {
        "raw_data": "data/raw",
        "processed_data": "data/processed",
        "exports": "data/exports",
        "logs": "logs",
    },
}


@dataclass
class PipelineStep:
    index: int
    name: str
    command: List[str]


def parse_value(value: str) -> Any:
    token = value.strip()
    if token.lower() in {"null", "none"}:
        return None
    if token.lower() in {"true", "false"}:
        return token.lower() == "true"
    if token.isdigit():
        return int(token)
    try:
        return float(token)
    except ValueError:
        return token


def parse_simple_yaml(path: Path) -> Dict[str, Any]:
    config: Dict[str, Any] = {}
    current_section: Optional[str] = None
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.rstrip()
            if not line or line.lstrip().startswith("#"):
                continue
            if line.startswith("  ") or line.startswith("\t"):
                if current_section is None:
                    continue
                key, _, value = line.strip().partition(":")
                config[current_section][key.strip()] = parse_value(value)
            else:
                key, _, value = line.partition(":")
                key = key.strip()
                if not key:
                    continue
                if value.strip() == "":
                    config[key] = {}
                    current_section = key
                else:
                    config[key] = parse_value(value)
                    current_section = None
    return config


def load_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        return DEFAULT_CONFIG.copy()

    try:
        import yaml

        with config_path.open("r", encoding="utf-8") as handle:
            raw_config = yaml.safe_load(handle) or {}
    except ImportError:
        raw_config = parse_simple_yaml(config_path)

    merged = DEFAULT_CONFIG.copy()
    merged.update({k: v for k, v in raw_config.items() if k != "paths"})
    paths = DEFAULT_CONFIG["paths"].copy()
    paths.update(raw_config.get("paths", {}))
    merged["paths"] = paths
    return merged


def format_duration(seconds: float) -> str:
    return f"{seconds:.1f}s"


def create_output_dirs(path_values: Dict[str, str]) -> None:
    for folder in [path_values["raw_data"], path_values["processed_data"], path_values["exports"], path_values["logs"], str(PROJECT_ROOT / "config")]:
        Path(folder).mkdir(parents=True, exist_ok=True)


def build_year_list(args: argparse.Namespace, config: Dict[str, Any]) -> List[str]:
    if args.years is not None and len(args.years) > 0:
        return [str(year) for year in args.years]

    years_setting = config.get("years")
    if isinstance(years_setting, list) and years_setting:
        return [str(year) for year in years_setting]

    start_year = int(args.start_year or config["start_year"])
    end_year = int(args.end_year or config["end_year"])
    return [str(year) for year in range(start_year, end_year + 1)]


def build_command_strings(steps: List[PipelineStep]) -> List[str]:
    return [" ".join(shlex.quote(str(part)) for part in step.command) for step in steps]


def run_step(step: PipelineStep, logger: logging.Logger) -> float:
    print(f"[{step.index}/4] {step.name}...")
    command_str = " ".join(shlex.quote(str(part)) for part in step.command)
    start_time = time.perf_counter()
    result = subprocess.run(step.command, capture_output=True, text=True)
    duration = time.perf_counter() - start_time

    logger.info("Step %s", step.name)
    logger.info("Command: %s", command_str)
    logger.info("Return code: %s", result.returncode)
    logger.info("Stdout: %s", result.stdout.strip())
    logger.info("Stderr: %s", result.stderr.strip())

    if result.returncode != 0:
        print(f"\nERROR: {step.name} failed")
        print(f"Command: {command_str}")
        if result.stderr:
            print(result.stderr.strip())
        else:
            print(result.stdout.strip())
        logger.error("Step failed: %s", step.name)
        logger.error("Command: %s", command_str)
        logger.error("Stderr: %s", result.stderr.strip())
        sys.exit(result.returncode or 1)

    print(f"Completed in {format_duration(duration)}\n")
    return duration


def run_pipeline(args: argparse.Namespace, config: Dict[str, Any]) -> None:
    config_paths = config["paths"]
    create_output_dirs(config_paths)

    raw_data_dir = Path(config_paths["raw_data"])
    processed_data_dir = Path(config_paths["processed_data"])
    exports_dir = Path(config_paths["exports"])
    logs_dir = Path(config_paths["logs"])
    years = build_year_list(args, config)
    export_format = args.export_format or config.get("export_format", "json")
    min_minutes = args.min_minutes if args.min_minutes is not None else config.get("min_minutes_played")

    steps: List[PipelineStep] = []
    step_index = 1

    if not args.skip_fetch:
        command = [
            sys.executable,
            str(BASE_DIR / "fetch_statsbomb.py"),
            "--raw-data",
            str(raw_data_dir),
            "--years",
            *years,
        ]
        steps.append(PipelineStep(step_index, "Fetching StatsBomb data", command))
        step_index += 1

    command = [
        sys.executable,
        str(BASE_DIR / "build_player_stats.py"),
        "--raw-data",
        str(raw_data_dir),
        "--processed-data",
        str(processed_data_dir),
    ]
    if min_minutes is not None:
        command.extend(["--min-minutes", str(min_minutes)])
    steps.append(PipelineStep(step_index, "Building player statistics", command))
    step_index += 1

    steps.append(
        PipelineStep(
            step_index,
            "Calculating IoG",
            [
                sys.executable,
                str(BASE_DIR / "calculate_iog.py"),
                "--processed-data",
                str(processed_data_dir),
            ],
        )
    )
    step_index += 1

    if not args.skip_export:
        steps.append(
            PipelineStep(
                step_index,
                "Exporting players.json",
                [
                    sys.executable,
                    str(BASE_DIR / "export_players.py"),
                    "--processed-data",
                    str(processed_data_dir),
                    "--exports",
                    str(exports_dir),
                    "--export-format",
                    export_format,
                ],
            )
        )
        # Add a final step to sync the exported data to the app source
        steps.append(
            PipelineStep(
                step_index,
                "Syncing to App Source (pipeline)" ,
                [
                    sys.executable,
                    "-c",
                    f"import shutil; shutil.copy({str(exports_dir / 'players.json')!r}, {str(SRC_DATA_DIR / 'players.json')!r})",
                ],
            )
        )

        # Post-export verification + quick stats
        steps.append(
            PipelineStep(
                step_index + 1,
                "Post-export verification (counts/top players)",
                [
                    sys.executable,
                    "-c",
                    "import json, pathlib; p=pathlib.Path('src/data/players.json');\n"
                    "d=json.loads(p.read_text(encoding='utf-8'));\n"
                    "print('POST: total players',len(d));\n"
                    "d_sorted=sorted(d, key=lambda x: float(x.get('iog',0) or 0), reverse=True)[:5];\n"
                    "print('POST: first 5 players by IoG');\n"
                    "[print(' -',x.get('name'),x.get('club'),x.get('era'),x.get('league'), 'iog=',x.get('iog')) for x in d_sorted];\n"
                    "from collections import Counter;\n"
                    "for f in ['league','club','era']:\n"
                    " c=Counter([x.get(f) for x in d]);\n"
                    " print('POST count_by_'+f, len(c));\n"
                    " print(c.most_common(10));\n",
                ],
            )
        )


    logger = logging.getLogger("galactico11_pipeline")
    logger.setLevel(logging.DEBUG)
    log_file = logs_dir / "pipeline.log"
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)

    logger.info("Pipeline started: %s", datetime.utcnow().isoformat())
    logger.info("Config: %s", json.dumps(config, indent=2))
    logger.info("Args: %s", vars(args))

    print("GALACTICO11 DATA PIPELINE\n")
    total_start = time.perf_counter()

    for step in steps:
        run_step(step, logger)

    total_duration = time.perf_counter() - total_start
    print("Pipeline completed successfully.")
    print(f"Total duration: {format_duration(total_duration)}")

    logger.info("Pipeline completed successfully")
    logger.info("Total duration: %s", format_duration(total_duration))
    logger.info("Pipeline ended: %s", datetime.utcnow().isoformat())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Galactico11 StatsBomb IoG data pipeline")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Pipeline configuration YAML file")
    parser.add_argument("--start-year", type=int, help="Start season year for data download")
    parser.add_argument("--end-year", type=int, help="End season year for data download")
    parser.add_argument("--years", nargs="*", help="Explicit season years to download")
    parser.add_argument("--skip-fetch", action="store_true", help="Skip raw StatsBomb download")
    parser.add_argument("--skip-export", action="store_true", help="Skip final export step")
    parser.add_argument("--export-format", choices=["json", "csv"], default=None, help="Final export file format")
    parser.add_argument("--min-minutes", type=int, default=None, help="Minimum minutes played filter for player stats")
    return parser.parse_args()


if __name__ == "__main__":
    parsed_args = parse_args()
    pipeline_config = load_config(parsed_args.config)
    if parsed_args.export_format is not None:
        pipeline_config["export_format"] = parsed_args.export_format
    if parsed_args.min_minutes is not None:
        pipeline_config["min_minutes_played"] = parsed_args.min_minutes
    run_pipeline(parsed_args, pipeline_config)
