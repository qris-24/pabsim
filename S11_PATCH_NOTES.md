# S11 — scripted opponent interaction (2026-10-18)

Kernel `…+S10+S11`. New layer `pab_interaction_s11.py` (`InteractionMixin`, above `CommanderMixin`; PhysicalZoneGame only). 662 reference fixtures (650 + 12). No frozen file edited. Deck, Lesson, Phase 9, sweeps and rankings unchanged.

## What was built
`script_opponent_actions(seat, [{'turn': N, 'kind': …}])` at game start. An action fires when the clock begins that seat's precombat main on game turn N (sorcery speed; no priority exchange is modeled, so the controller cannot respond). Six kinds with fixed, documented target policies — nothing is inferred from the board:
- `destroy_commander` — frozen `destroy()` on Savra (honours until-end-of-turn indestructibility); `no_target` if she is not on the battlefield.
- `destroy_creature` — the controller's highest-power nontoken creature, Savra last, tokens never.
- `exile_creature` — same policy; the permanent leaves without dying (no triggers), the card goes to `zones['exile']`, tokens cease; Savra returns to the command zone at the SBA check (S10, CR 903.9a from exile).
- `board_wipe` — every creature of every seat destroyed as ONE event under the S3 look-back view, so leave-the-battlefield triggers see the whole pre-wipe board (CR 603.10a): the controller's own dying Blood Artist / Deathgreeter trigger for every other death; indestructible creatures survive; opposing deaths reach the frozen own-card triggers.
- `graveyard_exile` — every card in the controller's graveyard exiled; graveyard links and LKI dropped (no longer reanimation targets).
- `edict` — the controller sacrifices one creature (a token if any, else the lowest-power nontoken that is not Savra, else Savra) through the frozen `sacrifice()`, so Savra's own triggers fire.
After each action state-based actions are checked (CR 704.3). Lost seats do not act. `opponent_actions_done` and the trace record every firing.

## Evidence
CR 603.10a (look-back) and 704.3 as used by S3; 903.9a as recorded for S10. No new card evidence: the actions are generic effects, not deck cards.

## Not modeled
Counterspells, instant-speed interaction, targeted discard, bounce, -X/-X, theft, opponents' responses, opponents attacking, commander damage, and any opponent choice beyond the script. The policies are stand-ins, not predictions of what a real opponent would do.
