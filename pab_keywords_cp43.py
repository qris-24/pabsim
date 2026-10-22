"""CP43 (open queue: keyword name lists from card data). The printed-keyword name sets the combat layer
(pab_combat_s17.py) and the policies use, read from the pinned card data (decks/CARDSOURCE_BG_COMMANDER_20261021.json)
for the creatures of the old baseline (upstream_frozen/FROZEN_PABTRV3_BASELINE.txt, the only gated deck). They were
hand-written lists (S17, CP37) with the same contents. Opponents' generic bodies are not in the card data and have no
keywords (unchanged). Fails closed: a deck card missing from the card data raises.
"""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CARD_DATA=ROOT/'decks'/'CARDSOURCE_BG_COMMANDER_20261021.json'
DECK=ROOT/'upstream_frozen'/'FROZEN_PABTRV3_BASELINE.txt'
_DECK_LINE=re.compile(r'^\s*1x\s+(.+?)\s*$')

def deck_creatures(card_data=CARD_DATA,deck=DECK):
    by={c['name']:c for c in json.loads(Path(card_data).read_text(encoding='utf-8'))['cards']}
    names=[m.group(1) for line in Path(deck).read_text(encoding='utf-8').splitlines() for m in [_DECK_LINE.match(line)] if m]
    missing=[n for n in names if n not in by]
    if missing: raise RuntimeError(f'CP43: deck cards missing from the card data: {missing}')
    return [by[n] for n in names if 'Creature' in by[n]['type_line']]

def _cant_block(card):
    """Printed "This creature can't block." (or the card's own name in place of "This creature"), as its own sentence."""
    return any(line.strip() in ("This creature can't block.",f"{card['name']} can't block.") for line in card['oracle_text'].split('\n'))

def keyword_names(creatures):
    kw=lambda k: frozenset(c['name'] for c in creatures if k in c['keywords'])
    return {'flying':kw('Flying'),'menace':kw('Menace'),'deathtouch':kw('Deathtouch'),'haste':kw('Haste'),
            'cant_block':frozenset(c['name'] for c in creatures if _cant_block(c))}

KEYWORDS=keyword_names(deck_creatures())
