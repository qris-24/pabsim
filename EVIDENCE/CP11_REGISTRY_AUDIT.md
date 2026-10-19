# CP11 — S20 model coverage registry verification

## Verdict counts

| Verdict | Cards |
|:--|--:|
| SUPPORTED | 86 |
| WEAK | 1 |
| UNSUPPORTED | 0 |
| OVERCLAIM | 0 |
| UNDERCLAIM | 1 |
| **Total** | **88** |

## Findings: OVERCLAIM / UNSUPPORTED / UNDERCLAIM

Only the requested discrepancy verdicts appear below; `WEAK` is counted but deliberately excluded from this findings table.

| Card | Verdict | Claim, code, test evidence and interpretation |
|:--|:--|:--|
| Infuse with Vitality | **UNDERCLAIM** | Registry `not_modeled`: deathtouch (no combat consequence modeled for the target). Literal code: `pab_cast_s15.py:106`. Name-in-source tests: `tests/test_auditfix_cp03.py; tests/test_auditfix_cp10.py; tests/test_c41_c47_contracts.py; tests/test_c78_c94_contracts.py; tests/test_cast_s15.py`. Additional implementation/tests: pab_auditfix_cp03.py:10-13 (_deathtouch checks infused_eot); pab_combat_s17.py:68-71,140 (deathtouch combat application); tests/test_auditfix_cp03.py:42-63 (combat lethal tests). **The not_modeled note says deathtouch has no modeled combat consequence, but CP03 adds the infused_eot deathtouch override; tests demonstrate lethal combat effects for either controller.** |

## Proposed corrections — approval required

1. **Propose (not applied):** Update the `Infuse with Vitality` entry in `build_model_coverage_s20.py`: add **deathtouch until end of turn, with lethal combat effects (CP03)** to `modeled`, and remove the obsolete `not_modeled` deathtouch note. Then regenerate `PABTRV3_MODEL_COVERAGE_S20.json`, re-pin and gate in a separately approved task.
2. **Propose (not applied):** Add an exact full-name assertion to `tests/test_lands_s9.py` for `Darkbore Pathway // Slitherbore Pathway` *if name-level grep coverage is required*. Existing `PATHWAY`-based tests already cover mechanics; this is a name-literal test discoverability gap, not proven rules defect.

## Scope and limits

The S20 registry continues to mark **88/88 PARTIAL and 0 CERTIFIED**, and the existing explicit partial-model gaps are not automatically OVERCLAIM. A name appearing in runtime code and a test does **not** establish every advertised ability is implemented, or official Oracle compliance. No kernel file, registry, or generator was edited in CP11.

Mechanical evidence, exact file/line references, modeled/unmodeled lists, test filenames, and verdict rationale for **each of the 88 names** are in `EVIDENCE/CP11_REGISTRY_AUDIT.json`.
