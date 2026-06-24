export type RatedSquadPlayer = {
  adjustedIog: number;
  assignedPosition?: string;
  positions?: string[] | string;
};

export type LibraContext = {
  formation?: string;
  chemistry?: number;
  positionFit?: number;
  tacticalDistribution?: number;
};

const formationBalance: Record<string, number> = {
  "4-4-2": 96,
  "4-4-1-1": 92,
  "4-2-3-1": 90,
  "4-1-4-1": 88,
  "4-3-3": 84,
  "3-5-2": 78,
  "3-4-2-1": 76,
  "3-4-3": 70,
  "5-4-1": 72,
  "4-1-2-1-2": 76,
  "4-6-0": 62,
  "3-2-4-1": 70
};

function clamp(value: number, min = 0, max = 100) {
  return Math.max(min, Math.min(max, value));
}

function normalizePosition(value: string) {
  const position = String(value ?? "").toUpperCase().replace(/[^A-Z0-9]/g, "").replace(/[0-9]+$/, "");
  if (position === "DM") return "CDM";
  if (position === "AM") return "CAM";
  return position;
}

function positionLine(value: string) {
  const position = normalizePosition(value);
  if (["ST", "CF", "SS", "LW", "RW"].includes(position)) return "attack";
  if (["CM", "CAM", "CDM", "LM", "RM"].includes(position)) return "midfield";
  if (["GK", "CB", "LB", "RB", "LWB", "RWB"].includes(position)) return "defense";
  return "unknown";
}

function formationTargets(formation = "") {
  const numbers = formation.split("-").map(Number).filter(Number.isFinite);
  if (numbers.length < 2) return { attack: 0.27, midfield: 0.36, defense: 0.37 };
  const defense = numbers[0];
  const attack = numbers[numbers.length - 1];
  const midfield = numbers.slice(1, -1).reduce((sum, value) => sum + value, 0);
  const total = Math.max(defense + midfield + attack, 1);
  return { attack: attack / total, midfield: midfield / total, defense: defense / total };
}

function calculateRoleBalance(players: RatedSquadPlayer[], formation?: string) {
  if (players.length === 0) return 0;
  const counts = { attack: 0, midfield: 0, defense: 0 };
  for (const player of players) {
    const line = positionLine(player.assignedPosition ?? "");
    if (line !== "unknown") counts[line] += 1;
  }
  const assigned = counts.attack + counts.midfield + counts.defense;
  if (assigned === 0) return 50;
  const targets = formationTargets(formation);
  const difference =
    Math.abs(counts.attack / assigned - targets.attack) +
    Math.abs(counts.midfield / assigned - targets.midfield) +
    Math.abs(counts.defense / assigned - targets.defense);
  const lineCoverage = Object.values(counts).filter((count) => count > 0).length / 3;
  return clamp((1 - difference / 2) * 75 + lineCoverage * 25);
}

function inferredPositionFit(players: RatedSquadPlayer[]) {
  const fitted = players.filter((player) => {
    const assigned = normalizePosition(player.assignedPosition ?? "");
    const positions = Array.isArray(player.positions)
      ? player.positions.map(normalizePosition)
      : String(player.positions ?? "").split(/[,/|]+/).map(normalizePosition);
    return assigned && positions.includes(assigned);
  }).length;
  return players.length ? fitted / players.length * 100 : 0;
}

export function calculateLibraScore(players: RatedSquadPlayer[], context: LibraContext = {}) {
  const values = players.map((player) => Number(player.adjustedIog)).filter(Number.isFinite);
  if (values.length < 2) return null;

  const averageIog = values.reduce((sum, value) => sum + value, 0) / values.length;
  const variance = values.reduce((sum, value) => sum + Math.pow(value - averageIog, 2), 0) / values.length;
  const standardDeviation = Math.sqrt(variance);
  const range = Math.max(...values) - Math.min(...values);
  const consistency = clamp(100 - standardDeviation * 3.2 - range * 1.15);
  const roleBalance = calculateRoleBalance(players, context.formation);
  const shapeBalance = formationBalance[context.formation ?? ""] ?? 78;
  const chemistry = clamp(context.chemistry ?? 60);
  const positionFit = clamp(context.positionFit ?? inferredPositionFit(players));
  const tacticalFit = clamp(context.tacticalDistribution ?? roleBalance);

  const score =
    averageIog * 0.25 +
    consistency * 0.3 +
    roleBalance * 0.12 +
    shapeBalance * 0.08 +
    chemistry * 0.1 +
    positionFit * 0.08 +
    tacticalFit * 0.07;

  return Math.round(clamp(score));
}
