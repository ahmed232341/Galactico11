<script lang="ts">
  import { players } from "../../data/players";

  export let position = "";

  $: filteredPlayers = players.filter((player) =>
    player.position.includes(position)
  );
</script>

<div class="picker">
  <h2>Select {position}</h2>
  <p class="count">{filteredPlayers.length} players found</p>

  {#if filteredPlayers.length === 0}
    <p class="empty">No players for this position yet.</p>
  {/if}

  {#each filteredPlayers as player}
    <button class="player">
      <div>
        <strong>{player.name}</strong>
        <p>{player.club} • {player.era}</p>
      </div>

      <span class="iog">IoG {player.iog}</span>
    </button>
  {/each}
</div>

<style>
  .picker {
    position: fixed;
    right: 0;
    top: 0;
    width: 360px;
    height: 100vh;
    background: #0b1020;
    color: white;
    padding: 1rem;
    overflow-y: auto;
    box-shadow: -10px 0 30px rgba(0, 0, 0, 0.35);
  }

  .count {
    color: #94a3b8;
    margin-bottom: 1rem;
  }

  .empty {
    color: #f87171;
  }

  .player {
    width: 100%;
    padding: 1rem;
    margin-bottom: 0.75rem;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    background: #141b2d;
    color: white;

    display: flex;
    justify-content: space-between;
    align-items: center;

    cursor: pointer;
  }

  .player:hover {
    border-color: #00d68f;
  }

  .player p {
    margin: 0.25rem 0 0;
    color: #94a3b8;
    font-size: 0.85rem;
  }

  .iog {
    background: #00d68f;
    color: #06120d;
    padding: 0.4rem 0.65rem;
    border-radius: 999px;
    font-weight: 800;
    white-space: nowrap;
  }
</style>