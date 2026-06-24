import argparse
import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PROCESSED_DIR = BASE_DIR.parent / "data" / "processed"
DEFAULT_EXPORTS_DIR = BASE_DIR.parent / "data" / "exports"


def as_positions(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if hasattr(value, "tolist"):
        return [str(item) for item in value.tolist()]
    if isinstance(value, str):
        return [value]
    return list(value)


def number_or_none(row, column):
    if column not in row or pd.isna(row[column]):
        return None
    return round(float(row[column]), 2)


def int_or_zero(row, column):
    if column not in row or pd.isna(row[column]):
        return 0
    return int(round(float(row[column])))


def export_players(processed_data_dir: Path, exports_dir: Path, export_format: str = "json"):
    exports_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(processed_data_dir / "player_iog.parquet")
    df = df.sort_values(["league", "season", "player_id"])

    players = []
    for _, row in df.iterrows():
        shots = float(row.get("shots", 0) or 0)
        shots_on_target = float(row.get("shots_on_target", 0) or 0)
        minutes = float(row.get("minutes", 0) or 0)
        shot_creation = int_or_zero(row, "chances_created")
        if shot_creation == 0:
            shot_creation = int_or_zero(row, "key_passes")
        players.append({
            "id": int(row["player_id"]),
            "name": row["name"],
            "club": row["club"],
            "league": row["league"],
            "season": row["season"],
            "era": row["era"],
            "positions": as_positions(row["positions"]),
            "iog": round(float(row["iog"]), 1),
            "attackIoG": round(float(row["AttackIoG"]), 1),
            "creationIoG": round(float(row["CreationIoG"]), 1),
            "progressionIoG": round(float(row["ProgressionIoG"]), 1),
            "defensiveIoG": round(float(row["DefensiveIoG"]), 1),
            "goalkeeperIoG": round(float(row["GoalkeeperIoG"]), 1),
            "percentile": round(float(row["position_percentile"]), 1),
            "rank_tier": str(row["rank_tier"]),
            "goals": int_or_zero(row, "goals"),
            "assists": int_or_zero(row, "assists"),
            "xg": number_or_none(row, "npxG"),
            "xa": number_or_none(row, "xA"),
            "shots": int_or_zero(row, "shots"),
            "shot_creation": shot_creation,
            "shots_on_target": int_or_zero(row, "shots_on_target"),
            "shots_on_target_pct": round(shots_on_target / shots * 100, 1) if shots > 0 else None,
            "key_passes": int_or_zero(row, "key_passes"),
            "progressive_passes": int_or_zero(row, "progressive_passes"),
            "progressive_carries": int_or_zero(row, "progressive_carries"),
            "carries_into_box": int_or_zero(row, "carries_into_box"),
            "passes_into_box": int_or_zero(row, "passes_into_box"),
            "touches_in_box": int_or_zero(row, "carries_into_box") + int_or_zero(row, "passes_into_box"),
            "touches": int_or_zero(row, "touches"),
            "tackles": int_or_zero(row, "tackles"),
            "interceptions": int_or_zero(row, "interceptions"),
            "blocks": int_or_zero(row, "blocks"),
            "clearances": int_or_zero(row, "clearances"),
            "recoveries": int_or_zero(row, "possession_won"),
            "saves": int_or_zero(row, "saves"),
            "save_pct": number_or_none(row, "save_percentage"),
            "goals_conceded_per90": number_or_none(row, "goals_conceded_per90"),
            "clean_sheets": int_or_zero(row, "clean_sheets"),
            "sweeper_actions": int_or_zero(row, "sweeper_actions"),
            "pass_pct": number_or_none(row, "pass_pct"),
            "distribution_pct": number_or_none(row, "pass_pct"),
            "psxg_prevented": number_or_none(row, "goals_prevented"),
            "aerial_win_pct": number_or_none(row, "aerial_win_pct"),
            "aerial_wins": int_or_zero(row, "aerial_wins"),
            "minutes": int(round(minutes)),
        })

    if export_format.lower() == "csv":
        output_path = exports_dir / "players.csv"
        pd.DataFrame(players).to_csv(output_path, index=False)
    else:
        output_path = exports_dir / "players.json"
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(players, handle, indent=2, ensure_ascii=False)

    print(f"Exported {len(players)} players to {output_path}.")


def main():
    parser = argparse.ArgumentParser(description="Export final IoG player dataset for Galactico11")
    parser.add_argument("--processed-data", type=Path, default=DEFAULT_PROCESSED_DIR, help="Processed data root directory")
    parser.add_argument("--exports", type=Path, default=DEFAULT_EXPORTS_DIR, help="Export output directory")
    parser.add_argument("--export-format", choices=["json", "csv"], default="json", help="Final export format")
    args = parser.parse_args()

    export_players(processed_data_dir=args.processed_data, exports_dir=args.exports, export_format=args.export_format)


if __name__ == "__main__":
    main()
