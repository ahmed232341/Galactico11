import json
import pathlib
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent

FILES = {
    'src_players_json': ROOT / 'src' / 'data' / 'players.json',
    'processed_player_stats_csv': ROOT / 'data' / 'processed' / 'player_stats.csv',
    'processed_player_stats_parquet': ROOT / 'data' / 'processed' / 'player_stats.parquet',
    'processed_player_iog_csv': ROOT / 'data' / 'processed' / 'player_iog.csv',
    'processed_player_iog_parquet': ROOT / 'data' / 'processed' / 'player_iog.parquet',
    'exports_players_json': ROOT / 'data' / 'exports' / 'players.json',
    'exports_players_csv': ROOT / 'data' / 'exports' / 'players.csv',
}


def file_info(p: pathlib.Path):
    if not p.exists():
        return {'exists': False, 'size': None}
    try:
        size = p.stat().st_size
    except Exception:
        size = None
    return {'exists': True, 'size': size}


def load_json_list(p: pathlib.Path):
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def top_n_iog(players, n=20):
    def key(p):
        try:
            return float(p.get('iog', 0))
        except Exception:
            return 0
    return sorted(players, key=key, reverse=True)[:n]


def counts_by(players, field):
    c = Counter(p.get(field) for p in players)
    if None in c:
        del c[None]
    return c


def main():
    print('=== Pipeline Audit ===')
    for name, p in FILES.items():
        info = file_info(p)
        print(f"{name}: exists={info['exists']} size={info['size']}")

    players = load_json_list(FILES['src_players_json'])
    print('\n=== Loaded src/data/players.json ===')
    print('total_players', len(players))
    if players:
        print('top_iog:')
        for p in top_n_iog(players, 20):
            print(' -', p.get('name'), 'iog=', p.get('iog'), 'club=', p.get('club'), 'era=', p.get('era'), 'league=', p.get('league'))

        for field in ['league', 'club', 'era']:
            c = counts_by(players, field)
            print(f"\ncount_by_{field} (top 15):")
            for k, v in c.most_common(15):
                print(' -', k, v)
    else:
        print('No players loaded from src/data/players.json (empty or invalid JSON).')

if __name__ == '__main__':
    main()

