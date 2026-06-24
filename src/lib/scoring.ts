type Player = {
  id: number;
  name: string;
  iog: number;
  club: string;
};

export function calculateTeamIoG(players: Array<Player | null>) {
  const selectedPlayers = players.filter(Boolean) as Player[];

  if (selectedPlayers.length === 0) {
    return 0;
  }

  const totalIoG = selectedPlayers.reduce((sum, player) => {
    return sum + player.iog;
  }, 0);

  return Number((totalIoG / selectedPlayers.length).toFixed(1));
}

export function getTeamGrade(score: number) {
  if (score >= 96) return "S+";
  if (score >= 93) return "S";
  if (score >= 90) return "A+";
  if (score >= 87) return "A";
  if (score >= 84) return "A-";
  if (score >= 80) return "B+";
  if (score >= 76) return "B";
  if (score >= 70) return "C";
  return "D";
}

export function getStrongestPlayer(players: Player[]): Player | null {
  if (players.length === 0) return null;
  return [...players].sort((a, b) => b.iog - a.iog)[0];
}

export function getWeakestPlayer(players: Player[]): Player | null {
  if (players.length === 0) return null;
  return [...players].sort((a, b) => a.iog - b.iog)[0];
}

export function getUniqueUniverses(players: { club: string, era: string }[]): number {
  const universes = players.map(p => `${p.club}-${p.era}`);
  return new Set(universes).size;
}