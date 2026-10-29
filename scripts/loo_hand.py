"""Session 4, PART H. Tests the distributional predictions implied by hand-sourced claims on held-out ICIT
texts from sites OTHER than Mohenjo-daro and Harappa. The claims were built mostly on those two sites'
material (M77/CISI 1-2). The null is a within-text shuffle (2000 permutations). These tests check the position
or function a claim implies, not its sound value."""
import sys, os, json, random, collections, re
import numpy as np, pandas as pd, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import claim_harness as C
from loo_signs import bh
ROOT = C.ROOT; OUT = os.path.join(ROOT, 'outputs', 'claims')
d = C.load_corpus()
d = d[~d.text.str.contains(r'000|999|/') & (d.text.str.len() > 0)]
con = sqlite3.connect(f'{ROOT}/map/indus_map.sqlite')
cc = pd.read_sql('select parpola_id, scheme, other_id from sign_concordance', con)
m2p = cc[cc.scheme == 'mahadevan'].groupby('other_id').parpola_id.apply(set).to_dict()
p2w = cc[cc.scheme == 'wells'].groupby('parpola_id').other_id.apply(set).to_dict()
def W(*ms):
    return {w[1:] for m in ms for p in m2p.get(m, ()) for w in p2w.get(p, ())}
held = [tuple(s) for s, site in zip(d.signs, d.site) if site not in ('Mohenjo-daro', 'Harappa') and len(s) >= 1]
insample = [tuple(s) for s, site in zip(d.signs, d.site) if site in ('Mohenjo-daro', 'Harappa') and len(s) >= 1]
NPERM = 2000
def pos_share(seqs, S, where):
    n = k = 0
    for s in seqs:
        if len(s) < 2: continue
        for i, x in enumerate(s):
            if x in S:
                n += 1; k += (i == 0) if where == 'initial' else (i == len(s)-1)
    return k, n
def bigram(seqs, A, B):
    return sum(1 for s in seqs for i in range(len(s)-1) if s[i] in A and s[i+1] in B)
def perm_p(seqs, f, obs):
    rng = random.Random(0); ge = 0; vals = []
    for _ in range(NPERM):
        sh = [tuple(rng.sample(s, len(s))) for s in seqs]; v = f(sh); vals.append(v); ge += v >= obs
    return (1 + ge) / (1 + NPERM), float(np.mean(vals))
def leftdist(seqs, S):
    c = collections.Counter(s[i-1] for s in seqs for i in range(1, len(s)) if s[i] in S); return c
def js(c1, c2):
    keys = set(c1) | set(c2); a = np.array([c1[k] for k in keys], float); b = np.array([c2[k] for k in keys], float)
    if a.sum() == 0 or b.sum() == 0: return np.nan
    a /= a.sum(); b /= b.sum(); m = (a+b)/2
    kl = lambda x, y: np.sum(x[x > 0]*np.log2(x[x > 0]/y[x > 0])); return 1 - 0.5*(kl(a, m)+kl(b, m))
T = []  # (claim, proponent, prediction, kind, args)
for m, val, prop in [('M284', 'pāḻ(-i) city', 'Mahadevan 2015'), ('M267', 'aka-(tt-i) palace', 'Mahadevan 2015'), ('M264', 'ampal(a) assembly', 'Mahadevan 2015'),
                     ('M150', 'kēr(-i) exclusive quarters', 'Mahadevan 2015'), ('M149', 'pāṭ(-i) ordinary quarters', 'Mahadevan 2015'), ('M261|M373', 'house', 'Mahadevan 2015')]:
    T.append((f'{m} = {val}', prop, 'place sign -> text-initial ("place signs are likely to occur in the initial position")', 'initial', (W(*m.split('|')),)))
for m, val, prop in [('M342', 'ā possessive suffix', 'Parpola 1994:188,277'), ('M342', '-at(tu) oblique suffix', 'Knorozov team (Parpola 1994:59-60)'),
                     ('M342', '-(a)nṟu masc. sg. suffix', 'Mahadevan 2015'), ('M211', '-(a)mpu non-masc. sg. suffix', 'Mahadevan 2015')]:
    T.append((f'{m} = {val}', prop, 'suffix -> text-final', 'final', (W(m),)))
for (a, b), val, prop in [(('M267', 'M099'), 'aka-tt-(i) lord of the house', 'Mahadevan 2015'), (('M108|M109', 'M059'), 'aṟu-mīn Pleiades', 'Parpola 1994:194 (after Heras)'),
                          (('M102|M103', 'M059'), 'mū-m-mīn', 'Parpola 1994:194'), (('M110|M112', 'M059'), 'eḻu-mīn Ursa Major', 'Parpola 1994:194'),
                          (('M087', 'M059'), 'vēḷ-mīn Venus', 'Parpola 1994:277'), (('M403', 'M087'), 'Muruku-Vēḷ', 'Parpola 1994:276'),
                          (('M267', 'M342'), "'cow at the city' (W861+W740)", 'Wells 2015:93')]:
    T.append((f'{a}+{b} = {val}', prop, 'compound -> adjacent pair (reading order) more frequent than within-text shuffle', 'bigram', (W(*a.split('|')), W(*b.split('|')))))
T.append(('M342 vs M211 = -(a)nṟu vs -(a)mpu gender paradigm', 'Mahadevan 2015', 'paradigm alternants -> similar left contexts (JS similarity) beyond frequency/position-matched random sign pairs', 'paradigm', (W('M342'), W('M211'))))
rows = []
for claim, prop, pred, kind, args in T:
    for cname, seqs in [('heldout_other_sites', held), ('insample_MD_H', insample)]:
        if kind in ('initial', 'final'):
            S = args[0]; k, n = pos_share(seqs, S, kind)
            f = lambda sh, S=S, kind=kind: pos_share(sh, S, kind)[0]
            p, nullm = perm_p([s for s in seqs if len(s) >= 2 and set(s) & S], f, k)
            rows.append(dict(claim=claim, proponent=prop, prediction=pred, corpus=cname, n=n, observed=k, null_mean=round(nullm, 2), share=round(k/n, 3) if n else np.nan, p=p))
        elif kind == 'bigram':
            A, B = args; k = bigram(seqs, A, B); sub = [s for s in seqs if set(s) & A and set(s) & B]
            p, nullm = perm_p(sub, lambda sh: bigram(sh, A, B), k) if sub else (1.0, 0.0)
            rows.append(dict(claim=claim, proponent=prop, prediction=pred, corpus=cname, n=len(sub), observed=k, null_mean=round(nullm, 2), share=np.nan, p=p))
        else:
            A, B = args; obs = js(leftdist(seqs, A), leftdist(seqs, B))
            freq = collections.Counter(x for s in seqs for x in s)
            fin = {x: pos_share(seqs, {x}, 'final') for x in freq}
            cand = [x for x in freq if freq[x] >= 10 and fin[x][1] and fin[x][0]/fin[x][1] >= .5 and x not in A | B]
            rng = random.Random(1); null = []
            for _ in range(2000):
                x, y = rng.sample(cand, 2); null.append(js(leftdist(seqs, {x}), leftdist(seqs, {y})))
            null = np.array([v for v in null if not np.isnan(v)])
            p = (1 + (null >= obs).sum()) / (1 + len(null)) if not np.isnan(obs) else 1.0
            rows.append(dict(claim=claim, proponent=prop, prediction=pred, corpus=cname, n=len(cand), observed=round(obs, 3), null_mean=round(null.mean(), 3), share=np.nan, p=p))
R = pd.DataFrame(rows)
for c in R.corpus.unique():
    R.loc[R.corpus == c, 'q_BH'] = bh(R.loc[R.corpus == c, 'p'].values)
R['mapped_W'] = [','.join(sorted(set().union(*a))) for *_, a in T for _ in (0, 1)]
R.to_csv(f'{OUT}/loo_hand_claims.csv', index=False)
print(R[['claim', 'corpus', 'n', 'observed', 'null_mean', 'share', 'p', 'q_BH']].to_string())
print('held-out n texts', len(held))
