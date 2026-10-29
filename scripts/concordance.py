"""Concordance M77 <-> ICIT(Wells): per-link confidence from distributional + visual evidence; CV accuracy vs Carlson's hand matches;
Hungarian assignment; proposals for unlinked signs."""
import os, re, json, collections, sqlite3, random, numpy as np, pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.linear_model import LogisticRegression
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphsim as G
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = f'{ROOT}/outputs/signmap'; os.makedirs(OUT, exist_ok=True)
# corpora
m = pd.read_csv(f'{ROOT}/data/joyboseroy_indus_decipher/data/m77_indusscript_real_corpus.csv', dtype=str)
def segs_m(seq):
    out, cur = [], []
    for x in seq.split():
        if x == 'MSg0':
            if cur: out.append(cur); cur = []
        else: cur.append('M%03d' % int(x[3:]))
    if cur: out.append(cur)
    return out
ML = [s for q in m.sign_sequence for s in segs_m(q)]
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
WL = [s for t in d.text for s in segs_w(t)]
def prof(L):
    f = collections.Counter(); ini = collections.Counter(); fin = collections.Counter(); solo = collections.Counter()
    left = collections.defaultdict(collections.Counter); right = collections.defaultdict(collections.Counter)
    for s in L:
        for i, x in enumerate(s):
            f[x] += 1
            left[x][s[i-1] if i else '<S>'] += 1; right[x][s[i+1] if i + 1 < len(s) else '</S>'] += 1
        if len(s) == 1: solo[s[0]] += 1
        else: ini[s[0]] += 1; fin[s[-1]] += 1
    N = sum(f.values())
    pos = {x: np.array([ini[x] / f[x], fin[x] / f[x], solo[x] / f[x], np.log(f[x] / N)]) for x in f}
    return f, pos, left, right
fM, posM, lM, rM = prof(ML); fW, posW, lW, rW = prof(WL)
con = sqlite3.connect(f'{ROOT}/map/indus_map.sqlite')
cc = pd.read_sql("select parpola_id, scheme, other_id from sign_concordance where scheme in ('mahadevan','wells')", con)
p2m = cc[cc.scheme == 'mahadevan'].groupby('parpola_id').other_id.apply(lambda v: sorted({'M%03d' % int(re.sub(r'\D', '', x)) for x in v})).to_dict()
p2w = cc[cc.scheme == 'wells'].groupby('parpola_id').other_id.apply(lambda v: sorted({'W%03d' % int(re.sub(r'\D', '', x)) for x in v})).to_dict()
links = set((mm, ww, p) for p in p2m for mm in p2m[p] for ww in p2w.get(p, []))
LP = collections.defaultdict(set)
for mm, ww, p in links: LP[(mm, ww)].add(p)
mcount = collections.Counter(mm for mm, ww in LP); wcount = collections.Counter(ww for mm, ww in LP)
anchors = sorted((mm, ww) for (mm, ww) in LP if mcount[mm] == 1 and wcount[ww] == 1 and fM[mm] >= 3 and fW[ww] >= 3)
print('Carlson M-W links', len(LP), 'one-to-one anchors (freq>=3 both)', len(anchors))
# glyph features
gM = json.load(open(f'{ROOT}/paper/evidence/glyphs/index.json')); gW = json.load(open(f'{ROOT}/paper/evidence/glyphs_W/index.json'))
FM = {k: G.feats(G.norm(f'{ROOT}/' + v['file'])) for k, v in gM.items()}; FW = {k: G.feats(G.norm(f'{ROOT}/' + v['file'])) for k, v in gW.items()}
Msigns = sorted(fM); Wsigns = sorted(w for w in fW)
def vis(mm, ww): return G.sim(FM.get(mm), FW.get(ww)) if FM.get(mm) is not None and FW.get(ww) is not None else np.nan
def vec(cnt, amap, keys):
    v = np.zeros(len(keys) + 2); idx = {k: i for i, k in enumerate(keys)}
    for k, n in cnt.items():
        a = amap.get(k, k)
        if a in ('<S>', '</S>'): v[len(keys) + (a == '</S>')] += n
        elif a in idx: v[idx[a]] += n
    return v / (np.linalg.norm(v) + 1e-9)
def dist_feats(train_anchors):
    keys = [a for a, b in train_anchors]; w2m = {b: a for a, b in train_anchors}
    VL = {x: vec(lM[x], {}, keys) for x in Msigns}; VR = {x: vec(rM[x], {}, keys) for x in Msigns}
    WL_ = {x: vec(lW[x], w2m, keys) for x in Wsigns}; WR_ = {x: vec(rW[x], w2m, keys) for x in Wsigns}
    return VL, VR, WL_, WR_
def pair_feats(mm, ww, D):
    VL, VR, WL_, WR_ = D
    pd_ = np.abs(posM[mm][:3] - posW[ww][:3]).sum(); fd = abs(posM[mm][3] - posW[ww][3])
    return [float(VL[mm] @ WL_[ww]), float(VR[mm] @ WR_[ww]), pd_, fd]
# visual matrix (all M x all W with glyphs) via HOG cosine for speed, chamfer for shortlisted
Wg = [w for w in Wsigns if FW.get(w) is not None]
vis_cache = {}
def V(mm, ww):
    k = (mm, ww)
    if k not in vis_cache: vis_cache[k] = vis(mm, ww)
    return vis_cache[k]
# ---- CV over anchors ----
rng = random.Random(0); A = anchors[:]; rng.shuffle(A); folds = [A[i::5] for i in range(5)]
rows = []; topk = collections.defaultdict(list); hung = []
for fi, test in enumerate(folds):
    train = [a for j, f in enumerate(folds) if j != fi for a in f]
    D = dist_feats(train); used = {b for a, b in train}
    cands = [w for w in Wsigns if w not in used and fW[w] >= 2]
    tm = [a for a, b in test]
    S = {}
    for mm, wt in test:
        for ww in cands:
            pf = pair_feats(mm, ww, D); v = V(mm, ww) if ww in FW and FW[ww] is not None else np.nan
            S[(mm, ww)] = pf + [0.0 if np.isnan(v) else v]
            rows.append(dict(fold=fi, M=mm, W=ww, y=int(ww == wt), cosL=pf[0], cosR=pf[1], posdiff=pf[2], freqdiff=pf[3], vis=S[(mm, ww)][4]))
R = pd.DataFrame(rows)
R['distscore'] = R.cosL + R.cosR - 1.0 * R.posdiff - 0.3 * R.freqdiff
Xc = ['cosL', 'cosR', 'posdiff', 'freqdiff', 'vis']
# out-of-fold logistic calibration (train on other folds' candidate rows)
R['p'] = np.nan; R['p_dist'] = np.nan; R['p_vis'] = np.nan
for fi in range(5):
    tr = R.fold != fi
    for col, X in [('p', Xc), ('p_dist', Xc[:4]), ('p_vis', ['vis'])]:
        lr = LogisticRegression(max_iter=2000, class_weight=None).fit(R.loc[tr, X], R.loc[tr, 'y'])
        R.loc[~tr, col] = lr.predict_proba(R.loc[~tr, X])[:, 1]
acc = {}
for col in ['p', 'p_dist', 'p_vis']:
    t1 = t5 = 0; n = 0
    for (fi, mm), g in R.groupby(['fold', 'M']):
        g = g.sort_values(col, ascending=False); r = list(g.W).index(g[g.y == 1].W.iloc[0]) if g.y.sum() else 999
        t1 += r == 0; t5 += r < 5; n += 1
    acc[col] = dict(top1=t1 / n, top5=t5 / n, n=n)
# Hungarian per fold on combined probability
hacc = []
for fi in range(5):
    g = R[R.fold == fi]; Ms = sorted(g.M.unique()); Ws = sorted(g.W.unique())
    C = np.full((len(Ms), len(Ws)), 1.0); im_ = {x: i for i, x in enumerate(Ms)}; iw = {x: i for i, x in enumerate(Ws)}
    for r in g.itertuples(): C[im_[r.M], iw[r.W]] = -np.log(max(r.p, 1e-9))
    ri, ci = linear_sum_assignment(C)
    truth = {r.M: r.W for r in g[g.y == 1].itertuples()}
    hacc += [Ws[c] == truth.get(Ms[r_]) for r_, c in zip(ri, ci)]
acc['hungarian_combined'] = dict(acc=float(np.mean(hacc)), n=len(hacc))
ncand = R.groupby(['fold', 'M']).size().mean(); acc['mean_candidates'] = float(ncand); acc['chance_top1'] = 1 / ncand
# calibration of p (reliability bins) for top-1 choices
R.to_csv(f'{OUT}/concordance_cv_rows.csv.gz', index=False)
# ---- final model on all anchors -> confidence for every Carlson link + proposals ----
D = dist_feats(anchors)
lr = LogisticRegression(max_iter=2000).fit(R[Xc], R.y)
def prob(mm, ww):
    if mm not in fM or ww not in fW: return np.nan, np.nan, np.nan
    pf = pair_feats(mm, ww, D); v = V(mm, ww); v0 = 0.0 if np.isnan(v) else v
    return float(lr.predict_proba([pf + [v0]])[0, 1]), v, pf
# leave-one-out for anchors: recompute D without the pair itself
link_rows = []
for (mm, ww), ps in sorted(LP.items()):
    if (mm, ww) in anchors:
        Dl = dist_feats([a for a in anchors if a != (mm, ww)]); pf = pair_feats(mm, ww, Dl) if mm in fM and ww in fW else None
    else:
        pf = pair_feats(mm, ww, D) if mm in fM and ww in fW else None
    v = V(mm, ww) if mm in FM and ww in FW else np.nan
    if pf is None: p = np.nan
    else: p = float(lr.predict_proba([pf + [0.0 if np.isnan(v) else v]])[0, 1])
    # rank of ww among all W for this M (combined)
    link_rows.append(dict(M=mm, W=ww, P=';'.join(sorted(ps)), one_to_one=(mm, ww) in anchors, freqM=fM.get(mm, 0), freqW=fW.get(ww, 0),
                          visual_sim=None if np.isnan(v) else round(v, 3), dist_cosL=None if pf is None else round(pf[0], 3), dist_cosR=None if pf is None else round(pf[1], 3),
                          posdiff=None if pf is None else round(pf[2], 3), p_link_raw=p))
L = pd.DataFrame(link_rows)
# per-M normalised support: p / (p + sum of p over top-20 alternative W)
def alt_mass(mm):
    if mm not in fM: return np.nan
    sc = []
    for ww in Wsigns:
        if fW[ww] < 2: continue
        pf = pair_feats(mm, ww, D); v = V(mm, ww) if ww in FW and FW[ww] is not None else np.nan
        sc.append((ww, pf + [0.0 if np.isnan(v) else v]))
    P = lr.predict_proba(np.array([s for _, s in sc]))[:, 1]
    return dict(zip([w for w, _ in sc], P))
allp = {mm: alt_mass(mm) for mm in Msigns if fM[mm] >= 2}
json.dump({k: sorted(v.items(), key=lambda x: -x[1])[:10] for k, v in allp.items()}, open(f'{OUT}/m_to_w_top10.json', 'w'))
pd.DataFrame([(k, w, p) for k, v in allp.items() for w, p in v.items()], columns=['M', 'W', 'p']).to_csv(f'{OUT}/m_w_pair_probs.csv.gz', index=False)
def share(mm, ww):
    a = allp.get(mm)
    if not a or ww not in a: return np.nan
    return a[ww] / sum(a.values())
sibs = collections.defaultdict(set)
for (mm_, ww_) in LP: sibs[mm_].add(ww_)
def rank(mm, ww):
    a = allp.get(mm)
    if not a or ww not in a: return None
    order = [k for k in sorted(a, key=lambda k: -a[k]) if k == ww or k not in sibs[mm]]
    return order.index(ww) + 1
L['support_share'] = [share(a, b) for a, b in zip(L.M, L.W)]
L['rank_among_W'] = [rank(a, b) for a, b in zip(L.M, L.W)]
# link confidence label: combine Carlson (hand match) prior with evidence; calibrated top-1 accuracy by rank bucket from CV
cvrank = []
for (fi, mm), g in R.groupby(['fold', 'M']):
    g = g.sort_values('p', ascending=False); r = list(g.W).index(g[g.y == 1].W.iloc[0]) + 1; cvrank.append(r)
cvrank = np.array(cvrank)
def conf_label(r, v):
    if r is None: return 'untestable (sign absent or rare in one corpus)'
    if r == 1: return 'strong: hand match = top candidate (other hand-matched variants of the same M excluded)'
    if r <= 5: return 'supported: hand match in top 5'
    if r <= 20: return 'weak support'
    return 'unsupported by distribution/visual evidence (check)'
L['confidence'] = [conf_label(r, v) for r, v in zip(L.rank_among_W, L.visual_sim)]
L.to_csv(f'{OUT}/concordance_links_scored.csv', index=False)
# proposals: M signs with no Carlson W
linkedM = set(L.M)
props = []
for mm in Msigns:
    if mm in linkedM or mm not in allp: continue
    a = allp[mm]; best = sorted(a, key=lambda k: -a[k])[:3]
    props.append(dict(M=mm, freqM=fM[mm], top3=[(w, round(a[w] / sum(a.values()), 3)) for w in best]))
json.dump(props, open(f'{OUT}/concordance_proposals_unlinked_M.json', 'w'), indent=0)
# Hungarian global assignment on all M (freq>=2) vs all W (freq>=2) — report agreement with Carlson
Ms = sorted(allp); Ws = sorted({w for v in allp.values() for w in v}); iw = {w: i for i, w in enumerate(Ws)}
C = np.full((len(Ms), len(Ws)), 30.0)
for i, mm in enumerate(Ms):
    for ww, p in allp[mm].items(): C[i, iw[ww]] = -np.log(max(p, 1e-12))
ri, ci = linear_sum_assignment(C)
H = {Ms[r_]: Ws[c] for r_, c in zip(ri, ci)}
carl = collections.defaultdict(set)
for mm, ww in LP: carl[mm].add(ww)
agree = [H[mm] in carl[mm] for mm in Ms if carl.get(mm)]
acc['global_hungarian_agreement_with_carlson'] = dict(agree=float(np.mean(agree)), n=len(agree))
acc['cv_rank_distribution'] = {'r1': float(np.mean(cvrank == 1)), 'r<=5': float(np.mean(cvrank <= 5)), 'r<=20': float(np.mean(cvrank <= 20)), 'median': float(np.median(cvrank))}
acc['n_links'] = len(L); acc['n_anchors'] = len(anchors); acc['label_counts'] = L.confidence.value_counts().to_dict()
pd.DataFrame([dict(M=k, W_hungarian=v, carlson=';'.join(sorted(carl.get(k, [])))) for k, v in H.items()]).to_csv(f'{OUT}/concordance_hungarian.csv', index=False)
json.dump(acc, open(f'{OUT}/concordance_accuracy.json', 'w'), indent=1)
print(json.dumps(acc, indent=1))
