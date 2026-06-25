<script lang="ts">
  import { onMount } from "svelte";
  import { players as rawPlayers } from "../../data/players";
  import TeamBalanceHexagon from "./TeamBalanceHexagon.svelte";
  import { calculateLibraScore } from "../../lib/squadAnalysis";
  import { calculateTeamBalance } from "../../lib/teamBalance";

  type Player = {
    id: number | string;
    name: string;
    club: string;
    league: string;
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
  type TutorialStep = 0 | 1 | 2;

  type PickedPlayer = DraftOption & {
    slotId: string;
    assignedPosition: string;
    penalty: number;
    mysteryPick?: boolean;
    goldenPick?: boolean;
    pickLabel?: string;
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

  const players = rawPlayers as Player[];
  const positionCache = new Map<string, string[]>();
  const iogCache = new Map<string, number>();
  const clubLeagueOptions: ClubLeague[] = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"];
  const supportedClubCompetitions = new Set<string>([...clubLeagueOptions, "Champions League"]);
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
  const etUniverse: Universe = { league: "ET Mode", club: "Earth", era: "All Eras", competition: "ET Mode" };

  const derivedUniverses: Universe[] = Array.from(
    new Map(
      players
        .filter((p) => p.league && p.club && p.era)
        .map((p) => [
          `${p.league}|${p.club}|${p.era}|${p.competition ?? "Draft"}`,
          { league: p.league, club: p.club, era: p.era, competition: p.competition }
        ])
    ).values()
  );

  const universes = derivedUniverses.length ? derivedUniverses : fallbackUniverses;
  const worldCupUniverses = universes.filter((item) => getUniverseCompetition(item) === "World Cup");
  const classicUniverses = universes.filter((item) => getUniverseCompetition(item) !== "World Cup");
  const universePlayerIndex = new Map<string, Player[]>();
  for (const player of players) {
    const teams = new Set([playerTeam(player), player.club, player.nation].filter(Boolean));
    for (const team of teams) {
      const key = `${player.league}|${team}|${player.era}|${getCompetition(player)}`;
      universePlayerIndex.set(key, [...(universePlayerIndex.get(key) ?? []), player]);
    }
  }

  let screen: "menu" | "loading" | "mode" | "clubFormat" | "formation" | "draft" | "analysis" | "simulation" | "record" | "libra" | "result" = "menu";
  let formation = "4-3-3";
  let draftMode: "worldcup" | "club" | "et" = "worldcup";
  let clubFormat: ClubFormat = "league";
  let selectedClubLeague: ClubLeague = "Premier League";
  let universe = worldCupUniverses[0] ?? classicUniverses[0] ?? universes[0];

  let picked: PickedPlayer[] = [];
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
  let options: DraftOption[] = [];
  let seenPlayerIds = new Set<string>();
  let rejectedPlayerIds = new Set<string>();
  let visibleOptionLimit = 80;
  let phoebeTutorialSeen = false;
  let showPhoebeTutorial = false;
  let tutorialStep: TutorialStep = 0;
  let loadingPercent = 0;
  let loadingExiting = false;
  let loadingTimer: ReturnType<typeof setInterval> | null = null;
  let analysisStepIndex = 0;
  let simulatedWins = 0;
  let simulatedDraws = 0;
  let simulatedLosses = 0;
  let simulationComplete = false;
  let simulationTimer: ReturnType<typeof setInterval> | null = null;
  const desktopHeroes = ["/hero1.png", "/hero2.png", "/hero3.png"];
  const mobileHeroes = ["/hero4.png", "/hero5.png", "/hero6.png"];
  let desktopHero = desktopHeroes[0];
  let mobileHero = mobileHeroes[0];
  let usesMobileHero = false;

  function getRandomHero(pool: string[]) {
    return pool[Math.floor(Math.random() * pool.length)];
  }

  const tutorialMessages: Record<TutorialStep, string> = {
    0: "Hey there! I'm your Galactico Draft Assistant Phoebe and I'll be assisting you through this journey. We'll select a draft mode to begin.",
    1: "World Cup 2026 is the realistic mode. You draft from qualified nations, real squads and international-style football logic. Every round gives you choices shaped by nation pools, position needs and tournament pressure. Pick carefully because balance matters more than collecting famous names.",
    2: "ET Mode is the fantasy mode. Earth is facing extraterrestrial opponents, so restrictions disappear. You are building humanity's strongest possible XI with freer picks, higher ceilings and more chaos. This is now or never: create a team powerful enough to survive beyond the planet."
  };

  onMount(() => {
    const seen = localStorage.getItem("phoebeTutorialSeen") === "true";
    phoebeTutorialSeen = seen;
    desktopHero = getRandomHero(desktopHeroes);
    mobileHero = getRandomHero(mobileHeroes);

    const heroMediaQuery = window.matchMedia("(max-width: 720px)");
    const updateHeroMode = () => {
      usesMobileHero = heroMediaQuery.matches;
    };
    updateHeroMode();
    heroMediaQuery.addEventListener("change", updateHeroMode);

    return () => {
      heroMediaQuery.removeEventListener("change", updateHeroMode);
    };
  });

  $: slots = formations[formation];
  $: pickedIds = new Set(picked.map((player) => String(player.id)));
  $: accent = clubColors[universe.club] ?? "#c9a646";
  $: emptySlots = slots.filter((slot) => !picked.some((p) => p.slotId === slot.id));
  $: openLabels = emptySlots.map((s) => s.label).join(", ");
  $: positionChoices = Array.from(new Set(options.flatMap((p) => getPositions(p)))).sort();
  $: showFeaturedPlayer = usesMobileHero && mobileHero === "/hero6.png";
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
  $: currentUniverseTitle = draftMode === "et" ? "ET Mode • Earth • Final XI" : universeTitle(universe);
  $: worldCupNations = buildWorldCupNations();
  $: hasClubUniverses = validClubUniverses().length > 0;
  $: teamIog = picked.length ? Math.round(picked.reduce((sum, p) => sum + p.adjustedIog, 0) / picked.length) : 0;
  $: avgIog = picked.length ? (picked.reduce((sum, p) => sum + p.adjustedIog, 0) / picked.length).toFixed(1) : "0.0";
  $: bestPlayer = picked.slice().sort((a, b) => b.adjustedIog - a.adjustedIog)[0];
  $: weakestPlayer = picked.slice().sort((a, b) => a.adjustedIog - b.adjustedIog)[0];
  $: captain = bestPlayer;
  $: chemistry = getChemistry(picked);
  $: positionFit = getPositionFit(picked);
  $: grade = getTeamGrade(Number(avgIog), chemistry, positionFit, weakestPlayer?.adjustedIog ?? 0);
  $: libraScore = calculateLibraScore(picked, { formation, chemistry, positionFit });
  $: finalBalanceProfile = calculateTeamBalance(picked, formation, chemistry, positionFit);
  $: baseWorldCupOutcome = getWorldCupOutcome(Number(avgIog), grade, chemistry, positionFit);
  $: libraBonusActive = draftMode === "worldcup" && (libraScore ?? 0) > 90 && baseWorldCupOutcome !== "Champion";
  $: predictedWorldCupOutcome = applyLibraBonus(baseWorldCupOutcome, libraBonusActive);
  $: predictedEtRecord = getEtLeagueRecord(picked);
  $: etPick = draftMode === "et" ? picked.find((player) => player.dataSource === "fictional_et_mode") : undefined;
  $: clubTeaserMessage = getClubTeaserMessage(predictedWorldCupOutcome);
  $: selectedLeagueMatches = leagueMatchCounts[selectedClubLeague] ?? 38;
  $: predictedClubRecord = getClubSeasonRecord(Number(avgIog), grade, selectedLeagueMatches);
  $: predictedChampionsLeagueOutcome = getChampionsLeagueOutcome(Number(avgIog), grade, chemistry, positionFit);
  $: postDraftAnalysis = buildPostDraftAnalysis(picked, formation, Number(avgIog), chemistry, positionFit, grade, draftMode);
  $: currentAnalysisStep = postDraftAnalysis[analysisStepIndex];
  $: analysisTotalSteps = postDraftAnalysis.length + 1;
  $: analysisProgress = ((analysisStepIndex + 1) / analysisTotalSteps) * 100;
  $: isGoldenRound = picked.length + 1 === goldenPickNumber && !picked.some((p) => p.goldenPick);
  $: isMysteryRound = picked.length + 1 === mysteryPickNumber && !picked.some((p) => p.mysteryPick) && !isGoldenRound;
  $: goldenRoundTitle = draftMode === "et" ? "Golden Pick • Earth • Full Player Pool" : draftMode === "worldcup" ? `Golden Pick • ${universe.club} • Full Pool` : "⭐ GOLDEN PICK";
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

  function calculatePlayerIog(player: Player) {
    const override = iogOverrides[playerNameKey(player.name)];
    if (override !== undefined) return override;

    if (player.dataSource === "fictional_et_mode") {
      return clamp(Math.round(player.iog ?? 70), 50, 99);
    }

    if (player.dataSource === "fc26") {
      return clamp(Math.round(player.iog ?? player.overall ?? 70), 50, 99);
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
        avgIog: (roster.reduce((sum, player) => sum + (player.iog ?? 0), 0) / Math.max(roster.length, 1)).toFixed(1),
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

  function activeUniverses() {
    if (draftMode === "et") return [etUniverse];
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

  function availableUniversePlayers() {
    if (draftMode === "et") return unpickedPlayers();
    const indexed = universePlayerIndex.get(universeKey(universe)) ?? [];
    return indexed.filter((player) => !isPicked(player));
  }

  function compatibleUniversePlayers() {
    return availableUniversePlayers().filter((p) => hasOpenSlot(p));
  }

  function availableModePlayers() {
    if (draftMode === "et") return unpickedPlayers();
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

  function mixedQualityOptions(pool: Player[]) {
    const ranked = sortOptions(pool.map((p) => toOption(p)), "iog_desc");
    if (ranked.length <= 5) return ranked;

    const highCut = Math.max(1, Math.ceil(ranked.length * 0.25));
    const lowStart = Math.max(highCut + 1, Math.floor(ranked.length * 0.75));
    const high = ranked.slice(0, highCut);
    const medium = ranked.slice(highCut, lowStart);
    const risky = ranked.slice(lowStart);

    let selected: DraftOption[] = [];
    selected = takeUnique(high, selected, 1);
    selected = takeUnique(medium.length ? medium : ranked, selected, 2);
    selected = takeUnique(risky.length ? risky : ranked.slice(-Math.min(6, ranked.length)), selected, 1);
    selected = takeUnique(ranked, selected, 1);

    if (selected.length < 5) selected = takeUnique(ranked, selected, 5 - selected.length);
    return sortOptions(selected.slice(0, 5), sortKey);
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
    return sortOptions(selected.slice(0, 5), sortKey);
  }

  function buildOptions() {
    fallbackNotice = "";

    if (emptySlots.length === 0) {
      startPostDraftAnalysis();
      return [];
    }

    const pool = isGoldenRound && (draftMode === "club" || draftMode === "et") ? availableModePlayers() : availableUniversePlayers();
    const compatiblePool = pool.filter((p) => hasOpenSlot(p));

    if (pool.length === 0) {
      fallbackNotice = isGoldenRound ? "No players left in this Golden Pick pool." : "No players left for this team.";
      return [];
    }

    if (isGoldenRound) {
      if (draftMode === "et") {
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

    if (isMysteryRound) {
      return draftMode === "et" ? etQualityOptions(compatiblePool) : mixedQualityOptions(compatiblePool);
    }

    return draftMode === "et" ? etQualityOptions(compatiblePool) : mixedQualityOptions(compatiblePool);
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
    markPhoebeTutorialSeen();
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
    if (tutorialStep < 2) {
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

  function phoebeResultLines(outcome: string) {
    const comments: Record<string, string[]> = {
      Champion: ["I knew you had it in you."],
      Final: ["One match away."],
      "Semi Final": ["A respectable run."],
      "Quarter Final": ["Not bad."],
      "Round of 16": ["We've seen better."],
      "Group Stage Exit": ["I have several questions.", "None of them are polite."],
      "Galactic Champions": ["Humanity survives in style."],
      "Historic Upset": ["That was not in the alien scouting report."],
      "Earth Victory": ["Earth has a team after all."],
      "Respectable Performance": ["They will remember that performance."],
      "Competitive Loss": ["Close enough to hurt."],
      "Hopeless Defeat": ["I have several questions."],
      "Extinction Event": ["I have several questions.", "None of them are polite."]
    };

    return comments[outcome] ?? [];
  }

  function resetDraftState() {
    if (simulationTimer) clearInterval(simulationTimer);
    simulationTimer = null;
    picked = [];
    selectedPlayer = null;
    selectedSlotId = "";
    options = [];
    seenPlayerIds = new Set<string>();
    rejectedPlayerIds = new Set<string>();
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
  }

  function startDraftFlow() {
    draftMode = "worldcup";
    resetDraftState();
    universe = worldCupUniverses[0] ?? universe;
    startLoading(() => {
      screen = "mode";
      if (!phoebeTutorialSeen) startPhoebeTutorial("mode");
    });
  }

  function chooseMode(mode: "club" | "worldcup" | "et") {
    draftMode = mode;
    universe = activeUniverses()[0] ?? universe;
    resetDraftState();
    screen = mode === "club" ? "clubFormat" : "formation";
  }

  function chooseTutorialMode(mode: "worldcup" | "et") {
    if (showPhoebeTutorial) return;
    chooseMode(mode);
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

  function backToMenu() {
    draftMode = "worldcup";
    clubFormat = "league";
    selectedClubLeague = "Premier League";
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
    screen = "menu";
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
      startPostDraftAnalysis();
      return;
    }

    if (manual && respinsRemaining <= 0) return;
    if (manual) respinsRemaining--;
    if (draftMode === "et" && options.length > 0) rememberRejectedOptions();

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

    let ticks = 0;

    const interval = setInterval(() => {
      universe = randomUniverse(excludeKey);
      ticks++;

      if (ticks >= 18) {
        clearInterval(interval);
        universe = findValidUniverse(excludeKey);
        options = buildSafeOptions(excludeKey);
        if (draftMode === "et") rememberShownOptions(isGoldenRound ? options.slice(0, visibleOptionLimit) : options);
        isSpinning = false;
        canPick = options.length > 0;
      }
    }, 85);
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
    const assignedPlayer = {
      ...selectedPlayer,
      slotId: slot.id,
      assignedPosition: slot.label,
      adjustedIog,
      penalty,
      mysteryPick: mysteryAssignment || isMysteryRound,
      goldenPick: isGoldenRound,
      pickLabel
    };

    if (draftMode === "et") rememberRejectedOptions(String(selectedPlayer.id));

    picked = [
      ...picked,
      assignedPlayer
    ];

    const previousUniverseKey = universeKey(universe);
    selectedPlayer = null;
    selectedSlotId = "";
    options = [];
    canPick = false;
    lastPickLabel = mysteryAssignment ? "Mystery Pick secured" : pickLabel;
    fallbackNotice = mysteryAssignment ? "Mystery Pick added to the XI. Identity remains hidden." : isGoldenRound ? `Golden Pick: ${pickLabel}` : pickLabel;

    if (picked.length >= 11) {
      startPostDraftAnalysis();
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

  function gradeValue(value: string) {
    const values: Record<string, number> = { "S+": 8, S: 6, "A+": 4, A: 2, B: 0, C: -3, D: -6 };
    return values[value] ?? 0;
  }

  function getWorldCupOutcome(avgIog: number, grade: string, chemistryScore: number, fitScore: number) {
    const outcomes = [
      "Group Stage Exit",
      "Round of 32",
      "Round of 16",
      "Quarter Final",
      "Semi Final",
      "Final",
      "Champion"
    ];

    const variance = (Math.random() - 0.5) * 12;
    const composite = avgIog * 0.78 + chemistryScore * 0.08 + fitScore * 0.07 + gradeValue(grade) + variance;

    let tier = 0;
    if (composite >= 96) tier = 6;
    else if (composite >= 91) tier = 5;
    else if (composite >= 86) tier = 4;
    else if (composite >= 80) tier = 3;
    else if (composite >= 74) tier = 2;
    else if (composite >= 68) tier = 1;

    if (avgIog >= 94 && tier < 3) tier = 3;
    if (avgIog < 74 && tier > 3) tier = 3;

    return outcomes[Math.max(0, Math.min(outcomes.length - 1, tier))];
  }

  function applyLibraBonus(outcome: string, active: boolean) {
    if (!active) return outcome;

    const advancement: Record<string, string> = {
      "Group Stage Exit": "Round of 16",
      "Round of 32": "Round of 16",
      "Round of 16": "Quarter Final",
      "Quarter Final": "Semi Final",
      "Semi Final": "Final",
      Final: "Champion",
      Champion: "Champion"
    };

    return advancement[outcome] ?? outcome;
  }

  function getEtLeagueRecord(roster: PickedPlayer[]): EtLeagueRecord {
    if (roster.length === 0) {
      return { wins: 0, draws: 0, losses: 30, record: "0-0-30", points: 0, position: "16th", goalDifference: -60 };
    }

    const squadAverage = roster.reduce((sum, player) => sum + player.adjustedIog, 0) / roster.length;
    const squadChemistry = getChemistry(roster);
    const squadFit = getPositionFit(roster);
    const squadLibra = calculateLibraScore(roster, {
      formation,
      chemistry: squadChemistry,
      positionFit: squadFit
    }) ?? Math.max(30, squadAverage - 20);
    const formationRatings: Record<string, number> = {
      "4-4-2": 88, "4-4-1-1": 87, "4-2-3-1": 90, "4-1-4-1": 86,
      "4-3-3": 89, "3-5-2": 84, "3-4-2-1": 83, "3-4-3": 81, "5-4-1": 82
    };
    const formationStrength = (formationRatings[formation] ?? 84) * 0.6 + squadFit * 0.4;
    const strength =
      squadAverage * 0.4 +
      squadLibra * 0.3 +
      squadChemistry * 0.2 +
      formationStrength * 0.1;

    let wins = Math.max(4, Math.min(28, Math.round(4 + (strength - 55) * 0.7)));
    let draws = Math.max(0, Math.min(8, Math.round(8 - Math.max(0, strength - 65) * 0.18)));
    if (wins + draws > 30) draws = Math.max(0, 30 - wins);
    const losses = 30 - wins - draws;
    const points = wins * 3 + draws;
    const goalDifference = Math.round((strength - 70) * 1.75 + wins * 0.8 - losses * 1.25);
    const position = points >= 72 ? "1st" : points >= 65 ? "2nd" : points >= 58 ? "3rd" : points >= 51 ? "4th" : points >= 44 ? "5th" : points >= 36 ? "8th" : "12th";
    const record = draws === 0 ? `${wins}-${losses}` : `${wins}-${draws}-${losses}`;

    return { wins, draws, losses, record, points, position, goalDifference };
  }

  function getClubTeaserMessage(projection: string) {
    const messages: Record<string, string> = {
      Champion: "You conquered the World Cup. Think you can do it in club football?",
      Final: "One match away from glory. Club football awaits.",
      "Semi Final": "A strong tournament run. Can you dominate a full season?",
      "Quarter Final": "A respectable finish. Club football offers another challenge.",
      "Round of 16": "Your squad had potential. Club football coming soon.",
      "Round of 32": "The tournament ended early. Club football redemption is coming.",
      "Group Stage Exit": "Maybe international football isn't your thing. Try club football soon."
    };

    return messages[projection] ?? "Club football coming soon.";
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
        if ((a.nation ?? a.club) && (a.nation ?? a.club) === (b.nation ?? b.club)) sameNationPairs += 1;
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
    if ((a.nation ?? a.club) && (a.nation ?? a.club) === (b.nation ?? b.club)) links += 8;
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

    const profiles = [
      { name: "Possession Dominant", score: midfielders * 14 + chemistryScore * 0.35 + fitScore * 0.2 },
      { name: "Vertical Counter Attack", score: attackers * 16 + Math.min(goals, 40) * 0.5 + (100 - chemistryScore) * 0.12 },
      { name: "Pressing Machine", score: (midfielders + defenders) * 8 + Math.min(defensiveActions, 140) * 0.22 + chemistryScore * 0.18 },
      { name: "Defensive Fortress", score: defenders * 17 + fitScore * 0.28 + Math.min(defensiveActions, 100) * 0.12 },
      { name: "Wide Overload", score: widePlayers * 20 + Math.min(assists, 35) * 0.6 + fitScore * 0.15 },
      { name: "Transitional Chaos", score: attackers * 12 + (100 - chemistryScore) * 0.28 + (100 - fitScore) * 0.2 }
    ];

    const identity = profiles.sort((a, b) => b.score - a.score)[0].name;
    const descriptions: Record<string, string> = {
      "Possession Dominant": `${midfielders} midfield roles and ${chemistryScore}% chemistry point toward a team that wants to control territory and dictate tempo.`,
      "Vertical Counter Attack": `${attackers} dedicated attackers and ${goals} combined recorded goals make this XI most dangerous when it attacks space quickly.`,
      "Pressing Machine": `${midfielders + defenders} players operate through the middle and defensive lines, giving this team the numbers to hunt the ball together.`,
      "Defensive Fortress": `${defenders} defenders and ${fitScore}% position fit make protection, structure and game control the clearest foundation.`,
      "Wide Overload": `${widePlayers} wide-role selections and ${assists} combined recorded assists make the flanks this team's natural route forward.`,
      "Transitional Chaos": `${attackers} attackers paired with ${chemistryScore}% chemistry creates a volatile side built to turn broken play into chances.`
    };

    return { name: identity, description: descriptions[identity] };
  }

  function buildPostDraftAnalysis(
    roster: PickedPlayer[],
    selectedFormation: string,
    averageIog: number,
    chemistryScore: number,
    fitScore: number,
    finalGrade: string,
    mode: "worldcup" | "club" | "et"
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
    if ((partnership.a.nation ?? partnership.a.club) === (partnership.b.nation ?? partnership.b.club)) partnershipLinks.push("shared national context");
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
        title: "The board is locked",
        body: `All 11 places in your ${selectedFormation} are filled. I have tracked every selection, every positional trade-off and the way your team developed from pick one to pick eleven.`,
        metricLabel: "Team IoG",
        metricValue: averageIog.toFixed(1),
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
        metricValue: earlyPick.mysteryPick ? `Pick ${earlyIndex + 1} • Identity Hidden` : `Pick ${earlyIndex + 1} • IoG ${earlyPick.adjustedIog}`,
        tone: "pick"
      },
      {
        id: "turning-point",
        kicker: "Turning Point",
        title: `${analysisName(turningPoint.player)} changed the direction`,
        body: `Pick ${turningPoint.index + 1} was the moment this draft found its level. ${turningReason}`,
        metricLabel: turningPoint.player.goldenPick ? "Golden Pick" : turningPoint.player.mysteryPick ? "Mystery Pick" : "Decision Impact",
        metricValue: turningPoint.player.mysteryPick ? "Mystery Pick • Identity Hidden" : `${normalizePosition(turningPoint.player.assignedPosition)} • IoG ${turningPoint.player.adjustedIog}`,
        tone: "turn"
      },
      {
        id: "partnership",
        kicker: "Strongest Partnership",
        title: `${analysisName(partnership.a)} + ${analysisName(partnership.b)}`,
        body: `Their combined ${((partnership.a.adjustedIog + partnership.b.adjustedIog) / 2).toFixed(1)} average IoG and ${partnershipLinks.join(", ")} make this the strongest relationship in your XI.`,
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
        body: `An average IoG of ${averageIog.toFixed(1)}, ${chemistryScore}% chemistry and ${fitScore}% position fit produced this grade. ${analysisName(weakest)} sets the floor; ${analysisName(best)} sets the ceiling.`,
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
        const fullProjection = mode === "et" ? getEtLeagueRecord(roster).points : 0;
        const reducedProjection = mode === "et"
          ? getEtLeagueRecord(reducedRoster).points
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
          metricValue: `${player.nation ?? player.club} • IoG ${player.adjustedIog}`,
          tone: "mystery",
          mysteryPlayer: player,
          mysteryImpact: {
            chemistry: chemistryImpact,
            line,
            lineRating: impact,
            projectedPoints: mode === "et" ? simulationImpact : undefined,
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
      if (draftMode === "et") startEtLeagueSimulation();
      else enterFinalReveal();
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
    if (draftMode === "et") startEtLeagueSimulation();
    else enterFinalReveal();
  }

  function etSeasonComment(wins: number) {
    if (wins < 15) return "This squad never found consistency.";
    if (wins <= 18) return "There were flashes of quality, but the margins were thin.";
    if (wins <= 23) return "This team competed every week.";
    return "This team was built to dominate.";
  }

  function libraLabel(score: number | null) {
    if (score === null) return "Building";
    if (score >= 95) return "Elite Balance";
    if (score >= 85) return "Well Balanced";
    if (score >= 70) return "Functional";
    if (score >= 50) return "Unstable";
    return "Chaotic";
  }

  function showRecordReveal() {
    screen = "record";
  }

  function showLibraReveal() {
    screen = "libra";
  }

  function startEtLeagueSimulation() {
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
    screen = "result";
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

  function restart() {
    backToMenu();
  }
</script>

<main class="page" style={`--accent:${accent}`}>
  {#if screen !== "loading" && screen !== "analysis" && screen !== "simulation" && screen !== "record" && screen !== "libra"}
    <nav class="nav">
      <div class="nav-brand">
        <img src="/logo-white.png" alt="Galactico11" />
        <span>
          {#if screen === "menu"}
            Galactico11
          {:else if screen === "mode" || screen === "formation"}
            {screen === "mode" ? "Choose mode" : "Choose formation"}
          {:else}
            {currentUniverseTitle} • {`${picked.length}/11 selected`}
          {/if}
        </span>
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
        <div class="hero-player">
          {#key desktopHero + mobileHero}
            <picture>
              <source media="(max-width: 720px)" srcset={mobileHero} />
              <img src={desktopHero} alt="Galactico11 featured footballer" />
            </picture>
          {/key}
        </div>
        <div class="hero-depth" aria-hidden="true"></div>
        <div class="hero-content">
          <h1>Galactico11</h1>
          <p class="hero-copy">Build football's ultimate eleven.</p>
          <p class="hero-tagline">Every pick has a consequence.</p>
          <div class="menu-actions">
            <button class="primary" on:click={startDraftFlow}>Start Draft</button>
            <a class="secondary" href="#about-galactico">About Galactico</a>
          </div>
        </div>

        <div class="hero-side-panels">
          {#if showFeaturedPlayer}
            <article class="featured-player-card" aria-label="Featured player Lamine Yamal">
              <p>Featured Player</p>
              <strong>Lamine Yamal</strong>
              <dl>
                <div><dt>Nation</dt><dd>Spain</dd></div>
                <div><dt>Position</dt><dd>RW</dd></div>
                <div class="featured-iog"><dt>IoG Rating</dt><dd>84</dd></div>
              </dl>
            </article>
          {/if}

          <div class="home-phoebe" aria-label="Phoebe, Draft Assistant Online">
            <img src="/phoebe.png" alt="Phoebe" />
            <span><i></i>Draft Assistant Online</span>
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
      <h1>Choose your stage.</h1>

      <div class="mode-grid">
        <button
          class="mode-card group overflow-hidden rounded-lg border border-yellow-500/30 bg-white/[0.04] text-left transition-all duration-300 hover:-translate-y-1 hover:border-yellow-400/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-yellow-400"
          class:tutorial-highlight={showPhoebeTutorial && tutorialStep === 1}
          class:tutorial-dim={showPhoebeTutorial && tutorialStep === 2}
          on:click={() => chooseTutorialMode("worldcup")}
          disabled={worldCupUniverses.length === 0}
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
            <span class="text-white/75">A realistic draft mode based on the 2026 FIFA World Cup. Build your best XI using real nations, real squads, realistic roles, and tournament-style football logic.</span>
          </div>
        </button>

        <button
          class="mode-card group overflow-hidden rounded-lg border border-yellow-500/30 bg-white/[0.04] text-left transition-all duration-300 hover:-translate-y-1 hover:border-yellow-400/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-yellow-400"
          class:tutorial-highlight={showPhoebeTutorial && tutorialStep === 2}
          class:tutorial-dim={showPhoebeTutorial && tutorialStep === 1}
          on:click={() => chooseTutorialMode("et")}
          aria-label="Choose ET Mode"
        >
          <img
            class="mode-card-image"
            src="/alien.png"
            alt="ET Mode"
          />
          <div class="mode-card-content">
            <strong class="text-white">ET Mode</strong>
            <span class="mode-badge">Fantasy</span>
            <span class="text-slate-300">A fantasy draft mode where Earth’s greatest footballers face extraterrestrial opponents. Build a galactic XI, break reality, and survive football beyond the planet.</span>
          </div>
        </button>
      </div>
    </section>
  {/if}

  {#if screen === "clubFormat"}
    <section class="panel mode-screen">
      <button class="back-link" on:click={backToMode}>Back</button>
      <h1>Choose Club Format.</h1>

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
            <h1>{isGoldenRound ? "Full Player Pool" : "Choose one player."}</h1>
          </div>

          <div class="counter">{picked.length}/11</div>
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

        {#if isSpinning}
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
                on:click={() => selectPlayer(player)}
                on:keydown={(event) => {
                  if (event.key === "Enter" || event.key === " ") selectPlayer(player);
                }}
              >
                <span class="draft-label">{draftLabel(player)}</span>
                <div class="player-main">
                  <div>
                    {#if isMysteryCardHidden(player)}
                      <strong class="mystery-unknown">Unknown Player</strong>
                      <small>Identity Hidden</small>
                      <small>Selected by Phoebe</small>
                      <div class="mystery-question" aria-hidden="true">?</div>
                    {:else}
                      <strong>{player.name}</strong>
                      <small>
                        {player.nation ?? player.club} · {getPositions(player).join(" · ")} · {player.era}
                      </small>
                      <div class="iog-line">
                        <span>IoG</span>
                        <b>{player.adjustedIog}</b>
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
      </div>

      <div class="panel right">
        <div class="board-head">
          <h2>Formation Board</h2>

          <div class="board-status">
            <div class="chemistry-pill">Chemistry <strong>{chemistry}%</strong></div>
            {#if selectedPlayer}
              <div class="selection-pill">
                {selectedPlayer.name} selected
              </div>
            {:else}
              <div class="selection-pill muted-pill">
                Select a player
              </div>
            {/if}
          </div>
        </div>

        <div class="mobile-draft-metrics" aria-label="Compact draft metrics">
          <span><b>Libra Score</b> {libraScore ?? "-"}</span>
          <span><b>Team Balance</b> {finalBalanceProfile.status}</span>
          <span><b>Chemistry</b> {chemistry}%</span>
          <span><b>Selected</b> {picked.length}/11</span>
        </div>

        <div class="pitch">
          {#each pitchSlots as slot}
            <button
              class:filled={slot.state === "filled"}
              class:eligible={slot.state === "eligible"}
              class:locked={slot.state === "locked"}
              class:selected={selectedSlotId === slot.id}
              disabled={slot.state === "filled" || slot.state === "locked"}
              style={`left:${slot.x}%; top:${slot.y}%`}
              on:click={() => clickSlot(slot)}
            >
              {#if slot.player}
                {#if isMysteryIdentityHidden(slot.player)}
                  <span class="mystery-pitch-label">MYSTERY</span>
                  <small>???</small>
                {:else}
                  <span>{initials(slot.player.name)}</span>
                  <small>IoG {slot.player.adjustedIog}</small>
                {/if}
              {:else}
                <span>+</span>
                <strong>{slot.label}</strong>
              {/if}
            </button>
          {/each}
        </div>

        <div class="live-analysis-visual">
          <TeamBalanceHexagon players={picked} {formation} {chemistry} {positionFit} />
        </div>

        {#if selectedPlayer}
          <div class="assign-panel">
            <div>
              <strong>{selectedPlayer.name}</strong>
              <span>{getPositions(selectedPlayer).join(" · ")}</span>
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
            <p class="analysis-kicker">{currentAnalysisStep.kicker} <span>{analysisStepIndex + 1} / {analysisTotalSteps}</span></p>
            <h1>{currentAnalysisStep.title}</h1>

            {#if currentAnalysisStep.mysteryPlayer && currentAnalysisStep.mysteryImpact}
              <p class="analysis-body">One selection remained hidden throughout the draft. Phoebe has completed the final identity check.</p>

              <div class="analysis-mystery-reveal" aria-live="polite">
                <div class="mystery-reveal-player">
                  <span>Identity Revealed</span>
                  <strong>{currentAnalysisStep.mysteryPlayer.name}</strong>
                  <div>
                    <b><small>Position</small>{getPositions(currentAnalysisStep.mysteryPlayer).join(", ")}</b>
                    <b><small>Nation</small>{currentAnalysisStep.mysteryPlayer.nation ?? currentAnalysisStep.mysteryPlayer.club}</b>
                    <b><small>IoG</small>{currentAnalysisStep.mysteryPlayer.adjustedIog}</b>
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
          {analysisStepIndex === postDraftAnalysis.length - 1 ? (draftMode === "et" ? "Run League Simulation" : "Reveal Final XI") : "Continue"}
        </button>
      </footer>
    </section>
  {/if}

  {#if screen === "simulation"}
    <section class="simulation-stage" aria-label="ET Mode league simulation">
      <header class="simulation-header">
        <img src="/logo-white.png" alt="Galactico11" />
        <span>League Simulation • 30 Matches</span>
      </header>

      <div class="simulation-content">
        <div class="simulation-copy">
          <p class="kicker">Draft Complete</p>
          <h1>Your record is</h1>
          <strong
            class="simulation-record"
            class:record-low={simulatedWins < 15}
            class:record-medium={simulatedWins >= 15 && simulatedWins <= 20}
            class:record-high={simulatedWins >= 21}
            aria-live="polite"
          >{simulatedWins}-{simulatedDraws}-{simulatedLosses}</strong>
          <div class="simulation-progress">
            <span style={`width:${((simulatedWins + simulatedDraws + simulatedLosses) / 30) * 100}%`}></span>
          </div>
          <small>{simulatedWins + simulatedDraws + simulatedLosses} / 30 matches</small>
        </div>

        <aside class="simulation-phoebe">
          <img src="/phoebe.png" alt="Phoebe, Draft Analyst" />
          <div>
            <span>Draft Analyst</span>
            {#if simulationComplete}
              <strong>{etSeasonComment(predictedEtRecord.wins)}</strong>
            {:else}
              <strong>We've built the squad. Now let's see how they perform across a 30 match ET season.</strong>
            {/if}
          </div>
        </aside>
      </div>

      {#if simulationComplete}
        <footer class="simulation-footer">
          <div>
            <span>Simulation Complete</span>
            <strong>All 30 matches have been processed</strong>
          </div>
          <button class="primary" on:click={showRecordReveal}>View Season Record</button>
        </footer>
      {/if}
    </section>
  {/if}

  {#if screen === "record"}
    <section class="simulation-stage reveal-stage" aria-label="ET Mode record reveal">
      <header class="simulation-header">
        <img src="/logo-white.png" alt="Galactico11" />
        <span>Season Complete • Record Reveal</span>
      </header>

      <div class="record-reveal-content">
        <p class="kicker">Your record is</p>
        <strong
          class="record-reveal-value"
          class:record-low={predictedEtRecord.wins < 15}
          class:record-medium={predictedEtRecord.wins >= 15 && predictedEtRecord.wins <= 20}
          class:record-high={predictedEtRecord.wins >= 21}
        >{predictedEtRecord.record}</strong>
        <span>{predictedEtRecord.points} / 90 pts</span>

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
          <div><dt>IoG Consistency</dt><dd>{avgIog}</dd></div>
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

  {#if screen === "result"}
    <section class="panel result">
      <div class="result-head">
        <div>
          <img class="result-logo" src="/logo-white.png" alt="Galactico11" />
          <p class="kicker">Final XI Reveal • {analysisTotalSteps} / {analysisTotalSteps}</p>
          <h1>Final team reveal.</h1>
          <p class="muted">Your XI is complete.</p>
        </div>

        <button class="secondary" on:click={restart}>Play Again</button>
      </div>

      <div class="result-grid">
        <aside class="summary">
          {#if draftMode === "et"}
            <div class="outcome-card et-record-card">
              <span>Record</span>
              <small>Your record is</small>
              <strong
                class:record-low={predictedEtRecord.wins < 15}
                class:record-medium={predictedEtRecord.wins >= 15 && predictedEtRecord.wins <= 20}
                class:record-high={predictedEtRecord.wins >= 21}
              >{predictedEtRecord.record}</strong>
            </div>
            <div class="outcome-card"><span>Points</span><strong>{predictedEtRecord.points} / 90 pts</strong></div>
            {#if etPick}
              <div class="outcome-card"><span>ET Pick</span><strong>{etPick.name}</strong></div>
            {/if}
            {#if bestPlayer}
              <div><span>Best Player</span><strong>{bestPlayer.name}</strong></div>
            {/if}
            {#if weakestPlayer}
              <div><span>Weakest Player</span><strong>{weakestPlayer.name}</strong></div>
            {/if}
          {:else}
            <div><span>Formation</span><strong>{formation}</strong></div>
            <div><span>Overall Team IoG</span><strong>{avgIog}</strong></div>
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
          {/if}
        </aside>

        <div class="final-pitch">
          {#each pitchSlots as slot}
            <div style={`left:${slot.x}%; top:${slot.y}%`}>
              {#if slot.player}
                <span>{initials(slot.player.name)}</span>
                <small>IoG {slot.player.adjustedIog}</small>
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

      {#if libraBonusActive}
        <section class="libra-bonus" aria-label="Libra tournament advancement bonus">
          <div>
            <span>LIBRA BONUS ACTIVATED</span>
            <strong>{baseWorldCupOutcome} → {predictedWorldCupOutcome}</strong>
          </div>
          <p>Phoebe: Your squad's balance elevated its tournament performance beyond the expected result.</p>
        </section>
      {/if}

      {#if draftMode === "worldcup" && phoebeResultLines(predictedWorldCupOutcome).length > 0}
        <div class="phoebe-result-comment" aria-live="polite">
          <span>Phoebe</span>
          {#each phoebeResultLines(predictedWorldCupOutcome) as line}
            <strong>{line}</strong>
          {/each}
        </div>
      {/if}

      {#if draftMode === "worldcup"}
        <div class="club-teaser-flow" aria-label="Club Football coming soon">
          <p class="club-teaser-message">{clubTeaserMessage}</p>

          <section class="club-teaser-card">
            <div class="teaser-divider"></div>
            <p class="teaser-kicker">Coming Soon</p>
            <h2>🏟 Club Football</h2>
            <p class="muted">Draft across:</p>

            <ul class="competition-list">
              <li>Premier League</li>
              <li>La Liga</li>
              <li>Serie A</li>
              <li>Bundesliga</li>
              <li>Ligue 1</li>
              <li>UEFA Champions League</li>
            </ul>

            <div class="teaser-features">
              <span>100+ Club Universes</span>
              <span>3000+ Players</span>
              <span>League Simulations</span>
              <span>Champions League Campaigns</span>
            </div>
            <div class="teaser-divider"></div>
          </section>

        </div>
      {/if}

      <p class="footer-note">Note: The statistics shown are limited to 2 seasons before and after 2026.</p>
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

  :global(body) {
    margin: 0;
    background: #090a0f;
  }

  .page {
    min-height: 100vh;
    background: #090a0f;
    color: #f4f4f5;
    font-family: Inter, system-ui, sans-serif;
    padding: 24px;
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
    background: #10121a;
    padding: 12px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    position: relative;
    z-index: 40;
  }

  .nav-brand {
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 14px;
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
    min-height: 680px;
    position: relative;
    overflow: hidden;
    border-radius: 30px;
    border: 1px solid #262a38;
    background: #10121a;
    display: grid;
    align-items: center;
    padding: 82px;
    box-shadow: 0 28px 90px rgba(0, 0, 0, 0.32);
  }

  .hero-shell::before {
    content: "";
    position: absolute;
    inset: 0;
    z-index: 0;
    background:
      linear-gradient(112deg, transparent 8%, rgba(255, 255, 255, 0.035) 28%, transparent 43%),
      linear-gradient(72deg, transparent 52%, rgba(201, 166, 70, 0.035) 70%, transparent 84%),
      linear-gradient(180deg, #0d111b 0%, #090a0f 70%);
    pointer-events: none;
  }

  .hero-player {
    position: absolute;
    inset: 0;
    z-index: 1;
    overflow: hidden;
    background: #08090d;
  }

  .hero-player picture {
    display: block;
    width: 100%;
    height: 100%;
    animation: heroSlideFade 0.55s ease both;
  }

  .hero-player img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center;
    opacity: 0.82;
    transition: opacity 0.45s ease, filter 0.45s ease;
  }

  @media (min-width: 721px) {
    .hero-player picture {
      display: flex;
      align-items: center;
      justify-content: flex-end;
    }

    .hero-player img {
      object-fit: contain;
      object-position: right center;
      height: 90%;
      opacity: 0.7;
      filter: saturate(0.9);
      transform: none;
    }
  }

  .hero-shell:hover .hero-player img {
    opacity: 0.85;
    filter: saturate(1.03);
  }

  @media (min-width: 721px) {
    .hero-shell:hover .hero-player img {
      opacity: 0.74;
      filter: saturate(0.95);
    }
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
      radial-gradient(circle at 66% 25%, transparent 0, rgba(0, 0, 0, 0.12) 48%, rgba(0, 0, 0, 0.62) 100%),
      linear-gradient(90deg, rgba(9, 10, 15, 0.97) 0%, rgba(9, 10, 15, 0.9) 28%, rgba(9, 10, 15, 0.54) 54%, rgba(9, 10, 15, 0.34) 76%, rgba(9, 10, 15, 0.48) 100%);
    z-index: 3;
    pointer-events: none;
  }

  .hero-content {
    position: relative;
    z-index: 4;
    max-width: 620px;
    animation: fadeUp 0.6s ease both;
  }

  .hero-content h1 {
    margin-bottom: 18px;
    font-size: 82px;
    line-height: 0.88;
  }

  .hero-copy {
    max-width: 560px;
    margin: 0;
    color: #f4f4f5;
    font-size: 30px;
    line-height: 1.12;
    font-weight: 900;
  }

  .hero-tagline {
    margin: 16px 0 34px;
    color: #c5cad8;
    font-size: 18px;
    line-height: 1.5;
  }

  .menu-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }

  .menu-actions a.secondary {
    display: inline-flex;
    align-items: center;
    text-decoration: none;
  }

  .hero-side-panels {
    position: absolute;
    right: 28px;
    bottom: 28px;
    z-index: 4;
    width: 270px;
    display: grid;
    justify-items: end;
    gap: 12px;
  }

  .featured-player-card {
    width: 100%;
    border: 1px solid rgba(201, 166, 70, 0.38);
    border-radius: 8px;
    background: rgba(8, 10, 16, 0.86);
    box-shadow: 0 18px 46px rgba(0, 0, 0, 0.34);
    padding: 18px;
    backdrop-filter: blur(14px);
    transition: transform 0.25s ease, border-color 0.25s ease, background 0.25s ease;
  }

  .featured-player-card:hover {
    transform: translateY(-3px);
    border-color: rgba(201, 166, 70, 0.64);
    background: rgba(12, 15, 23, 0.92);
  }

  .featured-player-card > p {
    margin: 0;
    color: var(--accent);
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 0.2em;
    text-transform: uppercase;
  }

  .featured-player-card > strong {
    display: block;
    margin-top: 8px;
    color: #ffffff;
    font-size: 22px;
    line-height: 1.1;
  }

  .featured-player-card dl {
    margin: 16px 0 0;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
  }

  .featured-player-card dl div {
    min-width: 0;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 9px;
  }

  .featured-player-card dt,
  .featured-player-card dd {
    margin: 0;
  }

  .featured-player-card dt {
    color: #7f8594;
    font-size: 9px;
    font-weight: 800;
    text-transform: uppercase;
  }

  .featured-player-card dd {
    margin-top: 4px;
    color: #e7e9ef;
    font-size: 13px;
    font-weight: 800;
  }

  .featured-player-card .featured-iog dd {
    color: var(--accent);
    font-size: 17px;
  }

  .home-phoebe {
    min-height: 58px;
    display: flex;
    align-items: center;
    gap: 10px;
    border: 1px solid rgba(201, 166, 70, 0.24);
    border-radius: 8px;
    background: rgba(8, 10, 16, 0.78);
    padding: 7px 12px 7px 7px;
    backdrop-filter: blur(12px);
    animation: phoebeHomeFloat 4.8s ease-in-out infinite;
  }

  .home-phoebe img {
    width: 44px;
    height: 44px;
    border: 1px solid rgba(201, 166, 70, 0.4);
    border-radius: 50%;
    object-fit: cover;
    object-position: center 24%;
  }

  .home-phoebe span {
    display: flex;
    align-items: center;
    gap: 7px;
    color: #c5cad8;
    font-size: 11px;
    font-weight: 800;
    white-space: nowrap;
  }

  .home-phoebe i {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #63b784;
    box-shadow: 0 0 0 3px rgba(99, 183, 132, 0.12);
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
    max-width: 1100px;
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

  .mode-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 32px;
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

  .mode-option {
    min-height: 270px;
    border: 1px solid #262a38;
    background: #151823;
    color: white;
    border-radius: 20px;
    padding: 34px;
    text-align: left;
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

  .mobile-draft-metrics {
    display: none;
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

  .controls {
    display: flex;
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
    background: var(--accent);
    color: #090a0f;
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
    margin-top: 20px;
    background: #151823;
    border: 1px solid #262a38;
    border-radius: 18px;
    padding: 22px;
    text-align: center;
  }

  .notice {
    color: var(--accent);
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
    margin-top: 22px;
    display: grid;
    grid-template-columns: 1fr 170px 170px;
    gap: 10px;
  }

  .search,
  .pool-tools select {
    width: 100%;
    border: 1px solid #262a38;
    background: #151823;
    color: white;
    border-radius: 16px;
    padding: 15px 18px;
    font-size: 16px;
  }

  .pool-tools select {
    cursor: pointer;
  }

  .spots {
    margin: 16px 0;
  }

  .player-list {
    max-height: 560px;
    overflow-y: auto;
    padding-right: 6px;
    display: grid;
    gap: 12px;
  }

  .load-more-options {
    width: 100%;
    margin-top: 14px;
  }

  .player-card {
    border: 1px solid #262a38;
    background: #151823;
    color: white;
    border-radius: 18px;
    padding: 18px;
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
    font-size: 20px;
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
    min-height: calc(100vh - 48px);
    max-width: 1420px;
    margin: 0 auto;
    position: relative;
    overflow: hidden;
    border: 1px solid #262a38;
    border-radius: 24px;
    background:
      linear-gradient(115deg, rgba(9, 10, 15, 0.98) 0%, rgba(13, 16, 25, 0.96) 52%, color-mix(in srgb, var(--analysis-tone) 12%, #0b0d14) 100%);
    box-shadow: 0 30px 90px rgba(0, 0, 0, 0.42);
    padding: 32px 50px 38px;
    display: grid;
    grid-template-rows: auto auto 1fr auto;
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
    margin-top: 26px;
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
    min-height: 460px;
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(230px, 290px);
    align-items: center;
    gap: clamp(46px, 6vw, 90px);
  }

  .analysis-copy {
    max-width: 780px;
    animation: analysisCopyIn 0.48s ease both;
  }

  .analysis-content.mystery-report {
    min-height: 390px;
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
    margin: 0 0 18px;
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

  .analysis-body {
    max-width: 720px;
    margin: 24px 0 0;
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
    margin-top: 30px;
    padding-top: 22px;
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
    width: min(100%, 280px);
    padding: 12px;
    border: 1px solid color-mix(in srgb, var(--analysis-tone) 48%, #262a38);
    border-radius: 8px;
    background: rgba(13, 16, 25, 0.78);
    box-shadow: 0 18px 44px rgba(0, 0, 0, 0.3);
    animation: analysisPhoebeIn 0.52s ease both;
  }

  .analysis-phoebe img {
    width: 100%;
    height: 300px;
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
    padding-top: 24px;
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

  .libra-bonus {
    margin-top: 24px;
    border: 1px solid rgba(201, 166, 70, 0.48);
    border-radius: 8px;
    background: rgba(201, 166, 70, 0.08);
    padding: 20px 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 28px;
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
    max-width: 560px;
    margin: 0;
    color: #c8ccd6;
    line-height: 1.55;
  }

  @media (max-width: 720px) {
    .libra-bonus {
      display: grid;
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

  .club-teaser-flow {
    margin-top: 28px;
    display: grid;
    gap: 18px;
  }

  .club-teaser-message,
  .club-teaser-card {
    border: 1px solid #262a38;
    background: #151823;
    border-radius: 20px;
    animation: fadeUp 0.55s ease both;
  }

  .club-teaser-message {
    margin: 0;
    padding: 22px 24px;
    color: #f4f4f5;
    font-size: 22px;
    font-weight: 900;
    animation-delay: 0.12s;
  }

  .club-teaser-card {
    padding: 28px;
    animation-delay: 0.22s;
  }

  .teaser-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(201, 166, 70, 0.75), transparent);
  }

  .teaser-kicker {
    margin: 24px 0 8px;
    color: var(--accent);
    font-size: 12px;
    font-weight: 950;
    letter-spacing: 0.28em;
    text-transform: uppercase;
  }

  .club-teaser-card h2 {
    margin: 0;
    color: white;
    letter-spacing: 0;
  }

  .competition-list {
    margin: 18px 0 0;
    padding: 0;
    list-style: none;
    display: grid;
    gap: 10px;
  }

  .competition-list li {
    color: #c5cad8;
    font-weight: 800;
  }

  .competition-list li::before {
    content: "•";
    color: var(--accent);
    margin-right: 10px;
  }

  .teaser-features {
    margin: 24px 0;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
  }

  .teaser-features span {
    border: 1px solid rgba(201, 166, 70, 0.28);
    border-radius: 14px;
    padding: 14px;
    color: #f4f4f5;
    font-size: 13px;
    font-weight: 900;
    text-align: center;
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

  .phoebe-side-comment,
  .phoebe-result-comment {
    border: 1px solid rgba(201, 166, 70, 0.36);
    background: rgba(21, 24, 35, 0.94);
    border-radius: 18px;
    padding: 18px 20px;
    animation: fadeUp 0.28s ease both;
  }

  .phoebe-side-comment {
    margin-top: 20px;
  }

  .phoebe-result-comment {
    margin-top: 24px;
    animation-delay: 0.08s;
  }

  .phoebe-side-comment span,
  .phoebe-result-comment span {
    display: block;
    color: var(--accent);
    font-size: 11px;
    font-weight: 950;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }

  .phoebe-side-comment strong,
  .phoebe-result-comment strong {
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

    .hero-side-panels {
      right: 20px;
      bottom: 20px;
      width: 240px;
    }

    .hero-content h1 {
      font-size: 48px;
    }

    .hero-copy {
      font-size: 24px;
    }

    .hero-tagline {
      font-size: 16px;
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
    .pool-tools,
    .teaser-features {
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
    }

    .nav-brand > span {
      display: none;
    }

    .nav img {
      height: 58px;
    }

    .hero-shell {
      min-height: 760px;
      align-items: start;
      padding: 56px 24px 260px;
    }

    .hero-player img {
      object-position: center;
    }

    .hero-side-panels {
      right: 20px;
      bottom: 20px;
      width: calc(100% - 40px);
    }

    .featured-player-card {
      max-width: 290px;
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
    .pool-tools,
    .teaser-features {
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
      height: 46px;
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
      min-height: 42px;
      padding: 11px 16px;
      font-size: 14px;
    }

    .main-menu {
      width: 100%;
    }

    .hero-shell {
      min-height: clamp(500px, 84svh, 590px);
      border-radius: 20px;
      padding: 42px 18px 24px;
      align-content: center;
      gap: 20px;
    }

    .hero-shell::after {
      background:
        radial-gradient(circle at 72% 26%, rgba(255, 255, 255, 0.05), transparent 25%),
        radial-gradient(circle at 66% 25%, transparent 0, rgba(0, 0, 0, 0.16) 48%, rgba(0, 0, 0, 0.7) 100%),
        linear-gradient(90deg, rgba(9, 10, 15, 0.98) 0%, rgba(9, 10, 15, 0.84) 55%, rgba(9, 10, 15, 0.48) 100%);
    }

    .hero-player img {
      object-position: center top;
      opacity: 0.68;
    }

    .hero-content {
      max-width: 100%;
    }

    .hero-content h1 {
      margin-bottom: 12px;
      font-size: clamp(40px, 13vw, 58px);
      line-height: 0.95;
    }

    .hero-copy {
      max-width: 320px;
      font-size: clamp(22px, 7vw, 28px);
      line-height: 1.12;
    }

    .hero-tagline {
      max-width: 300px;
      margin: 12px 0 22px;
      font-size: 14px;
      line-height: 1.45;
    }

    .menu-actions {
      display: grid;
      max-width: 310px;
      grid-template-columns: 1fr;
      gap: 10px;
    }

    .menu-actions .primary,
    .menu-actions .secondary {
      width: 100%;
      justify-content: center;
      text-align: center;
    }

    .hero-side-panels {
      position: relative;
      right: auto;
      bottom: auto;
      z-index: 4;
      width: min(100%, 310px);
      justify-items: start;
    }

    .home-phoebe {
      display: none;
    }

    .featured-player-card {
      max-width: 270px;
      padding: 12px;
      border-radius: 8px;
    }

    .featured-player-card > strong {
      font-size: 18px;
    }

    .featured-player-card dl {
      margin-top: 12px;
      gap: 6px;
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
    }

    .mode-card-image {
      width: min(58%, 160px);
      height: 118px;
      margin-bottom: 12px;
      border-radius: 12px;
    }

    .mode-card-content {
      padding: 0 12px 14px;
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

    .formation-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .formation-grid button {
      min-height: 88px;
      border-radius: 14px;
      padding: 12px 8px;
    }

    .formation-grid span {
      font-size: 9px;
      letter-spacing: 0.12em;
    }

    .formation-grid strong {
      margin-top: 6px;
      font-size: clamp(22px, 7vw, 30px);
    }

    .draft-grid {
      width: 100%;
      gap: 14px;
    }

    .draft-head,
    .board-head,
    .result-head {
      gap: 12px;
    }

    .draft-head h1 {
      font-size: clamp(27px, 8vw, 36px);
    }

    .counter,
    .selection-pill {
      padding: 8px 12px;
      font-size: 12px;
    }

    .board-head {
      display: grid;
      grid-template-columns: 1fr;
      padding-bottom: 12px;
    }

    .draft-grid .board-status {
      display: none;
    }

    .mobile-draft-metrics {
      margin-top: 12px;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 7px;
    }

    .mobile-draft-metrics span {
      min-width: 0;
      border: 1px solid rgba(201, 166, 70, 0.24);
      border-radius: 999px;
      background: rgba(201, 166, 70, 0.07);
      padding: 8px 10px;
      color: #f1f2f5;
      font-size: 11px;
      font-weight: 850;
      line-height: 1.2;
      overflow-wrap: anywhere;
    }

    .mobile-draft-metrics b {
      margin-right: 4px;
      color: #8f95a5;
      font-weight: 800;
    }

    .live-analysis-visual {
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

    .controls,
    .pool-tools {
      display: grid;
      grid-template-columns: 1fr;
    }

    .status,
    .notice {
      margin-top: 14px;
      border-radius: 14px;
      padding: 14px;
    }

    .search,
    .pool-tools select {
      min-height: 42px;
      border-radius: 12px;
      padding: 11px 12px;
      font-size: 14px;
    }

    .spots {
      margin: 12px 0;
      font-size: 12px;
      line-height: 1.4;
    }

    .player-list {
      max-height: 420px;
      gap: 9px;
      padding-right: 0;
    }

    .player-card {
      border-radius: 14px;
      padding: 12px;
    }

    .draft-label {
      margin-bottom: 8px;
      padding: 3px 7px;
      font-size: 8px;
      letter-spacing: 0.08em;
    }

    .player-main strong {
      font-size: 17px;
      line-height: 1.18;
    }

    .player-main small,
    .slot-info span {
      font-size: 11px;
      line-height: 1.35;
    }

    .iog-line {
      margin-top: 8px;
      gap: 8px;
    }

    .iog-line b {
      font-size: 22px;
    }

    .real-stats {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
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

    .libra-bonus,
    .phoebe-result-comment,
    .club-teaser-flow {
      margin-top: 16px;
    }

    .libra-bonus {
      padding: 14px;
      border-radius: 12px;
    }

    .libra-bonus strong,
    .phoebe-result-comment strong {
      font-size: 16px;
      line-height: 1.35;
    }

    .club-teaser-message {
      border-radius: 14px;
      padding: 15px;
      font-size: 17px;
      line-height: 1.3;
    }

    .club-teaser-card {
      border-radius: 14px;
      padding: 18px;
    }

    .competition-list {
      gap: 7px;
    }

    .teaser-features {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      margin: 18px 0;
    }

    .teaser-features span {
      border-radius: 10px;
      padding: 10px 8px;
      font-size: 11px;
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
      padding: 36px 16px 18px;
    }

    .hero-content h1 {
      font-size: clamp(38px, 13vw, 52px);
    }

    .hero-copy {
      max-width: 280px;
      font-size: 21px;
    }

    .hero-tagline {
      margin-bottom: 18px;
    }

    .featured-player-card {
      display: none;
    }

    .mode-screen,
    .formation-screen {
      padding: 16px 10px;
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
      max-height: 390px;
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

</style>
