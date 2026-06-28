export interface Player {
  id: number | string;
  name: string;
  club: string;
  domesticClub?: string;
  originalClub?: string;
  league: string;
  domesticLeague?: string;
  competition?: string;
  nation?: string;
  era: string;
  positions: string[];
  iog: number;
  overall?: number;
  potential?: number;
  dataSource?: string;
  source?: string;
  age?: number | null;
  appearances?: number | null;
  starts?: number | null;
  goals?: number | null;
  assists?: number | null;
  xg?: number | null;
  xa?: number | null;
  shots?: number | null;
  shots_on_target?: number | null;
  shotsOnTarget?: number | null;
  shots_on_target_pct?: number | null;
  shotsOnTargetPct?: number | null;
  yellowCards?: number | null;
  redCards?: number | null;
  key_passes?: number;
  progressive_passes?: number;
  progressive_carries?: number;
  carries_into_box?: number;
  passes_into_box?: number;
  touches_in_box?: number;
  tackles?: number | null;
  tacklesWon?: number | null;
  interceptions?: number | null;
  crosses?: number | null;
  blocks?: number | null;
  clearances?: number | null;
  recoveries?: number;
  saves?: number;
  savePct?: number | null;
  save_pct?: number | null;
  cleanSheets?: number | null;
  clean_sheets?: number;
  goalsAgainst?: number | null;
  goalsAgainstPer90?: number | null;
  goals_conceded_per90?: number | null;
  sweeper_actions?: number;
  pass_pct?: number | null;
  aerial_win_pct?: number | null;
  touches?: number | null;
  minutes?: number | null;
}

// Import generated players data from players.json (populated by pipeline).
import playersJson from './players.json';
import clubPlayersJson from './club_players.json';
import worldCupPlayersJson from './worldcup_2026_players.json';
import fc26PlayersJson from './fc26_players.json';

const normalizeNationKey = (value: unknown) =>
  String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z0-9]+/g, ' ')
    .trim()
    .toLowerCase();

const nationDisplayCorrections: Record<string, string> = {
  'congo dr': 'Congo DR',
  switzeland: 'Switzerland',
  usa: 'USA',
};

const qualifiedNationMap = new Map<string, string>();
for (const player of Array.isArray(worldCupPlayersJson) ? worldCupPlayersJson : []) {
  const nation = String(player.nation ?? player.club ?? '').trim();
  if (!nation) continue;
  const key = normalizeNationKey(nation);
  qualifiedNationMap.set(key, nationDisplayCorrections[key] ?? nation);
}

const fc26NationAliases: Record<string, string> = {
  'bosnia and herzegovina': 'bosnia',
  czechia: 'czech republic',
  'cote d ivoire': 'ivory coast',
  'korea republic': 'south korea',
  switzerland: 'switzeland',
  turkiye: 'turkey',
  'united states': 'usa',
};

const getQualifiedNation = (nation: unknown) => {
  const key = normalizeNationKey(nation);
  return qualifiedNationMap.get(key) ?? qualifiedNationMap.get(fc26NationAliases[key]);
};

const statsBombPlayers = Array.isArray(playersJson)
  ? playersJson.filter((player) => player.league !== 'World Cup' && player.competition !== 'World Cup')
  : [];
const clubPlayers = Array.isArray(clubPlayersJson)
  ? clubPlayersJson.map((player) => ({
      ...player,
      positions: player.positions ?? (player.position ? [player.position] : []),
      dataSource: player.dataSource ?? 'manual_club_mode',
    }))
  : [];
const fc26Players = Array.isArray(fc26PlayersJson)
  ? fc26PlayersJson.map((player) => {
      const qualifiedNation = getQualifiedNation(player.nation);
      return {
      ...player,
      domesticClub: player.club,
      originalClub: player.club,
      club: qualifiedNation ?? player.club,
      league: qualifiedNation ? 'World Cup' : 'ET Mode',
      competition: qualifiedNation ? 'World Cup' : 'ET Mode',
      era: '2020s',
      nation: qualifiedNation ?? player.nation,
      dataSource: 'fc26',
    };
    })
  : [];
const worldCupPlayers = fc26Players.filter((player) => player.competition === 'World Cup');

const fallbackPlayers: Player[] = [];
const mergedPlayers = [...statsBombPlayers, ...clubPlayers, ...fc26Players];

// Use fallback data only if both imported datasets are empty.
export const players: Player[] = (mergedPlayers.length ? mergedPlayers : fallbackPlayers) as Player[];
export const playerCounts = {
  statsBomb: statsBombPlayers.length,
  club: clubPlayers.length,
  fc26: fc26Players.length,
  worldCup: worldCupPlayers.length,
  total: mergedPlayers.length,
};
