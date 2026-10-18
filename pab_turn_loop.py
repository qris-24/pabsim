"""Stage S5 (approved 2026-10-18): integrated turn loop over EXISTING capabilities.

Drives a PhysicalZoneGame through whole turns with the S1–S4 clock: shuffle (R53,
CR 103.3) and opening hand, untap, draw, one supported land play per controller turn (Forest, Swamp,
Command Tower only; the other 18 fail closed), tapping linked lands for mana
in the first main phase. No new card mechanics; no casting from the physical
hand (not modeled yet); no opponents' libraries or boards.

check_invariants() is the point: it is evaluated at every step boundary and
after every action, and raises InvariantError on the first violation.
"""
from __future__ import annotations
from pab_zones import SUPPORTED_LAND_MANA, UnsupportedZoneMechanic

class InvariantError(AssertionError): pass

OPENING_HAND=7

def check_invariants(g):
    z=g.zones
    nontoken=[c for c in z.cards.values() if not c.token]
    if len(nontoken)!=101: raise InvariantError(f'card identity count {len(nontoken)} != 101')
    inzones=sum(len(v) for v in z.zones.values())
    tokens=[c for c in z.cards.values() if c.token]
    if inzones!=101+sum(1 for c in tokens if c.zone=='battlefield'):
        raise InvariantError('zone membership does not account for every card exactly once')
    for zone,uids in z.zones.items():
        for u in uids:
            if z.cards[u].zone!=zone: raise InvariantError(f'card {u} zone label {z.cards[u].zone} != {zone}')
    if len({u for v in z.zones.values() for u in v})!=inzones: raise InvariantError('a card is in two zones')
    savra_zones=[z.cards[u].zone for zone in ('command','battlefield','graveyard','exile') for u in z.zones[zone] if z.cards[u].name=='Savra, Queen of the Golgari']
    if len(savra_zones)!=1:                 # S10 (2026-10-18): she may pass through graveyard/exile between death and the next SBA check (903.9a); check_invariants_s10 bounds that
        raise InvariantError('Savra must be in exactly one of command, battlefield, graveyard or exile')
    if z.land_plays_this_turn>1: raise InvariantError('more than one land play this turn')
    if z.failed_draws: raise InvariantError('a draw from an empty library happened')
    if any(z.cards[u].tapped for u in z.zones['hand']+z.zones['library']+z.zones['graveyard']):
        raise InvariantError('a card outside the battlefield is tapped')
    g.assert_bridge_integrity()
    if g.life[0]<=0 and not g.game_lost: raise InvariantError('life <= 0 without loss adjudication')

def opening_hand(g,n=OPENING_HAND):
    """CR 103.3: shuffle the library, then draw the opening hand. R53 (approved 2026-10-18):
    before this fix no shuffle happened, so every seed drew the frozen decklist order."""
    g.zones.shuffle_library(); g.trace.append(('opening_shuffle_103_3',g.zones.seed))
    cards=g.zones.draw(n); g.trace.append(('opening_hand',len(cards))); check_invariants(g); return cards

def playable_land_in_hand(g):
    z=g.zones
    for u in z.zones['hand']:
        if z.cards[u].name in SUPPORTED_LAND_MANA: return u
    return None

def run_turns(g,turns,*,tap_lands=True):
    """Advance `turns` full game turns from the current clock position. Returns a ledger
    of controller turns: (turn, drawn, land_played, mana_produced)."""
    ledger=[]; start=g.clock.turn
    while g.clock.turn<start+turns:
        t,ap,ph,st=g.advance_step(); g.resolve(); check_invariants(g)
        if ap!=0 or st!='precombat_main': continue
        land=playable_land_in_hand(g); played=None
        if land is not None:
            played=g.play_physical_land(land).name; check_invariants(g)
        mana=[]
        if tap_lands:
            for ev,ph_uid in list(g.linked_battlefield.items()):
                p=g.permanents.get(ev)
                if p is not None and not p.tapped and g.zones.cards[ph_uid].is_land:
                    choices=SUPPORTED_LAND_MANA[g.zones.cards[ph_uid].name]
                    mana.append(g.tap_physical_land_for_mana(ev,color=choices[0] if len(choices)>1 else None)); check_invariants(g)
        drawn=[x for x in g.trace if x[0]=='draw' and x[2]=='draw step']
        ledger.append((t,len(drawn),played,tuple(mana)))
    return ledger
