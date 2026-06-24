import argparse
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
DEFAULT_RAW_DIR = ROOT_DIR / "data" / "manual" / "worldcup_2026" / "raw"
REQUESTED_RAW_DIR = ROOT_DIR / "src" / "data" / "worldcup"
ALT_RAW_DIR = ROOT_DIR / "src" / "data" / "manual" / "worldcup_2026" / "raw"
DEFAULT_OUTPUT_PATH = ROOT_DIR / "data" / "manual" / "worldcup_2026" / "worldcup_2026_players.json"
DEFAULT_SRC_OUTPUT_PATH = ROOT_DIR / "src" / "data" / "worldcup_2026_players.json"

SECTION_NAMES = {
    "roster",
    "standard stats",
    "goalkeeping",
    "shooting",
    "playing time",
    "miscellaneous stats",
    "player summary",
    "goalkeeper summary",
}

COUNTRY_CODES = {
    "argentina": "arg",
    "australia": "aus",
    "belgium": "bel",
    "brazil": "bra",
    "canada": "can",
    "croatia": "cro",
    "denmark": "den",
    "england": "eng",
    "france": "fra",
    "germany": "ger",
    "italy": "ita",
    "japan": "jpn",
    "mexico": "mex",
    "morocco": "mar",
    "netherlands": "ned",
    "portugal": "por",
    "senegal": "sen",
    "spain": "esp",
    "united states": "usa",
    "usa": "usa",
    "uruguay": "uru",
}

OUTPUT_FIELDS = [
    "id",
    "name",
    "nation",
    "club",
    "league",
    "competition",
    "era",
    "positions",
    "rawPosition",
    "age",
    "minutes",
    "appearances",
    "starts",
    "goals",
    "assists",
    "shots",
    "shotsOnTarget",
    "shotsOnTargetPct",
    "yellowCards",
    "redCards",
    "interceptions",
    "tacklesWon",
    "crosses",
    "saves",
    "savePct",
    "cleanSheets",
    "goalsAgainst",
    "goalsAgainstPer90",
    "iog",
    "dataSource",
    "sourceFile",
]

PLAYER_POSITION_OVERRIDES = {
    "martin odegaard": ["CAM", "CM"],
    "martin ødegaard": ["CAM", "CM"],
    "martin degaard": ["CAM", "CM"],
    "arda guler": ["CAM", "RW"],
    "arda güler": ["CAM", "RW"],
    "jamal musiala": ["CAM", "LW"],
    "phil foden": ["CAM", "RW", "LW"],
    "jude bellingham": ["CM", "CAM"],
    "rodri": ["CDM", "CM"],
    "declan rice": ["CDM", "CM"],
    "joshua kimmich": ["RB", "CDM", "CM"],
    "denzel dumfries": ["RB", "RWB"],
    "trent alexander arnold": ["RB", "CM"],
    "trent alexander-arnold": ["RB", "CM"],
    "joao cancelo": ["RB", "LB", "RWB", "LWB"],
    "joão cancelo": ["RB", "LB", "RWB", "LWB"],
    "achraf hakimi": ["RB", "RWB"],
    "theo hernandez": ["LB", "LWB"],
    "theo hérnandez": ["LB", "LWB"],
    "alphonso davies": ["LB", "LWB"],
    "bukayo saka": ["RW", "RM"],
    "lamine yamal": ["RW"],
    "kylian mbappe": ["ST", "LW"],
    "kylian mbappé": ["ST", "LW"],
    "lionel messi": ["RW", "CAM", "ST"],
    "cristiano ronaldo": ["ST"],
    "harry kane": ["ST"],
    "erling haaland": ["ST"],
    "neymar": ["LW", "CAM"],
    "mohamed salah": ["RW"],
    "vinicius junior": ["LW"],
    "vinícius júnior": ["LW"],
}

COLUMN_ALIASES = {
    "player": "name",
    "name": "name",
    "nation": "nation",
    "pos": "raw_positions",
    "position": "raw_positions",
    "age": "age",
    "mp": "appearances",
    "apps": "appearances",
    "starts": "starts",
    "start": "starts",
    "min": "minutes",
    "minutes": "minutes",
    "gls": "goals",
    "goals": "goals",
    "ast": "assists",
    "assists": "assists",
    "sh": "shots",
    "shots": "shots",
    "sot": "shotsOnTarget",
    "shotsontarget": "shotsOnTarget",
    "sot%": "shotsOnTargetPct",
    "shotsontarget%": "shotsOnTargetPct",
    "crdy": "yellowCards",
    "yc": "yellowCards",
    "yellowcards": "yellowCards",
    "crdr": "redCards",
    "rc": "redCards",
    "redcards": "redCards",
    "int": "interceptions",
    "interceptions": "interceptions",
    "tklw": "tacklesWon",
    "tackleswon": "tacklesWon",
    "crs": "crosses",
    "crosses": "crosses",
    "saves": "saves",
    "save": "saves",
    "save%": "savePct",
    "savepct": "savePct",
    "cs": "cleanSheets",
    "cleansheets": "cleanSheets",
    "ga": "goalsAgainst",
    "goalsagainst": "goalsAgainst",
    "ga90": "goalsAgainstPer90",
    "ga/90": "goalsAgainstPer90",
    "goalsagainstper90": "goalsAgainstPer90",
}

NUMERIC_FIELDS = {
    "age",
    "minutes",
    "appearances",
    "starts",
    "goals",
    "assists",
    "shots",
    "shotsOnTarget",
    "shotsOnTargetPct",
    "yellowCards",
    "redCards",
    "interceptions",
    "tacklesWon",
    "crosses",
    "saves",
    "savePct",
    "cleanSheets",
    "goalsAgainst",
    "goalsAgainstPer90",
}


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value))
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def repair_mojibake(value: str) -> str:
    try:
        return value.encode("latin1").decode("utf-8")
    except UnicodeError:
        return value


def slugify(value: str) -> str:
    value = normalize_text(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def normalized_player_key(name: str) -> str:
    value = normalize_text(name or "").lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def team_from_path(path: Path) -> str:
    return path.stem.replace("_", " ").replace("-", " ").title()


def team_from_roster_header(text: str):
    for line in text.splitlines():
        match = re.match(r"^\s*Roster\s+2026\s+(.+?):\s*World Cup\b", line, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def country_code(team: str) -> str:
    key = team.lower()
    return COUNTRY_CODES.get(key, slugify(team)[:3] or "wc")


def clean_header(value: str) -> str:
    value = normalize_text(value).strip().lower()
    value = value.replace(" ", "").replace("-", "").replace("/", "/")
    return value


def split_row(line: str) -> list[str]:
    line = line.strip()
    if "\t" in line:
        return [part.strip() for part in line.split("\t")]
    return [part.strip() for part in re.split(r"\s{2,}", line) if part.strip()]


def parse_number(value: str):
    if value is None:
        return None
    value = str(value).strip()
    if value == "" or value.lower() in {"na", "n/a", "nan", "-"}:
        return None
    age_match = re.match(r"^(\d+)-\d+$", value)
    if age_match:
        return int(age_match.group(1))
    value = value.replace(",", "").replace("%", "")
    try:
        number = float(value)
    except ValueError:
        return None
    if math.isnan(number):
        return None
    return int(number) if number.is_integer() else round(number, 2)


def merge_value(existing, incoming):
    if existing is not None:
        return existing
    return incoming


def apply_position_override(player: dict):
    override = PLAYER_POSITION_OVERRIDES.get(normalized_player_key(player.get("name", "")))
    if override:
        player["positions"] = override[:]


def normalize_positions(raw):
    if not raw:
        return []

    text = normalize_text(str(raw)).upper()
    compact = text.replace(" ", "")
    tags = [tag for tag in re.split(r"[,/;+\-]+", compact) if tag]
    tag_set = set(tags)
    is_left = any(token in text for token in ["LEFT", " L ", "-L", "_L", "LW", "LM", "LB", "LWB"])
    is_right = any(token in text for token in ["RIGHT", " R ", "-R", "_R", "RW", "RM", "RB", "RWB"])
    is_central = any(token in text for token in ["CENTRAL", "CENTRE", "CENTER", " CF", " ST", "CAM", "AM"])

    if tag_set == {"DF", "MF"}:
        if is_right:
            return ["RB", "RWB"]
        if is_left:
            return ["LB", "LWB"]
        return ["FB"]
    if tag_set == {"MF", "FW"} or tag_set == {"FW", "MF"}:
        if is_left:
            return ["LW", "CAM"]
        if is_right:
            return ["RW", "CAM"]
        if is_central:
            return ["ST", "CAM"]
        return ["CAM"]
    if tag_set == {"GK"}:
        return ["GK"]
    if tag_set == {"DF"}:
        return ["CB"]
    if tag_set == {"DF", "FB"}:
        if is_right:
            return ["RB"]
        if is_left:
            return ["LB"]
        return ["FB"]
    if tag_set == {"MF"}:
        return ["CM"]
    if tag_set == {"DM"}:
        return ["CDM", "CM"]
    if tag_set == {"AM"}:
        return ["CAM", "CM"]
    if tag_set == {"MF", "AM"}:
        return ["CM", "CAM"]
    if tag_set == {"FW"}:
        if is_left:
            return ["LW"]
        if is_right:
            return ["RW"]
        return ["ST"]
    mapped = []
    for tag in tags:
        if tag == "GK":
            mapped.append("GK")
        elif tag == "DF":
            mapped.append("CB")
        elif tag == "MF":
            mapped.append("CM")
        elif tag == "DM":
            mapped.extend(["CDM", "CM"])
        elif tag == "AM":
            mapped.extend(["CAM", "CM"])
        elif tag == "FW":
            mapped.append("ST")
        elif tag in {"FB", "CB", "LB", "RB", "LWB", "RWB", "CDM", "CM", "CAM", "LM", "RM", "LW", "RW", "ST"}:
            mapped.append(tag)

    return list(dict.fromkeys(mapped)) or ["CM"]


def normalize_career_positions(raw: str, section: str) -> list[str]:
    text = normalize_text(raw or "").upper()
    text = text.replace("POSITION:", "").split("▪")[0].strip()

    is_left = any(token in text for token in ["LEFT", " L ", "-L", "LW", "LM", "LB", "LWB"])
    is_right = any(token in text for token in ["RIGHT", " R ", "-R", "RW", "RM", "RB", "RWB"])
    is_central = any(token in text for token in ["CENTRAL", "CENTRE", "CENTER", " CF", " ST", "STRIKER"])

    if section == "Goalkeepers" or "GK" in text:
        return ["GK"]
    if section == "Defenders":
        if ("MF" in text or "MIDFIELD" in text or "DM" in text) and is_right:
            return ["RB", "RWB"]
        if ("MF" in text or "MIDFIELD" in text or "DM" in text) and is_left:
            return ["LB", "LWB"]
        if "FB" in text or "LEFT" in text or "RIGHT" in text:
            if is_right:
                return ["RB"]
            if is_left:
                return ["LB"]
            return ["FB"]
        return ["CB"]
    if section == "Midfielders":
        if "DM" in text:
            return ["CDM", "CM"]
        if "AM" in text:
            return ["CAM", "CM"]
        return ["CM"]
    if section == "Forwards":
        if ("MF" in text or "AM" in text) and is_left:
            return ["LW", "CAM"]
        if ("MF" in text or "AM" in text) and is_right:
            return ["RW", "CAM"]
        if "MF" in text or "AM" in text:
            return ["ST", "CAM"] if is_central else ["CAM"]
        if is_left:
            return ["LW"]
        if is_right:
            return ["RW"]
        return ["ST"]

    return normalize_positions(text)


def role_for_positions(positions):
    positions = positions or []
    if "GK" in positions:
        return "GK"
    if any(pos in positions for pos in ["LW", "RW", "LM", "RM"]):
        return "Winger"
    if "ST" in positions:
        return "ST"
    if "CAM" in positions:
        return "CAM"
    if "CDM" in positions:
        return "CDM"
    if "CM" in positions:
        return "CM"
    if "FB" in positions or any(pos in positions for pos in ["LB", "RB", "LWB", "RWB"]):
        return "FB"
    if "CB" in positions:
        return "CB"
    return "CM"


def split_sections(text: str) -> dict[str, list[str]]:
    sections = defaultdict(list)
    current = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        normalized = normalize_text(line).lower()

        if (
            normalized.startswith("2026 competitions")
            or normalized.startswith("2026 match log types")
            or normalized.startswith("scores & fixtures")
            or normalized.startswith("group stage")
            or normalized.startswith("includes all matches")
            or normalized.startswith("become a stathead")
            or re.match(r"^rk\s+squad\b", normalized)
        ):
            current = None
            continue

        roster_match = re.match(r"^roster\s+2026\s+.+?:\s*world cup\b", normalized)
        if roster_match:
            current = "roster"
            continue

        section_match = re.match(
            r"^(standard stats|goalkeeping|shooting|playing time|miscellaneous stats|player summary|goalkeeper summary)\s+2026\b",
            normalized,
        )
        if section_match:
            current = section_match.group(1)
            continue

        if normalized in SECTION_NAMES:
            current = normalized
            continue

        if line and current:
            sections[current].append(raw_line.rstrip())

    return sections


def is_footer_or_total(parts: list[str]) -> bool:
    lowered = " ".join(parts).lower()
    return any(marker in lowered for marker in ["squad total", "team total", "opponent total", "players"])


def parse_section(lines: list[str]) -> list[dict]:
    records = []
    headers = None

    for line in lines:
        parts = split_row(line)
        if not parts:
            continue

        lower_parts = [part.lower().strip() for part in parts]
        if "player" in lower_parts:
            headers = parts
            continue

        if headers is None or len(parts) < 2 or is_footer_or_total(parts):
            continue

        if len(parts) < len(headers):
            parts = parts + [""] * (len(headers) - len(parts))
        elif len(parts) > len(headers):
            parts = parts[: len(headers) - 1] + [" ".join(parts[len(headers) - 1 :])]

        row = {}
        for header, value in zip(headers, parts):
            key = COLUMN_ALIASES.get(clean_header(header))
            if not key:
                continue
            if key in row:
                continue
            row[key] = value.strip()

        if row.get("name"):
            records.append(row)

    return records


def empty_player(name: str, team: str) -> dict:
    player = {field: None for field in OUTPUT_FIELDS}
    player.update(
        {
            "name": name,
            "nation": team,
            "club": team,
            "league": "World Cup",
            "competition": "World Cup",
            "era": "2020s",
            "positions": [],
            "dataSource": "manual_worldcup_2026",
        }
    )
    return player


def merge_record(player: dict, record: dict):
    if record.get("nation") and player.get("nation") in {None, ""}:
        player["nation"] = record["nation"]

    if record.get("raw_positions"):
        player["rawPosition"] = merge_value(player.get("rawPosition"), record["raw_positions"])
        if not player["positions"]:
            player["positions"] = normalize_positions(record["raw_positions"])

    for field in NUMERIC_FIELDS:
        if field in record:
            player[field] = merge_value(player.get(field), parse_number(record[field]))


def raw_score(player: dict, role: str) -> float:
    def n(field):
        return float(player.get(field) or 0)

    if role == "GK":
        return n("savePct") * 0.6 + n("saves") * 0.8 + n("cleanSheets") * 4 - n("goalsAgainstPer90") * 3
    if role == "DEF":
        return n("interceptions") * 1.8 + n("tacklesWon") * 1.7 + n("crosses") * 0.5 + n("assists") * 2.5 + n("goals") * 3
    if role == "MID":
        return n("assists") * 3 + n("goals") * 2.5 + n("crosses") * 0.7 + n("tacklesWon") * 1.1 + n("interceptions") * 1.1
    return n("goals") * 5 + n("assists") * 3.5 + n("shotsOnTarget") * 1.5 + n("shots") * 0.4 + n("crosses") * 0.2


ELITE_FOOTBALL_NATIONS = {
    "Argentina",
    "Belgium",
    "Brazil",
    "Croatia",
    "England",
    "France",
    "Germany",
    "Italy",
    "Netherlands",
    "Portugal",
    "Spain",
    "Uruguay",
}

STRONG_FOOTBALL_NATIONS = {
    "Austria",
    "Colombia",
    "Czech Republic",
    "Denmark",
    "Ecuador",
    "Ghana",
    "Japan",
    "Mexico",
    "Morocco",
    "Norway",
    "Poland",
    "Senegal",
    "Serbia",
    "Sweden",
    "Turkey",
    "United States",
    "USA",
}

WEAKER_FOOTBALL_NATIONS = {
    "Algeria",
    "Congo Dr",
    "Congo DR",
    "Iran",
    "Qatar",
    "Tunisia",
}


def league_strength_multiplier(player: dict) -> float:
    """Career snippets do not preserve domestic leagues, so use nation strength as a conservative fallback."""
    nation = player.get("nation") or player.get("club") or ""
    if nation in ELITE_FOOTBALL_NATIONS:
        return 1.0
    if nation in STRONG_FOOTBALL_NATIONS:
        return 0.97
    if nation in WEAKER_FOOTBALL_NATIONS:
        return 0.78
    return 0.86


def career_raw_score(player: dict, role: str) -> float:
    minutes = float(player.get("minutes") or 0)
    nineties = max(minutes / 90, 1)
    appearances = float(player.get("appearances") or 0)
    goals = float(player.get("goals") or 0)
    assists = float(player.get("assists") or 0)
    goals_against = float(player.get("goalsAgainst") or 0)
    clean_sheets = float(player.get("cleanSheets") or 0)

    experience = min(math.log1p(max(minutes, appearances * 45)) * 1.25, 15)
    sample_confidence = min(1.0, math.sqrt(nineties / 120))
    strength = league_strength_multiplier(player)
    scoring = (goals / nineties) * sample_confidence
    creation = (assists / nineties) * sample_confidence
    keeping_clean_rate = (clean_sheets / nineties) * sample_confidence
    keeping_ga_rate = (goals_against / nineties) * sample_confidence

    if role == "GK":
        performance = keeping_clean_rate * 34 - keeping_ga_rate * 16
        return experience + performance * strength
    elif role == "CB":
        performance = scoring * 8 + creation * 7 + min(math.sqrt(nineties) * 0.75, 14)
    elif role == "FB":
        performance = scoring * 9 + creation * 18 + min(math.sqrt(nineties) * 0.55, 10)
    elif role == "CDM":
        performance = scoring * 9 + creation * 12 + min(math.sqrt(nineties) * 0.9, 16)
    elif role == "CM":
        performance = scoring * 17 + creation * 23
    elif role == "CAM":
        performance = scoring * 27 + creation * 31
    elif role == "Winger":
        performance = scoring * 35 + creation * 27
    elif role == "ST":
        performance = scoring * 42 + creation * 17
    else:
        performance = scoring * 20 + creation * 20

    return experience + performance * strength


def assign_iog(players: list[dict]):
    grouped = defaultdict(list)

    for player in players:
        if not player["positions"]:
            player["positions"] = ["CM"]
        role = role_for_positions(player["positions"])
        grouped[role].append((player, career_raw_score(player, role)))

    for role, rows in grouped.items():
        sorted_rows = sorted(rows, key=lambda item: item[1])
        total = len(sorted_rows)

        for rank, (player, _score) in enumerate(sorted_rows, start=1):
            if total == 1:
                percentile = 1.0
            else:
                percentile = (rank - 1) / (total - 1)
            player["positionRole"] = role
            player["leagueStrength"] = league_strength_multiplier(player)
            player["iog"] = round(50 + percentile * 49 * player["leagueStrength"], 1)


def print_iog_debug(players: list[dict]):
    def safe(value) -> str:
        return str(value).encode("ascii", errors="backslashreplace").decode("ascii")

    print("Top 20 IoG players:")
    for index, player in enumerate(sorted(players, key=lambda item: item.get("iog") or 0, reverse=True)[:20], start=1):
        print(
            f"  {index}. {safe(player['name'])} ({safe(player['nation'])}, {player.get('positionRole')}) "
            f"IoG {player.get('iog')} strength {player.get('leagueStrength')}"
        )

    suspicious = [
        player for player in players
        if (player.get("iog") or 0) >= 90 and league_strength_multiplier(player) < 0.9
    ]
    print("Suspicious high-IoG weaker-league/nation players:")
    if not suspicious:
        print("  none")
        return

    for player in sorted(suspicious, key=lambda item: item.get("iog") or 0, reverse=True)[:25]:
        print(
            f"  {safe(player['name'])} ({safe(player['nation'])}, {player.get('positionRole')}) "
            f"IoG {player.get('iog')} strength {player.get('leagueStrength')}"
        )


def print_position_mapping_debug(players: list[dict]):
    def safe(value) -> str:
        return str(value).encode("ascii", errors="backslashreplace").decode("ascii")

    suspicious = []
    for player in players:
        if PLAYER_POSITION_OVERRIDES.get(normalized_player_key(player.get("name", ""))):
            continue

        positions = player.get("positions") or []
        raw = player.get("rawPosition") or ""
        normalized_raw = normalize_text(str(raw)).upper()
        reason = None

        if len(positions) >= 4:
            reason = "4+ normalized positions"
        elif "ST" in positions and any(token in normalized_raw for token in ["MF", "MIDFIELD", "CM", "DM"]):
            reason = "midfielder mapped to ST"
        elif "ST" in positions and any(pos in positions for pos in ["FB", "RB", "LB", "RWB", "LWB"]):
            reason = "fullback mapped to striker"
        elif "GK" in positions and any(pos != "GK" for pos in positions):
            reason = "GK with outfield positions"

        if reason:
            suspicious.append((reason, player))

    print("Suspicious position mappings:")
    if not suspicious:
        print("  none")
        return

    for reason, player in suspicious:
        print(
            f"  {reason}: {safe(player.get('name'))} | raw={safe(player.get('rawPosition'))} "
            f"| normalized={player.get('positions')} | source={safe(player.get('sourceFile'))}"
        )


CAREER_SECTIONS = {"Goalkeepers", "Defenders", "Midfielders", "Forwards"}


def parse_totals_numbers(line: str) -> list:
    values = []
    for value in split_row(line):
        parsed = parse_number(value)
        if parsed is not None:
            values.append(parsed)
    return values


def is_player_name_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    lowered = stripped.lower()
    if lowered in {"wikipedia", "domestic leagues", "season", "see player's complete stats"}:
        return False
    if lowered.startswith("international cup statistics") or lowered.startswith("totals may not be complete"):
        return False
    if "headshot" in lowered or lowered.startswith("position:") or lowered.startswith("age:") or lowered.startswith("born:"):
        return False
    if "\t" in stripped or stripped.startswith("Note:"):
        return False
    return bool(re.search(r"[A-Za-zÀ-ÿ]", stripped))


def parse_career_players(text: str, team: str) -> tuple[list[dict], dict]:
    lines = [repair_mojibake(line.rstrip()) for line in text.splitlines()]
    players = []
    section = None
    block = []
    section_counts = Counter()

    def flush_block():
        if not section or not block:
            return

        position_index = next((idx for idx, line in enumerate(block) if line.strip().lower().startswith("position:")), None)
        totals_line = next((line for line in block if re.match(r"^\d+\s+Seasons\*", line.strip())), None)
        if position_index is None or totals_line is None:
            return

        name = None
        for candidate in block[:position_index]:
            if is_player_name_line(candidate):
                name = candidate.strip()
                break
        if not name:
            return

        age_line = next((line for line in block if line.strip().lower().startswith("age:")), "")
        age_match = re.search(r"Age:\s*(\d+)", age_line)
        age = int(age_match.group(1)) if age_match else None
        raw_position = block[position_index]
        positions = normalize_career_positions(raw_position, section)
        totals = parse_totals_numbers(totals_line)
        final = totals[-4:] if len(totals) >= 4 else []
        if len(final) < 4:
            return

        player = empty_player(name, team)
        player["competition"] = "World Cup"
        player["league"] = "Mexico League"
        player["positions"] = positions
        player["rawPosition"] = raw_position
        player["age"] = age
        player["appearances"] = final[0]
        player["minutes"] = final[1]

        if "GK" in positions:
            player["goalsAgainst"] = final[2]
            player["cleanSheets"] = final[3]
            player["goalsAgainstPer90"] = round(final[2] / max(final[1] / 90, 1), 2) if final[1] else None
            player["goals"] = None
            player["assists"] = None
        else:
            player["goals"] = final[2]
            player["assists"] = final[3]

        section_counts[section] += 1
        players.append(player)

    for line in lines:
        stripped = line.strip()
        if stripped in CAREER_SECTIONS:
            flush_block()
            section = stripped
            block = []
            continue
        if section:
            if stripped in CAREER_SECTIONS:
                flush_block()
                section = stripped
                block = []
            else:
                block.append(line)
                if re.match(r"^\d+\s+Seasons\*", stripped):
                    flush_block()
                    block = []

    flush_block()

    debug = {
        "career_sections": dict(section_counts),
        "goalkeepers": section_counts["Goalkeepers"],
        "defenders": section_counts["Defenders"],
        "midfielders": section_counts["Midfielders"],
        "forwards": section_counts["Forwards"],
        "career_players": len(players),
    }
    return players, debug


def parse_team_file(path: Path) -> tuple[list[dict], dict]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    team = team_from_roster_header(text) or team_from_path(path)
    players_by_name = {}
    career_players, career_debug = parse_career_players(text, team)

    if career_players:
        prefix = country_code(team)
        for player in career_players:
            apply_position_override(player)
            player["id"] = f"{prefix}-2026-{slugify(player['name'])}"
            player["nation"] = team
            player["club"] = team
            player["league"] = "World Cup"
            player["competition"] = "World Cup"
            player["era"] = "2020s"
            player["dataSource"] = "manual_worldcup_2026"
            player["sourceFile"] = path.name

        debug = {
            "path": str(path),
            "team": team,
            "section_counts": {
                "Roster section": 0,
                "Standard Stats section": 0,
                "Goalkeeping section": career_debug["goalkeepers"],
                "Shooting section": 0,
                "Playing Time section": 0,
                "Miscellaneous Stats section": 0,
                "Player Summary section": 0,
                "Goalkeeper Summary section": 0,
                "Career Goalkeepers": career_debug["goalkeepers"],
                "Career Defenders": career_debug["defenders"],
                "Career Midfielders": career_debug["midfielders"],
                "Career Forwards": career_debug["forwards"],
            },
            "roster_players": 0,
            "standard_players": 0,
            "goalkeepers": career_debug["goalkeepers"],
            "final_players": len(career_players),
            "parser": "career_snippet",
        }

        return career_players, debug

    section_counts = {
        "Roster section": 0,
        "Standard Stats section": 0,
        "Goalkeeping section": 0,
        "Shooting section": 0,
        "Playing Time section": 0,
        "Miscellaneous Stats section": 0,
        "Player Summary section": 0,
        "Goalkeeper Summary section": 0,
    }
    section_labels = {
        "roster": "Roster section",
        "standard stats": "Standard Stats section",
        "goalkeeping": "Goalkeeping section",
        "shooting": "Shooting section",
        "playing time": "Playing Time section",
        "miscellaneous stats": "Miscellaneous Stats section",
        "player summary": "Player Summary section",
        "goalkeeper summary": "Goalkeeper Summary section",
    }

    for section_name, lines in split_sections(text).items():
        if section_name not in SECTION_NAMES:
            continue

        records = parse_section(lines)
        section_counts[section_labels[section_name]] = len(records)

        for record in records:
            name = record["name"]
            players_by_name.setdefault(name, empty_player(name, team))
            merge_record(players_by_name[name], record)

    prefix = country_code(team)
    players = list(players_by_name.values())

    for player in players:
        apply_position_override(player)
        player["id"] = f"{prefix}-2026-{slugify(player['name'])}"
        player["nation"] = team
        player["club"] = team
        player["league"] = "World Cup"
        player["competition"] = "World Cup"
        player["era"] = "2020s"
        player["dataSource"] = "manual_worldcup_2026"
        player["sourceFile"] = path.name

    debug = {
        "path": str(path),
        "team": team,
        "section_counts": section_counts,
        "roster_players": section_counts["Roster section"],
        "standard_players": section_counts["Standard Stats section"],
        "goalkeepers": sum(1 for player in players if "GK" in player["positions"]),
        "final_players": len(players),
        "parser": "team_tables",
    }

    return players, debug


def build_report(players: list[dict]) -> dict:
    per_team = Counter(player["nation"] for player in players)
    role_counts = Counter(role_for_positions(player["positions"]) for player in players)
    missing = {
        field: sum(1 for player in players if player.get(field) is None)
        for field in OUTPUT_FIELDS
        if field not in {"id", "name", "nation", "club", "league", "competition", "era", "positions", "dataSource"}
    }

    return {
        "teams_imported": len(per_team),
        "total_players": len(players),
        "players_per_team": dict(sorted(per_team.items())),
        "role_counts": dict(sorted(role_counts.items())),
        "missing_stat_counts": missing,
    }


def import_worldcup_2026(raw_dir: Path, output_path: Path, src_output_path: Path):
    raw_dir.mkdir(parents=True, exist_ok=True)
    REQUESTED_RAW_DIR.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    src_output_path.parent.mkdir(parents=True, exist_ok=True)

    raw_paths = sorted(raw_dir.glob("*.txt"))
    if not raw_paths and raw_dir == DEFAULT_RAW_DIR:
        for fallback_dir in [REQUESTED_RAW_DIR, ALT_RAW_DIR]:
            if not fallback_dir.exists():
                continue
            fallback_paths = sorted(fallback_dir.glob("*.txt"))
            if fallback_paths:
                print(f"No .txt files found in default raw folder: {raw_dir}")
                print(f"Using fallback raw folder: {fallback_dir}")
                raw_dir = fallback_dir
                raw_paths = fallback_paths
                break

    print("FBref .txt files found:")
    if raw_paths:
        for path in raw_paths:
            print(f"  {path}")
    else:
        print("  none")

    players = []
    debug_reports = []
    for path in raw_paths:
        print(f"Parsing file: {path}")
        team_players, debug = parse_team_file(path)
        debug_reports.append(debug)
        players.extend(team_players)

        print(f"Detected team name: {debug['team']}")
        print(f"Parser: {debug['parser']}")
        for label, count in debug["section_counts"].items():
            print(f"  {label}: {count}")
        print(f"{debug['team']}:")
        print(f"Roster Players: {debug['roster_players']}")
        print(f"Standard Players: {debug['standard_players']}")
        print(f"Goalkeepers: {debug['goalkeepers']}")
        print(f"Final Players: {debug['final_players']}")

        if debug["final_players"] == 0:
            print("Debugging report:")
            print(f"  File path: {debug['path']}")
            print(f"  Team name detected: {debug['team']}")
            print("  No player records were generated from any parsed section.")
            print("  Check that the file contains a roster header like 'Roster 2026 Mexico: World Cup'.")
            print("  Check that player tables include a header row with a 'Player' column.")
            raise RuntimeError(f"No players generated from {path}")

    if not players:
        print("Debugging report:")
        print(f"  Raw folder checked: {raw_dir}")
        print("  No .txt files were found, so no player rows could be parsed.")
        print("  Place pasted FBref files such as mexico.txt in data/manual/worldcup_2026/raw/.")
        print(f"  Fallback folder also supported: {ALT_RAW_DIR}")
        raise RuntimeError("No World Cup 2026 player files found. Import aborted.")

    assign_iog(players)
    players.sort(key=lambda player: (player["nation"], player["name"]))

    for path in [output_path, src_output_path]:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(players, handle, indent=2, ensure_ascii=False)
            handle.write("\n")

    report = build_report(players)
    print("World Cup 2026 FBref manual import report")
    print(f"teams imported: {report['teams_imported']}")
    print(f"players imported: {report['total_players']}")
    print(f"total players: {report['total_players']}")
    print("players per team:")
    for team, count in report["players_per_team"].items():
        print(f"  {team}: {count}")
    print("role counts:")
    for role, count in report["role_counts"].items():
        print(f"  {role}: {count}")
    print("missing stat counts:")
    for field, count in report["missing_stat_counts"].items():
        print(f"  {field}: {count}")
    print_position_mapping_debug(players)
    print_iog_debug(players)
    print(f"wrote: {output_path}")
    print(f"wrote: {src_output_path}")

    return players, report


def main():
    parser = argparse.ArgumentParser(description="Import pasted FBref World Cup 2026 team text into Galactico11 JSON")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR, help="Folder of pasted FBref team .txt files")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Manual data JSON output path")
    parser.add_argument("--src-output", type=Path, default=DEFAULT_SRC_OUTPUT_PATH, help="App data JSON output path")
    args = parser.parse_args()

    import_worldcup_2026(args.raw_dir, args.output, args.src_output)


if __name__ == "__main__":
    main()
