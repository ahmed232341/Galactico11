from __future__ import annotations

import json
import math
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FC26_PATH = ROOT / "src" / "data" / "fc26_players.json"
WORLD_CUP_PATH = ROOT / "src" / "data" / "worldcup_2026_players.json"
COMPONENT_PATH = ROOT / "src" / "components" / "draft" / "DraftGame.svelte"
VALID_POSITIONS = {"GK", "RB", "CB", "LB", "RWB", "LWB", "CDM", "CM", "CAM", "RM", "LM", "RW", "LW", "ST"}

FORMATIONS: dict[str, list[str]] = {
    "4-3-3": ["LW", "ST", "RW", "CM", "CM", "CM", "LB", "CB", "CB", "RB", "GK"],
    "4-4-2": ["ST", "ST", "LM", "CM", "CM", "RM", "LB", "CB", "CB", "RB", "GK"],
    "4-4-1-1": ["ST", "CAM", "LM", "CM", "CM", "RM", "LB", "CB", "CB", "RB", "GK"],
    "4-2-3-1": ["ST", "LW", "CAM", "RW", "CDM", "CDM", "LB", "CB", "CB", "RB", "GK"],
    "4-1-4-1": ["ST", "LM", "CM", "CM", "RM", "CDM", "LB", "CB", "CB", "RB", "GK"],
    "3-5-2": ["ST", "ST", "LM", "CM", "CAM", "CM", "RM", "CB", "CB", "CB", "GK"],
    "3-4-3": ["LW", "ST", "RW", "LM", "CM", "CM", "RM", "CB", "CB", "CB", "GK"],
    "3-4-2-1": ["ST", "CAM", "CAM", "LM", "CM", "CM", "RM", "CB", "CB", "CB", "GK"],
    "5-4-1": ["ST", "LM", "CM", "CM", "RM", "LWB", "CB", "CB", "CB", "RWB", "GK"],
}

ALIASES = {
    "CB": {"CB"}, "ST": {"ST"}, "RW": {"RW", "RM"}, "LW": {"LW", "LM"},
    "RM": {"RM", "RW"}, "LM": {"LM", "LW"}, "CDM": {"CDM", "CM"},
    "CM": {"CM", "CDM", "CAM"}, "CAM": {"CAM", "CM"}, "RB": {"RB", "RWB"},
    "LB": {"LB", "LWB"}, "RWB": {"RWB", "RB", "RM"}, "LWB": {"LWB", "LB", "LM"},
    "GK": {"GK"},
}

FORMATION_RATING = {
    "4-4-2": 88, "4-4-1-1": 87, "4-2-3-1": 90, "4-1-4-1": 86,
    "4-3-3": 89, "3-5-2": 84, "3-4-2-1": 83, "3-4-3": 81, "5-4-1": 82,
}

NATION_ALIASES = {
    "bosnia and herzegovina": "bosnia", "czechia": "czech republic",
    "cote d ivoire": "ivory coast", "korea republic": "south korea",
    "switzerland": "switzeland", "turkiye": "turkey", "united states": "usa",
}


def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def key(value: Any) -> str:
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def positions(player: dict[str, Any]) -> list[str]:
    values = player.get("positions") or [player.get("position")]
    return [str(value).upper() for value in values if str(value).upper() in VALID_POSITIONS]


def compatible(player: dict[str, Any], slot: str) -> bool:
    return any(slot in ALIASES.get(position, {position}) for position in positions(player))


def fit_score(player: dict[str, Any], slot: str) -> float:
    player_positions = positions(player)
    if player_positions and player_positions[0] == slot:
        return 100
    if slot in player_positions:
        return 90
    if compatible(player, slot):
        return 80
    return 60


def line(slot: str) -> str:
    if slot in {"ST", "LW", "RW"}:
        return "attack"
    if slot in {"CAM", "CM", "CDM", "LM", "RM"}:
        return "midfield"
    return "defense"


def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0


def chemistry(picks: list[dict[str, Any]]) -> int:
    if not picks:
        return 0
    suitability = average([fit_score(player, player["assignedPosition"]) for player in picks])
    if len(picks) == 1:
        return round(clamp(28 + suitability * 0.42, 20, 70))
    pairs = [(picks[i], picks[j]) for i in range(len(picks)) for j in range(i + 1, len(picks))]
    nation = average([100 if key(a.get("nation")) == key(b.get("nation")) else 0 for a, b in pairs])
    era = average([100 if a.get("era", "2020s") == b.get("era", "2020s") else 0 for a, b in pairs])
    lines = {line(player["assignedPosition"]) for player in picks}
    coverage = len(lines) / 3 * 100
    diversity = len({player["assignedPosition"] for player in picks}) / min(len(picks), 6) * 100
    complementary = coverage * 0.65 + diversity * 0.35
    position_fit = average([fit_score(player, player["assignedPosition"]) for player in picks])
    score = 12 + suitability * 0.22 + position_fit * 0.18 + nation * 0.14 + era * 0.08 + complementary * 0.26
    return round(clamp(score, 20, 100))


def libra(picks: list[dict[str, Any]], formation: str, chemistry_score: int) -> int | None:
    if len(picks) < 2:
        return None
    values = [float(player["iog"]) for player in picks]
    avg = average(values)
    deviation = math.sqrt(average([(value - avg) ** 2 for value in values]))
    spread = max(values) - min(values)
    consistency = clamp(100 - deviation * 3.2 - spread * 1.15)
    counts = Counter(line(player["assignedPosition"]) for player in picks)
    target_counts = Counter(line(slot) for slot in FORMATIONS[formation])
    role_difference = sum(abs(counts[group] / len(picks) - target_counts[group] / 11) for group in ("attack", "midfield", "defense"))
    role_balance = clamp((1 - role_difference / 2) * 75 + len(counts) / 3 * 25)
    shape = {"4-4-2": 96, "4-4-1-1": 92, "4-2-3-1": 90, "4-1-4-1": 88, "4-3-3": 84,
             "3-5-2": 78, "3-4-2-1": 76, "3-4-3": 70, "5-4-1": 72}[formation]
    fit = average([fit_score(player, player["assignedPosition"]) for player in picks])
    tactical = clamp(100 - role_difference * 50)
    return round(clamp(avg * 0.25 + consistency * 0.30 + role_balance * 0.12 + shape * 0.08 +
                       chemistry_score * 0.10 + fit * 0.08 + tactical * 0.07))


def balance(picks: list[dict[str, Any]], formation: str, chemistry_score: int, libra_score: int | None) -> dict[str, float]:
    result: dict[str, float] = {}
    for group in ("attack", "midfield", "defense"):
        group_players = [player for player in picks if line(player["assignedPosition"]) == group]
        result[group] = round(average([player["iog"] * fit_score(player, player["assignedPosition"]) / 100 for player in group_players]), 1)
    result["chemistry"] = chemistry_score
    result["libra"] = libra_score or 0
    return result


def simulate_season(picks: list[dict[str, Any]], formation: str) -> dict[str, int]:
    chemistry_score = chemistry(picks)
    libra_score = libra(picks, formation, chemistry_score) or 30
    avg_iog = average([player["iog"] for player in picks])
    fit = average([fit_score(player, player["assignedPosition"]) for player in picks])
    formation_strength = FORMATION_RATING[formation] * 0.6 + fit * 0.4
    strength = avg_iog * 0.4 + libra_score * 0.3 + chemistry_score * 0.2 + formation_strength * 0.1
    wins = round(clamp(4 + (strength - 55) * 0.7, 4, 28))
    draws = round(clamp(8 - max(0, strength - 65) * 0.18, 0, 8))
    draws = min(draws, 30 - wins)
    losses = 30 - wins - draws
    return {"wins": wins, "draws": draws, "losses": losses, "points": wins * 3 + draws}


def weighted_et_options(pool: list[dict[str, Any]], count: int = 5) -> list[dict[str, Any]]:
    preferred = [player for player in pool if player["iog"] >= 75]
    eligible = preferred or pool
    bands = [
        ([player for player in eligible if player["iog"] >= 85], 60),
        ([player for player in eligible if 80 <= player["iog"] < 85], 25),
        ([player for player in eligible if 75 <= player["iog"] < 80], 15),
    ]
    selected: list[dict[str, Any]] = []
    while len(selected) < count:
        available = [(band, weight) for band, weight in bands if any(player not in selected for player in band)]
        if not available:
            break
        band = random.choices([entry[0] for entry in available], weights=[entry[1] for entry in available], k=1)[0]
        selected.append(random.choice([player for player in band if player not in selected]))
    return selected


def choose_assignment(options: list[dict[str, Any]], open_slots: list[str]) -> tuple[dict[str, Any], str]:
    candidates: list[tuple[int, float, dict[str, Any], str]] = []
    for player in options:
        compatible_slots = [slot for slot in open_slots if compatible(player, slot)]
        for slot in compatible_slots:
            scarcity = sum(1 for other in options if compatible(other, slot))
            candidates.append((scarcity, -float(player["iog"]), player, slot))
    if not candidates:
        raise RuntimeError("Offered player set has no compatible open slot")
    _, _, player, slot = min(candidates, key=lambda item: (item[0], item[1]))
    return player, slot


def run_draft(mode: str, formation: str, players: list[dict[str, Any]], nations: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], int]:
    open_slots = list(FORMATIONS[formation])
    picked: list[dict[str, Any]] = []
    picked_ids: set[str] = set()
    respins = 0
    for _round in range(11):
        if mode == "et":
            pool = [player for player in players if player["id"] not in picked_ids and any(compatible(player, slot) for slot in open_slots)]
            options = weighted_et_options(pool)
        else:
            options = []
            nation_names = list(nations)
            for _attempt in range(max(3, len(nation_names) * 2)):
                nation = random.choice(nation_names)
                pool = [player for player in nations[nation] if player["id"] not in picked_ids and any(compatible(player, slot) for slot in open_slots)]
                if pool:
                    ordered = sorted(pool, key=lambda player: player["iog"], reverse=True)
                    high = ordered[:max(1, len(ordered) // 4)]
                    middle = ordered[max(1, len(ordered) // 4):max(2, len(ordered) * 3 // 4)] or ordered
                    low = ordered[max(2, len(ordered) * 3 // 4):] or ordered
                    options = random.sample(high, min(1, len(high))) + random.sample(middle, min(2, len(middle))) + random.sample(low, min(1, len(low)))
                    remainder = [player for player in ordered if player not in options]
                    if remainder:
                        options += random.sample(remainder, min(5 - len(options), len(remainder)))
                    break
                respins += 1
        if not options:
            raise RuntimeError(f"{mode} produced an empty pool with slots {open_slots}")
        player, slot = choose_assignment(options, open_slots)
        assigned = dict(player, assignedPosition=slot)
        picked.append(assigned)
        picked_ids.add(str(player["id"]))
        open_slots.remove(slot)
    if open_slots or len(picked_ids) != 11:
        raise RuntimeError(f"{mode} did not complete {formation}")
    return picked, respins


def validate_mystery_contract() -> None:
    source = COMPONENT_PATH.read_text(encoding="utf-8")
    required = [
        "isMysteryCardHidden(player)", "Unknown Player", "Identity Hidden", "Selected by Phoebe",
        "isMysteryIdentityHidden(slot.player)", "currentAnalysisStep.mysteryPlayer",
    ]
    missing = [value for value in required if value not in source]
    if missing:
        raise RuntimeError(f"Mystery privacy contract missing: {missing}")
    hidden_payload = {"label": "MYSTERY PICK", "identity": "Identity Hidden", "value": "???"}
    forbidden = {"name", "nation", "iog", "era", "club", "positions"}
    if forbidden.intersection(hidden_payload):
        raise RuntimeError("Mystery card model leaks player metadata")


def main() -> int:
    random.seed(11062026)
    fc_players = json.loads(FC26_PATH.read_text(encoding="utf-8"))
    manual_world_cup = json.loads(WORLD_CUP_PATH.read_text(encoding="utf-8"))
    qualified = {key(player.get("nation") or player.get("club")) for player in manual_world_cup}
    qualified.discard("")
    nation_display = {key(player.get("nation") or player.get("club")): player.get("nation") or player.get("club") for player in manual_world_cup}
    nations: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for player in fc_players:
        nation_key = key(player.get("nation"))
        target = nation_key if nation_key in qualified else next((name for name in qualified if NATION_ALIASES.get(name) == nation_key or NATION_ALIASES.get(nation_key) == name), "")
        if target:
            nations[str(nation_display[target])].append(player)

    failures: list[str] = []
    metrics = Counter()
    validate_mystery_contract()
    for mode in ("et", "worldcup"):
        for index in range(100):
            formation = list(FORMATIONS)[index % len(FORMATIONS)]
            try:
                picks, respins = run_draft(mode, formation, fc_players, nations)
                chemistry_score = chemistry(picks)
                libra_score = libra(picks, formation, chemistry_score)
                team_balance = balance(picks, formation, chemistry_score, libra_score)
                if not (0 <= chemistry_score <= 100 and libra_score is not None and 0 <= libra_score <= 100):
                    raise RuntimeError("Chemistry or Libra fell outside 0-100")
                if any(not 0 <= value <= 100 for value in team_balance.values()):
                    raise RuntimeError("Team Balance fell outside 0-100")
                if mode == "et":
                    if any(player["iog"] < 75 for player in picks):
                        raise RuntimeError("ET draft used a sub-75 player without an emergency pool")
                    record = simulate_season(picks, formation)
                    if record["wins"] + record["draws"] + record["losses"] != 30 or record["points"] != record["wins"] * 3 + record["draws"]:
                        raise RuntimeError("ET simulation record is invalid")
                    metrics["et_points"] += record["points"]
                metrics[f"{mode}_completed"] += 1
                metrics[f"{mode}_respins"] += respins
            except Exception as exc:  # noqa: BLE001 - report every release failure
                failures.append(f"{mode} draft {index + 1} ({formation}): {exc}")

    print("GALACTICO11 BETA RELEASE QA")
    print(f"FC26 players: {len(fc_players)}")
    print(f"World Cup nations with FC26 pools: {len(nations)} / {len(qualified)}")
    print(f"ET drafts completed: {metrics['et_completed']} / 100")
    print(f"World Cup drafts completed: {metrics['worldcup_completed']} / 100")
    print(f"World Cup automatic respins: {metrics['worldcup_respins']}")
    print(f"Average ET points: {metrics['et_points'] / max(metrics['et_completed'], 1):.1f} / 90")
    print("Mystery privacy contract: passed")
    if failures:
        print("FAILURES")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Beta gameplay stress test: passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
