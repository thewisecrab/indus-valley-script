"""Session 4: per-sign leave-one-out tests of published sign-value proposals.

PART P (phonetic keys: Yajnadevam/Sanskrit, Field-Cady/Dravidian).
For each sign s with value v that occurs in >= 5 unique ICIT texts, hold out s's value and ask whether
v, combined with the rest of the key, makes the occurrences of s fall inside an attested lexicon word
(length >= 4, spanning s plus >= 1 character from a neighbour) more often than 40 alternative values
drawn from the same key's own value inventory (the alternative-value null).
The same statistic is then recomputed on within-text-shuffled corpora (2) and with 7 alternative
length-matched lexicons, and for a key FITTED to a shuffled corpus (the fitted-noise calibration).
A sign 'beats null' only if: BH q < 0.05 against the alternative values, its effect is larger than in
both shuffled corpora, and larger than under every alternative lexicon.
PART H (hand-sourced logographic/morphemic claims): tests the distributional predictions implied by
each claim on ICIT texts from sites OUTSIDE Mohenjo-daro and Harappa (site-held-out), against a
within-text shuffle null. These test the position or function implied by a claim, not the sound value.
"""
import sys, os, re, json, random, collections
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import claim_harness as C
ROOT = C.ROOT; OUT = os.path.join(ROOT, 'outputs', 'claims')
NALT = 300; MINOCC = 5   # alternatives = whole distinct value inventory, capped at 300

def owned_items_yaj(seq, key):
    items = []; prev = None
    for i, s in enumerate(seq):
        v = key.get(s, '')
        if i > 0 and re.match(r'^.*([iu]|an|as)$', prev) is None and re.match(r'^[aiu]$', v) is None and not prev.endswith('.'):
            items.append(('a', True, i-1))
        items += [(c, False, i) for c in v]
        prev = (prev or '') + v if i else v
    if re.match(r'.*([iu]|an|as)$', prev or '') is None: items.append(('a', True, len(seq)-1))
    out = []
    for c, o, w in items:
        r = C.SLP_MAP.get(c, c) if c in C.SLP_MAP else (c if c in C.ALPHA else '')
        for ch in r:
            if out and out[-1][0] == ch: continue
            out.append((ch, o, w))
    return out
def owned_items_syl(seq, key):
    out = []
    for i, s in enumerate(seq):
        v = key.get(s)
        r = C.red_lat(v) if v else '|'
        for ch in r:
            if out and out[-1][0] == ch and ch != '|': continue
            out.append((ch, False, i))
    return out

def hits(seq, key, pos, W, mode):
    """fraction of positions p (occurrences of the target sign) inside an attested word spanning a neighbour"""
    items = owned_items_yaj(seq, key) if mode == 'yaj' else owned_items_syl(seq, key)
    variants = [items] + ([[x for x in items if not x[1]]] if mode == 'yaj' else [])
    res = []
    for p in pos:
        ok = False
        for it in variants:
            s = ''.join(x[0] for x in it); own = [x[2] for x in it]
            span = [k for k, w in enumerate(own) if w == p]
            if not span: continue
            a, b = span[0], span[-1] + 1
            for i in range(max(0, b-10), a+1):
                for j in range(max(b, i+4), min(len(s), i+10)+1):
                    if j - i > b - a and s[i:j] in W: ok = True; break
                if ok: break
            if ok: break
        res.append(ok)
    return res

def sign_stat(args):
    s, occ, key, pool, W, mode, seed = args
    rng = random.Random(seed)
    alts = rng.sample([v for v in pool if v != key[s]], min(NALT, len(pool)-1))
    def stat(v):
        k = dict(key); k[s] = v; h = []
        for seq, pos in occ: h += hits(seq, k, pos, W, mode)
        return np.array(h, dtype=float)
    real = stat(key[s]); altm = np.array([stat(v) for v in alts])
    pi = altm.mean(0)                       # per-occurrence hit probability under alternative values
    p_rank = (1 + int((altm.mean(1) >= real.mean()).sum())) / (1 + len(alts))   # exact rank test vs alternative values
    # Poisson-binomial upper tail (normal approx., continuity-corrected; pi floored at 1/(2*NALT))
    pf = np.clip(pi, 0.5/len(alts), 1 - 0.5/len(alts)); mu = pf.sum(); sd = np.sqrt((pf*(1-pf)).sum())
    from scipy.stats import norm
    p_pb = float(norm.sf((real.sum() - 0.5 - mu) / sd)) if sd > 0 else 1.0
    return s, float(real.mean()), float(pi.mean()), float(real.mean() - pi.mean()), p_rank, p_pb, len(real)

def occurrences(seqs, signs):
    occ = collections.defaultdict(list)
    for seq in seqs:
        pos = collections.defaultdict(list)
        for i, x in enumerate(seq): pos[x].append(i)
        for x, ps in pos.items():
            if x in signs: occ[x].append((seq, ps))
    return occ

def bh(p):
    p = np.asarray(p); n = len(p); o = np.argsort(p); q = np.empty(n)
    q[o] = np.minimum.accumulate((p[o] * n / np.arange(1, n+1))[::-1])[::-1]
    return np.minimum(q, 1)

def run_condition(key, mode, seqs, W, label, procs=8):
    pool = sorted({v for v in key.values() if v})
    occ = occurrences(seqs, {s for s, v in key.items() if v})
    signs = [s for s, o in occ.items() if len(o) >= MINOCC]
    jobs = [(s, occ[s], key, pool, W, mode, hash((s, 'alt')) % 10**6) for s in signs]
    with Pool(procs) as P: rows = P.map(sign_stat, jobs, chunksize=4)
    df = pd.DataFrame(rows, columns=['sign', 'hit_real', 'hit_alt_mean', 'effect', 'p_alt', 'p_poissonbinom_anticonservative', 'n_occ'])
    df['q_alt'] = bh(df.p_alt); df['condition'] = label; df['n_texts'] = [len(occ[s]) for s in df.sign]
    print(label, 'signs', len(df), 'q<.05:', int((df.q_alt < .05).sum()), 'p<.05:', int((df.p_alt < .05).sum()), 'mean effect %.4f' % df.effect.mean(), flush=True)
    return df

def fit_key_on(seqs, lname, seed=0, iters=2000, topk=150):
    """same hill-climb as claim_harness.fit_run but returns the key (fitted in-sample on seqs)"""
    L = C.get_lexicons(); T = C.trie(L[lname]); rng = random.Random(seed)
    key0 = C.load_key(); freq = collections.Counter(x for s in seqs for x in s)
    top = [s for s, _ in freq.most_common(topk)]
    signs = list(key0); vals = [key0[s] for s in signs]; rng.shuffle(vals); key = dict(zip(signs, vals))
    inv = collections.defaultdict(list)
    for i, s in enumerate(seqs):
        for x in set(s): inv[x].append(i)
    cur = [C.segmentable(C.red_items(C.mech(s, key)), T) for s in seqs]; pool = [v for v in vals if v]
    for it in range(iters):
        a = rng.choice(top)
        if rng.random() < .5:
            b = rng.choice(top); changed = {a: key[b], b: key[a]}
        else: changed = {a: rng.choice(pool)}
        old = {k: key[k] for k in changed}; key.update(changed)
        idx = set(); [idx.update(inv[k]) for k in changed]
        new = {i: C.segmentable(C.red_items(C.mech(seqs[i], key)), T) for i in idx}
        if sum(new[i] - cur[i] for i in idx) >= 0:
            for i, v in new.items(): cur[i] = v
        else: key.update(old)
    return key

def part_P():
    L = C.get_lexicons(); lexn = [k for k in L if not k.startswith('_')]
    seqs = C.texts_for_tests()
    yk = C.load_key()
    fc = pd.read_csv(f'{ROOT}/data/field-cady_indus_valley_script_corpus/indus_dravidian_mapping_100.csv', dtype=str)
    fk = {s: v for s, v in zip(fc.Indus_Sign, fc.Dravidian_Syllable) if s not in ('000', '999')}
    sh900 = C.shuffle_within(seqs, random.Random(900))
    k_sh = fit_key_on(sh900, 'sanskrit_MW', seed=9)          # a key fitted to an order-destroyed corpus
    k_rr = fit_key_on(seqs, 'sanskrit_MW', seed=11)          # a key fitted to the real corpus from a random start
    json.dump(dict(fitted_to_shuffled=k_sh, fitted_to_real_random_init=k_rr), open(f'{OUT}/loo_fitted_noise_keys.json', 'w'))
    allres = []
    for kname, key, mode, claimed, corpus in [('Yajnadevam', yk, 'yaj', 'sanskrit_MW', seqs), ('FieldCady', fk, 'syl', 'proto_dravidian_PDR', seqs),
                                              ('FittedToShuffled', k_sh, 'yaj', 'sanskrit_MW', sh900), ('FittedToReal_randominit', k_rr, 'yaj', 'sanskrit_MW', seqs)]:
        for lname in [claimed] + [l for l in lexn if l != claimed]:
            allres.append(run_condition(key, mode, corpus, L[lname], f'{kname}|real|{lname}').assign(key=kname, lexicon=lname, corpus='real'))
            pd.concat(allres).to_csv(f'{OUT}/loo_phonetic_all_conditions.csv', index=False)
        for i in range(2):
            sh = C.shuffle_within(corpus, random.Random(500 + i))
            allres.append(run_condition(key, mode, sh, L[claimed], f'{kname}|shuffled{i}|{claimed}').assign(key=kname, lexicon=claimed, corpus=f'shuffled{i}'))
            pd.concat(allres).to_csv(f'{OUT}/loo_phonetic_all_conditions.csv', index=False)
    return pd.concat(allres)

def summarise_P(A):
    rows = []; summ = {}
    for kname, claimed in [('Yajnadevam', 'sanskrit_MW'), ('FieldCady', 'proto_dravidian_PDR'), ('FittedToShuffled', 'sanskrit_MW'), ('FittedToReal_randominit', 'sanskrit_MW')]:
        a = A[A.key == kname]
        base = a[(a.corpus == 'real') & (a.lexicon == claimed)].set_index('sign')
        sh = a[a.corpus.str.startswith('shuffled')].pivot_table(index='sign', columns='corpus', values='effect')
        al = a[(a.corpus == 'real') & (a.lexicon != claimed)].pivot_table(index='sign', columns='lexicon', values='effect')
        t = base[['hit_real', 'hit_alt_mean', 'effect', 'p_alt', 'q_alt', 'p_poissonbinom_anticonservative', 'n_texts', 'n_occ']].copy()
        t['max_effect_shuffled'] = sh.max(axis=1); t['max_effect_altlex'] = al.max(axis=1)
        t['best_altlex'] = al.idxmax(axis=1)
        t['beats_all_nulls'] = (t.q_alt < .05) & (t.effect > t.max_effect_shuffled) & (t.effect > t.max_effect_altlex)
        t['key'] = kname; t['claimed_lexicon'] = claimed; rows.append(t.reset_index())
        cnt = {c: dict(q05=int((g.q_alt < .05).sum()), p05=int((g.p_alt < .05).sum()), mean_effect=round(float(g.effect.mean()), 4)) for c, g in a.groupby('condition')}
        summ[kname] = dict(n_signs_tested=len(t), q05_by_condition=cnt, beats_all_nulls=int(t.beats_all_nulls.sum()),
                           beats_all_nulls_signs=t.index[t.beats_all_nulls].tolist())
    R = pd.concat(rows); R.to_csv(f'{OUT}/loo_phonetic_per_sign.csv', index=False)
    json.dump(summ, open(f'{OUT}/loo_phonetic_summary.json', 'w'), indent=1)
    print(json.dumps(summ, indent=1)); return R, summ

if __name__ == '__main__':
    A = part_P()
    summarise_P(A)
