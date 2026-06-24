import argparse
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PROCESSED_DIR = BASE_DIR.parent / "data" / "processed"

OUTPUT_DIR = DEFAULT_PROCESSED_DIR
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ROLE_WEIGHTS = {
    "GK": {
        "goalkeeper_norm": 0.70,
        "defense_norm": 0.15,
        "progression_norm": 0.15,
    },
    "CB": {
        "defense_norm": 0.55,
        "progression_norm": 0.25,
        "creation_norm": 0.10,
        "attack_norm": 0.10,
    },
    "FB": {
        "defense_norm": 0.35,
        "progression_norm": 0.35,
        "creation_norm": 0.20,
        "attack_norm": 0.10,
    },
    "CDM": {
        "defense_norm": 0.40,
        "progression_norm": 0.35,
        "creation_norm": 0.15,
        "attack_norm": 0.10,
    },
    "CM": {
        "progression_norm": 0.35,
        "creation_norm": 0.30,
        "defense_norm": 0.20,
        "attack_norm": 0.15,
    },
    "CAM": {
        "creation_norm": 0.40,
        "attack_norm": 0.30,
        "progression_norm": 0.25,
        "defense_norm": 0.05,
    },
    "WINGER": {
        "attack_norm": 0.35,
        "creation_norm": 0.30,
        "progression_norm": 0.30,
        "defense_norm": 0.05,
    },
    "ST": {
        "attack_norm": 0.55,
        "creation_norm": 0.25,
        "progression_norm": 0.15,
        "defense_norm": 0.05,
    },
}


def normalize_position(position):
    value = str(position).upper().strip()
    value = "".join(ch for ch in value if ch.isalnum())
    value = value.rstrip("0123456789")

    if value == "DM":
        return "CDM"
    if value == "AM":
        return "CAM"
    if value == "CF":
        return "ST"
    return value


def as_position_list(positions):
    if positions is None:
        return []
    if isinstance(positions, str):
        cleaned = positions.strip().strip("[]")
        parts = cleaned.replace("'", "").replace('"', "").replace(";", ",").replace("/", ",").split(",")
        return [normalize_position(pos) for pos in parts if pos.strip()]
    if not isinstance(positions, list):
        try:
            positions = list(positions)
        except TypeError:
            positions = [positions]
    return [normalize_position(pos) for pos in positions if str(pos).strip()]


def infer_position_role(positions):
    positions = as_position_list(positions)

    if "GK" in positions:
        return "GK"
    if "ST" in positions:
        return "ST"
    if any(pos in {"LW", "RW", "LM", "RM"} for pos in positions):
        return "WINGER"
    if "CAM" in positions:
        return "CAM"
    if "CM" in positions:
        return "CM"
    if "CDM" in positions:
        return "CDM"
    if any(pos in {"LB", "RB", "LWB", "RWB"} for pos in positions):
        return "FB"
    if "CB" in positions:
        return "CB"
    return "CM"


def percentile_rank(series: pd.Series) -> pd.Series:
    return series.rank(pct=True, method="max") * 100


def compute_zscore(series: pd.Series) -> pd.Series:
    if series.std(ddof=0) == 0:
        return pd.Series(0.0, index=series.index)
    return (series - series.mean()) / series.std(ddof=0)


def weighted_score(df, metrics):
    score = pd.Series(0.0, index=df.index)
    for metric, weight in metrics.items():
        score += df[metric].fillna(0.0) * weight
    return score


def normalize_group(df, group_cols, feature):
    return df.groupby(group_cols)[feature].transform(lambda x: compute_zscore(x))


def minmax(series: pd.Series) -> pd.Series:
    return (series - series.min()) / (series.max() - series.min() + 1e-9) * 100


def role_weighted_iog_raw(row):
    weights = ROLE_WEIGHTS.get(row["position_role"], ROLE_WEIGHTS["CM"])
    return sum(row[feature] * weight for feature, weight in weights.items())


def calculate_iog(processed_data_dir: Path):
    processed_data_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = processed_data_dir / "player_stats.parquet"
    csv_path = processed_data_dir / "player_stats.csv"

    if parquet_path.exists():
        print(f"Reading player_stats parquet: {parquet_path}")
        df = pd.read_parquet(parquet_path)
    elif csv_path.exists():
        print(f"WARNING: {parquet_path} missing; falling back to CSV: {csv_path}")
        df = pd.read_csv(csv_path)
    else:
        raise RuntimeError(f"Neither {parquet_path} nor {csv_path} exists; cannot calculate IoG")

    print(f"Loaded player_stats rows={len(df)} columns={list(df.columns)}")

    df["position_role"] = df["positions"].apply(infer_position_role)
    df["position_group"] = df["position_role"]
    df["era"] = df["era"].fillna("unknown")
    df["league"] = df["league"].fillna("unknown")
    df["season"] = df["season"].fillna("unknown")

    df["attack_score"] = weighted_score(df, {
        "goals": 2.5,
        "npxG": 2.0,
        "shots_on_target": 0.7,
        "xG_per_shot": 1.2,
        "big_chances": 1.3,
    })

    df["creation_score"] = weighted_score(df, {
        "assists": 2.5,
        "xA": 2.2,
        "key_passes": 1.0,
        "through_balls": 1.4,
        "chances_created": 1.1,
    })

    df["progression_score"] = weighted_score(df, {
        "progressive_passes": 1.5,
        "progressive_carries": 1.8,
        "carries_into_box": 1.6,
        "passes_into_box": 1.2,
    })

    df["defense_score"] = weighted_score(df, {
        "tackles": 1.4,
        "interceptions": 1.5,
        "blocks": 1.0,
        "clearances": 1.0,
        "pressures": 0.6,
        "counterpressures": 0.8,
    })

    df["goalkeeper_score"] = weighted_score(df, {
        "saves": 2.5,
        "save_percentage": 1.8,
        "goals_prevented": 2.5,
    })

    role_context = ["position_role", "league", "season", "era"]
    df["attack_norm"] = normalize_group(df, role_context, "attack_score")
    df["creation_norm"] = normalize_group(df, role_context, "creation_score")
    df["progression_norm"] = normalize_group(df, role_context, "progression_score")
    df["defense_norm"] = normalize_group(df, role_context, "defense_score")
    df["goalkeeper_norm"] = normalize_group(df, role_context, "goalkeeper_score")

    df["AttackIoG"] = minmax(df["attack_norm"])
    df["CreationIoG"] = minmax(df["creation_norm"])
    df["ProgressionIoG"] = minmax(df["progression_norm"])
    df["DefensiveIoG"] = minmax(df["defense_norm"])
    df["GoalkeeperIoG"] = minmax(df["goalkeeper_norm"])

    df["iog_raw"] = df.apply(role_weighted_iog_raw, axis=1)
    df["position_percentile"] = df.groupby("position_role")["iog_raw"].transform(percentile_rank)
    df["iog"] = 50 + (df["position_percentile"] / 100) * 49
    df["iog"] = df["iog"].round(1)

    df["position_percentile"] = df["position_percentile"].round(1)
    df["rank_tier"] = pd.cut(
        df["position_percentile"],
        bins=[0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100],
        labels=["Top 1%", "Top 5%", "Top 10%", "Top 25%", "Top 50%", "Top 75%", "Top 90%", "Top 95%", "Top 99%", "Elite"],
        include_lowest=True,
    )

    iog_csv_path = processed_data_dir / "player_iog.csv"
    df.to_csv(iog_csv_path, index=False)
    print(f"Wrote {iog_csv_path} rows={len(df)}")

    iog_parquet_path = processed_data_dir / "player_iog.parquet"
    try:
        df.to_parquet(iog_parquet_path, index=False)
        print(f"Wrote {iog_parquet_path} rows={len(df)}")
    except Exception as e:
        print(f"WARNING: Could not write parquet {iog_parquet_path}: {e}")

    print(f"Calculated IoG for {len(df)} player-seasons.")
    return df



def main():
    parser = argparse.ArgumentParser(description="Calculate IoG from processed player statistics")
    parser.add_argument("--processed-data", type=Path, default=DEFAULT_PROCESSED_DIR, help="Processed data root directory")
    args = parser.parse_args()

    calculate_iog(args.processed_data)


if __name__ == "__main__":
    main()
