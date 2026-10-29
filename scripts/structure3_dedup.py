"""Duplicate-aware controls (cf. Bose 2026): segmentation and HMM gains when exact duplicate texts cannot straddle train/test."""
import os, sys, json, random, collections, math, importlib.util, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(f'{ROOT}/scripts/structure2.py').read().split('# ============ 1. Segmentation')[0]
exec(src)
s2 = open(f'{ROOT}/scripts/structure2.py').read()
exec(s2.split('# ============ 1. Segmentation: BPE with held-out description length ============')[1].split('seg = {}')[0])
def dedup(L): return [list(t) for t in dict.fromkeys(tuple(s) for s in L)]
out = {'dup_share_M77_full': 1 - len(dedup(FULL)) / len(FULL), 'dup_share_ICIT_full': 1 - len(dedup(W_FULL)) / len(W_FULL), 'dup_share_seal': 1 - len(dedup(SEAL)) / len(SEAL)}
seg = {}
for name, L in [('M77_full_dedup', dedup(FULL)), ('ICIT_full_dedup', dedup(W_FULL))]:
    real = [seg_eval(L, seed=s)[0] for s in range(3)]; sh = [seg_eval(shuf_within(L, random.Random(10 + s)), seed=s)[0] for s in range(3)]
    Ks = list(real[0]); seg[name] = dict(K=Ks, real=[float(np.mean([x[K] for x in real])) for K in Ks], shuffled=[float(np.mean([x[K] for x in sh])) for K in Ks])
out['segmentation_dedup'] = seg
from hmmlearn.hmm import CategoricalHMM
def hmm_eval(lines, Ks=(1, 2, 3, 4, 5), seed=0, minf=5):
    r = random.Random(seed); L = [s for s in lines if len(s) >= 2]; r.shuffle(L); cut = int(.8 * len(L)); tr, te = L[:cut], L[cut:]
    fc = collections.Counter(x for s in tr for x in s); voc = ['<UNK>', '<END>'] + sorted(x for x in fc if fc[x] >= minf); ix = {x: i for i, x in enumerate(voc)}
    enc = lambda S: [[ix.get(x, 0) for x in s] + [1] for s in S]
    cat = lambda X: (np.concatenate([np.array(x).reshape(-1, 1) for x in X]), [len(x) for x in X])
    a, la = cat(enc(tr)); b, lb = cat(enc(te)); res = {}; best_models = {}
    for K in Ks:
        best = None
        for rs in range(2):
            mdl = CategoricalHMM(n_components=K, n_iter=60, tol=1e-3, random_state=rs + 10 * seed, init_params='ste', n_features=len(voc)); mdl.fit(a, la); sc = mdl.score(a, la)
            if best is None or sc > best[0]: best = (sc, mdl)
        res[K] = float(best[1].score(b, lb) / len(b)); best_models[K] = best[1]
    return res, best_models, voc
which = sys.argv[1] if len(sys.argv) > 1 else 'both'
SD = dedup(SEAL)
rr = [hmm_eval(SD, seed=s) for s in range(2)]; ss = [hmm_eval(shuf_within(SD, random.Random(30 + s)), seed=s) for s in range(2)]
Ks = list(rr[0][0])
h = dict(K=Ks, n_lines=len(SD), real=[float(np.mean([x[0][K] for x in rr])) for K in Ks], shuffled=[float(np.mean([x[0][K] for x in ss])) for K in Ks])
h['gain_real'] = [x - h['real'][0] for x in h['real']]; h['gain_shuffled'] = [x - h['shuffled'][0] for x in h['shuffled']]
Kb = Ks[int(np.argmax(h['real']))]; mdl, voc = rr[0][1][Kb], rr[0][2]
h['bestK'] = Kb; h['states'] = [dict(state=k, start=round(float(mdl.startprob_[k]), 3), top=[(voc[i], round(float(mdl.emissionprob_[k][i]), 3)) for i in np.argsort(-mdl.emissionprob_[k])[:8]]) for k in range(Kb)]
h['transmat'] = np.round(mdl.transmat_, 3).tolist()
out['hmm_seal_dedup'] = h
json.dump(out, open(f'{ROOT}/outputs/structure/structure3_dedup.json', 'w'), indent=1, default=str)
print(json.dumps(out, indent=1, default=str)[:6000])
