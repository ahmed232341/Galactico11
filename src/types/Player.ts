export type Player = {
  id: number;
  name: string;
  club: string;
  league: string;
  era: string;
  positions: string[];
  iog: number;
  image?: string;
  selectedPosition?: string;
  goals: number;
  assists: number;
  xg: number;
  xa: number;
  shots: number;
  shots_on_target: number;
  shots_on_target_pct?: number | null;
  key_passes?: number;
  progressive_passes?: number;
  progressive_carries?: number;
  carries_into_box?: number;
  passes_into_box?: number;
  touches_in_box?: number;
  tackles: number;
  interceptions: number;
  blocks: number;
  clearances: number;
  recoveries?: number;
  saves?: number;
  save_pct?: number | null;
  clean_sheets?: number;
  goals_conceded_per90?: number | null;
  sweeper_actions?: number;
  pass_pct?: number | null;
  aerial_win_pct?: number | null;
  touches: number;
  minutes: number;
};

export type Challenge = {
  league: string;
  club: string;
  era: string;
};

export type ScreenState = "formation" | "spin" | "draft" | "result";
