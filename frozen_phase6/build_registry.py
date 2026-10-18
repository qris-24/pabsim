"""Build conservative coverage registry from the frozen external audit inventory."""
import csv, json, hashlib, shutil, ast, unittest
from collections import Counter
from pathlib import Path
from pab_focus_engine import BODIES, SAVRA

here=Path(__file__).resolve().parent
source=here/'upstream_frozen'
rows=list(csv.DictReader((source/'PABTRV3_MECHANICAL_INVENTORY.csv').open(encoding='utf-8')))
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
  'current_reference_test_count':unittest.defaultTestLoader.discover(str(here/'tests'),pattern='test_*.py').countTestCases(),
  'new_reference_changes_from_v05':'56 additional tests; opt-in physical card zones, deterministic real library searches, limited three-name land fixtures and Demonic Tutor resolution only',
  'explicit_mana_reference_only':True,
  'full_land_engine':False,
  'limited_land_names_implemented':['Forest','Swamp','Command Tower'],
  'nonbasic_land_names_without_play_implementation':18,
  'basic_land_fixture_only':True,
  'real_library_in_separate_zone_prototype':True,
  'old_event_kernel_still_has_no_real_draw_or_library_zone':True,
  'full_casting_engine':False,
  'full_stack_and_priority_engine':False,
  'opponent_exogenous_events_only':True,
  'new_module_is_patch_to_original_engine':False,
  'zones_integrated_with_event_engine':False,
  'replacement_optimization_allowed':False,
  'learn_sideboard_default':False,
  'land_exact_card_text_complete':False,
  'colorless_nonland_exact_card_text_complete':False,
  'source_hashes_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source.iterdir() if p.is_file()}
}
(here/'PABTRV3_CARD_COVERAGE.json').write_text(json.dumps({'summary':summary,'cards':entry},indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
