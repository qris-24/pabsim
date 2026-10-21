"""Stage S19 (authorized 2026-10-18 11:05; "pause at 20"): integrated validation of whole games.

Not a deck score. S19 runs whole games under the S17/S18 driver and checks what a correct
kernel must satisfy regardless of how good the deck is:

  reproducibility   the same seed, configuration and policies give a byte-identical trace
  clock legality    every 'step_begin' follows the CR 500.1 step order; the active seat
                    rotates 0,1,2,3 minus seats that left; a lost seat never begins a turn
  life ledger       the controller's final life equals 40 + every 'gain' - every 'lose_life'
                    - every 'pay_life' - every combat damage dealt to seat 0 recorded in the
                    trace, and each opponent's life equals 40 - drains - targeted losses -
                    combat damage - Grist -5 - Witherbloom Command (all from the trace);
                    a seat that left ends at <= 0, or has 21+ commander damage (CP37)
  card identity     101 card identities throughout, every nontoken card in exactly one zone,
                    no token outside the battlefield (the S5–S11 invariants at every step)
  stack discipline  no card on either stack ledger at the end; nothing pending at the end
  counts            opponent_sacrifices == observed 'opponent_sacrifice' lines; commander
                    casts == 'commander_cast' lines; commander deaths == returns to the
                    command zone

validate_games(seeds, config) returns a report dict (also writable with write_report); the
per-game 'observed' block holds counts, not judgements. Any failed check lists the seed.
"""
from __future__ import annotations
import json
from pab_kernel import PhysicalZoneGame, KERNEL_VERSION
from pab_policy_s18 import run_game, check_invariants_s18
from pab_combat_s17 import COMMANDER_DAMAGE_LOSS
from pab_opponents_s8 import OPPONENT_SEATS
from pab_turn_clock import STEPS
from pab_turn_loop import opening_hand
from pab_terminal_audit_cp04 import no_steps_after_terminal

DEFAULT_BOARD=[{'name':'Bear','power':2,'toughness':2,'mana_value':2},{'name':'Knight','power':3,'toughness':3,'mana_value':3}]
DEFAULT_POLICY={1:{'removal_budget':2,'attack':'all'},2:{'wipe_at':4,'edict_budget':1,'attack':'all'},3:{'graveyard_hate_at':5,'attack':'all','exile_instead':True,'removal_budget':1}}
DEFAULT_CONFIG={'board':DEFAULT_BOARD,'policy':DEFAULT_POLICY,'block_policy':'none','learn':True,'max_turns':40}

def new_game(seed,config):
    g=PhysicalZoneGame(seed=seed,learn_sideboard_allowed=config.get('learn',True),block_policy=config.get('block_policy','none')); opening_hand(g)
    for s in OPPONENT_SEATS:
        g.declare_opponent_board(s,config.get('board',DEFAULT_BOARD))
        pol=config.get('policy',DEFAULT_POLICY).get(s)
        if pol: g.set_opponent_policy(s,dict(pol))
    return g

def life_ledger(g):
    """Ordered replay: returns the life vector the trace implies."""
    life=[40,40,40,40]; lost=set()
    for t in g.trace:
        k=t[0]
        if k=='gain': life[0]+=t[1]
        elif k in ('lose_life','pay_life'): life[0]-=t[1]
        elif k=='opponents_lose_each':
            for s in OPPONENT_SEATS:
                if s not in lost: life[s]-=t[1]
        elif k=='target_opponent_loses':
            alive=[s for s in OPPONENT_SEATS if s not in lost]
            if t[2]=='Witherbloom Command': continue          # seat recorded by the S15 handler below
            if alive: life[alive[0]]-=t[1]
        elif k=='witherbloom_command_target': life[t[1]]-=t[2]
        elif k=='target_self_loses': life[0]-=t[1]
        elif k=='combat_damage':
            for ev in t[1]:
                if ev[0]=='player': life[ev[1]]-=ev[3]
        elif k=='seat_leaves_game': lost.add(t[1])                     # CP37 (K12): a commander-damage loss does not change life
    return life

def clock_legal(g):
    """Every step_begin follows the step order; seats rotate skipping lost seats; returns (ok, detail)."""
    order=[st for _,st in STEPS]; prev=None; lost=set(); problems=[]
    for t in g.trace:
        if t[0]=='seat_leaves_game': lost.add(t[1]); continue
        if t[0]!='step_begin': continue
        _,turn,ap,phase,step=t
        if prev is not None:
            pturn,pap,pstep=prev
            if pturn==turn:
                if order.index(step)!=order.index(pstep)+1 or ap!=pap: problems.append(('step order',turn,pstep,step))
            else:
                if pstep!='cleanup' or step!='untap' or turn!=pturn+1: problems.append(('turn boundary',pturn,turn,pstep,step))
                nxt=(pap+1)%4
                while nxt in lost: nxt=(nxt+1)%4
                if ap!=nxt and ap not in lost: problems.append(('seat rotation',turn,pap,ap,tuple(sorted(lost))))
                if ap in lost and step=='untap': problems.append(('lost seat began a turn',turn,ap))
        prev=(turn,ap,step)
    term_ok,term_errors=no_steps_after_terminal(g.trace)
    if not term_ok: problems.extend(term_errors)
    return (not problems),problems[:5]

def lost_seats_ok(g):
    """CP37 (K12): every seat that left is at 0 or less life, or has 21+ commander damage (it leaves with its life)."""
    return all(g.life[s]<=0 or g.commander_damage[s]>=COMMANDER_DAMAGE_LOSS for s in g.lost_seats)

def validate_game(seed,config):
    g=new_game(seed,config); out,turns,ledger=run_game(g,config.get('max_turns',40)); check_invariants_s18(g)
    h=new_game(seed,config); run_game(h,config.get('max_turns',40))
    checks={}
    checks['reproducible']=(g.trace==h.trace and g.life==h.life)
    ok,detail=clock_legal(g); checks['clock_legal']=ok
    led=life_ledger(g); checks['life_ledger']=(led==g.life)
    checks['stacks_empty']=(g.stack_cards=={} and g.command_stack=={} and not g.pending)
    checks['counts']=(g.opponent_sacrifices==sum(1 for t in g.trace if t[0]=='opponent_sacrifice') and g.commander_casts==sum(1 for t in g.trace if t[0]=='commander_cast') and g.commander_deaths==sum(1 for t in g.trace if t[0]=='commander_to_command_zone'))
    checks['lost_seats_at_zero']=lost_seats_ok(g)                     # CP37 (K12)
    z=g.zones; checks['card_identity']=(sum(1 for c in z.cards.values() if not c.token)==101 and all(z.cards[u].zone==zone for zone,us in z.zones.items() for u in us))
    observed={'outcome':out,'turns':turns,'controller_turns':len(ledger),'life':list(g.life),'lost_seats':sorted(g.lost_seats),
              'cards_cast':sum(len(r[3]) for r in ledger),'lands_played':sum(1 for r in ledger if r[1]),'commander_casts':g.commander_casts,'commander_deaths':g.commander_deaths,
              'edict_opportunities':g.edict_opportunities,'opponent_sacrifices_observed':g.opponent_sacrifices,'policy_actions':len(g.policy_actions),
              'attacks_by_controller':sum(1 for t in g.trace if t[0]=='attackers_declared'),'attacks_on_controller':sum(1 for t in g.trace if t[0]=='opponent_attackers_declared'),
              'trace_length':len(g.trace),'sba_checks':g.sba_checks}
    return {'seed':seed,'checks':checks,'all_ok':all(checks.values()),'clock_problems':detail,'life_ledger':led,'observed':observed}

def validate_games(seeds,config=None):
    config={**DEFAULT_CONFIG,**(config or {})}
    games=[validate_game(s,config) for s in seeds]
    return {'kernel_version':KERNEL_VERSION,'config':{k:v for k,v in config.items()},'games':games,
            'all_ok':all(x['all_ok'] for x in games),'failed_seeds':[x['seed'] for x in games if not x['all_ok']],
            'note':'observed counts are not deck scores; no performance claim is made or implied'}

def write_report(report,path):
    with open(path,'w',encoding='utf-8') as fh: json.dump(report,fh,indent=1,sort_keys=True,default=str)
