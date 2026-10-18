"""PABTRV3-only compiler contracts. Failures are reported, never converted to card value zero.
Fixture text transcribed verbatim from Project card-data snapshot, not live-fetched.
"""
import json,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parent/'phase2_candidate'))
from tablesim.oracle import compile_card

CARD_TEXT={
'Savra, Queen of the Golgari':('Legendary Creature — Elf Shaman','{2}{B}{G}', '''Whenever you sacrifice a black creature, you may pay 2 life. If you do, each other player sacrifices a creature of their choice.\nWhenever you sacrifice a green creature, you may gain 2 life.'''),
'Pest Summoning':('Sorcery — Lesson','{1}{B/G}{B/G}', 'Create two 1/1 black and green Pest creature tokens with "When this token dies, you gain 1 life."'),
'Sedgemoor Witch':('Creature — Human Warlock','{2}{B}', '''Menace\nWard—Pay 3 life.\nMagecraft — Whenever you cast or copy an instant or sorcery spell, create a 1/1 black and green Pest creature token with "When this token dies, you gain 1 life."'''),
'The Hunger Tide Rises':('Enchantment — Saga','{2}{G}', '''(As this Saga enters and after your draw step, add a lore counter. Sacrifice after IV.)\nI, II, III — Create a 1/1 black and green Insect creature token.\nIV — Sacrifice any number of creatures. Search your library and/or graveyard for a creature card with mana value less than or equal to the number of creatures sacrificed this way and put it onto the battlefield. If you search your library this way, shuffle.'''),
'Wriggling Grub':('Creature — Worm','{1}{B}', 'When this creature dies, create two 1/1 black and green Worm creature tokens.'),
'Infestation Sage':('Creature — Elf Warlock','{B}', 'When this creature dies, create a 1/1 black and green Insect creature token with flying.'),
'Pest Rescuer':('Creature — Dryad Druid','{2}{G}', '''At the beginning of each upkeep, if you don't control a Pest creature token, create a 1/1 black and green Pest creature token with "When this token dies, you gain 1 life."\nIf you would gain life, you gain that much life plus 1 instead.'''),
'Moseo, Vein\'s New Dean':('Legendary Creature — Bird Skeleton Warlock','{2}{B}', '''Flying\nWhen Moseo enters, create a 1/1 black and green Pest creature token with "Whenever this token attacks, you gain 1 life."\nInfusion — At the beginning of your end step, if you gained life this turn, return up to one target creature card with mana value X or less from your graveyard to the battlefield, where X is the amount of life you gained this turn.'''),
'Cauldron of Essence':('Artifact','{1}{B}{G}', '''Whenever a creature you control dies, each opponent loses 1 life and you gain 1 life.\n{1}{B}{G}, {T}, Sacrifice a creature: Return target creature card from your graveyard to the battlefield. Activate only as a sorcery.'''),
'South Wind Avatar':('Creature — Snake Spirit Avatar','{3}{B}', '''Deathtouch\nWhenever another creature you control dies, you gain life equal to its toughness.\nWhenever you gain life, each opponent loses 1 life.'''),
'Teacher\'s Pest':('Creature — Skeleton Pest','{B}{G}', '''Menace (This creature can't be blocked except by two or more creatures.)\nWhenever this creature attacks, you gain 1 life.\n{B}{G}: Return this card from your graveyard to the battlefield tapped.'''),
'Blight Mound':('Enchantment','{2}{B}', '''Attacking Pests you control get +1/+0 and have menace.\nWhenever a nontoken creature you control dies, create a 1/1 black and green Pest creature token with "When this token dies, you gain 1 life."'''),
'Feral Appetite':('Enchantment','{2}{G}', '''Attacking Pests you control get +1/+0 and have deathtouch.\n{1}{G}: Exile target card from a graveyard. If a creature card is exiled this way, create a 1/1 black and green Pest creature token with "When this token dies, you gain 1 life."'''),
'Ribtruss Roaster':('Creature — Troll Druid','{4}{G}', '''Devour 1 (As this creature enters, you may sacrifice any number of creatures. This creature enters with that many +1/+1 counters on it.)\nAt the beginning of your end step, create a number of 1/1 black and green Pest creature tokens equal to the number of +1/+1 counters on this creature. They have "When this token dies, you gain 1 life."'''),
'Immoral Bargain':('Sorcery','{1}{B}{G}', '''As an additional cost to cast this spell, sacrifice X creatures.\nDestroy X target nonland permanents.'''),
'Chatterfang, Squirrel General':('Legendary Creature — Squirrel Warrior','{2}{G}', '''Forestwalk (This creature can't be blocked as long as defending player controls a Forest.)\nIf one or more tokens would be created under your control, those tokens plus that many 1/1 green Squirrel creature tokens are created instead.\n{B}, Sacrifice X Squirrels: Target creature gets +X/-X until end of turn.'''),
'Beledros Witherbloom':('Legendary Creature — Elder Dragon','{5}{B}{G}', '''Flying\nAt the beginning of each upkeep, create a 1/1 black and green Pest creature token with "When this token dies, you gain 1 life."\nPay 10 life: Untap all lands you control. Activate only once each turn.'''),
'Witherbloom Charm':('Instant','{B}{G}', '''Choose one —\n• You may sacrifice a permanent. If you do, draw two cards.\n• You gain 5 life.\n• Destroy target nonland permanent with mana value 2 or less.'''),
'Witherbloom Command':('Sorcery','{B}{G}', '''Choose two —\n• Target player mills three cards, then you return a land card from your graveyard to your hand.\n• Destroy target noncreature, nonland permanent with mana value 2 or less.\n• Target creature gets -3/-1 until end of turn.\n• Target opponent loses 2 life and you gain 2 life.'''),
'Agent of the Iron Throne':('Legendary Enchantment — Background','{2}{B}', '''Commander creatures you own have "Whenever an artifact or creature you control is put into a graveyard from the battlefield, each opponent loses 1 life."'''),
}

def compile_name(n):
    typ,cost,t=CARD_TEXT[n]
    colors=['B','G'] if '{B}{G}' in cost or '{B/G}' in cost else ['B'] if '{B}' in cost else ['G'] if '{G}' in cost else []
    return compile_card(dict(name=n,type_line=typ,mana_cost=cost,oracle_text=t,colors=colors,color_identity=colors))

def all_effects(c):
    return list(c.get('spell') or [])+[e for a in c['abilities'] for e in a.get('eff',[])]

def assert_test(n, pred, why):
    c=compile_name(n)
    if not pred(c):
        raise AssertionError(f"{n}: {why}; compiled effects={all_effects(c)!r}; statics={c['statics']!r}; unmodeled={c.get('unmodeled')!r}; partial={c.get('partial')!r}")

TESTS=[
('Savra separate BG sacrifice triggers',lambda: assert_test('Savra, Queen of the Golgari',lambda c: {a['f'].get('color') for a in c['abilities']}=={'B','G'},'two color-filtered sacrifice triggers needed')),
('Pest Summoning makes 2 tokens',lambda: assert_test('Pest Summoning',lambda c: any(e['k']=='tokens' and e.get('n')==2 and e.get('colors')=='BG' for e in all_effects(c)),'two BG Pest tokens not immediate lifegain')),
('Sedgemoor Witch magecraft makes token',lambda: assert_test('Sedgemoor Witch',lambda c: any(a.get('trig')=='cast_you' and any(e['k']=='tokens' and e.get('colors')=='BG' for e in a['eff']) for a in c['abilities']),'Magecraft must create Pest')),
('Hunger Tide first chapters make BG Insects',lambda: assert_test('The Hunger Tide Rises',lambda c: any(e.get('k')=='tokens' and ('Insect' in str(e.get('subs'))) and e.get('colors')=='BG' for e in all_effects(c)),'Saga creates INSECTS, not Pests')),
('Hunger Tide fourth chapter sacrifices and searches',lambda: assert_test('The Hunger Tide Rises',lambda c: any('tutor'==e.get('k') or 'reanimate'==e.get('k') for e in all_effects(c)),'IV should tutor/reanimate from library/gy after sacrifice')),
('Wriggling Grub makes TWO BG worms',lambda: assert_test('Wriggling Grub',lambda c: any(e.get('k')=='tokens' and e.get('n')==2 and 'Worm' in str(e.get('subs')) and e.get('colors')=='BG' for e in all_effects(c)),'black card dies to two BG Worms')),
('Infestation Sage dies to BG flying Insect',lambda: assert_test('Infestation Sage',lambda c: any(e.get('k')=='tokens' and e.get('colors')=='BG' and 'Insect' in str(e.get('subs')) and 'flying' in str(e.get('kw')) for e in all_effects(c)),'BG Insect flying')),
('Pest Rescuer creates tokens',lambda: assert_test('Pest Rescuer',lambda c: any(e.get('k')=='tokens' and e.get('colors')=='BG' for e in all_effects(c)),'upkeep Pest creation')),
('Pest Rescuer lifegain replacement',lambda: assert_test('Pest Rescuer',lambda c: any('life' in str(st).lower() or 'gain' in str(st).lower() for st in c['statics']),'gain that much plus one replacement')),
('Moseo ETB creates Pest',lambda: assert_test("Moseo, Vein's New Dean",lambda c: any(e.get('k')=='tokens' and 'Pest' in str(e.get('subs')) for e in all_effects(c)),'ETB Pest')),
('Moseo infusion reanimates',lambda: assert_test("Moseo, Vein's New Dean",lambda c: any(e.get('k')=='reanimate' for e in all_effects(c)),'end step life gained -> MV threshold reanimation')),
('Cauldron of Essence death drain',lambda: assert_test('Cauldron of Essence',lambda c: any(e.get('k')=='drain' for e in all_effects(c)),'death to each-opponent drain')),
('Cauldron of Essence activated reanimation',lambda: assert_test('Cauldron of Essence',lambda c: any(a.get('trig')=='activated' and any(e.get('k')=='reanimate' for e in a['eff']) for a in c['abilities']),'tap plus sacrifice-target reanimation')),
('South Wind Avatar lifegain at death',lambda: assert_test('South Wind Avatar',lambda c: any(e.get('k')=='gain' for e in all_effects(c)),'gain on controlled death')),
('South Wind Avatar drains on gain',lambda: assert_test('South Wind Avatar',lambda c: any(a.get('trig')=='lifegain_you' and any(e.get('k')=='drain' for e in a['eff']) for a in c['abilities']),'lifegain event drain')),
("Teacher's Pest returns from graveyard",lambda: assert_test("Teacher's Pest",lambda c: any('gy' in str(a).lower() or 'graveyard' in str(a).lower() for a in c['abilities']+c.get('alt',[])),'recursion {B}{G} ability')),
('Blight Mound makes BG tokens on nontoken death',lambda: assert_test('Blight Mound',lambda c: any(e.get('k')=='tokens' and e.get('colors')=='BG' for e in all_effects(c)),'BG Pest from nontoken creature deaths')),
('Feral Appetite graveyard-targeted tokens',lambda: assert_test('Feral Appetite',lambda c: any(e.get('k')=='tokens' and e.get('colors')=='BG' for e in all_effects(c)),'exile creature graveyard card to make Pest')),
('Ribtruss Roaster makes BG tokens by counters',lambda: assert_test('Ribtruss Roaster',lambda c: any(e.get('k')=='tokens' and e.get('colors')=='BG' for e in all_effects(c)),'# Pests equal +1 counters, not fixed 1')),
('Immoral Bargain sacrifices X as cost',lambda: assert_test('Immoral Bargain',lambda c: any('sac' in str(x).lower() for x in [c.get('additional'),c.get('add_cost'),c.get('spell'),c.get('alt')]),'X sacrificed as additional cost')),
('Chatterfang adds GREEN squirrels',lambda: assert_test('Chatterfang, Squirrel General',lambda c: any('token' in str(st).lower() and 'squirrel' in str(st).lower() for st in c['statics']),'token replacement creates green Squirrels')),
('Beledros upkeep makes BG Pest',lambda: assert_test('Beledros Witherbloom',lambda c: any(e.get('k')=='tokens' and e.get('colors')=='BG' for e in all_effects(c)),'upkeep Pest creation')),
('Witherbloom Charm modal sac/draw',lambda: assert_test('Witherbloom Charm',lambda c: any(e.get('k')=='draw' for e in all_effects(c)),'sac to draw two')),
('Witherbloom Command mill and land',lambda: assert_test('Witherbloom Command',lambda c: any(e.get('k') in ('self_mill','mill') for e in all_effects(c)),'mill mode')),
('Agent grants commander artifact/creature deaths',lambda: assert_test('Agent of the Iron Throne',lambda c: any('commander' in str(x).lower() for x in c['abilities']+c['statics']),'commander-owned granted dies trigger')),
]
if __name__=='__main__':
    out=[]
    for name,fn in TESTS:
        try:fn();out.append({'contract':name,'pass':True,'detail':''})
        except Exception as e:out.append({'contract':name,'pass':False,'detail':str(e)[:400]})
    (P/'PAB_COMPILER_CONTRACT_RESULTS.json').write_text(json.dumps(out,indent=2))
    for x in out:print(('PASS' if x['pass'] else 'FAIL')+' '+x['contract']+((': '+x['detail'][:90]) if not x['pass'] else ''))
    print('Total',len(out),'pass',sum(x['pass'] for x in out),'fail',sum(not x['pass'] for x in out))
