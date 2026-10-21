"""Stage S10 (authorized 2026-10-18 11:05, "all further engineering until a stop point"):
Savra from the command zone — cast, commander tax, death, return, recast.

Layered above pab_lands_s9.FixerLandsMixin (PhysicalZoneGame only). No frozen file edited.
Until S10 the only way Savra reached the battlefield was the fixture add(SAVRA): an event
body with no physical card behind it, while the physical Savra stayed in zones['command'].
That fixture path is untouched (every frozen test uses it). S10 adds the real path:

cast_commander() (CR 903.6, 903.8): Savra's physical card must be in the command zone and
not already on the command stack ledger; creature timing (own main phase, empty stack,
priority — the S6 clock rules); cost {2}{B}{G} plus {2} for each previous cast from the
command zone this game (commander tax, `commander_casts`); paid from the shared pool.
Resolution (608.3): command zone -> battlefield through the frozen add(SAVRA) + linked path,
so ETB behaviour (Essence Warden, Innkeeper, Lumaret) is the frozen kernel's. While on the
stack the card stays physically in the command zone and is recorded in `command_stack`
(the S6 substitute for the missing stack zone).

Death (CR 903.9a, 2020 wording): a linked Savra that dies goes to the graveyard through the
frozen _leave() — so every 'dies' trigger (Deathgreeter, Blood Artist, Grave Pact, Savra's
own look-back sacrifice triggers) fires exactly as for any creature — and at the next
state-based-action check her owner may put her into the command zone. The kernel's fixed
policy is always to do so (traced `commander_to_command_zone`): the physical card moves
graveyard -> command, the bridge's graveyard link and the event kernel's graveyard LKI for
that body are removed (she is no longer a reanimation target), and `commander_deaths`
counts it. The same SBA applies if the card is ever found in exile. Hand/library (903.9b)
cannot happen yet: nothing bounces or tucks her.

Not modeled: opponents' removal (next stage), protection, commander damage, partner,
choosing to leave her in the graveyard.
"""
from __future__ import annotations
from pab_lands_s9 import FixerLandsMixin, tap_lands_policy, play_land_policy, playable_land_in_hand
from pab_opponents_s8 import check_invariants_s8
from pab_zone_bridge import BridgeError
from pab_focus_engine import Trigger, SAVRA
import pab_cast_s7 as _s7

COMMANDER_COST=(1,1,2)          # (black, green, generic) = {2}{B}{G}; EVIDENCE/S10_COMMANDER_EVIDENCE.json
COMMANDER_BODY={'power':2,'toughness':2,'colors':'BG','mana_value':4}
TAX_PER_CAST=2

class CommanderMixin(FixerLandsMixin):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        self.command_stack: dict[int,str]={}
        self.commander_casts=0; self.commander_deaths=0

    def commander_card(self):
        return next((self.zones.cards[u] for u in self.zones.zones['command']),None)

    def commander_cost(self):
        b,g,gen=COMMANDER_COST; return (b,g,gen+TAX_PER_CAST*self.commander_casts)

    def cast_commander(self,*,main_phase=None,stack_empty=None,has_priority=None):
        card=self.commander_card()
        if card is None: raise BridgeError('S10: Savra is not in the command zone')
        if card.uid in self.command_stack: raise BridgeError('S10: Savra is already on the stack')
        if self.game_lost: raise BridgeError('S10: game already lost')
        self._timing('creature',main_phase=main_phase,stack_empty=stack_empty,has_priority=has_priority)
        black,green,generic=self.commander_cost(); pool=self.mana_pool
        if pool.count('B')<black or pool.count('G')<green or len(pool)<black+green+generic:
            raise BridgeError(f'S10: mana unavailable for Savra (cost {black},{green},{generic} with tax {TAX_PER_CAST*self.commander_casts})')
        # ---- mutation ----
        uid=card.uid; self.command_stack[uid]=SAVRA
        self.trace.append(('cast_begin',SAVRA,uid))
        self.pay_mana(black=black,green=green,generic=generic)
        self.trace.append(('cast',SAVRA))
        self.trace.append(('commander_cast',uid,(black,green,generic),self.commander_casts))
        self.commander_casts+=1
        self.pending.append(Trigger(SAVRA+' resolution (S10)',lambda:self._resolve_commander(uid)))
        self.assert_bridge_integrity()
        return card

    def _resolve_commander(self,uid):
        if self.command_stack.get(uid)!=SAVRA: raise BridgeError('S10: Savra is not on the command stack ledger')
        self.zones._require_in_zone(uid,'command')
        self.zones.move(uid,'battlefield',controller=0)
        del self.command_stack[uid]
        p=self.add(SAVRA,colors=COMMANDER_BODY['colors'],creature=True,mana_value=COMMANDER_BODY['mana_value'],
                   power=COMMANDER_BODY['power'],toughness=COMMANDER_BODY['toughness'])
        self.linked_battlefield[p.uid]=uid
        self.trace.append(('physical_creature_spell_resolved',SAVRA,uid,p.uid))
        self.assert_bridge_integrity()

    # ---- CR 903.9a as a state-based action ----
    def state_based_actions(self):
        rounds=super().state_based_actions()
        for zone in ('graveyard','exile'):
            for uid in list(self.zones.zones[zone]):
                card=self.zones.cards[uid]
                if card.name!=SAVRA or card.token: continue
                event_uid=next((e for e,ph in self.linked_graveyard.items() if ph==uid),None)
                if event_uid is not None:
                    del self.linked_graveyard[event_uid]
                    self.graveyard=[q for q in self.graveyard if q.uid!=event_uid]
                self.zones.move(uid,'command')
                self.commander_deaths+=1
                self.trace.append(('commander_to_command_zone',uid,zone,event_uid))
                self.assert_bridge_integrity()
        return rounds

    def assert_bridge_integrity(self):
        super().assert_bridge_integrity()
        for uid,name in getattr(self,'command_stack',{}).items():
            c=self.zones.cards.get(uid)
            if c is None or c.zone!='command' or c.name!=name: raise AssertionError('S10 command stack ledger card is not Savra in the command zone')
        return True

# ---- invariants and driver --------------------------------------------------
def check_invariants_s10(g):
    check_invariants_s8(g)
    for uid in g.command_stack:
        if g.zones.cards[uid].zone!='command': raise AssertionError('S10: command ledger card not in command zone')
    if g.command_stack and not g.pending and not (g.game_lost and g.command_stack==getattr(g,'loss_stacks',({},{}))[1]): raise AssertionError('S10: Savra on the command ledger with nothing pending')   # CP39
    z=g.zones
    if sum(1 for u in z.zones['graveyard']+z.zones['exile'] if z.cards[u].name==SAVRA) and not g.pending:
        raise AssertionError('S10: Savra left in graveyard/exile after state-based actions')

def commander_need(g):
    if g.commander_card() is None: return {'B':0,'G':0}
    b,gr,_=g.commander_cost(); return {'B':b,'G':gr}

def cast_commander_when_able(g):
    """Fixed policy: cast Savra from the command zone whenever the pool can pay cost + tax."""
    card=g.commander_card()
    if card is None or card.uid in g.command_stack: return False
    b,gr,gen=g.commander_cost(); pool=g.mana_pool
    if pool.count('B')<b or pool.count('G')<gr or len(pool)<b+gr+gen: return False
    g.cast_commander(); check_invariants_s10(g); g.resolve(); check_invariants_s10(g); return True

def run_turns_casting(g,turns):
    """S9 driver shape; Savra is cast before the hand pass. Ledger: (turn, land, mana, names_cast)."""
    ledger=[]; start=g.clock.turn
    while g.clock.turn<start+turns:
        t,ap,ph,st=g.advance_step(); g.resolve(); check_invariants_s10(g)
        if ap!=0 or st!='precombat_main': continue
        u,kw=play_land_policy(g); played=None
        if u is not None: played=g.play_physical_land(u,**kw).name; g.resolve(); check_invariants_s10(g)
        mana=tap_lands_policy(g,extra=commander_need(g))
        cast=[SAVRA] if cast_commander_when_able(g) else []
        cast+=_s7.cast_when_able(g); check_invariants_s10(g)
        ledger.append((t,played,tuple(mana),tuple(cast)))
    return ledger
