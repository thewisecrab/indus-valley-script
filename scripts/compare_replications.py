"""Session 5: replicate published results on our data and add missing baselines.
1. Yadav et al. 2010 (PLoS ONE 5:e9506): Witten-Bell n-gram held-out perplexity (n=1..5) on an EBUDS-like corpus
   (undamaged single-line M77 texts, one copy per duplicate), plus restoration of a dropped sign with
   'sensitivity' = truth lies inside the smallest candidate set holding 90% of probability mass (their 74%).
   Baselines they did not report: frequency-only (unigram), position-aware unigram, and 90%-set size.
2. Nair 2026 (arXiv 2604.17828): OLS Zipf slope over all ranks and plug-in bigram conditional entropy, with a
   within-inscription permutation null (1000 perms), on deduplicated ICIT/lipi texts.
3. Fuls 2013-style normalised positions (approximation: formula seen only as an abstract) vs our classes.
4. A SIGIL-like synthetic emblem system (cf. Raghavendra 2026): non-linguistic ordered fields with
   field-to-field dependence, length-matched to M77; run the same tests to check specificity."""
import os, json, math, random, collections, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = f'{ROOT}/outputs/compare'
src = open(f'{ROOT}/scripts/structure2.py').read(); exec(src.split('# ============ 1. Segmentation')[0])
OUT = f'{ROOT}/outputs/compare'  # structure2 preamble resets OUT
def dedup(L): return [list(t) for t in dict.fromkeys(tuple(s) for s in L)]
def shuf_within(L, R): return [R.sample(list(t), len(t)) for t in L]
BOS, EOS = '<s>', '</s>'

class WB:
    """Interpolated Witten-Bell n-gram LM over sign tokens, with </s>; base = uniform over V+1."""
    def __init__(self, texts, n):
        self.n = n; self.c = collections.defaultdict(collections.Counter)
        vocab = set()
        for t in texts:
            s = [BOS]*(n-1) + list(t) + [EOS]; vocab.update(t)
            for i in range(n-1, len(s)):
                for k in range(n):  # history length k
                    self.c[tuple(s[i-k:i])][s[i]] += 1
        self.V = len(vocab) + 1; self.vocab = sorted(vocab); self.cache = {}
        self.tot = {h: sum(v.values()) for h, v in self.c.items()}; self.T = {h: len(v) for h, v in self.c.items()}
    def p(self, w, h):
        key = (w, h)
        if key in self.cache: return self.cache[key]
        lower = 1.0/self.V if len(h) == 0 else self.p(w, h[1:])
        if len(h) == 0:
            hh = ()
            r = (self.c[hh][w] + self.T[hh]*lower)/(self.tot[hh] + self.T[hh])
        elif h in self.tot:
            r = (self.c[h][w] + self.T[h]*lower)/(self.tot[h] + self.T[h])
        else: r = lower
        self.cache[key] = r; return r
    def logp(self, t):
        s = [BOS]*(self.n-1) + list(t) + [EOS]
        return sum(math.log2(self.p(s[i], tuple(s[i-self.n+1:i]) if self.n > 1 else ())) for i in range(self.n-1, len(s)))

def folds(L, k=5, seed=0):
    idx = list(range(len(L))); random.Random(seed).shuffle(idx)
    return [[L[i] for i in idx[f::k]] for f in range(k)]

def perplexity_cv(L, ns=(1, 2, 3, 4, 5), seed=0):
    F = folds(L, seed=seed); res = {}
    for n in ns:
        H = []; N = 0
        for f in range(5):
            tr = [t for g in range(5) if g != f for t in F[g]]; m = WB(tr, n)
            for t in F[f]: H.append(-m.logp(t)); N += len(t) + 1
        h = sum(H)/N; res[n] = dict(cross_entropy_bits=round(h, 3), perplexity=round(2**h, 2))
    return res

def pos_unigram(tr):
    c = {k: collections.Counter() for k in ('I', 'M', 'F', 'S')}
    for t in tr:
        for i, x in enumerate(t): c['S' if len(t) == 1 else 'I' if i == 0 else 'F' if i == len(t)-1 else 'M'][x] += 1
    return c

def restoration(L, seed=0, orders=(2, 3)):
    F = folds(L, seed=seed); R = random.Random(seed); out = collections.defaultdict(list)
    for f in range(5):
        tr = [t for g in range(5) if g != f for t in F[g]]; models = {n: WB(tr, n) for n in orders}
        vocab = models[orders[0]].vocab; uni = collections.Counter(x for t in tr for x in t); pu = pos_unigram(tr)
        for t in F[f]:
            if len(t) < 2: continue
            i = R.randrange(len(t)); truth = t[i]
            slot = 'I' if i == 0 else 'F' if i == len(t)-1 else 'M'
            scorers = {'unigram': lambda c: math.log2(uni[c] + 0.01),
                       'position_unigram': lambda c: math.log2(pu[slot][c] + 0.01*(uni[c] + 0.01))}
            for n in orders: scorers[f'WB{n}'] = (lambda m: (lambda c: m.logp(t[:i] + [c] + t[i+1:])))(models[n])
            for name, sc in scorers.items():
                lp = np.array([sc(c) for c in vocab]); p = np.exp2(lp - lp.max()); p /= p.sum()
                order = np.argsort(-p); ranks = {vocab[j]: r for r, j in enumerate(order)}
                k90 = int(np.searchsorted(np.cumsum(p[order]), 0.90) + 1)
                r = ranks.get(truth, len(vocab))
                out[name].append((r == 0, r < 5, r < k90, k90))
    return {k: dict(top1=round(float(np.mean([x[0] for x in v])), 3), top5=round(float(np.mean([x[1] for x in v])), 3),
                    sensitivity90=round(float(np.mean([x[2] for x in v])), 3), mean_set90=round(float(np.mean([x[3] for x in v])), 1),
                    n=len(v)) for k, v in out.items()}

def zipf_ols(L):
    c = np.array(sorted(collections.Counter(x for t in L for x in t).values(), reverse=True), float)
    r = np.arange(1, len(c)+1); b, a = np.polyfit(np.log10(r), np.log10(c), 1)
    pred = a + b*np.log10(r); ss = ((np.log10(c)-pred)**2).sum(); st = ((np.log10(c)-np.log10(c).mean())**2).sum()
    return round(float(b), 3), round(float(1-ss/st), 3)

def hcond(L):
    big = collections.Counter((t[i], t[i+1]) for t in L for i in range(len(t)-1)); left = collections.Counter()
    for (a, b), v in big.items(): left[a] += v
    N = sum(big.values()); return -sum(v/N*math.log2(v/left[a]) for (a, b), v in big.items())

def hcond_perm(L, nperm=1000, seed=0):
    obs = hcond(L); R = random.Random(seed); null = []
    for _ in range(nperm):
        S = [R.sample(t, len(t)) for t in L]; null.append(hcond(S))
    null = np.array(null)
    return dict(obs=round(obs, 3), null_mean=round(float(null.mean()), 3), null_sd=round(float(null.std()), 3),
                p=float((1 + (null <= obs).sum())/(nperm + 1)))

def sigil_like(lengths, seed=0):
    """Non-linguistic emblem system: up to 6 ordered fields (owner-group, title, commodity, quantity, office, tag);
    each field has a Zipfian vocabulary; field values depend on the previous field's value (Dirichlet tables);
    text length chosen from the empirical length list by dropping optional fields. No phonology, no words."""
    R = np.random.default_rng(seed); sizes = [120, 60, 90, 12, 50, 30]; base = 0; fields = []
    for s in sizes:
        w = 1/np.arange(1, s+1)**1.1; fields.append((np.arange(base, base+s), w/w.sum())); base += s
    trans = [None] + [R.dirichlet(np.full(sizes[k], 0.05), size=sizes[k-1]) for k in range(1, 6)]
    texts = []
    for L in lengths:
        L = min(L, 6); keep = sorted(R.choice(6, size=L, replace=False)) if L < 6 else list(range(6))
        prev = None; t = []
        for k in range(6):
            ids, w = fields[k]
            if prev is None or trans[k] is None: j = R.choice(len(ids), p=w)
            else: j = R.choice(len(ids), p=0.5*w + 0.5*trans[k][prev])
            prev = j
            if k in keep: t.append(f'S{ids[j]:03d}')
        texts.append(t)
    return texts

res = {}
EB = dedup(FULL); res['corpus_sizes'] = dict(M77_single_line_undamaged=len(FULL), EBUDS_like_dedup=len(EB),
    EBUDS_published=1548, ICIT_lipi_undamaged_lines=len(W_FULL), ICIT_lipi_dedup=len(dedup(W_FULL)))
print(res['corpus_sizes'], flush=True)
# 1. Yadav replication
res['yadav_published'] = dict(perplexity={1: 68.82, 2: 26.69, 3: 26.09, 4: 25.26, 5: 25.26}, sensitivity90=0.74)
res['perplexity'] = {'M77_EBUDS_like_dedup': perplexity_cv(EB), 'M77_with_duplicates': perplexity_cv(FULL),
                     'ICIT_dedup': perplexity_cv(dedup(W_FULL)),
                     'M77_dedup_within_shuffled': perplexity_cv(shuf_within(EB, random.Random(5)))}
print(json.dumps(res['perplexity']), flush=True)
res['restoration'] = {'M77_EBUDS_like_dedup': restoration(EB), 'M77_with_duplicates': restoration(FULL),
                      'ICIT_dedup': restoration(dedup(W_FULL))}
print(json.dumps(res['restoration']), flush=True)
# 2. Nair replication
W_ALL = [s for ss in d.segs for s in ss]  # incl. damaged texts (Nair did not state damage filtering)
res['nair_published'] = dict(n_texts=1916, signs=584, tokens=11110, zipf_slope=-1.49, zipf_R2=0.96, hcond_bits=3.232)
for name, L in [('ICIT_lipi_dedup_undamaged', dedup(W_FULL)), ('ICIT_lipi_dedup_all_segments', dedup(W_ALL)),
                ('M77_EBUDS_like_dedup', EB)]:
    z = zipf_ols(L); res.setdefault('nair_replication', {})[name] = dict(
        n_texts=len(L), signs=len({x for t in L for x in t}), tokens=sum(map(len, L)), zipf_slope=z[0], zipf_R2=z[1],
        hcond=hcond_perm(L))
print(json.dumps(res['nair_replication']), flush=True)
# 3. Fuls-style normalised position (approximation)
cls = pd.read_csv(f'{ROOT}/outputs/structure/sign_classes_M77.csv')
pos = collections.defaultdict(list)
for t in EB:
    if len(t) >= 2:
        for i, x in enumerate(t): pos[x].append(i/(len(t)-1))
rows = []
for s, v in pos.items():
    if len(v) < 10: continue
    m = float(np.mean(v)); fc = 'initial' if m <= 0.15 else 'terminal' if m >= 0.85 else 'early-medial' if m < 0.4 else 'mid-medial' if m <= 0.6 else 'late-medial'
    rows.append(dict(sign=s, n=len(v), nwsp_approx=round(m, 3), fuls_style_class=fc))
fp = pd.DataFrame(rows).merge(cls[['sign', 'cls']], on='sign', how='left'); fp.to_csv(f'{OUT}/fuls_style_positions_M77.csv', index=False)
ct = pd.crosstab(fp.cls.fillna('not classed'), fp.fuls_style_class); ct.to_csv(f'{OUT}/fuls_vs_our_classes_crosstab.csv')
res['fuls_style'] = dict(n_signs=len(fp), crosstab=ct.to_dict(),
    our_INITIAL_mapped_initial_or_early=float(fp[fp.cls == 'INITIAL'].fuls_style_class.isin(['initial', 'early-medial']).mean()),
    our_TERMINAL_mapped_terminal=float((fp[fp.cls == 'TERMINAL'].fuls_style_class == 'terminal').mean()),
    our_PRETERMINAL_mapped_late=float(fp[fp.cls == 'PRE-TERMINAL'].fuls_style_class.isin(['late-medial', 'terminal']).mean()))
print(json.dumps({k: v for k, v in res['fuls_style'].items() if k != 'crosstab'}), flush=True)
# 4. SIGIL-like synthetic baseline
SY = dedup(sigil_like([len(t) for t in EB], seed=1))
z = zipf_ols(SY)
res['sigil_like'] = dict(n_texts=len(SY), signs=len({x for t in SY for x in t}), zipf_slope=z[0], zipf_R2=z[1],
    hcond=hcond_perm(SY, 300), perplexity=perplexity_cv(SY), restoration=restoration(SY))
print(json.dumps(res['sigil_like']), flush=True)
json.dump(res, open(f'{OUT}/replications.json', 'w'), indent=1, default=str)
