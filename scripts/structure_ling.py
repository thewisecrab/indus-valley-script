"""Linguistic-status measures v2 (per-system shuffled reference; fixed Tamil word tokenisation) + HMM slot-template conformity."""
import os, re, json, random, collections, math, numpy as np, pandas as pd, regex
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s2 = open(f'{ROOT}/scripts/structure2.py').read()
exec(s2.split('# ============ 1. Segmentation')[0])
exec(s2.split('# ============ 3. comparanda for script-type and linguistic status ============')[1].split('NT = sum(len(s) for s in FULL)')[0]
     .replace("elif mode == 'words': u = [w.lower() for w in re.findall(r'\\w+', s) if not w.isdigit()]",
              "elif mode == 'words': u = [w.lower() for w in regex.findall(r'[\\p{L}\\p{M}]+', s)]"))
COMP['Sanskrit words'] = wiki_units('sa', 'words')
def gshuffle(texts, r):
    toks = [x for s in texts for x in s]; r.shuffle(toks); out = []; i = 0
    for s in texts: out.append(toks[i:i + len(s)]); i += len(s)
    return out
def subsample(texts, n_tok, r):
    T = list(texts); r.shuffle(T); out = []; c = 0
    for s in T:
        if c >= n_tok: break
        out.append(s); c += len(s)
    return out
def dedup(L): return [list(t) for t in dict.fromkeys(tuple(s) for s in L)]
budget = 9000
systems = {'Indus M77 (complete lines)': FULL, 'Indus M77 (complete lines, deduplicated)': dedup(FULL), 'Indus ICIT (complete lines)': W_FULL, 'Indus M77 seals only': SEAL}
r0 = random.Random(1)
for k, v in COMP.items(): systems[k + ' (length-matched)'] = length_matched(v, len(FULL), r0)
for k in ['Tamil aksharas', 'English words']: systems[k + ' (natural sentences)'] = COMP[k]
systems['memoryless Zipf (Indus unigrams)'] = memoryless(len(FULL), r0)
systems['no-repeat badges (Indus unigrams)'] = norepeat(len(FULL), r0)
systems['rigid successor (Indus unigrams)'] = rigid(len(FULL), r0)
rows = []
for name, T in systems.items():
    reps = []
    for i in range(20):
        r = random.Random(i); S = subsample(T, budget, r); mm = measures(S); sh = gshuffle(S, r)
        mm['Hcond_shuffled'] = cond_entropy(sh); mm['Hcond_ratio_to_shuffle'] = mm['Hcond'] / mm['Hcond_shuffled']
        mm['r_over_R_shuffled'] = repetition(sh)[0]; reps.append(mm)
    agg = {}
    for k in reps[0]:
        v = np.array([x[k] for x in reps], float); v = v[~np.isnan(v)]
        agg[k] = (float(v.mean()) if len(v) else float('nan'), float(np.percentile(v, 2.5)) if len(v) else float('nan'), float(np.percentile(v, 97.5)) if len(v) else float('nan'))
    row = dict(system=name, **{k: round(v[0], 4) for k, v in agg.items()})
    for k in ('Hcond_ratio_to_shuffle', 'r_over_R', 'Cr', 'Ur'): row[k + '_95'] = f'{agg[k][1]:.3f}–{agg[k][2]:.3f}'
    rows.append(row)
M = pd.DataFrame(rows)
def lee_tree(Cr, Ur): return 'nonlinguistic' if Cr < 4.89 else ('linguistic: segmental' if Ur < 1.09 else 'linguistic: syllabic' if Ur < 1.37 else 'linguistic: logographic')
M['lee_tree'] = [lee_tree(c, u) for c, u in zip(M.Cr, M.Ur)]
M['sproat_rR_rule'] = np.where(M.r_over_R.isna(), 'no repeats', np.where(M.r_over_R > 0.10, 'nonlinguistic side (>0.10)', 'linguistic side (≤0.10)'))
M.to_csv(f'{OUT}/linguistic_measures.csv', index=False)
pd.set_option('display.width', 250)
print(M[['system', 'types', 'mean_len', 'Hcond', 'Hcond_ratio_to_shuffle', 'Hcond_ratio_to_shuffle_95', 'B2', 'B3', 'r_over_R', 'r_over_R_95', 'r_over_R_shuffled', 'repeats_per_token', 'Ur', 'Cr', 'lee_tree']].round(3).to_string())

# ---- HMM slot-template conformity (dedup seals, held-out) ----
from hmmlearn.hmm import CategoricalHMM
SD = [s for s in dedup(SEAL) if len(s) >= 2]
res = []
for seed in range(3):
    r = random.Random(seed); L = list(SD); r.shuffle(L); cut = int(.8 * len(L)); tr, te = L[:cut], L[cut:]
    fc = collections.Counter(x for s in tr for x in s); voc = ['<UNK>', '<END>'] + sorted(x for x in fc if fc[x] >= 5); ix = {x: i for i, x in enumerate(voc)}
    enc = lambda S: [[ix.get(x, 0) for x in s] + [1] for s in S]
    cat = lambda X: (np.concatenate([np.array(x).reshape(-1, 1) for x in X]), [len(x) for x in X])
    a, la = cat(enc(tr)); best = None
    for rs in range(3):
        mdl = CategoricalHMM(n_components=6, n_iter=80, tol=1e-3, random_state=rs + 7 * seed, init_params='ste', n_features=len(voc)); mdl.fit(a, la); sc = mdl.score(a, la)
        if best is None or sc > best[0]: best = (sc, mdl)
    mdl = best[1]
    # slot order = mean relative position of each state in Viterbi paths of training texts
    pos = collections.defaultdict(list)
    for s in enc(tr):
        _, path = mdl.decode(np.array(s).reshape(-1, 1))
        for i, k in enumerate(path[:-1]): pos[k].append(i / max(1, len(s) - 2))
    order = {k: (np.mean(pos[k]) if pos[k] else 9) for k in range(6)}; rank = {k: i for i, k in enumerate(sorted(order, key=order.get))}
    def conform(S):
        ok = 0; ll = 0
        for s in enc(S):
            lp, path = mdl.decode(np.array(s).reshape(-1, 1)); rk = [rank[k] for k in path[:-1]]
            ok += all(x <= y for x, y in zip(rk, rk[1:])); ll += mdl.score(np.array(s).reshape(-1, 1)) / len(s)
        return ok / len(S), ll / len(S)
    sh = [list(s) for s in te]; [random.Random(seed + 100 + i).shuffle(x) for i, x in enumerate(sh)]
    rev = [list(reversed(s)) for s in te]
    cr, lr = conform(te); cs, ls = conform(sh); cv, lv = conform(rev)
    states = [dict(rank=rank[k], mean_rel_pos=round(float(order[k]), 3), top=[voc[i] for i in np.argsort(-mdl.emissionprob_[k])[:6]]) for k in sorted(range(6), key=rank.get)]
    res.append(dict(seed=seed, n_test=len(te), conform_real=cr, conform_shuffled=cs, conform_reversed=cv, ll_real=lr, ll_shuffled=ls, ll_reversed=lv, states=states))
json.dump(dict(measures=M.to_dict('records'), slot_conformity=res), open(f'{OUT}/linguistic_v2_and_slots.json', 'w'), indent=1, default=str)
for x in res: print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in x.items() if k != 'states'}); [print('  ', s) for s in x['states']]
