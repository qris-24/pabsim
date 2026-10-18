# CP03 — Independent audit repair A-S20-04 (Infuse deathtouch)

Parent: rp-CP02. Change scope: versioned `pab_auditfix_cp03.py` only; the
canonical kernel entrypoint imports this layer. The pre-existing S15 Infuse
registry is checked by combat `_deathtouch()` for **both controllers**. The
S15 cleanup code remains responsible for effect expiration.

Evidence: supplied `EVIDENCE/S15_SPELL_EVIDENCE.json` includes the text
"Until end of turn, target creature gains deathtouch". Not authenticated
against a live official Oracle feed.

Regression suite: `tests/test_auditfix_cp03.py`, seven cases: evidence,
resolution timing, both controllers, actual damage, cleanup, illegal target.
Existing `S15/S17/CP02` tests unchanged. No accepted deck, frozen file,
performance score, or optimizer changed.

Limit: opponent-owned creature Infuse return-on-death is still incompletely
modeled by S15. Combat remains without first/double strike, trample, or
real opponent priority windows. CP03 is not full MTG deathtouch certification.
