"""CP28: pin the Oracle text the contract references need into an in-repo excerpt.

Reads C:\\pabsim\\data\\golgari_commander.json (read-only, outside the repo) and
decks/PAB_V3_ORACLE_SUPPLEMENT.json, and writes decks/ORACLE_EXCERPT_CP28.json
for exactly the cards named in CONTRACT_ORACLE_REFS_CP28.json. Not run by the
gate: the gate reads only the excerpt. Re-run after any mapping change.
Summary goes to EVIDENCE/CP28_ORACLE_EXCERPT_SUMMARY.txt, not the terminal.
"""
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CARD_DATA=Path(r'C:\pabsim\data\golgari_commander.json')
SUPPLEMENT='decks/PAB_V3_ORACLE_SUPPLEMENT.json'
MAPPING='CONTRACT_ORACLE_REFS_CP28.json'
EXCERPT='decks/ORACLE_EXCERPT_CP28.json'
SUMMARY='EVIDENCE/CP28_ORACLE_EXCERPT_SUMMARY.txt'

def sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def oracle_text(card):
    """Single-face: oracle_text as-is. Multi-face: 'face name\\ntext' per face, joined with '\\n//\\n'."""
    if 'oracle_text' in card: return card['oracle_text']
    return '\n//\n'.join(f['name']+'\n'+f.get('oracle_text','') for f in card['card_faces'])

def build():
    mapping=json.loads((ROOT/MAPPING).read_text(encoding='utf-8'))
    wanted=sorted({r['card'] for c in mapping['contracts'].values() for r in c['refs']})
    golgari={c['name']:c for c in json.loads(CARD_DATA.read_text(encoding='utf-8'))}
    supplement={r['name']:r for r in json.loads((ROOT/SUPPLEMENT).read_text(encoding='utf-8'))['records']}
    cards={}; missing=[]
    for name in wanted:
        if name in golgari: cards[name]={'oracle_text':oracle_text(golgari[name]),'source':'golgari_commander.json'}
        elif name in supplement: cards[name]={'oracle_text':supplement[name]['oracle_text'],'source':'supplement'}
        else: missing.append(name)
    excerpt={'build':'CP28',
             'purpose':'Pinned Oracle text for the cards named in '+MAPPING+'; the gate reads Oracle text only from this file. Text is exactly as in the source; nothing here is certified.',
             'mapping':MAPPING,
             'sources':{'golgari_commander.json':{'path':str(CARD_DATA),'sha256':sha256(CARD_DATA)},
                        'supplement':{'path':SUPPLEMENT,'sha256':sha256(ROOT/SUPPLEMENT)}},
             'cards':cards,'missing':missing}
    (ROOT/EXCERPT).write_text(json.dumps(excerpt,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
    lines=['CP28 Oracle excerpt build summary',
           'excerpt: '+EXCERPT,
           'cards referenced: %d'%len(wanted),
           'from golgari_commander.json: %d'%sum(c['source']=='golgari_commander.json' for c in cards.values()),
           'from supplement: %d'%sum(c['source']=='supplement' for c in cards.values()),
           'missing (referenced but in neither source): %d %s'%(len(missing),missing)]
    (ROOT/SUMMARY).write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')

if __name__=='__main__':
    build()
