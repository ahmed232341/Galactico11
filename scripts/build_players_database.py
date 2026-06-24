import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from statsbombpy import sb

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SRC_DATA_DIR = PROJECT_ROOT / "src" / "data"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(DATA_DIR / "build.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def ensure_dirs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    SRC_DATA_DIR.mkdir(parents=True, exist_ok=True)


def era_from_season(season_str: str) -> str:
    try:
        year = int(season_str.split("/")[0])
        decade = (year // 10) * 10
        return f"{decade}s"
    except (ValueError, IndexError):
        return "unknown"


def fetch_competitions() -> pd.DataFrame:
    try:
        logger.info("Fetching competitions...")
        comps = sb.competitions()
        if comps.empty:
            logger.warning("No competitions found")
            return comps
        logger.info(f"Fetched {len(comps)} competitions")
        return comps
    except Exception as e:
        logger.error(f"Error fetching competitions: {e}")
        return pd.DataFrame()


def fetch_matches(comp_id: int, season_id: int) -> pd.DataFrame:
    try:
        matches = sb.matches(competition_id=comp_id, season_id=season_id)
        return matches
    except Exception as e:
        logger.warning(f"Error fetching matches for comp {comp_id}, season {season_id}: {e}")
        return pd.DataFrame()


def fetch_events(match_id: int) -> pd.DataFrame:
    try:
        events = sb.events(match_id=match_id)
        return events
    except Exception as e:
        logger.warning(f"Error fetching events for match {match_id}: {e}")
        return pd.DataFrame()


def extract_event_data(event: Dict[str, Any], match_data: Dict[str, Any], player_events: Dict[int, List[Dict[str, Any]]]) -> None:
    try:
        player = event.get("player")
        if not player:
            return

        player_id = player.get("player_id")
        if not player_id:
            return

        if player_id not in player_events:
            player_events[player_id] = []

        event_data = {
            "match_id": match_data.get("match_id"),
            "competition": match_data.get("competition_name"),
            "season": match_data.get("season"),
            "team": event.get("team", {}).get("name"),
            "position": player.get("position"),
            "type": event.get("type", {}).get("name"),
            "subtype": event.get("subtype", {}).get("name"),
            "minute": event.get("minute"),
            "second": event.get("second"),
        }

        event_type = event_data["type"]

        if event_type == "Shot":
            event_data["goal"] = event.get("shot", {}).get("outcome", {}).get("name") == "Goal"
            event_data["on_target"] = event.get("shot", {}).get("outcome", {}).get("name") == "On Target"
            event_data["xg"] = float(event.get("shot", {}).get("statsbomb_xg", 0) or 0)

        if event_type == "Pass":
            event_data["goal_assist"] = event.get("pass", {}).get("outcome", {}).get("name") == "Goal Assist"
            event_data["xg_assist"] = float(event.get("pass", {}).get("statsbomb_xg", 0) or 0)
            event_data["pass_type"] = event.get("pass", {}).get("type", {}).get("name")
            event_data["length"] = float(event.get("pass", {}).get("length", 0) or 0)

        if event_type in {"Tackle", "Interception", "Block", "Clearance", "Pressure"}:
            event_data["defensive"] = True

        player_events[player_id].append(event_data)

    except Exception as e:
        logger.debug(f"Error processing event: {e}")


def build_player_stats(player_events: Dict[int, List[Dict[str, Any]]], players_metadata: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
    logger.info("Aggregating player statistics...")
    players_stats: Dict[str, Dict[str, Any]] = {}

    for player_id, events in player_events.items():
        if not events:
            continue

        metadata = players_metadata.get(player_id, {})
        player_name = metadata.get("name", "Unknown")
        player_nationality = metadata.get("nationality", "Unknown")

        for event in events:
            key = (
                player_id,
                player_name,
                player_nationality,
                event.get("team"),
                event.get("competition"),
                event.get("season")
            )

            if key not in players_stats:
                players_stats[key] = {
                    "player_id": player_id,
                    "name": player_name,
                    "nationality": player_nationality,
                    "club": event.get("team"),
                    "league": event.get("competition"),
                    "season": event.get("season"),
                    "era": era_from_season(event.get("season", "")),
                    "positions": set(),
                    "appearances": 0,
                    "minutes": 0,
                    "goals": 0,
                    "assists": 0,
                    "shots": 0,
                    "shots_on_target": 0,
                    "xg": 0.0,
                    "xa": 0.0,
                    "key_passes": 0,
                    "progressive_passes": 0,
                    "progressive_carries": 0,
                    "touches": 0,
                    "dribbles": 0,
                    "successful_dribbles": 0,
                    "tackles": 0,
                    "interceptions": 0,
                    "recoveries": 0,
                    "blocks": 0,
                    "clearances": 0,
                    "saves": 0,
                    "clean_sheets": 0,
                    "yellow_cards": 0,
                    "red_cards": 0,
                    "fouls": 0,
                }

            stat = players_stats[key]

            if event.get("position"):
                stat["positions"].add(normalize_position(event.get("position")))

            if event.get("type") == "Shot":
                stat["shots"] += 1
                if event.get("on_target"):
                    stat["shots_on_target"] += 1
                if event.get("goal"):
                    stat["goals"] += 1
                stat["xg"] += event.get("xg", 0.0)

            if event.get("type") == "Pass":
                if event.get("goal_assist"):
                    stat["assists"] += 1
                stat["xa"] += event.get("xg_assist", 0.0)
                if event.get("pass_type") in {"Through Ball", "Chipped Pass"}:
                    stat["key_passes"] += 1

            if event.get("type") == "Carry":
                stat["touches"] += 1

            if event.get("type") == "Ball Receipt":
                stat["touches"] += 1

            if event.get("type") in {"Tackle", "Ground defending"}:
                stat["tackles"] += 1

            if event.get("type") == "Interception":
                stat["interceptions"] += 1

            if event.get("type") == "Block":
                stat["blocks"] += 1

            if event.get("type") == "Clearance":
                stat["clearances"] += 1

            if event.get("type") == "Shot" and event.get("subtype") == "Penalty Saved":
                stat["saves"] += 1

            if event.get("type") == "Foul Committed":
                stat["fouls"] += 1

            if event.get("type") == "Miscontrol":
                pass

    result = []
    for key, stat in players_stats.items():
        stat["positions"] = sorted(list(stat["positions"])) or ["Unknown"]
        result.append(stat)

    logger.info(f"Built statistics for {len(result)} player-season combinations")
    return result


def normalize_position(pos: str) -> str:
    pos = str(pos).upper().strip()
    mapping = {
        "GK": "GK",
        "CB": "CB",
        "LB": "LB",
        "RB": "RB",
        "LWB": "LB",
        "RWB": "RB",
        "DM": "CDM",
        "CM": "CM",
        "CAM": "CAM",
        "LM": "LM",
        "RM": "RM",
        "LW": "LW",
        "RW": "RW",
        "CF": "ST",
        "ST": "ST",
        "SS": "CAM",
        "AM": "CAM",
    }
    return mapping.get(pos, pos)


def calculate_iog(player: Dict[str, Any]) -> float:
    position_group = categorize_position(player.get("positions", ["Unknown"])[0])
    base_score = 50.0

    if position_group == "GK":
        base_score = 50 + (player.get("saves", 0) * 2) + (player.get("clean_sheets", 0) * 3)

    elif position_group == "DEF":
        base_score = 50 + (player.get("tackles", 0) * 1.5) + (player.get("interceptions", 0) * 1.8) + (player.get("blocks", 0) * 1.2) + (player.get("clearances", 0) * 0.8)

    elif position_group == "MID":
        base_score = 50 + (player.get("assists", 0) * 3) + (player.get("key_passes", 0) * 1.5) + (player.get("tackles", 0) * 0.8) + (player.get("interceptions", 0) * 1.0) + (player.get("xg", 0) * 1.2)

    elif position_group == "FWD":
        base_score = 50 + (player.get("goals", 0) * 4) + (player.get("assists", 0) * 2.5) + (player.get("xg", 0) * 1.5) + (player.get("shots_on_target", 0) * 0.8)

    iog = max(1, min(100, base_score))
    return round(iog, 1)


def categorize_position(position: str) -> str:
    pos = str(position).upper()
    if pos == "GK":
        return "GK"
    if pos in {"CB", "LB", "RB", "LWB", "RWB"}:
        return "DEF"
    if pos in {"CM", "CDM", "CAM", "LM", "RM"}:
        return "MID"
    if pos in {"ST", "CF", "LW", "RW", "SS"}:
        return "FWD"
    return "MID"


def format_players_output(players_stats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    logger.info("Formatting players for export...")
    output = []

    for player in players_stats:
        iog = calculate_iog(player)

        output.append({
            "id": int(player.get("player_id", 0)),
            "name": player.get("name", "Unknown"),
            "club": player.get("club", "Unknown"),
            "league": player.get("league", "Unknown"),
            "era": player.get("era", "Unknown"),
            "positions": player.get("positions", ["Unknown"]),
            "iog": iog,
            "goals": int(player.get("goals", 0)),
            "assists": int(player.get("assists", 0)),
            "xg": round(float(player.get("xg", 0)), 2),
            "xa": round(float(player.get("xa", 0)), 2),
            "shots": int(player.get("shots", 0)),
            "shots_on_target": int(player.get("shots_on_target", 0)),
            "tackles": int(player.get("tackles", 0)),
            "interceptions": int(player.get("interceptions", 0)),
            "blocks": int(player.get("blocks", 0)),
            "clearances": int(player.get("clearances", 0)),
            "touches": int(player.get("touches", 0)),
            "minutes": int(player.get("minutes", 0)),
        })

    return sorted(output, key=lambda p: p.get("iog", 0), reverse=True)


def build_database(force: bool = False):
    ensure_dirs()
    logger.info("Starting player database build...")

    comps = fetch_competitions()
    if comps.empty:
        logger.error("No competitions available. Cannot proceed.")
        return

    player_events: Dict[int, List[Dict[str, Any]]] = {}
    players_metadata: Dict[int, Dict[str, Any]] = {}
    match_count = 0
    event_count = 0

    season_column = "season_name" if "season_name" in comps.columns else "season"
    logger.info(f"Using season column: {season_column}")

    for _, comp_row in comps.iterrows():
        try:
            comp_id = int(comp_row.get("competition_id"))
            season_id = int(comp_row.get("season_id"))
            comp_name = str(comp_row.get("competition_name", "Unknown"))
            season = str(comp_row.get(season_column, "Unknown"))

            logger.info(f"Processing {comp_name} {season}...")

            matches = fetch_matches(comp_id, season_id)
            if matches.empty:
                continue

            match_count += len(matches)

            for _, match_row in matches.iterrows():
                match_id = int(match_row.get("match_id"))
                match_data = {
                    "match_id": match_id,
                    "competition_name": comp_name,
                    "season": season,
                }

                events = fetch_events(match_id)
                if events.empty:
                    continue

                event_count += len(events)

                for _, event in events.iterrows():
                    extract_event_data(event, match_data, player_events)

                    player = event.get("player")
                    if player:
                        player_id = player.get("player_id")
                        if player_id and player_id not in players_metadata:
                            players_metadata[player_id] = {
                                "name": player.get("name"),
                                "nationality": player.get("nationality"),
                            }

        except Exception as e:
            logger.error(f"Error processing competition row: {e}")
            continue

    logger.info(f"Processed {match_count} matches with {event_count} events")

    players_stats = build_player_stats(player_events, players_metadata)
    output = format_players_output(players_stats)

    output_path = SRC_DATA_DIR / "players.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(f"Exported {len(output)} players to {output_path}")
    logger.info("Player database build complete!")

    return output


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build Galactico11 players database from StatsBomb data")
    parser.add_argument("--force", action="store_true", help="Force rebuild")
    args = parser.parse_args()

    build_database(force=args.force)
