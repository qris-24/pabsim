"""Build-only coverage registry generator (R02 patch).

Importing this module has NO side effects. `build()` returns the registry;
`canonical_bytes()` serialises it deterministically (sorted keys, fixed indent,
trailing newline). Only `python build_registry.py` writes to disk. The release
runner never calls the writer; it regenerates in memory and compares bytes.
"""
import csv, json, hashlib, re
from collections import Counter
from pathlib import Path
from pab_focus_engine import BODIES, SAVRA

HERE=Path(__file__).resolve().parent
REGISTRY_NAME='PABTRV3_CARD_COVERAGE.json'

def canonical_bytes(obj):
    """Deterministic serialisation: key order and whitespace fixed regardless of
    filesystem or dict insertion order."""
    return (json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode('utf-8')

def build(here=HERE):
    """Return {'summary':..., 'cards':...}. Pure: reads only, never writes."""
    source=here/'upstream_frozen'
    with (source/'PABTRV3_MECHANICAL_INVENTORY.csv').open(encoding='utf-8') as fh:
        rows=list(csv.DictReader(fh))
    main=[r for r in rows if r['section']=='Mainboard']
    assert sum(int(r['count']) for r in main)==99
    assert sum(int(r['count']) for r in main if r['group']=='land')==34
    assert sum(int(r['count']) for r in main if r['group']=='nonland')==65
    assert len([r for r in rows if r['group']=='commander'])==1
    assert len([r for r in rows if r['group']=='lesson'])==1
    assert next(r for r in rows if r['group']=='commander')['name']==SAVRA
    assert next(r for r in rows if r['group']=='lesson')['name']=='Pest Summoning'

    # A partial reference capability only. Never mistake this for full-card resolution.
    partial={
     SAVRA,'Dina, Soul Steeper','Pest Rescuer','Chatterfang, Squirrel General',
     "Moseo, Vein's New Dean",'Bastion of Remembrance','Cauldron of Essence',
     'Reassembling Skeleton',"Teacher's Pest",'Infestation Sage',
     'Wriggling Grub','Sedgemoor Witch','Beledros Witherbloom',
     'Ribtruss Roaster','South Wind Avatar','Agent of the Iron Throne',
     'Deathgreeter','Blood Artist','Poison-Tip Archer','Marauding Blight-Priest',
     'Starscape Cleric','Moldervine Reclamation','Dark Prophecy','Grave Pact',
     'Prosperous Innkeeper','Essence Warden','Blight Mound','Feral Appetite',
     'Mirkwood Bats','Village Rites','Diabolic Intent','Deadly Dispute',
     'Tend the Pests','Immoral Bargain','Hunt for Specimens','Pest Summoning',
     'The Hunger Tide Rises', 'Bogwater Lumaret','Sangromancer',
     'Carrion Feeder','Viscera Seer','Warren Soultrader','Phyrexian Reclamation',
     'Yawgmoth, Thran Physician','Yahenni, Undying Partisan',
     'Phyrexian Altar','Plumb the Forbidden',
     'Arcane Signet','Golgari Signet','Sol Ring','Sakura-Tribe Elder',
     "Nature's Lore",'Pest Infestation','Unearth','Skullclamp','Demonic Tutor'
    }
    # Actual standalone behavior contracts do not exhaust full text even for partial cards.
    entry=[]
    for row in rows:
        land=row['group']=='land'
        status=('SOURCE_AUDIT_PENDING' if land else
                'PARTIAL_REFERENCE_TESTED' if row['name'] in partial else
                'NOT_IN_REFERENCE_KERNEL')
        entry.append({
            'section':row['section'], 'quantity':int(row['count']),
            'name':row['name'], 'group':row['group'],
            'reported_mechanical_role':row['mechanical_role'],
            'reported_rules_contract':row['rules_contract'],
            'text_provenance':row['source_status'],
            'status':status, 'full_card_behavior_verified':False,
            'value_for_optimization':None
        })
    status_counts=dict(Counter(x['status'] for x in entry))

    # Preserve fact that the 25 old compiler contracts did NOT pass.
    old_contracts=json.loads((source/'PAB_COMPILER_CONTRACT_RESULTS.json').read_text())
    assert len(old_contracts)==25
    summary={
      'source':'PABTRV3 focus audit ZIP, recorded card snapshot text (not independently verified live Oracle)',
      'mainboard_count':99, 'commander_count':1, 'sideboard_count':1,
      'land_count':34,'nonland_count':65,
      'reference_coverage_status_counts':status_counts,
      'full_verified_cards':0,
      'old_compiler_25_contract_passes':sum(t['pass'] for t in old_contracts),
      'old_compiler_25_contract_failures':sum(not t['pass'] for t in old_contracts),
      'current_reference_test_count':sum(len(re.findall(r'^\s+def test_',f.read_text(encoding='utf-8'),re.M)) for f in sorted((here/'tests').glob('test_*.py'))),  # static count; no test-module imports
      'new_reference_changes_from_v05':'v0.6 added 56 physical-zone fixtures; v0.7 added 52 opt-in bridge fixtures; v0.8 adds 54 shared-mana and token-identity fixtures; R01 adds 13 Pest Rescuer token-predicate controls (11 run on both kernel and bridge) and 2 promoted corrections. All coverage values are partial.',
      'kernel_version':'v0.8+R02+R01+R47+R48+R49+S1+S2+S3+S4+S5+S6+R52+R53+S7+S8+S9+S10',
      'promoted_patches':["R02", "R01", "R47", "R48", "R49", "S1", "S2", "S3", "S4", "S5", "S6", "R52", "R53", "S7", "S8", "S9", "S10"],
      'r01_pest_rescuer_token_predicate_promoted':True,
      'superseded_frozen_contracts':['test_112_teacher_pest_blocks_rescuer_at_upkeep_start','test_113_teacher_pest_entered_before_rescuer_trigger_resolves','test_91_village_rejects_mana_shortage_before_sac'],
      'superseded_frozen_v08_fixtures_s9':['test_274_unsupported_land_fails_closed','test_307_unsupported_named_nonbasic_mana_does_not_fallback'],
      'pest_rescuer_text_independently_authenticated':False,
      'contracts_executed_against_kernel':['C41','C42','C43','C44','C45','C46','C47','C48','C49','C51','C52','C53','C54','C55','C56','C57','C58','C59','C60','C61','C63','C64','C65','C66','C67','C68','C69','C73','C77','C78','C79','C87'],
      'contracts_blocked_unsupported':['C50','C62','C70','C71','C72','C74','C75','C76','C80','C81','C82','C83','C84','C85','C86','C88','C89','C90','C91','C92','C93','C94'],
      'unsupported_land_names_verified_fail_closed':18,   # frozen zones path; S9 bridge: 9 still fail closed
      'pest_rescuer_text_checked_against_two_web_sources_2026_10_18':'Aetherhub and EchoMTG both read "if you don\'t control a Pest creature token"; still not an official Oracle feed',
      'cr_evidence':'EVIDENCE/CR_20260619_EVIDENCE.json (MagicCompRules 20260619, official PDF)',
      'issue_r49_status':'PROMOTED (LKI fallback in pab_r47_r48_sba.py)',
      'cast_from_hand_stage':'S6 promoted: cast_from_hand() on the physical bridge for Village Rites, Deadly Dispute, Tend the Pests, Nature\'s Lore, Sakura-Tribe Elder (pab_cast_s6.py); clock-derived timing, shared-pool mana, card leaves hand on resolution; all other names fail closed',
      'commander_stage_s10':'S10 promoted: Savra cast from the command zone with commander tax (pab_commander_s10.py); on death she goes to the graveyard (dies triggers fire) and returns to the command zone at the next SBA check (CR 903.9a, fixed policy); fixture add(SAVRA) path untouched; EVIDENCE/S10_COMMANDER_EVIDENCE.json (903.x from a secondary transcription)',
      'fixer_lands_stage_s9':'S9 promoted: the nine B/G-producing nonbasic lands playable and tappable on the physical bridge (pab_lands_s9.py) with their entry conditions, Pathway faces, Mortuary surveil, Wastes damage and Peatland life (EVIDENCE/S9_LAND_EVIDENCE.json); the other nine nonbasics still fail closed; frozen SUPPORTED_LAND_MANA untouched',
      'opponents_stage_s8':'S8 promoted: opponents as life totals + a fixed scripted board declared at game start (pab_opponents_s8.py); Savra-black and Grave Pact edicts resolve against real opposing creatures by a fixed policy (lowest power, toughness, uid); opponent_sacrifices counts observed sacrifices only; opponent deaths reach the frozen own-card triggers with frozen labels; seats at 0 life leave the game and the clock skips their later turns (CR 800.4a/g); opponents never act',
      'cast_from_hand_stage_s7':'S7 promoted: cast_from_hand() extended to the 27 other creature names in BODIES (pab_cast_s7.py): printed costs/P/T/colours from EVIDENCE/S7_CARD_EVIDENCE.json; hand->battlefield through the frozen add()+linked path so ETB behaviour is the frozen kernel\'s; Ribtruss Roaster devour via devour_uids (CR 702.82); Starscape Cleric Offspring, the legend rule, keywords and combat not modeled; lands, Savra, noncreatures and the Lesson still fail closed',
      'card_oracle_evidence_s7':'EVIDENCE/S7_CARD_EVIDENCE.json (user-provided Scryfall bulk export 2026-10-17 via the audit reference JSON; scryfall.com unreachable from the build environment on 2026-10-18; not Wizards official feed)',
      'issues_r52_r53_r54_status':'PROMOTED 2026-10-18: R52 Village Rites costs {B} (pab_r52_village_rites.py; frozen test_91 superseded, corrected copy r52_tests/); R53 pab_turn_loop.opening_hand() shuffles first (CR 103.3); R54 S5 land-play test compared against a trace key never emitted into g.trace and passed vacuously — fixed and made non-vacuous',
      'card_oracle_evidence_s6':'EVIDENCE/S6_CARD_EVIDENCE.json (scryfall.com card pages 2026-10-18; not Wizards official feed)',
      'integrated_turn_loop':'S5 promoted: pab_turn_loop.py drives whole turns over existing capabilities with invariants checked at every boundary and action (8 seeds, up to 30 turns); no casting from the physical hand, no opponents',
      'phase_clock_stage':'S4 promoted: untap step, draw step, land-play window on event kernel and physical bridge (pab_clock_s4.py); clock stages S1–S4 complete',
      'phase_clock_stage_history_s3':'S3 promoted: SBA between resolutions with look-back, retired inline Yawgmoth check, set_trigger_order() (pab_clock_s3.py); S4 not authorized',
      'phase_clock_stage_history':'S2 promoted: boundaries drive each-upkeep, controller end step, mana emptying, cleanup expiry (pab_clock_s2.py); S3–S4 not authorized',
      'issues_r50_r51_status':'CLOSED: S2 (upkeep/end/cleanup/mana) + S4 (untap/draw/land-play reset)',
      'contracts_c95_c99_status':'C95, C96, C98, C99 EXECUTED (tests/test_turn_clock_s2.py); C97 EXECUTED_WITH_SUBSTITUTION (tests/test_priority_s3.py)',
      'issues_r50_r51_design_only_historical':['R50: no active player/step clock; each-upkeep and your-end-step scoping is caller discipline','R51: mana pools never empty (CR 106.4)'],
      'proposed_contracts_c95_c99':'EVIDENCE/PROPOSED_CONTRACTS_C95_C99.json (PROPOSED_NOT_EXECUTED)',
      'phase_clock_design':'PHASE_CLOCK_DEPENDENCY_MAP.md (design only; implementation not authorized)',
      'issues_r47_r48_status':'PROMOTED (fixed in pab_r47_r48_sba.py; frozen v0.7 behaviour pinned in C61/C79 tests)',
      'new_issues_observed_design_only':['R47: Ribtruss Roaster end-step trigger snapshots +1/+1 counter count at trigger time; contract C61 expects the count at resolution (CR 608.2h). Unapproved; no code change.',
                                         'R48: the Yawgmoth -1/-1 state-based death path calls destroy(), so an indestructible creature at toughness 0 wrongly survives; contract C79 expects death (CR 704.5f; the Skullclamp path uses _leave directly and is correct). Unapproved; no code change.'],
      'contracts_c41_c94_all_executed_or_probed':True,
      'contract_execution_status_source':'VALIDATION_RESULTS.json: contracts_executed (EXECUTED vs EXECUTED_WITH_SUBSTITUTION, with substitutions listed)',
      'contracts_oracle_cr_authenticated':0,
      'explicit_mana_reference_only':True,
      'full_land_engine':False,
      'limited_land_names_implemented':['Forest','Swamp','Command Tower'],   # frozen zones path; S9 adds nine on the bridge (see fixer_lands_stage_s9)
      'nonbasic_land_names_without_play_implementation':9,   # S9: was 18
      'nonbasic_land_names_without_play_implementation_frozen_zones_path':18,
      'basic_land_fixture_only':True,
      'real_library_in_separate_zone_prototype':True,
      'old_event_kernel_still_has_no_real_draw_or_library_zone':True,
      'full_casting_engine':False,
      'full_stack_and_priority_engine':False,
      'opponent_exogenous_events_only':True,
      'new_module_is_patch_to_original_engine':False,
      'zones_integrated_with_event_engine':False,
      'bounded_opt_in_zone_event_bridge':True,
      'phase8_shared_mana_pool_fixture':True,
      'phase8_mirrored_event_tokens':True,
      'phase8_full_mana_token_engine':False,
      'physical_bridge_full_board_reconciliation':False,
      'event_candidate_five_draw_call_sites_normalized':True,
      'replacement_optimization_allowed':False,
      'learn_sideboard_default':False,
      'land_exact_card_text_complete':False,
      'colorless_nonland_exact_card_text_complete':False,
      'source_hashes_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source.iterdir()) if p.is_file()}
    }
    return {'summary':summary,'cards':entry}

def main():
    data=build()
    (HERE/REGISTRY_NAME).write_bytes(canonical_bytes(data))
    print(json.dumps(data['summary'],indent=2,sort_keys=True))

if __name__=='__main__':
    main()
