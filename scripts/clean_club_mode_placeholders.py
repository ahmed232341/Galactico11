import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT_DIR / "data" / "manual" / "club_mode" / "raw" / "club.txt"
MANUAL_JSON_PATH = ROOT_DIR / "data" / "manual" / "club_mode" / "club_players.json"
SRC_JSON_PATH = ROOT_DIR / "src" / "data" / "club_players.json"

PLACEHOLDER_RE = re.compile(
    r"\b(?:GK|RB|CB|LB|RWB|LWB|CDM|CM|CAM|RM|LM|RW|LW|ST)\s*\d{1,2}\b",
    re.IGNORECASE,
)

FIELDNAMES = [
    "id", "name", "club", "league", "competition", "era", "country", "position", "roleBucket",
    "minutes", "goals", "assists", "cleanSheets", "tackles", "interceptions", "keyPasses",
    "shots", "shotsOnTarget", "savePct", "iog", "dataSource", "estimated", "modeType",
]


def is_placeholder(player: dict) -> bool:
    if PLACEHOLDER_RE.search(str(player.get("name", ""))):
        return True
    if str(player.get("dataSource", "")) == "generated_club_mode_seed":
        return True
    return False


def load_players(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def write_players(path: Path, players: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(players, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def write_raw(players: list[dict]):
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RAW_PATH.open("w", encoding="utf-8", newline="") as handle:
        handle.write("# GALACTICO11 CLUB MODE REAL-PLAYER DATABASE\n")
        handle.write("# Placeholder/generated position-number players have been removed.\n")
        handle.write("# Add real footballer rows only. Do not generate fake players to fill squads.\n\n")
        handle.write("[PLAYER_ROWS_NORMALIZED_CSV]\n")
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(players)
        handle.write("[/PLAYER_ROWS_NORMALIZED_CSV]\n")


def main():
    source_players = load_players(SRC_JSON_PATH)
    manual_players = load_players(MANUAL_JSON_PATH)
    players = source_players if source_players else manual_players

    removed = [player for player in players if is_placeholder(player)]
    real_players = [player for player in players if not is_placeholder(player)]
    clubs_affected = sorted({player.get("club", "") for player in removed if player.get("club")})
    clubs_remaining = Counter(player.get("club", "") for player in real_players if player.get("club"))
    excluded_clubs = [club for club in clubs_affected if clubs_remaining.get(club, 0) == 0]

    write_players(MANUAL_JSON_PATH, real_players)
    write_players(SRC_JSON_PATH, real_players)
    write_raw(real_players)

    print(f"Total real players: {len(real_players)}")
    print(f"Total generated players removed: {len(removed)}")
    print(f"Clubs affected: {len(clubs_affected)}")
    for club in clubs_affected:
        print(f"  {club}")
    print(f"Clubs excluded from draft pool: {len(excluded_clubs)}")
    for club in excluded_clubs:
        print(f"  {club}")

    if any(is_placeholder(player) for player in real_players):
        raise RuntimeError("Placeholder cleanup failed; generated player remains.")


if __name__ == "__main__":
    main()
