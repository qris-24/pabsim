# S16 — Grist, the Hunger Tide (2026-10-18)

Kernel `…+S15+S16`. New layer `pab_grist_s16.py` (`GristMixin`, above `InteractionSpellsMixin`; PhysicalZoneGame only). 711 reference fixtures (703 + 8). No frozen file edited. Deck, Lesson, Phase 9, sweeps and rankings unchanged. With S16 every one of the 65 nonland cards and all 34 lands have a modeled path from the physical zones.

## What was built
- Cast {1}{B}{G} at sorcery speed; enters as a noncreature permanent with `loyalty` 3 (its own attribute, not the +1/+1 counter field); linked to the physical card. `EVIDENCE/S16_PLANESWALKER_EVIDENCE.json`.
- Loyalty abilities (CR 606): once per turn, controller's main phase, empty stack; the loyalty change is paid as the cost at once; the ability resolves from the stack. +1 (Insect token, mill one; the "Insect card milled → loyalty and repeat" loop is implemented but cannot fire in this deck — Grist is its only Insect card and cannot be milled while on the battlefield). −2 (optional sacrifice through the frozen `sacrifice()`; a reflexive trigger destroys the chosen creature or planeswalker, re-checked at resolution). −5 (each opponent loses life equal to the creature cards in your graveyard — and Grist at 0 loyalty is already there when the ability resolves, so she counts herself; this is the paper outcome).
- CR 704.5i: zero loyalty → graveyard as a state-based action. Leaving the battlefield keeps an event-kernel LKI with `creature=True`, MV 3, so the static "a 1/1 Insect creature when not on the battlefield" holds where the kernel looks: Unearth / Takenuma / Rise / Grisly Salvage treat the card as a creature card; the frozen `_return_creature_from_graveyard` is overridden so she re-enters as a planeswalker. `grist_graveyard_lki()` creates the LKI for a Grist that was milled or discarded.
- Abrupt Decay (MV 3) can destroy her; scripted creature removal, edicts and board wipes ignore her (she is not a creature on the battlefield).

## Not modeled
Opponents attacking Grist (no combat), responses to loyalty abilities, Grist as a creature spell on the stack (nothing in the kernel cares).

## Earlier-stage tests re-scoped (R54-style, not frozen)
The S6 fail-closed sweep now skips Grist; the S15 "Grist still fails closed" probe became a kw-timing refusal.
