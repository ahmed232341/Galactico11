<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import type { Player } from "../../types/Player";

  export let player: Player | null = null;
  export let availableSlots: string[] = [];
  export let isOpen = false;

  const dispatch = createEventDispatcher();
  let selectedSlot = "";

  $: if (player && !selectedSlot) {
    selectedSlot = availableSlots[0] || "";
  }

  function chooseSlot(slot: string) {
    selectedSlot = slot;
  }

  function confirm() {
    if (!selectedSlot) return;
    dispatch("confirm", { slot: selectedSlot });
  }

  function dismiss() {
    dispatch("cancel");
  }
</script>

{#if isOpen && player}
  <div class="overlay">
    <div class="modal-panel">
      <div class="modal-header">
        <div>
          <p class="label">Assign pick</p>
          <h2>{player.name}</h2>
          <p class="subtitle">Select an eligible slot before confirming.</p>
        </div>
        <button class="close" on:click={dismiss} aria-label="Close assign modal">×</button>
      </div>

      <div class="slot-group">
        <div class="slot-card">
          <p class="label">Eligible positions</p>
          <div class="badges">
            {#each player.position as pos}
              <span class="badge">{pos}</span>
            {/each}
          </div>
        </div>

        <div class="slot-card">
          <p class="label">Available slots</p>
          <div class="badges">
            {#each availableSlots as slot}
              <button
                type="button"
                class:selected={selectedSlot === slot}
                on:click={() => chooseSlot(slot)}
              >
                {slot}
              </button>
            {/each}
          </div>
        </div>
      </div>

      <div class="actions">
        <button class="primary-button" on:click={confirm} disabled={!selectedSlot}>
          Assign to {selectedSlot || "slot"}
        </button>
        <button class="secondary-button" on:click={dismiss}>Change selection</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .overlay {
    position: fixed;
    inset: 0;
    z-index: 50;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
    background: rgba(9, 10, 15, 0.9);
    backdrop-filter: blur(18px);
  }

  .modal-panel {
    width: min(680px, 100%);
    background: #10121a;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 24px;
    padding: 28px;
    display: grid;
    gap: 24px;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 24px;
  }

  .label {
    margin: 0;
    font-size: 0.72rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #8a8f9e;
  }

  h2 {
    margin: 10px 0 0;
    font-size: 2rem;
    color: #f4f4f5;
  }

  .subtitle {
    margin: 10px 0 0;
    color: #8a8f9e;
    line-height: 1.6;
  }

  .close {
    border: none;
    background: transparent;
    color: #8a8f9e;
    font-size: 1.75rem;
    cursor: pointer;
  }

  .slot-group {
    display: grid;
    gap: 16px;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .slot-card {
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.03);
    border-radius: 20px;
    padding: 22px;
  }

  .badges {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 16px;
  }

  .badge,
  .badges button {
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.04);
    color: #f4f4f5;
    border-radius: 999px;
    padding: 10px 14px;
    font-size: 0.95rem;
    cursor: pointer;
  }

  .badges button.selected {
    background: rgba(201, 166, 70, 0.18);
    border-color: rgba(201, 166, 70, 0.35);
    color: #c9a646;
  }

  .actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    flex-wrap: wrap;
  }

  .primary-button,
  .secondary-button {
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 14px 20px;
    font-size: 0.95rem;
    cursor: pointer;
  }

  .primary-button {
    background: #c9a646;
    color: #10121a;
    border-color: rgba(201, 166, 70, 0.4);
  }

  .secondary-button {
    background: transparent;
    color: #f4f4f5;
  }

  .primary-button:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  @media (max-width: 760px) {
    .slot-group {
      grid-template-columns: 1fr;
    }

    .modal-panel {
      padding: 20px;
    }
  }
</style>
