# CP38 — A2 Kernel 2: interaction and policy (K2, K5, K8, K11, K13) (2026-10-21)

Kernel repair stage, applied by night\\CP38_apply.py (deterministic; the fix was built and gated in a sandbox clone of rp-CP37; no Claude implementation session). Fixes are in the non-frozen layers pab_opponents_s8.py, pab_interaction_s11.py, pab_cast_s13.py, pab_lands_s14.py, pab_cast_s15.py, pab_grist_s16.py, pab_policy_s18.py and pab_shigeki_s20.py. No frozen file and no existing test expectation changed.

## Summary
- K2: the scripted board wipe regenerates a creature with a regeneration shield instead of destroying it (CR 701.15a; tokens' physical cards tapped too); indestructible creatures survive and keep their shield.
- K5: with exile_instead, the S18 "Savra on the battlefield" removal exiles Savra (new policy-only action exile_commander; the six scripted KINDS are unchanged).
- K8: Shigeki counts as a creature card and a legendary creature: Takenuma's cost and return (Grist too, a planeswalker card), Grisly Salvage, Rise of the Witch-king's return (Shigeki's own 1/3 enchantment body), Grist -5, the S13 tutor policy (Grist too).
- K11: the scripted edict, the removal target policy, the opponents' edict choice and the S15 driver's Decay/Trophy target and Golgari Charm count read current power/toughness; found during CP38: the removal hit a different creature than the one S18's reason named.
- K13: Shigeki returning itself to hand unattaches Skullclamp.
- Tests: tests/test_auditfix_cp38.py (18; 17 fail on rp-CP37); suite 900, release gate 21/21. KERNEL_VERSION/PROMOTED gain CP38.
- Follow-ups: S19 seed 32 stack-ledger error under an all-exile policy (K7 class, pre-existing on other seeds); the S20 model-coverage file's Takenuma note.
