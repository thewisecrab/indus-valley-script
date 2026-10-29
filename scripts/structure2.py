"""Segmentation (BPE, held-out MDL), HMM slot grammar, script-type and linguistic-status measures (Rao, Lee/Sproat) with
small-sample corrections and length-matched comparanda."""
import os, re, json, random, math, collections, unicodedata
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import regex
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = f'{ROOT}/outputs/structure'; FIG = f'{ROOT}/figures'
import importlib.util
spec = importlib.util.spec_from_file_location('st', f'{ROOT}/scripts/structure.py')
# reuse corpus loading only (avoid re-running analyses): replicate minimal loaders
m = pd.read_csv(f'{ROOT}/data/joyboseroy_indus_decipher/data/m77_indusscript_real_corpus.csv', dtype=str)
m['tn'] = m.inscription_id.str.split('.').str[0].astype(int)
def segs_m(seq):
    out, cur = [], []
    for x in seq.split():
        if x == 'MSg0':
            if cur: out.append(cur); cur = []
        else: cur.append('M%03d' % int(x[3:]))
    if cur: out.append(cur)
    return out
m['segs'] = m.sign_sequence.apply(segs_m); m['damaged'] = m.sign_sequence.str.contains('MSg0')
codes = pd.read_csv(f'{ROOT}/outputs/m77_codes_digitocr.csv', dtype=str); otype = {int(r.textnum): r.code[0] for r in codes.itertuples()}
m['otype'] = m.tn.map(otype)
LINES = [s for ss in m.segs for s in ss]
FULL = [ss[0] for ss, dmg in zip(m.segs, m.damaged) if not dmg and len(ss) == 1]
SEAL = [ss[0] for ss, dmg, t in zip(m.segs, m.damaged, m.otype) if not dmg and len(ss) == 1 and t == "1"]
d = pd.read_csv(f'{ROOT}/data/lipi/inscriptions.csv', dtype=str, keep_default_na=False)
def segs_w(text):
    out = []
    for part in text.split('/'):
        s = list(reversed(re.findall(r'\d+', part))); cur = []
        for x in s:
            if x in ('000', '999'):
                if cur: out.append(cur); cur = []
            else: cur.append('W' + x)
        if cur: out.append(cur)
    return out
d['segs'] = d.text.apply(segs_w); d['damaged'] = d.text.str.contains(r'000|999|\[|\]')
W_FULL = [s for ss, dmg in zip(d.segs, d.damaged) if not dmg for s in ss]
rng = np.random.default_rng(0); R = random.Random(0); RES = {}

# ============ 1. Segmentation: BPE with held-out description length ============
def bpe_learn(lines, K):
    lines = [list(s) for s in lines]; merges = []
    for _ in range(K):
        pc = collections.Counter(p for s in lines for p in zip(s, s[1:]))
        if not pc: break
        (a, b), n = pc.most_common(1)[0]
        if n < 3: break
        merges.append((a, b)); new = a + '+' + b
        for s in lines:
            i = 0
            while i < len(s) - 1:
                if s[i] == a and s[i+1] == b: s[i:i+2] = [new]
                i += 1
    return merges
def bpe_apply(lines, merges):
    lines = [list(s) for s in lines]
    for a, b in merges:
        new = a + '+' + b
        for s in lines:
            i = 0
            while i < len(s) - 1:
                if s[i] == a and s[i+1] == b: s[i:i+2] = [new]
                i += 1
    return lines
def heldout_bits(train, test, merges):
    tr = bpe_apply(train, merges); te = bpe_apply(test, merges)
    c = collections.Counter(u for s in tr for u in s); V = len(c) + 1; N = sum(c.values())
    # unseen units back off to sign-level spelling cost
    sc = collections.Counter(x for s in train for x in s); SN = sum(sc.values()); SV = len(sc) + 1
    def sign_cost(x): return -math.log2((sc.get(x, 0) + 0.5) / (SN + 0.5 * SV))
    bits = 0.0; nsign = 0
    for s in te:
        for u in s:
            k = u.count('+') + 1; nsign += k
            if u in c: bits += -math.log2(c[u] / (N + 1))
            else: bits += -math.log2(1 / (N + 1)) + sum(sign_cost(x) for x in u.split('+'))
        bits += -math.log2(len(te) / max(1, sum(len(s) for s in te)))  # boundary cost (constant across K)
    return bits / nsign
def seg_eval(lines, Ks=(0, 25, 50, 100, 200, 400, 800), seed=0):
    r = random.Random(seed); L = list(lines); r.shuffle(L); cut = int(.8 * len(L)); tr, te = L[:cut], L[cut:]
    merges = bpe_learn(tr, max(Ks))
    return {K: heldout_bits(tr, te, merges[:K]) for K in Ks}, merges
def shuf_within(lines, r):
    out = []
    for s in lines: s = list(s); r.shuffle(s); out.append(s)
    return out
seg = {}
for name, L in [('M77_full', FULL), ('ICIT_full', W_FULL)]:
    real = [seg_eval(L, seed=s)[0] for s in range(3)]
    sh = [seg_eval(shuf_within(L, random.Random(10 + s)), seed=s)[0] for s in range(3)]
    Ks = list(real[0]); seg[name] = dict(K=Ks, real=[float(np.mean([x[K] for x in real])) for K in Ks], shuffled=[float(np.mean([x[K] for x in sh])) for K in Ks])
_, merges_full = seg_eval(FULL, Ks=(0, 800))
bestK = seg['M77_full']['K'][int(np.argmin(seg['M77_full']['real']))]
units = collections.Counter(u for s in bpe_apply(FULL, merges_full[:bestK]) for u in s if '+' in u)
seg['M77_bestK'] = bestK; seg['M77_top_units'] = units.most_common(40)
# boundary stability across bootstrap re-learning
RES['segmentation'] = seg
fig, ax = plt.subplots(figsize=(6, 4))
for name, c in [('M77_full', 'C0'), ('ICIT_full', 'C1')]:
    ax.plot(seg[name]['K'], seg[name]['real'], 'o-', color=c, label=f'{name} real'); ax.plot(seg[name]['K'], seg[name]['shuffled'], 'o--', color=c, alpha=.6, label=f'{name} shuffled')
ax.set_xlabel('BPE merges K'); ax.set_ylabel('held-out bits per sign'); ax.legend(fontsize=7); ax.set_title('Segmentation: held-out description length')
fig.tight_layout(); fig.savefig(f'{FIG}/seg_bpe_heldout.png', dpi=150); plt.close(fig)

# ============ 2. HMM slot grammar on seal texts ============
from hmmlearn.hmm import CategoricalHMM
def hmm_eval(lines, Ks=(1, 2, 3, 4, 5, 6), seed=0, minf=5):
    r = random.Random(seed); L = [s for s in lines if len(s) >= 2]; r.shuffle(L); cut = int(.8 * len(L)); tr, te = L[:cut], L[cut:]
    fc = collections.Counter(x for s in tr for x in s); voc = ['<UNK>', '<END>'] + sorted(x for x in fc if fc[x] >= minf); ix = {x: i for i, x in enumerate(voc)}
    enc = lambda S: [[ix.get(x, 0) for x in s] + [1] for s in S]
    Xtr = enc(tr); Xte = enc(te)
    cat = lambda X: (np.concatenate([np.array(x).reshape(-1, 1) for x in X]), [len(x) for x in X])
    a, la = cat(Xtr); b, lb = cat(Xte); out = {}; models = {}
    for K in Ks:
        best = None
        for rs in range(3):
            mdl = CategoricalHMM(n_components=K, n_iter=200, random_state=rs + 10 * seed, init_params='ste', n_features=len(voc))
            mdl.fit(a, la); sc = mdl.score(a, la)
            if best is None or sc > best[0]: best = (sc, mdl)
        mdl = best[1]; out[K] = float(mdl.score(b, lb) / len(b)); models[K] = mdl
    return out, models, voc
seal_real = [hmm_eval(SEAL, seed=s) for s in range(2)]
seal_sh = [hmm_eval(shuf_within(SEAL, random.Random(30 + s)), seed=s) for s in range(2)]
Ks = list(seal_real[0][0])
hm = dict(K=Ks, real_ll_per_token=[float(np.mean([x[0][K] for x in seal_real])) for K in Ks], shuffled_ll_per_token=[float(np.mean([x[0][K] for x in seal_sh])) for K in Ks], n_seal_lines=len(SEAL))
hm['gain_real_K_vs_1'] = [r - hm['real_ll_per_token'][0] for r in hm['real_ll_per_token']]
hm['gain_shuffled_K_vs_1'] = [r - hm['shuffled_ll_per_token'][0] for r in hm['shuffled_ll_per_token']]
# describe best-K model (choose K maximizing real held-out)
Kb = Ks[int(np.argmax(hm['real_ll_per_token']))]; mdl, voc = seal_real[0][1][Kb], seal_real[0][2]
st = []
for k in range(Kb):
    e = mdl.emissionprob_[k]; top = np.argsort(-e)[:8]
    st.append(dict(state=k, start_prob=round(float(mdl.startprob_[k]), 3), top_emissions=[(voc[i], round(float(e[i]), 3)) for i in top]))
hm['bestK'] = Kb; hm['states'] = st; hm['transmat'] = np.round(mdl.transmat_, 3).tolist()
RES['hmm_seal_slots'] = hm

# ============ 3. comparanda for script-type and linguistic status ============
def wiki_units(lang, mode):
    t = open(f'{ROOT}/data/comparanda_text/wiki_{lang}.txt', encoding='utf8').read()
    t = re.sub(r'==+[^=]+==+', ' ', t)
    sents = [s for s in re.split(r'[.!?।॥\n]+', t) if len(s.strip()) > 3]
    out = []
    for s in sents:
        if mode == 'chars': u = [c for c in s.lower() if c.isalpha()]
        elif mode == 'aksharas': u = [g for g in regex.findall(r'\X', s) if regex.match(r'\p{L}', g)]
        elif mode == 'words': u = [w.lower() for w in re.findall(r'\w+', s) if not w.isdigit()]
        if u: out.append(u)
    return out
COMP = {'Tamil aksharas': wiki_units('ta', 'aksharas'), 'Sanskrit aksharas': wiki_units('sa', 'aksharas'), 'Finnish letters': wiki_units('fi', 'chars'),
        'English letters': wiki_units('en', 'chars'), 'English words': wiki_units('en', 'words'), 'Finnish words': wiki_units('fi', 'words'),
        'Tamil words': wiki_units('ta', 'words')}
lens = [len(s) for s in FULL]
def length_matched(texts, n_texts, r):
    stream = [u for s in texts for u in s]; out = []
    for _ in range(n_texts):
        L = r.choice(lens); i = r.randrange(0, len(stream) - L); out.append(stream[i:i+L])
    return out
# synthetic non-linguistic baselines matched to M77 unigram distribution and length
uni = collections.Counter(x for s in FULL for x in s); keys = list(uni); w = np.array([uni[k] for k in keys], float); w /= w.sum()
def memoryless(n, r): return [list(rng.choice(keys, size=r.choice(lens), p=w)) for _ in range(n)]
def norepeat(n, r):
    out = []
    for _ in range(n):
        L = r.choice(lens); s = []
        while len(s) < L:
            x = keys[rng.choice(len(keys), p=w)]
            if x not in s: s.append(x)
        out.append(s)
    return out
def rigid(n, r):
    # deterministic successor: a fixed random permutation chain (min-entropy reference)
    perm = keys[:]; r.shuffle(perm); nxt = {perm[i]: perm[(i + 1) % len(perm)] for i in range(len(perm))}; out = []
    for _ in range(n):
        x = keys[rng.choice(len(keys), p=w)]; s = [x]
        for _ in range(r.choice(lens) - 1): s.append(nxt[s[-1]])
        out.append(s)
    return out
# ---------- measures ----------
def H_mm(counter):
    N = sum(counter.values()); K = len(counter)
    return -sum(v / N * math.log2(v / N) for v in counter.values()) + (K - 1) / (2 * N * math.log(2))
def cond_entropy(texts, pad=True):
    big = collections.Counter(); ctx = collections.Counter()
    for s in texts:
        s2 = (['<s>'] + s + ['</s>']) if pad else s
        for a, b in zip(s2, s2[1:]): big[(a, b)] += 1; ctx[a] += 1
    return H_mm(big) - H_mm(ctx)
def unigram_H(texts): return H_mm(collections.Counter(x for s in texts for x in s))
def block_entropy_norm(texts, n):
    c = collections.Counter(tuple(s[i:i+n]) for s in texts for i in range(len(s) - n + 1))
    V = len(set(x for s in texts for x in s)); return H_mm(c) / math.log2(V) if V > 1 else 0
def repetition(texts):
    Rt = rt = 0
    for s in texts:
        seen = set()
        for i, x in enumerate(s):
            if x in seen:
                Rt += 1
                if i > 0 and s[i-1] == x: rt += 1
            seen.add(x)
    return (rt / Rt if Rt else float('nan')), Rt / max(1, sum(len(s) for s in texts))
def lee(texts, a=7):
    pads = [['<s>'] + s + ['</s>'] for s in texts]
    big = collections.Counter((p[i], p[i+1]) for p in pads for i in range(len(p) - 1)); uni_ = collections.Counter(x for p in pads for x in p)
    Nd, Nu = len(big), len(uni_); Sd = sum(1 for v in big.values() if v == 1); Td = sum(big.values())
    F2 = H_mm(big); Ur = F2 / math.log2(Nd / Nu); Cr = Nd / Nu + a * Sd / Td
    return Ur, Cr
def measures(texts, n_tok=None, r=None):
    # small-sample control: subsample texts to a fixed token budget
    if n_tok:
        T = list(texts); r.shuffle(T); out = []; c = 0
        for s in T:
            if c >= n_tok: break
            out.append(s); c += len(s)
        texts = out
    rr, Rrate = repetition(texts); Ur, Cr = lee(texts); H1 = unigram_H(texts); Hc = cond_entropy(texts)
    return dict(n_texts=len(texts), n_tokens=sum(map(len, texts)), types=len(set(x for s in texts for x in s)), mean_len=float(np.mean([len(s) for s in texts])),
                H1=H1, Hcond=Hc, Hcond_over_H1=Hc / H1 if H1 else float('nan'), B1=block_entropy_norm(texts, 1), B2=block_entropy_norm(texts, 2), B3=block_entropy_norm(texts, 3),
                r_over_R=rr, repeats_per_token=Rrate, Ur=Ur, Cr=Cr)
NT = sum(len(s) for s in FULL)
budget = min(NT, 9000)
systems = {'Indus M77 (complete lines)': FULL, 'Indus ICIT (complete lines)': W_FULL, 'Indus M77 seals only': SEAL}
r0 = random.Random(1)
for k, v in COMP.items(): systems[k + ' (length-matched)'] = length_matched(v, len(FULL), r0)
for k in ['Tamil aksharas', 'English words']: systems[k + ' (natural sentences)'] = COMP[k]
systems['memoryless Zipf (Indus unigrams)'] = memoryless(len(FULL), r0)
systems['no-repeat badges (Indus unigrams)'] = norepeat(len(FULL), r0)
systems['rigid successor (Indus unigrams)'] = rigid(len(FULL), r0)
rows = []
for name, T in systems.items():
    reps = [measures(T, budget, random.Random(i)) for i in range(20)]
    agg = {k: (float(np.nanmean([x[k] for x in reps])), float(np.nanpercentile([x[k] for x in reps], 2.5)), float(np.nanpercentile([x[k] for x in reps], 97.5))) for k in reps[0]}
    rows.append(dict(system=name, **{k: round(v[0], 4) for k, v in agg.items()}, **{k + '_ci': (round(v[1], 4), round(v[2], 4)) for k, v in agg.items() if k in ('Hcond', 'r_over_R', 'Cr', 'Ur')}))
M = pd.DataFrame(rows); M.to_csv(f'{OUT}/linguistic_measures.csv', index=False)
RES['linguistic_measures_token_budget'] = budget
# Rao-style relative conditional entropy: position between rigid (min) and memoryless (max) at matched budget
ref_min = M[M.system.str.startswith('rigid')].Hcond.values[0]; ref_max = M[M.system.str.startswith('memoryless')].Hcond.values[0]
M['rao_relative_position'] = (M.Hcond - ref_min) / (ref_max - ref_min)
M.to_csv(f'{OUT}/linguistic_measures.csv', index=False)
# Lee et al. tree as quoted by Sproat 2014: Cr >= 4.89 linguistic; Ur < 1.09 segmental, < 1.37 syllabic, else logographic
def lee_tree(Cr, Ur): return 'nonlinguistic' if Cr < 4.89 else ('linguistic: segmental' if Ur < 1.09 else 'linguistic: syllabic' if Ur < 1.37 else 'linguistic: logographic')
M['lee_tree'] = [lee_tree(c, u) for c, u in zip(M.Cr, M.Ur)]
M['sproat_rr_rule_(>0.10 nonling)'] = np.where(M.r_over_R > 0.10, 'nonlinguistic-like', 'linguistic-like')
M.to_csv(f'{OUT}/linguistic_measures.csv', index=False)
# ---------- script-type: inventory with sample-size correction ----------
def chao1(c):
    f1 = sum(1 for v in c.values() if v == 1); f2 = sum(1 for v in c.values() if v == 2); S = len(c)
    return S + (f1 * (f1 - 1) / (2 * (f2 + 1)))
inv = {}
for name, T in [('M77 all lines', LINES), ('ICIT all', [s for ss in d.segs for s in ss])]:
    c = collections.Counter(x for s in T for x in s)
    inv[name] = dict(tokens=sum(c.values()), observed_types=len(c), hapax=sum(1 for v in c.values() if v == 1), chao1=round(chao1(c), 1),
                     types_covering_80pct=int(np.searchsorted(np.cumsum(sorted(c.values(), reverse=True)) / sum(c.values()), .8) + 1),
                     types_covering_90pct=int(np.searchsorted(np.cumsum(sorted(c.values(), reverse=True)) / sum(c.values()), .9) + 1))
# Heaps curves
fig, ax = plt.subplots(figsize=(6, 4))
for name, T in [('Indus M77', LINES), ('Tamil aksharas', COMP['Tamil aksharas']), ('Sanskrit aksharas', COMP['Sanskrit aksharas']), ('English letters', COMP['English letters']), ('English words', COMP['English words'])]:
    stream = [x for s in T for x in s][:60000]; seen = set(); ys = []
    for i, x in enumerate(stream): seen.add(x); ys.append(len(seen))
    ax.plot(range(1, len(ys) + 1), ys, label=name)
ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xlabel('tokens'); ax.set_ylabel('distinct types'); ax.legend(fontsize=7); ax.set_title('Type growth (Heaps)')
fig.tight_layout(); fig.savefig(f'{FIG}/heaps_comparanda.png', dpi=150); plt.close(fig)
RES['inventory'] = inv
# lengths
RES['text_length'] = dict(M77_full_mean=float(np.mean(lens)), M77_full_median=float(np.median(lens)), M77_full_max=int(max(lens)), share_len_le_5=float(np.mean(np.array(lens) <= 5)),
                          seal_mean=float(np.mean([len(s) for s in SEAL])))
json.dump(RES, open(f'{OUT}/structure2_summary.json', 'w'), indent=1, default=str)
print(json.dumps({k: v for k, v in RES.items() if k != 'hmm_seal_slots'}, indent=1, default=str)[:4000])
print(json.dumps(RES['hmm_seal_slots'], default=str)[:3000])
pd.set_option('display.width', 250)
print(M[['system', 'n_tokens', 'types', 'mean_len', 'H1', 'Hcond', 'rao_relative_position', 'B2', 'B3', 'r_over_R', 'repeats_per_token', 'Ur', 'Cr', 'lee_tree']].round(3).to_string())
