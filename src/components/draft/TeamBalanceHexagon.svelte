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
    return Number.isFinite(value) && value > 0 ? formatIoG(value) : "—";
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

  $: profile = calculateTeamBalance(players, formation, chemistry, positionFit);
  $: attackTween.set(profile.attack);
  $: midfieldTween.set(profile.midfield);
  $: defenseTween.set(profile.defense);
  $: polygonPoints = [
    pointToward(150, 28, $attackTween),
    pointToward(244, 188, $midfieldTween),
    pointToward(56, 188, $defenseTween)
  ].join(" ");
  $: libraPercent = percent(profile.libraScore);
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
        <defs>
          <radialGradient id="balance-core" cx="50%" cy="48%" r="62%">
            <stop offset="0%" stop-color="#c9a646" stop-opacity="0.2" />
            <stop offset="56%" stop-color="#39e6c9" stop-opacity="0.07" />
            <stop offset="100%" stop-color="#07080d" stop-opacity="0" />
          </radialGradient>
          <linearGradient id="team-fill" x1="60" y1="28" x2="240" y2="198">
            <stop offset="0%" stop-color="#f1d56d" stop-opacity="0.52" />
            <stop offset="52%" stop-color="#c9a646" stop-opacity="0.28" />
            <stop offset="100%" stop-color="#39e6c9" stop-opacity="0.22" />
          </linearGradient>
          <filter id="triangle-glow" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <rect class="chart-bg" x="20" y="10" width="260" height="214" rx="24" />
        <ellipse class="chart-glow" cx="150" cy="132" rx="118" ry="92" />
        <polygon class="hex outer" points="150,16 252,74 252,190 150,224 48,190 48,74" />
        <polygon class="hex middle" points="150,55 218,94 218,171 150,194 82,171 82,94" />
        <polygon class="hex inner" points="150,94 184,113 184,152 150,164 116,152 116,113" />
        <line class="axis" x1="150" y1="134" x2="150" y2="28" />
        <line class="axis" x1="150" y1="134" x2="244" y2="188" />
        <line class="axis" x1="150" y1="134" x2="56" y2="188" />
        <circle class="center-dot" cx="150" cy="134" r="3.5" />
        <polygon class="team-shadow" points={polygonPoints} />
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

  {#if context === "final"}
    <section class="libra-scale" aria-label={`Libra Score ${profile.libraScore ?? 0}, ${libraLabel(profile.libraScore)}`}>
      <div class="libra-copy">
        <span>Libra Scale</span>
        <strong>{profile.libraScore ?? 0}</strong>
        <p>{libraLabel(profile.libraScore)}</p>
      </div>

      <div class="libra-meter" aria-hidden="true">
        <div class="meter-track">
          <i style={`width:${libraPercent}%`}></i>
          <b style={`left:${libraPercent}%`}></b>
        </div>
        <div class="meter-labels">
          <span>Volatile</span>
          <span>Stable</span>
          <span>Elite</span>
        </div>
        <p>{libraDescription(profile.libraScore)}</p>
      </div>
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
    isolation: isolate;
  }

  .chart-shell svg {
    width: 100%;
    max-height: 248px;
    display: block;
    overflow: visible;
  }

  .chart-bg {
    fill: rgba(4, 6, 12, 0.36);
    stroke: rgba(201, 166, 70, 0.14);
    stroke-width: 1;
  }

  .chart-glow {
    fill: url(#balance-core);
  }

  .hex,
  .axis {
    fill: none;
    stroke: rgba(201, 166, 70, 0.28);
    stroke-width: 1.15;
  }

  .outer {
    stroke: rgba(201, 166, 70, 0.48);
    filter: drop-shadow(0 5px 16px rgba(0, 0, 0, 0.32));
  }

  .middle { opacity: 0.72; }
  .inner { opacity: 0.52; }
  .axis {
    opacity: 0.72;
    stroke: rgba(170, 176, 192, 0.28);
  }

  .center-dot {
    fill: rgba(239, 213, 116, 0.72);
    filter: drop-shadow(0 0 8px rgba(239, 213, 116, 0.36));
  }

  .team-shadow {
    fill: rgba(0, 0, 0, 0.22);
    stroke: transparent;
    transform: translateY(5px);
  }

  .team-shape {
    fill: url(#team-fill);
    stroke: #f0d36a;
    stroke-width: 2.6;
    stroke-linejoin: round;
    transition: points 0.6s ease;
    filter: url(#triangle-glow) drop-shadow(0 8px 18px rgba(201, 166, 70, 0.22));
  }

  .point {
    fill: #fff3a3;
    stroke: #0b0d14;
    stroke-width: 1.8;
    filter: drop-shadow(0 0 7px rgba(239, 213, 116, 0.55));
  }

  .label {
    fill: #d9dce5;
    font: 800 10px Inter, system-ui, sans-serif;
    text-transform: uppercase;
    letter-spacing: 0.04em;
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
    height: 4px;
    overflow: hidden;
    border-radius: 999px;
    background: #282c38;
  }

  .line-scores i {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, #806b2f, #c9a646, #efd574);
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

  .libra-meter {
    min-width: 0;
    display: grid;
    gap: 9px;
  }

  .meter-track {
    position: relative;
    height: 16px;
    overflow: visible;
    border: 1px solid rgba(201, 166, 70, 0.3);
    border-radius: 999px;
    background:
      linear-gradient(90deg, rgba(239, 106, 106, 0.28), rgba(228, 191, 85, 0.26), rgba(98, 201, 139, 0.3)),
      #0b0d14;
    box-shadow: inset 0 0 18px rgba(0, 0, 0, 0.42);
  }

  .meter-track i {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, #c9a646, #efd574, #68d391);
    box-shadow: 0 0 16px rgba(201, 166, 70, 0.26);
    transition: width 0.65s cubic-bezier(0.22, 1, 0.36, 1);
  }

  .meter-track b {
    position: absolute;
    top: 50%;
    width: 12px;
    height: 28px;
    border: 2px solid #fff3a3;
    border-radius: 999px;
    background: #151823;
    transform: translate(-50%, -50%);
    box-shadow: 0 0 14px rgba(239, 213, 116, 0.38);
    transition: left 0.65s cubic-bezier(0.22, 1, 0.36, 1);
  }

  .meter-labels {
    display: flex;
    justify-content: space-between;
    color: #8f95a5;
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
  }

  .libra-meter p {
    margin: 0;
    color: #cbd0dc;
    font-size: 12px;
    line-height: 1.45;
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
      padding: 18px;
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

    .final-analysis .profile-grid {
      grid-template-columns: 1fr;
      align-items: stretch;
    }

    .chart-shell svg {
      max-height: 210px;
    }

    .final-analysis .chart-shell svg {
      height: clamp(180px, 48vw, 220px);
      max-height: 220px;
      margin-inline: auto;
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
      min-height: 0;
      display: grid;
      grid-template-columns: 104px minmax(0, 1fr);
      align-items: center;
      border-radius: 10px;
      padding: 12px;
      gap: 10px;
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

    .final-analysis .chart-shell svg {
      height: 180px;
      max-height: 190px;
    }

    .label {
      font-size: 9px;
    }

    .balance-factors {
      grid-template-columns: 1fr;
    }

    .libra-scale {
      grid-template-columns: 92px minmax(0, 1fr);
      gap: 8px;
      text-align: left;
    }

  }
</style>
