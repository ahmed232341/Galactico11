<script lang="ts">
  import { onMount } from "svelte";
  import TeamBalanceHexagon from "./TeamBalanceHexagon.svelte";
  import { formatIoG } from "../../lib/iogFormat";
  import { calculateLibraScore } from "../../lib/squadAnalysis";
  import { calculateTeamBalance, type TeamBalanceProfile } from "../../lib/teamBalance";

  type Player = {
    id: number | string;
    name: string;
    club: string;
    domesticClub?: string;
    originalClub?: string;
    league: string;
    domesticLeague?: string;
    competition?: string;
    nation?: string;
    team?: string;
    era: string;
    dataSource?: string;
    source?: string;
    position?: string[] | string;
    positions?: string[] | string;
    iog?: number;
    overall?: number;
    goals?: number;
    assists?: number;
    xg?: number;
    xa?: number;
    tackles?: number;
    interceptions?: number;
    blocks?: number;
    clearances?: number;
    recoveries?: number;
    progressivePasses?: number;
    progressive_passes?: number;
    progressiveCarries?: number;
    progressive_carries?: number;
    keyPasses?: number;
    key_passes?: number;
    shotCreation?: number;
    shot_creation?: number;
    shots?: number;
    shotsOnTargetPct?: number | null;
    shots_on_target_pct?: number | null;
    touchesInBox?: number;
    touches_in_box?: number;
    saves?: number;
    savePct?: number | null;
    save_pct?: number | null;
    cleanSheets?: number;
    clean_sheets?: number;
    goalsConcededPer90?: number | null;
    goals_conceded_per90?: number | null;
    goalsAgainst?: number | null;
    sweeperActions?: number;
    sweeper_actions?: number;
    passPct?: number | null;
    pass_pct?: number | null;
    aerialWinPct?: number | null;
    aerial_win_pct?: number | null;
    aerialWins?: number;
    aerial_wins?: number;
    psxgPrevented?: number | null;
    psxg_prevented?: number | null;
    distributionPct?: number | null;
    distribution_pct?: number | null;
    minutes?: number | null;
    appearances?: number | null;
    roleBucket?: string;
    leagueMultiplier?: number;
    leagueStrength?: number;
    positionRole?: string;
    superstarOverride?: boolean;
  };

  type Slot = {
    id: string;
    label: string;
    position: string;
    x: number;
    y: number;
  };

  type Universe = {
    league: string;
    club: string;
    era: string;
    competition?: string;
  };

  type NationCard = {
    name: string;
    flag: string;
    playerCount: number;
    avgIog: string;
    imported: boolean;
  };

  type DraftOption = Player & {
    adjustedIog: number;
    emergency: boolean;
    slotCount: number;
  };

  type SortKey = "iog_desc" | "iog_asc" | "name" | "best_fit" | "goals" | "assists";
  type ClubFormat = "league" | "champions";
  type ClubLeague = "Premier League" | "La Liga" | "Serie A" | "Bundesliga" | "Ligue 1";
  type InvinciblesChallengeId = "european" | "premier" | "laliga" | "seriea" | "bundesliga" | "ligue1";
  type WorldCupPoolProfile = "elite" | "strong" | "balanced" | "weak" | "chaos";
  type WorldCupOutcome =
    | "Group Stage Exit"
    | "Round of 32 Exit"
    | "Round of 16 Exit"
    | "Quarterfinal Exit"
    | "Semifinal Exit"
    | "Runner-up"
    | "World Cup Winner";
  type TutorialStep = 0 | 1 | 2 | 3;

  type PickedPlayer = DraftOption & {
    slotId: string;
    assignedPosition: string;
    penalty: number;
    mysteryPick?: boolean;
    goldenPick?: boolean;
    pickLabel?: string;
    alternatives?: string[];
  };

  type BenchSub = DraftOption & {
    benchRole: "Backup GK" | "Defensive Cover" | "Midfield Control" | "Attacking Wildcard" | "Utility Player";
  };

  type ClubSeasonRecord = {
    record: string;
    points: number;
  };

  type EtLeagueRecord = {
    wins: number;
    draws: number;
    losses: number;
    record: string;
    points: number;
    position: string;
    goalDifference: number;
    goalsFor: number;
    goalsAgainst: number;
    cleanSheets: number;
    titleChance: number;
    invincibleChance: number;
    invinciblesRating: number;
  };

  type AlienOpponent = {
    name: "Moonrock Rovers" | "Betelgeuse United" | "The Clones" | "Orion FC" | "Paradox";
    averageIog: number;
    threatLevel: string;
    tacticalStyle: string;
    pressure: number;
    premise: string;
  };

  type EtAlienMatch = {
    opponent: AlienOpponent;
    survivalChance: number;
    outcome: "win" | "loss" | "barely";
    resultText: string;
    resultTone: "high" | "medium" | "low";
    scoreline: string;
    route: string;
    keyPlayer: string;
    mirrorThreats: Array<{ name: string; originalIog: number; paradoxIog: number }>;
    tacticalNote: string;
  };

  type WorldCupSimulation = {
    baseOutcome: WorldCupOutcome;
    finalOutcome: WorldCupOutcome;
    libraBoostStages: number;
    score: number;
    varianceLabel: string;
    explanation: string;
  };

  type PostDraftAnalysisStep = {
    id: string;
    kicker: string;
    title: string;
    body: string;
    metricLabel: string;
    metricValue: string;
    tone: "intro" | "shape" | "pick" | "turn" | "pair" | "identity" | "balance" | "mystery" | "grade";
    mysteryPlayer?: PickedPlayer;
    mysteryImpact?: {
      chemistry: number;
      line: string;
      lineRating: number;
      projectedPoints?: number;
      quote: string;
    };
  };

  type PitchSlot = Slot & {
    player: PickedPlayer | undefined;
    state: "filled" | "eligible" | "locked" | "empty";
  };

  let players: Player[] = [];
  let playerDataLoaded = false;
  let playerDataLoading: Promise<void> | null = null;
  const positionCache = new Map<string, string[]>();
  const iogCache = new Map<string, number>();
  const clubLeagueOptions: ClubLeague[] = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"];
  const supportedClubCompetitions = new Set<string>([...clubLeagueOptions, "Champions League"]);
  const invinciblesChallenges: Array<{ id: InvinciblesChallengeId; label: string; shortLabel: string; leagues: ClubLeague[]; description: string }> = [
    {
      id: "european",
      label: "European Elite Challenge",
      shortLabel: "European Elite",
      leagues: clubLeagueOptions,
      description: "Draft across all five major European leagues."
    },
    {
      id: "premier",
      label: "Premier League Challenge",
      shortLabel: "Premier League",
      leagues: ["Premier League"],
      description: "Build an XI from Premier League clubs."
    },
    {
      id: "laliga",
      label: "La Liga Challenge",
      shortLabel: "La Liga",
      leagues: ["La Liga"],
      description: "Build an XI from Spanish clubs."
    },
    {
      id: "seriea",
      label: "Serie A Challenge",
      shortLabel: "Serie A",
      leagues: ["Serie A"],
      description: "Build an XI from Italian clubs."
    },
    {
      id: "bundesliga",
      label: "Bundesliga Challenge",
      shortLabel: "Bundesliga",
      leagues: ["Bundesliga"],
      description: "Build an XI from German clubs."
    },
    {
      id: "ligue1",
      label: "Ligue 1 Challenge",
      shortLabel: "Ligue 1",
      leagues: ["Ligue 1"],
      description: "Build an XI from French clubs."
    }
  ];
  const positionAliasesByPlayer: Record<string, string[]> = {
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
    "achraf hakimi": ["RB", "RWB"],
    "theo hernandez": ["LB", "LWB"],
    "theo hérnandez": ["LB", "LWB"],
    "alphonso davies": ["LB", "LWB"],
    "trent alexander arnold": ["RB", "CM"],
    "trent alexander-arnold": ["RB", "CM"],
    "joao cancelo": ["RB", "LB", "RWB", "LWB"],
    "joão cancelo": ["RB", "LB", "RWB", "LWB"],
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
    "vinícius júnior": ["LW"]
  };
  const roleAliasesByPlayer: Record<string, string> = {
    "erling haaland": "ST",
    "harry kane": "ST",
    "lautaro martinez": "ST",
    "romelu lukaku": "ST",
    "darwin nunez": "ST",
    "goncalo ramos": "ST",
    "martin odegaard": "CAM",
    "kevin de bruyne": "CAM",
    "bruno fernandes": "CAM",
    "rodri": "CDM",
    "virgil van dijk": "CB"
  };
  const superstarOverridePlayers = new Set([
    "antoine griezmann",
    "bernardo silva",
    "bruno fernandes",
    "bukayo saka",
    "christian pulisic",
    "cristiano ronaldo",
    "darwin nunez",
    "erling haaland",
    "harry kane",
    "jamal musiala",
    "jude bellingham",
    "khvicha kvaratskhelia",
    "julian alvarez",
    "kevin de bruyne",
    "kylian mbappe",
    "lamine yamal",
    "lautaro martinez",
    "lionel messi",
    "luis suarez",
    "luka modric",
    "martin odegaard",
    "mohamed salah",
    "neymar",
    "ousmane dembele",
    "pedri",
    "raphinha",
    "rodri",
    "rodrygo",
    "romelu lukaku",
    "son heung min",
    "vinicius junior",
    "virgil van dijk"
  ]);
  const tier1Nations = new Set([
    "Argentina", "France", "Spain", "England", "Brazil", "Morocco", "Portugal", "Netherlands", "Germany", "Belgium"
  ]);
  const tier2Nations = new Set([
    "Mexico", "Colombia", "Croatia", "USA", "Usa", "United States", "Senegal", "Japan", "Uruguay", "Switzerland",
    "Switzeland", "Austria", "Australia", "IR Iran", "Iran", "Korea Republic", "South Korea", "Nigeria"
  ]);
  let iogRankingsCache: {
    id: string;
    score: number;
    performance: number;
    strength: number;
    career: number;
    consistency: number;
  }[] | null = null;
  const leagueMatchCounts: Record<ClubLeague, number> = {
    "Premier League": 38,
    "La Liga": 38,
    "Serie A": 38,
    Bundesliga: 34,
    "Ligue 1": 34
  };

  function slot(id: string, position: string, x: number, y: number): Slot {
    return { id, label: position, position, x, y };
  }

  const formations: Record<string, Slot[]> = {
    "4-3-3": [
      slot("lw", "LW", 22, 18),
      slot("st", "ST", 50, 14),
      slot("rw", "RW", 78, 18),
      slot("cm1", "CM", 28, 43),
      slot("cm2", "CM", 50, 47),
      slot("cm3", "CM", 72, 43),
      slot("lb", "LB", 17, 68),
      slot("cb1", "CB", 38, 70),
      slot("cb2", "CB", 62, 70),
      slot("rb", "RB", 83, 68),
      slot("gk", "GK", 50, 90)
    ],

    "4-4-2": [
      slot("st1", "ST", 40, 15),
      slot("st2", "ST", 60, 15),
      slot("lm", "LM", 18, 42),
      slot("cm1", "CM", 40, 45),
      slot("cm2", "CM", 60, 45),
      slot("rm", "RM", 82, 42),
      slot("lb", "LB", 17, 68),
      slot("cb1", "CB", 38, 70),
      slot("cb2", "CB", 62, 70),
      slot("rb", "RB", 83, 68),
      slot("gk", "GK", 50, 90)
    ],

    "4-4-1-1": [
      slot("st", "ST", 50, 13),
      slot("cam", "CAM", 50, 29),
      slot("lm", "LM", 18, 43),
      slot("cm1", "CM", 40, 46),
      slot("cm2", "CM", 60, 46),
      slot("rm", "RM", 82, 43),
      slot("lb", "LB", 17, 70),
      slot("cb1", "CB", 38, 72),
      slot("cb2", "CB", 62, 72),
      slot("rb", "RB", 83, 70),
      slot("gk", "GK", 50, 90)
    ],

    "4-2-3-1": [
      slot("st", "ST", 50, 13),
      slot("lw", "LW", 22, 31),
      slot("cam", "CAM", 50, 34),
      slot("rw", "RW", 78, 31),
      slot("dm1", "CDM", 40, 52),
      slot("dm2", "CDM", 60, 52),
      slot("lb", "LB", 17, 70),
      slot("cb1", "CB", 38, 72),
      slot("cb2", "CB", 62, 72),
      slot("rb", "RB", 83, 70),
      slot("gk", "GK", 50, 90)
    ],

    "4-1-4-1": [
      slot("st", "ST", 50, 14),
      slot("lm", "LM", 18, 36),
      slot("cm1", "CM", 38, 40),
      slot("cm2", "CM", 62, 40),
      slot("rm", "RM", 82, 36),
      slot("cdm", "CDM", 50, 56),
      slot("lb", "LB", 17, 72),
      slot("cb1", "CB", 38, 74),
      slot("cb2", "CB", 62, 74),
      slot("rb", "RB", 83, 72),
      slot("gk", "GK", 50, 90)
    ],

    "3-5-2": [
      slot("st1", "ST", 40, 15),
      slot("st2", "ST", 60, 15),
      slot("lm", "LM", 16, 42),
      slot("cm1", "CM", 36, 44),
      slot("cam", "CAM", 50, 36),
      slot("cm2", "CM", 64, 44),
      slot("rm", "RM", 84, 42),
      slot("cb1", "CB", 30, 72),
      slot("cb2", "CB", 50, 75),
      slot("cb3", "CB", 70, 72),
      slot("gk", "GK", 50, 90)
    ],

    "3-4-3": [
      slot("lw", "LW", 22, 17),
      slot("st", "ST", 50, 13),
      slot("rw", "RW", 78, 17),
      slot("lm", "LM", 18, 43),
      slot("cm1", "CM", 40, 46),
      slot("cm2", "CM", 60, 46),
      slot("rm", "RM", 82, 43),
      slot("cb1", "CB", 30, 72),
      slot("cb2", "CB", 50, 75),
      slot("cb3", "CB", 70, 72),
      slot("gk", "GK", 50, 90)
    ],

    "3-4-2-1": [
      slot("st", "ST", 50, 13),
      slot("cam1", "CAM", 39, 30),
      slot("cam2", "CAM", 61, 30),
      slot("lm", "LM", 18, 43),
      slot("cm1", "CM", 40, 46),
      slot("cm2", "CM", 60, 46),
      slot("rm", "RM", 82, 43),
      slot("cb1", "CB", 30, 72),
      slot("cb2", "CB", 50, 75),
      slot("cb3", "CB", 70, 72),
      slot("gk", "GK", 50, 90)
    ],

    "5-4-1": [
      slot("st", "ST", 50, 14),
      slot("lm", "LM", 18, 40),
      slot("cm1", "CM", 40, 44),
      slot("cm2", "CM", 60, 44),
      slot("rm", "RM", 82, 40),
      slot("lb", "LB", 12, 70),
      slot("cb1", "CB", 31, 73),
      slot("cb2", "CB", 50, 76),
      slot("cb3", "CB", 69, 73),
      slot("rb", "RB", 88, 70),
      slot("gk", "GK", 50, 90)
    ]
  };

  const clubColors: Record<string, string> = {
    Chelsea: "#2563eb",
    Arsenal: "#dc2626",
    Liverpool: "#dc2626",
    "Manchester United": "#dc2626",
    "Manchester City": "#38bdf8",
    Barcelona: "#7c3aed",
    "Real Madrid": "#c9a646",
    "Atletico Madrid": "#ef4444",
    "Bayern Munich": "#dc2626",
    Dortmund: "#facc15",
    "Borussia Dortmund": "#facc15",
    "AC Milan": "#ef4444",
    Inter: "#2563eb",
    Juventus: "#f4f4f5",
    PSG: "#2563eb",
    Nigeria: "#16a34a",
    Haiti: "#2563eb"
  };

  const fallbackUniverses: Universe[] = [
    { league: "Premier League", club: "Chelsea", era: "2000s" },
    { league: "Premier League", club: "Arsenal", era: "2000s" },
    { league: "La Liga", club: "Barcelona", era: "2010s" },
    { league: "La Liga", club: "Real Madrid", era: "2010s" },
    { league: "Serie A", club: "AC Milan", era: "2000s" },
    { league: "Bundesliga", club: "Bayern Munich", era: "2010s" }
  ];
  const etUniverse: Universe = { league: "Signal Contact", club: "Galactico11", era: "2020s", competition: "Signal Contact" };
  const ET_ACCENT = "#39e6c9";

  let derivedUniverses: Universe[] = [];
  let universes: Universe[] = fallbackUniverses;
  let worldCupUniverses: Universe[] = [];
  let classicUniverses: Universe[] = fallbackUniverses;
  let universePlayerIndex = new Map<string, Player[]>();

  let screen: "menu" | "loading" | "mode" | "etIntro" | "clubFormat" | "formation" | "draft" | "bench" | "analysis" | "playLevel" | "simulation" | "record" | "libra" | "verdict" | "result" = "menu";
  let formation = "4-3-3";
  let draftMode: "worldcup" | "club" | "et" | "invinciblesClub" = "worldcup";
  let clubFormat: ClubFormat = "league";
  let selectedClubLeague: ClubLeague = "Premier League";
  let selectedInvinciblesChallenge: InvinciblesChallengeId = "european";
  let universe = worldCupUniverses[0] ?? classicUniverses[0] ?? universes[0];

  let picked: PickedPlayer[] = [];
  let bench: BenchSub[] = [];
  let benchCandidates: BenchSub[] = [];
  let benchPool: DraftOption[] = [];
  let benchSearch = "";
  let lastAssignedPlayer: PickedPlayer | null = null;
  let selectedPlayer: DraftOption | null = null;
  let selectedSlotId = "";

  let isSpinning = false;
  let canPick = false;
  let respinsRemaining = 2;
  let fallbackNotice = "";
  let search = "";
  let positionFilter = "ALL";
  let sortKey: SortKey = "iog_desc";
  let mysteryPickNumber = 0;
  let goldenPickNumber = 0;
  let revealedMysteryPlayerIds: string[] = [];
  let lastPickLabel = "";
  let pickChips: Array<{ text: string; tone: "good" | "warn" | "info" | "bad" }> = [];
  let pickChipTimer: ReturnType<typeof setTimeout> | null = null;
  let lastAssignedSlotId = "";
  let assignedPulseTimer: ReturnType<typeof setTimeout> | null = null;
  let options: DraftOption[] = [];
  let seenPlayerIds = new Set<string>();
  let rejectedPlayerIds = new Set<string>();
  let usedInvinciblesClubs = new Set<string>();
  let showDraftTimeline = false;
  let worldCupPoolProfile: WorldCupPoolProfile = "balanced";
  let worldCupSimulationSeed = randomInt(1000, 999999);
  let visibleOptionLimit = 80;
  let phoebeTutorialSeen = false;
  let showPhoebeTutorial = false;
  let tutorialStep: TutorialStep = 0;
  let tutorialAttackPoolActive = false;
  let showShareModal = false;
  let shareStatus = "";
  let loadingPercent = 0;
  let loadingExiting = false;
  let loadingTimer: ReturnType<typeof setInterval> | null = null;
  let analysisStepIndex = 0;
  let simulatedWins = 0;
  let simulatedDraws = 0;
  let simulatedLosses = 0;
  let simulationComplete = false;
  let finalVerdictStepIndex = 0;
  let finalVerdictTimer: ReturnType<typeof setTimeout> | null = null;
  let etSignalSearching = false;
  let etSignalText = "SEARCHING HUMANITY DATABASE";
  const etSignalMessages = [
    "SEARCHING HUMANITY DATABASE",
    "SIGNAL LOCKING",
    "PLAYER POOL DECRYPTING",
    "GALACTICO11 SIGNAL FOUND"
  ];
  const finalVerdictSteps = [
    "Analyzing XI...",
    "Calculating IoG...",
    "Testing Libra...",
    "Simulating pressure...",
    "Final Verdict..."
  ];

  // PLAY LEVEL (cinematic tournament + managerial checkpoints)
  let playLevelStepIndex = 0;
  let playLevelMaxSteps = 0;
  let playLevelCompleted = false;
  let playLevelStarted = false;

  type PlayLevelStep = {
    id: string;
    title: string;
    kicker: string;
    stage: string;
    opponent?: string;
    scoreline?: string;
    advanced?: boolean;
    manOfTheMatch?: string;
    tacticalAnalysis?: string;
    checkpointSummary?: {
      position: string;
      record: string;
      points: number;
      goalsFor: number;
      goalsAgainst: number;
      goalDifference?: number;
      invincible?: boolean;
      biggestWin: { vs: string; score: string };
      biggestDefeat?: { vs: string; score: string };
    };
  };

  let playLevelSteps: PlayLevelStep[] = [];
  let playLevelCurrentStep: PlayLevelStep | null = null;
  let playLevelSeed = 0;
  let playLevelSeasonSummary: {
    invincible: boolean;
    goldenBoot: string;
    bestPlayerName: string;
    biggestSurprise: string;
    trophyCabinet: string[];
    teamIdentityName: string;
    historicalComparison: string;
    topWins: number;
  } | null = null;

  let simulationTimer: ReturnType<typeof setInterval> | null = null;
  const tutorialMessages: Record<TutorialStep, string> = {
    0: "Pick a mode. I’ll judge the XI after the draft.",
    1: "World Cup is pressure football: nation pools, knockout margins, no easy picks.",
    2: "Invincibles is a season test: stars help, but consistency keeps the run alive.",
    3: "ET Mode is Galactico11’s alien signal challenge. Draft Earth’s strongest XI, survive interference, and face one of five cosmic opponents. Chemistry, Libra, balance, and IoG decide whether Earth survives or the transmission ends."
  };
  const alienOpponents: AlienOpponent[] = [
    {
      name: "Moonrock Rovers",
      averageIog: 68,
      threatLevel: "Low Orbit",
      tacticalStyle: "Erratic low-gravity counters",
      pressure: -8,
      premise: "A weak alien signal, beatable by most stable drafts."
    },
    {
      name: "Betelgeuse United",
      averageIog: 78,
      threatLevel: "Volatile",
      tacticalStyle: "Aggressive stellar overloads",
      pressure: 1,
      premise: "Dangerous in attack, but the signal has gaps."
    },
    {
      name: "The Clones",
      averageIog: 80,
      threatLevel: "Repeating Pattern",
      tacticalStyle: "Balanced duplication press",
      pressure: 3,
      premise: "Repetitive, organised and difficult to break down."
    },
    {
      name: "Orion FC",
      averageIog: 84,
      threatLevel: "Structured Threat",
      tacticalStyle: "Disciplined cosmic positional play",
      pressure: 6,
      premise: "Strong tactical structure that punishes weak balance."
    },
    {
      name: "Paradox",
      averageIog: 90,
      threatLevel: "Universal Final Boss",
      tacticalStyle: "",
      pressure: 12,
      premise: "The opposition is not from this timeline."
    }
  ];

  onMount(() => {
    const seen = localStorage.getItem("phoebeTutorialSeen") === "true";
    phoebeTutorialSeen = seen;
  });

  function rebuildPlayerIndexes(nextPlayers: Player[]) {
    players = nextPlayers;
    positionCache.clear();
    iogCache.clear();
    iogRankingsCache = null;

    derivedUniverses = Array.from(
      new Map(
        players
          .filter((p) => p.league && p.club && p.era)
          .map((p) => [
            `${p.league}|${p.club}|${p.era}|${p.competition ?? "Draft"}`,
            { league: p.league, club: p.club, era: p.era, competition: p.competition }
          ])
      ).values()
    );

    universes = derivedUniverses.length ? derivedUniverses : fallbackUniverses;
    worldCupUniverses = universes.filter((item) => getUniverseCompetition(item) === "World Cup");
    classicUniverses = universes.filter((item) => getUniverseCompetition(item) !== "World Cup");
    universePlayerIndex = new Map<string, Player[]>();

    for (const player of players) {
      const teams = new Set([playerTeam(player), player.club, player.nation].filter(Boolean));
      for (const team of teams) {
        const key = `${player.league}|${team}|${player.era}|${getCompetition(player)}`;
        universePlayerIndex.set(key, [...(universePlayerIndex.get(key) ?? []), player]);
      }
    }

    universe = draftMode === "worldcup"
      ? worldCupUniverses[0] ?? universes[0] ?? universe
      : draftMode === "et"
        ? etUniverse
        : activeUniverses()[0] ?? universes[0] ?? universe;
  }

  function ensurePlayerDataLoaded() {
    if (playerDataLoaded) return Promise.resolve();
    if (playerDataLoading) return playerDataLoading;

    playerDataLoading = import("../../data/players").then((module) => {
      rebuildPlayerIndexes(module.players as Player[]);
      playerDataLoaded = true;
    }).catch((error) => {
      console.error("Failed to load player database", error);
      rebuildPlayerIndexes([]);
      playerDataLoaded = true;
    });

    return playerDataLoading;
  }

  $: slots = formations[formation];
  $: pickedIds = new Set(picked.map((player) => String(player.id)));
  $: accent = draftMode === "et" ? ET_ACCENT : (clubColors[universe.club] ?? "#c9a646");
  $: etSkinActive = draftMode === "et" && screen !== "menu" && screen !== "mode";
  $: emptySlots = slots.filter((slot) => !picked.some((p) => p.slotId === slot.id));
  $: openLabels = emptySlots.map((s) => s.label).join(", ");
  $: positionChoices = Array.from(new Set(options.flatMap((p) => getPositions(p)))).sort();
  $: filteredOptions = isMysteryRound
    ? options
    : sortOptions(
        options.filter((p) => {
          const matchesSearch = p.name.toLowerCase().includes(search.toLowerCase());
          const matchesPosition = positionFilter === "ALL" || getPositions(p).includes(positionFilter);
          return matchesSearch && matchesPosition;
        }),
        sortKey
      );
  $: visibleOptions = filteredOptions.slice(0, visibleOptionLimit);
  $: universePlayers = players.filter((p) => p.league === universe.league && p.club === universe.club && p.era === universe.era && getCompetition(p) === getUniverseCompetition(universe));
  $: selectedInvinciblesConfig = invinciblesChallenges.find((challenge) => challenge.id === selectedInvinciblesChallenge) ?? invinciblesChallenges[0];
  $: selectedInvinciblesMatches = selectedInvinciblesConfig.leagues.length === 1 ? (leagueMatchCounts[selectedInvinciblesConfig.leagues[0]] ?? 38) : 38;
  $: invinciblesSeasonMatches = draftMode === "invinciblesClub" ? selectedInvinciblesMatches : 38;
  $: etMaxPoints = invinciblesSeasonMatches * 3;
  $: currentUniverseTitle = draftMode === "et"
    ? `Signal Contact • Galactico11`
    : draftMode === "invinciblesClub"
      ? `Invincibles • ${selectedInvinciblesConfig.shortLabel} • ${universe.club}`
      : universeTitle(universe);
  $: headerTitle = getHeaderTitle();
  $: worldCupNations = buildWorldCupNations();
  $: hasClubUniverses = validClubUniverses().length > 0;
  $: teamIog = picked.length ? Math.round(picked.reduce((sum, p) => sum + p.adjustedIog, 0) / picked.length) : 0;
  $: avgIog = picked.length ? (picked.reduce((sum, p) => sum + p.adjustedIog, 0) / picked.length).toFixed(1) : "0.0";
  $: displayAvgIog = formatIoG(avgIog);
  $: benchImpact = calculateBenchImpact(bench);
  $: filteredBenchPool = benchSearch.trim()
    ? benchPool.filter((p) => p.name.toLowerCase().includes(benchSearch.toLowerCase()))
    : benchPool;
  $: pickReaction = lastAssignedPlayer ? getPickReaction(lastAssignedPlayer) : "";
  $: bestPlayer = picked.slice().sort((a, b) => b.adjustedIog - a.adjustedIog)[0];
  $: weakestPlayer = picked.slice().sort((a, b) => a.adjustedIog - b.adjustedIog)[0];
  $: captain = bestPlayer;
  $: chemistry = getChemistry(picked);
  $: positionFit = getPositionFit(picked);
  $: grade = getTeamGrade(Number(avgIog), chemistry, positionFit, weakestPlayer?.adjustedIog ?? 0);
  $: libraScore = calculateLibraScore(picked, { formation, chemistry, positionFit });
  $: finalBalanceProfile = calculateTeamBalance(picked, formation, chemistry, positionFit);
  $: squadDiagnosis = buildSquadDiagnosis(picked, finalBalanceProfile, chemistry, positionFit);
  $: worldCupSimulation = simulateWorldCupOutcome(picked, Number(avgIog), grade, chemistry, positionFit, libraScore, finalBalanceProfile);
  $: baseWorldCupOutcome = worldCupSimulation.baseOutcome;
  $: libraBonusActive = draftMode === "worldcup" && worldCupSimulation.libraBoostStages > 0;
  $: predictedWorldCupOutcome = worldCupSimulation.finalOutcome;
  $: predictedEtRecord = getEtLeagueRecord(picked, invinciblesSeasonMatches);
  $: predictedEtAlienMatch = getEtAlienMatch(picked);
  $: hiddenGem = computeHiddenGem(picked, weakestPlayer, bestPlayer, Number(avgIog));
  $: mostUnderratedPick =
    picked
      .filter((player) => player.adjustedIog >= Number(avgIog) && player.adjustedIog < (bestPlayer?.adjustedIog ?? 100))
      .sort((a, b) => b.adjustedIog - a.adjustedIog)[0] ?? hiddenGem;
  $: breakoutPlayer =
    mostUnderratedPick ??
    picked
      .slice()
      .sort((a, b) => (b.adjustedIog - Number(avgIog)) - (a.adjustedIog - Number(avgIog)))[0];
  $: weakestPosition = weakestPlayer?.assignedPosition ?? "None";
  $: topThreeConnections = picked
    .slice()
    .sort((a, b) => b.adjustedIog - a.adjustedIog)
    .slice(0, 3)
    .map((player) => player.name)
    .join(" • ");
  $: selectedLeagueMatches = leagueMatchCounts[selectedClubLeague] ?? 38;
  $: predictedClubRecord = getClubSeasonRecord(Number(avgIog), grade, selectedLeagueMatches);
  $: predictedChampionsLeagueOutcome = getChampionsLeagueOutcome(Number(avgIog), grade, chemistry, positionFit);
  $: postDraftAnalysis = buildPostDraftAnalysis(picked, formation, Number(avgIog), chemistry, positionFit, grade, draftMode);
  $: currentAnalysisStep = postDraftAnalysis[analysisStepIndex];
  $: analysisTotalSteps = postDraftAnalysis.length + 1;
  $: analysisProgress = ((analysisStepIndex + 1) / analysisTotalSteps) * 100;
  $: isGoldenRound = draftMode !== "et" && picked.length + 1 === goldenPickNumber && !picked.some((p) => p.goldenPick);
  $: isMysteryRound = picked.length + 1 === mysteryPickNumber && !picked.some((p) => p.mysteryPick) && !isGoldenRound;
  $: goldenRoundTitle = draftMode === "invinciblesClub"
      ? `Golden Pick • ${selectedInvinciblesConfig.shortLabel} • Full Pool`
      : draftMode === "worldcup" ? `Golden Pick • ${universe.club} • Full Pool` : "⭐ GOLDEN PICK";
  $: pitchSlots = slots.map((slot): PitchSlot => {
    const player = picked.find((p) => p.slotId === slot.id);
    const filled = Boolean(player);
    const eligible = Boolean(selectedPlayer && !filled && isPlayerCompatibleWithSlot(selectedPlayer, slot));

    return {
      ...slot,
      player,
      state: filled ? "filled" : selectedPlayer ? (eligible ? "eligible" : "locked") : "empty"
    };
  });

  function normalizePosition(pos: string) {
    let p = String(pos).toUpperCase().trim();

    p = p.replace(/[^A-Z0-9]/g, "");
    p = p.replace(/\d+$/, "");

    if (p === "DM") return "CDM";
    if (p === "AM") return "CAM";
    if (p === "CF") return "ST";
    if (p === "FULLBACK") return "FB";

    return p;
  }

  function normalizeName(name: string) {
    return String(name)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, " ")
      .trim();
  }

  function normalizeRole(pos: string) {
    return normalizePosition(pos);
  }

  function compatibleSlotRoles(playerPosition: string) {
    const role = normalizePosition(playerPosition);
    const aliases: Record<string, string[]> = {
      CB: ["CB"],
      ST: ["ST"],
      RW: ["RW", "RM"],
      LW: ["LW", "LM"],
      RM: ["RM", "RW"],
      LM: ["LM", "LW"],
      CDM: ["CDM", "CM"],
      CM: ["CM", "CDM", "CAM"],
      CAM: ["CAM", "CM"],
      FB: ["RB", "LB"],
      RB: ["RB", "RWB"],
      LB: ["LB", "LWB"],
      RWB: ["RWB", "RB", "RM"],
      LWB: ["LWB", "LB", "LM"],
      GK: ["GK"]
    };

    return aliases[role] ?? [role];
  }

  function parsePositions(raw: string[] | string | undefined) {
    if (!raw) return [];

    if (Array.isArray(raw)) {
      return raw
        .flatMap((item) => String(item).split(/[\/,|·•+\-]/))
        .map(normalizePosition)
        .filter(Boolean);
    }

    return String(raw)
      .split(/[\/,|·•+\-]/)
      .map(normalizePosition)
      .filter(Boolean);
  }

  function getPositions(player: Player) {
    const cacheKey = String(player.id);
    const cached = positionCache.get(cacheKey);
    if (cached) return cached;
    const aliased = positionAliasesByPlayer[normalizeName(player.name)] ?? positionAliasesByPlayer[String(player.name).toLowerCase()];
    if (aliased) {
      const normalized = Array.from(new Set(parsePositions(aliased)));
      positionCache.set(cacheKey, normalized);
      return normalized;
    }

    const positions = [
      ...parsePositions(player.position),
      ...parsePositions(player.positions)
    ];

    const unique = Array.from(new Set(positions));
    positionCache.set(cacheKey, unique);
    return unique;
  }

  function roleFromPosition(position: string) {
    const role = normalizePosition(position);
    if (role === "GK") return "GK";
    if (role === "CB") return "CB";
    if (["RB", "LB", "RWB", "LWB"].includes(role)) return "FB";
    if (role === "CDM") return "CDM";
    if (role === "CM") return "CM";
    if (role === "CAM") return "CAM";
    if (["RW", "LW", "RM", "LM"].includes(role)) return "Winger";
    if (role === "ST") return "ST";
    return "CM";
  }

  function playerRole(player: Player) {
    const aliased = roleAliasesByPlayer[normalizeName(player.name)];
    if (aliased) return aliased;
    const declared = String(player.roleBucket ?? "").trim();
    if (["GK", "CB", "FB", "CDM", "CM", "CAM", "Winger", "ST"].includes(declared)) return declared;
    const imported = String(player.positionRole ?? "").trim();
    if (["GK", "CB", "FB", "CDM", "CM", "CAM", "Winger", "ST"].includes(imported)) return imported;
    return roleFromPosition(getPositions(player)[0] ?? "CM");
  }

  function numericStat(player: Player, ...keys: string[]) {
    for (const key of keys) {
      const value = (player as Record<string, unknown>)[key];
      if (typeof value === "number" && Number.isFinite(value)) return value;
      if (typeof value === "string" && value.trim() !== "" && Number.isFinite(Number(value))) return Number(value);
    }
    return 0;
  }

  function per90(player: Player, value: number) {
    const minutes = Math.max(numericStat(player, "minutes"), 1);
    return (value / minutes) * 90;
  }

  function strengthMultiplier(player: Player) {
    const leagueStrength = numericStat(player, "leagueStrength");
    if (leagueStrength > 0) return Math.max(0.68, Math.min(1.08, leagueStrength));
    const explicit = numericStat(player, "leagueMultiplier");
    if (explicit > 0) return Math.max(0.82, Math.min(1.08, explicit));
    return 0.86;
  }

  function playerNation(player: Player) {
    return player.nation ?? player.club ?? "";
  }

  function nationTier(player: Player) {
    const nation = playerNation(player);
    if (tier1Nations.has(nation)) return 1;
    if (tier2Nations.has(nation)) return 2;
    return 3;
  }

  function nationStrengthScore(player: Player) {
    const tier = nationTier(player);
    if (tier === 1) return 100;
    if (tier === 2) return 88;
    return 74;
  }

  function clubCompetitionScore(player: Player) {
    if (hasSuperstarOverride(player)) return Math.max(94, strengthMultiplier(player) * 100);
    return strengthMultiplier(player) * 100;
  }

  function hasSuperstarOverride(player: Player) {
    return Boolean(player.superstarOverride) || superstarOverridePlayers.has(normalizeName(player.name));
  }

  function clamp(value: number, min = 0, max = 100) {
    return Math.max(min, Math.min(max, value));
  }

  function normalizeComponent(value: number, eliteValue: number) {
    return clamp((value / eliteValue) * 100, 0, 100);
  }

  function sampleReliability(player: Player) {
    const minutes = numericStat(player, "minutes");
    const appearances = numericStat(player, "appearances");
    const minuteScore = clamp(minutes / 9000, 0, 1);
    const appearanceScore = clamp(appearances / 180, 0, 1);
    return clamp(0.28 + minuteScore * 0.48 + appearanceScore * 0.24, 0.28, 1);
  }

  function positionPerformanceScore(player: Player) {
    const role = playerRole(player);
    const goals90 = per90(player, numericStat(player, "goals"));
    const assists90 = per90(player, numericStat(player, "assists"));
    const shots90 = per90(player, numericStat(player, "shots"));
    const sot90 = per90(player, numericStat(player, "shotsOnTarget", "shots_on_target"));
    const tackles90 = per90(player, numericStat(player, "tackles", "tacklesWon"));
    const interceptions90 = per90(player, numericStat(player, "interceptions"));
    const cleanSheets90 = per90(player, numericStat(player, "cleanSheets", "clean_sheets"));
    const saves90 = per90(player, numericStat(player, "saves"));
    const savePct = numericStat(player, "savePct", "save_pct");
    const goalsAgainst90 = numericStat(player, "goalsAgainstPer90", "goals_conceded_per90");
    const defensive90 = tackles90 + interceptions90;
    const creation90 = assists90 + per90(player, numericStat(player, "keyPasses", "key_passes", "crosses")) * 0.35;

    const roleScores: Record<string, number> = {
      GK: normalizeComponent(savePct, 78) * 0.46 + normalizeComponent(saves90, 4.2) * 0.24 + normalizeComponent(cleanSheets90, 0.42) * 0.2 + (100 - normalizeComponent(goalsAgainst90, 2.2)) * 0.1,
      CB: normalizeComponent(defensive90, 3.9) * 0.54 + normalizeComponent(cleanSheets90, 0.36) * 0.22 + normalizeComponent(assists90, 0.12) * 0.08 + sampleReliability(player) * 16,
      FB: normalizeComponent(defensive90, 3.4) * 0.34 + normalizeComponent(assists90, 0.22) * 0.28 + normalizeComponent(creation90, 0.8) * 0.24 + sampleReliability(player) * 14,
      CDM: normalizeComponent(defensive90, 4.1) * 0.48 + normalizeComponent(creation90, 0.58) * 0.24 + normalizeComponent(assists90, 0.16) * 0.12 + sampleReliability(player) * 16,
      CM: normalizeComponent(creation90, 0.72) * 0.36 + normalizeComponent(defensive90, 2.8) * 0.24 + normalizeComponent(goals90 + assists90, 0.46) * 0.24 + sampleReliability(player) * 16,
      CAM: normalizeComponent(creation90, 0.96) * 0.36 + normalizeComponent(goals90, 0.42) * 0.28 + normalizeComponent(assists90, 0.34) * 0.22 + sampleReliability(player) * 14,
      Winger: normalizeComponent(goals90, 0.55) * 0.34 + normalizeComponent(assists90, 0.32) * 0.24 + normalizeComponent(shots90, 3.5) * 0.18 + normalizeComponent(sot90, 1.45) * 0.12 + sampleReliability(player) * 12,
      ST: normalizeComponent(goals90, 0.72) * 0.48 + normalizeComponent(assists90, 0.24) * 0.14 + normalizeComponent(shots90, 4.0) * 0.18 + normalizeComponent(sot90, 1.75) * 0.1 + sampleReliability(player) * 10
    };

    return clamp(roleScores[role] ?? roleScores.CM, 0, 100);
  }

  function careerQualityScore(player: Player) {
    const goals = numericStat(player, "goals");
    const assists = numericStat(player, "assists");
    const appearances = numericStat(player, "appearances");
    const minutes = numericStat(player, "minutes");
    const role = playerRole(player);
    const attackingValue = goals * (role === "ST" ? 1.15 : 1) + assists * (["CAM", "CM", "Winger"].includes(role) ? 1.1 : 0.75);
    const defensiveValue = numericStat(player, "cleanSheets") * (["GK", "CB", "FB"].includes(role) ? 0.65 : 0.2);
    const careerValue = attackingValue + defensiveValue + Math.min(appearances, 260) * 0.08 + Math.min(minutes, 18000) * 0.0012;
    return normalizeComponent(careerValue, 115);
  }

  function consistencyScore(player: Player) {
    const appearances = numericStat(player, "appearances");
    const minutes = numericStat(player, "minutes");
    const starts = numericStat(player, "starts");
    const avgMinutes = appearances > 0 ? minutes / appearances : 0;
    const availability = normalizeComponent(Math.min(appearances, 180), 180) * 0.42;
    const usage = normalizeComponent(avgMinutes, 76) * 0.36;
    const starter = normalizeComponent(starts || appearances * 0.55, 150) * 0.22;
    return clamp(availability + usage + starter, 0, 100);
  }

  function recentFormScore(player: Player) {
    const reliability = sampleReliability(player) * 100;
    const output = normalizeComponent(
      per90(player, numericStat(player, "goals") + numericStat(player, "assists") * 0.7),
      playerRole(player) === "ST" ? 0.9 : 0.65
    );
    return clamp(output * 0.56 + reliability * 0.44, 0, 100);
  }

  function rawIogComposite(player: Player) {
    const score = (
      positionPerformanceScore(player) * 0.5 +
      clubCompetitionScore(player) * 0.2 +
      nationStrengthScore(player) * 0.15 +
      careerQualityScore(player) * 0.1 +
      recentFormScore(player) * 0.05
    );

    return score + (hasSuperstarOverride(player) ? 8 : 0);
  }

  function worldCupIogRankings() {
    if (iogRankingsCache) return iogRankingsCache;

    const pool = players.filter((player) => getCompetition(player) === "World Cup");
    iogRankingsCache = pool
      .map((player) => ({
        id: String(player.id),
        score: rawIogComposite(player),
        performance: positionPerformanceScore(player),
        strength: strengthMultiplier(player),
        career: careerQualityScore(player),
        consistency: consistencyScore(player)
      }))
      .sort((a, b) => a.score - b.score);
    return iogRankingsCache;
  }

  function iogCap(player: Player) {
    if (hasSuperstarOverride(player)) return 99;

    const tier = nationTier(player);
    const consistency = consistencyScore(player);
    const regularMajorClubProfile =
      clubCompetitionScore(player) >= 95 &&
      numericStat(player, "minutes") >= 8000 &&
      numericStat(player, "appearances") >= 120 &&
      consistency >= 52;

    if (tier === 1) return 99;
    if (tier === 2) return 92;
    return regularMajorClubProfile ? 87 : 85;
  }

  function scoreFromGlobalRank(topRank: number) {
    if (topRank < 3) return 99;
    if (topRank < 10) return 98 - Math.floor((topRank - 3) / 3);
    if (topRank < 25) return 95 - Math.floor((topRank - 10) / 5);
    if (topRank < 80) return 92 - Math.floor((topRank - 25) / 14);
    if (topRank < 220) return 88 - Math.floor((topRank - 80) / 35);
    if (topRank < 650) return 84 - Math.floor((topRank - 220) / 86);
    if (topRank < 1400) return 79 - Math.floor((topRank - 650) / 150);
    if (topRank < 2100) return 74 - Math.floor((topRank - 1400) / 175);
    return 69;
  }

  const iogOverrides: Record<string, number> = {
    "lionel messi": 90,
    "l messi": 90,
    "cristiano ronaldo": 79,
    "c ronaldo": 79,
    "hugo ekitike": 86,
    "h ekitike": 86
  };

  function playerNameKey(name: string) {
    return String(name)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-zA-Z0-9]+/g, " ")
      .trim()
      .toLowerCase();
  }

  function iogBreakdown(player: Player) {
    const role = playerRole(player);
    const overall = numericStat(player, "overall", "iog");
    const potential = numericStat(player, "potential");
    const base = overall || numericStat(player, "iog") || 70;
    const goals90 = per90(player, numericStat(player, "goals"));
    const assists90 = per90(player, numericStat(player, "assists"));
    const shots90 = per90(player, numericStat(player, "shots"));
    const tackles90 = per90(player, numericStat(player, "tackles", "tacklesWon"));
    const interceptions90 = per90(player, numericStat(player, "interceptions"));
    const keyPasses90 = per90(player, numericStat(player, "keyPasses", "key_passes", "crosses"));
    const progression90 = per90(player, numericStat(player, "progressivePasses", "progressive_passes", "progressiveCarries", "progressive_carries"));
    const savePct = numericStat(player, "savePct", "save_pct");
    const cleanSheets90 = per90(player, numericStat(player, "cleanSheets", "clean_sheets"));
    const reliability = consistencyScore(player);
    const strength = clubCompetitionScore(player);
    const positionFitScore = getPositions(player).length ? 80 + Math.min(getPositions(player).length, 3) * 4 : 72;

    const goalThreat = role === "GK"
      ? normalizeComponent(cleanSheets90, 0.45) * 0.8
      : clamp(normalizeComponent(goals90, role === "ST" ? 0.7 : 0.45) * 0.58 + normalizeComponent(shots90, role === "ST" ? 4 : 3) * 0.22 + base * 0.2);
    const chanceCreation = clamp(normalizeComponent(assists90, 0.36) * 0.5 + normalizeComponent(keyPasses90, 2.2) * 0.34 + base * 0.16);
    const ballProgression = clamp(normalizeComponent(progression90, 7.2) * 0.6 + (potential || base) * 0.18 + base * 0.22);
    const ballRetention = clamp(base * 0.62 + reliability * 0.28 + strength * 0.1);
    const defensiveValue = role === "GK"
      ? clamp((savePct || base) * 0.52 + cleanSheets90 * 70 + base * 0.18)
      : clamp(normalizeComponent(tackles90 + interceptions90, ["CB", "CDM", "FB"].includes(role) ? 4 : 2.2) * 0.68 + base * 0.2 + reliability * 0.12);
    const pressResistance = clamp(base * 0.5 + chanceCreation * 0.18 + ballRetention * 0.24 + reliability * 0.08);
    const possessionInfluence = clamp(ballRetention * 0.36 + chanceCreation * 0.22 + ballProgression * 0.28 + reliability * 0.14);
    const buildup = clamp(ballProgression * 0.38 + possessionInfluence * 0.32 + defensiveValue * (["CB", "CDM", "FB", "GK"].includes(role) ? 0.2 : 0.08) + base * 0.1);
    const transitionImpact = clamp(goalThreat * 0.34 + ballProgression * 0.26 + defensiveValue * 0.18 + strength * 0.22);
    const offBallMovement = clamp(goalThreat * 0.34 + reliability * 0.24 + base * 0.3 + positionFitScore * 0.12);
    const bigMatch = clamp(strength * 0.34 + nationStrengthScore(player) * 0.2 + careerQualityScore(player) * 0.22 + base * 0.24);

    return {
      goalThreat: Math.round(goalThreat),
      chanceCreation: Math.round(chanceCreation),
      ballProgression: Math.round(ballProgression),
      ballRetention: Math.round(ballRetention),
      defensiveValue: Math.round(defensiveValue),
      pressResistance: Math.round(pressResistance),
      possessionInfluence: Math.round(possessionInfluence),
      buildUpContribution: Math.round(buildup),
      transitionImpact: Math.round(transitionImpact),
      offBallMovement: Math.round(offBallMovement),
      reliability: Math.round(reliability),
      bigMatchInfluence: Math.round(bigMatch),
      positionFit: Math.round(positionFitScore)
    };
  }

  function deepIogComposite(player: Player) {
    const b = iogBreakdown(player);
    const role = playerRole(player);
    const weights: Record<string, Partial<Record<keyof ReturnType<typeof iogBreakdown>, number>>> = {
      GK: { defensiveValue: 0.28, reliability: 0.16, buildUpContribution: 0.14, bigMatchInfluence: 0.14, positionFit: 0.12, ballRetention: 0.08, possessionInfluence: 0.08 },
      CB: { defensiveValue: 0.28, buildUpContribution: 0.16, reliability: 0.14, ballRetention: 0.12, bigMatchInfluence: 0.12, possessionInfluence: 0.1, positionFit: 0.08 },
      FB: { defensiveValue: 0.2, ballProgression: 0.16, chanceCreation: 0.14, transitionImpact: 0.13, reliability: 0.12, buildUpContribution: 0.1, positionFit: 0.08, bigMatchInfluence: 0.07 },
      CDM: { defensiveValue: 0.22, ballRetention: 0.18, possessionInfluence: 0.17, buildUpContribution: 0.14, ballProgression: 0.12, reliability: 0.09, bigMatchInfluence: 0.08 },
      CM: { possessionInfluence: 0.2, ballProgression: 0.16, chanceCreation: 0.14, ballRetention: 0.14, buildUpContribution: 0.12, reliability: 0.1, defensiveValue: 0.08, bigMatchInfluence: 0.06 },
      CAM: { chanceCreation: 0.22, goalThreat: 0.16, possessionInfluence: 0.14, pressResistance: 0.12, ballProgression: 0.12, offBallMovement: 0.1, bigMatchInfluence: 0.08, reliability: 0.06 },
      Winger: { goalThreat: 0.22, chanceCreation: 0.18, transitionImpact: 0.15, offBallMovement: 0.13, ballProgression: 0.12, pressResistance: 0.08, bigMatchInfluence: 0.07, reliability: 0.05 },
      ST: { goalThreat: 0.3, offBallMovement: 0.16, transitionImpact: 0.14, bigMatchInfluence: 0.12, reliability: 0.1, chanceCreation: 0.08, positionFit: 0.06, pressResistance: 0.04 }
    };
    const roleWeights = weights[role] ?? weights.CM;
    return Object.entries(roleWeights).reduce((sum, [key, weight]) => sum + b[key as keyof typeof b] * (weight ?? 0), 0);
  }

  function hasDetailedPerformanceData(player: Player) {
    return [
      "goals",
      "assists",
      "shots",
      "shotsOnTarget",
      "shots_on_target",
      "tackles",
      "tacklesWon",
      "interceptions",
      "keyPasses",
      "key_passes",
      "saves",
      "savePct",
      "save_pct",
      "cleanSheets",
      "clean_sheets"
    ].some((key) => numericStat(player, key) > 0);
  }

  function calibratedFc26Iog(player: Player) {
    const role = playerRole(player);
    const overall = numericStat(player, "overall");
    const importedIog = numericStat(player, "iog");
    const baseRating = overall > 0 && importedIog > 0
      ? Math.round(overall * 0.72 + importedIog * 0.28)
      : Math.round(overall || importedIog || 70);

    let score = baseRating;

    if (hasDetailedPerformanceData(player)) {
      score = Math.round(baseRating * 0.82 + deepIogComposite(player) * 0.18);
    }

    if (role === "GK") {
      score = Math.max(score, overall ? overall - 2 : score);
      const savePct = numericStat(player, "savePct", "save_pct");
      if (savePct >= 78) score += 2;
      if (numericStat(player, "cleanSheets", "clean_sheets") > 10) score += 1;
    }

    if (["ST", "Winger", "CAM"].includes(role) && overall >= 84) score += 1;
    if (["CB", "CDM", "CM"].includes(role) && overall >= 84) score += 1;
    if (overall >= 70) score = Math.max(score, overall - 5);

    return clamp(score, 50, 99);
  }

  function calculatePlayerIog(player: Player) {
    const override = iogOverrides[playerNameKey(player.name)];
    if (override !== undefined) return override;

    if (player.dataSource === "fc26") {
      return calibratedFc26Iog(player);
    }

    const rankings = worldCupIogRankings();
    if (rankings.length < 4) return Math.max(50, Math.min(99, Math.round(player.iog ?? 70)));

    const index = Math.max(0, rankings.findIndex((peer) => peer.id === String(player.id)));
    const topRank = rankings.length - 1 - index;
    const rankedScore = scoreFromGlobalRank(topRank);
    const superstarGatedScore = rankedScore >= 95 && !hasSuperstarOverride(player) ? 94 : rankedScore;
    return clamp(superstarGatedScore, 50, iogCap(player));
  }

  function getIog(player: Player) {
    const cacheKey = String(player.id);
    const cached = iogCache.get(cacheKey);
    if (cached !== undefined) return cached;
    const score = calculatePlayerIog(player);
    iogCache.set(cacheKey, score);
    return score;
  }

  function statNumber(player: Player, key: "minutes" | "goals" | "assists") {
    const value = player[key];
    return typeof value === "number" && Number.isFinite(value) ? value : 0;
  }

  function sortOptions(pool: DraftOption[], selectedSort: SortKey) {
    return [...pool].sort((a, b) => {
      if (selectedSort === "iog_asc") return a.adjustedIog - b.adjustedIog || a.name.localeCompare(b.name);
      if (selectedSort === "name") return a.name.localeCompare(b.name);
      if (selectedSort === "best_fit") return b.slotCount - a.slotCount || b.adjustedIog - a.adjustedIog;
      if (selectedSort === "goals") return statNumber(b, "goals") - statNumber(a, "goals") || b.adjustedIog - a.adjustedIog;
      if (selectedSort === "assists") return statNumber(b, "assists") - statNumber(a, "assists") || b.adjustedIog - a.adjustedIog;
      return b.adjustedIog - a.adjustedIog;
    });
  }

  function breakdownRows(player: Player) {
    const b = iogBreakdown(player);
    return [
      ["Goal Threat", b.goalThreat],
      ["Creation", b.chanceCreation],
      ["Progression", b.ballProgression],
      ["Retention", b.ballRetention],
      ["Defending", b.defensiveValue],
      ["Press Resistance", b.pressResistance],
      ["Possession", b.possessionInfluence],
      ["Build-up", b.buildUpContribution],
      ["Transition", b.transitionImpact],
      ["Off-ball", b.offBallMovement],
      ["Big Match", b.bigMatchInfluence],
      ["Consistency", b.reliability],
      ["Position Fit", b.positionFit]
    ];
  }

  function initials(name: string) {
    return name
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0])
      .join("")
      .toUpperCase();
  }

  function getCompetition(player: Player) {
    return player.competition ?? (player.league === "World Cup" ? "World Cup" : "Draft");
  }

  function getUniverseCompetition(value: Universe) {
    return value.competition ?? (value.league === "World Cup" ? "World Cup" : "Draft");
  }

  function isWorldCupUniverse(value: Universe) {
    return getUniverseCompetition(value) === "World Cup";
  }

  function playerTeam(player: Player) {
    return player.team ?? player.club ?? player.nation ?? "";
  }

  function normalizeKey(value: unknown) {
    return String(value ?? "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/&/g, " and ")
      .replace(/[^a-zA-Z0-9]+/g, " ")
      .trim()
      .toLowerCase();
  }

  function normalizeLeagueName(value: unknown): ClubLeague | "" {
    const key = normalizeKey(value);
    if (["premier league", "english premier league", "england premier league"].includes(key)) return "Premier League";
    if (["la liga", "laliga", "spanish la liga", "spain la liga"].includes(key)) return "La Liga";
    if (["serie a", "italy serie a", "italian serie a"].includes(key)) return "Serie A";
    if (["bundesliga", "german bundesliga", "1 bundesliga"].includes(key)) return "Bundesliga";
    if (["ligue 1", "ligue1", "france ligue 1", "french ligue 1"].includes(key)) return "Ligue 1";
    return "";
  }

  const clubLeagueByName: Record<string, ClubLeague> = {
    arsenal: "Premier League", "aston villa": "Premier League", bournemouth: "Premier League", brentford: "Premier League",
    brighton: "Premier League", "brighton and hove albion": "Premier League", burnley: "Premier League", chelsea: "Premier League",
    "crystal palace": "Premier League", everton: "Premier League", fulham: "Premier League", "leeds united": "Premier League",
    liverpool: "Premier League", "manchester city": "Premier League", "manchester united": "Premier League", "newcastle united": "Premier League",
    "nottingham forest": "Premier League", sunderland: "Premier League", "tottenham hotspur": "Premier League", tottenham: "Premier League",
    "west ham united": "Premier League", "wolverhampton wanderers": "Premier League", wolves: "Premier League",

    "real madrid": "La Liga", "real madrid cf": "La Liga", barcelona: "La Liga", "fc barcelona": "La Liga",
    "atletico madrid": "La Liga", "atletico de madrid": "La Liga", "athletic club": "La Liga", "real sociedad": "La Liga",
    villarreal: "La Liga", "villarreal cf": "La Liga", valencia: "La Liga", "valencia cf": "La Liga",
    sevilla: "La Liga", "sevilla fc": "La Liga", "real betis": "La Liga", "real betis balompie": "La Liga",
    "celta vigo": "La Liga", "rc celta": "La Liga", getafe: "La Liga", osasuna: "La Liga", mallorca: "La Liga",
    "rayo vallecano": "La Liga", girona: "La Liga", "girona fc": "La Liga", alaves: "La Liga", espanyol: "La Liga",
    elche: "La Liga", levante: "La Liga", oviedo: "La Liga", "real oviedo": "La Liga", "ud las palmas": "La Liga",

    inter: "Serie A", "inter milan": "Serie A", internazionale: "Serie A", "ac milan": "Serie A", milan: "Serie A",
    juventus: "Serie A", napoli: "Serie A", roma: "Serie A", lazio: "Serie A", atalanta: "Serie A",
    fiorentina: "Serie A", bologna: "Serie A", torino: "Serie A", udinese: "Serie A", genoa: "Serie A",
    parma: "Serie A", como: "Serie A", cagliari: "Serie A", verona: "Serie A", lecce: "Serie A", pisa: "Serie A",
    sassuolo: "Serie A", cremonese: "Serie A",

    "bayern munich": "Bundesliga", "fc bayern munchen": "Bundesliga", "fc bayern münchen": "Bundesliga",
    "borussia dortmund": "Bundesliga", dortmund: "Bundesliga", "bayer leverkusen": "Bundesliga", "bayer 04 leverkusen": "Bundesliga",
    "rb leipzig": "Bundesliga", "rasenballsport leipzig": "Bundesliga", "eintracht frankfurt": "Bundesliga",
    "vfb stuttgart": "Bundesliga", freiburg: "Bundesliga", mainz: "Bundesliga", "werder bremen": "Bundesliga",
    "sv werder bremen": "Bundesliga", "borussia monchengladbach": "Bundesliga", "borussia m gladbach": "Bundesliga",
    "union berlin": "Bundesliga", wolfsburg: "Bundesliga", augsburg: "Bundesliga", hoffenheim: "Bundesliga",
    "tsg 1899 hoffenheim": "Bundesliga", "st pauli": "Bundesliga", heidenheim: "Bundesliga", koln: "Bundesliga",
    "1 fc koln": "Bundesliga", hamburg: "Bundesliga", "hamburger sv": "Bundesliga", "vfl bochum 1848": "Bundesliga",
    "holstein kiel": "Bundesliga",

    "paris saint germain": "Ligue 1", psg: "Ligue 1", marseille: "Ligue 1", "olympique de marseille": "Ligue 1",
    monaco: "Ligue 1", "as monaco": "Ligue 1", lille: "Ligue 1", lyon: "Ligue 1", "olympique lyonnais": "Ligue 1",
    lens: "Ligue 1", nice: "Ligue 1", strasbourg: "Ligue 1", brest: "Ligue 1", rennes: "Ligue 1",
    nantes: "Ligue 1", toulouse: "Ligue 1", "toulouse fc": "Ligue 1", auxerre: "Ligue 1", "le havre": "Ligue 1",
    angers: "Ligue 1", metz: "Ligue 1", lorient: "Ligue 1", "paris fc": "Ligue 1", "estac troyes": "Ligue 1"
  };

  function normalizeClubName(value: unknown) {
    return normalizeKey(value)
      .replace(/\b(fc|cf|sc|afc|ac|as|rc|sv|vfl|club)\b/g, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function domesticClub(player: Player) {
    return player.domesticClub ?? player.originalClub ?? player.club;
  }

  function displayTeamContext(player: Player) {
    return (draftMode === "et" || draftMode === "invinciblesClub") ? domesticClub(player) : player.nation ?? player.club;
  }

  function chemistryTeamContext(player: Player) {
    return (draftMode === "et" || draftMode === "invinciblesClub") ? domesticClub(player) : player.nation ?? player.club;
  }

  function inferredClubLeague(player: Player): ClubLeague | "" {
    const direct = normalizeLeagueName(player.domesticLeague ?? player.league);
    if (direct) return direct;
    const raw = normalizeKey(domesticClub(player));
    const normalized = normalizeClubName(domesticClub(player));
    return clubLeagueByName[raw] ?? clubLeagueByName[normalized] ?? "";
  }

  function isInvinciblesEligible(player: Player) {
    const league = inferredClubLeague(player);
    return Boolean(league && selectedInvinciblesConfig.leagues.includes(league));
  }

  function isEtEligible(player: Player) {
    return Boolean(inferredClubLeague(player));
  }

  function matchesUniverse(player: Player) {
    const competition = getUniverseCompetition(universe);
    const team = playerTeam(player);
    const teamMatches = team === universe.club || player.club === universe.club || player.nation === universe.club;

    return (
      teamMatches &&
      player.league === universe.league &&
      player.era === universe.era &&
      getCompetition(player) === competition
    );
  }

  function universeTitle(value: Universe) {
    const competition = getUniverseCompetition(value);
    return `${value.era} Era • ${value.club} • ${competition === "World Cup" ? "World Cup" : value.league}`;
  }

  function getHeaderTitle() {
    if (screen === "menu") return "Galactico11";
    if (screen === "mode") return "Choose mode";
    if (screen === "etIntro") return "SIGNAL CONTACT";
    if (screen === "clubFormat" && draftMode === "invinciblesClub") return "INVINCIBLES";
    if (screen === "clubFormat") return "Club Football";
    if (screen === "formation") {
      if (draftMode === "et") return "Signal Contact • ET Mode";
      if (draftMode === "invinciblesClub") return `Invincibles • ${selectedInvinciblesConfig.shortLabel}`;
      if (draftMode === "worldcup") return "World Cup 2026";
      return "Choose formation";
    }
    if (screen === "draft") {
      if (draftMode === "et") return `Signal Contact • ET Mode • ${picked.length}/11 selected`;
      if (draftMode === "invinciblesClub") return `Invincibles • ${selectedInvinciblesConfig.shortLabel} • ${picked.length}/11 selected`;
      return `${currentUniverseTitle} • ${picked.length}/11 selected`;
    }
    if (screen === "bench") return "Bench Round";
    return "Galactico11";
  }

  function universeKey(value: Universe) {
    return `${value.league}|${value.club}|${value.era}|${getUniverseCompetition(value)}`;
  }

  function flagForNation(nation: string) {
    const codes: Record<string, string> = {
      Algeria: "DZ",
      Argentina: "AR",
      Brazil: "BR",
      England: "GB",
      France: "FR",
      Germany: "DE",
      Japan: "JP",
      Mexico: "MX",
      Morocco: "MA",
      Netherlands: "NL",
      Portugal: "PT",
      Spain: "ES"
    };
    const code = codes[nation];
    if (!code) return "🏳";
    return code
      .split("")
      .map((char) => String.fromCodePoint(127397 + char.charCodeAt(0)))
      .join("");
  }

  function buildWorldCupNations(): NationCard[] {
    const grouped = new Map<string, Player[]>();

    for (const player of players.filter((item) => getCompetition(item) === "World Cup")) {
      const nation = player.nation ?? player.club;
      if (!nation) continue;
      grouped.set(nation, [...(grouped.get(nation) ?? []), player]);
    }

    return Array.from(grouped.entries())
      .map(([name, roster]) => ({
        name,
        flag: flagForNation(name),
        playerCount: roster.length,
        avgIog: formatIoG(roster.reduce((sum, player) => sum + (player.iog ?? 0), 0) / Math.max(roster.length, 1)),
        imported: true
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  function universeRosterSize(value: Universe) {
    return players.filter((player) =>
      player.league === value.league &&
      player.club === value.club &&
      player.era === value.era &&
      getCompetition(player) === getUniverseCompetition(value)
    ).length;
  }

  function isNationalTeamCompetition(value: Universe) {
    const competition = getUniverseCompetition(value);
    return ["World Cup", "FIFA World Cup", "Copa America", "African Cup of Nations"].includes(competition) ||
      ["World Cup", "FIFA World Cup", "Copa America", "African Cup of Nations"].includes(value.league);
  }

  function validClubUniverses() {
    return classicUniverses.filter((item) =>
      !isNationalTeamCompetition(item) &&
      (supportedClubCompetitions.has(item.league) || supportedClubCompetitions.has(getUniverseCompetition(item)))
    );
  }

  function clubLeagueUniverses() {
    return validClubUniverses().filter((item) => item.league === selectedClubLeague);
  }

  function championsLeagueUniverses() {
    const byClub = new Map<string, Universe>();
    const sorted = [...validClubUniverses()]
      .filter((item) => item.league === "Champions League" || getUniverseCompetition(item) === "Champions League")
      .sort((a, b) => universeRosterSize(b) - universeRosterSize(a));

    for (const candidate of sorted) {
      const key = candidate.club;
      if (!byClub.has(key)) byClub.set(key, candidate);
      if (byClub.size >= 32) break;
    }

    return Array.from(byClub.values()).slice(0, 32);
  }

  function activeClubUniverses() {
    if (clubFormat === "champions") {
      const championsPool = championsLeagueUniverses();
      return championsPool.length > 0 ? championsPool : validClubUniverses();
    }

    return clubLeagueUniverses();
  }

  function invinciblesClubUniverses(): Universe[] {
    const byClub = new Map<string, ClubLeague>();
    for (const player of invinciblesPlayers()) {
      const club = domesticClub(player);
      if (!club || usedInvinciblesClubs.has(club)) continue;
      if (!byClub.has(club)) {
        const league = inferredClubLeague(player);
        if (league) byClub.set(club, league);
      }
    }
    return Array.from(byClub.entries()).map(([club, league]) => ({ league, club, era: "2020s", competition: "Invincibles" }));
  }

  function activeUniverses() {
    if (draftMode === "et") return [etUniverse];
    if (draftMode === "invinciblesClub") return isGoldenRound ? [etUniverse] : invinciblesClubUniverses();
    if (draftMode === "worldcup" && worldCupUniverses.length > 0) return worldCupUniverses;
    const clubPool = activeClubUniverses();
    if (clubPool.length > 0) return clubPool;
    return validClubUniverses();
  }

  function getSlotRole(slot: Slot) {
    return normalizePosition(slot.position || slot.label || slot.id);
  }

  function getFormationSlots() {
    return slots.map((slot) => ({
      id: slot.id,
      label: slot.label,
      role: getSlotRole(slot),
      filled: Boolean(getPlayer(slot.id))
    }));
  }

  function canAssignPlayerToSlot(player: Player, slot: Slot) {
    if (getPlayer(slot.id)) return false;
    return isPlayerCompatibleWithSlot(player, slot);
  }

  function isPlayerCompatibleWithSlot(player: Player, slot: Slot) {
    const slotRole = getSlotRole(slot);
    return getPositions(player).some((position) => compatibleSlotRoles(position).includes(slotRole));
  }

  function getCompatibleSlots(player: Player) {
    return slots.filter((slot) => canAssignPlayerToSlot(player, slot));
  }

  function warnIfNoCompatibleSlots(player: Player, compatible: Slot[]) {
    const playerRoles = getPositions(player);
    const matchingFilledSlots = slots.filter((slot) => isPlayerCompatibleWithSlot(player, slot) && getPlayer(slot.id));

    if (compatible.length === 0 && playerRoles.length > 0 && emptySlots.length > 0) {
      console.warn("No compatible slots found", player.name, player.positions);
      console.warn("No compatible slot found for player.", {
        player: player.name,
        positions: player.positions,
        normalizedPositions: playerRoles,
        formationSlots: getFormationSlots(),
        matchingFilledSlots
      });
      fallbackNotice = "No compatible slot found for player.";
    }
  }

  function hasOpenSlot(player: Player) {
    return getCompatibleSlots(player).length > 0;
  }

  function hasPerfectFit(player: Player) {
    const primary = getPositions(player)[0];
    if (!primary) return false;
    return emptySlots.some((slot) => getSlotRole(slot) === normalizePosition(primary));
  }

  function eligibleSlotLabels(player: Player) {
    const labels = getCompatibleSlots(player).map((slot) => slot.label);
    return Array.from(new Set(labels));
  }

  function draftLabel(player: DraftOption) {
    if (isGoldenRound) return "Golden Pick";
    if (isMysteryRound) return "Mystery Pick";
    if (player.slotCount === 0) return "Risk Pick";
    if (String(player.era).startsWith("199") || String(player.era).startsWith("200")) return "Legacy Pick";
    return "Available Pick";
  }

  function isMysteryCardHidden(player: Player) {
    return isMysteryRound;
  }

  function mysteryLabel(): string {
    return draftMode === "et" ? "SIGNAL OBSCURED" : "MYSTERY";
  }

  function isMysteryIdentityHidden(player: PickedPlayer) {
    return Boolean(player.mysteryPick) && !revealedMysteryPlayerIds.includes(String(player.id));
  }

  function isPicked(player: Player) {
    return pickedIds.has(String(player.id));
  }

  function shuffle<T>(arr: T[]) {
    return [...arr].sort(() => Math.random() - 0.5);
  }

  function unpickedPlayers() {
    return players.filter((p) => !isPicked(p));
  }

  function invinciblesPlayers() {
    return unpickedPlayers().filter(isInvinciblesEligible);
  }

  function etPlayers() {
    return unpickedPlayers().filter(isEtEligible);
  }

  function availableUniversePlayers() {
    if (draftMode === "et") return etPlayers();
    if (draftMode === "invinciblesClub") {
      if (isGoldenRound) return invinciblesPlayers();
      return invinciblesPlayers().filter((p) => domesticClub(p) === universe.club);
    }
    const indexed = universePlayerIndex.get(universeKey(universe)) ?? [];
    return indexed.filter((player) => !isPicked(player));
  }

  function compatibleUniversePlayers() {
    return availableUniversePlayers().filter((p) => hasOpenSlot(p));
  }

  function availableModePlayers() {
    if (draftMode === "et") return etPlayers();
    if (draftMode === "invinciblesClub") return invinciblesPlayers();
    const activeKeys = new Set(activeUniverses().map(universeKey));
    return unpickedPlayers().filter((player) => {
      const key = `${player.league}|${player.club}|${player.era}|${getCompetition(player)}`;
      return activeKeys.has(key);
    });
  }

  function compatibleModePlayers() {
    return availableModePlayers().filter((p) => hasOpenSlot(p));
  }

  function toOption(player: Player): DraftOption {
    const slotCount = getCompatibleSlots(player).length;

    return {
      ...player,
      adjustedIog: getIog(player),
      emergency: false,
      slotCount
    };
  }

  function benchRoleMatches(player: Player, roles: string[]) {
    const positions = getPositions(player);
    return positions.some((position) => compatibleSlotRoles(position).some((role) => roles.includes(role)) || roles.includes(normalizePosition(position)));
  }

  function bestBenchCandidate(role: BenchSub["benchRole"], roles: string[], selected: Set<string>) {
    const candidates = availableModePlayers()
      .filter((player) => !selected.has(String(player.id)) && benchRoleMatches(player, roles))
      .map((player) => ({ ...toOption(player), benchRole: role }) as BenchSub)
      .sort((a, b) => b.adjustedIog - a.adjustedIog);

    const pick = candidates[0];
    if (pick) selected.add(String(pick.id));
    return pick;
  }

  function buildBenchCandidates(): BenchSub[] {
    const selected = new Set([...picked.map((player) => String(player.id)), ...bench.map((player) => String(player.id))]);
    const roles: Array<{ label: BenchSub["benchRole"]; positions: string[] }> = [
      { label: "Backup GK", positions: ["GK"] },
      { label: "Defensive Cover", positions: ["CB", "RB", "LB", "RWB", "LWB", "CDM"] },
      { label: "Midfield Control", positions: ["CDM", "CM", "CAM"] },
      { label: "Attacking Wildcard", positions: ["ST", "LW", "RW", "CAM"] },
      { label: "Utility Player", positions: ["RB", "LB", "CM", "RM", "LM", "RW", "LW"] }
    ];

    return roles
      .map((role) => bestBenchCandidate(role.label, role.positions, selected))
      .filter(Boolean) as BenchSub[];
  }

  function calculateBenchImpact(subs: BenchSub[]) {
    if (!subs.length) {
      return {
        strength: 0,
        flexibility: "Optional" as const,
        lateThreat: 0,
        fatigue: 0,
        note: "No bench selected. The XI must survive without a safety net."
      };
    }

    const avg = subs.reduce((sum, p) => sum + p.adjustedIog, 0) / subs.length;
    const filled = subs.length;
    const roleCoverage = new Set(subs.map((p) => p.benchRole)).size;
    const attIog = subs.find((p) => p.benchRole === "Attacking Wildcard")?.adjustedIog ?? 0;
    const defIog = subs.find((p) => ["Backup GK", "Defensive Cover"].includes(p.benchRole))?.adjustedIog ?? 0;

    // Strength: IoG 70→24%, 78→50%, 84→69%, 90→88%
    const strength = Math.round(clamp((avg - 65) * 3.2, 0, 100));

    // Late threat: capped at 20%
    const lateThreat = Math.round(clamp(Math.max(0, (Math.max(attIog, avg) - 70) * 0.88), 0, 20));

    // Fatigue: filled slots + role coverage + defensive depth, capped at 28%
    const fatigue = Math.round(clamp(filled * 3.2 + roleCoverage * 1.6 + defIog * 0.055, 0, 28));

    const flexibility = roleCoverage >= 5 ? "High" : roleCoverage >= 3 ? "Medium" : "Low";

    const note = strength >= 72
      ? "Your bench gives the XI a second plan. Late-game pressure becomes survivable."
      : strength >= 48
        ? "Useful options exist, but the bench lacks coverage in key zones."
        : "The starters carry the project. One injury or extra-time spell could expose the bench.";

    return { strength, flexibility, lateThreat, fatigue, note };
  }

  const benchRoleSlots: Array<{ role: BenchSub["benchRole"]; label: string; positions: string[] }> = [
    { role: "Backup GK", label: "GK", positions: ["GK"] },
    { role: "Defensive Cover", label: "DEF", positions: ["CB", "RB", "LB", "RWB", "LWB", "CDM"] },
    { role: "Midfield Control", label: "MID", positions: ["CDM", "CM", "CAM", "LM", "RM"] },
    { role: "Attacking Wildcard", label: "ATT", positions: ["ST", "CF", "LW", "RW", "CAM"] },
    { role: "Utility Player", label: "FLEX", positions: [] }
  ];

  function startBenchRound() {
    benchCandidates = [];
    benchSearch = "";
    const all = availableModePlayers().map((p) => toOption(p));
    // Bench pool: weighted sampling so it feels like squad depth, not a second Ballon d'Or XI
    const common = shuffle(all.filter((p) => p.adjustedIog < 82)).slice(0, 26);
    const good   = shuffle(all.filter((p) => p.adjustedIog >= 82 && p.adjustedIog < 86)).slice(0, 12);
    const rare   = shuffle(all.filter((p) => p.adjustedIog >= 86 && p.adjustedIog < 88)).slice(0, 4);
    const elite  = shuffle(all.filter((p) => p.adjustedIog >= 88 && p.adjustedIog < 90)).slice(0, 1);
    const pool = [...common, ...good, ...rare, ...elite].sort((a, b) => b.adjustedIog - a.adjustedIog);
    benchPool = pool;
    if (pool.length === 0) {
      startPostDraftAnalysis();
      return;
    }
    screen = "bench";
  }

  function benchRoleForPlayer(player: DraftOption): BenchSub["benchRole"] {
    const pos = getPositions(player).map((p) => normalizePosition(p));
    const isGK = pos.includes("GK");
    const taken = new Set(benchCandidates.map((c) => c.benchRole));

    if (isGK) {
      // GK goes to GK slot, then FLEX, then any remaining (never outfield-specific slots)
      if (!taken.has("Backup GK")) return "Backup GK";
      if (!taken.has("Utility Player")) return "Utility Player";
      return benchRoleSlots.find((s) => !taken.has(s.role))?.role ?? "Utility Player";
    }

    // Outfield: try best-matching specific slot (skip GK slot always)
    for (const slot of benchRoleSlots) {
      if (slot.role === "Backup GK") continue;
      if (taken.has(slot.role)) continue;
      if (slot.positions.length === 0 || slot.positions.some((p) => pos.includes(p))) return slot.role;
    }

    // No position-matched slot — use FLEX if free, then any non-GK slot
    if (!taken.has("Utility Player")) return "Utility Player";
    const nonGkFree = benchRoleSlots.find((s) => s.role !== "Backup GK" && !taken.has(s.role));
    return nonGkFree?.role ?? "Utility Player";
  }

  function addToBench(player: DraftOption) {
    if (benchCandidates.length >= 5) return;
    const role = benchRoleForPlayer(player);
    benchCandidates = [...benchCandidates, { ...player, benchRole: role }];
    benchPool = benchPool.filter((p) => String(p.id) !== String(player.id));
  }

  function removeFromBench(index: number) {
    const removed = benchCandidates[index];
    if (!removed) return;
    benchCandidates = benchCandidates.filter((_, i) => i !== index);
    benchPool = [{ ...removed }, ...benchPool].sort((a, b) => b.adjustedIog - a.adjustedIog);
  }

  function acceptBench() {
    bench = [...benchCandidates];
    startPostDraftAnalysis();
  }

  function skipBench() {
    bench = [];
    startPostDraftAnalysis();
  }

  function getPickReaction(player: PickedPlayer) {
    const role = normalizePosition(player.assignedPosition);
    if (player.mysteryPick) return "Hidden pick secured. Phoebe will reveal the identity later.";
    if (role === "GK" || ["CB", "LB", "RB", "LWB", "RWB"].includes(role)) return `Defense stabilised by ${player.assignedPosition}. Watch the triangle pull backward.`;
    if (["CM", "CDM", "CAM", "LM", "RM"].includes(role)) return "Midfield pressure absorbed. Libra now matters more than star power.";
    return "Attack upgraded. Now protect chemistry before the XI tilts too far forward.";
  }

  function signedDecimal(value: number, suffix = "") {
    const rounded = Math.round(value * 10) / 10;
    return `${rounded > 0 ? "+" : ""}${rounded.toFixed(Math.abs(rounded) >= 10 ? 0 : 1)}${suffix}`;
  }

  function signedWhole(value: number, suffix = "") {
    const rounded = Math.round(value);
    return `${rounded > 0 ? "+" : ""}${rounded}${suffix}`;
  }

  function lineForAssignedPosition(position: string) {
    const role = normalizePosition(position);
    if (["ST", "CF", "SS", "LW", "RW"].includes(role)) return "attack";
    if (["CM", "CDM", "CAM", "LM", "RM"].includes(role)) return "midfield";
    if (["GK", "CB", "LB", "RB", "LWB", "RWB"].includes(role)) return "defense";
    return "attack";
  }

  function balanceDeltaChip(line: "attack" | "midfield" | "defense", delta: number) {
    const labels = { attack: "Attack", midfield: "Midfield", defense: "Defense" };
    if (Math.abs(delta) >= 0.3) {
      return {
        text: `${signedDecimal(delta)} ${labels[line]}`,
        tone: delta >= 0 ? "good" as const : "warn" as const
      };
    }

    if (line === "defense") return { text: "Defense still exposed", tone: "warn" as const };
    if (line === "midfield") return { text: "Midfield stabilized", tone: "info" as const };
    return { text: "Attack shape improved", tone: "info" as const };
  }

  function showPickChips(player: PickedPlayer, prevPicked: PickedPlayer[]) {
    if (pickChipTimer) clearTimeout(pickChipTimer);
    const chips: typeof pickChips = [];
    const newPicked = [...prevPicked, player];
    const prevChemistry = getChemistry(prevPicked);
    const nextChemistry = getChemistry(newPicked);
    const prevFit = getPositionFit(prevPicked);
    const nextFit = getPositionFit(newPicked);
    const previousBalance = calculateTeamBalance(prevPicked, formation, prevChemistry, prevFit);
    const nextBalance = calculateTeamBalance(newPicked, formation, nextChemistry, nextFit);
    const line = lineForAssignedPosition(player.assignedPosition);
    const lineDelta = nextBalance[line] - previousBalance[line];
    const chemistryDelta = nextChemistry - prevChemistry;
    const prevLibra = previousBalance.libraScore ?? 0;
    const nextLibra = nextBalance.libraScore ?? 0;
    const libraDelta = nextLibra - prevLibra;
    const lineValues = [nextBalance.attack, nextBalance.midfield, nextBalance.defense].filter((value) => value > 0);
    const spread = lineValues.length === 3 ? Math.max(...lineValues) - Math.min(...lineValues) : 100;

    chips.push(balanceDeltaChip(line, lineDelta));

    if (Math.abs(chemistryDelta) >= 2) {
      chips.push({
        text: `${signedWhole(chemistryDelta, "%")} Chemistry`,
        tone: chemistryDelta >= 0 ? "good" : "warn"
      });
    }

    if (newPicked.length >= 2 && Math.abs(libraDelta) >= 1) {
      chips.push({
        text: `Libra ${signedWhole(libraDelta)}`,
        tone: libraDelta >= 0 ? "good" : (libraDelta <= -4 ? "bad" : "warn")
      });
    } else if (newPicked.length >= 2 && nextLibra >= 80) {
      chips.push({ text: "Consistency improved", tone: "good" });
    }

    if (spread <= 7 && lineValues.length === 3) {
      chips.push({ text: "Shape becoming balanced", tone: "good" });
    } else if (spread >= 18 && newPicked.length >= 5) {
      chips.push({ text: "XI becoming top-heavy", tone: "warn" });
    }

    const weakestPlayerNow = newPicked.slice().sort((a, b) => a.adjustedIog - b.adjustedIog)[0];
    if (weakestPlayerNow && weakestPlayerNow.adjustedIog < 68) chips.push({ text: `Weak Link: ${weakestPlayerNow.assignedPosition}`, tone: "bad" });

    pickChips = chips.slice(0, 3);
    pickChipTimer = setTimeout(() => { pickChips = []; }, 2400);
  }

  function takeUnique(source: DraftOption[], selected: DraftOption[], count: number) {
    const next = [...selected];
    const used = new Set(next.map((player) => String(player.id)));

    for (const player of shuffle(source)) {
      if (next.length >= selected.length + count) break;
      if (used.has(String(player.id))) continue;
      next.push(player);
      used.add(String(player.id));
    }

    return next;
  }

  function noveltyPick(source: DraftOption[], selected: DraftOption[]) {
    const selectedIds = new Set(selected.map((player) => String(player.id)));
    const candidates = source.filter((player) => !selectedIds.has(String(player.id)));
    if (candidates.length === 0) return undefined;

    const weights = candidates.map((player) => {
      const id = String(player.id);
      if (!seenPlayerIds.has(id)) return 12;
      if (rejectedPlayerIds.has(id)) return 1;
      return 4;
    });
    let roll = Math.random() * weights.reduce((sum, weight) => sum + weight, 0);
    const index = weights.findIndex((weight) => {
      roll -= weight;
      return roll <= 0;
    });
    return candidates[index < 0 ? candidates.length - 1 : index];
  }

  function rememberShownOptions(shown: DraftOption[]) {
    const next = new Set(seenPlayerIds);
    for (const player of shown) next.add(String(player.id));
    seenPlayerIds = next;
  }

  function rememberRejectedOptions(selectedId = "") {
    const next = new Set(rejectedPlayerIds);
    const exposedOptions = isGoldenRound ? options.slice(0, visibleOptionLimit) : options;
    for (const player of exposedOptions) {
      if (String(player.id) !== selectedId) next.add(String(player.id));
    }
    rejectedPlayerIds = next;
  }

  function needsGoalkeeper() {
    return emptySlots.some((slot) => getSlotRole(slot) === "GK");
  }

  function includeGoalkeeperIfNeeded(selected: DraftOption[], ranked: DraftOption[]) {
    if (!needsGoalkeeper() || selected.some((player) => playerHasAnyPosition(player, ["GK"]))) return selected;
    const keeper = ranked.find((player) => playerHasAnyPosition(player, ["GK"]) && !selected.some((item) => String(item.id) === String(player.id)));
    if (!keeper) return selected;
    return [keeper, ...selected].slice(0, 5);
  }

  function rollWorldCupPoolProfile(): WorldCupPoolProfile {
    const roll = Math.random();
    if (roll < 0.12) return "elite";
    if (roll < 0.32) return "strong";
    if (roll < 0.67) return "balanced";
    if (roll < 0.86) return "weak";
    return "chaos";
  }

  function mixedQualityOptions(pool: Player[]) {
    const allRanked = sortOptions(pool.map((p) => toOption(p)), "iog_desc");
    const qualityRanked = allRanked.filter((player) => player.adjustedIog >= 70);
    const ranked = qualityRanked.length >= Math.min(5, allRanked.length) ? qualityRanked : allRanked;
    if (ranked.length <= 5) return ranked;

    const highCut = Math.max(1, Math.ceil(ranked.length * 0.25));
    const lowStart = Math.max(highCut + 1, Math.floor(ranked.length * 0.82));
    const high = ranked.slice(0, highCut);
    const medium = ranked.slice(highCut, lowStart);
    const risky = ranked.slice(lowStart);

    let selected: DraftOption[] = [];
    selected = takeUnique(high, selected, 1);
    selected = takeUnique(medium.length ? medium : ranked, selected, 3);
    selected = takeUnique(risky.length ? risky : ranked.slice(-Math.min(6, ranked.length)), selected, 1);

    if (selected.length < 5) selected = takeUnique(ranked, selected, 5 - selected.length);
    return sortOptions(includeGoalkeeperIfNeeded(selected.slice(0, 5), allRanked), sortKey);
  }

  function worldCupQualityOptions(pool: Player[]) {
    const allRanked = sortOptions(pool.map((p) => toOption(p)), "iog_desc");
    const ranked = allRanked.filter((player) => player.adjustedIog >= 62);
    const poolRanked = ranked.length >= Math.min(5, allRanked.length) ? ranked : allRanked;
    if (poolRanked.length <= 5) return sortOptions(poolRanked, sortKey);

    const eliteCut = Math.max(1, Math.ceil(poolRanked.length * 0.16));
    const strongCut = Math.max(eliteCut + 1, Math.ceil(poolRanked.length * 0.38));
    const mediumCut = Math.max(strongCut + 1, Math.ceil(poolRanked.length * 0.72));
    const elite = poolRanked.slice(0, eliteCut);
    const strong = poolRanked.slice(eliteCut, strongCut);
    const medium = poolRanked.slice(strongCut, mediumCut);
    const risky = poolRanked.slice(mediumCut);

    let selected: DraftOption[] = [];
    if (worldCupPoolProfile === "elite") {
      selected = takeUnique(elite, selected, 2);
      selected = takeUnique(strong.length ? strong : poolRanked, selected, 2);
      selected = takeUnique([...medium, ...risky].length ? [...medium, ...risky] : poolRanked, selected, 1);
    } else if (worldCupPoolProfile === "strong") {
      selected = takeUnique(elite, selected, 1);
      selected = takeUnique(strong.length ? strong : poolRanked, selected, 2);
      selected = takeUnique(medium.length ? medium : poolRanked, selected, 1);
      selected = takeUnique(risky.length ? risky : poolRanked, selected, 1);
    } else if (worldCupPoolProfile === "weak") {
      selected = takeUnique(strong.length ? strong : elite, selected, 1);
      selected = takeUnique(medium.length ? medium : poolRanked, selected, 2);
      selected = takeUnique(risky.length ? risky : poolRanked.slice(-Math.min(8, poolRanked.length)), selected, 2);
    } else if (worldCupPoolProfile === "chaos") {
      selected = takeUnique(elite.length ? elite : poolRanked, selected, 1);
      selected = takeUnique(strong.length ? strong : poolRanked, selected, 1);
      selected = takeUnique(risky.length ? risky : poolRanked.slice(-Math.min(8, poolRanked.length)), selected, 2);
      selected = takeUnique(poolRanked, selected, 1);
    } else {
      selected = takeUnique(elite, selected, 1);
      selected = takeUnique(strong.length ? strong : poolRanked, selected, 1);
      selected = takeUnique(medium.length ? medium : poolRanked, selected, 2);
      selected = takeUnique(risky.length ? risky : poolRanked.slice(-Math.min(8, poolRanked.length)), selected, 1);
    }

    if (selected.length < 5) selected = takeUnique(poolRanked, selected, 5 - selected.length);
    return sortOptions(includeGoalkeeperIfNeeded(selected.slice(0, 5), allRanked), sortKey);
  }

  function etQualityOptions(pool: Player[]) {
    const allOptions = pool.map((player) => toOption(player));
    const preferredOptions = allOptions.filter((player) => player.adjustedIog >= 75);
    const emergencyFallback = preferredOptions.length === 0;
    const eligibleOptions = emergencyFallback
      ? allOptions.map((player) => ({ ...player, emergency: true }))
      : preferredOptions;
    if (eligibleOptions.length <= 5) return sortOptions(eligibleOptions, sortKey);

    const elite = eligibleOptions.filter((player) => player.adjustedIog >= 85);
    const strong = eligibleOptions.filter((player) => player.adjustedIog >= 80 && player.adjustedIog < 85);
    const useful = eligibleOptions.filter((player) => player.adjustedIog >= 75 && player.adjustedIog < 80);
    let selected: DraftOption[] = [];

    const weightedBands: Array<{ pool: DraftOption[]; weight: number }> = [
      { pool: elite, weight: 60 },
      { pool: strong, weight: 25 },
      { pool: useful, weight: 15 }
    ];

    while (selected.length < 5) {
      const availableBands = weightedBands.filter(({ pool: band }) =>
        band.some((player) => !selected.some((pickedPlayer) => String(pickedPlayer.id) === String(player.id)))
      );
      if (availableBands.length === 0) break;

      const totalWeight = availableBands.reduce((sum, band) => sum + band.weight, 0);
      let roll = Math.random() * totalWeight;
      const chosenBand = availableBands.find((band) => {
        roll -= band.weight;
        return roll <= 0;
      }) ?? availableBands[availableBands.length - 1];
      const player = noveltyPick(chosenBand.pool, selected);
      if (player) selected = [...selected, player];
    }

    while (selected.length < 5) {
      const player = noveltyPick(eligibleOptions, selected);
      if (!player) break;
      selected = [...selected, player];
    }
    return sortOptions(includeGoalkeeperIfNeeded(selected.slice(0, 5), allOptions), sortKey);
  }

  const tutorialAttackNames = ["messi", "mbapp", "yamal", "dembele", "haaland"];

  function tutorialAttackOptions(pool: Player[]) {
    const selected = tutorialAttackNames
      .map((name) => pool.find((player) => playerNameKey(player.name).includes(name) || name.includes(playerNameKey(player.name))))
      .filter(Boolean) as Player[];
    const unique = Array.from(new Map(selected.map((player) => [String(player.id), player])).values());
    return unique.length >= 4 ? unique.map((player) => toOption(player)) : [];
  }

  function buildOptions() {
    fallbackNotice = "";

    if (emptySlots.length === 0) {
      startPostDraftAnalysis();
      return [];
    }

    const pool = isGoldenRound && (draftMode === "club" || draftMode === "et" || draftMode === "invinciblesClub") ? availableModePlayers() : availableUniversePlayers();
    const compatiblePool = pool.filter((p) => hasOpenSlot(p));

    if (pool.length === 0) {
      fallbackNotice = isGoldenRound ? "No players left in this Golden Pick pool." : "No players left for this team.";
      return [];
    }

    if (isGoldenRound) {
      if (draftMode === "et" || draftMode === "invinciblesClub") {
        const preferred = pool.filter((player) => getIog(player) >= 75);
        const goldenPool = preferred.some((player) => hasOpenSlot(player)) ? preferred : pool;
        return sortOptions(goldenPool.map((player) => toOption(player)), sortKey);
      }
      return sortOptions(pool.map((player) => toOption(player)), sortKey);
    }

    if (compatiblePool.length === 0) {
      fallbackNotice = "No compatible players remain for this formation.";
      return [];
    }

    if (tutorialAttackPoolActive && picked.length === 0 && !isGoldenRound && !isMysteryRound) {
      const tutorialOptions = tutorialAttackOptions(compatiblePool);
      if (tutorialOptions.length > 0) return sortOptions(tutorialOptions, sortKey).slice(0, 5);
    }

    if (isMysteryRound) {
      if (draftMode === "et" || draftMode === "invinciblesClub") return etQualityOptions(compatiblePool);
      if (draftMode === "worldcup") return worldCupQualityOptions(compatiblePool);
      return mixedQualityOptions(compatiblePool);
    }

    if (draftMode === "et" || draftMode === "invinciblesClub") return etQualityOptions(compatiblePool);
    if (draftMode === "worldcup") return worldCupQualityOptions(compatiblePool);
    return mixedQualityOptions(compatiblePool);
  }

  function getPickQualityLabel(player: DraftOption, slot: Slot) {
    if (player.adjustedIog >= 95) return "Galactico Pick";
    if (player.adjustedIog >= 90) return "Elite Pick";
    if (player.adjustedIog >= 85) return "Smart Pick";
    return "Squad Pick";
  }

  function markPhoebeTutorialSeen() {
    phoebeTutorialSeen = true;
    localStorage.setItem("phoebeTutorialSeen", "true");
  }

  function startPhoebeTutorial(targetScreen: "mode" | "formation" = "mode") {
    universe = activeUniverses()[0] ?? universe;
    tutorialStep = 0;
    showPhoebeTutorial = true;
    screen = targetScreen;
  }

  function skipPhoebeTutorial() {
    markPhoebeTutorialSeen();
    showPhoebeTutorial = false;
    screen = "mode";
  }

  function nextPhoebeScene() {
    if (tutorialStep < 3) {
      tutorialStep = (tutorialStep + 1) as TutorialStep;
    } else {
      markPhoebeTutorialSeen();
      showPhoebeTutorial = false;
    }
  }

  function startLoading(next: () => void) {
    if (loadingTimer) clearInterval(loadingTimer);
    loadingPercent = 1;
    loadingExiting = false;
    screen = "loading";

    // reset play-level state whenever we start loading a new flow
    playLevelStepIndex = 0;
    playLevelMaxSteps = 0;
    playLevelCompleted = false;


    loadingTimer = setInterval(() => {
      loadingPercent = Math.min(100, loadingPercent + randomInt(1, 3));

      if (loadingPercent >= 100 && loadingTimer) {
        clearInterval(loadingTimer);
        loadingTimer = null;
        loadingPercent = 100;
        loadingExiting = true;
        setTimeout(next, 420);
      }
    }, 32);
  }

  function playerHasAnyPosition(player: Player, roles: string[]) {
    return getPositions(player).some((position) => roles.includes(position));
  }

  function resetDraftState() {
    if (simulationTimer) clearInterval(simulationTimer);
    simulationTimer = null;
    picked = [];
    bench = [];
    benchCandidates = [];
    benchPool = [];
    benchSearch = "";
    pickChips = [];
    if (pickChipTimer) { clearTimeout(pickChipTimer); pickChipTimer = null; }
    if (assignedPulseTimer) { clearTimeout(assignedPulseTimer); assignedPulseTimer = null; }
    lastAssignedSlotId = "";
    if (finalVerdictTimer) { clearTimeout(finalVerdictTimer); finalVerdictTimer = null; }
    finalVerdictStepIndex = 0;
    lastAssignedPlayer = null;
    selectedPlayer = null;
    selectedSlotId = "";
    options = [];
    seenPlayerIds = new Set<string>();
    rejectedPlayerIds = new Set<string>();
    usedInvinciblesClubs = new Set<string>();
    canPick = false;
    isSpinning = false;
    respinsRemaining = 2;
    fallbackNotice = "";
    search = "";
    positionFilter = "ALL";
    sortKey = "iog_desc";
    visibleOptionLimit = 80;
    goldenPickNumber = randomInt(1, 11);
    mysteryPickNumber = randomInt(1, 11);
    worldCupSimulationSeed = randomInt(1000, 999999);
    if (draftMode === "worldcup") worldCupPoolProfile = rollWorldCupPoolProfile();
    while (mysteryPickNumber === goldenPickNumber) {
      mysteryPickNumber = randomInt(1, 11);
    }
    revealedMysteryPlayerIds = [];
    lastPickLabel = "";
    analysisStepIndex = 0;
    simulatedWins = 0;
    simulatedDraws = 0;
    simulatedLosses = 0;
    simulationComplete = false;
    etSignalSearching = false;
    etSignalText = etSignalMessages[0];
    playLevelStepIndex = 0;
    playLevelMaxSteps = 0;
    playLevelCompleted = false;
    playLevelStarted = false;
    playLevelSteps = [];
    playLevelCurrentStep = null;
    playLevelSeasonSummary = null;
  }

  function startDraftFlow() {
    tutorialAttackPoolActive = !phoebeTutorialSeen;
    draftMode = "worldcup";
    resetDraftState();
    screen = "mode";
    if (!phoebeTutorialSeen) startPhoebeTutorial("mode");
  }

  async function loadPlayersThen(next: () => void) {
    if (playerDataLoaded) {
      next();
      return;
    }

    startLoading(async () => {
      await ensurePlayerDataLoaded();
      next();
    });
  }

  function chooseMode(mode: "club" | "worldcup" | "et" | "invinciblesClub") {
    draftMode = mode;
    resetDraftState();
    loadPlayersThen(() => {
      universe = activeUniverses()[0] ?? universe;
      screen = mode === "club" || mode === "invinciblesClub" ? "clubFormat" : "formation";
    });
  }

  function chooseTutorialMode(mode: "worldcup" | "et" | "invinciblesClub") {
    if (showPhoebeTutorial) return;
    chooseMode(mode);
  }

  function confirmModeNavigation() {
    if (["draft", "bench", "analysis", "playLevel", "simulation", "record", "libra", "result"].includes(screen)) {
      return window.confirm("Changing mode will reset the current draft. Continue?");
    }
    return true;
  }

  function navigateMode(mode: "worldcup" | "et" | "invinciblesClub") {
    if (!confirmModeNavigation()) return;
    showPhoebeTutorial = false;
    tutorialAttackPoolActive = false;
    if (mode === "et") {
      openEtMode();
      return;
    }
    chooseMode(mode);
  }

  function openEtMode() {
    if (showPhoebeTutorial) return;
    draftMode = "et";
    resetDraftState();
    loadPlayersThen(() => {
      universe = etUniverse;
      screen = "etIntro";
    });
  }

  function backFromEtIntro() {
    resetDraftState();
    screen = "mode";
  }

  function continueFromEtIntro() {
    screen = "formation";
  }

  function chooseLeagueFormat(league: ClubLeague) {
    draftMode = "club";
    clubFormat = "league";
    selectedClubLeague = league;
    resetDraftState();
    universe = activeUniverses()[0] ?? universe;
    screen = "formation";
  }

  function chooseChampionsLeagueFormat() {
    draftMode = "club";
    clubFormat = "champions";
    resetDraftState();
    universe = activeUniverses()[0] ?? universe;
    screen = "formation";
  }

  function chooseInvinciblesChallenge(challengeId: InvinciblesChallengeId) {
    selectedInvinciblesChallenge = challengeId;
    resetDraftState();
    universe = etUniverse;
    screen = "formation";
  }

  function backToMenu() {
    draftMode = "worldcup";
    clubFormat = "league";
    selectedClubLeague = "Premier League";
    selectedInvinciblesChallenge = "european";
    universe = worldCupUniverses[0] ?? universes[0];
    resetDraftState();
    screen = "menu";
  }

  function backToMode() {
    resetDraftState();
    screen = "mode";
  }

  function backFromFormation() {
    resetDraftState();
    screen = draftMode === "invinciblesClub" ? "clubFormat" : draftMode === "et" ? "etIntro" : "menu";
  }

  function backFromDraft() {
    resetDraftState();
    screen = "formation";
  }

  function chooseFormation(value: string) {
    formation = value;
    universe = activeUniverses()[0] ?? universe;
    resetDraftState();
    screen = "draft";
    setTimeout(() => spinUniverse(false), 0);
  }

  function randomUniverse(excludeKey = "") {
    const candidates = activeUniverses();
    const available = candidates.filter((candidate) => universeKey(candidate) !== excludeKey);
    const pool = available.length > 0 ? available : candidates;
    return pool[Math.floor(Math.random() * pool.length)] ?? universe;
  }

  function findValidUniverse(excludeKey = "") {
    let candidate = randomUniverse(excludeKey);

    for (let i = 0; i < 20; i++) {
      universe = candidate;

      if (compatibleUniversePlayers().length > 0) {
        return candidate;
      }

      candidate = randomUniverse(excludeKey);
    }

    return candidate;
  }

  function buildSafeOptions(excludeKey = "") {
    for (let attempt = 0; attempt <= 2; attempt++) {
      const nextOptions = buildOptions();
      if (nextOptions.length > 0) {
        if (attempt > 0) fallbackNotice = `Auto-respun ${attempt} impossible universe${attempt === 1 ? "" : "s"}.`;
        return nextOptions;
      }

      if (attempt < 2) {
        universe = randomUniverse(excludeKey);
      }
    }

    for (const candidate of shuffle(activeUniverses().filter((item) => universeKey(item) !== excludeKey))) {
      universe = candidate;
      const nextOptions = buildOptions();
      if (nextOptions.length > 0) {
        fallbackNotice = "Skipped impossible universe.";
        return nextOptions;
      }
    }

    fallbackNotice = "No compatible unpicked players remain for this formation.";
    return [];
  }

  function spinUniverse(manual = false, excludeKey = "") {
    if (picked.length >= 11) {
      startBenchRound();
      return;
    }

    if (manual && respinsRemaining <= 0) return;
    if (manual) respinsRemaining--;
    if ((draftMode === "et" || draftMode === "invinciblesClub") && options.length > 0) rememberRejectedOptions();

    isSpinning = true;
    canPick = false;
    selectedPlayer = null;
    selectedSlotId = "";
    options = [];
    fallbackNotice = "";
    search = "";
    positionFilter = "ALL";
    sortKey = "iog_desc";
    visibleOptionLimit = 80;
    lastPickLabel = "";
    etSignalSearching = draftMode === "et";
    etSignalText = etSignalMessages[0];

    let ticks = 0;
    const targetTicks = draftMode === "et" ? 12 : 18;
    const tickDelay = draftMode === "et" ? 70 : 85;

    const interval = setInterval(() => {
      universe = randomUniverse(excludeKey);
      ticks++;
      if (draftMode === "et") {
        etSignalText = etSignalMessages[Math.min(etSignalMessages.length - 1, Math.floor((ticks / targetTicks) * etSignalMessages.length))];
      }

      if (ticks >= targetTicks) {
        clearInterval(interval);
        universe = findValidUniverse(excludeKey);
        options = buildSafeOptions(excludeKey);
        if (draftMode === "invinciblesClub" && !isGoldenRound) {
          usedInvinciblesClubs = new Set([...usedInvinciblesClubs, universe.club]);
        }
        if (draftMode === "et" || draftMode === "invinciblesClub") rememberShownOptions(isGoldenRound ? options.slice(0, visibleOptionLimit) : options);
        isSpinning = false;
        etSignalSearching = false;
        canPick = options.length > 0;
      }
    }, tickDelay);
  }

  function selectPlayer(player: DraftOption) {
    if (isMysteryCardHidden(player)) {
      const mysterySlot = getCompatibleSlots(player)[0];
      if (!mysterySlot) {
        fallbackNotice = "No compatible slot is available for this Mystery Pick.";
        return;
      }
      selectedPlayer = player;
      selectedSlotId = mysterySlot.id;
      assignSelected(mysterySlot, true);
      return;
    }

    selectedPlayer = player;
    selectedSlotId = "";

    const playableSlots = getCompatibleSlots(player);

    warnIfNoCompatibleSlots(player, playableSlots);

    if (playableSlots.length > 0) {
      selectedSlotId = playableSlots[0].id;
    }
  }

  function assignSelected(selectedSlot?: Slot, mysteryAssignment = false) {
    if (!selectedPlayer) {
      return;
    }

    const slot = selectedSlot ?? slots.find((s) => s.id === selectedSlotId) ?? getCompatibleSlots(selectedPlayer)[0];
    if (!slot || !canAssignPlayerToSlot(selectedPlayer, slot)) {
      if (mysteryAssignment) console.warn("Mystery Pick could not be assigned to a compatible slot.");
      else warnIfNoCompatibleSlots(selectedPlayer, getCompatibleSlots(selectedPlayer));
      return;
    }

    const adjustedIog = getIog(selectedPlayer);
    const penalty = 0;
    const pickLabel = mysteryAssignment ? "Mystery Pick" : getPickQualityLabel(selectedPlayer, slot);
    const alternatives = options
      .filter((option) => String(option.id) !== String(selectedPlayer?.id))
      .slice(0, 4)
      .map((option) => isMysteryRound ? "Mystery Player" : option.name);
    const assignedPlayer = {
      ...selectedPlayer,
      slotId: slot.id,
      assignedPosition: slot.label,
      adjustedIog,
      penalty,
      mysteryPick: mysteryAssignment || isMysteryRound,
      goldenPick: isGoldenRound,
      pickLabel,
      alternatives
    };

    if (draftMode === "et" || draftMode === "invinciblesClub") rememberRejectedOptions(String(selectedPlayer.id));

    const prevPicked = [...picked];
    picked = [
      ...picked,
      assignedPlayer
    ];
    lastAssignedPlayer = assignedPlayer;
    lastAssignedSlotId = slot.id;
    if (assignedPulseTimer) clearTimeout(assignedPulseTimer);
    assignedPulseTimer = setTimeout(() => {
      lastAssignedSlotId = "";
      assignedPulseTimer = null;
    }, 950);
    showPickChips(assignedPlayer, prevPicked);

    const previousUniverseKey = universeKey(universe);
    selectedPlayer = null;
    selectedSlotId = "";
    options = [];
    canPick = false;
    const assignedName = assignedPlayer.name;
    lastPickLabel = mysteryAssignment ? "Mystery Pick secured" : pickLabel;
    fallbackNotice = mysteryAssignment
      ? "Mystery Pick added to the XI. Identity remains hidden."
      : tutorialAttackPoolActive && picked.length === 1
        ? `${assignedName} changed the XI. Watch balance, chemistry and Libra react.`
        : isGoldenRound ? `Golden Pick: ${pickLabel}` : pickLabel;
    if (tutorialAttackPoolActive) tutorialAttackPoolActive = false;

    if (picked.length >= 11) {
      startBenchRound();
    } else {
      setTimeout(() => spinUniverse(false, previousUniverseKey), 0);
    }
  }

  function clickSlot(slot: Slot) {
    if (!selectedPlayer) return;
    if (canAssignPlayerToSlot(selectedPlayer, slot)) {
      selectedSlotId = slot.id;
      assignSelected(slot);
    } else {
      warnIfNoCompatibleSlots(selectedPlayer, getCompatibleSlots(selectedPlayer));
    }
  }

  function getPlayer(slotId: string) {
    return picked.find((p) => p.slotId === slotId);
  }

  function getTeamGrade(avgScore: number, chemistryScore: number, fitScore: number, weakestScore: number) {
    const weakLinkPenalty = weakestScore < 68 ? 8 : weakestScore < 74 ? 5 : weakestScore < 80 ? 2 : 0;
    const composite = avgScore * 0.72 + chemistryScore * 0.12 + fitScore * 0.12 + weakestScore * 0.04 - weakLinkPenalty;

    if (composite >= 95) return "S+";
    if (composite >= 91) return "S";
    if (composite >= 87) return "A+";
    if (composite >= 82) return "A";
    if (composite >= 76) return "B";
    if (composite >= 68) return "C";
    return "D";
  }

  function computeHiddenGem(
    roster: PickedPlayer[],
    weakest: PickedPlayer | undefined,
    best: PickedPlayer | undefined,
    averageIog: number
  ): PickedPlayer | undefined {
    if (roster.length === 0) return undefined;
    const excludingWeakest = weakest && roster.length > 1 ? roster.filter((p) => String(p.id) !== String(weakest.id)) : roster;
    const mystery = excludingWeakest.find((p) => p.mysteryPick);
    if (mystery) return mystery;
    const underrated = excludingWeakest
      .filter((p) => p.adjustedIog >= averageIog && p.adjustedIog < (best?.adjustedIog ?? Infinity))
      .sort((a, b) => b.adjustedIog - a.adjustedIog)[0];
    if (underrated) return underrated;
    return excludingWeakest.slice().sort((a, b) => b.adjustedIog - a.adjustedIog)[0] ?? roster[0];
  }

  function gradeValue(value: string) {
    const values: Record<string, number> = { "S+": 8, S: 6, "A+": 4, A: 2, B: 0, C: -3, D: -6 };
    return values[value] ?? 0;
  }

  const worldCupOutcomeOrder: WorldCupOutcome[] = [
    "Group Stage Exit",
    "Round of 32 Exit",
    "Round of 16 Exit",
    "Quarterfinal Exit",
    "Semifinal Exit",
    "Runner-up",
    "World Cup Winner"
  ];

  function outcomeIndex(score: number) {
    if (score >= 90) return 6;
    if (score >= 85) return 5;
    if (score >= 80) return 4;
    if (score >= 75) return 3;
    if (score >= 69) return 2;
    if (score >= 63) return 1;
    return 0;
  }

  function worldCupProfileModifier(profile: WorldCupPoolProfile) {
    const modifiers: Record<WorldCupPoolProfile, number> = {
      elite: 4.2,
      strong: 2.1,
      balanced: 0,
      weak: -4.1,
      chaos: 0
    };
    return modifiers[profile] ?? 0;
  }

  function varianceNote(value: number) {
    if (value >= 5) return "favourable tournament draw";
    if (value >= 2) return "shootout luck";
    if (value <= -5) return "injury and fatigue swing";
    if (value <= -2) return "hostile knockout margins";
    return "normal tournament variance";
  }

  function formatWorldCupBoost(stages: number) {
    if (stages <= 0) return "None";
    if (stages === 1) return "+1 stage";
    return "+2 stage miracle";
  }

  function simulateWorldCupOutcome(
    roster: PickedPlayer[],
    avgIogValue: number,
    gradeLabel: string,
    chemistryScore: number,
    fitScore: number,
    squadLibra: number | null,
    balanceProfile: TeamBalanceProfile
  ): WorldCupSimulation {
    if (roster.length === 0) {
      return {
        baseOutcome: "Group Stage Exit",
        finalOutcome: "Group Stage Exit",
        libraBoostStages: 0,
        score: 0,
        varianceLabel: "draft incomplete",
        explanation: "The tournament engine is waiting for a completed XI before making a serious projection."
      };
    }

    const seed = roster.map((player) => `${player.id ?? player.name}:${player.slotId}:${player.adjustedIog}`).join(",");
    const attackAverage = lineAverage(roster, ["ST", "CF", "LW", "RW", "CAM"], avgIogValue);
    const midfieldAverage = lineAverage(roster, ["CDM", "CM", "CAM", "LM", "RM"], avgIogValue);
    const defenseAverage = lineAverage(roster, ["GK", "CB", "LB", "RB", "LWB", "RWB"], avgIogValue);
    const goalkeeper = roster.find((player) => normalizePosition(player.assignedPosition) === "GK");
    const goalkeeperQuality = goalkeeper?.adjustedIog ?? defenseAverage;
    const sortedIog = roster.map((player) => player.adjustedIog).sort((a, b) => b - a);
    const starPower = sortedIog.slice(0, 2).reduce((sum, value) => sum + value, 0) / Math.max(1, Math.min(2, sortedIog.length));
    const weakestScore = sortedIog[sortedIog.length - 1] ?? avgIogValue;
    const lineScores = [attackAverage, midfieldAverage, defenseAverage].filter((value) => value > 0);
    const lineSpread = lineScores.length ? Math.max(...lineScores) - Math.min(...lineScores) : 18;
    const varianceSeed = seededUnit([worldCupSimulationSeed, seed, universe.club, formation, "worldcup-variance"]);
    const chaosWidth = worldCupPoolProfile === "chaos" ? 22 : 15;
    const variance = (varianceSeed - 0.5) * chaosWidth;
    const profileModifier = worldCupProfileModifier(worldCupPoolProfile);
    const collapsePenalty =
      Math.max(0, 66 - weakestScore) * 0.28 +
      Math.max(0, 70 - goalkeeperQuality) * 0.16 +
      Math.max(0, lineSpread - 13) * 0.22 +
      formationRiskScore(formation) * 0.38;
    const starCarry =
      Math.max(0, starPower - avgIogValue) * 0.22 +
      Math.max(0, attackAverage - 86) * 0.12 +
      Math.max(0, goalkeeperQuality - 86) * 0.1;

    let score =
      avgIogValue * 0.4 +
      chemistryScore * 0.11 +
      fitScore * 0.1 +
      (squadLibra ?? 62) * 0.12 +
      ((balanceProfile.attack + balanceProfile.midfield + balanceProfile.defense) / 3) * 0.09 +
      goalkeeperQuality * 0.06 +
      starPower * 0.06 +
      gradeValue(gradeLabel) +
      profileModifier +
      starCarry +
      variance -
      collapsePenalty;

    let baseIndex = outcomeIndex(score);
    const titleRoll = seededUnit([worldCupSimulationSeed, seed, "worldcup-title"]);
    if (baseIndex === 6 && (score < 93 || titleRoll < 0.26)) baseIndex = 5;
    if (avgIogValue < 70 && baseIndex > 2) baseIndex = 2;
    if ((squadLibra ?? 0) < 48 && baseIndex > 3) baseIndex -= 1;
    if (goalkeeperQuality < 64 && baseIndex > 4) baseIndex = 4;

    const baseOutcome = worldCupOutcomeOrder[clamp(baseIndex, 0, worldCupOutcomeOrder.length - 1)] as WorldCupOutcome;
    let boostStages = 0;
    const boostEligible =
      (squadLibra ?? 0) >= 80 &&
      avgIogValue >= 70 &&
      chemistryScore >= 48 &&
      fitScore >= 55 &&
      weakestScore >= 58 &&
      goalkeeperQuality >= 58 &&
      baseIndex < worldCupOutcomeOrder.length - 1;
    const boostRoll = seededUnit([worldCupSimulationSeed, seed, "libra-boost"]);
    if (boostEligible) {
      const oneStageChance = (squadLibra ?? 0) >= 90 ? 0.92 : 0.78;
      if (boostRoll < oneStageChance) boostStages = 1;
      const twoStageRoll = seededUnit([worldCupSimulationSeed, seed, "libra-miracle"]);
      if (
        boostStages === 1 &&
        (squadLibra ?? 0) >= 90 &&
        avgIogValue >= 82 &&
        chemistryScore >= 70 &&
        fitScore >= 70 &&
        weakestScore >= 68 &&
        baseIndex <= 4 &&
        twoStageRoll < 0.16
      ) {
        boostStages = 2;
      }
    }

    const finalIndex = clamp(baseIndex + boostStages, 0, worldCupOutcomeOrder.length - 1);
    const finalOutcome = worldCupOutcomeOrder[finalIndex] as WorldCupOutcome;
    const weakLink = weakestScore < 68;
    const weakGK = goalkeeperQuality < 72;
    const lowLibra = (squadLibra ?? 0) < 68;
    const thinSpread = lineSpread > 14;
    let explanation: string;
    if (finalOutcome === "World Cup Winner") {
      explanation = `Exceptional. Star power of ${Math.round(starPower)}, a ${Math.round(weakestScore)} weakest-link floor, and ${varianceNote(variance)} all aligned. This XI earned every round.`;
    } else if (finalOutcome === "Runner-up") {
      explanation = weakLink
        ? `So close to glory. The ${Math.round(weakestScore)} weakest-link score was exposed at the decisive moment — one stronger position could have changed the final.`
        : `Reached the final, but ${varianceNote(variance)} cost the trophy. This was a strong XI that deserved better.`;
    } else if (finalOutcome === "Semifinal Exit") {
      explanation = weakGK
        ? `The XI had the attacking quality to go further, but a ${Math.round(goalkeeperQuality)} GK rating left the last line vulnerable under knockout pressure.`
        : weakLink
          ? `Your XI had real quality, but the ${Math.round(weakestScore)} weakest-link floor was targeted in the knockout draw. A deeper bench would have changed the outcome.`
          : `Good enough for the semis, but ${varianceNote(variance)} ended the run at the wrong moment. Lift the Libra score and the ceiling rises significantly.`;
    } else if (finalOutcome === "Quarterfinal Exit") {
      explanation = thinSpread
        ? `The XI had talent, but the gap between your best and weakest lines was too exposed in a knockout format. Balance the three lines and QF exits become SF runs.`
        : lowLibra
          ? `Solid build, but consistency gaps across the XI meant one bad night ended the campaign. Higher Libra acts as a knockout insurance policy.`
          : `Quality was there for a deeper run, but the tournament draw was harsh. ${varianceNote(variance)} caught this team at the wrong moment.`;
    } else {
      explanation = weakLink
        ? `The weakest link (${Math.round(weakestScore)}) was the early exit reason — knockout football punishes any gap in the XI. Fix that position and the group stage exit becomes history.`
        : weakGK
          ? `Goalkeeping quality (${Math.round(goalkeeperQuality)}) was the pressure point that cracked. A stronger last line keeps you alive longer in tournament football.`
          : `Tough exit. ${varianceNote(variance)} hit at the worst time. This squad has more potential — review the weakest line and run again.`;
    }

    return {
      baseOutcome,
      finalOutcome,
      libraBoostStages: boostStages,
      score: Math.round(score),
      varianceLabel: varianceNote(variance),
      explanation
    };
  }

  function seededUnit(parts: Array<string | number | undefined>) {
    const source = parts.join("|");
    let hash = 2166136261;
    for (let index = 0; index < source.length; index++) {
      hash ^= source.charCodeAt(index);
      hash = Math.imul(hash, 16777619);
    }
    return ((hash >>> 0) % 10000) / 10000;
  }

  function seededRange(min: number, max: number, parts: Array<string | number | undefined>) {
    if (max <= min) return min;
    return min + Math.floor(seededUnit(parts) * (max - min + 1));
  }

  function formationRiskScore(selectedFormation: string) {
    const risk: Record<string, number> = {
      "4-2-3-1": 1,
      "4-3-3": 2,
      "4-4-2": 3,
      "4-4-1-1": 2,
      "4-1-4-1": 2,
      "3-5-2": 5,
      "3-4-2-1": 6,
      "3-4-3": 8,
      "5-4-1": 4
    };

    return risk[selectedFormation] ?? 4;
  }

  function lineAverage(roster: PickedPlayer[], positions: string[], fallback = 0) {
    const players = roster.filter((player) => positions.includes(normalizePosition(player.assignedPosition)));
    if (!players.length) return fallback;
    return players.reduce((sum, player) => sum + player.adjustedIog, 0) / players.length;
  }

  function scaledRange(range: [number, number], matches: number): [number, number] {
    const ratio = matches / 38;
    return [Math.max(0, Math.round(range[0] * ratio)), Math.max(0, Math.round(range[1] * ratio))];
  }

  function seasonTone(record: EtLeagueRecord | { wins: number; draws: number; losses: number; points: number }) {
    const maxPoints = invinciblesSeasonMatches * 3;
    const pointRatio = record.points / Math.max(maxPoints, 1);
    const winRatio = record.wins / Math.max(invinciblesSeasonMatches, 1);
    if (record.losses === 0 || pointRatio >= 0.72 || winRatio >= 0.64) return "high";
    if (pointRatio < 0.48 || winRatio < 0.4 || record.losses >= Math.round(invinciblesSeasonMatches * 0.32)) return "low";
    return "medium";
  }

  function valueTone(value: number, low: number, high: number) {
    if (value >= high) return "high";
    if (value < low) return "low";
    return "medium";
  }

  function positionTone(position: string) {
    if (["1st", "2nd", "3rd", "4th"].includes(position)) return "high";
    if (["13th", "16th", "17th", "20th"].includes(position)) return "low";
    return "medium";
  }

  function gradeTone(value: string) {
    if (["S+", "S", "A+"].includes(value)) return "high";
    if (["C", "D"].includes(value)) return "low";
    return "medium";
  }

  function invincibleTone(record: EtLeagueRecord) {
    if (record.losses === 0) return "high";
    if (record.losses <= (invinciblesSeasonMatches === 34 ? 2 : 3)) return "medium";
    return "low";
  }

  function invincibleProbability(
    squadAverage: number,
    chemistryScore: number,
    squadLibra: number,
    positionFitScore: number,
    defenseAverage: number,
    lineSpread: number
  ) {
    const avg10 = squadAverage / 10;
    let base = 0;
    let cap = 1;

    if (avg10 < 7.2) {
      base = 0.5;
      cap = 1;
    } else if (avg10 < 7.7) {
      base = 1 + (avg10 - 7.2) * 4;
      cap = 4;
    } else if (avg10 < 8.1) {
      base = 3 + (avg10 - 7.7) * 12;
      cap = 9;
    } else if (avg10 < 8.5) {
      base = 8 + (avg10 - 8.1) * 24;
      cap = 18;
    } else if (avg10 < 8.9) {
      base = 18 + (avg10 - 8.5) * 42;
      cap = 36;
    } else {
      base = 36 + Math.min(18, (avg10 - 8.9) * 36);
      cap = 54;
    }

    const balanceModifier =
      (chemistryScore - 75) * 0.14 +
      (squadLibra - 75) * 0.18 +
      (positionFitScore - 75) * 0.08 +
      (defenseAverage - 78) * 0.08 -
      formationRiskScore(formation) * 1.2 -
      lineSpread * 0.38;

    const chemistryCap = chemistryScore < 70 || squadLibra < 70 ? 12 : cap;
    return Math.round(clamp(base + balanceModifier, 0, chemistryCap));
  }

  function chooseSeasonBand(strength: number, weakestScore: number, lineSpread: number) {
    const adjusted = strength - Math.max(0, 74 - weakestScore) * 0.22 - Math.max(0, lineSpread - 10) * 0.22;
    if (adjusted < 72) return "weak";
    if (adjusted < 78) return "average";
    if (adjusted < 84) return "good";
    if (adjusted < 89) return "great";
    return "elite";
  }

  function getEtLeagueRecord(roster: PickedPlayer[], matches = 38): EtLeagueRecord {
    if (roster.length === 0) {
      return {
        wins: 0,
        draws: 0,
        losses: matches,
        record: `0-0-${matches}`,
        points: 0,
        position: "20th",
        goalDifference: -76,
        goalsFor: 18,
        goalsAgainst: 94,
        cleanSheets: 0,
        titleChance: 0,
        invincibleChance: 0,
        invinciblesRating: 0
      };
    }

    const squadAverage = roster.reduce((sum, player) => sum + player.adjustedIog, 0) / roster.length;
    const squadChemistry = getChemistry(roster);
    const squadFit = getPositionFit(roster);
    const squadLibra = calculateLibraScore(roster, {
      formation,
      chemistry: squadChemistry,
      positionFit: squadFit
    }) ?? Math.max(30, squadAverage - 20);
    const attackAverage = lineAverage(roster, ["ST", "CF", "LW", "RW", "CAM"], squadAverage);
    const midfieldAverage = lineAverage(roster, ["CDM", "CM", "CAM", "LM", "RM"], squadAverage);
    const defenseAverage = lineAverage(roster, ["GK", "CB", "LB", "RB", "LWB", "RWB"], squadAverage);
    const lineScores = [attackAverage, midfieldAverage, defenseAverage].filter((value) => value > 0);
    const lineSpread = lineScores.length ? Math.max(...lineScores) - Math.min(...lineScores) : 18;
    const weakestScore = Math.min(...roster.map((player) => player.adjustedIog));
    const riskPenalty = formationRiskScore(formation);
    const modeDifficulty = draftMode === "invinciblesClub" ? 0.4 : 3.8;
    const strength =
      squadAverage * 0.44 +
      squadLibra * 0.2 +
      squadChemistry * 0.14 +
      squadFit * 0.08 +
      defenseAverage * 0.07 +
      midfieldAverage * 0.04 +
      attackAverage * 0.03 -
      riskPenalty -
      modeDifficulty;

    const band = chooseSeasonBand(strength, weakestScore, lineSpread);
    const bands: Record<string, { wins: [number, number]; draws: [number, number]; losses: [number, number] }> = {
      weak: { wins: [10, 16], draws: [6, 10], losses: [12, 18] },
      average: { wins: [15, 20], draws: [6, 10], losses: [8, 14] },
      good: { wins: [20, 26], draws: [5, 9], losses: [3, 9] },
      great: { wins: [26, 32], draws: [4, 8], losses: [0, 5] },
      elite: { wins: [30, 36], draws: [2, 7], losses: [0, 3] }
    };
    const selectedBand = bands[band];
    const winsRange = scaledRange(selectedBand.wins, matches);
    const drawsRange = scaledRange(selectedBand.draws, matches);
    const lossesRange = scaledRange(selectedBand.losses, matches);
    const seed = roster.map((player) => `${player.id ?? player.name}:${player.slotId}:${player.adjustedIog}`).join(",");
    const candidates: Array<{ wins: number; draws: number; losses: number; score: number }> = [];
    const targetWins = clamp(8 + (strength - 58) * 0.72, winsRange[0], winsRange[1]);
    const targetDraws = clamp(9 - Math.max(0, strength - 72) * 0.12 + Math.max(0, lineSpread - 9) * 0.12, drawsRange[0], drawsRange[1]);

    for (let winsCandidate = winsRange[0]; winsCandidate <= winsRange[1]; winsCandidate++) {
      for (let drawsCandidate = drawsRange[0]; drawsCandidate <= drawsRange[1]; drawsCandidate++) {
        const lossesCandidate = matches - winsCandidate - drawsCandidate;
        if (lossesCandidate < lossesRange[0] || lossesCandidate > lossesRange[1]) continue;
        const jitter = seededUnit([seed, "candidate", winsCandidate, drawsCandidate, matches]) * 1.8;
        candidates.push({
          wins: winsCandidate,
          draws: drawsCandidate,
          losses: lossesCandidate,
          score: -Math.abs(winsCandidate - targetWins) * 2 - Math.abs(drawsCandidate - targetDraws) + jitter
        });
      }
    }

    let selected = (candidates.length ? candidates : [{ wins: 18, draws: 8, losses: Math.max(0, matches - 26), score: 0 }])
      .sort((a, b) => b.score - a.score)[0];
    const invincibleChance = invincibleProbability(squadAverage, squadChemistry, squadLibra, squadFit, defenseAverage, lineSpread);
    const goesInvincible = seededUnit([seed, "invincible", matches, formation]) * 100 < invincibleChance;

    if (goesInvincible) {
      const invincibleWins = Math.max(selected.wins, seededRange(Math.round(matches * 0.76), Math.round(matches * 0.9), [seed, "invincible-wins"]));
      selected = { wins: invincibleWins, draws: matches - invincibleWins, losses: 0, score: selected.score };
    } else if (selected.losses === 0) {
      const forcedLosses = seededRange(1, band === "elite" ? 3 : 5, [seed, "forced-loss"]);
      const drawReduction = Math.min(selected.draws, Math.max(0, forcedLosses - 1));
      selected = {
        wins: Math.max(0, selected.wins - (forcedLosses - drawReduction)),
        draws: Math.max(0, selected.draws - drawReduction),
        losses: forcedLosses,
        score: selected.score
      };
      const total = selected.wins + selected.draws + selected.losses;
      if (total < matches) selected.draws += matches - total;
      if (total > matches) selected.wins = Math.max(0, selected.wins - (total - matches));
    }

    const wins = selected.wins;
    const draws = selected.draws;
    const losses = matches - wins - draws;
    const points = wins * 3 + draws;
    const goalsFor = Math.max(24, Math.min(108, Math.round(34 + (attackAverage - 70) * 0.95 + wins * 1.05 + squadChemistry * 0.06)));
    const goalsAgainst = Math.max(18, Math.min(88, Math.round(72 - (defenseAverage - 68) * 0.82 - squadLibra * 0.11 + losses * 1.35 + riskPenalty * 0.8)));
    const goalDifference = goalsFor - goalsAgainst;
    const cleanSheets = Math.max(1, Math.min(Math.round(matches * 0.58), Math.round(3 + (defenseAverage - 70) * 0.28 + squadFit * 0.05 - losses * 0.12)));
    const titleChance = Math.max(1, Math.min(94, Math.round((points / etMaxPoints - 0.48) * 155 + squadLibra * 0.10 + squadChemistry * 0.06 - losses * 1.2)));
    const invinciblesRating = Math.max(0, Math.min(100, Math.round(strength * 0.72 + squadLibra * 0.18 + squadChemistry * 0.1)));
    const projectedPoints38 = matches === 38 ? points : Math.round((points / matches) * 38);
    const position = projectedPoints38 >= 88 ? "1st" : projectedPoints38 >= 82 ? "2nd" : projectedPoints38 >= 74 ? "3rd" : projectedPoints38 >= 66 ? "4th" : projectedPoints38 >= 58 ? "6th" : projectedPoints38 >= 48 ? "9th" : projectedPoints38 >= 38 ? "13th" : "17th";
    const record = `${wins}-${draws}-${losses}`;

    return { wins, draws, losses, record, points, position, goalDifference, goalsFor, goalsAgainst, cleanSheets, titleChance, invincibleChance, invinciblesRating };
  }

  function etEarthComposite(roster: PickedPlayer[]) {
    if (!roster.length) return 55;
    const squadAverage = roster.reduce((sum, player) => sum + player.adjustedIog, 0) / roster.length;
    const balance = calculateTeamBalance(roster, formation, getChemistry(roster), getPositionFit(roster));
    const lineValues = [balance.attack, balance.midfield, balance.defense].filter((value) => value > 0);
    const lineSpread = lineValues.length === 3 ? Math.max(...lineValues) - Math.min(...lineValues) : 18;
    const weakest = Math.min(...roster.map((player) => player.adjustedIog));
    return clamp(
      squadAverage * 0.46 +
      (balance.libraScore ?? 65) * 0.18 +
      balance.chemistry * 0.14 +
      balance.positionFit * 0.12 +
      balance.tacticalDistribution * 0.06 -
      Math.max(0, lineSpread - 8) * 0.42 -
      Math.max(0, 72 - weakest) * 0.18 -
      formationRiskScore(formation) * 0.35,
      45,
      98
    );
  }

  function chooseAlienOpponent(roster: PickedPlayer[]) {
    const composite = etEarthComposite(roster);
    const average = roster.length ? roster.reduce((sum, player) => sum + player.adjustedIog, 0) / roster.length : 68;
    const average10 = average / 10;
    const seed = roster.map((player) => `${player.id}:${player.slotId}:${player.adjustedIog}`).join(",");
    const byName = Object.fromEntries(alienOpponents.map((opponent) => [opponent.name, opponent])) as Record<AlienOpponent["name"], AlienOpponent>;
    const eliteParadoxChance = composite >= 90 && (libraScore ?? 0) >= 86 && chemistry >= 78 ? 25 : 15;
    const weights: Array<[AlienOpponent["name"], number]> = average10 < 7.3
      ? [["Moonrock Rovers", 55], ["Betelgeuse United", 35], ["The Clones", 8], ["Orion FC", 2], ["Paradox", 0]]
      : average10 < 8.0
        ? [["Moonrock Rovers", 15], ["Betelgeuse United", 40], ["The Clones", 30], ["Orion FC", 13], ["Paradox", 2]]
        : [["Moonrock Rovers", 5], ["Betelgeuse United", 20], ["The Clones", 28], ["Orion FC", 32], ["Paradox", eliteParadoxChance]];
    const total = weights.reduce((sum, [, weight]) => sum + weight, 0);
    let roll = seededUnit([seed, "alien-opponent", Math.round(composite), formation]) * total;

    for (const [name, weight] of weights) {
      roll -= weight;
      if (roll <= 0) return byName[name] ?? alienOpponents[0];
    }

    return byName["Orion FC"] ?? alienOpponents[3];
  }

  function paradoxMirrorThreats() {
    const realistic = players
      .filter((player) => player.name && player.dataSource !== "fictional_et_mode" && getCompetition(player) !== "ET Mode")
      .map((player) => ({ player, iog: getIog(player) }))
      .filter(({ iog }) => iog > 0 && iog <= 72)
      .sort((a, b) => a.iog - b.iog)
      .slice(0, 90);
    const source = realistic.length ? realistic : players.map((player) => ({ player, iog: getIog(player) })).sort((a, b) => a.iog - b.iog).slice(0, 40);

    return shuffle(source)
      .slice(0, 3)
      .map(({ player, iog }, index) => ({
        name: `${player.name}${index === 0 ? "-Prime" : index === 1 ? " Mirror" : " Variant"}`,
        originalIog: iog,
        paradoxIog: Math.round(clamp(94 - Math.max(0, iog - 50) * 0.18 - index * 1.2, 88, 94))
      }));
  }

  function getEtAlienMatch(roster: PickedPlayer[]): EtAlienMatch {
    const opponent = chooseAlienOpponent(roster);
    const composite = etEarthComposite(roster);
    const balance = calculateTeamBalance(roster, formation, getChemistry(roster), getPositionFit(roster));
    const weakPointPenalty = weakestPlayer ? Math.max(0, 74 - weakestPlayer.adjustedIog) * 0.22 : 0;
    const opponentScore = opponent.averageIog + opponent.pressure;
    let survivalChance = Math.round(clamp(48 + (composite - opponentScore) * 2.15 - weakPointPenalty, 3, 92));
    if (opponent.name === "Paradox") {
      const eliteCap = composite >= 91 && (balance.libraScore ?? 0) >= 88 && balance.chemistry >= 80 ? 58 : 42;
      survivalChance = Math.round(clamp(survivalChance - 10, 2, eliteCap));
    }

    const seed = roster.map((player) => `${player.id}:${player.assignedPosition}:${player.adjustedIog}`).join(",");
    const roll = seededUnit([seed, opponent.name, "alien-final"]) * 100;
    const barelyWindow = opponent.name === "Paradox" ? 18 : 13;
    const outcome: EtAlienMatch["outcome"] = roll <= survivalChance - 8
      ? "win"
      : roll <= survivalChance + barelyWindow
        ? "barely"
        : "loss";
    const resultTone = outcome === "win" ? "high" : outcome === "barely" ? "medium" : "low";
    const scoreline = outcome === "win"
      ? (opponent.name === "Paradox" ? "2-1" : "3-1")
      : outcome === "barely"
        ? (seededUnit([seed, "pens"]) > 0.5 ? "1-1 pens" : "2-2 aet")
        : (opponent.name === "Paradox" ? "1-3" : "1-2");
    const route = outcome === "win"
      ? "Earth wins before the signal can collapse."
      : outcome === "barely"
        ? "Earth survives... barely."
        : "Transmission ends.";

    const note = opponent.name === "Paradox"
      ? "Paradox has mirrored the weakest data points into elite threats. Libra stability is the only thing keeping the shape readable."
      : balance.status.includes("Balanced")
        ? "Earth's shape is stable. For now."
        : `${balance.status} gives Earth a clear route, but the signal pressure keeps rising.`;

    return {
      opponent,
      survivalChance,
      outcome,
      resultText: outcome === "win" ? "Earth survives." : outcome === "barely" ? "Earth survives... barely." : "Transmission ends.",
      resultTone,
      scoreline,
      route,
      keyPlayer: bestPlayer?.name ?? "Galactico11",
      mirrorThreats: opponent.name === "Paradox" ? paradoxMirrorThreats() : [],
      tacticalNote: note
    };
  }

  function randomInt(min: number, max: number) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  function signedImpact(value: number) {
    return `${value > 0 ? "+" : ""}${value}`;
  }

  function titleCase(value: string) {
    return value ? `${value[0].toUpperCase()}${value.slice(1)}` : value;
  }

  function getChemistry(roster: PickedPlayer[]) {
    if (roster.length === 0) return 0;

    const fitValues = roster.map((player) => {
      const primary = getPositions(player)[0];
      const assigned = normalizePosition(player.assignedPosition);
      const declared = getPositions(player).map(normalizePosition);
      if (primary && normalizePosition(primary) === assigned) return 100;
      if (declared.includes(assigned)) return 86;
      return isPlayerCompatibleWithSlot(player, slots.find((slot) => slot.id === player.slotId) ?? { id: "", label: assigned, position: assigned, x: 0, y: 0 }) ? 72 : 30;
    });
    const suitability = fitValues.reduce((sum, value) => sum + value, 0) / roster.length;

    let sameNationPairs = 0;
    let sameEraPairs = 0;
    let pairCount = 0;

    for (let i = 0; i < roster.length; i++) {
      for (let j = i + 1; j < roster.length; j++) {
        const a = roster[i];
        const b = roster[j];
        pairCount += 1;
        if (chemistryTeamContext(a) && chemistryTeamContext(a) === chemistryTeamContext(b)) sameNationPairs += 1;
        if (a.era && a.era === b.era) sameEraPairs += 1;
      }
    }

    const nationCohesion = (sameNationPairs / Math.max(pairCount, 1)) * 100;
    const eraCohesion = (sameEraPairs / Math.max(pairCount, 1)) * 100;

    const lineKey = (value: string) => value === "goalkeeper" ? "defence" : value;
    const lineNames = ["attack", "midfield", "defence"];
    const actualCounts = Object.fromEntries(lineNames.map((line) => [line, 0])) as Record<string, number>;
    const expectedCounts = Object.fromEntries(lineNames.map((line) => [line, 0])) as Record<string, number>;
    for (const player of roster) actualCounts[lineKey(tacticalLine(player))] += 1;
    for (const slot of slots) {
      const position = normalizePosition(slot.position);
      const slotLine = position === "GK" || ["CB", "LB", "RB", "LWB", "RWB"].includes(position)
        ? "defence"
        : ["CM", "CAM", "CDM", "LM", "RM"].includes(position) ? "midfield" : "attack";
      expectedCounts[slotLine] += 1;
    }

    const distributionDifference = lineNames.reduce((sum, line) =>
      sum + Math.abs(actualCounts[line] / roster.length - expectedCounts[line] / slots.length), 0);
    const formationSuitability = clamp(100 - distributionDifference * 65);
    const lineCoverage = lineNames.filter((line) => actualCounts[line] > 0).length / 3 * 100;
    const uniqueRoles = new Set(roster.map((player) => normalizePosition(player.assignedPosition))).size;
    const roleDiversity = clamp((uniqueRoles / Math.min(roster.length, 6)) * 100);
    const tacticalFit = lineCoverage * 0.35 + roleDiversity * 0.25 + suitability * 0.4;

    const lineAverages = lineNames
      .map((line) => roster.filter((player) => lineKey(tacticalLine(player)) === line))
      .filter((linePlayers) => linePlayers.length > 0)
      .map((linePlayers) => linePlayers.reduce((sum, player) => sum + player.adjustedIog, 0) / linePlayers.length);
    const lineSpread = lineAverages.length > 1 ? Math.max(...lineAverages) - Math.min(...lineAverages) : 30;
    const balanceScore = clamp(lineCoverage * 0.5 + (100 - lineSpread * 2.5) * 0.5);
    const mysteryPlayers = roster.filter((player) => player.mysteryPick);
    const mysteryImpact = mysteryPlayers.length
      ? mysteryPlayers.reduce((sum, player) => sum + fitValues[roster.indexOf(player)], 0) / mysteryPlayers.length
      : suitability;
    const chemistryScore =
      suitability * 0.3 +
      formationSuitability * 0.15 +
      tacticalFit * 0.15 +
      balanceScore * 0.2 +
      nationCohesion * 0.12 +
      eraCohesion * 0.03 +
      mysteryImpact * 0.05;

    return Math.round(clamp(chemistryScore, 0, 100));
  }

  function getPositionFit(roster: PickedPlayer[]) {
    if (roster.length === 0) return 0;

    const naturalFits = roster.filter((player) => {
      const primary = getPositions(player)[0];
      if (!primary) return false;
      return compatibleSlotRoles(primary).includes(normalizePosition(player.assignedPosition));
    }).length;

    return Math.round((naturalFits / roster.length) * 100);
  }

  function isNaturalAssignment(player: PickedPlayer) {
    const primary = getPositions(player)[0];
    if (!primary) return false;
    return compatibleSlotRoles(primary).includes(normalizePosition(player.assignedPosition));
  }

  function tacticalLine(player: PickedPlayer) {
    const position = normalizePosition(player.assignedPosition);
    if (position === "GK") return "goalkeeper";
    if (["CB", "LB", "RB", "LWB", "RWB"].includes(position)) return "defence";
    if (["CDM", "CM", "CAM", "LM", "RM"].includes(position)) return "midfield";
    return "attack";
  }

  function partnershipScore(a: PickedPlayer, b: PickedPlayer) {
    let links = 0;
    if (chemistryTeamContext(a) && chemistryTeamContext(a) === chemistryTeamContext(b)) links += 8;
    if (playerTeam(a) && playerTeam(a) === playerTeam(b)) links += 8;
    if (a.league === b.league || getCompetition(a) === getCompetition(b)) links += 4;
    if (a.era === b.era) links += 3;

    const lines = new Set([tacticalLine(a), tacticalLine(b)]);
    if (lines.has("midfield") && lines.has("attack")) links += 7;
    else if (lines.has("defence") && lines.has("midfield")) links += 6;
    else if (lines.size === 1) links += 4;

    return (a.adjustedIog + b.adjustedIog) / 2 + links;
  }

  function strongestPartnership(roster: PickedPlayer[]) {
    let best = { a: roster[0], b: roster[1] ?? roster[0], score: -Infinity };

    for (let i = 0; i < roster.length; i++) {
      for (let j = i + 1; j < roster.length; j++) {
        const score = partnershipScore(roster[i], roster[j]);
        if (score > best.score) best = { a: roster[i], b: roster[j], score };
      }
    }

    return best;
  }

  function teamIdentity(roster: PickedPlayer[], chemistryScore: number, fitScore: number) {
    const lines = roster.map(tacticalLine);
    const defenders = lines.filter((line) => line === "defence").length;
    const midfielders = lines.filter((line) => line === "midfield").length;
    const attackers = lines.filter((line) => line === "attack").length;
    const widePlayers = roster.filter((player) => ["LB", "RB", "LWB", "RWB", "LM", "RM", "LW", "RW"].includes(normalizePosition(player.assignedPosition))).length;
    const goals = roster.reduce((sum, player) => sum + Number(player.goals ?? 0), 0);
    const assists = roster.reduce((sum, player) => sum + Number(player.assists ?? 0), 0);
    const defensiveActions = roster.reduce((sum, player) => sum + Number(player.tackles ?? 0) + Number(player.interceptions ?? 0) + Number(player.recoveries ?? 0), 0);

    const balance = calculateTeamBalance(roster, formation, chemistryScore, fitScore);
    const lineScores = [balance.attack, balance.midfield, balance.defense].filter(Boolean);
    const spread = lineScores.length ? Math.max(...lineScores) - Math.min(...lineScores) : 100;
    const formationTags: Record<string, Partial<Record<string, number>>> = {
      "4-3-3": { "Wide Overload": 10, "High Press": 6, "Chaos Attack": 4 },
      "4-4-2": { "Direct Football": 12, "Counter-Attacking": 6 },
      "4-4-1-1": { "Direct Football": 8, "Press-Resistant XI": 6 },
      "4-2-3-1": { "Midfield Control": 10, "Press-Resistant XI": 7, "Possession Dominant": 4 },
      "4-1-4-1": { "Midfield Control": 11, "Defensive Fortress": 5 },
      "3-5-2": { "Midfield Control": 9, "Wing Overload": 8, "Transition Monsters": 5 },
      "3-4-3": { "Chaos Attack": 12, "High Press": 7, "Transition Monsters": 6 },
      "3-4-2-1": { "Transition Monsters": 10, "High Press": 7, "Chaos Attack": 6 },
      "5-4-1": { "Low Block Specialists": 12, "Defensive Fortress": 10, "Counter-Attacking": 4 }
    };
    const tagBoost = formationTags[formation] ?? {};

    const profiles = [
      { name: "Possession Dominant", score: balance.midfield * 0.35 + chemistryScore * 0.24 + fitScore * 0.16 + (tagBoost["Possession Dominant"] ?? 0) },
      { name: "Counter-Attacking", score: balance.attack * 0.32 + balance.defense * 0.18 + (100 - chemistryScore) * 0.08 + (tagBoost["Counter-Attacking"] ?? 0) },
      { name: "High Press", score: (balance.attack + balance.midfield) * 0.21 + Math.min(defensiveActions, 140) * 0.16 + chemistryScore * 0.08 + (tagBoost["High Press"] ?? 0) },
      { name: "Defensive Fortress", score: balance.defense * 0.42 + defenders * 3.6 + fitScore * 0.12 + (tagBoost["Defensive Fortress"] ?? 0) },
      { name: "Direct Football", score: attackers * 8 + Math.min(goals, 45) * 0.34 + balance.attack * 0.18 + (tagBoost["Direct Football"] ?? 0) },
      { name: "Wing Overload", score: widePlayers * 7 + Math.min(assists, 35) * 0.44 + balance.attack * 0.12 + (tagBoost["Wing Overload"] ?? 0) },
      { name: "Midfield Control", score: balance.midfield * 0.44 + midfielders * 3.6 + chemistryScore * 0.1 + (tagBoost["Midfield Control"] ?? 0) },
      { name: "Transition Monsters", score: spread * 1.8 + balance.attack * 0.18 + (100 - fitScore) * 0.08 + (tagBoost["Transition Monsters"] ?? 0) },
      { name: "Chaos Attack", score: balance.attack * 0.36 + attackers * 4 + (100 - chemistryScore) * 0.1 + (tagBoost["Chaos Attack"] ?? 0) },
      { name: "Low Block Specialists", score: balance.defense * 0.36 + defenders * 5 + (100 - balance.attack) * 0.08 + (tagBoost["Low Block Specialists"] ?? 0) },
      { name: "Balanced XI", score: spread <= 7 ? 54 + chemistryScore * 0.18 + fitScore * 0.16 : 10 },
      { name: "Set-Piece Threat", score: defenders * 5 + Math.min(goals, 30) * 0.22 + balance.defense * 0.12 },
      { name: "Press-Resistant XI", score: chemistryScore * 0.28 + fitScore * 0.22 + balance.midfield * 0.18 + (tagBoost["Press-Resistant XI"] ?? 0) }
    ];

    const identity = profiles.sort((a, b) => b.score - a.score)[0].name;
    const descriptions: Record<string, string> = {
      "Possession Dominant": `${midfielders} midfield roles and ${chemistryScore}% chemistry point toward a team that wants to control territory and dictate tempo.`,
      "Counter-Attacking": `${attackers} attacking roles and a ${formatIoG(balance.attack)} attack score make this XI most dangerous when it breaks into space.`,
      "Pressing Machine": `${midfielders + defenders} players operate through the middle and defensive lines, giving this team the numbers to hunt the ball together.`,
      "Defensive Fortress": `${defenders} defenders and ${fitScore}% position fit make protection, structure and game control the clearest foundation.`,
      "Direct Football": `${attackers} forward roles and ${goals} recorded goals point toward early service, box presence and quick territory gains.`,
      "Wide Overload": `${widePlayers} wide-role selections and ${assists} combined recorded assists make the flanks this team's natural route forward.`,
      "Midfield Control": `${formatIoG(balance.midfield)} midfield strength and ${midfielders} midfield roles make the centre of the pitch the team's main weapon.`,
      "Transition Monsters": `A ${Math.round(spread)} point line spread makes this team volatile, explosive and dangerous in broken phases.`,
      "Chaos Attack": `${formatIoG(balance.attack)} attacking strength gives this XI a high ceiling, but it may ask the rest of the team to survive open games.`,
      "Low Block Specialists": `${formatIoG(balance.defense)} defensive strength and this formation profile point toward compact defending and selective counters.`,
      "Balanced XI": `The three lines sit close enough together that no single unit has to carry the entire tactical identity.`,
      "Set-Piece Threat": `${defenders} defensive roles and the squad's physical profile make dead-ball moments a realistic route to goals.`,
      "Press-Resistant XI": `${chemistryScore}% chemistry and ${fitScore}% position fit suggest a team that can play through pressure without losing its shape.`
    };

    return { name: identity, description: descriptions[identity] };
  }

  function buildSquadDiagnosis(
    roster: PickedPlayer[],
    balance: TeamBalanceProfile,
    chemistryScore: number,
    fitScore: number
  ) {
    if (!roster.length) return [];

    const insights: string[] = [];
    const ranked = [
      ["Attack", balance.attack],
      ["Midfield", balance.midfield],
      ["Defense", balance.defense]
    ].sort((a, b) => Number(b[1]) - Number(a[1]));
    const lead = ranked[0];
    const gap = Number(ranked[0][1]) - Number(ranked[2][1]);

    if (gap >= 8) insights.push(`${lead[0]} carrying the squad`);
    else insights.push("No single line is carrying the whole XI");

    if (weakestPlayer) insights.push(`${weakestPosition} is the pressure point`);
    if (chemistryScore >= 78) insights.push("Strong chemistry spine");
    else if (chemistryScore < 55) insights.push("Chemistry may break under pressure");

    if ((balance.libraScore ?? 0) >= 85) insights.push("Libra profile supports consistent results");
    else if ((balance.libraScore ?? 0) < 65) insights.push("Uneven quality could swing the season");

    if (fitScore >= 82) insights.push("Most roles fit the formation naturally");
    else if (fitScore < 62) insights.push("Several tactical compromises remain");

    return Array.from(new Set(insights)).slice(0, 5);
  }

  function buildPostDraftAnalysis(
    roster: PickedPlayer[],
    selectedFormation: string,
    averageIog: number,
    chemistryScore: number,
    fitScore: number,
    finalGrade: string,
    mode: "worldcup" | "club" | "et" | "invinciblesClub"
  ): PostDraftAnalysisStep[] {
    if (roster.length === 0) return [];

    const formationSlots = formations[selectedFormation] ?? [];
    const defensiveSlots = formationSlots.filter((slot) => ["CB", "LB", "RB", "LWB", "RWB"].includes(normalizePosition(slot.position))).length;
    const midfieldSlots = formationSlots.filter((slot) => ["CDM", "CM", "CAM", "LM", "RM"].includes(normalizePosition(slot.position))).length;
    const attackingSlots = formationSlots.filter((slot) => ["ST", "LW", "RW"].includes(normalizePosition(slot.position))).length;
    const naturalFits = roster.filter(isNaturalAssignment).length;
    const shapeDemand = defensiveSlots >= 5
      ? "The shape demanded defensive depth and reliable width before luxury picks could be considered."
      : attackingSlots >= 3
        ? "The shape reserved major influence for the front line, so midfield balance became the price of attacking freedom."
        : midfieldSlots >= 5
          ? "The shape concentrated responsibility in midfield and made wide coverage a decisive drafting constraint."
          : "The shape split responsibility evenly across the lines and rewarded players who could solve more than one role.";

    const earlyPool = roster.slice(0, Math.min(4, roster.length));
    const earlyPick = earlyPool.reduce((best, player) => player.adjustedIog > best.adjustedIog ? player : best);
    const earlyIndex = roster.indexOf(earlyPick);

    const turningCandidates = roster
      .map((player, index) => {
        const previous = roster.slice(0, index);
        const previousAverage = previous.length ? previous.reduce((sum, pick) => sum + pick.adjustedIog, 0) / previous.length : player.adjustedIog;
        const swing = Math.max(0, player.adjustedIog - previousAverage);
        const score = player.adjustedIog + swing * 0.7 + (player.goldenPick ? 9 : 0) + (player.mysteryPick ? 5 : 0) + (isNaturalAssignment(player) ? 3 : 0);
        return { player, index, score };
      })
      .filter((candidate) => candidate.player !== earlyPick || roster.length === 1)
      .sort((a, b) => b.score - a.score);
    const turningPoint = turningCandidates[0] ?? { player: earlyPick, index: earlyIndex, score: earlyPick.adjustedIog };

    const partnership = strongestPartnership(roster);
    const partnershipLinks: string[] = [];
    if (chemistryTeamContext(partnership.a) === chemistryTeamContext(partnership.b)) partnershipLinks.push((draftMode === "et" || draftMode === "invinciblesClub") ? "shared club context" : "shared national context");
    if (playerTeam(partnership.a) === playerTeam(partnership.b)) partnershipLinks.push("club familiarity");
    if (partnership.a.era === partnership.b.era) partnershipLinks.push("the same era");
    if (partnershipLinks.length === 0) partnershipLinks.push(`${tacticalLine(partnership.a)}-to-${tacticalLine(partnership.b)} balance`);

    const identity = teamIdentity(roster, chemistryScore, fitScore);
    const balanceProfile = calculateTeamBalance(roster, selectedFormation, chemistryScore, fitScore);
    const best = roster.slice().sort((a, b) => b.adjustedIog - a.adjustedIog)[0];
    const weakest = roster.slice().sort((a, b) => a.adjustedIog - b.adjustedIog)[0];
    const analysisName = (player: PickedPlayer) => player.mysteryPick ? "Mystery Pick" : player.name;
    const strongestTrait = averageIog >= 86
      ? `${analysisName(best)} gives the XI an elite ceiling`
      : chemistryScore >= 68
        ? `${chemistryScore}% chemistry gives the team a coherent base`
        : `${naturalFits} natural assignments keep the structure recognisable`;
    const weakness = weakest.adjustedIog < 75
      ? `${analysisName(weakest)} is the clearest pressure point`
      : chemistryScore < 55
        ? `${chemistryScore}% chemistry may make coordinated phases inconsistent`
        : fitScore < 75
          ? `${fitScore}% position fit leaves tactical compromises for opponents to target`
          : `the gap between ${analysisName(best)} and ${analysisName(weakest)} could make performance uneven across the XI`;

    const turningReason = turningPoint.player.goldenPick
      ? "The Golden Pick opened the pool, and you used it on the player who changed the squad's ceiling most."
      : turningPoint.player.mysteryPick
        ? "The hidden choice became the draft's defining gamble once the card was revealed."
        : isNaturalAssignment(turningPoint.player)
          ? "That selection added quality while solving its assigned role without structural compromise."
          : "That selection raised the team's raw level enough to justify the positional compromise.";

    const steps: PostDraftAnalysisStep[] = [
      {
        id: "complete",
        kicker: "Draft Complete",
        title: mode === "et" ? "Congratulations, you have built Earth’s strongest team - Galactico11." : "The board is locked",
        body: `All 11 places in your ${selectedFormation} are filled. I have tracked every selection, every positional trade-off and the way your team developed from pick one to pick eleven.`,
        metricLabel: "Team IoG",
        metricValue: formatIoG(averageIog),
        tone: "intro"
      },
      {
        id: "formation",
        kicker: "Formation Analysis",
        title: `${selectedFormation} shaped every decision`,
        body: `${shapeDemand} You finished with ${naturalFits} of 11 players in their primary role and ${fitScore}% overall position fit.`,
        metricLabel: "Line Structure",
        metricValue: `${defensiveSlots} DEF • ${midfieldSlots} MID • ${attackingSlots} ATT`,
        tone: "shape"
      },
      {
        id: "first-pick",
        kicker: "First Major Pick",
        title: `${analysisName(earlyPick)} set the standard`,
        body: `Selected at pick ${earlyIndex + 1}, ${analysisName(earlyPick)} made the strongest statement among your opening four decisions.`,
        metricLabel: "Opening Impact",
        metricValue: earlyPick.mysteryPick ? `Pick ${earlyIndex + 1} • Identity Hidden` : `Pick ${earlyIndex + 1} • IoG ${formatIoG(earlyPick.adjustedIog)}`,
        tone: "pick"
      },
      {
        id: "turning-point",
        kicker: "Turning Point",
        title: `${analysisName(turningPoint.player)} changed the direction`,
        body: `Pick ${turningPoint.index + 1} was the moment this draft found its level. ${turningReason}`,
        metricLabel: turningPoint.player.goldenPick ? "Golden Pick" : turningPoint.player.mysteryPick ? "Mystery Pick" : "Decision Impact",
        metricValue: turningPoint.player.mysteryPick ? "Mystery Pick • Identity Hidden" : `${normalizePosition(turningPoint.player.assignedPosition)} • IoG ${formatIoG(turningPoint.player.adjustedIog)}`,
        tone: "turn"
      },
      {
        id: "partnership",
        kicker: "Strongest Partnership",
        title: `${analysisName(partnership.a)} + ${analysisName(partnership.b)}`,
        body: `Their combined ${formatIoG((partnership.a.adjustedIog + partnership.b.adjustedIog) / 2)} average IoG and ${partnershipLinks.join(", ")} make this the strongest relationship in your XI.`,
        metricLabel: "Assigned Roles",
        metricValue: partnership.a.mysteryPick || partnership.b.mysteryPick ? "One role remains hidden" : `${normalizePosition(partnership.a.assignedPosition)} + ${normalizePosition(partnership.b.assignedPosition)}`,
        tone: "pair"
      },
      {
        id: "identity",
        kicker: "Team Identity",
        title: identity.name,
        body: identity.description,
        metricLabel: "Chemistry",
        metricValue: `${chemistryScore}%`,
        tone: "identity"
      },
      {
        id: "balance",
        kicker: "Strengths and Weaknesses",
        title: balanceProfile.status,
        body: `${balanceProfile.insight} Strength: ${strongestTrait}. Risk: ${weakness}`,
        metricLabel: "ATT • MID • DEF",
        metricValue: `${balanceProfile.attack.toFixed(0)} • ${balanceProfile.midfield.toFixed(0)} • ${balanceProfile.defense.toFixed(0)}`,
        tone: "balance"
      },
      {
        id: "grade",
        kicker: "Draft Grade",
        title: `${finalGrade} is the final verdict`,
        body: `An average IoG of ${formatIoG(averageIog)}, ${chemistryScore}% chemistry and ${fitScore}% position fit produced this grade. ${analysisName(weakest)} sets the floor; ${analysisName(best)} sets the ceiling.`,
        metricLabel: "Final Grade",
        metricValue: finalGrade,
        tone: "grade"
      }
    ];

    const mysteryRevealSteps = roster
      .filter((player) => player.mysteryPick)
      .map((player, index): PostDraftAnalysisStep => {
        const reducedRoster = roster.filter((candidate) => String(candidate.id) !== String(player.id));
        const reducedChemistry = getChemistry(reducedRoster);
        const reducedFit = getPositionFit(reducedRoster);
        const reducedBalance = calculateTeamBalance(reducedRoster, selectedFormation, reducedChemistry, reducedFit);
        const reducedLibra = calculateLibraScore(reducedRoster, {
          formation: selectedFormation,
          chemistry: reducedChemistry,
          positionFit: reducedFit
        }) ?? 0;
        const fullLibra = calculateLibraScore(roster, {
          formation: selectedFormation,
          chemistry: chemistryScore,
          positionFit: fitScore
        }) ?? 0;
        const isInvinciblesMode = mode === "invinciblesClub";
        const fullProjection = isInvinciblesMode ? getEtLeagueRecord(roster, invinciblesSeasonMatches).points : 0;
        const reducedProjection = isInvinciblesMode
          ? getEtLeagueRecord(reducedRoster, invinciblesSeasonMatches).points
          : 0;
        const lineFor = (candidate: PickedPlayer) => tacticalLine(candidate) === "goalkeeper" ? "defense" : tacticalLine(candidate);
        const line = lineFor(player) as "attack" | "midfield" | "defense";
        const impact = Math.round(balanceProfile[line] - reducedBalance[line]);
        const libraImpact = fullLibra - reducedLibra;
        const chemistryImpact = chemistryScore - reducedChemistry;
        const simulationImpact = fullProjection - reducedProjection;
        const isHighestIog = player.adjustedIog === best.adjustedIog;
        const impactSentence = isHighestIog
          ? `That became the highest IoG player in your squad.`
          : impact >= 1
            ? `${player.name} raised your ${line} score by ${impact} points.`
            : `${player.name} added depth to your ${line} without destabilising the shape.`;
        const quote = impact >= 2
          ? `Your mystery selection strengthened the ${line === "defense" ? "spine" : line} of the squad more than expected.`
          : chemistryImpact >= 2
            ? "This selection connected the structure and improved the relationships around it."
            : simulationImpact >= 2
              ? "The individual impact raised the squad's projected season ceiling."
              : "A measured selection that added useful depth without disrupting the tactical plan.";

        return {
          id: `mystery-reveal-${player.id}-${index}`,
          kicker: "Mystery Reveal",
          title: "The final hidden selection has been identified",
          body: `${impactSentence} The selection changed Libra by ${libraImpact >= 0 ? "+" : ""}${libraImpact} and chemistry by ${chemistryImpact >= 0 ? "+" : ""}${chemistryImpact}.`,
          metricLabel: "Mystery Identity",
          metricValue: `${displayTeamContext(player)} • IoG ${formatIoG(player.adjustedIog)}`,
          tone: "mystery",
          mysteryPlayer: player,
          mysteryImpact: {
            chemistry: chemistryImpact,
            line,
            lineRating: impact,
            projectedPoints: isInvinciblesMode ? simulationImpact : undefined,
            quote
          }
        };
      });

    steps.push(...mysteryRevealSteps);

    return steps;
  }

  function startPostDraftAnalysis() {
    revealedMysteryPlayerIds = [];
    analysisStepIndex = 0;
    screen = "analysis";
  }

  function revealMysteryForStep(step: PostDraftAnalysisStep | undefined) {
    if (!step?.mysteryPlayer) return;
    const playerId = String(step.mysteryPlayer.id);
    if (!revealedMysteryPlayerIds.includes(playerId)) {
      revealedMysteryPlayerIds = [...revealedMysteryPlayerIds, playerId];
    }
  }

  function advancePostDraftAnalysis() {
    if (analysisStepIndex < postDraftAnalysis.length - 1) {
      const nextIndex = analysisStepIndex + 1;
      revealMysteryForStep(postDraftAnalysis[nextIndex]);
      analysisStepIndex = nextIndex;
    } else {
      startPlayLevelExperience();
    }
  }


  function skipPostDraftAnalysis() {
    const nextMysteryIndex = postDraftAnalysis.findIndex((step) =>
      step.mysteryPlayer && !revealedMysteryPlayerIds.includes(String(step.mysteryPlayer.id))
    );
    if (nextMysteryIndex >= 0) {
      revealMysteryForStep(postDraftAnalysis[nextMysteryIndex]);
      analysisStepIndex = nextMysteryIndex;
      return;
    }
    revealedMysteryPlayerIds = picked.filter((player) => player.mysteryPick).map((player) => String(player.id));

    startPlayLevelExperience();
  }


  function etSeasonComment(wins: number, record = predictedEtRecord) {
    if (record.losses === 0) return "A rare unbeaten campaign. The balance held even when the season turned hostile.";
    if (wins >= Math.round(invinciblesSeasonMatches * 0.76) && record.losses <= 3) return "This was a genuine title-level season, even if perfection stayed out of reach.";
    if (wins >= Math.round(invinciblesSeasonMatches * 0.62)) return "This team competed every week, but a few weak spots kept the ceiling realistic.";
    if (wins >= Math.round(invinciblesSeasonMatches * 0.42)) return "There were flashes of quality, but the margins were thin.";
    return "This squad never found consistency.";
  }

  function libraLabel(score: number | null) {
    if (score === null) return "Building";
    if (score >= 95) return "Elite Balance";
    if (score >= 85) return "Well Balanced";
    if (score >= 70) return "Functional";
    if (score >= 50) return "Unstable";
    return "Chaotic";
  }

  function playLevelKeyPlayer(index = 0) {
    const ordered = picked.slice().sort((a, b) => b.adjustedIog - a.adjustedIog);
    return ordered[index % Math.max(ordered.length, 1)]?.name ?? "The XI";
  }

  function playLevelOpponents(count: number) {
    const worldCupPool = worldCupNations.map((nation) => nation.name).filter((name) => name && name !== universe.club);
    const fallback = ["Brazil", "France", "Argentina", "Spain", "England", "Portugal", "Germany", "Netherlands", "Morocco", "Belgium"];
    return shuffle(worldCupPool.length >= count ? worldCupPool : fallback).slice(0, count);
  }

  function buildWorldCupPlayLevelSteps(): PlayLevelStep[] {
    const stages = ["Group Stage", "Round of 32", "Round of 16", "Quarterfinal", "Semifinal", "Final"];
    const outcomeRank: Record<string, number> = {
      "Group Stage Exit": 0,
      "Round of 32 Exit": 1,
      "Round of 16 Exit": 2,
      "Quarterfinal Exit": 3,
      "Semifinal Exit": 4,
      "Runner-up": 5,
      "World Cup Winner": 6
    };
    const reached = outcomeRank[predictedWorldCupOutcome] ?? 3;
    const opponents = playLevelOpponents(stages.length);
    const strength = Number(avgIog) * 0.72 + chemistry * 0.1 + positionFit * 0.08 + (libraScore ?? 70) * 0.1;

    return stages
      .map((stage, index): PlayLevelStep => {
        const isFinalStage = index === stages.length - 1;
        const advanced = reached > index;
        const eliminatedHere = !advanced && reached === index;
        const winGoals = Math.max(1, Math.min(4, Math.round(1 + (strength - 72) / 14 + Math.random())));
        const conceded = Math.max(0, Math.min(3, Math.round(2 - (strength - 70) / 18 + Math.random() * 0.8)));
        const scoreline = advanced
          ? `${Math.max(winGoals, conceded + 1)}-${conceded}`
          : eliminatedHere
            ? `${Math.max(0, conceded - 1)}-${Math.max(1, conceded)}`
            : "Pending";

        return {
          id: `worldcup-${index}`,
          kicker: "World Cup Play Level",
          title: isFinalStage && predictedWorldCupOutcome === "World Cup Winner"
              ? "World Champions"
              : advanced
            ? `${stage} cleared`
              : `${stage} exit`,
          stage,
          opponent: opponents[index] ?? "Elite Opposition",
          scoreline,
          advanced,
          manOfTheMatch: playLevelKeyPlayer(index),
          tacticalAnalysis: advanced
            ? `${finalBalanceProfile.status} gave the side enough control to manage the decisive moments.`
            : `The margins tightened here. ${weakestPosition} became the pressure point as the opponent forced the game away from your strengths.`
        };
      })
      .filter((step, index) => index <= Math.min(reached, stages.length - 1));
  }

  function positionFromPoints(points: number, maxPoints: number) {
    const ratio = points / Math.max(maxPoints, 1);
    if (ratio >= 0.82) return "1st";
    if (ratio >= 0.74) return "2nd";
    if (ratio >= 0.66) return "3rd";
    if (ratio >= 0.58) return "5th";
    if (ratio >= 0.48) return "8th";
    if (ratio >= 0.38) return "12th";
    return "16th";
  }

  function checkpointCommentary(wins: number, draws: number, losses: number, matchday: number) {
    const profile = finalBalanceProfile.status;
    const attack = finalBalanceProfile.attack;
    const midfield = finalBalanceProfile.midfield;
    const defense = finalBalanceProfile.defense;

    if (losses === 0 && matchday > invinciblesSeasonMatches * 0.65) {
      return `${profile} is still holding, but the unbeaten run is fragile this deep into the season.`;
    }
    if (losses > 0 && defense < Math.max(attack, midfield) - 8) {
      return `The unbeaten dream has broken because the defensive line could not absorb pressure consistently.`;
    }
    if (losses > 0 && weakestPlayer) {
      return `The campaign is still alive, but ${weakestPosition} is being targeted in the decisive stretches.`;
    }
    if (midfield >= attack + 6 && midfield >= defense + 6) {
      return `Midfield control is driving the checkpoints; the question is whether both boxes can keep pace.`;
    }
    if (attack >= midfield + 7 && attack >= defense + 7) {
      return `The attack is winning shootouts, but every dropped point threatens the title pace.`;
    }
    if (defense >= attack + 7 && defense >= midfield + 7) {
      return `Defensive stability is keeping the season under control, even when the attack is not explosive.`;
    }
    if (wins >= draws + losses + 3) {
      return `${profile} has translated into a strong run of results without becoming automatic.`;
    }
    return `The record is playable, but this squad still needs cleaner control of match state.`;
  }

  function buildInvinciblesPlayLevelSteps(): PlayLevelStep[] {
    const checkpoints = invinciblesSeasonMatches === 34 ? [1, 6, 12, 19, 27] : [1, 8, 15, 23, 31];
    const record = predictedEtRecord;
    const clubOpponents = invinciblesClubUniverses().map((item) => item.club).filter((club) => club !== universe.club);
    const fallbackOpponents = ["Manchester City", "Real Madrid", "Bayern Munich", "Inter", "PSG", "Liverpool", "Barcelona"];
    const opponents = shuffle(clubOpponents.length ? clubOpponents : fallbackOpponents);
    const biggestWin = { vs: opponents[0] ?? "Title Rival", score: "4-1" };
    const biggestDefeat = record.losses > 0 ? { vs: opponents[1] ?? "Away Rival", score: "1-2" } : undefined;

    return checkpoints.map((matchday, index): PlayLevelStep => {
      const ratio = matchday / invinciblesSeasonMatches;
      const wins = Math.min(record.wins, Math.round(record.wins * ratio));
      const draws = Math.min(record.draws, Math.round(record.draws * ratio));
      const playedBeforeLosses = Math.max(0, matchday - wins - draws);
      const losses = Math.min(record.losses, playedBeforeLosses);
      const points = wins * 3 + draws;
      const goalsFor = Math.round(record.goalsFor * ratio);
      const goalsAgainst = Math.round(record.goalsAgainst * ratio);
      const invincible = losses === 0;

      return {
        id: `invincibles-${matchday}`,
        kicker: "Invincibles Play Level",
        title: `Matchday ${matchday} checkpoint`,
        stage: `Matchday ${matchday}`,
        opponent: opponents[index % Math.max(opponents.length, 1)] ?? "League Rival",
        scoreline: `${wins}-${draws}-${losses}`,
        advanced: true,
        manOfTheMatch: playLevelKeyPlayer(index),
        tacticalAnalysis: checkpointCommentary(wins, draws, losses, matchday),
        checkpointSummary: {
          position: positionFromPoints(points, etMaxPoints),
          record: `${wins}-${draws}-${losses}`,
          points,
          goalsFor,
          goalsAgainst,
          goalDifference: goalsFor - goalsAgainst,
          invincible,
          biggestWin,
          biggestDefeat
        }
      };
    });
  }

  function buildEtAlienPlayLevelSteps(): PlayLevelStep[] {
    const match = predictedEtAlienMatch;
    const opponent = match.opponent;
    const firstHalfScore = match.outcome === "loss"
      ? "0-1"
      : match.outcome === "barely"
        ? "1-1"
        : "1-0";
    const secondPhase = match.outcome === "barely"
      ? (match.scoreline.includes("pens") ? "Penalty Signal" : "Extra Time")
      : "Second Half";

    return [
      {
        id: "et-opponent",
        kicker: "Signal Review",
        title: `Opponent detected: ${opponent.name}`,
        stage: "Opponent Reveal",
        opponent: opponent.name,
        manOfTheMatch: match.keyPlayer,
        tacticalAnalysis: opponent.name === "Paradox"
          ? "The opposition is not from this timeline. Paradox has mirrored the weakest realistic football data into elite threats."
          : opponent.premise
      },
      {
        id: "et-threat",
        kicker: "Transmission Analysis",
        title: "Threat analysis",
        stage: "Threat Analysis",
        opponent: opponent.name,
        manOfTheMatch: match.keyPlayer,
        tacticalAnalysis: `Survival chance: ${match.survivalChance}%. ${match.tacticalNote}`
      },
      {
        id: "et-first-half",
        kicker: "Final Alien Match",
        title: "First half signal",
        stage: "First Half",
        opponent: opponent.name,
        scoreline: firstHalfScore,
        manOfTheMatch: match.keyPlayer,
        tacticalAnalysis: match.outcome === "loss"
          ? "Signal pressure rising. Earth's defensive shape is being dragged out of its normal rhythm."
          : "Earth's shape is stable. For now."
      },
      {
        id: "et-second-half",
        kicker: "Final Alien Match",
        title: secondPhase,
        stage: secondPhase,
        opponent: opponent.name,
        scoreline: match.outcome === "barely" ? match.scoreline : match.scoreline,
        manOfTheMatch: match.keyPlayer,
        tacticalAnalysis: match.outcome === "barely"
          ? "The signal breaks into fragments. Earth survives through the smallest possible margin."
          : match.outcome === "win"
            ? "Galactico11 bends the match back toward Earth before the final transmission."
            : "Libra instability detected. The alien pressure has found the weakest channel."
      },
      {
        id: "et-final",
        kicker: "Final Signal",
        title: match.resultText,
        stage: "Final Result",
        opponent: opponent.name,
        scoreline: match.scoreline,
        advanced: match.outcome !== "loss",
        manOfTheMatch: match.keyPlayer,
        tacticalAnalysis: match.route
      }
    ];
  }

  function buildPlayLevelSummary() {
    const invincible = predictedEtRecord.losses === 0;
    const identity = teamIdentity(picked, chemistry, positionFit).name;
    return {
      invincible,
      goldenBoot: bestPlayer?.name ?? "No standout scorer",
      bestPlayerName: bestPlayer?.name ?? "No standout player",
      biggestSurprise: hiddenGem?.name ?? "No hidden gem",
      trophyCabinet: invincible ? ["League Title", "Invincible Season"] : predictedEtRecord.position === "1st" ? ["League Title"] : ["European Qualification Push"],
      teamIdentityName: identity,
      historicalComparison: invincible ? "Arsenal 2003/04 territory" : predictedEtRecord.points >= etMaxPoints * 0.75 ? "Title-contender pace" : predictedEtRecord.points >= etMaxPoints * 0.5 ? "Competitive but imperfect campaign" : "Work-in-progress campaign",
      topWins: predictedEtRecord.wins
    };
  }

  function startPlayLevelExperience() {
    playLevelStarted = false;
    playLevelCompleted = false;
    playLevelStepIndex = 0;
    playLevelSeed = Date.now();
    playLevelSteps = draftMode === "worldcup"
      ? buildWorldCupPlayLevelSteps()
      : draftMode === "et"
        ? buildEtAlienPlayLevelSteps()
        : buildInvinciblesPlayLevelSteps();
    playLevelMaxSteps = playLevelSteps.length;
    playLevelCurrentStep = playLevelSteps[0] ?? null;
    playLevelSeasonSummary = draftMode === "invinciblesClub" ? buildPlayLevelSummary() : null;
    screen = "playLevel";
  }

  function beginPlayLevel() {
    playLevelStarted = true;
    playLevelCurrentStep = playLevelSteps[0] ?? null;
    playLevelCompleted = playLevelSteps.length === 0;
  }

  function continuePlayLevel() {
    if (!playLevelStarted) {
      beginPlayLevel();
      return;
    }

    const nextIndex = playLevelStepIndex + 1;
    if (nextIndex >= playLevelSteps.length) {
      playLevelCompleted = true;
      playLevelCurrentStep = playLevelSteps[playLevelSteps.length - 1] ?? null;
      return;
    }

    playLevelStepIndex = nextIndex;
    playLevelCurrentStep = playLevelSteps[nextIndex];
  }

  function skipPlayLevel() {
    playLevelStarted = true;
    playLevelCompleted = true;
    playLevelStepIndex = Math.max(0, playLevelSteps.length - 1);
    playLevelCurrentStep = playLevelSteps[playLevelStepIndex] ?? null;
  }

  function showRecordReveal() {
    screen = "record";
  }

  function showLibraReveal() {
    screen = "libra";
  }

  function startInvinciblesSeasonExperience() {

    if (simulationTimer) clearInterval(simulationTimer);
    simulatedWins = 0;
    simulatedDraws = 0;
    simulatedLosses = 0;
    simulationComplete = false;
    screen = "simulation";

    const season = shuffle([
      ...Array(predictedEtRecord.wins).fill("W"),
      ...Array(predictedEtRecord.draws).fill("D"),
      ...Array(predictedEtRecord.losses).fill("L")
    ]);

    let matchIndex = 0;

    simulationTimer = setInterval(() => {
      const result = season[matchIndex];
      if (result === "W") simulatedWins += 1;
      if (result === "D") simulatedDraws += 1;
      if (result === "L") simulatedLosses += 1;
      matchIndex += 1;

      if (matchIndex >= season.length) {
        if (simulationTimer) clearInterval(simulationTimer);
        simulationTimer = null;
        simulationComplete = true;
      }
    }, 125);
  }

  function enterFinalReveal() {
    revealedMysteryPlayerIds = picked.filter((player) => player.mysteryPick).map((player) => String(player.id));
    showDraftTimeline = false;
    startFinalVerdictSequence();
  }

  function prefersReducedMotion() {
    return typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  }

  function finalVerdictTitle() {
    if (draftMode === "worldcup") return `WORLD CUP RESULT: ${predictedWorldCupOutcome.toUpperCase()}`;
    if (draftMode === "et") return `FINAL SIGNAL: ${predictedEtAlienMatch.resultText.toUpperCase()}`;
    if (draftMode === "invinciblesClub") return `SEASON RESULT: ${predictedEtRecord.position.toUpperCase()}`;
    if (clubFormat === "champions") return `EUROPEAN RESULT: ${predictedChampionsLeagueOutcome.toUpperCase()}`;
    return `SEASON RESULT: ${predictedClubRecord.record}`;
  }

  function finalVerdictDetail() {
    if (draftMode === "worldcup") {
      return libraBonusActive ? `LIBRA BOOST: +${worldCupSimulation.libraBoostStages} ROUND` : `TEAM BALANCE: ${finalBalanceProfile.status.toUpperCase()}`;
    }
    if (draftMode === "et") return `OPPONENT: ${predictedEtAlienMatch.opponent.name.toUpperCase()}`;
    if (draftMode === "invinciblesClub") {
      const run = predictedEtRecord.losses === 0 ? invinciblesSeasonMatches : Math.max(6, Math.round((predictedEtRecord.wins + predictedEtRecord.draws) * 0.66));
      return `UNBEATEN RUN: ${run} MATCHES`;
    }
    if (clubFormat === "champions") return `GRADE: ${grade}`;
    return `POINTS: ${predictedClubRecord.points}`;
  }

  function completeFinalVerdict() {
    if (finalVerdictTimer) {
      clearTimeout(finalVerdictTimer);
      finalVerdictTimer = null;
    }
    finalVerdictStepIndex = finalVerdictSteps.length - 1;
    screen = "result";
  }

  function scheduleFinalVerdictStep() {
    if (finalVerdictTimer) clearTimeout(finalVerdictTimer);
    if (prefersReducedMotion()) {
      finalVerdictTimer = setTimeout(completeFinalVerdict, 350);
      return;
    }

    finalVerdictTimer = setTimeout(() => {
      if (finalVerdictStepIndex < finalVerdictSteps.length - 1) {
        finalVerdictStepIndex += 1;
        scheduleFinalVerdictStep();
      } else {
        finalVerdictTimer = setTimeout(completeFinalVerdict, 520);
      }
    }, 560);
  }

  function startFinalVerdictSequence() {
    if (finalVerdictTimer) clearTimeout(finalVerdictTimer);
    finalVerdictStepIndex = 0;
    screen = "verdict";
    scheduleFinalVerdictStep();
  }

  function skipFinalVerdict() {
    completeFinalVerdict();
  }

  function getClubSeasonRecord(avgIog: number, grade: string, matches = 38): ClubSeasonRecord {
    let minWins = 8;
    let maxWins = 15;

    if (avgIog >= 95) {
      minWins = 34;
      maxWins = 38;
    } else if (avgIog >= 90) {
      minWins = 29;
      maxWins = 34;
    } else if (avgIog >= 85) {
      minWins = 24;
      maxWins = 30;
    } else if (avgIog >= 80) {
      minWins = 19;
      maxWins = 25;
    } else if (avgIog >= 75) {
      minWins = 14;
      maxWins = 20;
    }

    const scale = matches / 38;
    minWins = Math.round(minWins * scale);
    maxWins = Math.round(maxWins * scale);

    if (grade === "S") minWins = Math.min(matches, minWins + 1);
    if (grade === "D") maxWins = Math.max(minWins, maxWins - 1);

    const gradeBoost = grade === "S" ? 1 : grade === "A+" ? 0.5 : grade === "D" ? -1 : 0;
    const wins = Math.max(0, Math.min(matches, Math.round((minWins + maxWins) / 2 + gradeBoost)));
    const remaining = matches - wins;
    const targetDraws = avgIog >= 95 ? 2 : avgIog >= 90 ? 4 : avgIog >= 85 ? 6 : avgIog >= 80 ? 8 : 9;
    const draws = Math.min(remaining, Math.round(targetDraws * scale));
    const losses = remaining - draws;

    return {
      record: `${wins}-${draws}-${losses}`,
      points: wins * 3 + draws
    };
  }

  function getChampionsLeagueOutcome(avgIog: number, grade: string, chemistryScore: number, fitScore: number) {
    const outcomes = [
      "Group Stage Exit",
      "Relegated to Europa League",
      "Round of 16",
      "Quarter Final",
      "Semi Final",
      "Final",
      "Champions"
    ];

    const gradeBoost = grade === "S" ? 3 : grade === "A+" ? 2 : grade === "A" ? 1 : grade === "D" ? -2 : 0;
    const composite = avgIog + gradeBoost + chemistryScore * 0.06 + fitScore * 0.05;

    let tier = 0;
    if (composite >= 103) tier = 6;
    else if (composite >= 99) tier = 5;
    else if (composite >= 95) tier = 4;
    else if (composite >= 90) tier = 3;
    else if (composite >= 85) tier = 2;
    else if (composite >= 80) tier = 1;

    return outcomes[Math.max(0, Math.min(outcomes.length - 1, tier))];
  }

  function primaryPosition(player: Player) {
    const preferred = getPositions(player);
    return preferred[0] ?? "CM";
  }

  function statRole(player: Player) {
    const positions = getPositions(player);

    if (positions.includes("GK")) return "GK";
    if (positions.includes("ST")) return "ST";
    if (positions.some((pos) => ["LW", "RW", "LM", "RM"].includes(pos))) return "WINGER";
    if (positions.includes("CAM")) return "CAM";
    if (positions.includes("CM")) return "CM";
    if (positions.includes("CDM")) return "CDM";
    if (positions.some((pos) => ["LB", "RB", "LWB", "RWB"].includes(pos))) return "FB";
    if (positions.includes("CB")) return "CB";

    return primaryPosition(player);
  }

  function statValue(player: Player, ...keys: string[]) {
    for (const key of keys) {
      const value = player[key as keyof Player];
      if (value !== undefined && value !== null && value !== "") {
        return value;
      }
    }
    return null;
  }

  function hasDisplayableStat(value: unknown) {
    if (value === null || value === undefined || value === "") return false;
    if (typeof value === "string") {
      const normalized = value.trim().toUpperCase();
      return normalized !== "" && normalized !== "N/A" && normalized !== "NA" && normalized !== "0" && normalized !== "0.0";
    }
    if (typeof value === "number") return Number.isFinite(value) && value !== 0;
    return true;
  }

  function formatStat(value: unknown, suffix = "") {
    if (value === null || value === undefined || value === "") return "-";
    if (typeof value === "number") {
      const formatted = Number.isInteger(value) ? String(value) : value.toFixed(1);
      return `${formatted}${suffix}`;
    }
    return `${value}${suffix}`;
  }

  function statRows(player: Player) {
    const pos = statRole(player);
    const groups: Record<string, { label: string; keys: string[]; suffix?: string }[]> = {
      GK: [
        { label: "Save %", keys: ["save_pct", "savePct"], suffix: "%" },
        { label: "Clean Sheets", keys: ["clean_sheets", "cleanSheets"] },
        { label: "PSxG Prevented", keys: ["psxg_prevented", "psxgPrevented"] },
        { label: "Distribution %", keys: ["distribution_pct", "distributionPct", "pass_pct", "passPct"], suffix: "%" }
      ],
      CB: [
        { label: "Tackles", keys: ["tackles"] },
        { label: "Interceptions", keys: ["interceptions"] },
        { label: "Aerial Wins", keys: ["aerial_wins", "aerialWins"] },
        { label: "Blocks", keys: ["blocks"] },
        { label: "Prog Passes", keys: ["progressive_passes", "progressivePasses"] }
      ],
      FB: [
        { label: "Tackles", keys: ["tackles"] },
        { label: "Interceptions", keys: ["interceptions"] },
        { label: "Assists", keys: ["assists"] },
        { label: "xA", keys: ["xa"] },
        { label: "Prog Carries", keys: ["progressive_carries", "progressiveCarries"] }
      ],
      CDM: [
        { label: "Tackles", keys: ["tackles"] },
        { label: "Interceptions", keys: ["interceptions"] },
        { label: "Recoveries", keys: ["recoveries"] },
        { label: "Prog Passes", keys: ["progressive_passes", "progressivePasses"] }
      ],
      CM: [
        { label: "Assists", keys: ["assists"] },
        { label: "Prog Passes", keys: ["progressive_passes", "progressivePasses"] },
        { label: "Tackles", keys: ["tackles"] },
        { label: "Interceptions", keys: ["interceptions"] },
        { label: "Recoveries", keys: ["recoveries"] }
      ],
      CAM: [
        { label: "Assists", keys: ["assists"] },
        { label: "xA", keys: ["xa"] },
        { label: "Key Passes", keys: ["key_passes", "keyPasses"] },
        { label: "Shot Creation", keys: ["shot_creation", "shotCreation"] },
        { label: "Prog Passes", keys: ["progressive_passes", "progressivePasses"] }
      ],
      WINGER: [
        { label: "Goals", keys: ["goals"] },
        { label: "Assists", keys: ["assists"] },
        { label: "xG", keys: ["xg"] },
        { label: "xA", keys: ["xa"] },
        { label: "Prog Carries", keys: ["progressive_carries", "progressiveCarries"] }
      ],
      ST: [
        { label: "Goals", keys: ["goals"] },
        { label: "Assists", keys: ["assists"] },
        { label: "xG", keys: ["xg"] },
        { label: "Shots", keys: ["shots"] },
        { label: "Shot Creation", keys: ["shot_creation", "shotCreation"] }
      ]
    };

    return (groups[pos] ?? groups.CM)
      .map((item) => {
        const value = statValue(player, ...item.keys);
        return {
          label: item.label,
          rawValue: value,
          value: formatStat(value, item.suffix)
        };
      })
      .filter((item) => hasDisplayableStat(item.rawValue));
  }

  function shortStatLabel(label: string) {
    const labels: Record<string, string> = {
      "Clean Sheets": "CS",
      "PSxG Prevented": "PSxG",
      "Distribution %": "Dist",
      "Interceptions": "Int",
      "Aerial Wins": "Aerial",
      "Prog Passes": "Pass",
      "Prog Carries": "Carry",
      "Shot Creation": "SC"
    };
    return labels[label] ?? label;
  }

  function restart() {
    backToMenu();
  }

  function shareFinalResult() {
    shareStatus = "";
    showShareModal = true;
  }

  function shareOutcome() {
    return draftMode === "worldcup"
      ? predictedWorldCupOutcome
      : `${predictedEtRecord.record}`;
  }

  function shareModeLabel() {
    if (draftMode === "worldcup") return "World Cup Mode";
    if (draftMode === "et") return "Invincibles — ET Mode";
    if (draftMode === "invinciblesClub") return `Invincibles — ${selectedInvinciblesConfig.shortLabel}`;
    return clubFormat === "champions" ? "Club Football — Champions League" : `Club Football — ${selectedClubLeague}`;
  }

  function sharePlayerRows() {
    return picked.map((player) => ({
      position: player.assignedPosition,
      name: isMysteryIdentityHidden(player) ? "Mystery Pick" : player.name,
      context: displayTeamContext(player),
      era: player.era,
      iog: formatIoG(player.adjustedIog)
    }));
  }

  function escapeSvg(value: unknown) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function shareText() {
    return `Galactico11: ${shareOutcome()} • Grade ${grade} • Team IoG ${displayAvgIog}. Every pick has a consequence.`;
  }

  function shareUrl() {
    return typeof window === "undefined" ? "https://galactico11.com" : window.location.href;
  }

  function openShareTarget(target: "twitter" | "facebook" | "whatsapp" | "telegram" | "reddit") {
    const text = encodeURIComponent(shareText());
    const url = encodeURIComponent(shareUrl());
    const targets = {
      twitter: `https://twitter.com/intent/tweet?text=${text}&url=${url}`,
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${url}`,
      whatsapp: `https://wa.me/?text=${text}%20${url}`,
      telegram: `https://t.me/share/url?url=${url}&text=${text}`,
      reddit: `https://www.reddit.com/submit?url=${url}&title=${text}`
    };
    window.open(targets[target], "_blank", "noopener,noreferrer");
  }

  async function copyShareLink() {
    await navigator.clipboard?.writeText(`${shareText()} ${shareUrl()}`);
    shareStatus = "Copied";
    setTimeout(() => (shareStatus = ""), 1800);
  }

  function shareCardSvg() {
    const rows = sharePlayerRows()
      .slice(0, 11)
      .map((player, index) => {
        const y = 510 + index * 58;
        return `
          <rect x="72" y="${y - 34}" width="936" height="46" rx="18" fill="${index % 2 === 0 ? "#151923" : "#10131c"}" stroke="#242938"/>
          <rect x="92" y="${y - 22}" width="58" height="24" rx="12" fill="#c9a646"/>
          <text x="121" y="${y - 5}" fill="#080a0f" font-size="16" font-weight="900" text-anchor="middle">${escapeSvg(player.position)}</text>
          <text x="170" y="${y - 8}" fill="#ffffff" font-size="23" font-weight="850">${escapeSvg(player.name)}</text>
          <text x="170" y="${y + 14}" fill="#9ba1b0" font-size="16">${escapeSvg(player.context)} • ${escapeSvg(player.era)} • IoG ${escapeSvg(player.iog)}</text>
        `;
      })
      .join("");

    return `
      <svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1350" viewBox="0 0 1080 1350">
        <defs>
          <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
            <stop stop-color="#07080d"/><stop offset="0.58" stop-color="#111827"/><stop offset="1" stop-color="#211b0c"/>
          </linearGradient>
          <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
            <stop stop-color="#171b25"/><stop offset="1" stop-color="#0c0e15"/>
          </linearGradient>
        </defs>
        <rect width="1080" height="1350" fill="url(#bg)"/>
        <circle cx="880" cy="150" r="245" fill="none" stroke="#c9a646" stroke-opacity=".18" stroke-width="2"/>
        <circle cx="875" cy="150" r="160" fill="none" stroke="#ffffff" stroke-opacity=".08" stroke-width="1"/>
        <rect x="44" y="44" width="992" height="1262" rx="42" fill="url(#panel)" stroke="#3a2f13" stroke-width="2"/>
        <text x="72" y="118" fill="#c9a646" font-family="Inter, Arial" font-size="24" font-weight="900" letter-spacing="7">GALACTICO11</text>
        <text x="72" y="188" fill="#ffffff" font-family="Inter, Arial" font-size="48" font-weight="950">Share your team</text>
        <text x="72" y="230" fill="#9ba1b0" font-family="Inter, Arial" font-size="22">${escapeSvg(shareModeLabel())}</text>
        <rect x="72" y="284" width="936" height="160" rx="30" fill="#0d1018" stroke="#2a2f3d"/>
        <text x="104" y="334" fill="#8f95a5" font-family="Inter, Arial" font-size="18" font-weight="900" letter-spacing="4">${draftMode === "worldcup" ? "TOURNAMENT RESULT" : "PROJECTED RECORD"}</text>
        <text x="104" y="398" fill="#ffffff" font-family="Inter, Arial" font-size="56" font-weight="950">${escapeSvg(shareOutcome())}</text>
        <text x="734" y="338" fill="#8f95a5" font-family="Inter, Arial" font-size="17" font-weight="900" letter-spacing="4">GRADE</text>
        <text x="734" y="400" fill="#c9a646" font-family="Inter, Arial" font-size="58" font-weight="950">${escapeSvg(grade)}</text>
        <text x="870" y="338" fill="#8f95a5" font-family="Inter, Arial" font-size="17" font-weight="900" letter-spacing="4">TEAM IOG</text>
        <text x="870" y="398" fill="#ffffff" font-family="Inter, Arial" font-size="42" font-weight="950">${escapeSvg(displayAvgIog)}</text>
        <text x="72" y="476" fill="#c9a646" font-family="Inter, Arial" font-size="18" font-weight="900" letter-spacing="5">FINAL XI</text>
        ${rows}
        <line x1="72" y1="1210" x2="1008" y2="1210" stroke="#2a2f3d"/>
        <text x="72" y="1262" fill="#c9a646" font-family="Inter, Arial" font-size="22" font-weight="900" letter-spacing="5">GALACTICO11</text>
        <text x="1008" y="1262" fill="#8f95a5" font-family="Inter, Arial" font-size="18" font-weight="700" text-anchor="end">Created by Zain Ahmed</text>
      </svg>`;
  }

  async function downloadShareImage() {
    shareStatus = "Preparing image";
    const svg = shareCardSvg();
    const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const image = new Image();

    image.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = 1080;
      canvas.height = 1350;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(image, 0, 0);
      URL.revokeObjectURL(url);
      canvas.toBlob((pngBlob) => {
        if (!pngBlob) return;
        const pngUrl = URL.createObjectURL(pngBlob);
        const link = document.createElement("a");
        link.href = pngUrl;
        link.download = "galactico11-share-card.png";
        link.click();
        URL.revokeObjectURL(pngUrl);
        shareStatus = "Downloaded";
        setTimeout(() => (shareStatus = ""), 1800);
      }, "image/png");
    };

    image.onerror = () => {
      URL.revokeObjectURL(url);
      shareStatus = "Download failed";
    };

    image.src = url;
  }
</script>

<main class="page" class:et-mode={etSkinActive} style={`--accent:${accent}`}>
  {#if etSkinActive}
    <div class="et-ambience" aria-hidden="true">
      <div class="et-cosmic-fog"></div>
      <div class="et-stars"></div>
      <div class="et-ufo et-ufo-one"></div>
      <div class="et-ufo et-ufo-two"></div>
      <div class="et-scanline"></div>
      <div class="et-static-noise"></div>
    </div>
  {/if}

  {#if screen !== "loading" && screen !== "analysis" && screen !== "simulation" && screen !== "record" && screen !== "libra" && screen !== "verdict"}
    <nav class="nav" class:menu-nav={screen === "menu"}>
      <div class="nav-brand">
        <img src="/logo-white.png" alt="Galactico11" />
        {#if screen !== "menu"}
          <span>{headerTitle}</span>
        {/if}
      </div>

      <div class="mode-nav-icons" aria-label="Mode navigation">
        <button
          type="button"
          class="mode-nav-button et"
          class:active={screen !== "menu" && screen !== "mode" && draftMode === "et"}
          on:click={() => navigateMode("et")}
          aria-label="Go to ET Mode"
          title="ET Mode"
        >
          <img src="/aliennav.png" alt="" />
        </button>
        <button
          type="button"
          class="mode-nav-button worldcup"
          class:active={screen !== "menu" && screen !== "mode" && draftMode === "worldcup"}
          on:click={() => navigateMode("worldcup")}
          aria-label="Go to World Cup Mode"
          title="World Cup Mode"
        >
          <img src="/world-cup.png" alt="" />
        </button>
        <button
          type="button"
          class="mode-nav-button invincibles"
          class:active={screen !== "menu" && screen !== "mode" && (draftMode === "invinciblesClub" || draftMode === "club")}
          on:click={() => navigateMode("invinciblesClub")}
          aria-label="Go to Invincibles Mode"
          title="Invincibles Mode"
        >
          <img src="/league.png" alt="" />
        </button>
      </div>

      <div class="header-iog-help">
        <span class="iog-help-label">What is IoG?</span>
        <span>
          IoG means Impact on Game.<br /><br />
          It combines position-specific performance, competition level, career quality and overall influence.
        </span>
      </div>
    </nav>
  {/if}

  {#if screen === "menu"}
    <section class="main-menu">
      <div class="hero-shell">
        <div class="classified-stars" aria-hidden="true"></div>
        <div class="orbital-map" aria-hidden="true"></div>
        <div class="hero-depth" aria-hidden="true"></div>
        <div class="hero-content">
          <div class="hero-copy-column">
            <div class="hero-system-label">
              <img class="mobile-menu-logo" src="/logo-white.png" alt="Galactico11" />
              <span>CLASSIFIED XI SYSTEM</span>
            </div>
            <h1>Every pick<br />has a<br />consequence.</h1>
            <p class="hero-copy">A football intelligence simulation.</p>
            <p class="hero-tagline">Draft an XI. Test the system. Survive the result.</p>
            <div class="menu-actions">
              <button class="primary" on:click={startDraftFlow}>Start Draft</button>
              <a class="secondary about-inline-link" href="#about-galactico">About Galactico</a>
            </div>
            <div class="hero-status-row" aria-label="System status">
              <span>0/11 Selected</span>
              <span>Consequence Engine Idle</span>
              <span>Draft Model Armed</span>
            </div>
          </div>
          <div class="hero-intel-panel" aria-hidden="true">
            <span>SYSTEM ONLINE</span>
            <span>XI BUILDER READY</span>
            <span>IoG MODEL ACTIVE</span>
            <span>SIMULATION LOCKED</span>
          </div>
        </div>
      </div>

      <article id="about-galactico" class="about-card">
        <p class="entry-word">GALÁCTICO</p>
        <p class="entry-kind">noun</p>
        <div class="entry-prose">
          <p>Galáctico is the Spanish term for ‘galactic’ and is used in football to describe players whose talent is considered out of this world.</p>
          <p>To be considered a Galáctico, a player must not only perform at the highest level but also possess a reputation that transcends the sport itself.</p>
          <p>A true Galáctico is recognised globally, influences generations, and leaves a lasting mark on football history.</p>
        </div>
      </article>
    </section>
  {/if}

  {#if screen === "loading"}
    <section class="loading-screen" class:exiting={loadingExiting} aria-label="Loading draft">
      <div class="loading-ball" aria-hidden="true">
        <svg viewBox="0 0 120 120" role="presentation">
          <circle cx="60" cy="60" r="55" fill="#f8f8f8" stroke="#111" stroke-width="3" />
          <path d="M60 29 78 42 71 64 49 64 42 42Z" fill="#111" />
          <path d="M60 29 60 9M78 42 102 34M71 64 86 86M49 64 34 86M42 42 18 34" fill="none" stroke="#111" stroke-width="3" stroke-linecap="round" />
          <path d="M60 9 91 18 102 34 108 61 96 91 75 109 45 109 24 91 12 61 18 34 29 18Z" fill="none" stroke="#111" stroke-width="3" stroke-linejoin="round" />
          <path d="M29 18 42 42M91 18 78 42M96 91 86 86M24 91 34 86M45 109 34 86M75 109 86 86M12 61 49 64M108 61 71 64" fill="none" stroke="#111" stroke-width="2" stroke-linecap="round" opacity="0.95" />
          <path d="M21 34 29 18 60 9 91 18 99 34 78 42 60 29 42 42Z" fill="#fff" opacity="0.28" />
        </svg>
      </div>
      <strong>{loadingPercent}%</strong>
    </section>
  {/if}

  {#if screen === "mode"}
    <section class="panel mode-screen">
      <button class="back-link" on:click={backToMenu}>Back</button>
      <h1>Choose your stage</h1>
      <div class="quick-loop" aria-label="Galactico11 flow">
        <span>Pick a star</span>
        <i></i>
        <span>Watch balance move</span>
        <i></i>
        <span>Simulate the consequence</span>
      </div>

      <div class="mode-grid">
        <button
          class="mode-card group overflow-hidden rounded-lg border border-yellow-500/30 bg-white/[0.04] text-left transition-all duration-300 hover:-translate-y-1 hover:border-yellow-400/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-yellow-400"
          class:tutorial-highlight={showPhoebeTutorial && tutorialStep === 1}
          class:tutorial-dim={showPhoebeTutorial && (tutorialStep === 2 || tutorialStep === 3)}
          on:click={() => chooseTutorialMode("worldcup")}
          aria-label="Choose World Cup 2026 mode"
        >
          <img
            class="mode-card-image"
            src="/world-cup.png"
            alt="World Cup 2026"
          />
          <div class="mode-card-content">
            <strong class="text-white">World Cup 2026</strong>
            <span class="mode-badge">Realistic</span>
            <em>Build a nation’s XI. Survive the tournament.</em>
            <div class="mode-preview">
              <span>Nation pools</span>
              <span>Knockouts</span>
              <span>Pressure picks</span>
            </div>
            <span class="mode-select-label">Select</span>
          </div>
        </button>

        <button
          class="mode-card group overflow-hidden rounded-lg border border-yellow-500/30 bg-white/[0.04] text-left transition-all duration-300 hover:-translate-y-1 hover:border-yellow-400/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-yellow-400"
          class:tutorial-highlight={showPhoebeTutorial && tutorialStep === 2}
          class:tutorial-dim={showPhoebeTutorial && (tutorialStep === 1 || tutorialStep === 3)}
          on:click={() => chooseTutorialMode("invinciblesClub")}
          aria-label="Choose Invincibles Mode"
        >
          <img
            class="mode-card-image"
            src="/invincibles.png"
            alt="Invincibles Mode"
          />
          <div class="mode-card-content">
            <strong class="text-white">Invincibles Mode</strong>
            <span class="mode-badge">Club Season</span>
            <em>Draft a club side. Chase an unbeaten season.</em>
            <div class="mode-preview">
              <span>38 matches</span>
              <span>Streak meter</span>
              <span>Title pressure</span>
            </div>
            <span class="mode-select-label">Select</span>
          </div>
        </button>

        <button
          class="mode-card et-mode-card group overflow-hidden rounded-lg border border-yellow-500/30 bg-white/[0.04] text-left transition-all duration-300 hover:-translate-y-1 hover:border-yellow-400/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-yellow-400"
          class:tutorial-highlight={showPhoebeTutorial && tutorialStep === 3}
          class:tutorial-dim={showPhoebeTutorial && (tutorialStep === 1 || tutorialStep === 2)}
          on:click={openEtMode}
          aria-label="Choose ET Mode"
        >
          <div class="mode-card-content">
            <strong class="text-white">ET Mode</strong>
            <span class="mode-badge">Signature Mode</span>
            <em>Build Earth’s XI. Survive the signal.</em>
            <div class="mode-preview et-preview">
              <span>Free draft</span>
              <span>Alien threat</span>
              <span>Superteam chaos</span>
            </div>
            <span class="mode-select-label">Select</span>
          </div>
        </button>
      </div>
    </section>
  {/if}

  {#if screen === "etIntro"}
    <section class="panel mode-screen et-intro-screen">
      <button class="back-link" on:click={backFromEtIntro}>Back</button>

      <div class="et-intro-body">
        <div class="et-intro-sigil" aria-hidden="true">
          <img src="/alien.png" alt="" />
        </div>
        <p class="kicker">Signal Contact</p>
        <h1>Unknown Signal Detected</h1>
        <p class="muted">Earth has been challenged to a final competition. Something beyond football is interfering with the broadcast — and with your draft.</p>
        <p class="muted">Build the Galactico11 XI. Trust your football intelligence: the signal cannot be relied on to tell you everything.</p>
        <button class="primary" on:click={continueFromEtIntro}>Begin Formation Select</button>
      </div>
    </section>
  {/if}

  {#if screen === "clubFormat"}
    <section class="panel mode-screen">
      <button class="back-link" on:click={backToMode}>Back</button>
      {#if draftMode === "invinciblesClub"}
        <img class="desktop-mode-logo" src="/clubfootball.png" alt="Club Football" />
        <h1>Choose Club Mode Challenge</h1>
        <p class="muted">Pick the league. Each round will scout a single random club from that pool.</p>

        <div class="challenge-grid">
          {#each invinciblesChallenges as challenge}
            <button on:click={() => chooseInvinciblesChallenge(challenge.id)}>
              <strong>{challenge.label}</strong>
              <span>{challenge.description}</span>
            </button>
          {/each}
        </div>
      {:else}
        <h1>Choose Club Format</h1>

        <div class="mode-grid">
          <div class="mode-option">
            <strong>League Format</strong>
            <span>Draft for a domestic season across one major league.</span>

            <div class="league-buttons">
              {#each clubLeagueOptions as league}
                <button on:click={() => chooseLeagueFormat(league)}>
                  <strong>{league}</strong>
                  <span>{leagueMatchCounts[league]} games</span>
                </button>
              {/each}
            </div>
          </div>

          <button on:click={chooseChampionsLeagueFormat}>
            <strong>Champions League Format</strong>
            <span>Draft from a 32-club European field.</span>
          </button>
        </div>
      {/if}
    </section>
  {/if}

  {#if screen === "formation"}
    <section class="panel formation-screen">
      <button class="back-link" on:click={backFromFormation}>Back</button>
      <p class="kicker">Galactico11</p>
      <h1>Choose Formation</h1>
      <p class="muted">Pick the shape of your eleven.</p>

      <div class="formation-grid">
        {#each Object.keys(formations) as item}
          <button on:click={() => chooseFormation(item)}>
            <span>Formation</span>
            <strong>{item}</strong>
          </button>
        {/each}
      </div>
    </section>
  {/if}

  {#if screen === "draft"}
    <section class="draft-grid">
      <div class="panel left">
        <div class="draft-head">
          <div>
            <p class="kicker">{isGoldenRound ? goldenRoundTitle : currentUniverseTitle}</p>
            <h1>{isGoldenRound ? "Full Player Pool" : "Choose one player"}</h1>
          </div>

          <div class="counter">{picked.length}/11</div>
        </div>

        {#if lastAssignedPlayer && picked.length > 0}
          <div class="pick-impact-strip" aria-live="polite">
            <div>
              <span>Last Pick</span>
              <strong>
                {#if isMysteryIdentityHidden(lastAssignedPlayer)}
                  Mystery Pick
                {:else}
                  {lastAssignedPlayer.name}
                {/if}
              </strong>
            </div>
            <div>
              <span>IoG</span>
              <strong>{isMysteryIdentityHidden(lastAssignedPlayer) ? "???" : formatIoG(lastAssignedPlayer.adjustedIog)}</strong>
            </div>
            <p>{pickReaction}</p>
          </div>
        {/if}

        <div class="mobile-draft-sticky" aria-label="Mobile draft controls">
          <div class="mobile-draft-pills">
            <span aria-label={`Formation ${formation}`}><i>⚽</i>{formation}</span>
            <span aria-label={`Libra Score ${libraScore ?? "-"}`}><i>⚖</i>{libraScore ?? "-"}</span>
            <span aria-label={`Team Balance ${finalBalanceProfile.status}`}><i>⚡</i>{finalBalanceProfile.status}</span>
            <span aria-label={`Chemistry ${chemistry}%`}><i>⌬</i>{chemistry}%</span>
            <span aria-label={`Draft progress ${picked.length} of 11`}><i>✓</i>{picked.length}/11</span>
            <span aria-label={`${respinsRemaining} respins remaining`}><i>↻</i>{respinsRemaining}</span>
          </div>

          {#if pickChips.length > 0}
            <div class="pick-chips mobile-pick-chips" aria-live="polite" aria-atomic="true">
              {#each pickChips as chip (chip.text)}
                <span class="pick-chip pick-chip-{chip.tone}">{chip.text}</span>
              {/each}
            </div>
          {/if}

          <div class="mobile-squad-tracker" aria-label={`Selected ${picked.length} of 11 players`}>
            <div class="mobile-squad-slots">
              {#each pitchSlots as slot}
                <button
                  class:filled={slot.state === "filled"}
                  class:eligible={slot.state === "eligible"}
                  class:locked={slot.state === "locked"}
                  class:selected={selectedSlotId === slot.id}
                  class:just-assigned={lastAssignedSlotId === slot.id}
                  disabled={slot.state === "filled" || slot.state === "locked"}
                  style={`left:${slot.x}%; top:${slot.y}%`}
                  on:click={() => clickSlot(slot)}
                  aria-label={`${slot.label} squad slot`}
                >
                  {#if slot.player}
                    {#if isMysteryIdentityHidden(slot.player)}
                      <strong>???</strong>
                      <small>{slot.label}</small>
                    {:else}
                      <strong>{initials(slot.player.name)}</strong>
                      <small>{formatIoG(slot.player.adjustedIog)}</small>
                    {/if}
                  {:else}
                    <strong>{slot.label}</strong>
                    <small>Empty</small>
                  {/if}
                </button>
              {/each}
            </div>
          </div>

          {#if selectedPlayer}
            <div class="mobile-assign-strip">
              <span>
                {#if isMysteryCardHidden(selectedPlayer)}
                  Mystery Pick selected
                {:else}
                  {selectedPlayer.name} selected
                {/if}
              </span>
              <button class="primary" disabled={!selectedSlotId} on:click={() => assignSelected()}>
                Assign {selectedSlotId ? slots.find((s) => s.id === selectedSlotId)?.label : ""}
              </button>
            </div>
          {/if}
        </div>

        {#if isGoldenRound || draftMode !== "et"}
          <div class="universe-grid">
          {#if isGoldenRound}
            <div class:spinning={isSpinning}>
              <span>Special Round</span>
              <strong>{draftMode === "worldcup" ? "Golden Pick" : "Golden Pick"}</strong>
            </div>

            <div class:spinning={isSpinning}>
              <span>{draftMode === "worldcup" ? "Country" : "Pool"}</span>
              <strong>{draftMode === "worldcup" ? universe.club : "Full Player Pool"}</strong>
            </div>

            <div class:spinning={isSpinning}>
              <span>Remaining</span>
              <strong>{options.length}</strong>
            </div>

            <div>
              <span>Respins</span>
              <strong>{respinsRemaining}</strong>
            </div>
          {:else}
            <div class:spinning={isSpinning}>
              <span>Competition</span>
              <strong>{isWorldCupUniverse(universe) ? "World Cup" : "Club Football"}</strong>
            </div>

            <div class:spinning={isSpinning}>
              <span>Team</span>
              <strong>{universe.club}</strong>
            </div>

            <div class:spinning={isSpinning}>
              <span>Era</span>
              <strong>{universe.era}</strong>
            </div>

            <div>
              <span>Respins</span>
              <strong>{respinsRemaining}</strong>
            </div>
          {/if}
          </div>
        {/if}

        <div class="controls">
          <button class="secondary" on:click={backFromDraft}>Back</button>

          {#if !canPick && !isSpinning}
            <button class="primary" on:click={() => spinUniverse(false)}>Spin universe</button>
          {/if}

          {#if canPick && !isSpinning && respinsRemaining > 0}
            <button class="secondary" on:click={() => spinUniverse(true)}>Use respin</button>
          {/if}
        </div>

        {#if draftMode === "et" && (isSpinning || etSignalSearching)}
          <div class="et-signal-search" aria-live="polite">
            <div class="et-signal-orb">
              <img src="/alien.png" alt="" />
            </div>
            <strong>{etSignalText}</strong>
            <span>Signal sweep in progress</span>
          </div>
        {:else if isSpinning}
          <div class="status">Spinning universe...</div>
        {/if}

        {#if isSpinning && lastPickLabel}
          <div class="notice pick-result">{lastPickLabel}</div>
        {/if}

        {#if fallbackNotice}
          <div class="notice">{fallbackNotice}</div>
        {/if}

        {#if canPick && !isSpinning}
          {#if isGoldenRound}
            <div class="notice golden-round">{draftMode === "worldcup" ? `Golden Pick • ${universe.club} • Full Pool` : "⭐ GOLDEN PICK — Full Player Pool"}</div>
          {/if}

          {#if !isMysteryRound}
            <div class="pool-tools">
              <input class="search" bind:value={search} placeholder="Search player..." />

              <select bind:value={positionFilter} aria-label="Filter by position">
                <option value="ALL">All positions</option>
                {#each positionChoices as position}
                  <option value={position}>{position}</option>
                {/each}
              </select>

              <select bind:value={sortKey} aria-label="Sort players">
                <option value="iog_desc">IoG ↓</option>
                <option value="iog_asc">IoG ↑</option>
                <option value="name">Name A-Z</option>
                <option value="best_fit">Best Fit</option>
                <option value="goals">Goals</option>
                <option value="assists">Assists</option>
              </select>
            </div>
          {/if}

          <p class="spots">
            {picked.length}/11 selected — {filteredOptions.length} of {options.length} round options shown
          </p>

          <div class="player-list">
            {#each visibleOptions as player}
              <div
                class="player-card"
                class:selected={selectedPlayer?.id === player.id}
                class:emergency={player.emergency}
                class:incompatible={player.slotCount === 0}
                class:golden={isGoldenRound}
                role="button"
                tabindex="0"
                on:click={(event) => {
                  if ((event.target as HTMLElement).closest(".stats-details")) return;
                  selectPlayer(player);
                }}
                on:keydown={(event) => {
                  if (event.key === "Enter" || event.key === " ") selectPlayer(player);
                }}
              >
                <span class="draft-label">{draftLabel(player)}</span>
                <div class="player-main">
                  <div>
                    {#if isMysteryCardHidden(player)}
                      <strong class="mystery-unknown">Mystery Pick</strong>
                      <small>Eligible Slot: {eligibleSlotLabels(player)[0] ?? "?"}</small>
                    {:else}
                      <strong class="desktop-player-name">{player.name}</strong>
                      <div class="mobile-player-head">
                        <div class="mobile-player-initials" aria-hidden="true">{initials(player.name)}</div>
                        <div>
                          <strong>{player.name}</strong>
                          <small>{getPositions(player).join(" · ")}</small>
                          <small>{displayTeamContext(player)} · {player.era}</small>
                        </div>
                        <div class="mobile-card-metrics">
                          <b>{formatIoG(player.adjustedIog)}</b>
                          {#each statRows(player).slice(0, 2) as stat}
                            <span>{shortStatLabel(stat.label)} {stat.value}</span>
                          {/each}
                        </div>
                      </div>
                      <small class="desktop-player-meta">
                        {displayTeamContext(player)} · {getPositions(player).join(" · ")} · {player.era}
                      </small>
                      <div class="iog-line">
                        <span>IoG</span>
                        <b>{formatIoG(player.adjustedIog)}</b>
                        {#if player.slotCount === 0}
                          <em>No open compatible slot</em>
                        {/if}
                      </div>
                    {/if}
                    {#if !isMysteryCardHidden(player)}
                      <div class="slot-info">
                        <span>Positions: <b>{getPositions(player).join(", ") || "-"}</b></span>
                        <span>Eligible Slots: <b>{eligibleSlotLabels(player).join(", ") || "-"}</b></span>
                      </div>
                    {/if}
                    {#if !isMysteryCardHidden(player) && statRows(player).length > 0}
                      <details class="stats-details">
                        <summary class="stats-toggle">Expand Stats</summary>
                        <div class="iog-breakdown">
                          {#each breakdownRows(player) as row}
                            <span>{row[0]} <b>{formatIoG(row[1])}</b></span>
                          {/each}
                        </div>
                        <div class="real-stats">
                          {#each statRows(player) as stat}
                            <span>{stat.label} <b>{stat.value}</b></span>
                          {/each}
                        </div>
                      </details>
                    {/if}
                  </div>
                </div>
              </div>
            {/each}
          </div>

          {#if visibleOptions.length < filteredOptions.length}
            <button
              class="secondary load-more-options"
              type="button"
              on:click={() => (visibleOptionLimit += 80)}
            >
              Load more players ({filteredOptions.length - visibleOptions.length} remaining)
            </button>
          {/if}

          {#if filteredOptions.length === 0}
            <div class="status danger">No players visible. Clear search or add more players.</div>
          {/if}

        {/if}

        <div class="progress">
          {#each Array(11) as _, i}
            <div class:active={i < picked.length}></div>
          {/each}
        </div>

        <div class="mobile-live-balance">
          <TeamBalanceHexagon players={picked} {formation} {chemistry} {positionFit} />
        </div>
      </div>

      <div class="panel right">
        <div class="board-head">
          <h2>Formation Board</h2>

          <div class="board-status">
            <div class="chemistry-pill">Chemistry <strong>{chemistry}%</strong></div>
            {#if selectedPlayer}
              <div class="selection-pill">
                {isMysteryCardHidden(selectedPlayer) ? "Mystery Pick" : selectedPlayer.name} selected
              </div>
            {:else}
              <div class="selection-pill muted-pill">
                Select a player
              </div>
            {/if}
          </div>
        </div>

        <div class="pitch">
          {#each pitchSlots as slot}
            <button
              class:filled={slot.state === "filled"}
              class:eligible={slot.state === "eligible"}
              class:locked={slot.state === "locked"}
              class:selected={selectedSlotId === slot.id}
              class:just-assigned={lastAssignedSlotId === slot.id}
              disabled={slot.state === "filled" || slot.state === "locked"}
              style={`left:${slot.x}%; top:${slot.y}%`}
              on:click={() => clickSlot(slot)}
            >
              {#if slot.player}
                {#if isMysteryIdentityHidden(slot.player)}
                  <span class="mystery-pitch-label">{mysteryLabel()}</span>
                  <small>???</small>
                {:else}
                  <span>{initials(slot.player.name)}</span>
                  <small>IoG {formatIoG(slot.player.adjustedIog)}</small>
                {/if}
              {:else}
                <span>+</span>
                <strong>{slot.label}</strong>
              {/if}
            </button>
          {/each}
        </div>

        <div class="pick-impact-row" class:empty={pickChips.length === 0} aria-live="polite" aria-atomic="true">
          {#if pickChips.length > 0}
            <span class="pick-impact-label">Pick Impact</span>
            <div class="pick-chips">
              {#each pickChips as chip (chip.text)}
                <span class="pick-chip pick-chip-{chip.tone}">{chip.text}</span>
              {/each}
            </div>
          {/if}
        </div>

        <div class="live-analysis-visual">
          <TeamBalanceHexagon players={picked} {formation} {chemistry} {positionFit} />
        </div>

        {#if selectedPlayer}
          <div class="assign-panel">
            <div>
              <strong>{isMysteryCardHidden(selectedPlayer) ? "Mystery Pick" : selectedPlayer.name}</strong>
              <span>
                {#if isMysteryCardHidden(selectedPlayer)}
                  Eligible Slot: {eligibleSlotLabels(selectedPlayer)[0] ?? "?"}
                {:else}
                  {getPositions(selectedPlayer).join(" · ")}
                {/if}
              </span>
              <small>
                Choose a highlighted compatible slot.
              </small>
            </div>

            <button class="primary" disabled={!selectedSlotId} on:click={() => assignSelected()}>
              Assign {selectedSlotId ? slots.find((s) => s.id === selectedSlotId)?.label : ""}
            </button>
          </div>
        {/if}
      </div>

      {#if selectedPlayer}
        <button
          type="button"
          class="mobile-sheet-backdrop"
          aria-label="Close position chooser"
          on:click={() => { selectedPlayer = null; selectedSlotId = ""; }}
        ></button>
        <div class="mobile-slot-sheet" role="dialog" aria-label="Assign selected player">
          <div class="mobile-slot-sheet-handle"></div>
          <header>
            <div>
              <span>Assign Player</span>
              <strong>{isMysteryCardHidden(selectedPlayer) ? "Mystery Pick" : selectedPlayer.name} — Choose Position</strong>
            </div>
            <button type="button" aria-label="Close position chooser" on:click={() => { selectedPlayer = null; selectedSlotId = ""; }}>×</button>
          </header>
          <p>Tap an eligible spot.</p>
          <div class="mobile-slot-list">
            {#each pitchSlots as slot}
              <button
                type="button"
                class:eligible={slot.state === "eligible"}
                class:filled={slot.state === "filled"}
                class:unavailable={slot.state === "locked"}
                class:selected={selectedSlotId === slot.id}
                class:just-assigned={lastAssignedSlotId === slot.id}
                disabled={slot.state !== "eligible"}
                on:click={() => assignSelected(slot)}
              >
                <strong>{slot.label}</strong>
                <span>
                  {#if slot.state === "filled"}
                    Filled
                  {:else if slot.state === "eligible"}
                    Eligible
                  {:else}
                    N/A
                  {/if}
                </span>
              </button>
            {/each}
          </div>
          {#if getCompatibleSlots(selectedPlayer).length === 0}
            <p class="mobile-slot-warning">No open compatible slot found for this player.</p>
          {/if}
        </div>
      {/if}
    </section>
  {/if}

  {#if screen === "bench"}
    <section class="panel bench-screen">
      <header class="bench-header">
        <div>
          <p class="kicker">Optional Bench Round</p>
          <h1>Build Your Bench</h1>
          <p class="bench-subtitle">Pick up to 5 substitutes — tap a player to assign them.</p>
        </div>
        <div class="bench-counter">
          <span class="bench-counter-value">{benchCandidates.length}</span>
          <span class="bench-counter-label">/ 5</span>
        </div>
      </header>

      <div class="bench-slots-row">
        {#each benchRoleSlots as slot, i}
          {@const sub = benchCandidates.find((c) => c.benchRole === slot.role)}
          {@const subIndex = sub ? benchCandidates.indexOf(sub) : -1}
          <div class="bench-slot" class:bench-slot-filled={Boolean(sub)}>
            <span class="bench-slot-label">{slot.label}</span>
            {#if sub}
              <strong class="bench-slot-name">{sub.name}</strong>
              <small class="bench-slot-iog">IoG {formatIoG(sub.adjustedIog)}</small>
              <button
                type="button"
                class="bench-slot-remove"
                aria-label="Remove {sub.name} from bench"
                on:click={() => removeFromBench(subIndex)}
              >×</button>
            {:else}
              <span class="bench-slot-empty">{slot.role}</span>
            {/if}
          </div>
        {/each}
      </div>

      {#if benchCandidates.length > 0}
        {@const impact = calculateBenchImpact(benchCandidates)}
        <div class="bench-live-impact">
          <span>Bench Strength <strong>{impact.strength}%</strong></span>
          <span>Tactical Flexibility <strong>{impact.flexibility}</strong></span>
          <span>Late Threat <strong>+{impact.lateThreat}%</strong></span>
          <span>Fatigue Resistance <strong>+{impact.fatigue}%</strong></span>
        </div>
      {/if}

      <div class="bench-pool-header">
        <span>Available Players ({filteredBenchPool.length})</span>
        <input
          type="text"
          class="bench-search-input"
          bind:value={benchSearch}
          placeholder="Search by name..."
          aria-label="Search bench players"
        />
      </div>

      <div class="bench-pool-grid" aria-label="Available bench players">
        {#each filteredBenchPool.slice(0, 40) as player}
          <button
            type="button"
            class="bench-pool-card"
            disabled={benchCandidates.length >= 5}
            aria-label="Add {player.name} to bench"
            on:click={() => addToBench(player)}
          >
            <div class="bench-pool-info">
              <strong>{player.name}</strong>
              <small>{getPositions(player).join(" · ")} · {displayTeamContext(player)}</small>
            </div>
            <b class="bench-pool-iog">IoG {formatIoG(player.adjustedIog)}</b>
          </button>
        {/each}
        {#if filteredBenchPool.length === 0}
          <p class="bench-pool-empty">No players found. Clear the search.</p>
        {/if}
      </div>

      {#if benchCandidates.length > 0}
        <div class="bench-phoebe">
          <img src="/phoebe.png" alt="Phoebe" />
          <p>{calculateBenchImpact(benchCandidates).note}</p>
        </div>
      {/if}

      <div class="bench-actions">
        <button class="primary" on:click={acceptBench}>
          {benchCandidates.length === 5 ? "Confirm Bench" : benchCandidates.length > 0 ? `Confirm ${benchCandidates.length} Sub${benchCandidates.length > 1 ? "s" : ""}` : "Skip — No Bench"}
        </button>
        {#if benchCandidates.length > 0}
          <button class="secondary" on:click={skipBench}>Skip Bench</button>
        {/if}
      </div>
    </section>
  {/if}

  {#if screen === "analysis" && currentAnalysisStep}
    <section
      class={`analysis-stage analysis-${currentAnalysisStep.tone}`}
      aria-label={`Phoebe post-draft analysis, ${currentAnalysisStep.kicker}`}
    >
      <button class="analysis-click-surface" aria-label="Continue post-draft analysis" on:click={advancePostDraftAnalysis}></button>

      <header class="analysis-header">
        <img src="/logo-white.png" alt="Galactico11" />
        <button class="analysis-skip" on:click={skipPostDraftAnalysis}>Skip Analysis</button>
      </header>

      <div class="analysis-progress" aria-label={`Step ${analysisStepIndex + 1} of ${analysisTotalSteps}`}>
        <span style={`width:${analysisProgress}%`}></span>
      </div>

      {#key currentAnalysisStep.id}
        <div class="analysis-content" class:mystery-report={Boolean(currentAnalysisStep.mysteryPlayer)}>
          <div class="analysis-copy">
            <p class="analysis-kicker">{draftMode === "et" ? (currentAnalysisStep.tone === "grade" ? "Signal Verdict" : "Transmission Analysis") : currentAnalysisStep.kicker} <span>{analysisStepIndex + 1} / {analysisTotalSteps}</span></p>
            <h1 class:et-phoebe-completion-message={draftMode === "et" && currentAnalysisStep.id === "complete"}>{currentAnalysisStep.title}</h1>

            {#if currentAnalysisStep.mysteryPlayer && currentAnalysisStep.mysteryImpact}
              <p class="analysis-body">One selection remained hidden throughout the draft. Phoebe has completed the final identity check.</p>

              <div class="analysis-mystery-reveal" aria-live="polite">
                <div class="mystery-reveal-player">
                  <span>Identity Revealed</span>
                  <strong>{currentAnalysisStep.mysteryPlayer.name}</strong>
                  <div>
                    <b><small>Position</small>{getPositions(currentAnalysisStep.mysteryPlayer).join(", ")}</b>
                    <b><small>Nation</small>{currentAnalysisStep.mysteryPlayer.nation ?? currentAnalysisStep.mysteryPlayer.club}</b>
                    <b><small>IoG</small>{formatIoG(currentAnalysisStep.mysteryPlayer.adjustedIog)}</b>
                  </div>
                </div>
              </div>

              <div class="mystery-impact-summary">
                <span>Impact</span>
                <div>
                  <strong>{signedImpact(currentAnalysisStep.mysteryImpact.chemistry)} <small>Chemistry</small></strong>
                  <strong>{signedImpact(currentAnalysisStep.mysteryImpact.lineRating)} <small>{titleCase(currentAnalysisStep.mysteryImpact.line)} Rating</small></strong>
                  {#if currentAnalysisStep.mysteryImpact.projectedPoints !== undefined}
                    <strong>{signedImpact(currentAnalysisStep.mysteryImpact.projectedPoints)} <small>Projected Points</small></strong>
                  {/if}
                </div>
              </div>
            {:else}
              <p class="analysis-body">{currentAnalysisStep.body}</p>

              <div class="analysis-metric">
                <span>{currentAnalysisStep.metricLabel}</span>
                <strong>{currentAnalysisStep.metricValue}</strong>
              </div>
            {/if}
          </div>

          <aside class="analysis-phoebe" aria-label="Phoebe, post-draft analyst">
            <img src="/phoebe.png" alt="Phoebe" />
            <div>
              <strong>Phoebe</strong>
              <span>Draft Analyst</span>
            </div>
            {#if currentAnalysisStep.mysteryImpact}
              <blockquote>“{currentAnalysisStep.mysteryImpact.quote}”</blockquote>
            {/if}
          </aside>
        </div>
      {/key}

      <footer class="analysis-footer">
        <span>Click anywhere to continue</span>
        <button class="analysis-continue" on:click={advancePostDraftAnalysis}>
          {analysisStepIndex === postDraftAnalysis.length - 1 ? (draftMode === "et" ? "Run Final Match" : draftMode === "invinciblesClub" ? "Run League Simulation" : "Reveal Final XI") : "Continue"}
        </button>
      </footer>
    </section>
  {/if}

  {#if screen === "playLevel"}
    <section class="play-level-stage" aria-label="Play Level simulation">
      <header class="play-level-header">
        <div>
          <p class="kicker">Play Level</p>
          <h1>{draftMode === "worldcup" ? "Tournament Simulation" : draftMode === "et" ? "Final Alien Match" : "Season Simulation"}</h1>
          <p class="muted">
            {draftMode === "worldcup"
              ? "Reveal your World Cup path one stage at a time."
              : draftMode === "et"
                ? "Signal confirmed. One match remains. Build Galactico11 and defend Earth."
                : `Reveal your ${invinciblesSeasonMatches}-match Invincibles campaign through live checkpoints.`}
          </p>
        </div>
        <button class="secondary" on:click={skipPlayLevel}>Skip Simulation</button>
      </header>

      <div class="play-level-progress" aria-label={`Simulation step ${playLevelStarted ? playLevelStepIndex + 1 : 0} of ${playLevelMaxSteps}`}>
        <span style={`width:${playLevelStarted ? ((playLevelStepIndex + 1) / Math.max(playLevelMaxSteps, 1)) * 100 : 0}%`}></span>
      </div>

      {#if !playLevelStarted}
        <div class="play-level-intro">
          <span>{draftMode === "worldcup" ? "Knockout path loaded" : draftMode === "et" ? "Alien signal locked" : "League engine ready"}</span>
          <strong>{draftMode === "worldcup" ? "Tournament Path" : draftMode === "et" ? "Earth Survival Match" : `${invinciblesSeasonMatches}-Match Season`}</strong>
          <p>
            {draftMode === "worldcup"
              ? "Phoebe has generated the tournament bracket from your final XI strength, chemistry and tactical balance."
              : draftMode === "et"
                ? "Opponent detected. Phoebe has converted your average IoG, chemistry, Libra Score and tactical balance into one final survival model."
                : "Phoebe has prepared progressive season checkpoints from your IoG, chemistry, Libra Score and formation fit. The final record stays sealed until the campaign is complete."}
          </p>
          <button class="primary" on:click={beginPlayLevel}>{draftMode === "et" ? "Start Final Match" : "Start Simulation"}</button>
        </div>
      {:else if playLevelCurrentStep}
        <article class="play-level-card" class:completed={playLevelCompleted}>
          <div class="play-level-card-head">
            <span>{playLevelCurrentStep.kicker}</span>
            <strong>{playLevelCurrentStep.stage}</strong>
          </div>

          <div class="play-level-main">
            <div>
              <h2>{playLevelCurrentStep.title}</h2>
              {#if playLevelCurrentStep.opponent}
                <p class="play-opponent">Opponent: <strong>{playLevelCurrentStep.opponent}</strong></p>
              {/if}
              {#if playLevelCurrentStep.scoreline}
                <div
                  class="play-scoreline"
                  class:record-low={draftMode === "et" && predictedEtAlienMatch.resultTone === "low"}
                  class:record-medium={draftMode === "et" && predictedEtAlienMatch.resultTone === "medium"}
                  class:record-high={draftMode === "et" && predictedEtAlienMatch.resultTone === "high"}
                >{playLevelCurrentStep.scoreline}</div>
              {/if}
              <p>{playLevelCurrentStep.tacticalAnalysis}</p>
            </div>

            <aside class="play-match-details">
              <div><span>Key Player</span><strong>{playLevelCurrentStep.manOfTheMatch}</strong></div>
              {#if draftMode === "et"}
                <div><span>Opponent IoG</span><strong>{formatIoG(predictedEtAlienMatch.opponent.averageIog)}</strong></div>
                <div><span>Threat Level</span><strong>{predictedEtAlienMatch.opponent.threatLevel}</strong></div>
                <div><span>Survival Chance</span><strong
                  class:record-low={predictedEtAlienMatch.resultTone === "low"}
                  class:record-medium={predictedEtAlienMatch.resultTone === "medium"}
                  class:record-high={predictedEtAlienMatch.resultTone === "high"}
                >{predictedEtAlienMatch.survivalChance}%</strong></div>
              {:else if draftMode === "worldcup"}
                <div><span>Status</span><strong>{playLevelCurrentStep.advanced ? "Advanced" : "Eliminated"}</strong></div>
              {:else if playLevelCurrentStep.checkpointSummary}
                <div><span>Position</span><strong
                  class:record-low={positionTone(playLevelCurrentStep.checkpointSummary.position) === "low"}
                  class:record-medium={positionTone(playLevelCurrentStep.checkpointSummary.position) === "medium"}
                  class:record-high={positionTone(playLevelCurrentStep.checkpointSummary.position) === "high"}
                >{playLevelCurrentStep.checkpointSummary.position}</strong></div>
                <div><span>Points</span><strong>{playLevelCurrentStep.checkpointSummary.points} / {etMaxPoints}</strong></div>
                <div><span>GF / GA</span><strong>{playLevelCurrentStep.checkpointSummary.goalsFor} / {playLevelCurrentStep.checkpointSummary.goalsAgainst}</strong></div>
                <div><span>Invincible</span><strong
                  class:record-low={!playLevelCurrentStep.checkpointSummary.invincible}
                  class:record-high={playLevelCurrentStep.checkpointSummary.invincible}
                >{playLevelCurrentStep.checkpointSummary.invincible ? "Alive" : "Broken"}</strong></div>
              {/if}
            </aside>
          </div>

          {#if playLevelSeasonSummary && playLevelCompleted}
            <div class="play-season-summary">
              <div><span>Best Player</span><strong>{playLevelSeasonSummary.bestPlayerName}</strong></div>
              <div><span>Biggest Surprise</span><strong>{playLevelSeasonSummary.biggestSurprise}</strong></div>
              <div><span>Identity</span><strong>{playLevelSeasonSummary.teamIdentityName}</strong></div>
              <div><span>Historical Pace</span><strong>{playLevelSeasonSummary.historicalComparison}</strong></div>
            </div>
          {/if}
        </article>

        <footer class="play-level-actions">
          <button class="secondary" on:click={skipPlayLevel}>Skip Simulation</button>
          {#if playLevelCompleted}
            <button class="primary" on:click={enterFinalReveal}>View Final Report</button>
          {:else}
            <button class="primary" on:click={continuePlayLevel}>Continue</button>
          {/if}
        </footer>
      {/if}
    </section>
  {/if}

  {#if screen === "simulation"}
    <section class="simulation-stage" aria-label="Invincibles league simulation">
      <header class="simulation-header">
        <img src="/logo-white.png" alt="Galactico11" />
        <span>League Simulation • {invinciblesSeasonMatches} Matches</span>
      </header>

      <div class="simulation-content">
        <div class="simulation-copy">
          <p class="kicker">Draft Complete</p>
          <h1>Your record is</h1>
          <strong
            class="simulation-record"
            class:record-low={valueTone(simulatedWins, Math.round(invinciblesSeasonMatches * 0.4), Math.round(invinciblesSeasonMatches * 0.64)) === "low"}
            class:record-medium={valueTone(simulatedWins, Math.round(invinciblesSeasonMatches * 0.4), Math.round(invinciblesSeasonMatches * 0.64)) === "medium"}
            class:record-high={valueTone(simulatedWins, Math.round(invinciblesSeasonMatches * 0.4), Math.round(invinciblesSeasonMatches * 0.64)) === "high"}
            aria-live="polite"
          >{simulatedWins}-{simulatedDraws}-{simulatedLosses}</strong>
          <div class="simulation-progress">
            <span style={`width:${((simulatedWins + simulatedDraws + simulatedLosses) / invinciblesSeasonMatches) * 100}%`}></span>
          </div>
          <small>{simulatedWins + simulatedDraws + simulatedLosses} / {invinciblesSeasonMatches} matches</small>
        </div>

        <aside class="simulation-phoebe">
          <img src="/phoebe.png" alt="Phoebe, Draft Analyst" />
          <div>
            <span>Draft Analyst</span>
            {#if simulationComplete}
              <strong>{etSeasonComment(predictedEtRecord.wins)}</strong>
            {:else}
              <strong>We've built the squad. Now let's see how they perform across a {invinciblesSeasonMatches}-match Invincibles season.</strong>
            {/if}
          </div>
        </aside>
      </div>

      {#if simulationComplete}
        <footer class="simulation-footer">
          <div>
            <span>Simulation Complete</span>
            <strong>All {invinciblesSeasonMatches} matches have been processed</strong>
          </div>
          <button class="primary" on:click={showRecordReveal}>View Season Record</button>
        </footer>
      {/if}
    </section>
  {/if}

  {#if screen === "record"}
    <section class="simulation-stage reveal-stage" aria-label="Invincibles record reveal">
      <header class="simulation-header">
        <img src="/logo-white.png" alt="Galactico11" />
        <span>Season Complete • Record Reveal</span>
      </header>

      <div class="record-reveal-content">
        <p class="kicker">Your record is</p>
        <strong
          class="record-reveal-value"
          class:record-low={seasonTone(predictedEtRecord) === "low"}
          class:record-medium={seasonTone(predictedEtRecord) === "medium"}
          class:record-high={seasonTone(predictedEtRecord) === "high"}
        >{predictedEtRecord.record}</strong>
        <span>{predictedEtRecord.points} / {etMaxPoints} pts</span>

        <aside class="record-phoebe">
          <img src="/phoebe.png" alt="Phoebe, Draft Analyst" />
          <div>
            <small>Season Verdict</small>
            <strong>{etSeasonComment(predictedEtRecord.wins)}</strong>
          </div>
        </aside>
      </div>

      <footer class="simulation-footer">
        <span>Next: Squad harmony analysis</span>
        <button class="primary" on:click={showLibraReveal}>Reveal Libra Score</button>
      </footer>
    </section>
  {/if}

  {#if screen === "libra"}
    <section class="simulation-stage reveal-stage" aria-label="Libra Score reveal">
      <header class="simulation-header">
        <img src="/logo-white.png" alt="Galactico11" />
        <span>Squad Harmony • Libra Reveal</span>
      </header>

      <div class="libra-reveal-content">
        <div>
          <p class="kicker">Libra Score</p>
          <strong class="libra-reveal-value">{libraScore ?? 0}</strong>
          <h1>{libraLabel(libraScore)}</h1>
          <p>{finalBalanceProfile.insight}</p>
        </div>

        <dl class="libra-breakdown">
          <div><dt>IoG Consistency</dt><dd>{displayAvgIog}</dd></div>
          <div><dt>Chemistry</dt><dd>{chemistry}%</dd></div>
          <div><dt>Position Fit</dt><dd>{finalBalanceProfile.positionFit}%</dd></div>
          <div><dt>Tactical Distribution</dt><dd>{finalBalanceProfile.tacticalDistribution}%</dd></div>
        </dl>
      </div>

      <footer class="simulation-footer">
        <span>Analysis complete</span>
        <button class="primary" on:click={enterFinalReveal}>Reveal Final XI</button>
      </footer>
    </section>
  {/if}

  {#if screen === "verdict"}
    <section
      class="final-verdict-stage"
      class:verdict-et={draftMode === "et"}
      class:verdict-invincibles={draftMode === "invinciblesClub" || draftMode === "club"}
      class:verdict-worldcup={draftMode === "worldcup"}
      aria-label="Final verdict sequence"
    >
      <header class="final-verdict-header">
        <img src="/logo-white.png" alt="Galactico11" />
        <button class="analysis-skip" on:click={skipFinalVerdict}>Skip</button>
      </header>

      <div class="final-verdict-content" aria-live="polite">
        <p class="kicker">{finalVerdictSteps[finalVerdictStepIndex]}</p>
        <h1>{finalVerdictTitle()}</h1>
        <strong>{finalVerdictDetail()}</strong>
        <div class="final-verdict-progress" aria-label={`Verdict step ${finalVerdictStepIndex + 1} of ${finalVerdictSteps.length}`}>
          {#each finalVerdictSteps as _, index}
            <span class:active={index <= finalVerdictStepIndex}></span>
          {/each}
        </div>
      </div>
    </section>
  {/if}

  {#if screen === "result"}
    <section class="panel result">
      <div class="result-head">
        <div>
          <img class="result-logo" src="/logo-white.png" alt="Galactico11" />
          <p class="kicker">Final XI Reveal • {analysisTotalSteps} / {analysisTotalSteps}</p>
          <h1>Final team reveal</h1>
          <p class="muted">Your XI is complete.</p>
        </div>

        <div class="result-actions">
          <button class="secondary" on:click={shareFinalResult}>Share</button>
          <button class="secondary" on:click={restart}>Play Again</button>
        </div>
      </div>

      {#if bench.length > 0}
        <section class="result-section bench-result-summary">
          <h2>Bench Impact</h2>
          <div class="bench-impact-grid">
            <article><span>Bench Strength</span><strong>{benchImpact.strength}%</strong></article>
            <article><span>Tactical Flexibility</span><strong>{benchImpact.flexibility}</strong></article>
            <article><span>Late Threat</span><strong>+{benchImpact.lateThreat}%</strong></article>
            <article><span>Fatigue Resistance</span><strong>+{benchImpact.fatigue}%</strong></article>
          </div>
          <p class="bench-result-note">{benchImpact.note}</p>
        </section>
      {/if}

      {#if draftMode === "et"}
        <div class="et-match-result">
          <div
            class="et-result-summary"
            class:result-loss={predictedEtAlienMatch.resultTone === "low"}
            class:result-narrow={predictedEtAlienMatch.resultTone === "medium"}
            class:result-win={predictedEtAlienMatch.resultTone === "high"}
          >
            <div class="et-result-banner">
              <span>Final Signal</span>
              <strong>{predictedEtAlienMatch.resultText}</strong>
              <p>{predictedEtAlienMatch.resultTone === "low"
                ? "Draft quality was elite. Match survival was not."
                : predictedEtAlienMatch.resultTone === "medium"
                  ? "The signal faded before the inversion could finish."
                  : "The final signal breaks. Galactico11 holds."}</p>
            </div>

            <div class="et-result-stats">
              <div><span>Opponent</span><strong>{predictedEtAlienMatch.opponent.name}</strong></div>
              <div><span>Scoreline</span><strong>{predictedEtAlienMatch.scoreline}</strong></div>
              <div
                class:et-stat-low={predictedEtAlienMatch.resultTone === "low"}
                class:et-stat-medium={predictedEtAlienMatch.resultTone === "medium"}
                class:et-stat-high={predictedEtAlienMatch.resultTone === "high"}
              ><span>Survival Chance</span><strong>{predictedEtAlienMatch.survivalChance}%</strong></div>
              <div><span>Opponent IoG</span><strong>{formatIoG(predictedEtAlienMatch.opponent.averageIog)}</strong></div>
              <div
                class:et-stat-low={predictedEtAlienMatch.resultTone === "low"}
                class:et-stat-medium={predictedEtAlienMatch.resultTone === "medium"}
                class:et-stat-high={predictedEtAlienMatch.resultTone === "high"}
              ><span>Match Outcome</span><strong>{predictedEtAlienMatch.outcome === "loss" ? "Loss" : predictedEtAlienMatch.outcome === "barely" ? "Narrow Escape" : "Win"}</strong></div>
              <div><span>Draft Grade</span><strong>{grade}</strong></div>
            </div>
          </div>

          <div class="result-section result-pitch-section">
            <h2>Earth XI</h2>
            <div class="final-pitch">
              {#each pitchSlots as slot}
                <div style={`left:${slot.x}%; top:${slot.y}%`}>
                  {#if slot.player}
                    <span>{initials(slot.player.name)}</span>
                    <small>IoG {formatIoG(slot.player.adjustedIog)}</small>
                  {:else}
                    <strong>{slot.label}</strong>
                  {/if}
                </div>
              {/each}
            </div>
          </div>

          <div class="result-section">
            <h2>Alien Threat Analysis</h2>
            <div class="stat-cards-grid">
              <div class="stat-card"><span>Threat Level</span><strong>{predictedEtAlienMatch.opponent.threatLevel}</strong></div>
              <div class="stat-card"><span>Key Player</span><strong>{predictedEtAlienMatch.keyPlayer}</strong></div>
              <div class="stat-card"><span>Team Balance</span><strong>{finalBalanceProfile.status}</strong></div>
            </div>
          </div>

          {#if predictedEtAlienMatch.mirrorThreats.length > 0}
            <div class="result-section">
              <h2>Paradox Mirror Threats</h2>
              <div class="paradox-threats">
                {#each predictedEtAlienMatch.mirrorThreats as threat}
                  <article>
                    <span>{formatIoG(threat.originalIog)} realistic IoG</span>
                    <strong>{threat.name}</strong>
                    <small>Paradox form: {formatIoG(threat.paradoxIog)}</small>
                  </article>
                {/each}
              </div>
            </div>
          {/if}

          <div class="result-section">
            <h2>Signal Notes</h2>
            <div class="analysis-cards-grid">
              <div class="analysis-card">
                <h3>Match Verdict</h3>
                <p><strong>{predictedEtAlienMatch.resultText}</strong> {predictedEtAlienMatch.route}</p>
                <p>{predictedEtAlienMatch.tacticalNote}</p>
              </div>
              <div class="analysis-card">
                <h3>Tactical Profile</h3>
                <p><strong>Strengths —</strong> {finalBalanceProfile.insight}</p>
                <p><strong>Weaknesses —</strong> {weakestPlayer ? `${weakestPosition} was the clearest pressure channel.` : "No obvious weak point."}</p>
                <div class="tactical-hexagon">
                  <TeamBalanceHexagon players={picked} {formation} {chemistry} {positionFit} context="final" />
                </div>
              </div>
            </div>
          </div>
        </div>
      {/if}

      {#if draftMode === "invinciblesClub"}
        <div class="invincibles-result">
          <div class="result-hero">
            <div class="result-hero-item hero-grade">
              <span>Final Grade</span>
              <strong
                class="grade-score"
                class:record-low={gradeTone(grade) === "low"}
                class:record-medium={gradeTone(grade) === "medium"}
                class:record-high={gradeTone(grade) === "high"}
              >{grade}</strong>
            </div>
            <div class="result-hero-item">
              <span>Record</span>
              <strong
                class:record-low={seasonTone(predictedEtRecord) === "low"}
                class:record-medium={seasonTone(predictedEtRecord) === "medium"}
                class:record-high={seasonTone(predictedEtRecord) === "high"}
              >{predictedEtRecord.record}</strong>
            </div>
            <div class="result-hero-item">
              <span>Points</span>
              <strong
                class:record-low={valueTone(predictedEtRecord.points, etMaxPoints * 0.48, etMaxPoints * 0.72) === "low"}
                class:record-medium={valueTone(predictedEtRecord.points, etMaxPoints * 0.48, etMaxPoints * 0.72) === "medium"}
                class:record-high={valueTone(predictedEtRecord.points, etMaxPoints * 0.48, etMaxPoints * 0.72) === "high"}
              >{predictedEtRecord.points}<small> / {etMaxPoints}</small></strong>
            </div>
            <div class="result-hero-item">
              <span>Final League Position</span>
              <strong
                class:record-low={positionTone(predictedEtRecord.position) === "low"}
                class:record-medium={positionTone(predictedEtRecord.position) === "medium"}
                class:record-high={positionTone(predictedEtRecord.position) === "high"}
              >{predictedEtRecord.position}</strong>
            </div>
            <div class="result-hero-item">
              <span>Invincible Status</span>
              <strong
                class:record-low={invincibleTone(predictedEtRecord) === "low"}
                class:record-medium={invincibleTone(predictedEtRecord) === "medium"}
                class:record-high={invincibleTone(predictedEtRecord) === "high"}
              >
                {predictedEtRecord.losses === 0 ? "Invincible" : `${predictedEtRecord.losses} Losses`}
              </strong>
            </div>
            <div class="result-hero-item">
              <span>Overall IoG</span>
              <strong>{displayAvgIog}</strong>
            </div>
          </div>

          <div class="result-section result-pitch-section">
            <h2>Final XI</h2>
            <div class="final-pitch">
              {#each pitchSlots as slot}
                <div style={`left:${slot.x}%; top:${slot.y}%`}>
                  {#if slot.player}
                    <span>{initials(slot.player.name)}</span>
                    <small>IoG {formatIoG(slot.player.adjustedIog)}</small>
                  {:else}
                    <strong>{slot.label}</strong>
                  {/if}
                </div>
              {/each}
            </div>
          </div>

          <div class="result-section">
            <h2>Season Statistics</h2>
            <div class="stat-cards-grid">
              <div class="stat-card"><span>Goals Scored</span><strong>{predictedEtRecord.goalsFor}</strong></div>
              <div class="stat-card"><span>Goals Conceded</span><strong>{predictedEtRecord.goalsAgainst}</strong></div>
              <div class="stat-card"><span>Goal Difference</span><strong>{predictedEtRecord.goalDifference > 0 ? "+" : ""}{predictedEtRecord.goalDifference}</strong></div>
              <div class="stat-card"><span>Clean Sheets</span><strong>{predictedEtRecord.cleanSheets}</strong></div>
              <div class="stat-card"><span>Chance of Winning League</span><strong
                class:record-low={valueTone(predictedEtRecord.titleChance, 25, 60) === "low"}
                class:record-medium={valueTone(predictedEtRecord.titleChance, 25, 60) === "medium"}
                class:record-high={valueTone(predictedEtRecord.titleChance, 25, 60) === "high"}
              >{predictedEtRecord.titleChance}%</strong></div>
              <div class="stat-card"><span>Chance of Going Invincible</span><strong
                class:record-low={valueTone(predictedEtRecord.invincibleChance, 5, 25) === "low"}
                class:record-medium={valueTone(predictedEtRecord.invincibleChance, 5, 25) === "medium"}
                class:record-high={valueTone(predictedEtRecord.invincibleChance, 5, 25) === "high"}
              >{predictedEtRecord.invincibleChance}%</strong></div>
            </div>
          </div>

          <div class="result-section">
            <h2>Football Analysis</h2>
            <div class="analysis-cards-grid">
              <div class="analysis-card">
                <h3>Squad Report</h3>
                <dl>
                  {#if bestPlayer}
                    <div><dt>Best Player</dt><dd>{bestPlayer.name}</dd></div>
                  {/if}
                  {#if hiddenGem}
                    <div><dt>Hidden Gem</dt><dd>{hiddenGem.name}</dd></div>
                  {/if}
                  <div><dt>Weakest Position</dt><dd>{weakestPosition}</dd></div>
                  <div><dt>Team Balance</dt><dd>{finalBalanceProfile.status}</dd></div>
                </dl>
                <div class="squad-diagnosis">
                  <span>Squad Diagnosis</span>
                  <ul>
                    {#each squadDiagnosis as insight}
                      <li>{insight}</li>
                    {/each}
                  </ul>
                </div>
              </div>

              <div class="analysis-card">
                <h3>Tactical Notes</h3>
                <p><strong>Strengths —</strong> {finalBalanceProfile.insight}</p>
                <p><strong>Weaknesses —</strong> {weakestPlayer ? `${weakestPosition} is the clearest pressure point.` : "No obvious weak point."}</p>
                <div class="tactical-hexagon">
                  <TeamBalanceHexagon players={picked} {formation} {chemistry} {positionFit} context="final" />
                </div>
              </div>
            </div>
          </div>

          <div class="result-section result-deepdive">
            <div class="deepdive-buttons">
              <button class="secondary" on:click={() => (showDraftTimeline = !showDraftTimeline)}>{showDraftTimeline ? "Hide" : "View"} Draft Timeline</button>
              <button class="secondary" on:click={shareFinalResult}>Export Share Card</button>
            </div>

            {#if showDraftTimeline}
              <div class="deepdive-panel">
                <h3>Draft Timeline</h3>
                <ol class="draft-timeline-list">
                  {#each picked as player, index}
                    <li>
                      <span>Pick {index + 1}</span>
                      <strong>{isMysteryIdentityHidden(player) ? "Mystery Pick" : player.name}</strong>
                      <small>{displayTeamContext(player)} · {player.nation ?? "-"} · {player.assignedPosition} · IoG {formatIoG(player.adjustedIog)}</small>
                      <em>Chosen over: {player.alternatives?.join(", ") || "No clear alternatives"}</em>
                      <p>Phoebe: {player.adjustedIog >= Number(avgIog) ? "This pick raised the squad ceiling, but the structure still had to hold." : "This was a compromise pick. The next decision needed to protect the balance."}</p>
                    </li>
                  {/each}
                </ol>
              </div>
            {/if}

          </div>
        </div>
      {:else if draftMode !== "et"}
        <div class="result-grid">
          <aside class="summary">
            <div><span>Formation</span><strong>{formation}</strong></div>
            <div><span>Overall Team IoG</span><strong>{displayAvgIog}</strong></div>
            <div><span>Grade</span><strong class="grade-score">{grade}</strong></div>
            <div><span>Captain</span><strong>{captain?.name}</strong></div>
            <div><span>Chemistry</span><strong>{chemistry}%</strong></div>
            {#if draftMode === "worldcup"}
              <div class="outcome-card"><span>World Cup Projection</span><strong>{predictedWorldCupOutcome}</strong></div>
            {:else if clubFormat === "champions"}
              <div class="outcome-card"><span>Predicted Champions League Result</span><strong>{predictedChampionsLeagueOutcome}</strong></div>
            {:else}
              <div><span>League</span><strong>{selectedClubLeague}</strong></div>
              <div class="outcome-card"><span>Predicted League Record</span><strong>{predictedClubRecord.record}</strong></div>
              <div class="outcome-card"><span>Points</span><strong>{predictedClubRecord.points} pts</strong></div>
            {/if}
            {#if bestPlayer}
              <div><span>Best Player</span><strong>{bestPlayer.name}</strong></div>
            {/if}
            {#if weakestPlayer}
              <div><span>Weakest Player</span><strong>{weakestPlayer.name}</strong></div>
            {/if}
          </aside>

          <div class="final-pitch">
            {#each pitchSlots as slot}
              <div style={`left:${slot.x}%; top:${slot.y}%`}>
                {#if slot.player}
                  <span>{initials(slot.player.name)}</span>
                  <small>IoG {formatIoG(slot.player.adjustedIog)}</small>
                {:else}
                  <strong>{slot.label}</strong>
                {/if}
              </div>
            {/each}
          </div>
        </div>

        <div class="final-live-analysis">
          <TeamBalanceHexagon players={picked} {formation} {chemistry} {positionFit} context="final" />
        </div>

        {#if draftMode === "worldcup"}
          <section class="worldcup-projection-note" aria-label="World Cup projection explanation">
            <span>Projection Logic</span>
            <p>{worldCupSimulation.explanation}</p>
          </section>
        {/if}

        <section class="mobile-scouting-report" aria-label="Final scouting report">
          <div><span>Overall IoG</span><strong>{displayAvgIog}</strong></div>
          <div><span>Libra Score</span><strong>{libraScore ?? "-"}</strong></div>
          <div><span>Balance</span><strong>{finalBalanceProfile.status}</strong></div>
          <div><span>Chemistry</span><strong>{chemistry}%</strong></div>
          <div><span>Grade</span><strong>{grade}</strong></div>
          <div><span>Formation</span><strong>{formation}</strong></div>
          <article>
            <span>Strengths</span>
            <p>{finalBalanceProfile.insight}</p>
          </article>
          <article>
            <span>Weaknesses</span>
            <p>{weakestPlayer ? `${weakestPosition} is the clearest pressure point through ${weakestPlayer.name}.` : "No obvious weak point."}</p>
          </article>
          {#if bestPlayer}
            <div><span>Best Player</span><strong>{bestPlayer.name}</strong></div>
          {/if}
          {#if hiddenGem}
            <div><span>Hidden Gem</span><strong>{hiddenGem.name}</strong></div>
          {/if}
          {#if mostUnderratedPick}
            <div><span>Most Underrated Pick</span><strong>{mostUnderratedPick.name}</strong></div>
          {/if}
          <div><span>Weakest Position</span><strong>{weakestPosition}</strong></div>
          <article>
            <span>Top Three Connections</span>
            <p>{topThreeConnections || "Still forming."}</p>
          </article>
        </section>
      {/if}

      {#if libraBonusActive}
        <section class="libra-bonus" aria-label="Libra tournament advancement bonus">
          <div>
            <span>LIBRA BONUS ACTIVATED</span>
            <strong>Libra Score over 85 pushed the squad further.</strong>
          </div>
          <div>
            <span>Base Projection</span>
            <strong>{baseWorldCupOutcome}</strong>
          </div>
          <div>
            <span>Libra Boost</span>
            <strong>{formatWorldCupBoost(worldCupSimulation.libraBoostStages)}</strong>
          </div>
          <div>
            <span>Final Outcome</span>
            <strong>{predictedWorldCupOutcome}</strong>
          </div>
          <p>Phoebe: Your squad's balance elevated its tournament performance beyond the expected result.</p>
        </section>
      {/if}

      <p class="footer-note">Note: The statistics shown are limited to 2 seasons before and after 2026.</p>
    </section>
  {/if}

  {#if showShareModal}
    <section class="share-overlay" aria-label="Share your team modal">
      <div class="share-modal" role="dialog" aria-modal="true" aria-labelledby="share-title">
        <header class="share-modal-head">
          <div>
            <span>Galactico11</span>
            <h2 id="share-title">Share your team</h2>
          </div>
          <button type="button" aria-label="Close share modal" on:click={() => (showShareModal = false)}>×</button>
        </header>

        <article class="share-card-preview" aria-label="Share card preview">
          <div class="share-card-orbit" aria-hidden="true"></div>
          <section class="share-card-top">
            <div>
              <span>{draftMode === "worldcup" ? "Tournament Result" : "Projected Record"}</span>
              <strong>{shareOutcome()}</strong>
            </div>
            <div>
              <span>Grade</span>
              <strong>{grade}</strong>
            </div>
            <div>
              <span>Team IoG</span>
              <strong>{displayAvgIog}</strong>
            </div>
          </section>

          <p class="share-mode-badge">Mode: {shareModeLabel()}</p>

          <div class="share-xi-list">
            {#each sharePlayerRows() as player}
              <div>
                <b>{player.position}</b>
                <span>
                  <strong>{player.name}</strong>
                  <small>{player.context} · {player.era} · IoG {player.iog}</small>
                </span>
              </div>
            {/each}
          </div>

          <div class="share-card-brand">
            <strong>Galactico11</strong>
            <span>Created by Zain Ahmed</span>
          </div>
        </article>

        <div class="share-actions" aria-label="Share actions">
          <button type="button" on:click={() => openShareTarget("twitter")}>𝕏 / Twitter</button>
          <button type="button" on:click={() => openShareTarget("facebook")}>Facebook</button>
          <button type="button" on:click={() => openShareTarget("whatsapp")}>WhatsApp</button>
          <button type="button" on:click={() => openShareTarget("telegram")}>Telegram</button>
          <button type="button" on:click={() => openShareTarget("reddit")}>Reddit</button>
          <button type="button" on:click={copyShareLink}>Copy Link</button>
          <button type="button" class="share-download" on:click={downloadShareImage}>Download Image</button>
        </div>

        {#if shareStatus}
          <p class="share-status">{shareStatus}</p>
        {/if}
      </div>
    </section>
  {/if}

  {#if showPhoebeTutorial}
    <section class="phoebe-overlay" aria-label="Phoebe onboarding">
      <div class="phoebe-companion">
        <div class="phoebe-bubble">
          <p>{tutorialMessages[tutorialStep]}</p>

          <div class="phoebe-actions">
            {#if tutorialStep === 0}
              <button class="primary" on:click={nextPhoebeScene}>Next</button>
              <button class="secondary" on:click={skipPhoebeTutorial}>Skip Tutorial</button>
            {:else if tutorialStep === 1}
              <button class="primary" on:click={nextPhoebeScene}>Next</button>
            {:else if tutorialStep === 2}
              <button class="primary" on:click={nextPhoebeScene}>Next</button>
            {:else if tutorialStep === 3}
              <button class="primary" on:click={nextPhoebeScene}>Next</button>
            {/if}
          </div>
        </div>

        <div class="phoebe-mascot" aria-hidden="true">
          <img src="/phoebe.png" alt="" />
        </div>
      </div>
    </section>
  {/if}

  <footer class="site-footer">© 2026 Galactico11 — Created by Zain Ahmed</footer>
</main>

<style>
  :global(*) {
    box-sizing: border-box;
  }

  :global(html) {
    scroll-behavior: smooth;
  }

  :global(body) {
    margin: 0;
    background: #090a0f;
  }

  /* ── TeamBalanceHexagon global styles (CSS extraction fix for Svelte 5 + Astro) ── */
  :global(.balance-panel) {
    margin-top: 24px;
    border-top: 1px solid #262a38;
    padding-top: 22px;
    color: #f5f5f6;
  }

  :global(.balance-header) {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 18px;
  }

  :global(.balance-header span),
  :global(.formation-badge small),
  :global(.balance-factors span),
  :global(.balance-insight span) {
    display: block;
    color: #8c92a2;
    font-size: 10px;
    font-weight: 850;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  :global(.balance-header h3) {
    margin: 5px 0 0;
    font-size: 20px;
  }

  :global(.formation-badge) {
    border: 1px solid rgba(201, 166, 70, 0.32);
    border-radius: 10px;
    background: rgba(201, 166, 70, 0.07);
    padding: 9px 12px;
    text-align: right;
  }

  :global(.formation-badge strong) {
    display: block;
    margin-top: 3px;
    color: #d6b956;
  }

  :global(.profile-grid) {
    margin-top: 16px;
    display: grid;
    grid-template-columns: minmax(0, 1fr) 130px;
    align-items: center;
    gap: 14px;
  }

  :global(.chart-shell) {
    position: relative;
    isolation: isolate;
    display: grid;
    place-items: center;
  }

  :global(.balance-radar) {
    width: min(320px, 100%);
    height: 256px;
    max-height: 256px;
    display: block;
    overflow: visible;
  }

  :global(.team-shadow) {
    transform: translateY(4px);
  }

  :global(.team-shape) {
    transition: points 0.6s ease;
    filter: drop-shadow(0 0 7px rgba(34, 240, 230, 0.72)) drop-shadow(0 0 18px rgba(34, 240, 230, 0.22));
  }

  :global(.point) {
    filter: drop-shadow(0 0 7px rgba(34, 240, 230, 0.52));
  }

  :global(.hud-label) {
    fill: rgba(226, 232, 240, 0.8);
    font: 800 10px Inter, system-ui, sans-serif;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  :global(.forming-label) {
    fill: rgba(239, 213, 116, 0.9);
    font: 850 9px Inter, system-ui, sans-serif;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  :global(.line-scores) {
    display: grid;
    gap: 15px;
  }

  :global(.line-scores article) {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: baseline;
    gap: 8px;
  }

  :global(.line-scores span) {
    color: #9298a8;
    font-size: 11px;
  }

  :global(.line-scores strong) {
    font-size: 16px;
    font-variant-numeric: tabular-nums;
  }

  :global(.line-scores article > div) {
    grid-column: 1 / -1;
    height: 4px;
    overflow: hidden;
    border-radius: 999px;
    background: #282c38;
  }

  :global(.line-scores i) {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, #806b2f, #c9a646, #efd574);
    transition: width 0.6s ease;
  }

  :global(.balance-factors) {
    margin-top: 18px;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  :global(.balance-factors article) {
    border: 1px solid #282c38;
    border-radius: 10px;
    background: #151823;
    padding: 11px;
  }

  :global(.balance-factors strong) {
    display: block;
    margin-top: 5px;
    font-size: 17px;
    font-variant-numeric: tabular-nums;
  }

  :global(.balance-insight) {
    margin-top: 10px;
    border-left: 2px solid #c9a646;
    background: rgba(201, 166, 70, 0.06);
    padding: 12px 14px;
  }

  :global(.libra-scale) {
    margin-top: 12px;
    display: grid;
    grid-template-columns: minmax(0, 150px) minmax(180px, 1fr);
    align-items: center;
    gap: 14px;
    border: 1px solid rgba(201, 166, 70, 0.24);
    border-radius: 12px;
    background:
      radial-gradient(circle at 86% 20%, rgba(57, 230, 201, 0.08), transparent 32%),
      linear-gradient(135deg, rgba(201, 166, 70, 0.08), rgba(13, 16, 24, 0.94));
    padding: 14px 16px;
  }

  :global(.libra-copy > span) {
    color: #8c92a2;
    font-size: 10px;
    font-weight: 850;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  :global(.libra-copy strong) {
    display: block;
    margin-top: 7px;
    color: #efd574;
    font-size: 34px;
    line-height: 1;
  }

  :global(.libra-copy p) {
    margin: 7px 0 0;
    color: #d0d4de;
    font-size: 13px;
    font-weight: 750;
  }

  :global(.libra-meter) {
    min-width: 0;
    display: grid;
    gap: 8px;
  }

  :global(.libra-scale-svg) {
    width: 100%;
    height: 120px;
    display: block;
    overflow: visible;
  }

  :global(.libra-scale-svg text) {
    fill: #8f95a5;
    font: 850 10px Inter, system-ui, sans-serif;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  :global(.scale-base) {
    fill: none;
    stroke: rgba(201, 166, 70, 0.58);
    stroke-width: 3;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  :global(.scale-pivot) {
    fill: #efd574;
    stroke: #11131b;
    stroke-width: 3;
    filter: drop-shadow(0 0 8px rgba(239, 213, 116, 0.24));
  }

  :global(.libra-meter p) {
    margin: 0;
    color: #cbd0dc;
    font-size: 12px;
    line-height: 1.45;
  }

  :global(.balance-insight p) {
    margin: 6px 0 0;
    color: #c9cdd7;
    font-size: 13px;
    line-height: 1.5;
  }

  :global(.final-analysis) {
    border: 1px solid #282c38;
    border-radius: 18px;
    background: #11141d;
    padding: 20px;
  }

  @media (max-width: 560px) {
    :global(.profile-grid) {
      grid-template-columns: 1fr;
    }

    :global(.line-scores) {
      grid-template-columns: repeat(3, 1fr);
    }

    :global(.libra-scale) {
      grid-template-columns: 104px minmax(0, 1fr);
      padding-inline: 12px;
    }

    :global(.libra-copy strong) {
      font-size: 28px;
    }
  }

  @media (max-width: 768px) {
    :global(.balance-panel) {
      margin-top: 16px;
      padding-top: 16px;
    }

    :global(.final-analysis) {
      border-radius: 14px;
      padding: 18px;
    }

    :global(.balance-header) {
      gap: 12px;
    }

    :global(.balance-header span),
    :global(.formation-badge small),
    :global(.balance-factors span),
    :global(.balance-insight span) {
      font-size: 8px;
      letter-spacing: 0.1em;
    }

    :global(.balance-header h3) {
      font-size: 18px;
    }

    :global(.formation-badge) {
      border-radius: 8px;
      padding: 7px 9px;
    }

    :global(.profile-grid) {
      margin-top: 12px;
      gap: 10px;
    }

    :global(.final-analysis .profile-grid) {
      grid-template-columns: 1fr;
      align-items: stretch;
    }

    :global(.balance-radar) {
      width: min(300px, 100%);
      height: 226px;
      max-height: 226px;
    }

    :global(.final-analysis .balance-radar) {
      height: clamp(188px, 50vw, 226px);
      max-height: 226px;
      margin-inline: auto;
    }

    :global(.line-scores) {
      gap: 10px;
    }

    :global(.line-scores span) {
      font-size: 10px;
    }

    :global(.line-scores strong) {
      font-size: 14px;
    }

    :global(.balance-factors) {
      margin-top: 12px;
      gap: 7px;
    }

    :global(.balance-factors article) {
      border-radius: 8px;
      padding: 9px;
    }

    :global(.balance-factors strong) {
      font-size: 15px;
    }

    :global(.libra-scale) {
      min-height: 0;
      display: grid;
      grid-template-columns: 104px minmax(0, 1fr);
      align-items: center;
      border-radius: 10px;
      padding: 12px;
      gap: 10px;
    }

    :global(.libra-copy strong) {
      font-size: 28px;
    }

    :global(.libra-copy p) {
      font-size: 12px;
    }

    :global(.balance-insight) {
      margin-top: 9px;
      padding: 10px 12px;
    }

    :global(.balance-insight p) {
      font-size: 12px;
      line-height: 1.42;
    }
  }

  @media (max-width: 430px) {
    :global(.balance-header) {
      display: grid;
      grid-template-columns: 1fr auto;
      align-items: start;
    }

    :global(.balance-radar) {
      width: min(280px, 100%);
      height: 202px;
      max-height: 202px;
    }

    :global(.final-analysis .balance-radar) {
      height: 196px;
      max-height: 202px;
    }

    :global(.hud-label) {
      font-size: 9px;
    }

    :global(.balance-factors) {
      grid-template-columns: 1fr;
    }

    :global(.libra-scale) {
      grid-template-columns: 92px minmax(0, 1fr);
      gap: 8px;
      text-align: left;
    }
  }
  /* ── end TeamBalanceHexagon global styles ── */

  .page {
    min-height: 100vh;
    background: #090a0f;
    color: #f4f4f5;
    --display-font: "Bricolage Grotesque", Syne, "Space Grotesk", Sora, Outfit, Inter, system-ui, sans-serif;
    --mono-font: "IBM Plex Mono", "JetBrains Mono", "SFMono-Regular", Consolas, monospace;
    --body-font: Geist, Inter, "Plus Jakarta Sans", system-ui, sans-serif;
    font-family: var(--body-font);
    padding: 24px;
  }

  h1,
  h2,
  .mode-card strong,
  .challenge-grid strong,
  .analysis-copy h1,
  .result-head h1 {
    font-family: var(--display-font);
    letter-spacing: -0.035em;
  }

  .site-footer {
    width: 100%;
    margin: 26px auto 0;
    padding: 14px 20px 4px;
    color: rgba(185, 190, 203, 0.52);
    font-size: 11px;
    font-weight: 650;
    letter-spacing: 0.05em;
    text-align: center;
    transition: color 0.2s ease;
  }

  .site-footer:hover {
    color: #c9a646;
  }

  .nav {
    max-width: 1420px;
    min-height: 82px;
    margin: 0 auto 24px;
    border: 1px solid #262a38;
    border-radius: 22px;
    background:
      radial-gradient(circle at 76% 22%, rgba(201, 166, 70, 0.18), transparent 26%),
      radial-gradient(circle at 28% 82%, rgba(78, 103, 149, 0.16), transparent 28%),
      linear-gradient(135deg, #07080d 0%, #101522 54%, #14120a 100%);
    padding: 12px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: clamp(28px, 4vw, 72px);
    position: relative;
    z-index: 40;
  }

  .nav-brand {
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .mode-nav-icons {
    position: absolute;
    left: 50%;
    top: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: clamp(40px, 5vw, 96px);
    transform: translate(-50%, -50%);
  }

  .mode-nav-button {
    width: 48px;
    height: 48px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.055);
    display: grid;
    place-items: center;
    cursor: pointer;
    transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
  }

  .mode-nav-button img {
    width: 30px;
    height: 30px;
    object-fit: contain;
    animation: none;
  }

  .mode-nav-button:hover,
  .mode-nav-button:focus-visible {
    transform: translateY(-2px);
    background: rgba(255, 255, 255, 0.08);
  }

  .mode-nav-button.worldcup:hover,
  .mode-nav-button.worldcup:focus-visible,
  .mode-nav-button.worldcup.active {
    border-color: rgba(201, 166, 70, 0.82);
    box-shadow: 0 0 22px rgba(201, 166, 70, 0.28);
  }

  .mode-nav-button.invincibles:hover,
  .mode-nav-button.invincibles:focus-visible,
  .mode-nav-button.invincibles.active {
    border-color: rgba(91, 157, 255, 0.82);
    box-shadow: 0 0 22px rgba(91, 157, 255, 0.28);
  }

  .mode-nav-button.et:hover,
  .mode-nav-button.et:focus-visible,
  .mode-nav-button.et.active {
    border-color: rgba(57, 230, 201, 0.9);
    box-shadow: 0 0 24px rgba(57, 230, 201, 0.34);
  }

  .nav span,
  .muted,
  .spots {
    color: #8a8f9e;
  }

  .nav span {
    font-weight: 900;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }

  .nav img {
    height: 66px;
    flex: 0 0 auto;
    animation: logoFade 0.7s ease both;
  }

  .mode-nav-icons .mode-nav-button img {
    width: 30px;
    height: 30px;
    object-fit: contain;
    animation: none;
  }

  .menu-nav {
    min-height: 64px;
    background:
      linear-gradient(135deg, rgba(7, 8, 13, 0.92), rgba(16, 21, 34, 0.78));
    padding: 10px 16px;
  }

  .menu-nav img {
    height: 42px;
  }

  .header-iog-help {
    position: relative;
    flex: 0 0 auto;
  }

  .iog-help-label {
    display: inline-block;
    color: #c5cad8;
    padding: 0;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: none;
    cursor: help;
  }

  .header-iog-help > span:not(.iog-help-label) {
    position: absolute;
    right: 0;
    top: calc(100% + 12px);
    z-index: 60;
    width: min(430px, calc(100vw - 48px));
    border: 1px solid rgba(201, 166, 70, 0.32);
    border-radius: 16px;
    background: rgba(10, 12, 18, 0.98);
    box-shadow: 0 24px 70px rgba(0, 0, 0, 0.48);
    color: #f4f4f5;
    padding: 18px 20px;
    font-size: 15px;
    font-weight: 800;
    line-height: 1.5;
    letter-spacing: 0;
    text-transform: none;
    opacity: 0;
    pointer-events: none;
    transform: translateY(-6px);
    transition: opacity 0.16s ease, transform 0.16s ease;
  }

  .header-iog-help:hover > span:not(.iog-help-label),
  .header-iog-help:focus-within > span:not(.iog-help-label) {
    opacity: 1;
    transform: translateY(0);
  }

  .panel {
    background: #10121a;
    border: 1px solid #262a38;
    border-radius: 26px;
    padding: 32px;
  }

  .main-menu {
    max-width: 1240px;
    margin: 0 auto;
    animation: fadeIn 0.55s ease both;
  }

  .hero-shell {
    min-height: 670px;
    position: relative;
    overflow: hidden;
    border-radius: 30px;
    border: 1px solid #262a38;
    background: #10121a;
    display: grid;
    align-items: center;
    padding: clamp(44px, 6vw, 78px);
    box-shadow: 0 28px 90px rgba(0, 0, 0, 0.32);
  }

  .hero-shell::before {
    content: "";
    position: absolute;
    inset: 0;
    z-index: 0;
    background:
      radial-gradient(circle at 78% 22%, rgba(201, 166, 70, 0.12), transparent 24%),
      radial-gradient(circle at 18% 78%, rgba(78, 103, 149, 0.1), transparent 28%),
      linear-gradient(112deg, transparent 8%, rgba(255, 255, 255, 0.034) 28%, transparent 43%),
      linear-gradient(72deg, transparent 54%, rgba(201, 166, 70, 0.045) 70%, transparent 84%),
      linear-gradient(180deg, #0d111b 0%, #090a0f 72%);
    pointer-events: none;
  }

  .classified-stars,
  .orbital-map {
    position: absolute;
    inset: 0;
    z-index: 1;
    pointer-events: none;
  }

  .classified-stars {
    background:
      radial-gradient(circle at 12% 18%, rgba(255,255,255,.35) 0 1px, transparent 2px),
      radial-gradient(circle at 28% 72%, rgba(255,255,255,.28) 0 1px, transparent 2px),
      radial-gradient(circle at 52% 22%, rgba(201,166,70,.55) 0 1px, transparent 2px),
      radial-gradient(circle at 72% 48%, rgba(255,255,255,.25) 0 1px, transparent 2px),
      radial-gradient(circle at 86% 16%, rgba(201,166,70,.45) 0 1px, transparent 2px),
      radial-gradient(circle at 91% 78%, rgba(255,255,255,.22) 0 1px, transparent 2px);
    background-size: 260px 260px;
    opacity: 0.58;
    animation: starDrift 16s linear infinite;
  }

  .orbital-map {
    opacity: 0.28;
    background:
      radial-gradient(ellipse at 78% 45%, transparent 0 150px, rgba(201,166,70,.36) 152px 154px, transparent 156px),
      radial-gradient(ellipse at 76% 45%, transparent 0 245px, rgba(255,255,255,.16) 247px 248px, transparent 250px),
      radial-gradient(ellipse at 76% 45%, transparent 0 340px, rgba(201,166,70,.18) 342px 343px, transparent 345px),
      linear-gradient(118deg, transparent 0 58%, rgba(201,166,70,.24) 58.1%, transparent 58.3%),
      linear-gradient(24deg, transparent 0 68%, rgba(255,255,255,.14) 68.1%, transparent 68.25%);
    transform-origin: 78% 45%;
    animation: orbitalShift 22s ease-in-out infinite alternate;
  }

  .hero-depth {
    position: absolute;
    inset: 0;
    z-index: 2;
    opacity: 0.075;
    background:
      linear-gradient(90deg, transparent 49.85%, rgba(255, 255, 255, 0.8) 50%, transparent 50.15%),
      linear-gradient(0deg, transparent 67%, rgba(255, 255, 255, 0.58) 67.2%, transparent 67.4%),
      radial-gradient(circle at 50% 67%, transparent 0 72px, rgba(255, 255, 255, 0.65) 73px 74px, transparent 75px),
      radial-gradient(circle at 77% 30%, rgba(201, 166, 70, 0.75) 0 3px, transparent 4px),
      linear-gradient(128deg, transparent 0 62%, rgba(255, 255, 255, 0.55) 62.15%, transparent 62.3%);
    pointer-events: none;
  }

  .hero-shell::after {
    content: "";
    position: absolute;
    inset: 0;
    background:
      radial-gradient(circle at 70% 28%, rgba(255, 255, 255, 0.06), transparent 28%),
      radial-gradient(circle at 66% 25%, transparent 0, rgba(0, 0, 0, 0.1) 48%, rgba(0, 0, 0, 0.54) 100%),
      linear-gradient(90deg, rgba(9, 10, 15, 0.1) 0%, rgba(9, 10, 15, 0.22) 48%, rgba(9, 10, 15, 0.66) 100%),
      linear-gradient(180deg, rgba(9, 10, 15, 0.32) 0%, rgba(9, 10, 15, 0.68) 100%);
    z-index: 3;
    pointer-events: none;
  }

  .hero-content {
    position: relative;
    z-index: 4;
    width: 100%;
    display: grid;
    grid-template-columns: minmax(0, 1.15fr) minmax(280px, 0.85fr);
    gap: clamp(48px, 6vw, 120px);
    align-items: center;
    text-align: left;
    animation: fadeUp 0.6s ease both;
  }

  .hero-copy-column {
    min-width: 0;
    max-width: 950px;
  }

  .hero-system-label {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
    color: #c9a646;
    font-family: var(--mono-font);
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }

  .mobile-menu-logo {
    display: block;
    width: auto;
    height: 54px;
    margin: 0;
    object-fit: contain;
  }

  .hero-content h1 {
    max-width: 900px;
    margin: 0;
    font-size: clamp(64px, 8.1vw, 118px);
    line-height: 0.86;
    font-weight: 950;
    text-transform: uppercase;
  }

  .hero-copy {
    max-width: 720px;
    margin: 28px 0 0;
    color: #f4f4f5;
    font-size: clamp(24px, 2.5vw, 34px);
    line-height: 1.12;
    font-weight: 700;
  }

  .hero-tagline {
    margin: 14px 0 34px;
    max-width: 560px;
    color: #c5cad8;
    font-size: clamp(17px, 1.55vw, 22px);
    line-height: 1.5;
  }

  .menu-actions {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-start;
    align-items: center;
    gap: 12px;
  }

  .menu-actions .primary {
    min-height: 58px;
    padding-inline: 30px;
    font-size: 16px;
  }

  .about-inline-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-top: 0;
    min-height: 58px;
    color: #f4f4f5;
    font-size: 14px;
    font-weight: 900;
    letter-spacing: 0;
    text-decoration: none;
  }

  .about-inline-link:hover {
    color: #c9a646;
  }

  .hero-status-row {
    margin-top: 28px;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  .hero-status-row span,
  .hero-intel-panel span {
    border: 1px solid rgba(201, 166, 70, 0.2);
    border-radius: 999px;
    background: rgba(7, 8, 13, 0.48);
    color: rgba(213, 216, 224, 0.76);
    font-family: var(--mono-font);
    font-size: 11px;
    font-weight: 750;
    letter-spacing: 0.09em;
    text-transform: uppercase;
  }

  .hero-status-row span {
    padding: 8px 11px;
  }

  .hero-intel-panel {
    justify-self: end;
    width: min(260px, 100%);
    display: grid;
    gap: 12px;
    opacity: 0.66;
    pointer-events: none;
  }

  .hero-intel-panel span {
    display: block;
    padding: 10px 12px;
    border-radius: 14px;
    border-color: rgba(201, 166, 70, 0.14);
    background: rgba(11, 14, 23, 0.34);
    color: rgba(213, 216, 224, 0.62);
    backdrop-filter: blur(10px);
  }

  .hero-intel-panel span:nth-child(2),
  .hero-intel-panel span:nth-child(4) {
    transform: translateX(18px);
  }

  .about-card {
    margin: 28px auto 0;
    max-width: 880px;
    border: 1px solid rgba(255, 255, 255, 0.16);
    background: rgba(16, 18, 26, 0.72);
    border-radius: 24px;
    padding: 42px;
    backdrop-filter: blur(16px);
    animation: fadeUp 0.7s ease 0.08s both;
  }

  .entry-word {
    margin: 0;
    color: white;
    font-size: 58px;
    line-height: 0.9;
    font-weight: 950;
    letter-spacing: 0.08em;
  }

  .entry-kind {
    margin: 14px 0 24px;
    color: var(--accent);
    font-family: Inter, system-ui, sans-serif;
    font-size: 18px;
    font-style: italic;
  }

  .entry-prose {
    max-width: 720px;
    display: grid;
    gap: 18px;
  }

  .entry-prose p {
    margin: 0;
    color: #d5d8e0;
    font-size: clamp(17px, 1.6vw, 22px);
    line-height: 1.55;
  }

  .entry-prose p + p {
    border-top: 1px solid #262a38;
    padding-top: 18px;
  }

  .mode-screen,
  .formation-screen {
    max-width: 1120px;
    margin: 0 auto;
    text-align: center;
    padding: 72px;
    animation: fadeUp 0.45s ease both;
  }

  .mode-screen {
    max-width: 1100px;
    padding: 72px 48px;
  }

  .mode-screen .mode-grid {
    max-width: 1320px;
    margin-left: auto;
    margin-right: auto;
  }

  .back-link {
    display: inline-flex;
    margin: 0 auto 24px 0;
    border: 1px solid #262a38;
    background: #151823;
    color: white;
    border-radius: 999px;
    padding: 10px 16px;
    font-weight: 900;
    cursor: pointer;
  }

  .kicker {
    margin: 0;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.26em;
    font-size: 12px;
    font-weight: 900;
  }

  h1 {
    margin: 10px 0;
    font-size: 46px;
    line-height: 0.95;
    letter-spacing: -0.05em;
  }

  h2 {
    margin: 0;
    font-size: 28px;
  }

  .mode-grid,
  .formation-grid {
    margin-top: 36px;
    display: grid;
    gap: 16px;
  }

  .quick-loop {
    width: min(720px, 100%);
    margin: 18px auto 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    color: #c9cdd7;
    font-size: 12px;
    font-weight: 850;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }

  .quick-loop i {
    width: 34px;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(201, 166, 70, 0.85), transparent);
  }

  .mode-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 32px;
  }

  .mode-card.et-mode-card:hover {
    border-color: rgba(57, 230, 201, 0.72);
    box-shadow: 0 24px 70px rgba(0, 0, 0, 0.35), 0 0 30px rgba(57, 230, 201, 0.16);
  }

  .et-intro-screen .et-intro-body {
    position: relative;
    z-index: 2;
    max-width: 640px;
    margin: 48px auto 0;
    display: grid;
    gap: 16px;
    justify-items: center;
    text-align: center;
    animation: signalReveal 1.2s ease-out 1;
  }

  .et-intro-sigil {
    width: 128px;
    height: 128px;
    display: grid;
    place-items: center;
    border: 1px solid rgba(57, 230, 201, 0.32);
    border-radius: 32px;
    background:
      radial-gradient(circle at 50% 50%, rgba(57, 230, 201, 0.14), transparent 52%),
      rgba(5, 18, 14, 0.72);
    box-shadow: 0 0 42px rgba(57, 230, 201, 0.16);
  }

  .et-intro-sigil img {
    width: 92px;
    height: 92px;
    object-fit: contain;
    filter: drop-shadow(0 0 20px rgba(57, 230, 201, 0.34));
  }

  .et-intro-screen h1 {
    font-family: var(--display-font);
    font-size: clamp(28px, 4vw, 44px);
    color: #eafff7;
    letter-spacing: -0.02em;
  }

  .et-intro-screen .primary {
    margin-top: 8px;
    background: #39e6c9;
    color: #06120d;
    box-shadow: 0 12px 28px rgba(57, 230, 201, 0.22);
  }

  @keyframes signalReveal {
    0% { opacity: 0; transform: translateY(8px); filter: blur(2px); }
    35% { opacity: 0.5; filter: blur(1px); }
    55% { opacity: 0.25; }
    100% { opacity: 1; transform: translateY(0); filter: blur(0); }
  }

  .formation-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .mode-grid button,
  .formation-grid button {
    min-height: 150px;
    border: 1px solid #262a38;
    background: #151823;
    color: white;
    border-radius: 20px;
    cursor: pointer;
  }

  .mode-grid button {
    min-height: 260px;
    padding: 34px;
    text-align: center;
    display: grid;
    align-content: center;
    justify-items: center;
  }

  .mode-grid .mode-card {
    min-height: 470px;
    padding: 10px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    text-align: left;
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(234, 179, 8, 0.3);
    border-radius: 8px;
    box-shadow: 0 18px 50px rgba(0, 0, 0, 0.22);
    transition: transform 250ms ease, border-color 250ms ease, box-shadow 250ms ease;
  }

  .mode-grid .mode-card:hover {
    transform: translateY(-4px);
    border-color: rgba(250, 204, 21, 0.7);
    box-shadow: 0 24px 70px rgba(0, 0, 0, 0.35), 0 0 28px rgba(201, 166, 70, 0.13);
  }

  .mode-card-image {
    width: 72%;
    height: 158px;
    object-fit: contain;
    object-position: center;
    display: block;
    border-radius: 18px;
    margin: 0 auto 24px;
  }

  .mode-grid .mode-card .mode-badge {
    position: static;
    margin-top: 12px;
    color: rgba(201, 166, 70, 0.94);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.16em;
    text-transform: uppercase;
  }

  .mode-card-content {
    padding: 0 20px 22px;
  }

  .mode-grid .mode-card .mode-card-content strong {
    margin: 0;
    color: #ffffff;
    font-size: 29px;
    line-height: 1.08;
  }

  .mode-grid .mode-card .mode-card-content span {
    max-width: none;
    margin-top: 14px;
    color: rgba(255, 255, 255, 0.75);
    font-size: 15px;
    line-height: 1.6;
    text-align: left;
  }

  .mode-grid .mode-card .mode-card-content .mode-badge {
    font-size: 11px;
    line-height: 1;
  }

  .mode-card-content em {
    display: block;
    max-width: 260px;
    margin-top: 14px;
    color: rgba(226, 232, 240, 0.72);
    font-size: clamp(0.9rem, 1vw, 1rem);
    font-style: normal;
    font-weight: 500;
    line-height: 1.35;
  }

  .mode-select-label {
    display: inline-flex !important;
    align-items: center;
    justify-content: center;
    width: auto !important;
    margin-top: 22px !important;
    border: 1px solid rgba(201, 166, 70, 0.35);
    border-radius: 999px;
    background: rgba(201, 166, 70, 0.1);
    color: #f3e4a3 !important;
    padding: 9px 14px;
    font-size: 10px !important;
    font-weight: 900;
    letter-spacing: 0.12em;
    line-height: 1 !important;
    text-transform: uppercase;
  }

  .mode-preview {
    margin-top: 18px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .mode-preview span {
    width: auto;
    margin: 0 !important;
    border: 1px solid rgba(201, 166, 70, 0.24);
    border-radius: 999px;
    background: rgba(201, 166, 70, 0.07);
    color: #d8dce6 !important;
    padding: 7px 9px;
    font-size: 10px !important;
    font-weight: 850;
    letter-spacing: 0.08em;
    line-height: 1 !important;
    text-transform: uppercase;
  }

  .et-preview span {
    border-color: rgba(57, 230, 201, 0.28);
    background: rgba(57, 230, 201, 0.08);
  }

  .mode-card.et-mode-card {
    justify-content: center;
  }

  .mode-card.et-mode-card .mode-card-content {
    min-height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .mode-option {
    min-height: 270px;
    border: 1px solid #262a38;
    background: #151823;
    color: white;
    border-radius: 20px;
    padding: 34px;
    text-align: left;
  }

  .desktop-mode-logo {
    display: block;
    width: min(240px, 32vw);
    max-height: 128px;
    object-fit: contain;
    margin: 0 auto 22px;
    filter: drop-shadow(0 18px 34px rgba(201, 166, 70, 0.12));
  }

  .challenge-grid {
    width: min(1100px, 100%);
    margin: 34px auto 0;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 18px;
  }

  .challenge-grid button {
    min-height: 176px;
    padding: 24px;
    border: 1px solid rgba(201, 166, 70, 0.28);
    border-radius: 18px;
    background:
      linear-gradient(145deg, rgba(255, 255, 255, 0.07), rgba(255, 255, 255, 0.02)),
      #151823;
    color: white;
    text-align: left;
    cursor: pointer;
    transition: transform 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease, background 0.22s ease;
  }

  .challenge-grid button:hover,
  .challenge-grid button:focus-visible {
    transform: translateY(-3px);
    border-color: rgba(234, 179, 8, 0.72);
    box-shadow: 0 18px 42px rgba(0, 0, 0, 0.34), 0 0 26px rgba(201, 166, 70, 0.1);
    outline: none;
  }

  .challenge-grid strong {
    display: block;
    color: #fff;
    font-size: 18px;
    line-height: 1.2;
  }

  .challenge-grid span {
    display: block;
    margin-top: 12px;
    color: rgba(221, 226, 238, 0.72);
    font-size: 13px;
    line-height: 1.5;
  }

  .bench-screen {
    max-width: 1100px;
    margin: 0 auto;
    padding: 36px 40px 48px;
    animation: fadeUp 0.45s ease both;
  }

  .bench-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 24px;
  }

  .bench-subtitle {
    margin: 6px 0 0;
    color: #8c92a2;
    font-size: 14px;
  }

  .bench-counter {
    flex-shrink: 0;
    border: 1px solid #282c38;
    border-radius: 14px;
    background: #151823;
    padding: 12px 18px;
    text-align: center;
  }

  .bench-counter-value {
    display: block;
    color: #efd574;
    font-size: 30px;
    font-weight: 900;
    line-height: 1;
  }

  .bench-counter-label {
    display: block;
    margin-top: 2px;
    color: #6b7180;
    font-size: 12px;
    font-weight: 750;
  }

  .bench-slots-row {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 10px;
    margin-bottom: 20px;
  }

  .bench-slot {
    position: relative;
    border: 1px solid #282c38;
    border-radius: 14px;
    background: #151823;
    padding: 12px;
    min-height: 88px;
    display: flex;
    flex-direction: column;
    gap: 5px;
    transition: border-color 0.18s, background 0.18s;
  }

  .bench-slot.bench-slot-filled {
    border-color: rgba(201, 166, 70, 0.4);
    background: rgba(201, 166, 70, 0.06);
  }

  .bench-slot-label {
    display: block;
    color: #8c92a2;
    font-size: 9px;
    font-weight: 900;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  .bench-slot-name {
    display: block;
    color: #f0f2f6;
    font-size: 13px;
    font-weight: 800;
    line-height: 1.2;
  }

  .bench-slot-iog {
    display: block;
    color: #efd574;
    font-size: 11px;
    font-weight: 700;
  }

  .bench-slot-empty {
    display: block;
    color: #434858;
    font-size: 11px;
    line-height: 1.3;
    margin-top: 4px;
  }

  .bench-slot-remove {
    position: absolute;
    top: 8px;
    right: 8px;
    width: 20px;
    height: 20px;
    border: 0;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
    color: #8c92a2;
    font-size: 14px;
    line-height: 1;
    cursor: pointer;
    padding: 0;
    display: grid;
    place-items: center;
    transition: background 0.15s, color 0.15s;
  }

  .bench-slot-remove:hover {
    background: rgba(248, 113, 113, 0.18);
    color: #f87171;
  }

  .bench-live-impact {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    align-items: stretch;
    border: 1px solid #282c38;
    border-radius: 12px;
    background: #0f1119;
    padding: 10px;
    margin-bottom: 18px;
  }

  .bench-live-impact span {
    min-width: 0;
    border: 1px solid rgba(201, 166, 70, 0.16);
    border-radius: 10px;
    background: rgba(201, 166, 70, 0.045);
    padding: 10px;
    color: #6b7180;
    font-size: 11px;
    font-weight: 750;
    letter-spacing: 0.04em;
    line-height: 1.25;
  }

  .bench-live-impact span strong {
    display: block;
    margin: 5px 0 0;
    color: #efd574;
    font-size: 13px;
  }

  .bench-pool-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    margin-bottom: 12px;
  }

  .bench-pool-header > span {
    color: #8c92a2;
    font-size: 11px;
    font-weight: 850;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    white-space: nowrap;
  }

  .bench-search-input {
    width: 100%;
    max-width: 280px;
    border: 1px solid #282c38;
    border-radius: 10px;
    background: #151823;
    color: #f0f2f6;
    font-size: 14px;
    padding: 8px 12px;
    outline: none;
    transition: border-color 0.15s;
  }

  .bench-search-input:focus {
    border-color: rgba(201, 166, 70, 0.5);
  }

  .bench-pool-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 8px;
    max-height: 340px;
    overflow-y: auto;
    padding-right: 4px;
    margin-bottom: 18px;
  }

  .bench-pool-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    border: 1px solid #282c38;
    border-radius: 12px;
    background: #151823;
    color: #f0f2f6;
    padding: 11px 14px;
    text-align: left;
    cursor: pointer;
    transition: border-color 0.15s, background 0.15s, transform 0.12s;
  }

  .bench-pool-card:hover:not(:disabled) {
    border-color: rgba(201, 166, 70, 0.42);
    background: rgba(201, 166, 70, 0.06);
    transform: translateY(-1px);
  }

  .bench-pool-card:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .bench-pool-info {
    min-width: 0;
  }

  .bench-pool-info strong {
    display: block;
    font-size: 14px;
    font-weight: 800;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .bench-pool-info small {
    display: block;
    margin-top: 2px;
    color: #8c92a2;
    font-size: 11px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .bench-pool-iog {
    flex-shrink: 0;
    border: 1px solid rgba(201, 166, 70, 0.28);
    border-radius: 999px;
    color: #efd574;
    padding: 4px 9px;
    font-size: 11px;
    font-weight: 700;
    white-space: nowrap;
  }

  .bench-pool-empty {
    grid-column: 1 / -1;
    text-align: center;
    color: #6b7180;
    font-size: 14px;
    padding: 24px 0;
  }

  .bench-phoebe {
    width: min(660px, 100%);
    margin: 0 0 18px;
    display: flex;
    align-items: center;
    gap: 14px;
    border: 1px solid rgba(201, 166, 70, 0.24);
    border-radius: 18px;
    background: rgba(201, 166, 70, 0.06);
    padding: 12px 16px;
  }

  .bench-phoebe img {
    width: 48px;
    height: 48px;
    border-radius: 14px;
    object-fit: cover;
    flex-shrink: 0;
  }

  .bench-phoebe p {
    margin: 0;
    color: #d7dbe5;
    font-size: 14px;
    line-height: 1.45;
  }

  .bench-actions {
    display: flex;
    gap: 12px;
  }

  .bench-result-summary {
    margin-top: 28px;
  }

  .bench-result-summary h2 {
    margin: 0 0 16px;
    font-size: 18px;
    letter-spacing: -0.02em;
  }

  .bench-impact-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }

  .bench-impact-grid article {
    border: 1px solid #282c38;
    border-radius: 14px;
    background: #151823;
    padding: 14px 16px;
  }

  .bench-impact-grid span {
    display: block;
    color: #8c92a2;
    font-size: 10px;
    font-weight: 850;
    letter-spacing: 0.13em;
    text-transform: uppercase;
  }

  .bench-impact-grid strong {
    display: block;
    margin-top: 8px;
    color: #efd574;
    font-size: 22px;
    font-variant-numeric: tabular-nums;
  }

  .bench-result-note {
    margin: 14px 0 0;
    border-left: 2px solid rgba(201, 166, 70, 0.5);
    padding: 8px 12px;
    background: rgba(201, 166, 70, 0.05);
    color: #c8ccd6;
    font-size: 13px;
    line-height: 1.5;
  }

  @media (max-width: 768px) {
    .bench-screen {
      padding: 20px 16px 32px;
    }

    .bench-slots-row {
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 6px;
    }

    .bench-slot {
      padding: 8px 6px;
      min-height: 72px;
    }

    .bench-slot-name {
      font-size: 11px;
    }

    .bench-slot-empty {
      font-size: 9px;
    }

    .bench-pool-grid {
      grid-template-columns: 1fr;
      max-height: 280px;
    }

    .bench-counter {
      padding: 9px 14px;
    }

    .bench-counter-value {
      font-size: 24px;
    }
  }

  @media (max-width: 430px) {
    .bench-slots-row {
      grid-template-columns: repeat(5, 1fr);
    }

    .bench-slot-label {
      font-size: 8px;
    }

    .bench-slot-name {
      font-size: 10px;
    }

    .bench-slot-remove {
      width: 16px;
      height: 16px;
      font-size: 12px;
    }
  }

  .league-buttons {
    margin-top: 22px;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .mode-grid .league-buttons button {
    min-height: 0;
    border-radius: 12px;
    padding: 14px;
  }

  .mode-grid .league-buttons strong {
    margin-top: 0;
    font-size: 16px;
  }

  .mode-grid .league-buttons span {
    margin-top: 6px;
    font-size: 12px;
  }

  .mode-grid button:hover,
  .formation-grid button:hover {
    border-color: var(--accent);
  }

  .mode-grid button.tutorial-highlight {
    position: relative;
    z-index: 1101;
    border-color: var(--accent);
    box-shadow: 0 0 0 1px rgba(201, 166, 70, 0.65), 0 24px 70px rgba(0, 0, 0, 0.42);
  }

  .mode-grid .mode-card:nth-child(2).tutorial-highlight {
    box-shadow: 0 0 0 1px rgba(201, 166, 70, 0.65), 0 0 34px rgba(168, 85, 247, 0.3), 0 24px 70px rgba(0, 0, 0, 0.42);
  }

  .mode-grid button.tutorial-dim {
    opacity: 0.38;
  }

  .mode-grid button:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  .formation-grid span {
    display: block;
    color: #8a8f9e;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.18em;
  }

  .mode-grid span {
    display: block;
    max-width: 300px;
    margin-top: 20px;
    color: #a7adc2;
    font-size: 17px;
    line-height: 1.45;
    text-align: center;
  }

  .mode-grid strong,
  .mode-option > strong,
  .formation-grid strong {
    display: block;
    margin-top: 10px;
  }

  .mode-grid strong,
  .mode-option > strong {
    color: white;
    font-size: 34px;
    line-height: 1;
  }

  .mode-option > span {
    display: block;
    max-width: 300px;
    margin-top: 20px;
    color: #a7adc2;
    font-size: 17px;
    line-height: 1.45;
  }

  .formation-grid strong {
    font-size: 34px;
  }

  .formation-grid small {
    display: none;
  }

  .draft-grid {
    max-width: 1420px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 1.35fr 0.9fr;
    gap: 24px;
  }

  .panel.right {
    display: flex;
    flex-direction: column;
  }

  .draft-head,
  .board-head,
  .result-head {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .result-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: flex-end;
  }

  .board-head {
    align-items: center;
    gap: 18px;
    padding-bottom: 18px;
    border-bottom: 1px solid #262a38;
  }

  .board-head h2 {
    line-height: 1;
  }

  .counter,
  .selection-pill {
    background: #1b1f2b;
    border-radius: 999px;
    padding: 12px 20px;
    color: #a7adc2;
    font-weight: 800;
  }

  .muted-pill {
    opacity: 0.7;
  }

  .board-status {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    align-items: center;
    gap: 8px;
  }

  .chemistry-pill {
    border: 1px solid rgba(201, 166, 70, 0.3);
    border-radius: 999px;
    background: rgba(201, 166, 70, 0.08);
    padding: 11px 14px;
    color: #9da3b2;
    font-size: 12px;
    font-weight: 800;
  }

  .chemistry-pill strong {
    margin-left: 5px;
    color: #c9a646;
  }

  .mobile-draft-sticky {
    display: none;
  }

  .mobile-squad-tracker {
    display: none;
  }

  .mobile-slot-sheet {
    display: none;
  }

  .mobile-sheet-backdrop {
    display: none;
  }

  .pick-impact-strip {
    margin-top: 14px;
    display: grid;
    grid-template-columns: minmax(0, 1fr) 76px minmax(240px, 1.35fr);
    align-items: center;
    gap: 12px;
    border: 1px solid rgba(201, 166, 70, 0.24);
    border-radius: 16px;
    background:
      radial-gradient(circle at 12% 0%, rgba(201, 166, 70, 0.11), transparent 34%),
      #121620;
    min-height: 76px;
    padding: 12px 14px;
    animation: pickImpactFlash 0.75s ease both;
  }

  .pick-impact-strip span {
    display: block;
    color: #8f95a5;
    font-size: 10px;
    font-weight: 850;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  .pick-impact-strip strong {
    display: block;
    margin-top: 4px;
    color: #f6f1d0;
    font-size: 15px;
    line-height: 1.15;
  }

  .pick-impact-strip p {
    margin: 0;
    color: #cbd0dd;
    font-size: 13px;
    line-height: 1.35;
  }

  @keyframes pickImpactFlash {
    0% { box-shadow: 0 0 0 rgba(201, 166, 70, 0); transform: translateY(-2px); }
    40% { box-shadow: 0 0 28px rgba(201, 166, 70, 0.16); }
    100% { box-shadow: 0 0 0 rgba(201, 166, 70, 0); transform: translateY(0); }
  }

  .pick-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 10px;
    animation: chipsIn 0.22s ease both;
  }

  .pick-impact-row {
    width: min(100%, 560px);
    min-height: 32px;
    align-self: center;
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 12px auto 22px;
    padding-inline: 4px;
    flex-wrap: wrap;
  }

  .pick-impact-row.empty {
    margin-bottom: 18px;
  }

  .pick-impact-row .pick-chips {
    margin: 0;
    min-width: 0;
  }

  .pick-impact-label {
    flex: 0 0 auto;
    color: rgba(148, 163, 184, 0.85);
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    white-space: nowrap;
  }

  .live-analysis-visual :global(.balance-panel) {
    margin-top: 0;
  }

  .pick-chip {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    min-height: 28px;
    padding: 0 10px;
    font-size: 12px;
    font-weight: 800;
    line-height: 1;
    letter-spacing: 0.04em;
    white-space: nowrap;
    animation: chipFadeOut 2.4s ease forwards;
    animation-delay: 0.18s;
    backdrop-filter: blur(6px);
  }

  .pick-chip-good {
    background: rgba(34, 240, 178, 0.14);
    border: 1px solid rgba(34, 240, 178, 0.35);
    color: #22f0b2;
  }

  .pick-chip-warn {
    background: rgba(251, 191, 36, 0.12);
    border: 1px solid rgba(251, 191, 36, 0.3);
    color: #fbbf24;
  }

  .pick-chip-info {
    background: rgba(148, 163, 184, 0.1);
    border: 1px solid rgba(148, 163, 184, 0.24);
    color: #94a3b8;
  }

  .pick-chip-bad {
    background: rgba(248, 113, 113, 0.12);
    border: 1px solid rgba(248, 113, 113, 0.34);
    color: #f87171;
  }

  @keyframes chipsIn {
    from { opacity: 0; transform: translateY(-6px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  @keyframes chipFadeOut {
    0%   { opacity: 1; }
    70%  { opacity: 1; }
    100% { opacity: 0; }
  }

  .universe-grid {
    margin: 28px 0;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
  }

  .universe-grid div {
    background: #151823;
    border: 1px solid #262a38;
    border-radius: 18px;
    padding: 20px;
  }

  .universe-grid span {
    display: block;
    color: #8a8f9e;
    font-size: 12px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }

  .universe-grid strong {
    display: block;
    margin-top: 10px;
    font-size: 22px;
  }

  .spinning {
    animation: spinPulse 0.12s linear infinite;
  }

  @keyframes spinPulse {
    0% { opacity: 0.55; transform: translateY(0); }
    50% { opacity: 1; transform: translateY(-7px); }
    100% { opacity: 0.55; transform: translateY(0); }
  }

  @keyframes starDrift {
    from { background-position: 0 0; }
    to { background-position: 260px 160px; }
  }

  @keyframes orbitalShift {
    from { transform: rotate(-1.5deg) scale(1); opacity: 0.18; }
    to { transform: rotate(1.5deg) scale(1.03); opacity: 0.3; }
  }

  /* ET Mode alien ambience */
  .et-ambience {
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    overflow: hidden;
  }

  .et-cosmic-fog {
    position: absolute;
    inset: 0;
    background:
      radial-gradient(ellipse at 50% 0%, rgba(8, 30, 24, 0.55) 0%, transparent 60%),
      radial-gradient(ellipse at 50% 100%, rgba(6, 20, 16, 0.6) 0%, transparent 65%),
      linear-gradient(180deg, #050a08 0%, #07120f 50%, #050a08 100%);
  }

  .et-stars {
    position: absolute;
    inset: 0;
    opacity: 0.5;
    background:
      radial-gradient(circle at 14% 22%, rgba(57, 230, 201, .4) 0 1px, transparent 2px),
      radial-gradient(circle at 32% 68%, rgba(255, 255, 255, .22) 0 1px, transparent 2px),
      radial-gradient(circle at 58% 14%, rgba(201, 166, 70, .35) 0 1px, transparent 2px),
      radial-gradient(circle at 74% 52%, rgba(57, 230, 201, .3) 0 1px, transparent 2px),
      radial-gradient(circle at 88% 78%, rgba(255, 255, 255, .18) 0 1px, transparent 2px);
    background-size: 300px 300px;
    animation: starDrift 46s linear infinite;
  }

  .et-ufo {
    position: absolute;
    width: 220px;
    height: 70px;
    opacity: 0.16;
    background:
      radial-gradient(ellipse 50% 100% at 50% 35%, rgba(180, 255, 230, 0.8) 0%, transparent 70%),
      radial-gradient(ellipse 100% 45% at 50% 70%, rgba(57, 230, 201, 0.55) 0%, transparent 75%);
    filter: blur(2px);
  }

  .et-ufo-one {
    top: 14%;
    left: -10%;
    animation: ufoDriftOne 64s linear infinite;
  }

  .et-ufo-two {
    top: 58%;
    left: -16%;
    width: 160px;
    height: 52px;
    animation: ufoDriftTwo 80s linear infinite;
    animation-delay: -22s;
  }

  .et-scanline {
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(0deg, transparent 0px, rgba(57, 230, 201, 0.05) 1px, transparent 3px);
    opacity: 0.5;
    animation: scanlineDrift 9s linear infinite;
  }

  .et-static-noise {
    position: absolute;
    inset: 0;
    opacity: 0.035;
    background: repeating-conic-gradient(rgba(255, 255, 255, 0.5) 0% 0.02%, transparent 0% 0.04%);
    animation: staticFlicker 6s steps(2, jump-none) infinite;
  }

  .et-glyph-ring {
    background:
      radial-gradient(circle at 50% 50%, transparent 0 38%, rgba(57, 230, 201, 0.5) 38.3% 38.6%, transparent 39%),
      radial-gradient(circle at 50% 50%, transparent 0 58%, rgba(57, 230, 201, 0.3) 58.3% 58.6%, transparent 59%),
      radial-gradient(circle at 50% 50%, transparent 0 78%, rgba(57, 230, 201, 0.18) 78.3% 78.6%, transparent 79%);
  }

  .page.et-mode .nav,
  .page.et-mode .panel,
  .page.et-mode .analysis-stage,
  .page.et-mode .play-level-stage,
  .page.et-mode .simulation-stage,
  .page.et-mode .result-grid {
    border-color: rgba(57, 230, 201, 0.2);
    background:
      radial-gradient(circle at 84% 14%, rgba(57, 230, 201, 0.08), transparent 28%),
      linear-gradient(145deg, rgba(5, 17, 14, 0.95), rgba(10, 13, 22, 0.95) 64%, rgba(4, 14, 11, 0.98));
  }

  .page.et-mode .panel,
  .page.et-mode .analysis-stage,
  .page.et-mode .play-level-stage,
  .page.et-mode .simulation-stage,
  .page.et-mode .result-grid {
    box-shadow: 0 24px 80px rgba(0, 0, 0, 0.36), inset 0 0 54px rgba(57, 230, 201, 0.025);
  }

  .page.et-mode .formation-screen,
  .page.et-mode .draft-grid,
  .page.et-mode .play-level-stage,
  .page.et-mode .result-grid {
    position: relative;
  }

  .page.et-mode .formation-screen::after,
  .page.et-mode .draft-grid::after,
  .page.et-mode .play-level-stage::after,
  .page.et-mode .result-grid::after {
    content: "";
    position: absolute;
    right: clamp(18px, 4vw, 52px);
    top: clamp(18px, 4vw, 52px);
    width: min(150px, 18vw);
    aspect-ratio: 1;
    background: url("/alien.png") center / contain no-repeat;
    opacity: 0.07;
    filter: drop-shadow(0 0 30px rgba(57, 230, 201, 0.34));
    pointer-events: none;
  }

  .page.et-mode .kicker,
  .page.et-mode .analysis-kicker,
  .page.et-mode .mode-badge {
    color: #39e6c9;
  }

  .page.et-mode .primary {
    background: #39e6c9;
    color: #04120f;
    box-shadow: 0 12px 28px rgba(57, 230, 201, 0.16);
  }

  .page.et-mode .primary:hover {
    background: #28cdb4;
  }

  .page.et-mode .secondary,
  .page.et-mode .back-link,
  .page.et-mode .player-card,
  .page.et-mode .universe-grid div,
  .page.et-mode .formation-grid button,
  .page.et-mode .assign-panel {
    border-color: rgba(57, 230, 201, 0.18);
    background: rgba(9, 20, 18, 0.72);
  }

  .page.et-mode .player-card:hover,
  .page.et-mode .formation-grid button:hover,
  .page.et-mode .back-link:hover {
    border-color: rgba(57, 230, 201, 0.42);
    box-shadow: 0 0 24px rgba(57, 230, 201, 0.1);
  }

  .page.et-mode .analysis-stage {
    --analysis-tone: #39e6c9;
  }

  .page.et-mode .analysis-stage::before {
    opacity: 0.18;
    background:
      repeating-linear-gradient(0deg, transparent 0 12px, rgba(57, 230, 201, 0.05) 13px),
      radial-gradient(circle at 86% 22%, rgba(57, 230, 201, 0.16), transparent 30%);
  }

  .page.et-mode .analysis-stage::after {
    content: "";
    position: absolute;
    right: 5%;
    bottom: 7%;
    width: min(190px, 22vw);
    aspect-ratio: 1;
    background: url("/alien.png") center / contain no-repeat;
    opacity: 0.075;
    filter: drop-shadow(0 0 36px rgba(57, 230, 201, 0.42));
    pointer-events: none;
  }

  @keyframes ufoDriftOne {
    0% { transform: translate(0, 0); }
    50% { transform: translate(60vw, 4vh); }
    100% { transform: translate(120vw, 0); }
  }

  @keyframes ufoDriftTwo {
    0% { transform: translate(0, 0); }
    50% { transform: translate(55vw, -6vh); }
    100% { transform: translate(130vw, 0); }
  }

  @keyframes scanlineDrift {
    from { background-position: 0 0; }
    to { background-position: 0 60px; }
  }

  @keyframes staticFlicker {
    0%, 100% { opacity: 0.02; }
    50% { opacity: 0.05; }
  }

  @media (prefers-reduced-motion: reduce) {
    .et-stars,
    .et-ufo,
    .et-scanline,
    .et-static-noise,
    .et-intro-screen .et-intro-body,
    .et-signal-orb,
    .et-signal-orb img {
      animation: none !important;
    }

    .page.et-mode .pitch::before,
    .page.et-mode .final-pitch::before {
      animation: none !important;
      background: none !important;
    }
  }

  .controls {
    margin-top: 16px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
  }

  .primary,
  .secondary {
    border: 0;
    border-radius: 999px;
    padding: 14px 22px;
    font-weight: 900;
    cursor: pointer;
    transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease;
  }

  .back-link,
  .mode-grid button,
  .formation-grid button,
  .player-card {
    transition: transform 0.16s ease, border-color 0.16s ease;
  }

  .back-link:hover,
  .primary:hover,
  .secondary:hover,
  .mode-grid button:hover,
  .formation-grid button:hover {
    transform: translateY(-1px);
  }

  .primary {
    background: #c9a646;
    color: #090a0f;
    box-shadow: 0 12px 28px rgba(201, 166, 70, 0.18);
  }

  .primary:hover {
    background: #b99634;
  }

  .primary:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }

  .secondary {
    background: #151823;
    color: white;
    border: 1px solid #262a38;
  }

  .status,
  .notice {
    margin-top: 16px;
    background: #151823;
    border: 1px solid #262a38;
    border-radius: 16px;
    padding: 16px 18px;
    text-align: center;
  }

  .notice {
    color: var(--accent);
  }

  .et-signal-search {
    margin-top: 20px;
    min-height: 172px;
    border: 1px solid rgba(57, 230, 201, 0.28);
    border-radius: 20px;
    background:
      repeating-linear-gradient(0deg, transparent 0 9px, rgba(57, 230, 201, 0.035) 10px),
      radial-gradient(circle at 50% 42%, rgba(57, 230, 201, 0.14), transparent 45%),
      linear-gradient(145deg, rgba(5, 18, 14, 0.94), rgba(10, 18, 25, 0.94));
    display: grid;
    place-items: center;
    gap: 8px;
    padding: 26px;
    text-align: center;
    box-shadow: inset 0 0 38px rgba(57, 230, 201, 0.045), 0 16px 48px rgba(0, 0, 0, 0.26);
  }

  .et-signal-orb {
    width: 78px;
    height: 78px;
    display: grid;
    place-items: center;
    border-radius: 999px;
    background:
      radial-gradient(circle at center, rgba(57, 230, 201, 0.12), transparent 62%),
      conic-gradient(from 0deg, transparent, rgba(57, 230, 201, 0.42), transparent 38%);
    animation: etSignalRotate 0.82s linear infinite;
  }

  .et-signal-orb img {
    width: 44px;
    height: 44px;
    object-fit: contain;
    filter: drop-shadow(0 0 14px rgba(57, 230, 201, 0.45));
    animation: etSignalCounter 0.82s linear infinite;
  }

  .et-signal-search strong {
    color: #dffff8;
    font-family: var(--mono-font);
    font-size: 13px;
    font-weight: 850;
    letter-spacing: 0.16em;
  }

  .et-signal-search span {
    color: rgba(168, 255, 235, 0.6);
    font-size: 12px;
    font-weight: 750;
  }

  @keyframes etSignalRotate {
    to { transform: rotate(360deg); }
  }

  @keyframes etSignalCounter {
    to { transform: rotate(-360deg); }
  }

  .golden-round,
  .pick-result {
    border-color: rgba(201, 166, 70, 0.45);
    background: linear-gradient(135deg, rgba(201, 166, 70, 0.22), #151823 60%);
  }

  .danger {
    color: #f87171;
  }

  .pool-tools {
    margin-top: 18px;
    display: grid;
    grid-template-columns: minmax(0, 1fr) 220px 180px;
    gap: 10px;
  }

  .search,
  .pool-tools select {
    width: 100%;
    border: 1px solid #262a38;
    background: #151823;
    color: white;
    border-radius: 16px;
    min-height: 56px;
    padding: 13px 16px;
    font-size: 16px;
    box-sizing: border-box;
  }

  .pool-tools select {
    cursor: pointer;
  }

  .spots {
    margin: 12px 0 14px;
  }

  .player-list {
    max-height: 560px;
    overflow-y: auto;
    padding-right: 6px;
    display: grid;
    gap: 10px;
  }

  .load-more-options {
    width: 100%;
    margin-top: 14px;
  }

  .player-card {
    border: 1px solid #262a38;
    background: #151823;
    color: white;
    border-radius: 16px;
    padding: 16px;
    text-align: left;
    cursor: pointer;
    position: relative;
    transform-style: preserve-3d;
  }

  .player-card:hover,
  .player-card.selected {
    border-color: var(--accent);
  }

  .player-card:hover {
    transform: translateY(-3px);
  }

  .player-card.selected {
    box-shadow: 0 0 0 2px rgba(201, 166, 70, 0.6), 0 0 28px rgba(201, 166, 70, 0.24);
  }

  .player-card.selected .player-main {
    animation: mysteryFlip 0.34s ease both;
  }

  .mystery-unknown {
    color: #fff;
  }

  .mystery-question {
    width: 58px;
    height: 58px;
    margin-top: 16px;
    display: grid;
    place-items: center;
    border: 1px solid rgba(201, 166, 70, 0.48);
    border-radius: 50%;
    background: rgba(201, 166, 70, 0.08);
    color: #d6b957;
    font-size: 30px;
    font-weight: 900;
  }

  .mystery-pitch-label {
    font-size: 12px !important;
    letter-spacing: 0.08em;
  }

  .page.et-mode .mystery-pitch-label {
    font-size: 9px !important;
    letter-spacing: 0.03em;
    line-height: 1.15;
    white-space: normal;
    max-width: 76px;
  }

  .draft-label {
    display: inline-block;
    margin-bottom: 10px;
    border: 1px solid color-mix(in srgb, var(--accent) 42%, #262a38);
    border-radius: 999px;
    padding: 4px 9px;
    color: var(--accent);
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }

  .player-card.emergency {
    border-color: #f97316;
  }

  .player-card.golden {
    border-color: rgba(201, 166, 70, 0.7);
    background:
      linear-gradient(135deg, rgba(201, 166, 70, 0.28), rgba(21, 24, 35, 0.96) 46%),
      #151823;
    box-shadow: 0 0 28px rgba(201, 166, 70, 0.14);
  }

  .player-card.golden:hover,
  .player-card.golden.selected {
    box-shadow: 0 0 0 2px rgba(201, 166, 70, 0.72), 0 0 36px rgba(201, 166, 70, 0.32);
  }

  .player-card.incompatible {
    opacity: 0.42;
  }

  .player-card.incompatible:hover,
  .player-card.incompatible.selected {
    opacity: 0.72;
  }

  .player-main {
    display: flex;
    justify-content: space-between;
  }

  .player-main strong {
    display: block;
    font-size: 19px;
  }

  .mobile-player-head {
    display: none;
  }

  .player-main small {
    display: block;
    margin-top: 5px;
    color: #8a8f9e;
  }

  .iog-line {
    margin-top: 10px;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .iog-line span {
    color: #8a8f9e;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    font-weight: 900;
  }

  .iog-line b {
    color: var(--accent);
    font-size: 26px;
  }

  .iog-line em {
    color: #f97316;
    font-style: normal;
    font-size: 12px;
    font-weight: 900;
  }

  .slot-info {
    margin-top: 10px;
    display: grid;
    gap: 4px;
  }

  .slot-info span {
    color: #8a8f9e;
    font-size: 12px;
    font-weight: 800;
  }

  .slot-info b {
    color: #f4f4f5;
    font-weight: 900;
  }

  .stats-toggle {
    display: inline-block;
    margin-top: 10px;
    border: 0;
    background: transparent;
    padding: 0;
    color: var(--accent);
    font-size: 12px;
    font-weight: 900;
    cursor: pointer;
  }

  .stats-toggle::-webkit-details-marker {
    display: none;
  }

  .stats-toggle::marker {
    content: "";
  }

  .real-stats {
    margin-top: 16px;
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 8px;
  }

  .real-stats span {
    color: #8a8f9e;
    font-size: 11px;
    font-weight: 900;
  }

  .real-stats b {
    display: block;
    margin-top: 4px;
    color: white;
    font-size: 16px;
  }

  .iog-breakdown {
    margin-top: 14px;
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
  }

  .iog-breakdown span {
    border: 1px solid #262a38;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.03);
    padding: 9px;
    color: #8f95a5;
    font-size: 10px;
    font-weight: 900;
  }

  .iog-breakdown b {
    display: block;
    margin-top: 4px;
    color: #f4f4f5;
    font-size: 15px;
  }

  .progress {
    margin-top: 24px;
    display: grid;
    grid-template-columns: repeat(11, 1fr);
    gap: 9px;
  }

  .progress div {
    height: 7px;
    border-radius: 999px;
    background: #262a38;
  }

  .progress div.active {
    background: var(--accent);
  }

  .mobile-live-balance {
    display: none;
  }

  .pitch,
  .final-pitch {
    margin-top: 24px;
    position: relative;
    height: 680px;
    border-radius: 24px;
    overflow: hidden;
    background:
      repeating-linear-gradient(
        0deg,
        #357f43 0,
        #357f43 50px,
        #45a157 50px,
        #45a157 100px
      );
    border: 1px solid #25442f;
  }

  .pitch {
    width: min(100%, 560px);
    height: 650px;
    align-self: center;
    margin-top: 22px;
  }

  .pitch::after,
  .final-pitch::after {
    content: "";
    position: absolute;
    inset: 22px;
    border: 2px solid rgba(255, 255, 255, 0.34);
    pointer-events: none;
  }

  .page.et-mode .pitch,
  .page.et-mode .final-pitch {
    background:
      repeating-linear-gradient(
        0deg,
        #0a1410 0,
        #0a1410 50px,
        #0d1b16 50px,
        #0d1b16 100px
      );
    border-color: rgba(57, 230, 201, 0.32);
  }

  .page.et-mode .pitch::after,
  .page.et-mode .final-pitch::after {
    border-color: rgba(57, 230, 201, 0.4);
    background:
      radial-gradient(circle at 50% 50%, transparent 0 27%, rgba(57, 230, 201, 0.42) 27.3% 27.6%, transparent 27.9%),
      radial-gradient(circle at 50% 50%, transparent 0 45%, rgba(57, 230, 201, 0.24) 45.3% 45.6%, transparent 45.9%),
      radial-gradient(circle at 50% 50%, transparent 0 63%, rgba(57, 230, 201, 0.14) 63.3% 63.6%, transparent 63.9%);
  }

  .page.et-mode .pitch::before,
  .page.et-mode .final-pitch::before {
    content: "";
    position: absolute;
    inset: 0;
    z-index: 1;
    pointer-events: none;
    background: linear-gradient(100deg, transparent 42%, rgba(57, 230, 201, 0.14) 50%, transparent 58%);
    background-size: 260% 100%;
    animation: scanBeamSweep 14s ease-in-out infinite alternate;
  }

  @keyframes scanBeamSweep {
    from { background-position: -100% 0; }
    to { background-position: 100% 0; }
  }

  .pitch button,
  .final-pitch > div {
    position: absolute;
    transform: translate(-50%, -50%);
    width: 96px;
    min-height: 82px;
    border-radius: 20px;
    border: 2px dashed rgba(255, 255, 255, 0.42);
    background: rgba(0, 0, 0, 0.18);
    color: white;
    display: grid;
    place-items: center;
    text-align: center;
    z-index: 2;
  }

  .pitch button {
    cursor: not-allowed;
    width: 88px;
    min-height: 74px;
    border-radius: 18px;
  }

  .pitch button.eligible {
    cursor: pointer;
    background: var(--accent);
    border-color: var(--accent);
    color: #090a0f;
    box-shadow: 0 0 0 7px color-mix(in srgb, var(--accent) 24%, transparent);
    animation: slotGlow 1.2s ease-in-out infinite alternate;
  }

  .pitch button.locked {
    opacity: 0.32;
  }

  .pitch button.selected {
    outline: 5px solid white;
  }

  .pitch button.filled,
  .final-pitch > div {
    background: #10121a;
    border: 1px solid var(--accent);
  }

  .pitch button.just-assigned,
  .mobile-squad-slots button.just-assigned,
  .mobile-slot-list button.just-assigned {
    animation: assignPulse 0.9s ease both;
  }

  .pitch button.filled.just-assigned {
    border-color: #fff1a8;
    box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent) 22%, transparent), 0 0 28px color-mix(in srgb, var(--accent) 28%, transparent);
  }

  .pitch button span,
  .final-pitch span {
    font-size: 24px;
    font-weight: 900;
  }

  .pitch button strong,
  .final-pitch small {
    background: rgba(0, 0, 0, 0.5);
    border-radius: 999px;
    padding: 4px 9px;
    font-size: 12px;
  }

  .pitch button small {
    color: var(--accent);
    font-weight: 900;
  }

  .assign-panel {
    margin-top: 18px;
    background: #151823;
    border: 1px solid #262a38;
    border-radius: 18px;
    padding: 18px;
    display: grid;
    gap: 12px;
    animation: assignPulse 0.9s ease both;
  }

  .assign-panel strong {
    font-size: 20px;
  }

  .assign-panel span,
  .assign-panel small {
    color: #8a8f9e;
  }

  .analysis-stage {
    --analysis-tone: #c9a646;
    min-height: clamp(520px, calc(100vh - 48px), 760px);
    max-width: 1420px;
    margin: 0 auto;
    position: relative;
    overflow: hidden;
    border: 1px solid #262a38;
    border-radius: 24px;
    background:
      linear-gradient(115deg, rgba(9, 10, 15, 0.98) 0%, rgba(13, 16, 25, 0.96) 52%, color-mix(in srgb, var(--analysis-tone) 12%, #0b0d14) 100%);
    box-shadow: 0 30px 90px rgba(0, 0, 0, 0.42);
    padding: 28px 44px 30px;
    display: grid;
    grid-template-rows: auto auto auto auto;
    row-gap: 18px;
    cursor: pointer;
    isolation: isolate;
    font-family: Sora, Manrope, Outfit, Inter, system-ui, sans-serif;
  }

  .analysis-stage::before {
    content: "";
    position: absolute;
    inset: 0;
    z-index: -1;
    opacity: 0.13;
    background: linear-gradient(0deg, transparent 0 66.5%, rgba(255, 255, 255, 0.14) 66.8%, transparent 67.1%);
    pointer-events: none;
  }

  .final-verdict-stage {
    --verdict-accent: #c9a646;
    min-height: calc(100vh - 120px);
    max-width: 1420px;
    margin: 0 auto;
    position: relative;
    overflow: hidden;
    border: 1px solid color-mix(in srgb, var(--verdict-accent) 32%, #262a38);
    border-radius: 26px;
    background:
      radial-gradient(circle at 72% 24%, color-mix(in srgb, var(--verdict-accent) 12%, transparent), transparent 34%),
      linear-gradient(135deg, #080a10 0%, #10131d 58%, color-mix(in srgb, var(--verdict-accent) 10%, #090b12) 100%);
    box-shadow: 0 34px 100px rgba(0, 0, 0, 0.46);
    padding: 26px 34px;
    display: grid;
    grid-template-rows: auto 1fr;
    isolation: isolate;
    animation: fadeIn 0.24s ease both;
  }

  .final-verdict-stage::before {
    content: "";
    position: absolute;
    inset: 0;
    z-index: -1;
    background:
      linear-gradient(90deg, rgba(255, 255, 255, 0.06) 1px, transparent 1px),
      linear-gradient(0deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
    background-size: 72px 72px;
    opacity: 0.12;
    mask-image: radial-gradient(circle at 55% 45%, black, transparent 72%);
  }

  .final-verdict-stage.verdict-et {
    --verdict-accent: #39e6c9;
  }

  .final-verdict-stage.verdict-invincibles {
    --verdict-accent: #8db7ff;
  }

  .final-verdict-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
  }

  .final-verdict-header img {
    width: auto;
    height: 46px;
    display: block;
  }

  .final-verdict-content {
    align-self: center;
    width: min(900px, 100%);
    margin: 0 auto;
    text-align: center;
    animation: fadeUp 0.34s ease both;
  }

  .final-verdict-content .kicker {
    margin: 0;
    color: var(--verdict-accent);
    font-size: 12px;
    font-weight: 950;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }

  .final-verdict-content h1 {
    margin: 18px 0 0;
    color: #fff;
    font-size: clamp(42px, 6vw, 82px);
    line-height: 0.95;
    letter-spacing: -0.035em;
  }

  .final-verdict-content strong {
    display: inline-flex;
    margin-top: 20px;
    border: 1px solid color-mix(in srgb, var(--verdict-accent) 38%, transparent);
    border-radius: 999px;
    background: color-mix(in srgb, var(--verdict-accent) 10%, transparent);
    color: #f8fafc;
    padding: 10px 16px;
    font-size: clamp(13px, 1.3vw, 17px);
    font-weight: 900;
    letter-spacing: 0.02em;
  }

  .final-verdict-progress {
    margin-top: 30px;
    display: flex;
    justify-content: center;
    gap: 8px;
  }

  .final-verdict-progress span {
    width: 46px;
    height: 4px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.12);
    transition: background 0.24s ease, transform 0.24s ease;
  }

  .final-verdict-progress span.active {
    background: var(--verdict-accent);
    transform: scaleY(1.25);
  }

  .analysis-click-surface {
    position: absolute;
    inset: 0;
    z-index: 0;
    width: 100%;
    height: 100%;
    border: 0;
    background: transparent;
    cursor: pointer;
  }

  .analysis-click-surface:focus-visible {
    outline: 2px solid var(--analysis-tone);
    outline-offset: -4px;
  }

  .analysis-shape { --analysis-tone: #b7c3d8; }
  .analysis-pick { --analysis-tone: #d5b95f; }
  .analysis-turn { --analysis-tone: #e1a956; }
  .analysis-pair { --analysis-tone: #d3c485; }
  .analysis-identity { --analysis-tone: #9eb7c8; }
  .analysis-balance { --analysis-tone: #bd9f64; }
  .analysis-mystery { --analysis-tone: #e0bd55; }
  .analysis-grade { --analysis-tone: #e0bd55; }

  .analysis-header,
  .analysis-footer {
    position: relative;
    z-index: 1;
    pointer-events: none;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
  }

  .analysis-header img {
    width: auto;
    height: 48px;
    display: block;
  }

  .analysis-skip,
  .analysis-continue {
    position: relative;
    z-index: 2;
    pointer-events: auto;
    border-radius: 999px;
    font: inherit;
    font-weight: 850;
    cursor: pointer;
    transition: background-color 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
  }

  .analysis-skip {
    border: 1px solid #323746;
    background: rgba(12, 14, 22, 0.72);
    color: #c7cad3;
    padding: 10px 16px;
  }

  .analysis-skip:hover {
    background: #151823;
    border-color: #555b6d;
  }

  .analysis-progress {
    position: relative;
    z-index: 1;
    pointer-events: none;
    width: 100%;
    height: 3px;
    margin-top: 0;
    overflow: hidden;
    background: #242834;
  }

  .analysis-progress span {
    display: block;
    height: 100%;
    background: var(--analysis-tone);
    transition: width 0.45s ease;
  }

  .analysis-content {
    position: relative;
    z-index: 1;
    pointer-events: none;
    min-height: 340px;
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(230px, 290px);
    align-items: center;
    gap: clamp(30px, 4vw, 64px);
  }

  .analysis-copy {
    max-width: 780px;
    animation: analysisCopyIn 0.48s ease both;
  }

  .analysis-content.mystery-report {
    min-height: 300px;
    grid-template-columns: minmax(0, 1fr) minmax(240px, 310px);
    align-items: center;
    gap: clamp(30px, 4vw, 58px);
  }

  .mystery-report .analysis-copy {
    max-width: 720px;
  }

  .mystery-report .analysis-copy h1 {
    max-width: 650px;
    font-size: clamp(32px, 3.5vw, 50px);
    line-height: 1.08;
  }

  .mystery-report .analysis-body {
    margin-top: 14px;
    font-size: 16px;
    line-height: 1.5;
  }

  .analysis-kicker {
    margin: 0 0 12px;
    color: var(--analysis-tone);
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }

  .analysis-kicker span {
    margin-left: 10px;
    color: #747b8c;
  }

  .analysis-copy h1 {
    max-width: 740px;
    margin: 0;
    color: #fff;
    font-size: clamp(42px, 5vw, 72px);
    line-height: 1.04;
    letter-spacing: 0;
    font-family: Sora, Outfit, Inter, system-ui, sans-serif;
    font-weight: 800;
  }

  .analysis-copy h1.et-phoebe-completion-message {
    max-width: 100%;
    font-size: clamp(1.25rem, 2vw, 2.25rem);
    line-height: 1.12;
    letter-spacing: -0.015em;
  }

  .analysis-body {
    max-width: 720px;
    margin: 18px 0 0;
    color: #c8ccd6;
    font-size: clamp(16px, 1.35vw, 20px);
    line-height: 1.65;
    font-family: Manrope, Outfit, Inter, system-ui, sans-serif;
  }

  .analysis-mystery-reveal {
    max-width: 650px;
    margin-top: 18px;
    animation: mysteryAnalysisReveal 0.65s ease both;
  }

  .mystery-reveal-player {
    border: 1px solid rgba(224, 189, 85, 0.5);
    border-radius: 8px;
    background: linear-gradient(120deg, rgba(224, 189, 85, 0.16), rgba(13, 16, 25, 0.9));
    padding: 18px 20px;
    box-shadow: 0 0 32px rgba(201, 166, 70, 0.15);
  }

  .mystery-reveal-player > span {
    display: block;
    color: #9da3b2;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }

  .mystery-reveal-player > strong {
    display: block;
    margin: 5px 0;
    color: #fff;
    font-size: 28px;
  }

  .mystery-reveal-player > div {
    margin-top: 14px;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
  }

  .mystery-reveal-player b {
    border: 1px solid #353a47;
    border-radius: 7px;
    padding: 9px 10px;
    color: #d9dce4;
    font-size: 13px;
  }

  .mystery-reveal-player b small {
    display: block;
    margin-bottom: 4px;
    color: #858c9c;
    font-size: 8px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }

  .mystery-impact-summary {
    max-width: 650px;
    margin-top: 16px;
  }

  .mystery-impact-summary > span {
    color: #8e94a3;
    font-size: 10px;
    font-weight: 850;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  .mystery-impact-summary > div {
    margin-top: 8px;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
  }

  .mystery-impact-summary strong {
    border-top: 1px solid rgba(224, 189, 85, 0.4);
    background: rgba(255, 255, 255, 0.025);
    padding: 10px;
    color: #e0bd55;
    font-size: 18px;
  }

  .mystery-impact-summary small {
    display: block;
    margin-top: 4px;
    color: #a5aab7;
    font-size: 9px;
    font-weight: 750;
    text-transform: uppercase;
  }

  .analysis-metric {
    max-width: 600px;
    margin-top: 22px;
    padding-top: 18px;
    border-top: 1px solid color-mix(in srgb, var(--analysis-tone) 52%, #262a38);
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 20px;
    animation: analysisMetricIn 0.55s ease 0.12s both;
  }

  .analysis-metric span {
    color: #8e94a3;
    font-size: 12px;
    font-weight: 850;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  .analysis-metric strong {
    color: var(--analysis-tone);
    font-size: clamp(24px, 3vw, 42px);
    text-align: right;
  }

  .analysis-phoebe {
    align-self: center;
    justify-self: end;
    width: min(100%, 260px);
    padding: 12px;
    border: 1px solid color-mix(in srgb, var(--analysis-tone) 48%, #262a38);
    border-radius: 8px;
    background: rgba(13, 16, 25, 0.78);
    box-shadow: 0 18px 44px rgba(0, 0, 0, 0.3);
    animation: analysisPhoebeIn 0.52s ease both;
  }

  .analysis-phoebe img {
    width: 100%;
    height: 250px;
    display: block;
    border: 0;
    border-radius: 8px;
    object-fit: cover;
    object-position: center 24%;
    filter: saturate(0.88) contrast(1.04);
  }

  .analysis-phoebe div {
    margin-top: 12px;
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 14px;
  }

  .analysis-phoebe strong {
    color: #fff;
    font-size: 18px;
  }

  .analysis-phoebe span {
    color: #8e94a3;
    font-size: 12px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .analysis-phoebe blockquote {
    position: relative;
    margin: 12px 0 0;
    border-top: 1px solid rgba(224, 189, 85, 0.24);
    padding: 13px 6px 4px;
    color: #d1d5df;
    font-size: 12px;
    line-height: 1.55;
  }

  .analysis-footer {
    padding-top: 18px;
    border-top: 1px solid #262a38;
  }

  .analysis-footer > span {
    color: #6f7584;
    font-size: 13px;
  }

  .analysis-continue {
    min-width: 150px;
    border: 1px solid color-mix(in srgb, var(--analysis-tone) 70%, #262a38);
    background: var(--analysis-tone);
    color: #090a0f;
    padding: 13px 24px;
  }

  .analysis-continue:hover {
    background: color-mix(in srgb, var(--analysis-tone) 84%, #090a0f);
    transform: translateY(-1px);
  }

  @keyframes analysisCopyIn {
    from { opacity: 0; transform: translateY(18px); }
    to { opacity: 1; transform: translateY(0); }
  }

  @keyframes analysisMetricIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  @keyframes analysisPhoebeIn {
    from { opacity: 0; transform: translateX(20px); }
    to { opacity: 1; transform: translateX(0); }
  }

  @media (max-width: 820px) {
    .analysis-stage {
      min-height: calc(100vh - 32px);
      padding: 20px 18px 22px;
    }

    .analysis-header img {
      height: 38px;
    }

    .analysis-content {
      min-height: 0;
      padding: 30px 0 26px;
      grid-template-columns: 1fr;
      align-content: center;
      gap: 24px;
    }

    .analysis-content.mystery-report {
      min-height: 0;
      grid-template-columns: 1fr;
      gap: 18px;
    }

    .mystery-report .analysis-copy h1 {
      font-size: clamp(28px, 8vw, 40px);
    }

    .mystery-reveal-player > div,
    .mystery-impact-summary > div {
      grid-template-columns: 1fr;
    }

    .analysis-copy h1 {
      font-size: clamp(34px, 10vw, 50px);
    }

    .analysis-body {
      margin-top: 18px;
      font-size: 16px;
      line-height: 1.48;
    }

    .analysis-metric {
      margin-top: 22px;
      align-items: flex-start;
    }

    .analysis-metric strong {
      max-width: 65%;
      font-size: 24px;
    }

    .analysis-phoebe {
      width: min(100%, 320px);
      display: grid;
      grid-template-columns: 72px 1fr;
      align-items: center;
      gap: 12px;
      justify-self: start;
      padding: 10px;
    }

    .analysis-phoebe img {
      width: 72px;
      height: 88px;
      border-radius: 8px;
    }

    .analysis-phoebe div {
      margin: 0;
      display: grid;
      justify-content: start;
      gap: 3px;
    }

    .analysis-phoebe strong {
      font-size: 16px;
    }

    .analysis-phoebe span {
      white-space: nowrap;
      font-size: 9px;
    }

    .analysis-phoebe blockquote {
      grid-column: 1 / -1;
      margin-top: 6px;
    }

    .analysis-footer > span {
      display: none;
    }
  }

  .play-level-stage,
  .simulation-stage {
    min-height: calc(100vh - 48px);
    max-width: 1180px;
    margin: 0 auto;
    display: grid;
    grid-template-rows: auto 1fr auto;
    border: 1px solid #262a38;
    border-radius: 24px;
    background: linear-gradient(125deg, #090a0f, #10131d 62%, #171711);
    padding: clamp(24px, 4vw, 52px);
    box-shadow: 0 30px 90px rgba(0, 0, 0, 0.42);
  }

  .play-level-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 20px;
  }

  .play-level-header h1 {
    margin: 4px 0 8px;
    color: #fff;
    font-size: clamp(34px, 5vw, 64px);
    line-height: 1;
  }

  .play-level-progress {
    height: 5px;
    margin-top: 24px;
    overflow: hidden;
    border-radius: 999px;
    background: #252936;
  }

  .play-level-progress span {
    display: block;
    height: 100%;
    background: linear-gradient(90deg, #c9a646, #f1d27a);
    transition: width 0.45s ease;
  }

  .play-level-intro,
  .play-level-card {
    align-self: center;
    border: 1px solid rgba(201, 166, 70, 0.28);
    border-radius: 26px;
    background:
      radial-gradient(circle at 80% 18%, rgba(201, 166, 70, 0.14), transparent 34%),
      rgba(15, 17, 25, 0.88);
    padding: clamp(24px, 4vw, 44px);
    box-shadow: 0 24px 70px rgba(0, 0, 0, 0.28);
    animation: fadeUp 0.42s ease both;
  }

  .play-level-intro {
    max-width: 760px;
    margin: 48px auto;
    text-align: center;
  }

  .play-level-intro span,
  .play-level-card-head span,
  .play-match-details span,
  .play-season-summary span {
    color: #c9a646;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  .play-level-intro strong {
    display: block;
    margin-top: 10px;
    color: #fff;
    font-size: clamp(34px, 6vw, 78px);
    line-height: 1;
  }

  .play-level-intro p {
    max-width: 620px;
    margin: 20px auto 28px;
    color: #cbd0dc;
    line-height: 1.65;
  }

  .play-level-card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    border-bottom: 1px solid #262a38;
    padding-bottom: 18px;
  }

  .play-level-card-head strong {
    color: #f4f4f5;
    font-size: 14px;
  }

  .play-level-main {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(230px, 320px);
    gap: clamp(24px, 5vw, 62px);
    align-items: center;
    padding-top: 28px;
  }

  .play-level-main h2 {
    margin: 0;
    color: #fff;
    font-size: clamp(32px, 5vw, 68px);
    line-height: 1.02;
  }

  .play-opponent {
    margin: 14px 0 0;
    color: #aeb4c1;
  }

  .play-opponent strong {
    color: #fff;
  }

  .play-scoreline {
    width: fit-content;
    margin: 22px 0;
    border: 1px solid rgba(201, 166, 70, 0.45);
    border-radius: 18px;
    background: rgba(201, 166, 70, 0.1);
    padding: 12px 20px;
    color: #f1d27a;
    font-size: clamp(34px, 6vw, 80px);
    font-weight: 900;
    line-height: 1;
    font-variant-numeric: tabular-nums;
  }

  .play-scoreline.record-low {
    border-color: rgba(239, 106, 106, 0.55);
    background: rgba(239, 106, 106, 0.1);
    color: #ef6a6a;
  }

  .play-scoreline.record-medium {
    border-color: rgba(228, 191, 85, 0.55);
    background: rgba(228, 191, 85, 0.1);
    color: #e4bf55;
  }

  .play-scoreline.record-high {
    border-color: rgba(98, 201, 139, 0.55);
    background: rgba(98, 201, 139, 0.1);
    color: #62c98b;
  }

  .play-level-main p {
    color: #cbd0dc;
    line-height: 1.65;
  }

  .play-match-details,
  .play-season-summary {
    display: grid;
    gap: 12px;
  }

  .play-match-details div,
  .play-season-summary div {
    border: 1px solid #262a38;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.035);
    padding: 16px;
  }

  .play-match-details strong,
  .play-season-summary strong {
    display: block;
    margin-top: 8px;
    color: #fff;
    font-size: 18px;
    line-height: 1.25;
  }

  .play-season-summary {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    margin-top: 22px;
  }

  .play-level-actions {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 12px;
    border-top: 1px solid #262a38;
    padding-top: 24px;
  }

  .simulation-header,
  .simulation-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
  }

  .simulation-header img {
    height: 44px;
    width: auto;
  }

  .simulation-header > span,
  .simulation-footer span {
    color: #858b9a;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  .simulation-content {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(250px, 330px);
    align-items: center;
    gap: clamp(36px, 7vw, 90px);
    padding: 54px 0;
  }

  .simulation-copy h1 {
    margin: 0;
    color: #fff;
    font-size: clamp(38px, 6vw, 76px);
  }

  .simulation-record {
    display: block;
    margin-top: 20px;
    font-size: clamp(54px, 9vw, 112px);
    line-height: 1;
    font-variant-numeric: tabular-nums;
    transition: color 0.45s ease;
  }

  .simulation-progress {
    max-width: 620px;
    height: 4px;
    margin-top: 28px;
    overflow: hidden;
    background: #252936;
  }

  .simulation-progress span {
    display: block;
    height: 100%;
    background: #c9a646;
    transition: width 0.12s linear;
  }

  .simulation-copy > small {
    display: block;
    margin-top: 10px;
    color: #858b9a;
  }

  .simulation-phoebe {
    border: 1px solid rgba(201, 166, 70, 0.35);
    border-radius: 20px;
    background: rgba(15, 17, 25, 0.82);
    overflow: hidden;
  }

  .simulation-phoebe img {
    width: 100%;
    height: 250px;
    display: block;
    object-fit: contain;
    object-position: bottom center;
  }

  .simulation-phoebe div {
    border-top: 1px solid #282c38;
    padding: 18px;
  }

  .simulation-phoebe span {
    color: #c9a646;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  .simulation-phoebe strong,
  .simulation-footer strong {
    display: block;
    margin-top: 7px;
    color: #fff;
    line-height: 1.5;
  }

  .simulation-footer {
    border-top: 1px solid #262a38;
    padding-top: 24px;
    animation: fadeUp 0.4s ease both;
  }

  @media (max-width: 760px) {
    .play-level-stage {
      min-height: calc(100vh - 20px);
      padding: 16px;
      border-radius: 18px;
    }

    .play-level-header {
      align-items: stretch;
      gap: 12px;
    }

    .play-level-header h1 {
      font-size: clamp(28px, 9vw, 38px);
    }

    .play-level-header .secondary {
      min-width: 104px;
      padding-inline: 12px;
      font-size: 12px;
    }

    .play-level-intro,
    .play-level-card {
      margin: 22px 0;
      padding: 18px;
      border-radius: 18px;
    }

    .play-level-intro strong {
      font-size: clamp(30px, 12vw, 52px);
    }

    .play-level-main {
      grid-template-columns: 1fr;
      gap: 18px;
    }

    .play-level-main h2 {
      font-size: clamp(28px, 10vw, 44px);
    }

    .play-scoreline {
      margin: 16px 0;
      font-size: clamp(34px, 15vw, 58px);
    }

    .play-match-details {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }

    .play-match-details div,
    .play-season-summary div {
      padding: 13px;
      border-radius: 14px;
    }

    .play-match-details strong,
    .play-season-summary strong {
      font-size: 15px;
      overflow-wrap: anywhere;
    }

    .play-season-summary {
      grid-template-columns: 1fr;
    }

    .play-level-actions {
      position: sticky;
      bottom: 8px;
      z-index: 5;
      gap: 14px;
      padding: 12px;
      border: 1px solid #262a38;
      border-radius: 16px;
      background: rgba(9, 10, 15, 0.92);
      backdrop-filter: blur(14px);
    }

    .play-level-actions .primary,
    .play-level-actions .secondary {
      flex: 1;
      min-height: 42px;
      padding: 10px;
      font-size: 12px;
    }

    .simulation-content {
      grid-template-columns: 1fr;
      padding: 38px 0;
    }

    .simulation-phoebe {
      display: grid;
      grid-template-columns: 100px 1fr;
      align-items: center;
    }

    .simulation-phoebe img {
      height: 130px;
    }

    .simulation-phoebe div {
      border-top: 0;
      border-left: 1px solid #282c38;
    }

    .simulation-footer {
      align-items: flex-end;
    }
  }

  .reveal-stage {
    animation: finalReveal 0.55s ease both;
  }

  .record-reveal-content {
    align-self: center;
    text-align: center;
    padding: 42px 0;
  }

  .record-reveal-value {
    display: block;
    font-size: clamp(76px, 14vw, 166px);
    line-height: 0.95;
    font-variant-numeric: tabular-nums;
    transition: color 0.45s ease;
    animation: outcomeReveal 0.7s ease both;
  }

  .record-reveal-content > span {
    display: block;
    margin-top: 18px;
    color: #a2a8b7;
    font-size: 18px;
    font-weight: 800;
  }

  .record-phoebe {
    max-width: 620px;
    margin: 36px auto 0;
    display: grid;
    grid-template-columns: 86px 1fr;
    align-items: center;
    border: 1px solid rgba(201, 166, 70, 0.35);
    border-radius: 12px;
    background: rgba(15, 17, 25, 0.82);
    overflow: hidden;
    text-align: left;
  }

  .record-phoebe img {
    width: 86px;
    height: 110px;
    object-fit: contain;
    object-position: bottom center;
  }

  .record-phoebe div {
    border-left: 1px solid #292d39;
    padding: 16px 20px;
  }

  .record-phoebe small {
    color: #c9a646;
    font-weight: 850;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }

  .record-phoebe strong {
    display: block;
    margin-top: 6px;
    color: #fff;
    line-height: 1.5;
  }

  .libra-reveal-content {
    align-self: center;
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(260px, 380px);
    align-items: center;
    gap: clamp(42px, 8vw, 110px);
    padding: 48px 0;
  }

  .libra-reveal-value {
    display: block;
    color: #d5b957;
    font-size: clamp(92px, 15vw, 176px);
    line-height: 0.85;
    font-variant-numeric: tabular-nums;
    animation: gradeCount 0.8s ease both;
  }

  .libra-reveal-content h1 {
    margin: 22px 0 0;
    color: #fff;
    font-size: clamp(32px, 4vw, 56px);
  }

  .libra-reveal-content p {
    max-width: 620px;
    color: #b9becb;
    line-height: 1.65;
  }

  .libra-breakdown {
    margin: 0;
    display: grid;
    gap: 10px;
  }

  .libra-breakdown div {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 20px;
    border-bottom: 1px solid #292d39;
    padding: 14px 0;
  }

  .libra-breakdown dt {
    color: #8f95a5;
  }

  .libra-breakdown dd {
    margin: 0;
    color: #fff;
    font-size: 22px;
    font-weight: 900;
    font-variant-numeric: tabular-nums;
  }

  @media (max-width: 760px) {
    .libra-reveal-content {
      grid-template-columns: 1fr;
      gap: 24px;
      padding: 34px 0;
    }

    .record-reveal-value {
      font-size: clamp(62px, 21vw, 96px);
    }
  }

  .result {
    max-width: 1320px;
    margin: 0 auto;
    animation: finalReveal 0.55s ease both;
  }

  .result-logo {
    height: 56px;
    margin-bottom: 16px;
    animation: logoFade 0.7s ease both;
  }

  .result-grid {
    margin-top: 30px;
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 24px;
  }

  .final-live-analysis {
    margin-top: 32px;
    padding-top: 28px;
    border-top: 1px solid #262a38;
  }

  .worldcup-projection-note {
    margin-top: 22px;
    border: 1px solid rgba(201, 166, 70, 0.28);
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.035);
    padding: 18px 20px;
  }

  .worldcup-projection-note span {
    color: #c9a646;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  .worldcup-projection-note p {
    margin: 8px 0 0;
    color: #d8dbe5;
    line-height: 1.55;
  }

  .mobile-scouting-report {
    display: none;
  }

  .libra-bonus {
    margin-top: 24px;
    border: 1px solid rgba(201, 166, 70, 0.48);
    border-radius: 8px;
    background: rgba(201, 166, 70, 0.08);
    padding: 20px 22px;
    display: grid;
    grid-template-columns: minmax(220px, 1.25fr) repeat(3, minmax(120px, 0.8fr));
    align-items: center;
    gap: 18px;
    animation: outcomeReveal 0.65s ease both;
  }

  .libra-bonus span,
  .libra-bonus strong {
    display: block;
  }

  .libra-bonus span {
    color: #c9a646;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 0.14em;
  }

  .libra-bonus strong {
    margin-top: 7px;
    color: #fff;
    font-size: 20px;
  }

  .libra-bonus p {
    grid-column: 1 / -1;
    max-width: 560px;
    margin: 0;
    color: #c8ccd6;
    line-height: 1.55;
  }

  @media (max-width: 720px) {
    .libra-bonus {
      display: grid;
      grid-template-columns: 1fr;
      gap: 14px;
    }
  }

  .summary {
    display: grid;
    gap: 12px;
  }

  .summary div {
    background: #151823;
    border: 1px solid #262a38;
    border-radius: 18px;
    padding: 18px;
    animation: finalReveal 0.45s ease both;
  }

  .summary span {
    display: block;
    color: #8a8f9e;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    font-weight: 900;
  }

  .summary strong {
    display: block;
    margin-top: 8px;
    font-size: 24px;
  }

  .grade-score {
    animation: gradeCount 0.8s ease both;
  }

  .outcome-card {
    animation: outcomeReveal 0.75s ease both;
  }

  .et-record-card small {
    display: block;
    margin-top: 10px;
    color: #c8ccd6;
    font-size: 14px;
    font-weight: 600;
  }

  .et-record-card strong {
    font-variant-numeric: tabular-nums;
  }

  .record-low {
    color: #ef6a6a;
  }

  .record-medium {
    color: #e4bf55;
  }

  .record-high {
    color: #62c98b;
  }

  .final-pitch {
    margin-top: 0;
    animation: finalReveal 0.7s ease 0.1s both;
  }

  .final-pitch strong {
    font-size: 12px;
    padding: 0 6px;
  }

  .invincibles-result {
    margin-top: 28px;
    display: flex;
    flex-direction: column;
    gap: 28px;
  }

  .et-match-result {
    margin-top: 28px;
    display: flex;
    flex-direction: column;
    gap: 28px;
  }

  .et-result-summary {
    border: 1px solid rgba(57, 230, 201, 0.32);
    border-radius: 24px;
    background:
      radial-gradient(circle at 12% 18%, rgba(57, 230, 201, 0.12), transparent 30%),
      linear-gradient(165deg, rgba(57, 230, 201, 0.08), #111820 58%, #07120f);
    padding: 24px;
    display: grid;
    gap: 18px;
    box-shadow: 0 22px 70px rgba(0, 0, 0, 0.32);
  }

  .et-result-summary.result-loss {
    border-color: rgba(239, 106, 106, 0.48);
    box-shadow: 0 22px 70px rgba(0, 0, 0, 0.32), 0 0 32px rgba(239, 106, 106, 0.1);
  }

  .et-result-summary.result-narrow {
    border-color: rgba(228, 191, 85, 0.5);
    box-shadow: 0 22px 70px rgba(0, 0, 0, 0.32), 0 0 32px rgba(228, 191, 85, 0.1);
  }

  .et-result-summary.result-win {
    border-color: rgba(98, 201, 139, 0.5);
    box-shadow: 0 22px 70px rgba(0, 0, 0, 0.32), 0 0 32px rgba(98, 201, 139, 0.1);
  }

  .et-result-banner {
    min-width: 0;
    border-radius: 18px;
    background: rgba(4, 12, 10, 0.58);
    padding: 24px;
  }

  .et-result-banner span,
  .et-result-stats span {
    display: block;
    color: #8fbab1;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  .et-result-banner strong {
    display: block;
    margin-top: 9px;
    color: #effffb;
    font-size: clamp(34px, 5vw, 68px);
    line-height: 0.98;
    overflow-wrap: anywhere;
  }

  .result-loss .et-result-banner strong {
    color: #ef6a6a;
  }

  .result-narrow .et-result-banner strong {
    color: #e4bf55;
  }

  .result-win .et-result-banner strong {
    color: #62c98b;
  }

  .et-result-banner p {
    max-width: 680px;
    margin: 12px 0 0;
    color: #cbd0dc;
    font-size: 15px;
    line-height: 1.45;
  }

  .et-result-stats {
    display: grid;
    grid-template-columns: repeat(3, minmax(180px, 1fr));
    gap: 12px;
  }

  .et-result-stats div {
    min-width: 0;
    border: 1px solid rgba(57, 230, 201, 0.18);
    border-radius: 16px;
    background: rgba(9, 20, 18, 0.72);
    padding: 16px;
  }

  .et-result-stats strong {
    display: block;
    margin-top: 8px;
    color: #fff;
    font-size: clamp(20px, 2.3vw, 30px);
    line-height: 1.08;
    overflow-wrap: anywhere;
  }

  .et-result-stats .et-stat-low {
    border-color: rgba(239, 106, 106, 0.42);
    background: rgba(42, 14, 17, 0.62);
  }

  .et-result-stats .et-stat-low strong {
    color: #ef6a6a;
  }

  .et-result-stats .et-stat-medium {
    border-color: rgba(228, 191, 85, 0.42);
    background: rgba(39, 31, 12, 0.58);
  }

  .et-result-stats .et-stat-medium strong {
    color: #e4bf55;
  }

  .et-result-stats .et-stat-high {
    border-color: rgba(98, 201, 139, 0.42);
    background: rgba(11, 34, 23, 0.6);
  }

  .et-result-stats .et-stat-high strong {
    color: #62c98b;
  }

  .paradox-threats {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 14px;
  }

  .paradox-threats article {
    border: 1px solid rgba(57, 230, 201, 0.22);
    border-radius: 16px;
    background:
      repeating-linear-gradient(0deg, transparent 0 10px, rgba(57, 230, 201, 0.03) 11px),
      rgba(9, 20, 18, 0.82);
    padding: 16px;
  }

  .paradox-threats span,
  .paradox-threats small {
    display: block;
    color: #8fbab1;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .paradox-threats strong {
    display: block;
    margin: 8px 0;
    color: #effffb;
    font-size: 20px;
    line-height: 1.15;
  }

  .result-hero {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 16px;
    padding: 28px;
    border: 1px solid rgba(201, 166, 70, 0.35);
    border-radius: 22px;
    background: linear-gradient(165deg, rgba(201, 166, 70, 0.1), #151823 55%);
    animation: finalReveal 0.5s ease both;
  }

  .result-hero-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .result-hero-item span {
    color: #c9a646;
    font-size: 11px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.16em;
  }

  .result-hero-item strong {
    color: #fff;
    font-size: 32px;
    font-weight: 900;
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
  }

  .result-hero-item strong.record-low,
  .stat-card strong.record-low,
  .play-match-details strong.record-low,
  .record-reveal-value.record-low,
  .simulation-record.record-low {
    color: #ef6a6a;
  }

  .result-hero-item strong.record-medium,
  .stat-card strong.record-medium,
  .play-match-details strong.record-medium,
  .record-reveal-value.record-medium,
  .simulation-record.record-medium {
    color: #e4bf55;
  }

  .result-hero-item strong.record-high,
  .stat-card strong.record-high,
  .play-match-details strong.record-high,
  .record-reveal-value.record-high,
  .simulation-record.record-high {
    color: #62c98b;
  }

  .result-hero-item strong small {
    font-size: 15px;
    font-weight: 700;
    color: #9aa0b0;
  }

  .hero-grade strong {
    color: var(--accent, #c9a646);
  }

  .hero-grade strong.record-low {
    color: #ef6a6a;
  }

  .hero-grade strong.record-medium {
    color: #e4bf55;
  }

  .hero-grade strong.record-high {
    color: #62c98b;
  }

  .result-section {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .result-section h2 {
    margin: 0;
    color: #f4f4f5;
    font-size: 20px;
    font-weight: 900;
  }

  .result-pitch-section .final-pitch {
    max-width: 640px;
    width: 100%;
    margin: 0 auto;
  }

  .stat-cards-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 14px;
  }

  .stat-card {
    background: #151823;
    border: 1px solid #262a38;
    border-radius: 16px;
    padding: 18px;
    animation: finalReveal 0.45s ease both;
  }

  .stat-card span {
    display: block;
    color: #8a8f9e;
    font-size: 11px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.14em;
  }

  .stat-card strong {
    display: block;
    margin-top: 8px;
    font-size: 22px;
    color: #fff;
  }

  .analysis-cards-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
  }

  .analysis-card {
    background: #151823;
    border: 1px solid #262a38;
    border-radius: 18px;
    padding: 22px;
  }

  .analysis-card h3 {
    margin: 0 0 14px;
    color: #c9a646;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-weight: 900;
  }

  .analysis-card dl {
    margin: 0;
    display: grid;
    gap: 12px;
  }

  .analysis-card dl div {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    border-bottom: 1px solid #20232f;
    padding-bottom: 10px;
  }

  .analysis-card dt {
    color: #8a8f9e;
    font-size: 13px;
  }

  .analysis-card dd {
    margin: 0;
    color: #fff;
    font-weight: 800;
    text-align: right;
  }

  .squad-diagnosis {
    margin-top: 16px;
    border: 1px solid rgba(201, 166, 70, 0.18);
    border-radius: 14px;
    background: rgba(201, 166, 70, 0.055);
    padding: 14px;
  }

  .squad-diagnosis span {
    display: block;
    color: #c9a646;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  .squad-diagnosis ul {
    margin: 10px 0 0;
    padding: 0;
    list-style: none;
    display: grid;
    gap: 8px;
  }

  .squad-diagnosis li {
    color: #d7dbe5;
    font-size: 13px;
    line-height: 1.35;
  }

  .squad-diagnosis li::before {
    content: "";
    display: inline-block;
    width: 6px;
    height: 6px;
    margin-right: 8px;
    border-radius: 999px;
    background: #c9a646;
    vertical-align: middle;
  }

  .analysis-card p {
    margin: 0 0 10px;
    color: #c8ccd6;
    line-height: 1.55;
  }

  .tactical-hexagon {
    margin-top: 14px;
  }

  .result-deepdive {
    border-top: 1px solid #262a38;
    padding-top: 20px;
  }

  .deepdive-buttons {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }

  .deepdive-panel {
    margin-top: 18px;
    background: #151823;
    border: 1px solid #262a38;
    border-radius: 18px;
    padding: 20px;
    animation: fadeUp 0.4s ease both;
  }

  .deepdive-panel h3 {
    margin: 0 0 14px;
    color: #f4f4f5;
    font-size: 15px;
  }

  .draft-timeline-list {
    margin: 0;
    padding: 0;
    list-style: none;
    display: grid;
    gap: 10px;
  }

  .draft-timeline-list li {
    display: grid;
    grid-template-columns: 70px 1fr auto;
    align-items: center;
    gap: 12px;
    background: #11141d;
    border: 1px solid #20232f;
    border-radius: 12px;
    padding: 10px 14px;
  }

  .draft-timeline-list span {
    color: #8a8f9e;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
  }

  .draft-timeline-list strong {
    color: #fff;
  }

  .draft-timeline-list small {
    color: #8a8f9e;
    font-size: 12px;
  }

  .draft-timeline-list em,
  .draft-timeline-list p {
    grid-column: 2 / -1;
    margin: 0;
    font-size: 12px;
    line-height: 1.45;
  }

  .draft-timeline-list em {
    color: #cbd0dc;
    font-style: normal;
  }

  .draft-timeline-list p {
    color: #f1d27a;
  }

  .footer-note {
    margin: 20px 0 0;
    color: #6f7484;
    font-size: 11px;
    line-height: 1.5;
    text-align: center;
    animation: fadeUp 0.55s ease 0.32s both;
  }

  .loading-screen {
    min-height: calc(100vh - 130px);
    display: grid;
    grid-template-rows: auto auto;
    align-content: center;
    justify-items: center;
    gap: 48px;
    place-items: center;
    text-align: center;
    perspective: 900px;
    animation: fadeIn 0.28s ease both;
  }

  .loading-screen.exiting {
    animation: loadingFadeOut 0.42s ease both;
  }

  .loading-ball {
    width: clamp(100px, 9vw, 120px);
    aspect-ratio: 1;
    position: relative;
    transform-origin: center;
    animation: footballSpin 2.6s linear infinite;
  }

  .loading-ball svg {
    display: block;
    width: 100%;
    height: 100%;
  }

  .loading-screen strong {
    display: block;
    color: #ffffff;
    font-size: 20px;
    font-weight: 500;
    letter-spacing: 2px;
  }

  .share-overlay {
    position: fixed;
    inset: 0;
    z-index: 1100;
    display: grid;
    place-items: center;
    background: rgba(4, 5, 9, 0.76);
    padding: 22px;
    backdrop-filter: blur(16px);
    animation: fadeIn 0.18s ease both;
  }

  .share-modal {
    width: min(960px, 100%);
    max-height: min(92vh, 1040px);
    overflow: auto;
    border: 1px solid rgba(201, 166, 70, 0.32);
    border-radius: 26px;
    background:
      radial-gradient(circle at 86% 10%, rgba(201, 166, 70, 0.16), transparent 26%),
      linear-gradient(155deg, #10131c, #07080d 72%);
    box-shadow: 0 34px 120px rgba(0, 0, 0, 0.62);
    padding: 24px;
  }

  .share-modal-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 18px;
    margin-bottom: 18px;
  }

  .share-modal-head span {
    color: #c9a646;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 0.16em;
    text-transform: uppercase;
  }

  .share-modal-head h2 {
    margin: 4px 0 0;
    color: #fff;
    font-size: clamp(30px, 4vw, 48px);
    line-height: 1;
  }

  .share-modal-head button {
    width: 42px;
    height: 42px;
    border: 1px solid #2a2f3d;
    border-radius: 50%;
    background: #151923;
    color: #fff;
    font-size: 24px;
    line-height: 1;
    cursor: pointer;
    transition: border-color 0.18s ease, transform 0.18s ease;
  }

  .share-modal-head button:hover {
    border-color: rgba(201, 166, 70, 0.7);
    transform: translateY(-1px);
  }

  .share-card-preview {
    position: relative;
    overflow: hidden;
    border: 1px solid #2a2f3d;
    border-radius: 22px;
    background:
      linear-gradient(165deg, rgba(255, 255, 255, 0.045), transparent 42%),
      linear-gradient(145deg, #151923, #0b0d14 76%);
    padding: clamp(16px, 3vw, 28px);
  }

  .share-card-orbit {
    position: absolute;
    right: -90px;
    top: -120px;
    width: 330px;
    height: 330px;
    border: 1px solid rgba(201, 166, 70, 0.2);
    border-radius: 50%;
    box-shadow: 0 0 0 72px rgba(255, 255, 255, 0.025);
    pointer-events: none;
  }

  .share-card-top {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: 1.4fr 0.55fr 0.7fr;
    gap: 12px;
  }

  .share-card-top div {
    min-width: 0;
    border: 1px solid #272d3c;
    border-radius: 18px;
    background: rgba(6, 8, 13, 0.58);
    padding: 18px;
  }

  .share-card-top span,
  .share-mode-badge {
    display: block;
    color: #8f95a5;
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  .share-card-top strong {
    display: block;
    margin-top: 8px;
    color: #fff;
    font-size: clamp(26px, 4vw, 44px);
    line-height: 1;
    overflow-wrap: anywhere;
  }

  .share-card-top div:nth-child(2) strong,
  .share-mode-badge {
    color: #c9a646;
  }

  .share-mode-badge {
    position: relative;
    z-index: 1;
    margin: 16px 0 14px;
    text-transform: none;
    letter-spacing: 0.06em;
  }

  .share-xi-list {
    position: relative;
    z-index: 1;
    display: grid;
    gap: 8px;
  }

  .share-xi-list div {
    display: grid;
    grid-template-columns: 54px 1fr;
    align-items: center;
    gap: 12px;
    border: 1px solid #222736;
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.035);
    padding: 10px 12px;
  }

  .share-xi-list b {
    display: grid;
    place-items: center;
    min-height: 30px;
    border-radius: 999px;
    background: #c9a646;
    color: #090a0f;
    font-size: 12px;
    font-weight: 950;
  }

  .share-xi-list strong {
    display: block;
    color: #fff;
    font-size: 15px;
    line-height: 1.15;
  }

  .share-xi-list small {
    display: block;
    margin-top: 3px;
    color: #9ba1b0;
    font-size: 12px;
    line-height: 1.25;
  }

  .share-card-brand {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-top: 12px;
    border-top: 1px solid #2a2f3d;
    padding-top: 10px;
  }

  .share-card-brand strong {
    color: #c9a646;
    font-size: 12px;
    font-weight: 950;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }

  .share-card-brand span {
    color: #8f95a5;
    font-size: 11px;
    font-weight: 750;
  }

  .share-actions {
    margin-top: 18px;
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
  }

  .share-actions button {
    min-height: 46px;
    border: 1px solid #2a2f3d;
    border-radius: 14px;
    background: #151923;
    color: #f4f4f5;
    font-weight: 850;
    cursor: pointer;
    transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
  }

  .share-actions button:hover {
    transform: translateY(-1px);
    border-color: rgba(201, 166, 70, 0.64);
    background: #1a1f2c;
  }

  .share-actions .share-download {
    grid-column: span 2;
    background: #c9a646;
    color: #090a0f;
  }

  .share-status {
    margin: 12px 0 0;
    color: #c9a646;
    font-weight: 800;
    text-align: center;
  }

  .phoebe-overlay {
    position: fixed;
    inset: 0;
    z-index: 1000;
    background: rgba(0, 0, 0, 0.45);
    pointer-events: none;
    animation: fadeIn 0.28s ease both;
  }

  .phoebe-companion {
    position: fixed;
    right: 24px;
    bottom: 24px;
    width: min(480px, calc(100vw - 32px));
    min-height: 260px;
    z-index: 1002;
    pointer-events: none;
    animation: phoebeSlideIn 0.4s ease-out both;
  }

  .phoebe-bubble {
    position: absolute;
    right: 126px;
    bottom: 132px;
    width: min(360px, calc(100vw - 164px));
    border: 1px solid rgba(201, 166, 70, 0.42);
    border-radius: 20px 20px 6px 20px;
    background: linear-gradient(145deg, rgba(16, 18, 26, 0.86), rgba(8, 10, 16, 0.92));
    box-shadow: 0 22px 58px rgba(0, 0, 0, 0.48), 0 0 26px rgba(201, 166, 70, 0.1);
    padding: 20px 22px;
    backdrop-filter: blur(14px);
    transform-origin: bottom right;
    animation: bubbleExpand 0.32s ease both;
    pointer-events: auto;
  }

  .phoebe-bubble::after {
    content: "";
    position: absolute;
    right: 18px;
    bottom: -10px;
    width: 18px;
    height: 18px;
    background: rgba(12, 14, 21, 0.94);
    border-right: 1px solid rgba(201, 166, 70, 0.42);
    border-bottom: 1px solid rgba(201, 166, 70, 0.42);
    transform: rotate(45deg);
  }

  .phoebe-bubble p {
    margin: 8px 0 0;
    color: #eef1f8;
    font-size: 14px;
    line-height: 1.55;
    font-weight: 500;
    letter-spacing: 0.01em;
  }

  .phoebe-actions {
    margin-top: 14px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .phoebe-mascot {
    position: absolute;
    right: 0;
    bottom: 0;
    width: 128px;
    height: 180px;
    border: 1px solid rgba(201, 166, 70, 0.38);
    border-radius: 28px;
    background: linear-gradient(160deg, rgba(12, 18, 31, 0.98), rgba(5, 7, 13, 0.98));
    overflow: hidden;
    box-shadow: 0 22px 60px rgba(0, 0, 0, 0.48);
    pointer-events: none;
  }

  .phoebe-mascot img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center bottom;
    display: block;
  }

  .phoebe-side-comment {
    border: 1px solid rgba(201, 166, 70, 0.36);
    background: rgba(21, 24, 35, 0.94);
    border-radius: 18px;
    padding: 18px 20px;
    animation: fadeUp 0.28s ease both;
  }

  .phoebe-side-comment {
    margin-top: 20px;
  }

  .phoebe-side-comment span {
    display: block;
    color: var(--accent);
    font-size: 11px;
    font-weight: 950;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }

  .phoebe-side-comment strong {
    display: block;
    margin-top: 7px;
    color: #f4f4f5;
    font-size: 20px;
    line-height: 1.25;
  }

  @media (max-width: 1100px) {
    .draft-grid,
    .result-grid,
    .mode-grid,
    .formation-grid {
      grid-template-columns: 1fr;
    }

    .hero-shell {
      min-height: 650px;
      padding: 36px;
    }

    .hero-content {
      grid-template-columns: minmax(0, 1fr) minmax(210px, 0.45fr);
      gap: 34px;
    }

    .hero-content h1 {
      max-width: 760px;
      font-size: clamp(54px, 9vw, 96px);
    }

    .hero-copy {
      font-size: 24px;
    }

    .hero-tagline {
      font-size: 16px;
    }

    .hero-intel-panel {
      width: min(220px, 100%);
      gap: 10px;
    }

    .hero-intel-panel span {
      padding: 9px 10px;
      font-size: 10px;
    }

    .mode-screen,
    .formation-screen {
      padding: 36px;
    }

    .mode-screen .mode-grid {
      max-width: 640px;
    }

    .universe-grid,
    .real-stats,
    .pool-tools {
      grid-template-columns: repeat(2, 1fr);
    }

    .phoebe-bubble {
      right: 112px;
      bottom: 126px;
      width: min(340px, calc(100vw - 154px));
    }

    .phoebe-mascot {
      width: 112px;
      height: 158px;
    }
  }

  @media (max-width: 720px) {
    .page {
      padding: 16px;
    }

    .nav {
      min-height: 76px;
      padding-inline: 14px;
      gap: 10px;
    }

    .nav-brand > span {
      display: none;
    }

    .nav img {
      height: 58px;
    }

    .mode-nav-icons {
      position: static;
      transform: none;
      gap: 14px;
      margin-left: auto;
    }

    .mode-nav-button {
      width: 44px;
      height: 44px;
      border-radius: 14px;
    }

    .mode-nav-icons .mode-nav-button img {
      width: 27px;
      height: 27px;
    }

    .header-iog-help {
      margin-left: 2px;
    }

    .iog-help-label {
      font-size: 11px;
      white-space: nowrap;
    }

    .hero-shell {
      min-height: min(620px, calc(100svh - 116px));
      align-items: center;
      padding: 42px 22px;
    }

    .hero-intel-panel {
      display: none;
    }

    .hero-content {
      display: block;
      text-align: left;
    }

    .hero-content h1 {
      font-size: clamp(45px, 14vw, 76px);
    }

    .entry-word {
      font-size: 40px;
    }

    .entry-prose p {
      font-size: 16px;
    }

    .menu-actions,
    .controls {
      display: grid;
    }

    .universe-grid,
    .real-stats,
    .pool-tools {
      grid-template-columns: 1fr;
    }

    .phoebe-companion {
      right: 12px;
      bottom: 12px;
    }

    .phoebe-bubble {
      right: 92px;
      bottom: 118px;
      width: min(300px, calc(100vw - 120px));
      padding: 16px 18px;
    }

    .phoebe-bubble p {
      font-size: 13px;
      line-height: 1.48;
    }

    .phoebe-mascot {
      width: 96px;
      height: 140px;
    }
  }

  @media (max-width: 768px) {
    :global(html),
    :global(body) {
      overflow-x: hidden;
    }

    .page {
      width: 100%;
      overflow-x: hidden;
      padding: 12px;
    }

    .panel {
      border-radius: 18px;
      padding: 16px;
    }

    .site-footer {
      margin-top: 14px;
      padding-inline: 8px;
      font-size: 10px;
    }

    .nav {
      min-height: 56px;
      margin-bottom: 14px;
      border-radius: 16px;
      padding: 7px 10px;
      gap: 10px;
    }

    .nav-brand {
      gap: 8px;
    }

    .nav-brand > span {
      display: none;
    }

    .nav img {
      display: block;
      height: 34px;
    }

    .nav-brand {
      min-width: 1px;
      flex: 1 1 auto;
    }

    .share-overlay {
      padding: 10px;
      align-items: start;
      overflow-y: auto;
    }

    .share-modal {
      max-height: none;
      border-radius: 18px;
      padding: 14px;
    }

    .share-modal-head h2 {
      font-size: 30px;
    }

    .share-card-preview {
      border-radius: 16px;
      padding: 14px;
    }

    .share-card-top {
      grid-template-columns: 1fr 0.62fr;
    }

    .share-card-top div:first-child {
      grid-column: 1 / -1;
    }

    .share-card-top div {
      padding: 14px;
      border-radius: 14px;
    }

    .share-card-top strong {
      font-size: 28px;
    }

    .share-xi-list {
      gap: 7px;
    }

    .share-xi-list div {
      grid-template-columns: 44px 1fr;
      gap: 9px;
      padding: 9px;
    }

    .share-xi-list b {
      min-height: 28px;
      font-size: 10px;
    }

    .share-xi-list strong {
      font-size: 13px;
    }

    .share-xi-list small {
      font-size: 11px;
    }

    .share-card-brand {
      align-items: flex-start;
      flex-direction: column;
      gap: 3px;
      padding-top: 8px;
    }

    .share-actions {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .share-actions button {
      min-height: 48px;
    }

    .share-actions .share-download {
      grid-column: 1 / -1;
    }

    .iog-help-label {
      font-size: 11px;
      white-space: nowrap;
    }

    .header-iog-help > span:not(.iog-help-label) {
      right: -4px;
      width: min(330px, calc(100vw - 24px));
      padding: 14px;
      font-size: 13px;
    }

    h1 {
      font-size: clamp(28px, 8.4vw, 40px);
      line-height: 1.02;
      letter-spacing: -0.035em;
    }

    h2 {
      font-size: clamp(20px, 6vw, 25px);
    }

    .kicker {
      font-size: 10px;
      letter-spacing: 0.16em;
    }

    .primary,
    .secondary,
    .back-link {
      min-height: 56px;
      padding: 15px 18px;
      font-size: 15px;
    }

    .main-menu {
      width: 100%;
    }

    .hero-shell {
      min-height: min(560px, calc(100svh - 96px));
      border-radius: 20px;
      padding: 34px 18px;
      align-content: center;
      justify-items: stretch;
      text-align: left;
      gap: 20px;
      background:
        radial-gradient(circle at 50% 0%, rgba(201, 166, 70, 0.12), transparent 34%),
        linear-gradient(180deg, #11141d, #090a0f);
    }

    .hero-shell::after {
      display: none;
    }

    .hero-depth {
      display: none;
    }

    .hero-content {
      max-width: 100%;
      display: block;
    }

    .hero-intel-panel {
      display: none;
    }

    .hero-system-label {
      margin-bottom: 18px;
      gap: 9px;
      font-size: 10px;
      letter-spacing: 0.12em;
    }

    .mobile-menu-logo {
      display: block;
      height: 42px;
      width: auto;
      margin: 0;
    }

    .hero-content h1 {
      margin-bottom: 0;
      font-size: clamp(43px, 14vw, 66px);
      line-height: 0.84;
    }

    .hero-copy {
      margin: 24px 0 0;
      max-width: 330px;
      font-size: clamp(20px, 6vw, 25px);
      line-height: 1.16;
    }

    .hero-tagline {
      margin-inline: 0;
      max-width: 300px;
      margin: 10px 0 22px;
      font-size: 14px;
      line-height: 1.45;
    }

    .menu-actions {
      display: grid;
      max-width: 310px;
      margin-inline: 0;
      grid-template-columns: 1fr;
      gap: 10px;
    }

    .menu-actions .primary,
    .menu-actions .about-inline-link {
      width: 100%;
      justify-content: center;
      text-align: center;
    }

    .hero-status-row {
      margin-top: 18px;
      gap: 7px;
    }

    .hero-status-row span {
      font-size: 9px;
      letter-spacing: 0.06em;
      padding: 7px 9px;
    }

    .about-card {
      margin-top: 18px;
      border-radius: 18px;
      padding: 22px 18px;
    }

    .entry-word {
      font-size: clamp(34px, 11vw, 44px);
    }

    .entry-kind {
      margin: 10px 0 16px;
      font-size: 15px;
    }

    .entry-prose {
      gap: 12px;
    }

    .entry-prose p {
      font-size: 14px;
      line-height: 1.5;
    }

    .mode-screen,
    .formation-screen {
      padding: 20px 14px;
    }

    .mode-screen h1,
    .formation-screen h1 {
      margin-top: 8px;
      font-size: clamp(30px, 9vw, 40px);
    }

    .mode-grid,
    .formation-grid {
      margin-top: 22px;
      gap: 12px;
    }

    .mode-grid {
      grid-template-columns: 1fr;
    }

    .mode-grid .mode-card {
      min-height: 0;
      padding: 8px;
      border-radius: 14px;
      position: relative;
    }

    .mode-card-image {
      display: none;
    }

    .mode-card-content {
      padding: 6px 12px 12px;
    }

    .mode-grid .mode-card .mode-card-content strong {
      font-size: 24px;
    }

    .mode-grid .mode-card .mode-card-content span {
      margin-top: 10px;
      font-size: 13px;
      line-height: 1.45;
    }

    .mode-grid .mode-card .mode-card-content .mode-badge {
      margin-top: 8px;
      font-size: 9px;
    }

    .mode-grid .mode-card::after {
      content: none;
    }

    .mode-select-label {
      margin-top: 16px !important;
      min-height: 34px;
      width: 100% !important;
    }

    .formation-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }

    .formation-grid button {
      min-height: 112px;
      border-radius: 18px;
      padding: 18px 10px;
    }

    .formation-grid span {
      font-size: 9px;
      letter-spacing: 0.12em;
    }

    .formation-grid strong {
      margin-top: 8px;
      font-size: clamp(25px, 8vw, 34px);
    }

    .draft-grid {
      width: 100%;
      gap: 14px;
    }

    .draft-grid > .panel.left {
      padding: 10px;
    }

    .draft-grid > .panel.right {
      display: none;
    }

    .draft-head,
    .board-head,
    .result-head {
      gap: 12px;
    }

    .draft-head {
      align-items: center;
      margin-bottom: 6px;
    }

    .draft-head h1 {
      margin-block: 3px 0;
      font-size: clamp(21px, 6vw, 28px);
    }

    .draft-head .kicker {
      font-size: 9px;
      letter-spacing: 0.11em;
    }

    .counter,
    .selection-pill {
      padding: 8px 12px;
      font-size: 12px;
    }

    .mobile-draft-sticky {
      position: sticky;
      top: 8px;
      z-index: 30;
      margin: 8px -4px 8px;
      display: grid;
      gap: 8px;
      border: 1px solid rgba(201, 166, 70, 0.22);
      border-radius: 14px;
      background: rgba(10, 12, 18, 0.96);
      box-shadow: 0 14px 34px rgba(0, 0, 0, 0.28);
      padding: 8px;
      backdrop-filter: blur(14px);
    }

    .mobile-pick-chips {
      margin: -2px 0 0;
      gap: 5px;
    }

    .mobile-pick-chips .pick-chip {
      padding: 3px 9px;
      font-size: 10px;
    }

    .mobile-draft-pills {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 6px;
    }

    .mobile-draft-pills span {
      min-width: 0;
      border: 1px solid rgba(201, 166, 70, 0.24);
      border-radius: 999px;
      background: rgba(201, 166, 70, 0.07);
      padding: 7px 8px;
      color: #f1f2f5;
      font-size: 10px;
      font-weight: 850;
      line-height: 1.2;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }

    .mobile-draft-pills i {
      color: #c9a646;
      font-style: normal;
      font-size: 11px;
      line-height: 1;
    }

    .live-analysis-visual {
      display: none;
    }

    .mobile-live-balance {
      display: none;
    }

    .draft-grid .universe-grid {
      display: none;
    }

    .chemistry-pill {
      padding: 8px 10px;
      font-size: 11px;
    }

    .universe-grid {
      margin: 18px 0;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }

    .universe-grid div {
      border-radius: 12px;
      padding: 12px;
    }

    .universe-grid span {
      font-size: 9px;
      letter-spacing: 0.12em;
    }

    .universe-grid strong {
      margin-top: 6px;
      font-size: 15px;
      line-height: 1.2;
    }

    .pool-tools {
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 7px;
      margin-top: 9px;
    }

    .draft-grid .controls {
      margin-top: 9px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }

    .draft-grid .controls .primary,
    .draft-grid .controls .secondary {
      min-height: 42px;
      padding: 10px 15px;
      font-size: 13px;
      flex: 1 1 0;
    }

    .status,
    .notice {
      margin-top: 10px;
      border-radius: 14px;
      padding: 12px;
    }

    .search,
    .pool-tools select {
      min-height: 44px;
      border-radius: 11px;
      padding: 9px 10px;
      font-size: 13px;
    }

    .pool-tools select {
      min-width: 0;
    }

    .pool-tools {
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    }

    .pool-tools .search {
      grid-column: 1 / -1;
    }

    .spots {
      margin: 8px 0;
      font-size: 11px;
      line-height: 1.4;
    }

    .player-list {
      max-height: min(58svh, 560px);
      gap: 6px;
      padding-right: 0;
    }

    .player-card {
      min-height: 68px;
      border-radius: 14px;
      padding: 7px 10px;
    }

    .player-card:hover {
      transform: none;
    }

    .player-card.selected {
      box-shadow: 0 0 0 1px rgba(201, 166, 70, 0.78), 0 0 18px rgba(201, 166, 70, 0.18);
    }

    .draft-label {
      display: none;
      margin-bottom: 0;
      padding: 3px 7px;
      font-size: 8px;
      letter-spacing: 0.08em;
    }

    .player-main strong {
      font-size: 17px;
      line-height: 1.18;
    }

    .desktop-player-name,
    .desktop-player-meta {
      display: none !important;
    }

    .mobile-player-head {
      display: grid;
      grid-template-columns: 46px minmax(0, 1fr) 72px;
      align-items: center;
      gap: 9px;
    }

    .mobile-player-initials {
      width: 42px;
      height: 42px;
      display: grid;
      place-items: center;
      border: 1px solid rgba(201, 166, 70, 0.35);
      border-radius: 12px;
      background: rgba(201, 166, 70, 0.09);
      color: #f4f4f5;
      font-size: 13px;
      font-weight: 950;
    }

    .mobile-player-head > div:nth-child(2) {
      min-width: 0;
    }

    .mobile-player-head strong {
      font-size: 15px;
      line-height: 1.12;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .mobile-player-head small {
      margin-top: 2px;
      color: #aeb4c2;
      font-size: 10px;
      line-height: 1.18;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .mobile-card-metrics {
      width: 72px;
      display: grid;
      justify-items: center;
      text-align: center;
      gap: 2px;
    }

    .mobile-card-metrics::before {
      content: "IoG";
      color: #8f95a5;
      font-size: 8px;
      font-weight: 950;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }

    .mobile-card-metrics b {
      color: #c9a646;
      font-size: 20px;
      line-height: 1;
      font-variant-numeric: tabular-nums;
    }

    .mobile-card-metrics span {
      color: #d7dbe5;
      font-size: 9px;
      font-weight: 850;
      line-height: 1.05;
      white-space: nowrap;
    }

    .player-main small,
    .slot-info span {
      font-size: 12px;
      line-height: 1.35;
    }

    .iog-line {
      margin-top: 0;
      gap: 8px;
    }

    .iog-line span,
    .iog-line b {
      display: none;
    }

    .iog-line b {
      font-size: 22px;
    }

    .real-stats {
      display: none;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
    }

    .slot-info,
    .stats-details,
    .iog-breakdown {
      display: none;
    }

    .real-stats b {
      font-size: 14px;
    }

    .mystery-question {
      width: 46px;
      height: 46px;
      margin-top: 12px;
      font-size: 24px;
    }

    .progress {
      display: none;
      margin-top: 16px;
      gap: 5px;
    }

    .progress div {
      height: 5px;
    }

    .pitch,
    .final-pitch {
      height: clamp(390px, 116vw, 610px);
      margin-top: 16px;
      border-radius: 16px;
    }

    .page.et-mode .pitch::before,
    .page.et-mode .final-pitch::before {
      display: none;
    }

    .et-static-noise,
    .et-ufo-two {
      display: none;
    }

    .draft-grid .pitch {
      display: none;
    }

    .mobile-squad-tracker {
      display: grid;
      gap: 6px;
    }

    .mobile-squad-slots {
      position: static;
      height: auto;
      margin-inline: auto;
      width: 100%;
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 6px;
    }

    .mobile-squad-slots button {
      position: static;
      transform: none;
      width: 100%;
      aspect-ratio: 1;
      min-height: 0;
      border: 1px solid #2d3342;
      border-radius: 50%;
      background: #151823;
      color: #f4f4f5;
      display: grid;
      place-items: center;
      align-content: center;
      gap: 2px;
      padding: 3px;
      cursor: not-allowed;
      transition: border-color 0.18s ease, background 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
    }

    .mobile-squad-slots button.eligible {
      cursor: pointer;
      border-color: #c9a646;
      box-shadow: 0 0 0 3px rgba(201, 166, 70, 0.17);
      transform: translateY(-1px);
    }

    .mobile-squad-slots button.selected {
      outline: 2px solid white;
      outline-offset: 2px;
    }

    .mobile-squad-slots button.filled {
      border-color: #c9a646;
      background: rgba(201, 166, 70, 0.14);
      cursor: default;
      animation: mobileSlotFill 0.34s ease both;
    }

    .mobile-squad-slots button.just-assigned,
    .mobile-slot-list button.just-assigned {
      border-color: #fff1a8;
      box-shadow: 0 0 0 4px rgba(201, 166, 70, 0.2), 0 0 22px rgba(201, 166, 70, 0.22);
    }

    .mobile-squad-slots button.locked {
      opacity: 0.35;
    }

    .page.et-mode .mobile-squad-slots button.eligible {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 24%, transparent);
    }

    .page.et-mode .mobile-squad-slots button.filled {
      border-color: var(--accent);
      background: color-mix(in srgb, var(--accent) 16%, transparent);
    }

    .mobile-squad-slots strong {
      font-size: clamp(9px, 2.8vw, 12px);
      line-height: 1;
    }

    .mobile-squad-slots small {
      color: #8f95a5;
      font-size: 6.5px;
      font-weight: 850;
      line-height: 1;
    }

    .mobile-assign-strip {
      display: none;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
      gap: 8px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      padding-top: 8px;
    }

    .mobile-assign-strip span {
      min-width: 0;
      color: #f4f4f5;
      font-size: 12px;
      font-weight: 850;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .mobile-assign-strip .primary {
      min-height: 48px;
      padding: 10px 14px;
      font-size: 12px;
    }

    .mobile-sheet-backdrop {
      position: fixed;
      inset: 0;
      z-index: 79;
      display: block;
      border: 0;
      background: rgba(0, 0, 0, 0.48);
      backdrop-filter: blur(2px);
      padding: 0;
    }

    .mobile-slot-sheet {
      position: fixed;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 80;
      display: block;
      border: 1px solid rgba(201, 166, 70, 0.34);
      border-bottom: 0;
      border-radius: 24px 24px 0 0;
      background: rgba(10, 12, 18, 0.97);
      box-shadow: 0 24px 70px rgba(0, 0, 0, 0.52);
      padding: 12px 14px max(16px, env(safe-area-inset-bottom));
      backdrop-filter: blur(18px);
      animation: mobileSheetIn 0.22s ease both;
      max-height: min(72svh, 520px);
      overflow-y: auto;
    }

    .mobile-slot-sheet-handle {
      width: 44px;
      height: 4px;
      margin: 0 auto 10px;
      border-radius: 999px;
      background: #3a4050;
    }

    .mobile-slot-sheet header {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
    }

    .mobile-slot-sheet header span {
      display: block;
      color: #c9a646;
      font-size: 9px;
      font-weight: 900;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }

    .mobile-slot-sheet header strong {
      display: block;
      margin-top: 3px;
      color: #fff;
      font-size: clamp(18px, 5.2vw, 22px);
      line-height: 1.15;
    }

    .mobile-slot-sheet header button {
      border: 1px solid #2d3342;
      border-radius: 14px;
      background: #151823;
      color: #f4f4f5;
      width: 40px;
      height: 40px;
      padding: 0;
      display: grid;
      place-items: center;
      font-size: 25px;
      line-height: 1;
      font-weight: 850;
    }

    .mobile-slot-sheet p {
      margin: 8px 0 12px;
      color: #b9bfcc;
      font-size: 14px;
      font-weight: 750;
      line-height: 1.35;
    }

    .mobile-slot-list {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
    }

    .mobile-slot-list button {
      min-height: 68px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 16px;
      background: rgba(21, 24, 35, 0.78);
      color: rgba(255, 255, 255, 0.46);
      padding: 8px;
      font-weight: 900;
    }

    .mobile-slot-list button.eligible {
      border-color: rgba(201, 166, 70, 0.78);
      background: rgba(201, 166, 70, 0.16);
      color: #fff;
      box-shadow: 0 0 0 3px rgba(201, 166, 70, 0.12);
    }

    .mobile-slot-list button.selected {
      outline: 2px solid #fff;
      outline-offset: 2px;
    }

    .mobile-slot-list button.filled,
    .mobile-slot-list button.unavailable {
      opacity: 0.48;
      cursor: not-allowed;
    }

    .mobile-slot-list span {
      display: block;
      margin-top: 2px;
      color: currentColor;
      font-size: 9px;
      opacity: 0.72;
    }

    .mobile-slot-warning {
      color: #ffb4a6 !important;
    }

    .pitch::after,
    .final-pitch::after {
      inset: 12px;
      border-width: 1px;
    }

    .pitch button,
    .final-pitch > div {
      width: clamp(52px, 14.5vw, 76px);
      min-height: clamp(46px, 12vw, 62px);
      border-radius: 14px;
      border-width: 1px;
    }

    .pitch button.eligible {
      box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent) 24%, transparent);
    }

    .pitch button.selected {
      outline-width: 3px;
    }

    .pitch button span,
    .final-pitch span {
      font-size: clamp(15px, 5vw, 21px);
    }

    .mystery-pitch-label {
      font-size: 9px !important;
    }

    .page.et-mode .mystery-pitch-label {
      font-size: 7.5px !important;
      max-width: 60px;
    }

    .pitch button strong,
    .final-pitch small {
      padding: 3px 6px;
      font-size: 9px;
      line-height: 1.1;
    }

    .assign-panel {
      margin-top: 12px;
      border-radius: 14px;
      padding: 13px;
    }

    .assign-panel strong {
      font-size: 17px;
    }

    .assign-panel .primary {
      width: 100%;
    }

    .analysis-stage {
      min-height: calc(100svh - 24px);
      border-radius: 18px;
      padding: 14px;
    }

    .analysis-header img {
      height: 34px;
    }

    .analysis-skip {
      padding: 8px 11px;
      font-size: 12px;
    }

    .analysis-progress {
      margin-top: 14px;
    }

    .analysis-content {
      padding: 20px 0 18px;
      gap: 14px;
    }

    .analysis-kicker {
      margin-bottom: 10px;
      font-size: 9px;
      letter-spacing: 0.12em;
    }

    .analysis-copy h1,
    .mystery-report .analysis-copy h1 {
      font-size: clamp(25px, 8vw, 36px);
      line-height: 1.1;
    }

    .analysis-body,
    .mystery-report .analysis-body {
      margin-top: 12px;
      font-size: 14px;
      line-height: 1.5;
    }

    .mystery-reveal-player {
      padding: 13px;
    }

    .mystery-reveal-player > strong {
      font-size: 22px;
    }

    .mystery-reveal-player b {
      padding: 8px;
      font-size: 12px;
    }

    .mystery-impact-summary strong {
      padding: 8px;
      font-size: 15px;
    }

    .analysis-metric {
      margin-top: 16px;
      padding-top: 14px;
      display: grid;
      gap: 8px;
    }

    .analysis-metric strong {
      max-width: 100%;
      text-align: left;
      font-size: 22px;
    }

    .analysis-phoebe {
      width: 100%;
      max-width: 300px;
      grid-template-columns: 58px 1fr;
      gap: 10px;
      padding: 8px;
    }

    .analysis-phoebe img {
      width: 58px;
      height: 72px;
    }

    .analysis-phoebe blockquote {
      font-size: 11px;
      line-height: 1.45;
    }

    .analysis-footer {
      padding-top: 14px;
    }

    .analysis-continue {
      min-width: 0;
      padding: 10px 16px;
      font-size: 13px;
    }

    .simulation-stage {
      min-height: calc(100svh - 24px);
      border-radius: 18px;
      padding: 16px;
    }

    .simulation-header img {
      height: 34px;
    }

    .simulation-header > span,
    .simulation-footer span {
      font-size: 9px;
      letter-spacing: 0.1em;
    }

    .simulation-content {
      padding: 26px 0;
      gap: 16px;
    }

    .simulation-copy h1 {
      font-size: clamp(28px, 9vw, 42px);
    }

    .simulation-record {
      margin-top: 12px;
      font-size: clamp(48px, 17vw, 78px);
    }

    .simulation-progress {
      margin-top: 18px;
    }

    .simulation-phoebe {
      grid-template-columns: 74px 1fr;
      border-radius: 14px;
    }

    .simulation-phoebe img {
      height: 96px;
    }

    .simulation-phoebe div {
      padding: 12px;
    }

    .simulation-phoebe strong {
      font-size: 13px;
      line-height: 1.4;
    }

    .simulation-footer {
      gap: 12px;
      padding-top: 14px;
    }

    .record-reveal-content {
      padding: 26px 0;
    }

    .record-reveal-value {
      font-size: clamp(54px, 20vw, 92px);
    }

    .record-reveal-content > span {
      margin-top: 10px;
      font-size: 15px;
    }

    .record-phoebe {
      margin-top: 22px;
      grid-template-columns: 64px 1fr;
    }

    .record-phoebe img {
      width: 64px;
      height: 82px;
    }

    .record-phoebe div {
      padding: 12px;
    }

    .record-phoebe strong {
      font-size: 13px;
      line-height: 1.4;
    }

    .libra-reveal-content {
      gap: 18px;
      padding: 26px 0;
    }

    .libra-reveal-value {
      font-size: clamp(66px, 23vw, 108px);
    }

    .libra-reveal-content h1 {
      margin-top: 12px;
      font-size: clamp(27px, 8vw, 38px);
    }

    .libra-reveal-content p {
      font-size: 14px;
      line-height: 1.5;
    }

    .libra-breakdown div {
      padding: 10px 0;
    }

    .libra-breakdown dd {
      font-size: 18px;
    }

    .result-head {
      display: grid;
      grid-template-columns: 1fr;
    }

    .result-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      justify-content: stretch;
    }

    .result-actions .secondary {
      width: 100%;
      justify-content: center;
    }

    .result-logo {
      height: 42px;
      margin-bottom: 10px;
    }

    .result-grid {
      margin-top: 18px;
      gap: 14px;
    }

    .summary {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }

    .summary div {
      min-width: 0;
      border-radius: 12px;
      padding: 11px;
    }

    .summary span {
      font-size: 9px;
      letter-spacing: 0.1em;
    }

    .summary strong {
      margin-top: 6px;
      font-size: clamp(15px, 4.5vw, 19px);
      line-height: 1.2;
      overflow-wrap: anywhere;
    }

    .et-record-card small {
      margin-top: 6px;
      font-size: 11px;
    }

    .final-live-analysis {
      margin-top: 18px;
      padding-top: 16px;
    }

    .mobile-scouting-report {
      margin-top: 18px;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }

    .mobile-scouting-report div,
    .mobile-scouting-report article {
      min-width: 0;
      border: 1px solid #262a38;
      border-radius: 16px;
      background: #151823;
      padding: 14px;
      animation: finalReveal 0.45s ease both;
    }

    .mobile-scouting-report article {
      grid-column: 1 / -1;
    }

    .mobile-scouting-report span {
      display: block;
      color: #8f95a5;
      font-size: 9px;
      font-weight: 900;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }

    .mobile-scouting-report strong {
      display: block;
      margin-top: 7px;
      color: #f4f4f5;
      font-size: 17px;
      line-height: 1.2;
      overflow-wrap: anywhere;
    }

    .mobile-scouting-report p {
      margin: 8px 0 0;
      color: #cbd0dc;
      font-size: 13px;
      line-height: 1.45;
    }

    .invincibles-result {
      margin-top: 18px;
      gap: 20px;
    }

    .result-hero {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      padding: 18px;
      gap: 12px;
      border-radius: 16px;
    }

    .result-hero-item strong {
      font-size: 22px;
    }

    .result-section h2 {
      font-size: 17px;
    }

    .result-pitch-section .final-pitch {
      max-width: 100%;
    }

    .stat-cards-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }

    .et-result-summary {
      padding: 16px;
      border-radius: 16px;
      gap: 12px;
    }

    .et-result-banner {
      padding: 18px;
      border-radius: 14px;
    }

    .et-result-stats {
      grid-template-columns: 1fr;
      gap: 10px;
    }

    .et-result-stats div {
      padding: 14px;
      border-radius: 12px;
    }

    .paradox-threats {
      grid-template-columns: 1fr;
      gap: 10px;
    }

    .stat-card {
      padding: 14px;
      border-radius: 12px;
    }

    .stat-card strong {
      font-size: 18px;
    }

    .analysis-cards-grid {
      grid-template-columns: 1fr;
      gap: 12px;
    }

    .analysis-card {
      padding: 14px;
      border-radius: 14px;
    }

    .tactical-hexagon {
      margin-top: 10px;
    }

    .analysis-copy h1.et-phoebe-completion-message {
      font-size: clamp(1.3rem, 6vw, 1.6rem);
      line-height: 1.16;
    }

    .deepdive-buttons {
      flex-direction: column;
    }

    .deepdive-buttons button {
      width: 100%;
      justify-content: center;
    }

    .draft-timeline-list li {
      grid-template-columns: 1fr;
      text-align: left;
      gap: 4px;
    }

    .libra-bonus {
      margin-top: 16px;
    }

    .libra-bonus {
      padding: 14px;
      border-radius: 12px;
    }

    .libra-bonus strong {
      font-size: 16px;
      line-height: 1.35;
    }

    .loading-screen {
      min-height: calc(100svh - 70px);
      gap: 30px;
    }

    .loading-ball {
      width: 92px;
    }

    .loading-screen strong {
      font-size: 18px;
    }

    .phoebe-companion {
      right: 10px;
      bottom: 10px;
      width: min(360px, calc(100vw - 20px));
      min-height: 176px;
    }

    .phoebe-bubble {
      right: 76px;
      bottom: 92px;
      width: min(284px, calc(100vw - 104px));
      border-radius: 16px 16px 5px 16px;
      padding: 12px 13px;
    }

    .phoebe-bubble p {
      font-size: 12px;
      line-height: 1.42;
    }

    .phoebe-actions {
      margin-top: 10px;
      gap: 6px;
    }

    .phoebe-actions .primary,
    .phoebe-actions .secondary {
      min-height: 34px;
      padding: 8px 10px;
      font-size: 12px;
    }

    .phoebe-mascot {
      width: 78px;
      height: 112px;
      border-radius: 20px;
    }
  }

  @media (max-width: 430px) {
    .page {
      padding: 10px;
    }

    .panel {
      padding: 13px;
    }

    .hero-shell {
      min-height: 485px;
      padding: 30px 16px 18px;
    }

    .hero-content h1 {
      font-size: clamp(38px, 13.5vw, 55px);
      line-height: 0.85;
    }

    .hero-copy {
      max-width: 280px;
      font-size: 20px;
    }

    .hero-tagline {
      margin-bottom: 18px;
    }

    .mode-screen,
    .formation-screen {
      padding: 16px 10px;
    }

    .desktop-mode-logo {
      display: none;
    }

    .challenge-grid {
      grid-template-columns: 1fr;
      gap: 12px;
      margin-top: 22px;
    }

    .challenge-grid button {
      min-height: 112px;
      padding: 18px;
      border-radius: 16px;
    }

    .challenge-grid strong {
      font-size: 16px;
    }

    .challenge-grid span {
      font-size: 12px;
      line-height: 1.45;
    }

    .mode-card-image {
      width: min(62%, 150px);
      height: 104px;
    }

    .formation-grid button {
      min-height: 80px;
    }

    .universe-grid {
      grid-template-columns: 1fr;
    }

    .player-list {
      max-height: min(58svh, 500px);
    }

    .pitch,
    .final-pitch {
      height: clamp(360px, 112vw, 490px);
    }

    .summary {
      grid-template-columns: 1fr;
    }

    .analysis-stage,
    .simulation-stage {
      border-radius: 14px;
    }

    .final-verdict-stage {
      min-height: calc(100svh - 24px);
      border-radius: 18px;
      padding: 16px;
    }

    .final-verdict-header img {
      height: 34px;
    }

    .final-verdict-content h1 {
      font-size: clamp(38px, 15vw, 58px);
      line-height: 0.98;
    }

    .final-verdict-content strong {
      padding: 9px 13px;
      font-size: 12px;
    }

    .final-verdict-progress span {
      width: 32px;
    }

    .analysis-footer,
    .simulation-footer {
      display: grid;
      grid-template-columns: 1fr;
    }

    .analysis-continue,
    .simulation-footer .primary {
      width: 100%;
    }

    .phoebe-bubble {
      right: 62px;
      width: min(260px, calc(100vw - 86px));
    }

    .phoebe-mascot {
      width: 66px;
      height: 96px;
    }
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
  }

  @keyframes heroSlideFade {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes phoebeHomeFloat {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-3px); }
  }

  @keyframes slotGlow {
    from { box-shadow: 0 0 0 6px color-mix(in srgb, var(--accent) 18%, transparent); }
    to { box-shadow: 0 0 0 10px color-mix(in srgb, var(--accent) 34%, transparent); }
  }

  @keyframes assignPulse {
    0% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--accent) 34%, transparent); }
    100% { box-shadow: 0 0 0 12px transparent; }
  }

  @keyframes mysteryFlip {
    from { transform: rotateY(-8deg) scale(0.98); opacity: 0.72; }
    to { transform: rotateY(0) scale(1); opacity: 1; }
  }

  @keyframes mysteryGoldReveal {
    0% { border-color: #262a38; box-shadow: none; }
    38% { border-color: #f0cf66; box-shadow: 0 0 0 3px rgba(240, 207, 102, 0.34), 0 0 38px rgba(201, 166, 70, 0.34); }
    100% { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(201, 166, 70, 0.42); }
  }

  @keyframes mysteryBannerIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  @keyframes mysteryAnalysisReveal {
    0% { opacity: 0; transform: translateY(12px) scale(0.98); filter: brightness(1.8); }
    55% { opacity: 1; filter: brightness(1.25); }
    100% { opacity: 1; transform: translateY(0) scale(1); filter: brightness(1); }
  }

  @keyframes mobileSlotFill {
    0% { transform: scale(0.88); box-shadow: 0 0 0 0 rgba(201, 166, 70, 0.28); }
    100% { transform: scale(1); box-shadow: 0 0 0 5px rgba(201, 166, 70, 0); }
  }

  @keyframes mobileSheetIn {
    from { opacity: 0; transform: translateY(18px); }
    to { opacity: 1; transform: translateY(0); }
  }

  @keyframes finalReveal {
    from { opacity: 0; transform: translateY(14px); }
    to { opacity: 1; transform: translateY(0); }
  }

  @keyframes gradeCount {
    from { opacity: 0; transform: scale(0.82); }
    to { opacity: 1; transform: scale(1); }
  }

  @keyframes outcomeReveal {
    from { opacity: 0; transform: translateY(10px) scale(0.98); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }

  @keyframes logoFade {
    from { opacity: 0; transform: translateY(-6px); }
    to { opacity: 1; transform: translateY(0); }
  }

  @keyframes footballSpin {
    from { transform: rotateY(0deg); }
    to { transform: rotateY(360deg); }
  }

  @keyframes loadingFadeOut {
    from { opacity: 1; }
    to { opacity: 0; }
  }

  @keyframes bubbleExpand {
    from { opacity: 0; transform: scale(0.92) translateY(16px); }
    to { opacity: 1; transform: scale(1) translateY(0); }
  }

  @keyframes phoebeSlideIn {
    from { opacity: 0; transform: translateX(72px); }
    to { opacity: 1; transform: translateX(0); }
  }

  @keyframes starFloat {
    0%, 100% { opacity: 0.35; transform: translateY(0) scale(0.8); }
    50% { opacity: 1; transform: translateY(-12px) scale(1.25); }
  }

  @media (max-width: 768px) {
    .quick-loop {
      flex-wrap: wrap;
      gap: 8px;
      font-size: 10px;
      letter-spacing: 0.06em;
    }

    .quick-loop i {
      width: 20px;
    }

    .mode-card-content em {
      font-size: 13px;
      font-weight: 500;
      line-height: 1.35;
    }

    .mode-preview {
      margin-top: 12px;
      gap: 6px;
    }

    .mode-preview span {
      padding: 6px 7px;
      font-size: 9px !important;
    }

    .pick-impact-strip {
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 8px;
      padding: 10px 11px;
      border-radius: 13px;
    }

    .pick-impact-strip p {
      grid-column: 1 / -1;
      font-size: 12px;
    }

    .bench-screen {
      padding: 24px 16px;
    }

    .bench-impact-grid {
      gap: 8px;
    }

    .bench-live-impact {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      padding: 8px;
    }

    .bench-live-impact span {
      padding: 9px;
      font-size: 9px;
    }

    .bench-live-impact span strong {
      font-size: 12px;
    }

    .bench-impact-grid article {
      border-radius: 12px;
      padding: 12px;
    }

    .bench-impact-grid strong {
      font-size: 18px;
    }

    .bench-role-grid {
      grid-template-columns: 1fr;
      gap: 8px;
    }

    .bench-phoebe {
      border-radius: 14px;
      padding: 10px;
    }

    .bench-phoebe img {
      width: 44px;
      height: 44px;
    }

    .bench-actions {
      display: grid;
      grid-template-columns: 1fr;
      gap: 8px;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .pick-chip,
    .pitch button.just-assigned,
    .mobile-squad-slots button.just-assigned,
    .mobile-slot-list button.just-assigned,
    .final-verdict-stage,
    .final-verdict-content,
    .final-verdict-progress span {
      animation: none !important;
      transition: none !important;
    }
  }
</style>
