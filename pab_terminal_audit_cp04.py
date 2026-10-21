"""CP04: independent trace guard for turn advancement after an adjudicable loss/win.

The S18 kernel did not consistently log an explicit `lose_game` transition (CP39 closed K7: resolve() now does);
replay controller life from the same sources as S19's life ledger and require
life to be positive when each new step begins. Loss within a multi-event
resolution may be healed before the next step (so no premature death claim).
An explicit win_game/lose_game is terminal immediately.
"""

def no_steps_after_terminal(trace):
    balance = 40
    terminal_event = None
    errors = []
    for index, event in enumerate(trace):
        kind=event[0]
        if kind == 'step_begin':
            if terminal_event is not None:
                errors.append(('step after terminal marker', index, terminal_event, event[1:]))
            elif balance <= 0:
                errors.append(('step after nonpositive controller life', index, balance, event[1:]))
        elif kind == 'gain':
            balance += event[1]
        elif kind in ('lose_life', 'pay_life', 'target_self_loses'):
            balance -= event[1]
        elif kind == 'combat_damage':
            for damage in event[1]:
                if damage[0] == 'player' and damage[1] == 0:
                    balance -= damage[3]
        elif kind in ('win_game','lose_game'):
            terminal_event=(kind,index)
    return not errors, errors[:5]
