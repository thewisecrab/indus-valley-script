"""Session 4: branching-entropy (BE) segmentation (Tanaka-Ishii 2005; Zhikov et al. 2010 style forward+backward
increase criterion) compared with the BPE boundaries and the HMM slot boundaries from session 3. Everything is
trained on 80% of the de-duplicated M77 seal texts and evaluated on the held-out 20%. The null for each
agreement is random boundaries with the same number per text (1000 draws). The whole pipeline is repeated
on within-text shuffled corpora."""
import os, sys, json, random, collections, math, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(f'{ROOT}/scripts/structure2.py').read()
exec(src.split('# ============ 1. Segmentation')[0])
exec(src.split('# ============ 1. Segmentation: BPE with held-out description length ============')[1].split('seg = {}')[0])
from hmmlearn.hmm import CategoricalHMM
def dedup(L): return [list(t) for t in dict.fromkeys(tuple(s) for s in L)]
s3 = json.load(open(f'{ROOT}/outputs/structure/structure3_dedup.json'))
sd = s3['segmentation_dedup']['M77_full_dedup']; BPEK = sd['K'][int(np.argmin(sd['real']))]; HK = s3['hmm_seal_dedup']['bestK']

def be_model(train, nmax=2, mincount=3):
    fw = collections.defaultdict(collections.Counter); bw = collections.defaultdict(collections.Counter)
    for s in train:
        t = ['<s>'] + list(s) + ['</s>']
        for i in range(1, len(t)):
            for n in range(1, nmax+1):
                if i-n >= 0: fw[tuple(t[i-n:i])][t[i]] += 1
        r = t[::-1]
        for i in range(1, len(r)):
            for n in range(1, nmax+1):
                if i-n >= 0: bw[tuple(r[i-n:i])][r[i]] += 1
    H = lambda c: -sum(v/sum(c.values())*math.log2(v/sum(c.values())) for v in c.values())
    def ent(tab, ctx):
        for n in range(len(ctx), 0, -1):
            c = tab.get(tuple(ctx[-n:]))
            if c and sum(c.values()) >= mincount: return H(c)
        return None
    return fw, bw, ent
def be_boundaries(s, M):
    fw, bw, ent = M; t = ['<s>'] + list(s) + ['</s>']; n = len(s); out = set()
    for k in range(1, n):          # boundary between s[k-1] and s[k]
        # forward: entropy after context ending at s[k-1] vs after context ending at s[k-2]
        f1 = ent(fw, t[max(0, k-1):k+1]); f0 = ent(fw, t[max(0, k-2):k])
        r = t[::-1]; j = n + 1 - k   # position in reversed seq
        b1 = ent(bw, r[max(0, j-1):j+1]); b0 = ent(bw, r[max(0, j-2):j])
        inc = ((f1 - f0) if f1 is not None and f0 is not None else 0) + ((b1 - b0) if b1 is not None and b0 is not None else 0)
        if inc > 0: out.add(k)
    return out
def bpe_boundaries(units):
    out = set(); k = 0
    for u in units[:-1]:
        k += u.count('+') + 1; out.add(k)
    return out
def hmm_fit(train, K, seed=0, minf=5):
    fc = collections.Counter(x for s in train for x in s); voc = ['<UNK>', '<END>'] + sorted(x for x in fc if fc[x] >= minf); ix = {x: i for i, x in enumerate(voc)}
    enc = lambda S: [[ix.get(x, 0) for x in s] + [1] for s in S]
    X = enc([s for s in train if len(s) >= 2]); a = np.concatenate([np.array(x).reshape(-1, 1) for x in X]); la = [len(x) for x in X]
    best = None
    for rs in range(2):
        m_ = CategoricalHMM(n_components=K, n_iter=60, tol=1e-3, random_state=rs + 10*seed, init_params='ste', n_features=len(voc)); m_.fit(a, la)
        sc = m_.score(a, la)
        if best is None or sc > best[0]: best = (sc, m_)
    return best[1], enc
def hmm_boundaries(s, M):
    m_, enc = M; x = np.array(enc([s])[0]).reshape(-1, 1); st = m_.predict(x)[:len(s)]
    return {k for k in range(1, len(s)) if st[k] != st[k-1]}
def f1(A, B):
    tp = sum(len(a & b) for a, b in zip(A, B)); na = sum(map(len, A)); nb = sum(map(len, B))
    return 2*tp/(na+nb) if na+nb else np.nan
def rand_like(A, lens, r):
    return [set(r.sample(range(1, n), min(len(a), n-1))) if n > 1 else set() for a, n in zip(A, lens)]
def run(L, seed):
    r = random.Random(seed); L = [s for s in L if len(s) >= 2]; r.shuffle(L); cut = int(.8*len(L)); tr, te = L[:cut], L[cut:]
    BEm = be_model(tr); merges = bpe_learn(tr, BPEK); Hm = hmm_fit(tr, HK, seed)
    B = {'BE': [be_boundaries(s, BEm) for s in te], 'BPE': [bpe_boundaries(u) for u in bpe_apply(te, merges)], 'HMM': [hmm_boundaries(s, Hm) for s in te]}
    lens = [len(s) for s in te]; res = {'n_test': len(te), 'boundary_rate': {k: sum(map(len, v))/sum(n-1 for n in lens) for k, v in B.items()}}
    rr = random.Random(seed+99)
    for a, b in [('BE', 'BPE'), ('BE', 'HMM'), ('BPE', 'HMM')]:
        obs = f1(B[a], B[b]); null = [f1(rand_like(B[a], lens, rr), B[b]) for _ in range(1000)]
        res[f'{a}~{b}'] = dict(F1=obs, null_mean=float(np.mean(null)), p=(1+sum(x >= obs for x in null))/1001)
    return res, B, te
L = dedup(SEAL)
out = {'bpe_K_from_dedup_MDL': BPEK, 'hmm_K': HK, 'n_dedup_seal_texts': len(L)}
for cname, corp in [('real', L), ('shuffled', shuf_within(L, random.Random(77)))]:
    rs = [run(corp, s)[0] for s in range(3)]
    agg = {'boundary_rate': {k: float(np.mean([x['boundary_rate'][k] for x in rs])) for k in rs[0]['boundary_rate']}}
    for k in ['BE~BPE', 'BE~HMM', 'BPE~HMM']:
        agg[k] = {m_: float(np.mean([x[k][m_] for x in rs])) for m_ in ['F1', 'null_mean', 'p']}
    out[cname] = agg; print(cname, json.dumps(agg, indent=1), flush=True)
# BE units on the full dedup corpus (for the sign map: most frequent BE-delimited chunks)
BEm = be_model(L); units = collections.Counter()
for s in L:
    b = sorted(be_boundaries(s, BEm)); cuts = [0] + b + [len(s)]
    for i in range(len(cuts)-1):
        u = tuple(s[cuts[i]:cuts[i+1]])
        if len(u) >= 2: units[u] += 1
out['top_BE_units'] = [('+'.join(u), n) for u, n in units.most_common(30)]
json.dump(out, open(f'{ROOT}/outputs/structure/structure4_branching_entropy.json', 'w'), indent=1)
print(out['top_BE_units'][:15])
