<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import type { Player } from "../../types/Player";

  export let player: Player;
  export let roleLabel = "";

  const dispatch = createEventDispatcher();

  function selectPlayer() {
    dispatch("select", { player });
  }

  const initials = player.name
    .split(" ")
    .filter(Boolean)
    .map((segment) => segment[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
</script>

<button type="button" class="group flex w-full items-center gap-4 rounded-[2rem] border border-slate-700/80 bg-[#0f1320]/90 p-5 text-left transition hover:border-[#C9A646]/40 hover:bg-[#171a28]" on:click={selectPlayer}>
  <div class="flex h-20 w-20 items-center justify-center rounded-[1.5rem] border border-slate-700/80 bg-slate-900 text-xl font-semibold text-white">
    {initials}
  </div>

  <div class="min-w-0 flex-1">
    <p class="text-[11px] uppercase tracking-[0.32em] text-slate-500">{roleLabel || player.position.join(" / ")}</p>
    <h3 class="mt-2 text-lg font-semibold text-white">{player.name}</h3>
    <p class="mt-1 text-sm text-slate-400">{player.club}</p>
  </div>

  <div class="flex flex-col items-end gap-1 rounded-[1.5rem] bg-[#11131b] px-4 py-3">
    <span class="text-[10px] uppercase tracking-[0.35em] text-slate-500">IoG</span>
    <strong class="text-2xl text-[#C9A646]">{player.iog}</strong>
  </div>
</button>
