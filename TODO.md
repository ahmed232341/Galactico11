# TODO — Play Level System

## Step 1 — Audit current DraftGame flow
- [x] Confirm Draft → Analysis → Simulation/Result chain.
- [x] Identify existing states: `simulation`, `record`, `libra`, `result`.
- [x] Detect whether any `playLevel` UI already exists (should not rely on assumptions).


## Step 2 — Add PLAY LEVEL state machine (no draft/final UI changes)
- [ ] Introduce `screen === "playLevel"` rendering.
- [ ] Ensure existing Final Reveal (the `screen === "result"` block) remains untouched.


## Step 3 — World Cup Play Level (cinematic stages)


- [ ] Add tournament stages: Group Match 1–3 → Round of 32 → Round of 16 → Quarter Final → Semi Final → Final.
- [ ] Implement stage progression bar + “gold completed” markers.
- [ ] Add one-match-at-a-time reveal with Continue/Skip + Simulation Speed.
- [ ] Generate match stats (possession, shots, xG, MOTM) without purely random outcomes.
- [ ] Aggregate tournament stats needed by Final Reveal.

## Step 4 — Invincibles Play Level (checkpoint progression)
- [ ] Replace current 38-match W/D/L shuffle UI with checkpoint-based progression cards:
  - Matches 1–6, 7–12, 13–19, 20–25, 26–31, 32–38
- [ ] Keep simulation statistical dependence on: avg IoG, formation, chemistry, libra/team balance, tactical identity.
- [ ] Provide Continue/Skip + Simulation Speed; animate counters.
- [ ] Aggregate league stats needed by Final Reveal.

## Step 5 — Wire Play Level completion into existing Final Reveal chain
- [ ] Ensure Final Reveal uses computed stats via existing variables:
  - World Cup: `predictedWorldCupOutcome` and any other used fields.
  - Invincibles: keep `predictedEtRecord` chain consistent or derive equivalent.

## Step 6 — Mobile polish
- [ ] Ensure cards stack vertically.
- [ ] Keep bottom-fixed action buttons.
- [ ] Ensure progress indicators stay visible.

## Step 7 — Testing
- [ ] Smoke test World Cup mode: draft → analysis → playLevel → final reveal.
- [ ] Smoke test Invincibles mode: draft → analysis → playLevel → final reveal.
- [ ] Verify Mystery Picks still reveal correctly during analysis.

