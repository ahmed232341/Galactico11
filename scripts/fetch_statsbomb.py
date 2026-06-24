import argparse
import json
from pathlib import Path
from typing import List, Optional

from statsbombpy import sb

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_RAW_DIR = BASE_DIR.parent / "data" / "raw"


def raw_paths(raw_data_dir: Path):
    competitions_dir = raw_data_dir / "competitions"
    matches_dir = raw_data_dir / "matches"
    events_dir = raw_data_dir / "events"
    return competitions_dir, matches_dir, events_dir


def ensure_dirs(raw_data_dir: Path):
    for directory in raw_paths(raw_data_dir):
        directory.mkdir(parents=True, exist_ok=True)


def save_json(path: Path, payload):
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def download_competitions(raw_data_dir: Path, years: Optional[List[str]] = None, competitions: Optional[List[str]] = None, force: bool = False, debug: bool = False):
    competitions_dir, _, _ = raw_paths(raw_data_dir)
    ensure_dirs(raw_data_dir)
    comps = sb.competitions()
    if debug:
        print(comps.columns.tolist())

    if "season_name" in comps.columns:
        season_column = "season_name"
    elif "season" in comps.columns:
        season_column = "season"
    else:
        raise ValueError(
            f"Could not find season column. Available columns: {comps.columns.tolist()}"
        )

    required_columns = ["competition_id", "season_id", season_column, "competition_name"]
    missing_columns = [col for col in required_columns if col not in comps.columns]
    if missing_columns:
        raise ValueError(
            f"StatsBomb competitions response is missing required columns: {missing_columns}. Available columns: {comps.columns.tolist()}"
        )
    if years:
        comps = comps[comps[season_column].astype(str).isin(years)]
    if competitions:
        comps = comps[comps["competition_name"].isin(competitions)]

    competition_files = []
    for _, row in comps.iterrows():
        row_dict = row.to_dict()
        comp_id = int(row_dict["competition_id"])
        season_value = str(row_dict.get(season_column, row_dict.get("season", "unknown"))).replace("/", "_")
        competition_name = str(row_dict.get("competition_name", "competition")).replace(" ", "_")
        filename = competitions_dir / f"competition_{comp_id}_{competition_name}_{season_value}.json"
        if filename.exists() and not force:
            competition_files.append(filename)
            continue
        save_json(filename, row.to_dict())
        competition_files.append(filename)
    return competition_files


def download_matches(raw_data_dir: Path, force: bool = False):
    competitions_dir, matches_dir, _ = raw_paths(raw_data_dir)
    ensure_dirs(raw_data_dir)
    competition_files = list(competitions_dir.glob("competition_*.json"))
    match_files = []
    for comp_file in competition_files:
        with comp_file.open("r", encoding="utf-8") as handle:
            competition = json.load(handle)
        competition_id = competition["competition_id"]
        season_id = competition["season_id"]
        season = competition.get("season_name") or competition.get("season")
        if season is None:
            raise ValueError(
                f"Competition file {comp_file} is missing season_name or season"
            )
        competition_name = competition["competition_name"].replace(" ", "_")
        season_filename = str(season).replace("/", "_")
        matches = sb.matches(competition_id=competition_id, season_id=season_id)
        filename = matches_dir / f"matches_{competition_name}_{season_filename}.json"
        if filename.exists() and not force:
            match_files.append(filename)
            continue
        save_json(filename, matches.to_dict(orient="records"))
        match_files.append(filename)
    return match_files


def download_events(raw_data_dir: Path, force: bool = False):
    _, matches_dir, events_dir = raw_paths(raw_data_dir)
    ensure_dirs(raw_data_dir)
    match_files = list(matches_dir.glob("matches_*.json"))
    event_files = []
    for match_file in match_files:
        with match_file.open("r", encoding="utf-8") as handle:
            matches = json.load(handle)
        for match in matches:
            match_id = match["match_id"]
            competition_name = match["competition_name"].replace(" ", "_")
            season = match["season"].replace("/", "_")
            filename = events_dir / f"events_{competition_name}_{season}_{match_id}.json"
            if filename.exists() and not force:
                event_files.append(filename)
                continue
            events = sb.events(match_id=match_id)
            save_json(filename, events.to_dict(orient="records"))
            event_files.append(filename)
    return event_files


def main():
    parser = argparse.ArgumentParser(description="Fetch StatsBomb open data for Galactico11 IoG pipeline")
    parser.add_argument("--raw-data", type=Path, default=DEFAULT_RAW_DIR, help="Directory for raw StatsBomb files")
    parser.add_argument("--years", nargs="*", help="List of seasons to download, e.g. 2018 2019")
    parser.add_argument("--competitions", nargs="*", help="Competition names to download")
    parser.add_argument("--force", action="store_true", help="Force re-download of existing files")
    args = parser.parse_args()

    download_competitions(args.raw_data, years=args.years, competitions=args.competitions, force=args.force)
    download_matches(args.raw_data, force=args.force)
    download_events(args.raw_data, force=args.force)


if __name__ == "__main__":
    main()
