"""S20 (2026-10-18): per-card model-coverage registry for PABTRV3.

Project rule: every card must have its relevant mechanical contribution represented, or be
explicitly marked as insufficiently modeled — and no card may be scored as if unmodeled parts
were zero. This script builds PABTRV3_MODEL_COVERAGE_S20.json: for each of the 100 cards and
the Lesson, what the kernel (frozen v0.5–v0.8 + R01–R55 + S1–S19) models, what it does NOT,
the stage that gave the card its physical path, and a status. No card is CERTIFIED: that
needs independent verification against the official Oracle/CR feed, which this package does
not have (all card text is from the user's Scryfall bulk export). `value_for_optimization` is
null everywhere: this registry describes coverage, never worth.

Importing has no side effects; `python build_model_coverage_s20.py` writes the file; the
S20 test regenerates it in memory and requires byte identity.
"""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
NAME='PABTRV3_MODEL_COVERAGE_S20.json'

L='land'; C='creature'; S='spell'; P='permanent'
BASIC_NOT=['nothing: a basic land is fully modeled except that the frozen zones path (not the bridge) is the one that plays it']
def card(kind,stage,modeled,not_modeled,status='PARTIAL'): return {'kind':kind,'physical_path_stage':stage,'modeled':modeled,'not_modeled':not_modeled,'status':status,'value_for_optimization':None,'certified':False}

CARDS={
 # ---- commander ----
 'Savra, Queen of the Golgari':card(C,'S10',['cast from the command zone with commander tax','black-sacrifice trigger: pay 2 life, real edict against opposing boards (S8 policy)','green-sacrifice trigger: gain 2','dies -> graveyard (dies triggers) -> command zone at the next SBA (903.9a)','attacks, commander damage (903.10a)','targeted by scripted/policy removal; hexproof via Heroic Intervention'],['choosing to leave her in the graveyard','partner / commander damage from other sources']),
 # ---- creatures ----
 'Dina, Soul Steeper':card(C,'S7',['cast','lifegain drain (frozen)','Dina pump activation (frozen fixture)'],['menace/combat use of the pump beyond the frozen fixture']),
 'Mirkwood Bats':card(C,'S7',['cast','token created/sacrificed drain (frozen)','flying body attacks'],['flying as evasion (opponents have no flyers; blocks ignore flying)']),
 'Pest Rescuer':card(C,'S7',['cast','each-upkeep conditional Pest (R01, S2 clock)','lifegain +1 replacement (frozen)'],['Oracle text not from an official feed (flagged since R01)']),
 'Chatterfang, Squirrel General':card(C,'S7',['cast','token-creation replacement (frozen)','{B} sacrifice-X activation (frozen fixture)'],['forestwalk']),
 "Moseo, Vein's New Dean":card(C,'S7',['cast','ETB attack-gain Pest (frozen)','end-step Infusion reanimation (frozen, S2 clock)','flying body attacks'],['flying as evasion']),
 'Reassembling Skeleton':card(C,'S7',['cast','{1}{B} graveyard return tapped (frozen)'],[]),
 "Teacher's Pest":card(C,'S7',['cast','Pest subtype for Pest Rescuer (R01)','attack-gain (S17)','{B}{G} graveyard return tapped (frozen)'],['menace as evasion']),
 'Infestation Sage':card(C,'S7',['cast','dies -> flying Insect (frozen)'],['flying as evasion']),
 'Wriggling Grub':card(C,'S7',['cast','dies -> two Worms (frozen)'],[]),
 'Sedgemoor Witch':card(C,'S7',['cast','Magecraft Pest on every instant/sorcery cast or copy (frozen)'],['menace','ward (no opponent targeting of our permanents is a spell/ability with a cost; policy removal ignores ward)']),
 'Beledros Witherbloom':card(C,'S7',['cast','each-upkeep Pest (frozen, S2 clock)','flying body attacks'],['pay 10 life: untap lands']),
 'Ribtruss Roaster':card(C,'S7',['cast with devour (CR 702.82)','end-step Pests equal to +1/+1 counters (R47/R49)'],[]),
 'South Wind Avatar':card(C,'S7',['cast','another creature dies -> gain toughness (frozen)','lifegain drain (frozen)','deathtouch in combat (S17)'],[]),
 'Deathgreeter':card(C,'S7',['cast','another creature dies -> may gain 1 (frozen; opposing deaths via S8)'],[]),
 'Blood Artist':card(C,'S7',['cast','any creature dies -> target loses 1, gain 1 (frozen; target = lowest seat in the game, S8)'],['free choice of target player']),
 'Poison-Tip Archer':card(C,'S7',['cast','another creature dies -> each opponent loses 1 (frozen)','deathtouch in combat (S17)'],['reach (opponents have no flyers)']),
 'Marauding Blight-Priest':card(C,'S7',['cast','lifegain drain (frozen)'],[]),
 'Starscape Cleric':card(C,'S7',['cast for the printed cost','lifegain drain (frozen)'],['Offspring {2}{B} (token copy)','flying','can\'t block (blocks policy would need it)']),
 'Prosperous Innkeeper':card(C,'S7',['cast','ETB Treasure (frozen)','another creature you control enters -> gain 1 (frozen)'],[]),
 'Essence Warden':card(C,'S7',['cast','another creature enters (any controller, incl. opponents\' bodies) -> gain 1 (frozen)'],[]),
 'Warren Soultrader':card(C,'S7',['cast','pay 1 life + sacrifice -> Treasure (frozen fixture)'],[]),
 'Carrion Feeder':card(C,'S7',['cast','sacrifice -> +1/+1 counter (frozen fixture)'],['can\'t block']),
 'Viscera Seer':card(C,'S7',['cast','sacrifice -> scry 1 (frozen fixture; scry not applied to the physical library)'],['scry on the real library']),
 'Bogwater Lumaret':card(C,'S7',['cast','this or another creature you control enters -> gain 1 (frozen)'],[]),
 'Sangromancer':card(C,'S7',['cast','opposing creature dies -> may gain 3 (frozen; S8 deaths)','opponent discards -> gain 3 (frozen exogenous only)'],['flying','opponents never discard (no hands)']),
 'Yawgmoth, Thran Physician':card(C,'S7',['cast','pay 1 life + sacrifice -> -1/-1 counter + draw (frozen, R48 SBA)','proliferate (frozen fixture)'],['protection from Humans']),
 'Yahenni, Undying Partisan':card(C,'S7',['cast','opposing creature dies -> +1/+1 counter (frozen; S8 deaths)','sacrifice -> indestructible until end of turn (frozen; cleared every cleanup since S15)','haste (S17)'],[]),
 'Sakura-Tribe Elder':card(C,'S6',['cast','sacrifice -> basic land tapped (frozen bridge)'],['nonbasic search is not what the card does; nothing missing']),
 'Shigeki, Jukai Visionary':card(C,'S20',['cast as a 1/3 enchantment creature (found missing from every frozen table while building this registry)','{1}{G}, T, return to hand: reveal four, a land tapped, rest to graveyard','channel {X}{X}{G}{G}: X nonlegendary cards from graveyard to hand'],['summoning-sick activation is refused (correct); nothing else']),
 # ---- noncreature permanents ----
 'Bastion of Remembrance':card(P,'S12',['cast','ETB Human Soldier (frozen)','creature you control dies -> drain/gain (frozen)'],[]),
 'Agent of the Iron Throne':card(P,'S12',['cast','commander grants: artifact or creature you control to graveyard from the battlefield -> each opponent loses 1 (frozen)'],['Background rules beyond the granted ability']),
 'Moldervine Reclamation':card(P,'S12',['cast','creature you control dies -> gain 1 and draw (frozen)'],[]),
 'Skullclamp':card(P,'S12',['cast','equip and +1/-1 with death draw 2 (frozen fixture)'],['equip from the cast path (enters unattached)']),
 'Phyrexian Altar':card(P,'S12',['cast','sacrifice -> one mana (frozen fixture)'],[]),
 'Cauldron of Essence':card(P,'S12',['cast','creature you control dies -> drain/gain (frozen)'],['{1}{B}{G}, T, sacrifice: reanimate (frozen fixture only)']),
 'Grave Pact':card(P,'S12',['cast','creature you control dies -> real edict against opposing boards (S8)'],[]),
 'Arcane Signet':card(P,'S12',['cast','mana rock (frozen fixture)'],[]),
 'Golgari Signet':card(P,'S12',['cast','{1}, T -> {B}{G} (frozen fixture)'],[]),
 'Sol Ring':card(P,'S12',['cast','{C}{C} (frozen fixture)'],[]),
 'Phyrexian Reclamation':card(P,'S12',['cast','{1}{B}, pay 2 life: creature card graveyard -> hand (frozen bridge)'],[]),
 'Dark Prophecy':card(P,'S12',['cast','creature you control dies -> draw, lose 1 (frozen)'],[]),
 'Feral Appetite':card(P,'S12',['cast','attacking Pests +1/+0 and deathtouch (S17)','{1}{G}: exile card from a graveyard -> Pest (frozen fixture)'],[]),
 'Blight Mound':card(P,'S12',['cast','nontoken creature you control dies -> Pest (frozen)','attacking Pests +1/+0 and menace (S17)'],[]),
 'The Hunger Tide Rises':card(P,'S12',['cast','chapters I–III Insects, IV sacrifice/search (frozen saga, S2 clock)'],['chapter IV search against the physical library (frozen fixture semantics)']),
 # ---- spells ----
 'Village Rites':card(S,'S6',['cast with sacrifice cost, draw 2 (R52 cost)'],[]),
 'Deadly Dispute':card(S,'S6',['cast with artifact/creature sacrifice, draw 2 + Treasure'],[]),
 'Tend the Pests':card(S,'S6',['cast with sacrifice, X Pests by LKI power'],[]),
 "Nature's Lore":card(S,'S6',['cast, basic Forest to the battlefield untapped'],['nonbasic Forest-typed targets (Overgrown Tomb, Underground Mortuary)']),
 'Demonic Tutor':card(S,'S13',['cast, any card from the real library to hand, shuffle'],[]),
 'Diabolic Intent':card(S,'S13',['cast with sacrifice, any card to hand'],[]),
 'Hunt for Specimens':card(S,'S13',['cast, Pest, Learn (lesson under the house rule / discard-draw / decline)'],['Learn\'s discard with an empty hand']),
 'Pest Summoning':card(S,'S13',['Lesson: into hand through Learn, cast with hybrid pips, two Pests'],['the Lesson outside the house rule']),
 'Unearth':card(S,'S13',['cast, MV<=3 creature card back (linked), Grist as a creature card (S16)','cycling (frozen bridge)'],['milled creature cards without event LKI (bridge limitation, except Grist)']),
 'Plumb the Forbidden':card(S,'S13',['cast with 0+ sacrifices, copies, draw/lose per resolution (frozen)'],['copies as separate stack objects']),
 'Immoral Bargain':card(S,'S13',['cast with X sacrifices, destroys X targets (own creatures/artifacts/enchantments, opposing creatures)'],[]),
 'Pest Infestation':card(S,'S13',['cast with X, up to X artifact/enchantment targets, 2X Pests (frozen)'],[]),
 'Abrupt Decay':card(S,'S15',['cast, destroy target nonland permanent MV<=3 (any seat); fizzles if the target left'],['"can\'t be countered" (no counterspells exist)']),
 "Assassin's Trophy":card(S,'S15',['cast, destroy target permanent an opponent controls'],['the opponent\'s basic-land search (no libraries)']),
 'Witherbloom Charm':card(S,'S15',['three modes: sacrifice a permanent + draw 2 / gain 5 / destroy nonland MV<=2'],[]),
 'Golgari Charm':card(S,'S15',['three modes: all creatures -1/-1 (SBA, any seat) / destroy enchantment / regenerate each creature you control'],['regeneration\'s remove-from-combat']),
 'Heroic Intervention':card(S,'S15',['hexproof + indestructible for your permanents until end of turn (every cleanup)'],[]),
 'Infuse with Vitality':card(S,'S15',['target creature returns tapped when it dies this turn; gain 2','deathtouch until end of turn with lethal combat effects (CP03)'],[]),
 'Grisly Salvage':card(S,'S15',['reveal five, one creature or land to hand, rest to graveyard'],['event-kernel LKI for the milled creature cards']),
 'Rise of the Witch-king':card(S,'S15',['each player sacrifices (opponents by the S8 policy), return another permanent card (creature/land/artifact/enchantment)'],[]),
 'Witherbloom Command':card(S,'S15',['two modes of four: mill 3 + land back / destroy noncreature nonland MV<=2 / -3/-1 / target opponent loses 2, gain 2'],['an opponent\'s mill (no libraries)']),
 'Grist, the Hunger Tide':card(P,'S16',['cast as a planeswalker, loyalty 3','+1 Insect + mill (repeat loop present, cannot fire in this deck)','-2 sacrifice -> reflexive destroy','-5 drain by creature cards in graveyard','704.5i, creature-card static off the battlefield'],['opponents attacking her','responses to loyalty abilities']),
 # ---- lands ----
 'Forest':card(L,'frozen v0.8',['play, {G}'],BASIC_NOT),'Swamp':card(L,'frozen v0.8',['play, {B}'],BASIC_NOT),'Command Tower':card(L,'frozen v0.8',['play, {B} or {G}'],[]),
 'Blooming Marsh':card(L,'S9',['entry condition (<=2 other lands), {B}/{G}'],[]),'Deathcap Glade':card(L,'S9',['entry condition (>=2 other lands), {B}/{G}'],[]),
 'Woodland Cemetery':card(L,'S9',['entry condition (Swamp/Forest type), {B}/{G}'],[]),'Undergrowth Stadium':card(L,'S9',['entry condition (2+ opponents in the game), {B}/{G}'],[]),
 'Overgrown Tomb':card(L,'S9',['pay 2 life or tapped, {B}/{G}, Swamp Forest types'],[]),'Underground Mortuary':card(L,'S9',['tapped, surveil 1, {B}/{G}, Swamp Forest types'],[]),
 'Darkbore Pathway // Slitherbore Pathway':card(L,'S9',['play one face, face decides the colour'],['the permanent keeps the full card name (bridge identity rule; documented)']),
 'Llanowar Wastes':card(L,'S9',['{C} free, {B}/{G} with 1 damage'],['damage prevention']),'Nurturing Peatland':card(L,'S9',['pay 1 life per coloured tap'],['{1}, T, sacrifice: draw']),
 'Phyrexian Tower':card(L,'S14',['{C}; T + sacrifice -> {B}{B} (mana ability)'],[]),'High Market':card(L,'S14',['{C}; T + sacrifice -> gain 1'],[]),'Grim Backwoods':card(L,'S14',['{C}; {2}{B}{G}, T + sacrifice -> draw'],[]),
 'Castle Locthwain':card(L,'S14',['entry condition (Swamp type), {B}, draw then lose by hand size'],[]),'Verdant Catacombs':card(L,'S14',['T, pay 1 life, sacrifice: Swamp/Forest-typed card with its own entry rule, shuffle'],[]),
 'Boseiju, Who Endures':card(L,'S14',['play, {G}'],['channel (no legal target exists in this kernel)']),'Takenuma, Abandoned Mire':card(L,'S14',['play, {B}, channel with legendary discount: mill 3, creature card to hand'],['planeswalker cards as the return target']),
 'Geier Reach Sanitarium':card(L,'S14',['{C}; {2}, T: you draw then discard'],['opponents\' draw/discard']),'Mikokoro, Center of the Sea':card(L,'S14',['{C}; {2}, T: you draw'],['opponents\' draw']),
}
QUANTITIES={'Forest':6,'Swamp':9}

def build(here=HERE):
    ref=json.loads((here/'PABTRV3_CARD_COVERAGE.json').read_text(encoding='utf-8'))
    names={c['name'] for c in ref['cards']}
    missing=sorted(names-set(CARDS)); extra=sorted(set(CARDS)-names)
    assert not missing and not extra,(missing,extra)
    total=sum(QUANTITIES.get(n,1) for n in CARDS)
    assert total==101,total
    entries={n:CARDS[n] for n in sorted(CARDS)}
    for n,e in entries.items(): e['quantity']=QUANTITIES.get(n,1)
    return {'built_by':'build_model_coverage_s20.py','cards':entries,
            'summary':{'cards_total':total,'distinct':len(entries),'certified':0,'partial':sum(1 for e in entries.values() if e['status']=='PARTIAL'),
                       'with_not_modeled_items':sum(1 for e in entries.values() if e['not_modeled'] and e['not_modeled']!=BASIC_NOT),
                       'rule':'no card is scored; unmodeled parts are listed, never treated as zero','card_text_source':'user-provided Scryfall bulk export (secondary-official); no official Oracle/CR authentication'}}

def canonical_bytes(obj): return (json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode('utf-8')

if __name__=='__main__':
    data=build(); (HERE/NAME).write_bytes(canonical_bytes(data)); print(f'{NAME}: {data["summary"]["distinct"]} cards, {data["summary"]["with_not_modeled_items"]} with explicit gaps')
