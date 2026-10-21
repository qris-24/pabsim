# CP37 — A2 Kernel 1: combat and state-based actions (K1, K4, K9, K10, K12) (2026-10-21)

Kernel repair stage, applied by night\CP37_apply.py (deterministic; the fix was built and gated in a sandbox clone of rp-CP35; no Claude implementation session). Fixes are in the non-frozen layers pab_clock_s3.py, pab_cast_s6.py, pab_opponents_s8.py, pab_cast_s15.py, pab_combat_s17.py, pab_policy_s18.py and the S19 validation tool. No frozen file and no existing test expectation changed.

## Summary
- K1: lethal or deathtouch damage no longer destroys an indestructible creature (traced once per turn); a regeneration shield replaces it (CR 701.15a: shield used, damage removed, tapped, removed from combat); toughness 0 or less still kills.
- Found and fixed: regenerating a token through destroy() left its physical card untapped (bridge integrity failure); regeneration is one routine now.
- K4: one current power/toughness (Skullclamp +1/-1 per clamp, until-end-of-turn changes, attacking-Pest +1/+0) for the state-based check (event kernel and physical), combat, Tend the Pests' X and S18's removal choice. South Wind Avatar's lifegain still reads printed toughness (frozen file; follow-up).
- K9: opponents' generic bodies cannot block an attacker with flying (FLYING_NAMES, token kinds with flying); intrinsic menace (Sedgemoor Witch, Teacher's Pest) counts. A-S20-05 unchanged.
- K10: Carrion Feeder and Starscape Cleric never block under block_policy 'all'.
- K12: 21 commander damage makes the seat leave with its life unchanged (CR 704.6c); the S19 life replay and lost-seat check follow (lost_seats_ok; key name lost_seats_at_zero kept).
- Keyword name sets are checked against the pinned card data for the 30 old-baseline creatures; CLAUDE.md open queue lists them with HASTE_NAMES.
- Tests: tests/test_auditfix_cp37.py (21; 20 fail on rp-CP35); suite 882, release gate 21/21. KERNEL_VERSION/PROMOTED gain CP37.
- Note: EVIDENCE/CP31d_INTEGRITY_REVIEW.md line numbers for pab_combat_s17.py and pab_validation_s19.py do not match the files (K12 is pab_combat_s17.py:150, not :243).
- Follow-ups: S3 SBA trace label for lethal damage (K3/K6/K7 stage); South Wind Avatar toughness LKI (Stage C).
