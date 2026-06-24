<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import type { Challenge, Formation } from "../../types/Player";

  const dispatch = createEventDispatcher();
  export let challenge: Challenge;
  export let formation: Formation | "";

  function onSpin() {
    dispatch("spin");
  }

  function onStart() {
    dispatch("start");
  }
</script>

<div class="grid gap-5 lg:grid-cols-[1fr_1.1fr]">
  <div class="rounded-[2rem] border border-slate-700/80 bg-[#11131d]/90 p-6 shadow-[0_28px_80px_-50px_rgba(0,0,0,0.75)]">
    <p class="text-xs uppercase tracking-[0.32em] text-slate-500">League</p>
    <h2 class="mt-4 text-3xl font-semibold text-white">{challenge.league}</h2>
    <p class="mt-3 text-sm leading-6 text-slate-400">A premium pool from one of football’s elite competitions.</p>
  </div>

  <div class="grid gap-4 sm:grid-cols-3">
    <div class="rounded-[2rem] border border-slate-700/80 bg-[#11131d]/90 p-5">
      <p class="text-[11px] uppercase tracking-[0.36em] text-slate-500">Club</p>
      <strong class="mt-3 block text-xl text-white">{challenge.club}</strong>
    </div>
    <div class="rounded-[2rem] border border-slate-700/80 bg-[#11131d]/90 p-5">
      <p class="text-[11px] uppercase tracking-[0.36em] text-slate-500">Era</p>
      <strong class="mt-3 block text-xl text-white">{challenge.era}</strong>
    </div>
    <div class="rounded-[2rem] border border-slate-700/80 bg-[#11131d]/90 p-5">
      <p class="text-[11px] uppercase tracking-[0.36em] text-slate-500">Formation</p>
      <strong class="mt-3 block text-xl text-white">{formation}</strong>
    </div>
  </div>

  <div class="flex flex-col gap-4 rounded-[2rem] border border-slate-700/80 bg-[#11131d]/90 p-6 sm:col-span-3">
    <div>
      <p class="text-xs uppercase tracking-[0.32em] text-slate-500">Draft preview</p>
      <h3 class="mt-3 text-2xl font-semibold text-white">Spin the universe. Lock your currency of players.</h3>
    </div>
    <div class="mt-4 flex flex-col gap-3 sm:flex-row">
      <button class="rounded-[1.5rem] border border-[#C9A646]/30 bg-[#C9A646]/10 px-5 py-3 text-sm font-semibold text-[#C9A646] transition hover:bg-[#C9A646]/20" on:click={onSpin}>
        Spin again
      </button>
      <button class="rounded-[1.5rem] bg-white px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-slate-100" on:click={onStart}>
        Start draft
      </button>
    </div>
  </div>
</div>
