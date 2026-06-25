<script lang="ts">
  import { cubicOut } from "svelte/easing";
  import { tweened } from "svelte/motion";
  import { calculateTeamBalance, type TeamBalancePlayer } from "../../lib/teamBalance";

  export let players: TeamBalancePlayer[] = [];
  export let formation = "4-3-3";
  export let chemistry = 0;
  export let positionFit = 0;
  export let context: "live" | "final" = "live";

  const attackTween = tweened(0, { duration: 600, easing: cubicOut });
  const midfieldTween = tweened(0, { duration: 600, easing: cubicOut });
  const defenseTween = tweened(0, { duration: 600, easing: cubicOut });

  function pointToward(vertexX: number, vertexY: number, value: number) {
    const centerX = 150;
    const centerY = 134;
    const ratio = Math.max(0, Math.min(100, value)) / 100;
    return `${centerX + (vertexX - centerX) * ratio},${centerY + (vertexY - centerY) * ratio}`;
  }

  function display(value: number) {
    return value > 0 ? value.toFixed(1) : "-";
  }

  function libraLabel(value: number | null) {
    const score = value ?? 0;
    if (score >= 95) return "Elite Balance";
    if (score >= 85) return "Well Balanced";
    if (score >= 70) return "Functional";
    if (score >= 50) return "Unstable";
    return "Chaotic";
  }

  function libraTilt(value: number | null) {
    const score = value ?? 0;
    if (score >= 90) return 0;
    if (score >= 80) return -1;
    if (score >= 60) return -4;
    if (score >= 40) return -10;
    return -16;
  }

  $: profile = calculateTeamBalance(players, formation, chemistry, positionFit);
  $: attackTween.set(profile.attack);
  $: midfieldTween.set(profile.midfield);
  $: defenseTween.set(profile.defense);
  $: polygonPoints = [
    pointToward(150, 28, $attackTween),
    pointToward(244, 188, $midfieldTween),
    pointToward(56, 188, $defenseTween)
  ].join(" ");
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
      <svg viewBox="0 0 300 240" role="img" aria-label={`Attack ${profile.attack}, midfield ${profile.midfield}, defense ${profile.defense}`}>
        <polygon class="hex outer" points="150,16 252,74 252,190 150,224 48,190 48,74" />
        <polygon class="hex middle" points="150,55 218,94 218,171 150,194 82,171 82,94" />
        <polygon class="hex inner" points="150,94 184,113 184,152 150,164 116,152 116,113" />
        <line class="axis" x1="150" y1="134" x2="150" y2="28" />
        <line class="axis" x1="150" y1="134" x2="244" y2="188" />
        <line class="axis" x1="150" y1="134" x2="56" y2="188" />
        <polygon class="team-shape" points={polygonPoints} />
        <circle class="point" cx={150} cy={134 + (28 - 134) * ($attackTween / 100)} r="4" />
        <circle class="point" cx={150 + (244 - 150) * ($midfieldTween / 100)} cy={134 + (188 - 134) * ($midfieldTween / 100)} r="4" />
        <circle class="point" cx={150 + (56 - 150) * ($defenseTween / 100)} cy={134 + (188 - 134) * ($defenseTween / 100)} r="4" />
        <text class="label attack" x="150" y="12">Attack</text>
        <text class="label midfield" x="274" y="213">Midfield</text>
        <text class="label defense" x="26" y="213">Defense</text>
      </svg>
      <strong class="shape-status">{profile.status}</strong>
    </div>

    <div class="line-scores">
      <article>
        <span>Attack</span>
        <strong>{display(profile.attack)}</strong>
        <div><i style={`width:${profile.attack}%`}></i></div>
      </article>
      <article>
        <span>Midfield</span>
        <strong>{display(profile.midfield)}</strong>
        <div><i style={`width:${profile.midfield}%`}></i></div>
      </article>
      <article>
        <span>Defense</span>
        <strong>{display(profile.defense)}</strong>
        <div><i style={`width:${profile.defense}%`}></i></div>
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

  {#if context === "final"}
    <section class="libra-scale" aria-label={`Libra Score ${profile.libraScore ?? 0}, ${libraLabel(profile.libraScore)}`}>
      <div class="libra-copy">
        <span>Libra Scale</span>
        <strong>{profile.libraScore ?? 0}</strong>
        <p>{libraLabel(profile.libraScore)}</p>
      </div>

      <svg viewBox="0 0 300 150" role="img" aria-hidden="true">
        <path class="scale-base" d="M112 132 H188 M150 38 V132 M126 132 Q150 112 174 132" />
        <circle class="scale-pivot" cx="150" cy="56" r="7" />
        <g class="scale-beam" style={`transform: rotate(${libraTilt(profile.libraScore)}deg)`}>
          <path d="M70 56 H230" />
          <path d="M82 56 V103 M218 56 V103" />
          <path d="M55 103 Q82 126 109 103 Z M191 103 Q218 126 245 103 Z" />
        </g>
      </svg>
    </section>
  {/if}

  <div class="balance-insight">
    <span>Phoebe Analysis</span>
    <p>{profile.insight}</p>
  </div>
</section>

<style>
  .balance-panel {
    margin-top: 24px;
    border-top: 1px solid #262a38;
    padding-top: 22px;
    color: #f5f5f6;
  }

  .balance-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 18px;
  }

  .balance-header span,
  .formation-badge small,
  .balance-factors span,
  .balance-insight span {
    display: block;
    color: #8c92a2;
    font-size: 10px;
    font-weight: 850;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  .balance-header h3 {
    margin: 5px 0 0;
    font-size: 20px;
  }

  .formation-badge {
    border: 1px solid rgba(201, 166, 70, 0.32);
    border-radius: 10px;
    background: rgba(201, 166, 70, 0.07);
    padding: 9px 12px;
    text-align: right;
  }

  .formation-badge strong {
    display: block;
    margin-top: 3px;
    color: #d6b956;
  }

  .profile-grid {
    margin-top: 16px;
    display: grid;
    grid-template-columns: minmax(0, 1fr) 130px;
    align-items: center;
    gap: 14px;
  }

  .chart-shell {
    position: relative;
  }

  .chart-shell svg {
    width: 100%;
    max-height: 248px;
    display: block;
    overflow: visible;
  }

  .hex,
  .axis {
    fill: none;
    stroke: #343947;
    stroke-width: 1;
  }

  .middle { opacity: 0.68; }
  .inner { opacity: 0.42; }
  .axis { opacity: 0.55; }

  .team-shape {
    fill: rgba(201, 166, 70, 0.2);
    stroke: #d2b453;
    stroke-width: 2.2;
    stroke-linejoin: round;
    transition: points 0.6s ease;
    filter: drop-shadow(0 5px 14px rgba(201, 166, 70, 0.14));
  }

  .point {
    fill: #efd574;
    stroke: #11131b;
    stroke-width: 1.5;
  }

  .label {
    fill: #aab0c0;
    font: 800 10px Inter, system-ui, sans-serif;
    text-transform: uppercase;
  }

  .attack { text-anchor: middle; }
  .midfield { text-anchor: end; }
  .defense { text-anchor: start; }

  .shape-status {
    position: absolute;
    left: 50%;
    bottom: 8px;
    transform: translateX(-50%);
    border: 1px solid rgba(201, 166, 70, 0.3);
    border-radius: 999px;
    background: rgba(12, 14, 21, 0.9);
    color: #d3b657;
    padding: 5px 9px;
    font-size: 9px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    white-space: nowrap;
  }

  .line-scores {
    display: grid;
    gap: 15px;
  }

  .line-scores article {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: baseline;
    gap: 8px;
  }

  .line-scores span {
    color: #9298a8;
    font-size: 11px;
  }

  .line-scores strong {
    font-size: 16px;
    font-variant-numeric: tabular-nums;
  }

  .line-scores article > div {
    grid-column: 1 / -1;
    height: 3px;
    overflow: hidden;
    background: #282c38;
  }

  .line-scores i {
    display: block;
    height: 100%;
    background: #c9a646;
    transition: width 0.6s ease;
  }

  .balance-factors {
    margin-top: 18px;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  .balance-factors article {
    border: 1px solid #282c38;
    border-radius: 10px;
    background: #151823;
    padding: 11px;
  }

  .balance-factors strong {
    display: block;
    margin-top: 5px;
    font-size: 17px;
    font-variant-numeric: tabular-nums;
  }

  .balance-insight {
    margin-top: 10px;
    border-left: 2px solid #c9a646;
    background: rgba(201, 166, 70, 0.06);
    padding: 12px 14px;
  }

  .libra-scale {
    margin-top: 12px;
    min-height: 148px;
    display: grid;
    grid-template-columns: minmax(0, 140px) minmax(180px, 1fr);
    align-items: center;
    gap: 14px;
    border: 1px solid rgba(201, 166, 70, 0.24);
    border-radius: 12px;
    background: linear-gradient(135deg, rgba(201, 166, 70, 0.07), rgba(13, 16, 24, 0.94));
    padding: 14px 16px;
  }

  .libra-copy > span {
    color: #8c92a2;
    font-size: 10px;
    font-weight: 850;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  .libra-copy strong {
    display: block;
    margin-top: 7px;
    color: #efd574;
    font-size: 34px;
    line-height: 1;
  }

  .libra-copy p {
    margin: 7px 0 0;
    color: #d0d4de;
    font-size: 13px;
    font-weight: 750;
  }

  .libra-scale svg {
    width: 100%;
    height: 132px;
    overflow: visible;
  }

  .scale-base,
  .scale-beam path {
    fill: none;
    stroke: #c9a646;
    stroke-width: 3;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  .scale-beam {
    transform-origin: 150px 56px;
    transition: transform 0.65s cubic-bezier(0.22, 1, 0.36, 1);
  }

  .scale-beam path:last-child {
    fill: rgba(201, 166, 70, 0.14);
    stroke-width: 2;
  }

  .scale-pivot {
    fill: #efd574;
    stroke: #11131b;
    stroke-width: 3;
  }

  .balance-insight p {
    margin: 6px 0 0;
    color: #c9cdd7;
    font-size: 13px;
    line-height: 1.5;
  }

  .final-analysis {
    border: 1px solid #282c38;
    border-radius: 18px;
    background: #11141d;
    padding: 20px;
  }

  @media (max-width: 560px) {
    .profile-grid {
      grid-template-columns: 1fr;
    }

    .line-scores {
      grid-template-columns: repeat(3, 1fr);
    }

    .shape-status {
      bottom: 2px;
    }

    .libra-scale {
      grid-template-columns: 104px minmax(0, 1fr);
      padding-inline: 12px;
    }

    .libra-copy strong {
      font-size: 28px;
    }
  }

  @media (max-width: 768px) {
    .balance-panel {
      margin-top: 16px;
      padding-top: 16px;
    }

    .final-analysis {
      border-radius: 14px;
      padding: 14px;
    }

    .balance-header {
      gap: 12px;
    }

    .balance-header span,
    .formation-badge small,
    .balance-factors span,
    .balance-insight span {
      font-size: 8px;
      letter-spacing: 0.1em;
    }

    .balance-header h3 {
      font-size: 18px;
    }

    .formation-badge {
      border-radius: 8px;
      padding: 7px 9px;
    }

    .profile-grid {
      margin-top: 12px;
      gap: 10px;
    }

    .chart-shell svg {
      max-height: 210px;
    }

    .shape-status {
      padding: 4px 7px;
      font-size: 8px;
    }

    .line-scores {
      gap: 10px;
    }

    .line-scores span {
      font-size: 10px;
    }

    .line-scores strong {
      font-size: 14px;
    }

    .balance-factors {
      margin-top: 12px;
      gap: 7px;
    }

    .balance-factors article {
      border-radius: 8px;
      padding: 9px;
    }

    .balance-factors strong {
      font-size: 15px;
    }

    .libra-scale {
      min-height: 126px;
      border-radius: 10px;
      padding: 12px;
    }

    .libra-scale svg {
      height: 106px;
    }

    .libra-copy strong {
      font-size: 28px;
    }

    .libra-copy p {
      font-size: 12px;
    }

    .balance-insight {
      margin-top: 9px;
      padding: 10px 12px;
    }

    .balance-insight p {
      font-size: 12px;
      line-height: 1.42;
    }
  }

  @media (max-width: 430px) {
    .balance-header {
      display: grid;
      grid-template-columns: 1fr auto;
      align-items: start;
    }

    .chart-shell svg {
      max-height: 184px;
    }

    .label {
      font-size: 9px;
    }

    .balance-factors {
      grid-template-columns: 1fr;
    }

    .libra-scale {
      grid-template-columns: 1fr;
      gap: 8px;
      text-align: center;
    }

    .libra-scale svg {
      height: 94px;
    }
  }
</style>
