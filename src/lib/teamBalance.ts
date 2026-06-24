import { calculateLibraScore } from "./squadAnalysis";

export type BalanceLine = "attack" | "midfield" | "defense";

export type TeamBalancePlayer = {
  assignedPosition: string;
  adjustedIog?: number;
  iog?: number;
  positions?: string[] | string;
};

export type TeamBalanceProfile = {
  attack: number;
  midfield: number;
  defense: number;
  chemistry: number;
  positionFit: number;
  libraScore: number | null;
  tacticalDistribution: number;
  status: string;
  insight: string;
};

const linePositions: Record<BalanceLine, string[]> = {
  attack: ["ST", "CF", "SS", "RW", "LW"],
  midfield: ["CM", "CAM", "CDM", "RM", "LM"],
  defense: ["CB", "LB", "RB", "LWB", "RWB", "GK"]
};

const roleWeights: Record<string, number> = {
  ST: 1.15,
  CF: 1.12,
  SS: 1.1,
  RW: 1,
  LW: 1,
  CAM: 1.08,
  CDM: 1.05,
  CM: 1,
  RM: 0.92,
  LM: 0.92,
  CB: 1.08,
  GK: 1.1,
  LB: 1,
  RB: 1,
  LWB: 0.95,
  RWB: 0.95
};

const formationBias: Record<string, Record<BalanceLine, number>> = {
  "4-4-2": { attack: 2, midfield: -3, defense: 2 },
  "4-3-3": { attack: 7, midfield: 1, defense: -4 },
  "4-2-3-1": { attack: -2, midfield: 8, defense: 2 },
  "4-1-2-1-2": { attack: 3, midfield: 8, defense: -1 },
  "4-6-0": { attack: -12, midfield: 12, defense: 1 },
  "3-5-2": { attack: 2, midfield: 7, defense: -3 },
  "3-4-3": { attack: 8, midfield: 1, defense: -7 },
  "3-4-2-1": { attack: 6, midfield: 7, defense: -6 },
  "5-4-1": { attack: -9, midfield: 1, defense: 10 },
  "3-2-4-1": { attack: 6, midfield: 7, defense: -6 },
  "4-1-4-1": { attack: -4, midfield: 7, defense: 4 },
  "4-4-1-1": { attack: 1, midfield: 2, defense: 1 }
};

function clamp(value: number, min = 0, max = 100) {
  return Math.max(min, Math.min(max, value));
}

function normalizePosition(value: string) {
  const position = String(value ?? "").toUpperCase().trim().replace(/[^A-Z0-9]/g, "").replace(/[0-9]+$/, "");
  if (position === "DM") return "CDM";
  if (position === "AM") return "CAM";
  return position;
}

function parsePositions(value: TeamBalancePlayer["positions"]) {
  if (Array.isArray(value)) return value.map(normalizePosition).filter(Boolean);
  return String(value ?? "").split(/[,/|]+/).map(normalizePosition).filter(Boolean);
}

function lineForPosition(position: string): BalanceLine | null {
  const normalized = normalizePosition(position);
  for (const line of Object.keys(linePositions) as BalanceLine[]) {
    if (linePositions[line].includes(normalized)) return line;
  }
  return null;
}

function compatibleRole(playerPosition: string, assignedPosition: string) {
  const player = normalizePosition(playerPosition);
  const assigned = normalizePosition(assignedPosition);
  const aliases: Record<string, string[]> = {
    RB: ["RB", "RWB"], RWB: ["RB", "RWB", "RM"],
    LB: ["LB", "LWB"], LWB: ["LB", "LWB", "LM"],
    CDM: ["CDM", "CM"], CM: ["CM", "CDM", "CAM"], CAM: ["CAM", "CM"],
    RW: ["RW", "RM"], RM: ["RM", "RW"], LW: ["LW", "LM"], LM: ["LM", "LW"],
    ST: ["ST", "CF", "SS"], CF: ["ST", "CF", "CAM"], SS: ["ST", "CF", "CAM"],
    CB: ["CB"], GK: ["GK"]
  };
  return (aliases[player] ?? [player]).includes(assigned);
}

export function playerPositionFit(player: TeamBalancePlayer) {
  const assigned = normalizePosition(player.assignedPosition);
  const positions = parsePositions(player.positions);
  const exactIndex = positions.indexOf(assigned);
  if (exactIndex === 0) return 1;
  if (exactIndex === 1) return 0.9;
  if (exactIndex >= 2) return 0.8;
  if (positions.some((position) => compatibleRole(position, assigned))) return 0.8;
  return 0.6;
}

function weightedLineScore(players: TeamBalancePlayer[], line: BalanceLine) {
  const linePlayers = players.filter((player) => lineForPosition(player.assignedPosition) === line);
  if (linePlayers.length === 0) return 0;
  let weightedTotal = 0;
  let totalWeight = 0;
  for (const player of linePlayers) {
    const position = normalizePosition(player.assignedPosition);
    const weight = roleWeights[position] ?? 1;
    const iog = Number.isFinite(Number(player.adjustedIog)) ? Number(player.adjustedIog) : Number(player.iog);
    if (!Number.isFinite(iog)) continue;
    weightedTotal += iog * playerPositionFit(player) * weight;
    totalWeight += weight;
  }
  return totalWeight ? weightedTotal / totalWeight : 0;
}

function tacticalDistribution(players: TeamBalancePlayer[]) {
  if (players.length === 0) return 0;
  const assignedCounts = { attack: 0, midfield: 0, defense: 0 };
  const naturalCounts = { attack: 0, midfield: 0, defense: 0 };
  for (const player of players) {
    const assignedLine = lineForPosition(player.assignedPosition);
    const naturalLine = lineForPosition(parsePositions(player.positions)[0] ?? "");
    if (assignedLine) assignedCounts[assignedLine] += 1;
    if (naturalLine) naturalCounts[naturalLine] += 1;
  }
  const difference = (Object.keys(assignedCounts) as BalanceLine[])
    .reduce((sum, line) => sum + Math.abs(assignedCounts[line] - naturalCounts[line]), 0);
  return clamp(100 - (difference / Math.max(players.length * 2, 1)) * 100);
}

function makeInsight(scores: Record<BalanceLine, number>, formation: string, libra: number | null, chemistry: number, fit: number) {
  const ranked = (Object.entries(scores) as Array<[BalanceLine, number]>).sort((a, b) => b[1] - a[1]);
  const spread = ranked[0][1] - ranked[2][1];
  if (fit < 72) return "The Libra Score was dragged down by positional compromises.";
  if (formation === "4-1-2-1-2" && scores.midfield > scores.attack) return "The central overload is strong, but the lack of natural width reduced overall balance.";
  if (spread <= 4 && (libra ?? 0) >= 85 && chemistry >= 80 && fit >= 90) return "Your shape is one of the most balanced I've seen.";
  if (ranked[0][0] === "midfield") return formationBias[formation]?.midfield > 4 ? "The formation amplified your midfield advantage." : "Your midfield is carrying the team.";
  if (ranked[0][0] === "defense") return "You built a defensively dominant structure.";
  if (ranked[0][0] === "attack" && scores.attack - scores.defense >= 10) return "The attack is elite but the defense may collapse.";
  return `${ranked[0][0][0].toUpperCase()}${ranked[0][0].slice(1)} is your strongest line, while ${ranked[2][0]} needs protection.`;
}

export function calculateTeamBalance(
  players: TeamBalancePlayer[],
  formation: string,
  chemistry: number,
  positionFit: number
): TeamBalanceProfile {
  const raw = {
    attack: weightedLineScore(players, "attack"),
    midfield: weightedLineScore(players, "midfield"),
    defense: weightedLineScore(players, "defense")
  };
  const bias = formationBias[formation] ?? { attack: 0, midfield: 0, defense: 0 };
  const distribution = tacticalDistribution(players);
  const tieredPositionFit = players.length
    ? players.reduce((sum, player) => sum + playerPositionFit(player), 0) / players.length * 100
    : positionFit;
  const libraScore = calculateLibraScore(players as Array<{ adjustedIog: number }>, {
    formation,
    chemistry,
    positionFit: tieredPositionFit,
    tacticalDistribution: distribution
  });
  const chemistryFactor = 0.84 + clamp(chemistry) * 0.0016;
  const tacticalFactor = 0.9 + distribution * 0.001;
  const libraFactor = 0.94 + clamp(libraScore ?? 0) * 0.0006;
  const scores = {} as Record<BalanceLine, number>;

  for (const line of Object.keys(raw) as BalanceLine[]) {
    if (raw[line] === 0) {
      scores[line] = 0;
      continue;
    }
    const shaped = raw[line] + bias[line];
    scores[line] = clamp(shaped * chemistryFactor * tacticalFactor * libraFactor);
  }

  const rounded = {
    attack: Math.round(scores.attack * 10) / 10,
    midfield: Math.round(scores.midfield * 10) / 10,
    defense: Math.round(scores.defense * 10) / 10
  };
  const ranked = (Object.entries(rounded) as Array<[BalanceLine, number]>).filter(([, value]) => value > 0).sort((a, b) => b[1] - a[1]);
  const spread = ranked.length === 3 ? ranked[0][1] - ranked[2][1] : 100;
  const status = ranked.length < 3
    ? "Shape Forming"
    : spread <= 4 && (libraScore ?? 0) >= 85 && chemistry >= 80 && tieredPositionFit >= 90
      ? "Elite Balance"
      : spread <= 7
        ? "Balanced XI"
        : `${ranked[0][0][0].toUpperCase()}${ranked[0][0].slice(1)} Led`;

  return {
    ...rounded,
    chemistry: Math.round(clamp(chemistry)),
    positionFit: Math.round(clamp(tieredPositionFit)),
    libraScore,
    tacticalDistribution: Math.round(distribution),
    status,
    insight: players.length < 3
      ? "The tactical shape will emerge as more players are assigned."
      : makeInsight(rounded, formation, libraScore, chemistry, tieredPositionFit)
  };
}
