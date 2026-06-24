import argparse
import json
import re
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DEFAULT_INPUT_DIRS = [
    PROJECT_ROOT / "data" / "raw" / "footballcsv",
    PROJECT_ROOT / "data" / "raw" / "football_csv",
    PROJECT_ROOT / "data" / "raw" / "football-data",
    PROJECT_ROOT / "data" / "raw" / "football_data",
    PROJECT_ROOT / "data" / "raw" / "datahub",
]
DEFAULT_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_PLAYERS_PATHS = [
    PROJECT_ROOT / "data" / "exports" / "players.json",
    PROJECT_ROOT / "src" / "data" / "players.json",
]

LEAGUE_ALIASES = {
    "E0": "Premier League",
    "ENG1": "Premier League",
    "ENGLAND": "Premier League",
    "ENGLAND 1": "Premier League",
    "PREMIER LEAGUE": "Premier League",
    "SP1": "La Liga",
    "ESP1": "La Liga",
    "SPAIN": "La Liga",
    "SPAIN 1": "La Liga",
    "LA LIGA": "La Liga",
    "PRIMERA DIVISION": "La Liga",
    "I1": "Serie A",
    "ITA1": "Serie A",
    "ITALY": "Serie A",
    "ITALY 1": "Serie A",
    "SERIE A": "Serie A",
    "D1": "Bundesliga",
    "GER1": "Bundesliga",
    "GERMANY": "Bundesliga",
    "GERMANY 1": "Bundesliga",
    "BUNDESLIGA": "Bundesliga",
    "1. BUNDESLIGA": "Bundesliga",
    "F1": "Ligue 1",
    "FRA1": "Ligue 1",
    "FRANCE": "Ligue 1",
    "FRANCE 1": "Ligue 1",
    "LIGUE 1": "Ligue 1",
}
SUPPORTED_LEAGUES = {"Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"}

LEAGUE_COLUMNS = ["league", "League", "competition", "Competition", "division", "Division", "Div", "div"]
SEASON_COLUMNS = ["season", "Season", "season_name", "SeasonName", "year", "Year"]
HOME_COLUMNS = ["HomeTeam", "home_team", "home", "Home", "hometeam", "home.name"]
AWAY_COLUMNS = ["AwayTeam", "away_team", "away", "Away", "awayteam", "away.name"]
CLUB_COLUMNS = ["club", "Club", "team", "Team", "team_name", "TeamName"]


def existing_input_dirs(paths: Iterable[Path]) -> list[Path]:
    return [path for path in paths if path.exists()]


def find_csv_paths(input_dirs: Iterable[Path]) -> list[Path]:
    paths: list[Path] = []
    for input_dir in input_dirs:
        if input_dir.is_file() and input_dir.suffix.lower() == ".csv":
            paths.append(input_dir)
        elif input_dir.is_dir():
            paths.extend(input_dir.rglob("*.csv"))
    return sorted(set(paths))


def first_existing_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    for column in candidates:
        if column in df.columns:
            return column
    lower_map = {str(column).lower(): column for column in df.columns}
    for column in candidates:
        match = lower_map.get(column.lower())
        if match is not None:
            return match
    return None


def normalize_league(value) -> Optional[str]:
    if value is None or pd.isna(value):
        return None
    key = str(value).strip().replace("_", " ").upper()
    key = re.sub(r"\s+", " ", key)
    return LEAGUE_ALIASES.get(key)


def infer_league_from_path(path: Path) -> Optional[str]:
    candidates = [path.stem, *[part for part in path.parts[-4:]]]
    for value in candidates:
        normalized = normalize_league(value)
        if normalized:
            return normalized
    return None


def season_start_year(value) -> Optional[int]:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    four_digit = re.search(r"(19|20)\d{2}", text)
    if four_digit:
        return int(four_digit.group(0))
    compact = re.fullmatch(r"(\d{2})(\d{2})", text)
    if compact:
        year = int(compact.group(1))
        return 1900 + year if year >= 50 else 2000 + year
    return None


def infer_season_from_path(path: Path) -> Optional[str]:
    for part in reversed(path.parts):
        start_year = season_start_year(part)
        if start_year is not None:
            return f"{start_year}/{str(start_year + 1)[-2:]}"
    return None


def normalize_season(value, path: Path) -> Optional[str]:
    start_year = season_start_year(value)
    if start_year is None:
        inferred = infer_season_from_path(path)
        if inferred:
            return inferred
        return None
    return f"{start_year}/{str(start_year + 1)[-2:]}"


def era_from_season(season: str) -> str:
    start_year = int(str(season).split("/")[0])
    return f"{(start_year // 10) * 10}s"


def clean_club(value) -> Optional[str]:
    if value is None or pd.isna(value):
        return None
    club = str(value).strip()
    return club or None


def clubs_from_dataframe(df: pd.DataFrame) -> list[str]:
    clubs: set[str] = set()
    home_column = first_existing_column(df, HOME_COLUMNS)
    away_column = first_existing_column(df, AWAY_COLUMNS)
    if home_column and away_column:
        for column in [home_column, away_column]:
            clubs.update(club for club in df[column].map(clean_club).dropna())
        return sorted(clubs)

    club_column = first_existing_column(df, CLUB_COLUMNS)
    if club_column:
        clubs.update(club for club in df[club_column].map(clean_club).dropna())
    return sorted(clubs)


def extract_universes_from_csv(path: Path) -> list[dict]:
    try:
        df = pd.read_csv(path)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin-1")

    if df.empty:
        return []

    league_column = first_existing_column(df, LEAGUE_COLUMNS)
    season_column = first_existing_column(df, SEASON_COLUMNS)

    league = normalize_league(df[league_column].dropna().iloc[0]) if league_column and df[league_column].notna().any() else infer_league_from_path(path)
    if league not in SUPPORTED_LEAGUES:
        return []

    season_value = df[season_column].dropna().iloc[0] if season_column and df[season_column].notna().any() else None
    season = normalize_season(season_value, path)
    if not season:
        return []

    start_year = int(season.split("/")[0])
    if start_year < 1993:
        return []

    records = []
    for club in clubs_from_dataframe(df):
        records.append(
            {
                "league": league,
                "club": club,
                "season": season,
                "era": era_from_season(season),
                "source_file": str(path),
            }
        )
    return records


def load_existing_player_universes(players_paths: Iterable[Path]) -> set[tuple[str, str, str]]:
    for path in players_paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as handle:
            players = json.load(handle)
        if not isinstance(players, list):
            continue
        return {
            (str(player.get("league")), str(player.get("club")), str(player.get("era")))
            for player in players
            if player.get("league") and player.get("club") and player.get("era")
        }
    return set()


def summarize_universes(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=["league", "club", "era", "first_season", "last_season", "seasons_count", "source_files"])

    df = pd.DataFrame(records).drop_duplicates(["league", "club", "season", "era"])
    grouped = (
        df.groupby(["league", "club", "era"], as_index=False)
        .agg(
            first_season=("season", "min"),
            last_season=("season", "max"),
            seasons_count=("season", "nunique"),
            source_files=("source_file", lambda values: ";".join(sorted(set(map(str, values))))),
        )
        .sort_values(["league", "era", "club"])
    )
    return grouped


def import_universes(input_dirs: list[Path], processed_data_dir: Path, players_paths: list[Path]) -> tuple[pd.DataFrame, pd.DataFrame]:
    processed_data_dir.mkdir(parents=True, exist_ok=True)
    csv_paths = find_csv_paths(input_dirs)

    records: list[dict] = []
    for path in csv_paths:
        records.extend(extract_universes_from_csv(path))

    universes = summarize_universes(records)
    player_universes = load_existing_player_universes(players_paths)

    if universes.empty:
        missing = pd.DataFrame(columns=[*universes.columns, "missing_reason"])
    else:
        has_pack = universes.apply(lambda row: (row["league"], row["club"], row["era"]) in player_universes, axis=1)
        missing = universes.loc[~has_pack].copy()
        missing["missing_reason"] = "No StatsBomb or curated player pack found for league+club+era"

    universes_path = processed_data_dir / "universes.csv"
    missing_path = processed_data_dir / "missing_universe_packs.csv"
    universes.to_csv(universes_path, index=False)
    missing.to_csv(missing_path, index=False)

    print(f"Scanned {len(csv_paths)} football.csv/DataHub CSV files.")
    print(f"Wrote {universes_path} rows={len(universes)}")
    print(f"Wrote {missing_path} rows={len(missing)}")
    print("Note: these CSVs are used only as historical universe scaffolding, never as player stat data.")
    return universes, missing


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import football.csv/DataHub league match CSVs as Galactico11 universe scaffolding only.")
    parser.add_argument("--input-dir", type=Path, action="append", help="Directory or CSV file to scan. Can be supplied more than once.")
    parser.add_argument("--processed-data", type=Path, default=DEFAULT_PROCESSED_DIR, help="Processed output directory")
    parser.add_argument("--players-json", type=Path, action="append", help="Existing players.json path used only to identify already-covered league+club+era packs")
    return parser.parse_args()


def main():
    args = parse_args()
    input_dirs = args.input_dir or existing_input_dirs(DEFAULT_INPUT_DIRS)
    players_paths = args.players_json or DEFAULT_PLAYERS_PATHS
    import_universes(input_dirs=input_dirs, processed_data_dir=args.processed_data, players_paths=players_paths)


if __name__ == "__main__":
    main()
