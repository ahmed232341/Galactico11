<script lang="ts">
  import { cubicOut } from "svelte/easing";
  import { tweened } from "svelte/motion";
  import { formatIoG } from "../../lib/iogFormat";
  import { calculateTeamBalance, type TeamBalancePlayer } from "../../lib/teamBalance";

  export let players: TeamBalancePlayer[] = [];
  export let formation = "4-3-3";
  export let chemistry = 0;
  export let positionFit = 0;
  export let context: "live" | "final" = "live";

  const attackTween = tweened(0, { duration: 420, easing: cubicOut });
  const midfieldTween = tweened(0, { duration: 420, easing: cubicOut });
  const defenseTween = tweened(0, { duration: 420, easing: cubicOut });

  const centerX = 150;
  const centerY = 128;
  const radarVertices = [
    { key: "attack", label: "ATK", x: 150, y: 22 },
    { key: "defense", label: "DEF", x: 242, y: 181 },
    { key: "midfield", label: "MID", x: 58, y: 181 }
  ] as const;

  function pointToward(vertexX: number, vertexY: number, value: number, floor = 0) {
    const ratio = Math.max(0, Math.min(100, value)) / 100;
    const shapedRatio = Math.max(floor, ratio);
    return `${centerX + (vertexX - centerX) * shapedRatio},${centerY + (vertexY - centerY) * shapedRatio}`;
  }

  function ringPoints(scale: number) {
    return radarVertices.map((vertex) => pointToward(vertex.x, vertex.y, scale * 100)).join(" ");
  }

  function axisValue(key: (typeof radarVertices)[number]["key"]) {
    if (key === "attack") return $attackTween;
    if (key === "midfield") return $midfieldTween;
    return $defenseTween;
  }

  function axisPoint(vertex: (typeof radarVertices)[number]) {
    const [x, y] = pointToward(vertex.x, vertex.y, axisValue(vertex.key)).split(",");
    return { x, y };
  }

  function display(value: number) {
    return Number.isFinite(value) && value > 0 ? formatIoG(value) : "-";
  }

  function libraLabel(value: number | null) {
    const score = value ?? 0;
    if (score >= 90) return "Elite Consistency";
    if (score >= 80) return "Well Balanced";
    if (score >= 70) return "Stable but Uneven";
    if (score >= 60) return "Fragile Structure";
    return "Volatile XI";
  }

  function libraDescription(value: number | null) {
    const score = value ?? 0;
    if (score >= 90) return "Consistent quality across the XI with very few weak links.";
    if (score >= 80) return "Strong squad consistency with enough balance to survive pressure.";
    if (score >= 70) return "Useful structure, but some line gaps can still be targeted.";
    if (score >= 60) return "A fragile squad profile with uneven quality across roles.";
    return "Stars may be carrying too many weak links.";
  }

  function percent(value: number | null) {
    return Math.max(0, Math.min(100, Number(value) || 0));
  }

  function libraTilt(value: number | null) {
    const score = value ?? 0;
    if (score >= 90) return 0;
    if (score >= 80) return -3;
    if (score >= 70) return -7;
    if (score >= 60) return -12;
    return -18;
  }

  $: profile = calculateTeamBalance(players, formation, chemistry, positionFit);
  $: attackTween.set(profile.attack);
  $: midfieldTween.set(profile.midfield);
  $: defenseTween.set(profile.defense);
  $: polygonPoints = [
    pointToward(150, 22, $attackTween, players.length ? 0 : 0.025),
    pointToward(242, 181, $defenseTween, players.length ? 0 : 0.025),
    pointToward(58, 181, $midfieldTween, players.length ? 0 : 0.025)
  ].join(" ");
  $: libraRotation = libraTilt(profile.libraScore);
</script>

<section class="balance-panel" class:final-analysis={context === "final"} aria-label={context === "final" ? "Final tactical balance" : "Live tactical balance"}>
  <header class="balance-header">
    <div>
      <span>{context === "final" ? "Final Tactical Profile" : "Live Tactical Profile"}</span>
      <h3>Team Balance</h3>
    </div>
    <div class="formation-badge">
      <small>Formation</small>
      <strong>{formation}</strong>
    </div>
  </header>

  <div class="profile-grid">
    <div class="chart-shell">
      <svg
        class="balance-radar"
        viewBox="0 0 300 256"
        width="300"
        height="256"
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label={`Attack ${profile.attack}, midfield ${profile.midfield}, defense ${profile.defense}`}
      >
        <rect x="28" y="18" width="244" height="216" rx="18" fill="rgba(9, 13, 20, 0.42)" stroke="rgba(255, 255, 255, 0.08)" stroke-width="1" />
        <polygon points={ringPoints(1)} fill="rgba(8, 11, 19, 0.18)" stroke="rgba(255, 255, 255, 0.24)" stroke-width="1.15" />
        <polygon points={ringPoints(0.68)} fill="none" stroke="rgba(255, 255, 255, 0.18)" stroke-width="1" />
        <polygon points={ringPoints(0.36)} fill="none" stroke="rgba(255, 255, 255, 0.12)" stroke-width="1" />
        {#each radarVertices as vertex}
          <line x1={centerX} y1={centerY} x2={vertex.x} y2={vertex.y} stroke="rgba(255, 255, 255, 0.22)" stroke-width="1" />
        {/each}
        <circle cx={centerX} cy={centerY} r="3.5" fill="rgba(255, 255, 255, 0.55)" />
        <polygon class="team-shadow" points={polygonPoints} fill="rgba(0, 0, 0, 0.26)" stroke="transparent" />
        <polygon class="team-shape" points={polygonPoints} fill="rgba(34, 240, 230, 0.18)" stroke="rgba(34, 240, 230, 0.95)" stroke-width="3" stroke-linejoin="round" />
        {#each radarVertices as vertex}
          {@const axis = axisPoint(vertex)}
          <circle class="point" cx={axis.x} cy={axis.y} r="3.2" fill="rgba(221, 255, 253, 0.95)" stroke="rgba(4, 9, 14, 0.95)" stroke-width="1.5" />
        {/each}
        <text class="hud-label" x="150" y="13" text-anchor="middle" fill="rgba(226, 232, 240, 0.8)" font-size="10" font-weight="800" font-family="Inter, system-ui, sans-serif" letter-spacing="0.08em">ATK</text>
        <text class="hud-label" x="271" y="190" text-anchor="end" fill="rgba(226, 232, 240, 0.8)" font-size="10" font-weight="800" font-family="Inter, system-ui, sans-serif" letter-spacing="0.08em">DEF</text>
        <text class="hud-label" x="29" y="190" text-anchor="start" fill="rgba(226, 232, 240, 0.8)" font-size="10" font-weight="800" font-family="Inter, system-ui, sans-serif" letter-spacing="0.08em">MID</text>
        {#if profile.status === "Shape Forming"}
          <text class="forming-label" x="150" y="149" text-anchor="middle" fill="rgba(239, 213, 116, 0.9)" font-size="9" font-weight="850" font-family="Inter, system-ui, sans-serif" letter-spacing="1.25">Shape Forming</text>
        {/if}
      </svg>
    </div>

    <div class="line-scores">
      <article>
        <span>Attack</span>
        <strong>{display(profile.attack)}</strong>
        <div><i style={`width:${percent(profile.attack)}%`}></i></div>
      </article>
      <article>
        <span>Midfield</span>
        <strong>{display(profile.midfield)}</strong>
        <div><i style={`width:${percent(profile.midfield)}%`}></i></div>
      </article>
      <article>
        <span>Defense</span>
        <strong>{display(profile.defense)}</strong>
        <div><i style={`width:${percent(profile.defense)}%`}></i></div>
      </article>
    </div>
  </div>

  <div class="balance-factors">
    <article>
      <span>Position Fit</span>
      <strong>{profile.positionFit}%</strong>
    </article>
    <article>
      <span>Chemistry</span>
      <strong>{profile.chemistry}%</strong>
    </article>
    <article>
      <span>Libra</span>
      <strong>{profile.libraScore ?? "-"}</strong>
    </article>
    <article>
      <span>Tactical Distribution</span>
      <strong>{profile.tacticalDistribution}%</strong>
    </article>
  </div>

  <section class="libra-scale" aria-label={`Libra Score ${profile.libraScore ?? 0}, ${libraLabel(profile.libraScore)}`}>
    <div class="libra-copy">
      <span>Libra Scale</span>
      <strong>{profile.libraScore ?? "-"}</strong>
      <p>{profile.libraScore == null ? "Building" : libraLabel(profile.libraScore)}</p>
    </div>

    <div class="libra-meter" aria-hidden="true">
      <svg class="libra-scale-svg" viewBox="0 0 320 150" width="320" height="150" preserveAspectRatio="xMidYMid meet" role="presentation">
        <text x="54" y="24" fill="#8f95a5" font-size="10" font-weight="850" font-family="Inter, system-ui, sans-serif" letter-spacing="0.8">Volatile</text>
        <text x="266" y="24" text-anchor="end" fill="#8f95a5" font-size="10" font-weight="850" font-family="Inter, system-ui, sans-serif" letter-spacing="0.8">Consistent</text>
        <path class="scale-base" d="M128 132 H192 M160 46 V132 M134 132 Q160 112 186 132" fill="none" stroke="rgba(201, 166, 70, 0.68)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
        <circle class="scale-pivot" cx="160" cy="58" r="7" fill="#efd574" stroke="#11131b" stroke-width="3" />
        <g class="scale-beam" style={`transform-box: view-box; transform-origin: 160px 58px; transform: rotate(${libraRotation}deg); transition: transform 0.42s cubic-bezier(0.22,1,0.36,1);`}>
          <path d="M70 58 H250" fill="none" stroke="#e7cf78" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
          <path d="M86 58 V104 M234 58 V104" fill="none" stroke="#e7cf78" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
          <path class="scale-pan" d="M58 104 Q86 128 114 104 Z" fill="rgba(201, 166, 70, 0.16)" stroke="#e7cf78" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          <path class="scale-pan" d="M206 104 Q234 128 262 104 Z" fill="rgba(201, 166, 70, 0.16)" stroke="#e7cf78" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
        </g>
      </svg>
      <p>{profile.libraScore == null ? "Consistency appears once enough players are selected." : libraDescription(profile.libraScore)}</p>
    </div>
  </section>

  <div class="balance-insight">
    <span>Phoebe Analysis</span>
    <p>{profile.insight}</p>
  </div>
</section>
