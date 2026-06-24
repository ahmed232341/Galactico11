import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_OUTPUT = ROOT_DIR / "data" / "manual" / "club_mode" / "raw" / "club.txt"
MANUAL_JSON_OUTPUT = ROOT_DIR / "data" / "manual" / "club_mode" / "club_players.json"
SRC_JSON_OUTPUT = ROOT_DIR / "src" / "data" / "club_players.json"

ERAS = ["2010s", "2020s"]
DATA_SOURCE = "generated_club_mode_seed"

LEAGUE_MULTIPLIERS = {
    "Premier League": 1.00,
    "La Liga": 0.98,
    "Serie A": 0.96,
    "Bundesliga": 0.95,
    "Ligue 1": 0.92,
    "Champions League": 1.00,
}

DOMESTIC_CLUBS = {
    "Premier League": [
        "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton", "Burnley",
        "Chelsea", "Crystal Palace", "Everton", "Fulham", "Leeds United", "Liverpool",
        "Manchester City", "Manchester United", "Newcastle United", "Nottingham Forest",
        "Sunderland", "Tottenham Hotspur", "West Ham United", "Wolverhampton Wanderers",
    ],
    "La Liga": [
        "Real Madrid", "Barcelona", "Atletico Madrid", "Athletic Club", "Real Sociedad",
        "Villarreal", "Valencia", "Sevilla", "Real Betis", "Celta Vigo", "Getafe",
        "Osasuna", "Mallorca", "Rayo Vallecano", "Girona", "Alaves", "Espanyol",
        "Elche", "Levante", "Oviedo",
    ],
    "Serie A": [
        "Inter", "AC Milan", "Juventus", "Napoli", "Roma", "Lazio", "Atalanta",
        "Fiorentina", "Bologna", "Torino", "Udinese", "Genoa", "Parma", "Como",
        "Cagliari", "Verona", "Lecce", "Pisa", "Sassuolo", "Cremonese",
    ],
    "Bundesliga": [
        "Bayern Munich", "Borussia Dortmund", "Bayer Leverkusen", "RB Leipzig",
        "Eintracht Frankfurt", "VfB Stuttgart", "Freiburg", "Mainz", "Werder Bremen",
        "Borussia Monchengladbach", "Union Berlin", "Wolfsburg", "Augsburg",
        "Hoffenheim", "St Pauli", "Heidenheim", "Koln", "Hamburg",
    ],
    "Ligue 1": [
        "Paris Saint-Germain", "Marseille", "Monaco", "Lille", "Lyon", "Lens", "Nice",
        "Strasbourg", "Brest", "Rennes", "Nantes", "Toulouse", "Auxerre", "Le Havre",
        "Angers", "Metz", "Lorient", "Paris FC",
    ],
}

CHAMPIONS_LEAGUE_CLUBS = [
    "Real Madrid", "Barcelona", "Atletico Madrid", "Bayern Munich", "Borussia Dortmund",
    "Bayer Leverkusen", "PSG", "Marseille", "Monaco", "Inter", "AC Milan", "Juventus",
    "Napoli", "Roma", "Arsenal", "Liverpool", "Manchester City", "Manchester United",
    "Chelsea", "Tottenham", "Newcastle United", "Aston Villa", "Benfica", "Porto",
    "Sporting CP", "Ajax", "PSV", "Feyenoord", "Club Brugge", "Celtic", "Galatasaray",
    "Shakhtar Donetsk",
]

COUNTRIES = {
    "Premier League": "England",
    "La Liga": "Spain",
    "Serie A": "Italy",
    "Bundesliga": "Germany",
    "Ligue 1": "France",
    "Champions League": "Europe",
}

SQUAD_TEMPLATE = [
    ("GK", "GK"), ("GK", "GK"), ("GK", "GK"),
    ("CB", "CB"), ("CB", "CB"), ("CB", "CB"), ("CB", "CB"),
    ("RB", "FB"), ("RB", "FB"), ("LB", "FB"), ("LB", "FB"),
    ("CDM", "CDM"), ("CDM", "CDM"), ("CM", "CM"), ("CM", "CM"), ("CM", "CM"), ("CM", "CM"),
    ("CAM", "CAM"), ("CAM", "CAM"),
    ("RW", "Winger"), ("RW", "Winger"), ("LW", "Winger"), ("LW", "Winger"),
    ("ST", "ST"), ("ST", "ST"), ("ST", "ST"),
]

ROLE_IOG_BASE = {
    "GK": 76,
    "CB": 78,
    "FB": 77,
    "CDM": 79,
    "CM": 78,
    "CAM": 80,
    "Winger": 81,
    "ST": 82,
}

FORBIDDEN_LEAGUES = {"NWSL", "WSL", "Major League Soccer", "MLS"}
FORBIDDEN_TERMS = {"Women", "WFC", "NWSL", "WSL", "MLS"}

FIELDNAMES = [
    "id", "name", "club", "league", "competition", "era", "country", "position", "roleBucket",
    "minutes", "goals", "assists", "cleanSheets", "tackles", "interceptions", "keyPasses",
    "shots", "shotsOnTarget", "savePct", "iog", "dataSource", "estimated", "modeType",
]


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value))
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def slugify(value: str) -> str:
    value = normalize_text(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def player_name(club: str, era: str, position: str, index: int) -> str:
    return f"{club} {era} {position} {index:02d}"


def estimated_iog(league: str, role: str, slot_index: int, era: str) -> int:
    league_boost = round((LEAGUE_MULTIPLIERS[league] - 0.92) * 20)
    era_boost = 1 if era == "2020s" else 0
    depth_penalty = min(slot_index // 3, 5)
    return max(50, min(99, ROLE_IOG_BASE[role] + league_boost + era_boost - depth_penalty))


def build_player(club: str, league: str, era: str, position: str, role: str, index: int) -> dict:
    name = player_name(club, era, position, index)
    mode_type = "champions_league" if league == "Champions League" else "league"
    return {
        "id": f"{slugify(club)}-{slugify(name)}",
        "name": name,
        "club": club,
        "league": league,
        "competition": league,
        "era": era,
        "country": COUNTRIES[league],
        "position": position,
        "roleBucket": role,
        "minutes": None,
        "goals": None,
        "assists": None,
        "cleanSheets": None,
        "tackles": None,
        "interceptions": None,
        "keyPasses": None,
        "shots": None,
        "shotsOnTarget": None,
        "savePct": None,
        "iog": estimated_iog(league, role, index, era),
        "dataSource": DATA_SOURCE,
        "estimated": True,
        "modeType": mode_type,
    }


def generate_players() -> list[dict]:
    players = []

    for league, clubs in DOMESTIC_CLUBS.items():
        for club in clubs:
            for era in ERAS:
                for index, (position, role) in enumerate(SQUAD_TEMPLATE, start=1):
                    players.append(build_player(club, league, era, position, role, index))

    for club in CHAMPIONS_LEAGUE_CLUBS:
        for era in ERAS:
            for index, (position, role) in enumerate(SQUAD_TEMPLATE, start=1):
                players.append(build_player(club, "Champions League", era, position, role, index))

    return players


def validate(players: list[dict]):
    if len({player["club"] for player in players}) < 50:
        raise RuntimeError("Rejected: total clubs < 50")

    forbidden_rows = [
        player for player in players
        if player["league"] in FORBIDDEN_LEAGUES or any(term.lower() in player["club"].lower() for term in FORBIDDEN_TERMS)
    ]
    if forbidden_rows:
        sample = ", ".join(row["club"] for row in forbidden_rows[:5])
        raise RuntimeError(f"Rejected: forbidden women/non-European/MLS club detected: {sample}")

    by_universe = defaultdict(list)
    for player in players:
        by_universe[(player["era"], player["club"], player["league"])].append(player)

    thin = {key: len(rows) for key, rows in by_universe.items() if len(rows) < 20}
    if thin:
        sample = next(iter(thin.items()))
        raise RuntimeError(f"Rejected: club universe has fewer than 20 players: {sample}")

    if any(player["league"] not in LEAGUE_MULTIPLIERS for player in players):
        raise RuntimeError("Rejected: unsupported league detected")


def write_raw_club_txt(players: list[dict]):
    RAW_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with RAW_OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        handle.write("# GALACTICO11 CLUB MODE GENERATED DATABASE\n")
        handle.write("# Men's club football only. Generated estimated squad shells; unavailable real stats are null.\n\n")
        handle.write("[META]\n")
        handle.write("version=2\n")
        handle.write(f"dataSource={DATA_SOURCE}\n")
        handle.write("estimated=true\n\n")
        handle.write("[LEAGUE_MULTIPLIERS]\n")
        for league, value in LEAGUE_MULTIPLIERS.items():
            handle.write(f"{league}={value:.2f}\n")
        handle.write("\n[PLAYER_ROWS_NORMALIZED_CSV]\n")
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(players)
        handle.write("[/PLAYER_ROWS_NORMALIZED_CSV]\n")


def write_json(players: list[dict]):
    for path in (MANUAL_JSON_OUTPUT, SRC_JSON_OUTPUT):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(players, handle, indent=2, ensure_ascii=False)
            handle.write("\n")


def print_report(players: list[dict]):
    clubs = Counter(player["club"] for player in players)
    universes = Counter((player["era"], player["club"], player["league"]) for player in players)
    leagues = Counter(player["league"] for player in players)
    eras = Counter(player["era"] for player in players)

    print(f"Total clubs: {len(clubs)}")
    print(f"Total club universes: {len(universes)}")
    print(f"Total players: {len(players)}")
    print("Players per league")
    for league, count in sorted(leagues.items()):
        print(f"  {league}: {count}")
    print("Players per era")
    for era, count in sorted(eras.items()):
        print(f"  {era}: {count}")
    print("Players per club")
    for club, count in sorted(clubs.items()):
        print(f"  {club}: {count}")


def main():
    raise RuntimeError(
        "Disabled: this generator created placeholder players. "
        "Club Mode must use real footballer names only."
    )


if __name__ == "__main__":
    main()
