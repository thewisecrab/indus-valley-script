"""Sign-by-sign table: top 100 M77 signs by frequency + all stroke numerals."""
import os, re, json, sqlite3, collections, math
import pandas as pd, numpy as np
from scipy.stats import binomtest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = f'{ROOT}/outputs/structure'
m = pd.read_csv(f'{ROOT}/data/joyboseroy_indus_decipher/data/m77_indusscript_real_corpus.csv', dtype=str)
def segs_m(seq):
    out, cur = [], []
    for x in seq.split():
        if x == 'MSg0':
            if cur: out.append(cur); cur = []
        else: cur.append('M%03d' % int(x[3:]))
    if cur: out.append(cur)
    return out
LINES = [s for q in m.sign_sequence for s in segs_m(q)]
freq = collections.Counter(x for s in LINES for x in s)
ini = collections.Counter(s[0] for s in LINES if len(s) > 1); fin = collections.Counter(s[-1] for s in LINES if len(s) > 1); solo = collections.Counter(s[0] for s in LINES if len(s) == 1)
nonsolo = collections.Counter(x for s in LINES if len(s) > 1 for x in s)
base_i = sum(ini.values()) / sum(nonsolo.values()); base_f = sum(fin.values()) / sum(nonsolo.values())
NUM_SHORT = {'M097':1,'M098':1,'M099':2,'M100':2,'M101':2,'M102':3,'M103':3,'M104':4,'M105':4,'M106':5,'M107':5,'M108':6,'M109':6,'M110':7,'M112':7,'M114':8,'M115':9,'M116':9,'M118':10,'M121':12}
NUM_LONG = {'M086':1,'M087':2,'M089':3,'M095':4,'M096':5}
NUM_OTHER = {'M111':'bracketed strokes','M113':'bracketed strokes','M117':'roofed strokes','M119':'slanted strokes','M120':'slanted strokes','M122':'bracketed strokes','M088':'long+short strokes'}
cls = pd.read_csv(f'{OUT}/sign_classes_M77.csv', dtype={'replicated': str}).set_index('sign')
con = sqlite3.connect(f'{ROOT}/map/indus_map.sqlite')
cc = pd.read_sql("select parpola_id, scheme, other_id from sign_concordance where scheme in ('mahadevan','wells')", con)
p2m = cc[cc.scheme == 'mahadevan'].groupby('parpola_id').other_id.apply(list).to_dict(); p2w = cc[cc.scheme == 'wells'].groupby('parpola_id').other_id.apply(list).to_dict()
m2p = collections.defaultdict(set); m2w = collections.defaultdict(set)
for p, ms in p2m.items():
    for mm in ms:
        mm = 'M%03d' % int(re.sub(r'\D', '', mm)); m2p[mm].add(p)
        for w in p2w.get(p, []): m2w[mm].add('W%03d' % int(re.sub(r'\D', '', w)))
desc = dict(pd.read_sql("select sign_id, description from signs where scheme='parpola'", con).values)
xl = pd.read_csv(f'{ROOT}/data/lipi/xlits.csv', dtype=str, keep_default_na=False); yv = {'W' + r.sign: r.xlit for r in xl.itertuples()}
MAHA = {'M261': 'house (place sign) — Mahadevan 2015', 'M373': 'house (place sign) — Mahadevan 2015', 'M267': 'fortified house (place sign) — Mahadevan 2015',
        'M284': 'city (place sign) — Mahadevan 2015', 'M342': 'jar; most frequent end sign — Mahadevan 2015'}
PARP = {'M059': 'fish = Dravidian *mīn "fish/star" (rebus) — Parpola 1994', 'M108': "'6'+fish = aru-mīn (Pleiades) — Parpola 1994",
        'M102': "'3'+fish = mū-m-mīn — Parpola 1994", 'M103': "'3'+fish = mū-m-mīn — Parpola 1994", 'M110': "'7'+fish = eḻu-mīn (Ursa Major) — Parpola 1994"}
top = [s for s, _ in freq.most_common(100)]
nums = list(NUM_SHORT) + list(NUM_LONG) + list(NUM_OTHER)
rows = []
for s in top + [n for n in nums if n not in top]:
    n = freq.get(s, 0); ns = nonsolo.get(s, 0)
    pi = binomtest(ini[s], ns, base_i, alternative='greater').pvalue if ns else float('nan')
    pf = binomtest(fin[s], ns, base_f, alternative='greater').pvalue if ns else float('nan')
    c = cls.loc[s] if s in cls.index else None
    W = c.W if c is not None and isinstance(c.W, str) else ';'.join(sorted(m2w[s])) if m2w[s] else ''
    P = c.P if c is not None and isinstance(c.P, str) else ';'.join(sorted(m2p[s]))
    d0 = c.description if c is not None and isinstance(c.description, str) else (desc.get(sorted(m2p[s])[0], '') if m2p[s] else '')
    lit = []
    yvs = [f'{w}={yv[w].strip()}' for w in W.split(';') if w in yv and re.search(r'[a-zA-Z]', yv[w])]
    if yvs: lit.append('Sanskrit syllabic value(s) ' + ', '.join(yvs[:4]) + (' …' if len(yvs) > 4 else '') + ' — Yajnadevam/lipi')
    if s in MAHA: lit.append(MAHA[s])
    if s in PARP: lit.append(PARP[s])
    if s in NUM_SHORT or s in NUM_LONG: lit.append('numeral (stroke count) — Mahadevan 1977 sign list grouping; Parpola 1994 (e.g. p. 194)')
    structural = c.cls if c is not None else ('NUMERAL-STROKE' if s in nums else 'n<10 (unclassified)')
    pos = c.positional_class if c is not None and isinstance(c.positional_class, str) else ('n<10' if n < 10 else '')
    conf = c.conf_distributional if c is not None else float('nan'); rep = c.replicated if c is not None else ''
    # assessed function + confidence basis
    if s in NUM_SHORT or s in NUM_LONG:
        v = NUM_SHORT.get(s, NUM_LONG.get(s))
        func = f'numeral, value {v} ({"short" if s in NUM_SHORT else "long"} strokes)'
        cnum = 'qualitative: high'; basis = 'iconic stroke count checked on M77 plates (paper/evidence); long 2/3/4 substitute in the W700 tablet formula; NOT distributionally cohesive (cohesion p=0.70/0.74) — not calibratable as %'
    elif s in NUM_OTHER:
        func = f'stroke variant ({NUM_OTHER[s]}); numeral status uncertain'; cnum = 'qualitative: low–moderate'; basis = 'plate inspection only'
    elif structural in ('TERMINAL', 'INITIAL', 'PRE-TERMINAL', 'BOUND-COLLOCATE') and conf == conf:
        func = {'TERMINAL': 'text-final marker (suffix/determinative/title-like); semantic value unknown',
                'INITIAL': 'text-initial sign (title/place/category-like); semantic value unknown',
                'PRE-TERMINAL': 'occurs immediately before terminal signs (modifier/inflection-like slot)',
                'BOUND-COLLOCATE': 'part of a fixed collocation (ligature/compound-like)'}[structural]
        cnum = f'{100*conf:.1f}% (positional class)'
        basis = f'bootstrap stability × (1−FDR vs 30 within-line shuffles); ICIT replication: {"yes" if rep == "True" else "no" if rep == "False" else "n/a"}'
    else:
        func = 'no distinctive positional behaviour (medial/unspecified)'; cnum = '—'; basis = 'class MEDIAL/STAND-ALONE has FDR≈1 (not distinguishable from shuffled)'
    phon = 'not estimable above null' if lit and any('Yajnadevam' in x or 'Parpola' in x or 'Mahadevan 2015' in x for x in lit) else 'no proposal tested'
    rows.append(dict(M=s, P=P, W=W, description=d0, freq=n, init_share=round(ini[s] / ns, 3) if ns else None, final_share=round(fin[s] / ns, 3) if ns else None,
                     solo_share=round(solo[s] / n, 3) if n else None, p_initial=float(f'{pi:.2g}') if pi == pi else None, p_final=float(f'{pf:.2g}') if pf == pf else None,
                     positional_class=pos, structural_class=structural, literature_values=' | '.join(lit), our_function=func, function_confidence=cnum,
                     function_confidence_basis=basis, phonetic_value_confidence=phon))
T = pd.DataFrame(rows); T.to_csv(f'{OUT}/sign_table.csv', index=False)
# per-sign notes on literature tests
notes = {'M342': 'Jar is terminal (final share 0.70, p≈1e-272); this confirms the positional half of Mahadevan’s claim only.',
         'M267': 'Initial share 0.78, p≈1e-92: positional prediction of “place sign” confirmed; the meaning “fortified house” is not tested by position.',
         'M059': 'Parpola’s restriction of numbers before fish to 3,4,6,7 is contradicted in M77 (short-2 M099/M100 precedes the fish 16×; plate-checked). Asterism compounds absent from the Dravidian DB except mū-m-mīn.'}
T['note'] = T.M.map(notes).fillna('')
T.to_csv(f'{OUT}/sign_table.csv', index=False)
def md(df):
    cols = ['M', 'P', 'W', 'freq', 'init_share', 'final_share', 'structural_class', 'literature_values', 'our_function', 'function_confidence', 'phonetic_value_confidence']
    lines = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for r in df[cols].fillna('').itertuples(index=False):
        lines.append('| ' + ' | '.join(str(x).replace('|', '/').replace('\n', ' ') for x in r) + ' |')
    return '\n'.join(lines)
open(f'{OUT}/sign_table.md', 'w').write(md(T))
print(len(T), T.structural_class.value_counts().to_dict())
print(T[T.function_confidence.str.contains('%')][['M', 'structural_class', 'function_confidence']].to_string())
