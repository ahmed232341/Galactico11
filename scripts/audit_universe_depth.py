import argparse
import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PLAYERS_PATH = BASE_DIR.parent / "src" / "data" / "players.json"
DEFAULT_OUTPUT_PATH = BASE_DIR.parent / "data" / "processed" / "universe_audit.csv"


def audit_universe_depth(players_path: Path, output_path: Path) -> pd.DataFrame:
    with players_path.open("r", encoding="utf-8") as handle:
        players = json.load(handle)

    df = pd.DataFrame(players)
    if df.empty:
        raise RuntimeError(f"No players found in {players_path}")

    required = {"league", "club", "era"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing player fields for universe audit: {sorted(missing)}")

    audit = (
        df.groupby(["league", "club", "era"], dropna=False)
        .size()
        .reset_index(name="player_count")
        .sort_values(["player_count", "league", "club", "era"], ascending=[True, True, True, True])
    )
    audit["needs_player_pack"] = audit["player_count"] < 22

    output_path.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(output_path, index=False)

    print(f"Wrote {output_path} rows={len(audit)}")
    print(f"Universes below 22 players: {int(audit['needs_player_pack'].sum())}")
    return audit


def main():
    parser = argparse.ArgumentParser(description="Audit Galactico11 universe player depth")
    parser.add_argument("--players", type=Path, default=DEFAULT_PLAYERS_PATH, help="Exported players.json path")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Universe audit CSV path")
    args = parser.parse_args()

    audit_universe_depth(args.players, args.output)


if __name__ == "__main__":
    main()
