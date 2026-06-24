import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_RAW_DIR = BASE_DIR.parent / "data" / "raw"
DEFAULT_PROCESSED_DIR = BASE_DIR.parent / "data" / "processed"

POSITION_MAP = {
    "goalkeeper": "GK",
    "right back": "RB",
    "right wing back": "RWB",
    "right center back": "CB",
    "center back": "CB",
    "left center back": "CB",
    "left back": "LB",
    "left wing back": "LWB",
    "right defensive midfield": "CDM",
    "center defensive midfield": "CDM",
    "left defensive midfield": "CDM",
    "right center midfield": "CM",
    "center midfield": "CM",
    "left center midfield": "CM",
    "right attacking midfield": "CAM",
    "center attacking midfield": "CAM",
    "left attacking midfield": "CAM",
    "right midfield": "RM",
    "left midfield": "LM",
    "right wing": "RW",
    "left wing": "LW",
    "center forward": "ST",
    "striker": "ST",
}


def is_present(value) -> bool:
    if value is None:
        return False
    try:
        return bool(pd.notna(value))
    except ValueError:
        return True


def raw_paths(raw_data_dir: Path):
    return raw_data_dir / "competitions", raw_data_dir / "matches", raw_data_dir / "events"


@dataclass
class PlayerStats:
    player_id: int
    name: str
    nationality: str
    club: str
    league: str
    season: str
    era: str
    positions: List[str] = field(default_factory=list)

    goals: int = 0
    npxG: float = 0.0
    shots: int = 0
    shots_on_target: int = 0
    xG_per_shot: float = 0.0
    big_chances: int = 0

    assists: int = 0
    xA: float = 0.0
    key_passes: int = 0
    through_balls: int = 0
    chances_created: int = 0

    progressive_passes: int = 0
    progressive_carries: int = 0
    carries_into_box: int = 0
    passes_into_box: int = 0

    touches: int = 0
    possession_won: int = 0
    possession_lost: int = 0

    tackles: int = 0
    interceptions: int = 0
    blocks: int = 0
    clearances: int = 0
    pressures: int = 0
    counterpressures: int = 0

    saves: int = 0
    save_percentage: float = 0.0
    goals_prevented: float = 0.0

    possession_value: float = 0.0
    ball_progression_value: float = 0.0
    attacking_value: float = 0.0
    defensive_value: float = 0.0

    minutes: int = 0

    def to_dict(self):
        data = asdict(self)
        data["positions"] = sorted(set(self.positions))
        return data


def event_tagged(event, tag_id: int) -> bool:
    tags = event.get("tags", [])
    if not isinstance(tags, list):
        return False
    return any(isinstance(tag, dict) and tag.get("id") == tag_id for tag in tags)


def event_in_box(event) -> bool:
    location = event.get("location")
    if not isinstance(location, list) or len(location) < 2:
        return False
    x, y = location
    return x >= 96 and 21 <= y <= 79


def era_from_season(season: str) -> str:
    year = int(season.split("/")[0])
    decade = (year // 10) * 10
    return f"{decade}s"


def load_matches(matches_dir: Path) -> pd.DataFrame:
    all_matches = []
    for path in matches_dir.glob("*.json"):
        with path.open("r", encoding="utf-8") as handle:
            records = json.load(handle)
        all_matches.extend(records)
    return pd.DataFrame(all_matches)


def load_events(events_dir: Path) -> pd.DataFrame:
    all_events = []
    for path in events_dir.glob("*.json"):
        with path.open("r", encoding="utf-8") as handle:
            records = json.load(handle)
        competition_name, season = competition_and_season_from_event_path(path)
        for record in records:
            record.setdefault("competition_name", competition_name)
            record.setdefault("season", season)
        all_events.extend(records)
    return pd.DataFrame(all_events)


def fill_competition_and_season_from_matches(events: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    if "match_id" not in events.columns or "match_id" not in matches.columns:
        return events

    match_columns = [column for column in ["match_id", "competition_name", "season"] if column in matches.columns]
    if len(match_columns) < 3:
        return events

    match_lookup = matches[match_columns].drop_duplicates("match_id")
    events = events.merge(match_lookup, on="match_id", how="left", suffixes=("", "_from_match"))
    for column in ["competition_name", "season"]:
        match_column = f"{column}_from_match"
        if match_column in events.columns:
            events[column] = events[column].where(events[column].apply(is_present), events[match_column])
            events = events.drop(columns=[match_column])
    return events


def competition_and_season_from_event_path(path: Path) -> tuple:
    stem = path.stem
    if not stem.startswith("events_"):
        return "unknown", "unknown"
    parts = stem.removeprefix("events_").rsplit("_", 2)
    if len(parts) != 3:
        return "unknown", "unknown"
    competition_name, season, _ = parts
    return competition_name.replace("_", " "), season.replace("_", "/")


def series_from_existing_or_nested(events: pd.DataFrame, existing_columns: List[str], nested_column: str, nested_keys: List[str]) -> pd.Series:
    for column in existing_columns:
        if column in events.columns and events[column].notna().any():
            non_null_values = events[column].dropna()
            if column != nested_column or not non_null_values.map(lambda value: isinstance(value, dict)).any():
                return events[column]

    if nested_column in events.columns:
        def from_nested(value):
            if not isinstance(value, dict):
                return None
            for key in nested_keys:
                if key in value and is_present(value[key]):
                    return value[key]
            return None

        return events[nested_column].apply(from_nested)

    return pd.Series([None] * len(events), index=events.index)


def get_existing_or_nested_player_id(events: pd.DataFrame) -> pd.Series:
    return series_from_existing_or_nested(events, ["player_id"], "player", ["player_id", "id"])


def get_existing_or_nested_player_name(events: pd.DataFrame) -> pd.Series:
    return series_from_existing_or_nested(events, ["player_name", "player"], "player", ["name", "player_name"])


def get_existing_or_nested_player_position(events: pd.DataFrame) -> pd.Series:
    return series_from_existing_or_nested(events, ["player_position", "position"], "player", ["position", "player_position"])


def get_existing_or_nested_team_name(events: pd.DataFrame) -> pd.Series:
    return series_from_existing_or_nested(events, ["team_name", "team"], "team", ["name", "team_name"])


def normalize_position(position) -> Optional[str]:
    if not is_present(position):
        return None
    value = str(position).strip()
    if not value:
        return None
    upper_value = value.upper()
    allowed = {"GK", "RB", "CB", "LB", "RWB", "LWB", "CDM", "CM", "CAM", "RM", "LM", "RW", "LW", "ST"}
    if upper_value in allowed:
        return upper_value
    return POSITION_MAP.get(value.lower())


def nested_or_flat_value(event, nested_column: str, nested_path: List[str], flat_column: Optional[str] = None):
    value = event.get(nested_column)
    if isinstance(value, dict):
        current = value
        for key in nested_path:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current
    if flat_column:
        value = event.get(flat_column)
        if is_present(value):
            return value
    return None


def event_type_name(event) -> Optional[str]:
    value = event.get("type")
    if isinstance(value, dict):
        return value.get("name")
    if is_present(value):
        return str(value)
    return None


def event_subtype_name(event) -> Optional[str]:
    value = event.get("subtype")
    if isinstance(value, dict):
        return value.get("name")
    pass_type = event.get("pass_type")
    if is_present(pass_type):
        return str(pass_type)
    return None


def build_player_stats(raw_data_dir: Path, processed_data_dir: Path, min_minutes: int = 0):
    _, matches_dir, events_dir = raw_paths(raw_data_dir)
    processed_data_dir.mkdir(parents=True, exist_ok=True)

    matches = load_matches(matches_dir)
    events = load_events(events_dir)
    if events.empty or matches.empty:
        raise RuntimeError("No events or matches found. Run fetch_statsbomb first.")
    events = fill_competition_and_season_from_matches(events, matches)

    players: Dict[str, PlayerStats] = {}
    player_minutes: Dict[tuple, int] = {}

    print(f"Loaded matches rows={len(matches)}")
    print(f"Total events loaded: {len(events)}")
    print("Available columns:", list(events.columns))

    if 'type' not in events.columns:
        raise RuntimeError("Raw events do not include 'type' column; cannot compute player stats")
    if 'competition_name' not in events.columns:
        print("WARNING: events missing 'competition_name'. Using 'competition_name' as expected later may fail")
    if 'season' not in events.columns:
        print("WARNING: events missing 'season'. Using season field later may fail")

    events["player_id"] = get_existing_or_nested_player_id(events)
    events["player_name"] = get_existing_or_nested_player_name(events)
    events["player_position"] = get_existing_or_nested_player_position(events).apply(normalize_position)
    events["team_name"] = get_existing_or_nested_team_name(events)
    if "player_nationality" not in events.columns:
        events["player_nationality"] = series_from_existing_or_nested(events, ["player_nationality"], "player", ["nationality"])

    print("Non-null player_id rows:", int(events["player_id"].notna().sum()))
    print("Non-null player_name rows:", int(events["player_name"].notna().sum()))
    print("Non-null team_name rows:", int(events["team_name"].notna().sum()))
    print("Non-null player_position rows:", int(events["player_position"].notna().sum()))

    if int(events["player_id"].notna().sum()) == 0:
        raise RuntimeError("No player identity columns found. Check raw event schema.")

    for _, event in events.iterrows():


        player_id = event["player_id"]
        if not is_present(player_id):
            continue

        season = event["season"]
        league = event["competition_name"]
        club = event["team_name"]
        era = era_from_season(season)
        name = event["player_name"]
        nationality = event["player_nationality"] if is_present(event["player_nationality"]) else ""
        position = event["player_position"]
        minute_value = event.get("minute")
        minute = int(minute_value) if is_present(minute_value) else 0

        key = (player_id, name, club, league, season, era)
        player_minutes[key] = max(player_minutes.get(key, 0), minute)

        if key not in players:
            players[key] = PlayerStats(
                player_id=int(player_id),
                name=name if is_present(name) else "",
                nationality=nationality,
                club=club,
                league=league,
                season=season,
                era=era,
                positions=[position] if is_present(position) else [],
            )

        stats = players[key]
        if is_present(position) and position not in stats.positions:
            stats.positions.append(position)

        event_type = event_type_name(event)
        event_subtype = event_subtype_name(event)

        if event_type == "Shot":
            stats.shots += 1
            stats.npxG += float(nested_or_flat_value(event, "shot", ["statsbomb_xg"], "shot_statsbomb_xg") or 0.0)
            shot_outcome = nested_or_flat_value(event, "shot", ["outcome", "name"], "shot_outcome")
            if shot_outcome == "Goal":
                stats.goals += 1
            if shot_outcome == "On Target":
                stats.shots_on_target += 1
            if event_tagged(event, 1011):
                stats.big_chances += 1

        if event_type == "Pass":
            pass_outcome = nested_or_flat_value(event, "pass", ["outcome", "name"], "pass_outcome")
            if nested_or_flat_value(event, "pass", ["goal_assist"], "pass_goal_assist") or pass_outcome == "Goal Assist":
                stats.assists += 1
            if is_present(nested_or_flat_value(event, "pass", ["recipient"], "pass_recipient")):
                stats.chances_created += 1
            if event_tagged(event, 1801):
                stats.progressive_passes += 1
            if event_in_box(event):
                stats.passes_into_box += 1
            if event_subtype == "Through Ball":
                stats.through_balls += 1
            if event_tagged(event, 302):
                stats.key_passes += 1
            stats.xA += float(nested_or_flat_value(event, "pass", ["statsbomb_xg"], "pass_statsbomb_xg") or 0.0)

        if event_type == "Carry":
            if event_tagged(event, 1802):
                stats.progressive_carries += 1
            if event_in_box(event):
                stats.carries_into_box += 1

        if event_type == "Ball Receipt":
            stats.touches += 1

        if event_type in {"Tackle", "Ground defending"}:
            stats.tackles += 1
            stats.possession_won += 1

        if event_type == "Interception":
            stats.interceptions += 1
            stats.possession_won += 1

        if event_type == "Block":
            stats.blocks += 1

        if event_type == "Clearance":
            stats.clearances += 1

        if event_type == "Pressure":
            stats.pressures += 1
            if event_tagged(event, 1002):
                stats.counterpressures += 1

        if event_type == "Shot" and nested_or_flat_value(event, "shot", ["outcome", "name"], "shot_outcome") == "Saved":
            stats.saves += 1

        if event_type == "Pass" and nested_or_flat_value(event, "pass", ["outcome", "name"], "pass_outcome") == "Incomplete":
            stats.possession_lost += 1

        if event_type == "Ball Receipt" and nested_or_flat_value(event, "ball_receipt", ["miscontrol"], "ball_receipt_miscontrol"):
            stats.possession_lost += 1

        touches = event.get("touches", 0)
        stats.touches += int(touches) if is_present(touches) else 0

    for key, stats in players.items():
        stats.minutes = player_minutes.get(key, 0) + 1
        if stats.shots > 0:
            stats.xG_per_shot = stats.npxG / stats.shots
        if stats.saves + stats.goals_prevented > 0:
            stats.save_percentage = float(stats.saves) / max(1, stats.saves + stats.goals_prevented) * 100
        stats.attacking_value = stats.goals * 1.8 + stats.npxG * 1.3 + stats.shots_on_target * 0.6
        stats.creation_value = stats.assists * 2.0 + stats.xA * 1.4 + stats.key_passes * 0.8 + stats.chances_created * 0.7
        stats.ball_progression_value = stats.progressive_passes * 0.9 + stats.progressive_carries * 1.0 + stats.carries_into_box * 1.3 + stats.passes_into_box * 1.2
        stats.defensive_value = stats.tackles * 1.1 + stats.interceptions * 1.2 + stats.blocks * 1.0 + stats.clearances * 0.9 + stats.pressures * 0.5
        stats.possession_value = stats.touches * 0.04 + stats.possession_won * 0.8 - stats.possession_lost * 0.6

    data = [stats.to_dict() for stats in players.values()]
    df = pd.DataFrame(data)
    # Ensure minutes column exists before filtering
    if "minutes" not in df.columns:
        df["minutes"] = 0

    print(f"player_stats dataframe columns: {list(df.columns)}")
    print(f"Filtering by min_minutes={min_minutes} (current rows={len(df)})")
    if min_minutes > 0:
        if "minutes" not in df.columns:
            raise RuntimeError("Internal error: df is missing 'minutes' column before filtering")
        df = df[df["minutes"] >= min_minutes].copy()

    stats_csv_path = processed_data_dir / "player_stats.csv"
    df.to_csv(stats_csv_path, index=False)
    print(f"Wrote {stats_csv_path} rows={len(df)}")

    # Parquet is optional (depends on pyarrow/fastparquet)
    stats_parquet_path = processed_data_dir / "player_stats.parquet"
    try:
        df.to_parquet(stats_parquet_path, index=False)
        print(f"Wrote {stats_parquet_path} rows={len(df)}")
    except Exception as e:
        print(f"WARNING: Could not write parquet {stats_parquet_path}: {e}")
        if stats_parquet_path.exists():
            stats_parquet_path.unlink()
            print(f"Removed stale parquet {stats_parquet_path}; downstream steps should use CSV.")

    print(f"Built player stats for {len(df)} player-seasons.")



def main():
    parser = argparse.ArgumentParser(description="Build player statistics for Galactico11 from raw StatsBomb event data")
    parser.add_argument("--raw-data", type=Path, default=DEFAULT_RAW_DIR, help="Raw data root directory")
    parser.add_argument("--processed-data", type=Path, default=DEFAULT_PROCESSED_DIR, help="Processed output directory")
    parser.add_argument("--min-minutes", type=int, default=0, help="Filter players with fewer than this many minutes")
    args = parser.parse_args()

    build_player_stats(raw_data_dir=args.raw_data, processed_data_dir=args.processed_data, min_minutes=args.min_minutes)


if __name__ == "__main__":
    main()
