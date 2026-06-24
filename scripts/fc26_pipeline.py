from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INTERMEDIATE = PROJECT_ROOT / "data" / "processed" / "fc26_players_imported.json"
DEFAULT_IMPORT_REPORT = PROJECT_ROOT / "data" / "processed" / "fc26_import_report.json"
DEFAULT_VALIDATION_REPORT = PROJECT_ROOT / "data" / "processed" / "fc26_validation_report.json"
DEFAULT_EXPORT = PROJECT_ROOT / "src" / "data" / "fc26_players.json"

VALID_POSITIONS = (
    "GK", "RB", "CB", "LB", "RWB", "LWB", "CDM", "CM", "CAM", "RM", "LM", "RW", "LW", "ST"
)

IOG_OVERRIDES = {
    "lionel messi": 90,
    "l messi": 90,
    "cristiano ronaldo": 79,
    "c ronaldo": 79,
    "hugo ekitike": 86,
    "h ekitike": 86,
}

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "source_id": ("player_id", "sofifa_id", "id", "playerid", "player_id_ea"),
    "name": ("short_name", "player_name", "name", "known_as", "display_name", "long_name", "full_name"),
    "nation": ("nationality_name", "nationality", "nation_name", "nation", "country", "country_name"),
    "club": ("club_name", "club", "team_name", "team", "squad_name"),
    "positions": ("player_positions", "positions", "position", "preferred_positions", "preferred_position", "club_position"),
    "age": ("age", "player_age"),
    "overall": ("overall", "ova", "rating", "overall_rating"),
    "potential": ("potential", "pot", "potential_rating"),
    "iog": ("iog", "impact_on_game"),
    "dob": ("dob", "date_of_birth", "birth_date"),
    "version": ("fifa_version", "game_version", "version", "season"),
    "update": ("fifa_update", "update", "update_id"),
}

POSITION_MAP = {
    "GK": "GK", "GKP": "GK", "GOALKEEPER": "GK",
    "RB": "RB", "RFB": "RB", "RIGHTBACK": "RB", "RIGHT BACK": "RB",
    "LB": "LB", "LFB": "LB", "LEFTBACK": "LB", "LEFT BACK": "LB",
    "CB": "CB", "LCB": "CB", "RCB": "CB", "SW": "CB", "DF": "CB", "DEF": "CB",
    "RWB": "RWB", "RIGHT WING BACK": "RWB", "RIGHT WINGBACK": "RWB",
    "LWB": "LWB", "LEFT WING BACK": "LWB", "LEFT WINGBACK": "LWB",
    "CDM": "CDM", "DM": "CDM", "LDM": "CDM", "RDM": "CDM", "DEFENSIVE MIDFIELDER": "CDM",
    "CM": "CM", "LCM": "CM", "RCM": "CM", "MF": "CM", "MID": "CM", "MIDFIELDER": "CM",
    "CAM": "CAM", "AM": "CAM", "LAM": "CAM", "RAM": "CAM", "ATTACKING MIDFIELDER": "CAM",
    "RM": "RM", "RIGHT MIDFIELDER": "RM", "RIGHT MID": "RM",
    "LM": "LM", "LEFT MIDFIELDER": "LM", "LEFT MID": "LM",
    "RW": "RW", "RF": "RW", "RIGHT WINGER": "RW", "RIGHT FORWARD": "RW",
    "LW": "LW", "LF": "LW", "LEFT WINGER": "LW", "LEFT FORWARD": "LW",
    "ST": "ST", "CF": "ST", "LS": "ST", "RS": "ST", "FW": "ST", "FWD": "ST", "FORWARD": "ST", "STRIKER": "ST",
}


@dataclass
class Candidate:
    player: dict[str, Any]
    dedup_key: str
    quality: tuple[int, int, int, int]


def log(message: str) -> None:
    print(f"[FC26] {message}")


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def repair_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return ""
    if any(marker in text for marker in ("Ã", "Â", "â€", "ðŸ")):
        try:
            text = text.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return " ".join(text.split())


def normalized_row(row: dict[str, Any]) -> dict[str, Any]:
    return {str(key).strip().lower(): value for key, value in row.items() if key is not None}


def first_value(row: dict[str, Any], aliases: Iterable[str]) -> Any:
    for alias in aliases:
        value = row.get(alias.lower())
        if value is not None and repair_text(value) != "":
            return value
    return None


def to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or repair_text(value) == "":
            return default
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def slugify(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug or "player"


def normalized_name(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.lower()).strip()


def normalize_positions(value: Any) -> list[str]:
    if isinstance(value, list):
        raw_positions = value
    else:
        text = repair_text(value).replace("[", "").replace("]", "").replace("'", "").replace('"', "")
        raw_positions = re.split(r"[,;/|]+", text) if text else []

    normalized: list[str] = []
    for raw_position in raw_positions:
        key = re.sub(r"\s+", " ", repair_text(raw_position).upper().replace("-", " ")).strip()
        position = POSITION_MAP.get(key)
        if position and position not in normalized:
            normalized.append(position)
    return normalized


def numeric_attribute(row: dict[str, Any], key: str) -> float | None:
    value = row.get(key)
    if value is None or repair_text(value) == "":
        return None
    try:
        parsed = float(value)
        return max(0.0, min(99.0, parsed))
    except (TypeError, ValueError):
        return None


def weighted_attribute_score(row: dict[str, Any], weights: dict[str, float]) -> tuple[float, int]:
    weighted_total = 0.0
    available_weight = 0.0
    available_attributes = 0
    for attribute, weight in weights.items():
        value = numeric_attribute(row, attribute)
        if value is None:
            continue
        weighted_total += value * weight
        available_weight += weight
        available_attributes += 1
    if available_weight == 0:
        return 0.0, 0
    return weighted_total / available_weight, available_attributes


def calculate_iog(row: dict[str, Any], positions: list[str], overall: int) -> int:
    primary = positions[0]
    if primary == "GK":
        weights = {
            "goalkeeping_diving": 0.22,
            "goalkeeping_reflexes": 0.25,
            "goalkeeping_handling": 0.18,
            "goalkeeping_positioning": 0.20,
            "goalkeeping_kicking": 0.15,
        }
    elif primary in {"CB", "LB", "RB", "LWB", "RWB"}:
        weights = {
            "defending": 0.25,
            "physic": 0.15,
            "pace": 0.12,
            "attacking_heading_accuracy": 0.12,
            "mentality_interceptions": 0.16,
            "defending_standing_tackle": 0.12,
            "defending_sliding_tackle": 0.08,
        }
    elif primary in {"CDM", "CM", "CAM", "LM", "RM"}:
        weights = {
            "passing": 0.20,
            "mentality_vision": 0.16,
            "skill_ball_control": 0.15,
            "dribbling": 0.12,
            "power_stamina": 0.12,
            "defending": 0.10 if primary in {"CDM", "CM"} else 0.05,
            "mentality_interceptions": 0.08 if primary in {"CDM", "CM"} else 0.03,
            "shooting": 0.04 if primary == "CDM" else 0.09,
            "mentality_positioning": 0.03 if primary == "CDM" else 0.08,
        }
    else:
        weights = {
            "attacking_finishing": 0.24,
            "shooting": 0.18,
            "pace": 0.18,
            "dribbling": 0.18,
            "mentality_positioning": 0.12,
            "passing": 0.10,
        }

    attribute_score, available_attributes = weighted_attribute_score(row, weights)
    if available_attributes < 3:
        return overall
    return max(0, min(99, round(attribute_score * 0.78 + overall * 0.22)))


def stable_player_id(source_id: Any, name: str, nation: str, club: str, dob: str) -> str:
    source_text = repair_text(source_id)
    if source_text:
        if re.fullmatch(r"\d+(?:\.0+)?", source_text):
            source_text = str(int(float(source_text)))
        return f"fc26-{slugify(source_text)}"

    identity = "|".join((name.casefold(), nation.casefold(), club.casefold(), dob.casefold()))
    digest = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:10]
    return f"fc26-{slugify(name)}-{digest}"


def candidate_from_row(raw_row: dict[str, Any], counters: Counter[str]) -> Candidate | None:
    row = normalized_row(raw_row)
    name = repair_text(first_value(row, FIELD_ALIASES["name"]))
    if not name:
        counters["missing_names"] += 1
        counters["invalid_discarded"] += 1
        return None

    positions = normalize_positions(first_value(row, FIELD_ALIASES["positions"]))
    if not positions:
        counters["missing_positions"] += 1
        counters["invalid_discarded"] += 1
        return None

    nation = repair_text(first_value(row, FIELD_ALIASES["nation"]))
    if not nation:
        counters["missing_nations"] += 1
        counters["invalid_discarded"] += 1
        return None
    club = repair_text(first_value(row, FIELD_ALIASES["club"]))
    if not club:
        counters["missing_clubs_repaired"] += 1
        club = "Free Agent"

    age = max(0, to_int(first_value(row, FIELD_ALIASES["age"])))
    overall = max(0, min(99, to_int(first_value(row, FIELD_ALIASES["overall"]))))
    potential = max(0, min(99, to_int(first_value(row, FIELD_ALIASES["potential"]), overall)))
    iog = IOG_OVERRIDES.get(normalized_name(name), calculate_iog(row, positions, overall))
    if iog <= 0:
        counters["missing_iog"] += 1
        counters["invalid_discarded"] += 1
        return None
    source_id = first_value(row, FIELD_ALIASES["source_id"])
    dob = repair_text(first_value(row, FIELD_ALIASES["dob"]))
    player_id = stable_player_id(source_id, name, nation, club, dob)

    source_identity = repair_text(source_id)
    dedup_key = f"source:{source_identity}" if source_identity else "identity:" + "|".join(
        (name.casefold(), nation.casefold(), dob.casefold() or club.casefold())
    )
    completeness = sum(bool(value) for value in (name, nation, club, positions, age, overall, potential))
    quality = (
        to_int(first_value(row, FIELD_ALIASES["version"])),
        to_int(first_value(row, FIELD_ALIASES["update"])),
        completeness,
        overall,
    )

    return Candidate(
        player={
            "id": player_id,
            "name": name,
            "nation": nation,
            "club": club,
            "position": positions[0],
            "positions": positions,
            "age": age,
            "overall": overall,
            "potential": potential,
            "iog": iog,
            "source": "fc26",
        },
        dedup_key=dedup_key,
        quality=quality,
    )


def detect_encoding(path: Path) -> str:
    sample = path.read_bytes()[:65536]
    try:
        sample.decode("utf-8-sig")
        return "utf-8-sig"
    except UnicodeDecodeError:
        return "cp1252"


def csv_columns(path: Path) -> list[str]:
    with path.open("r", encoding=detect_encoding(path), errors="replace", newline="") as handle:
        reader = csv.reader(handle)
        return [column.strip() for column in next(reader, [])]


def json_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("players", "data", "items", "results", "records"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if any(alias in {str(key).lower() for key in payload} for alias in FIELD_ALIASES["name"]):
            return [payload]
    return []


def read_json(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding=detect_encoding(path), errors="replace") as handle:
        return json_records(json.load(handle))


def source_columns(path: Path) -> list[str]:
    if path.suffix.lower() == ".csv":
        return csv_columns(path)
    records = read_json(path)
    return sorted({str(key) for record in records[:20] for key in record})


def looks_like_player_columns(columns: Iterable[str]) -> bool:
    available = {str(column).strip().lower() for column in columns}
    has_name = any(alias in available for alias in FIELD_ALIASES["name"])
    has_identity = any(alias in available for alias in FIELD_ALIASES["source_id"])
    has_position_or_rating = any(alias in available for alias in FIELD_ALIASES["positions"] + FIELD_ALIASES["overall"])
    return has_name and (has_identity or has_position_or_rating)


def iter_records(path: Path) -> Iterator[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding=detect_encoding(path), errors="replace", newline="") as handle:
            yield from csv.DictReader(handle)
        return
    yield from read_json(path)


def discover_dataset_dir(explicit: str | Path | None = None) -> Path:
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.exists() or not path.is_dir():
            raise FileNotFoundError(f"FC26 dataset folder does not exist: {path}")
        return path

    environment_path = os.environ.get("FC26_DATASET_DIR")
    if environment_path:
        return discover_dataset_dir(environment_path)

    canonical_files = list(PROJECT_ROOT.glob("*FC26*DataHub*/**/players.csv"))
    if not canonical_files:
        canonical_files = list(PROJECT_ROOT.rglob("players.csv"))
    if canonical_files:
        canonical_files.sort(
            key=lambda path: (
                len(path.relative_to(PROJECT_ROOT).parts),
                0 if path.parent.name.lower() == "data" else 1,
                -path.stat().st_size,
            )
        )
        return canonical_files[0].parent.resolve()

    raise FileNotFoundError(
        "Could not auto-detect an FC26 dataset folder. Pass --input or set FC26_DATASET_DIR."
    )


def discover_source_files(dataset_dir: Path) -> list[Path]:
    files = [
        path for path in dataset_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".csv", ".json"}
    ]
    return sorted(files, key=lambda path: str(path).casefold())


def ensure_unique_ids(players: list[dict[str, Any]]) -> int:
    seen: dict[str, str] = {}
    collisions = 0
    for player in players:
        player_id = str(player["id"])
        identity = f"{player['name']}|{player['nation']}|{player['club']}"
        if player_id in seen and seen[player_id] != identity:
            collisions += 1
            suffix = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:8]
            player["id"] = f"{player_id}-{suffix}"
        seen[str(player["id"])] = identity
    return collisions


def top_players(players: list[dict[str, Any]], field: str, limit: int = 50) -> list[dict[str, Any]]:
    ranked = sorted(players, key=lambda player: (-to_int(player.get(field)), -to_int(player.get("overall")), player["name"]))
    return [
        {
            "id": player["id"],
            "name": player["name"],
            "club": player["club"],
            "nation": player["nation"],
            "iog": player["iog"],
            "overall": player["overall"],
            "potential": player["potential"],
            "positions": player["positions"],
        }
        for player in ranked[:limit]
    ]


def build_report(
    players: list[dict[str, Any]],
    counters: Counter[str],
    dataset_dir: Path,
    discovered_files: list[Path],
    imported_files: list[dict[str, Any]],
    skipped_files: list[dict[str, str]],
    errors: list[dict[str, str]],
) -> dict[str, Any]:
    primary_distribution = Counter(player["position"] for player in players)
    all_position_distribution = Counter(position for player in players for position in player["positions"])
    discarded = counters["invalid_discarded"] + counters["duplicates_removed"]
    return {
        "dataset_folder": str(dataset_dir),
        "files_discovered": len(discovered_files),
        "files_imported": imported_files,
        "files_skipped": skipped_files,
        "errors": errors,
        "players_processed": counters["processed_rows"],
        "total_players_imported": len(players),
        "players_discarded": discarded,
        "invalid_players_discarded": counters["invalid_discarded"],
        "duplicates_removed": counters["duplicates_removed"],
        "missing_names": counters["missing_names"],
        "missing_nations": counters["missing_nations"],
        "missing_positions": counters["missing_positions"],
        "missing_iog": counters["missing_iog"],
        "missing_clubs_repaired_as_free_agent": counters["missing_clubs_repaired"],
        "id_collisions_repaired": counters["id_collisions_repaired"],
        "primary_position_distribution": dict(sorted(primary_distribution.items())),
        "position_distribution": dict(sorted(all_position_distribution.items())),
        "top_50_overall": top_players(players, "overall"),
        "top_50_potential": top_players(players, "potential"),
        "top_50_iog": top_players(players, "iog"),
    }


def import_dataset(dataset_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    discovered_files = discover_source_files(dataset_dir)
    counters: Counter[str] = Counter()
    candidates: dict[str, Candidate] = {}
    imported_files: list[dict[str, Any]] = []
    skipped_files: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    log(f"Dataset folder: {dataset_dir}")
    log(f"Files discovered: {len(discovered_files)}")
    for path in discovered_files:
        log(f"Discovered: {path}")

    for path in discovered_files:
        try:
            columns = source_columns(path)
            if not looks_like_player_columns(columns):
                skipped_files.append({"file": str(path), "reason": "No player-like schema detected"})
                log(f"Skipped non-player file: {path.name}")
                continue

            mapped_columns = {
                field: next((alias for alias in aliases if alias in {column.lower() for column in columns}), None)
                for field, aliases in FIELD_ALIASES.items()
            }
            file_rows = 0
            file_valid = 0
            log(f"Parsing: {path}")
            log(f"Available columns ({len(columns)}): {', '.join(columns)}")
            log(f"Mapped columns: {json.dumps(mapped_columns, ensure_ascii=False)}")

            for row in iter_records(path):
                file_rows += 1
                counters["processed_rows"] += 1
                candidate = candidate_from_row(row, counters)
                if candidate is None:
                    continue
                file_valid += 1
                existing = candidates.get(candidate.dedup_key)
                if existing is None or candidate.quality > existing.quality:
                    if existing is not None:
                        counters["duplicates_removed"] += 1
                    candidates[candidate.dedup_key] = candidate
                else:
                    counters["duplicates_removed"] += 1

            imported_files.append({
                "file": str(path),
                "rows": file_rows,
                "valid_rows": file_valid,
                "columns": columns,
                "mapped_columns": mapped_columns,
            })
            log(f"Players processed from {path.name}: {file_rows} ({file_valid} valid before deduplication)")
        except Exception as exc:  # Continue importing other files while recording bounded diagnostics.
            error = {"file": str(path), "error": f"{type(exc).__name__}: {exc}"}
            errors.append(error)
            log(f"ERROR: {error['file']}: {error['error']}")

    players = [candidate.player for candidate in candidates.values()]
    counters["id_collisions_repaired"] = ensure_unique_ids(players)
    players.sort(key=lambda player: (-player["overall"], -player["potential"], player["name"].casefold(), player["id"]))
    report = build_report(players, counters, dataset_dir, discovered_files, imported_files, skipped_files, errors)
    return players, report


def validate_players(players: Any) -> dict[str, Any]:
    if not isinstance(players, list):
        return {"valid": False, "errors": ["Top-level JSON value must be an array"], "total_players": 0}

    missing_names: list[str] = []
    missing_nations: list[str] = []
    missing_positions: list[str] = []
    missing_clubs: list[str] = []
    duplicate_ids: list[str] = []
    invalid_records: list[str] = []
    missing_iog: list[str] = []
    seen_ids: set[str] = set()
    distribution: Counter[str] = Counter()

    for index, player in enumerate(players):
        if not isinstance(player, dict):
            invalid_records.append(f"index:{index}")
            continue
        player_id = repair_text(player.get("id"))
        if not player_id:
            invalid_records.append(f"index:{index}:missing_id")
        elif player_id in seen_ids:
            duplicate_ids.append(player_id)
        seen_ids.add(player_id)

        if not repair_text(player.get("name")):
            missing_names.append(player_id or f"index:{index}")
        if not repair_text(player.get("nation")):
            missing_nations.append(player_id or f"index:{index}")
        positions = player.get("positions")
        if not isinstance(positions, list) or not positions or any(position not in VALID_POSITIONS for position in positions):
            missing_positions.append(player_id or f"index:{index}")
        else:
            distribution.update(positions)
        if not repair_text(player.get("club")):
            missing_clubs.append(player_id or f"index:{index}")
        if to_int(player.get("iog")) <= 0:
            missing_iog.append(player_id or f"index:{index}")

    errors: list[str] = []
    if invalid_records:
        errors.append(f"Invalid records: {len(invalid_records)}")
    if missing_names:
        errors.append(f"Missing names: {len(missing_names)}")
    if missing_nations:
        errors.append(f"Missing nations: {len(missing_nations)}")
    if missing_positions:
        errors.append(f"Missing or invalid positions: {len(missing_positions)}")
    if missing_clubs:
        errors.append(f"Missing clubs: {len(missing_clubs)}")
    if missing_iog:
        errors.append(f"Missing IoG: {len(missing_iog)}")
    if duplicate_ids:
        errors.append(f"Duplicate IDs: {len(duplicate_ids)}")

    return {
        "valid": not errors,
        "total_players": len(players),
        "errors": errors,
        "missing_names": missing_names,
        "missing_nations": missing_nations,
        "missing_positions": missing_positions,
        "missing_clubs": missing_clubs,
        "missing_iog": missing_iog,
        "duplicate_ids": duplicate_ids,
        "invalid_records": invalid_records,
        "position_distribution": dict(sorted(distribution.items())),
    }


def read_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json_atomic(path: Path, payload: Any, *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        if compact:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    temporary.replace(path)


def print_ranked(title: str, players: list[dict[str, Any]], field: str) -> None:
    print(f"\n{title}")
    for rank, player in enumerate(players, start=1):
        print(f"{rank:>2}. {player['name']} | {player['club']} | {field} {player[field]}")


def print_import_summary(report: dict[str, Any]) -> None:
    print("\nFC26 IMPORT SUMMARY")
    print(f"Total players imported: {report['total_players_imported']}")
    print(f"Players processed: {report['players_processed']}")
    print(f"Players discarded: {report['players_discarded']}")
    print(f"Duplicates removed: {report['duplicates_removed']}")
    print(f"Missing names: {report['missing_names']}")
    print(f"Missing nations: {report['missing_nations']}")
    print(f"Missing positions: {report['missing_positions']}")
    print(f"Missing IoG: {report['missing_iog']}")
    print(f"Missing clubs repaired: {report['missing_clubs_repaired_as_free_agent']}")
    print(f"Errors encountered: {len(report['errors'])}")
    print("Position distribution:")
    for position, count in report["position_distribution"].items():
        print(f"  {position}: {count}")
    print_ranked("TOP 50 HIGHEST OVERALL", report["top_50_overall"], "overall")
    print_ranked("TOP 50 HIGHEST POTENTIAL", report["top_50_potential"], "potential")
    print_ranked("TOP 50 HIGHEST IOG", report["top_50_iog"], "iog")
