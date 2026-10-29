"""Session 4: comparative look-alikes. Strictly VISUAL resemblance (glyphsim: chamfer + HOG, mirror-invariant);
no reading is implied. Tests:
(a) Does the category of a sign's best foreign look-alike predict its Indus positional class? Statistic:
    mutual information between the look-alike category and the Indus class over signs with a class, against
    10,000 permutations of the class labels. Run with and without stroke-numeral signs, since
    "strokes = numbers" is close to universal.
(b) Indus-internal: is visual similarity between two Indus signs correlated with similarity of their positional
    profiles? Mantel test, 5000 permutations.
(c) Calibration: per script, each M sign's best-match score is compared with the best-match scores for
    the same sign against a size-matched random sample of glyphs from the other scripts. Reported only."""
import os, sys, json, random, collections, re, numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import glyphsim as G
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = f'{ROOT}/outputs/comparanda'; os.makedirs(OUT, exist_ok=True)
CMP = f'{ROOT}/paper/evidence/comparanda'
gM = json.load(open(f'{ROOT}/paper/evidence/glyphs/index.json'))
FM = {k: G.feats(G.norm(v['file'])) for k, v in sorted(gM.items())}; FM = {k: v for k, v in FM.items() if v is not None}
SCRIPTS = ['linear_elamite', 'egyptian', 'cuneiform', 'brahmi', 'linear_a']
def cat(script, key, name):
    if script == 'egyptian':
        m = re.match(r'EGYPTIAN HIEROGLYPH ([A-Z]+)\d', name); return 'Gardiner_' + (m.group(1) if m else '?')
    if script == 'brahmi':
        if 'NUMBER' in name or 'DIGIT' in name: return 'numeral'
        if re.search(r'LETTER (A|AA|I|II|U|UU|E|AI|O|AU|VOCALIC)', name): return 'vowel'
        if 'LETTER' in name: return 'consonant'
        return 'other'
    if script == 'linear_a':
        m = re.match(r'LINEAR A SIGN (AB|A)(\d+)', name)
        if not m: return 'other'
        n = int(m.group(2))
        return 'AB_syllabogram' if m.group(1) == 'AB' else ('A_fraction' if 700 <= n < 800 else 'A_only')
    if script == 'cuneiform': return 'numeric' if 'NUMERIC' in name else 'sign'
    return 'n/a'
GL = {}
for s in SCRIPTS:
    idx = json.load(open(f'{CMP}/{s}/index.json'))
    for k, v in idx.items():
        f = G.feats(G.norm(v['file']))
        if f is not None: GL[(s, k)] = (f, v['name'], cat(s, k, v['name']))
KEYS = list(GL)
def row(m):
    fm = FM[m]; return m, [G.sim(fm, GL[k][0]) for k in KEYS]
if __name__ == '__main__':
    if os.path.exists(f'{OUT}/sim_matrix.npy'):
        A = np.load(f'{OUT}/sim_matrix.npy'); Ms = json.load(open(f'{OUT}/sim_matrix_index.json'))['M']
    else:
        with Pool(8) as P: S = dict(P.map(row, list(FM), chunksize=8))
        Ms = list(S); A = np.array([S[m] for m in Ms])
    np.save(f'{OUT}/sim_matrix.npy', A); json.dump(dict(M=Ms, keys=[list(k) for k in KEYS]), open(f'{OUT}/sim_matrix_index.json', 'w'))
    rows = []
    for i, m in enumerate(Ms):
        for s in SCRIPTS:
            cols = [j for j, k in enumerate(KEYS) if k[0] == s]; v = A[i, cols]; o = np.argsort(-v)[:3]
            others = [j for j, k in enumerate(KEYS) if k[0] != s]; rr = random.Random(__import__('zlib').crc32(f'{m}|{s}'.encode()) % 10**6)  # session 6: was hash()
            ctrl = [A[i, rr.sample(others, len(cols))].max() for _ in range(20)]
            rows.append(dict(M=m, script=s, best=KEYS[cols[o[0]]][1], best_name=GL[KEYS[cols[o[0]]]][1], best_cat=GL[KEYS[cols[o[0]]]][2],
                             score=round(float(v[o[0]]), 3), second=KEYS[cols[o[1]]][1], score2=round(float(v[o[1]]), 3),
                             third=KEYS[cols[o[2]]][1], score3=round(float(v[o[2]]), 3), ctrl_best_mean=round(float(np.mean(ctrl)), 3),
                             label='visual resemblance only; no reading implied'))
    L = pd.DataFrame(rows); L.to_csv(f'{OUT}/lookalikes_top3.csv', index=False)
    # (a) category vs Indus positional class
    cls = pd.read_csv(f'{ROOT}/outputs/structure/sign_classes_M77.csv', dtype=str)
    C = dict(zip(cls['sign'], cls['cls']))
    strokes = set(cls.sign[cls.cls == 'NUMERAL-STROKE'])
    def MI(x, y):
        n = len(x); cx = collections.Counter(x); cy = collections.Counter(y); cxy = collections.Counter(zip(x, y))
        return sum(c/n*np.log2(c*n/(cx[a]*cy[b])) for (a, b), c in cxy.items())
    tests = {}
    for s in ['egyptian', 'brahmi', 'linear_a', 'cuneiform']:
        for excl in [False, True]:
            sub = L[(L.script == s) & L.M.isin(C) & (~L.M.isin(strokes) if excl else True)]
            x = list(sub.best_cat); y = [C[m] for m in sub.M]; obs = MI(x, y); rr = np.random.default_rng(0); null = []
            for _ in range(10000): null.append(MI(x, list(rr.permutation(y))))
            null = np.array(null)
            tests[f'{s}{"_no_strokes" if excl else ""}'] = dict(n=len(x), MI_bits=round(obs, 4), null_mean=round(float(null.mean()), 4),
                p=float((1 + (null >= obs).sum())/(1 + len(null))), crosstab=pd.crosstab(pd.Series(x, name='lookalike_cat'), pd.Series(y, name='indus_class')).to_dict())
            print(s, excl, tests[f'{s}{"_no_strokes" if excl else ""}']['MI_bits'], tests[f'{s}{"_no_strokes" if excl else ""}']['null_mean'], tests[f'{s}{"_no_strokes" if excl else ""}']['p'], flush=True)
    # (b) Indus-internal Mantel: visual similarity vs positional-profile similarity (signs with freq >= 10)
    pos = pd.read_csv(f'{ROOT}/outputs/M77/positional.csv'); pos = pos[pos.total >= 10]
    pos['sign'] = pos.sign.astype(str).str.replace('MSg', '').apply(lambda x: 'M%03d' % int(x) if x.isdigit() else x)
    pos = pos[pos.sign.isin(FM)]; sg = list(pos.sign)
    P_ = pos[['solo_pct', 'initial_pct', 'medial_pct', 'final_pct']].values / 100.0
    n = len(sg); V = np.zeros((n, n))
    for i_ in range(n):
        for j_ in range(i_+1, n): V[i_, j_] = V[j_, i_] = G.sim(FM[sg[i_]], FM[sg[j_]])
    D = -np.abs(P_[:, None, :] - P_[None, :, :]).sum(-1)   # positional similarity = -L1
    iu = np.triu_indices(n, 1)
    from scipy.stats import spearmanr
    obs = spearmanr(V[iu], D[iu]).correlation; rr = np.random.default_rng(1); null = []
    for _ in range(2000):
        pp = rr.permutation(n); null.append(spearmanr(V[iu], D[pp][:, pp][iu]).correlation)
    null = np.array(null)
    ns = [k for k, sgn in enumerate(sg) if sgn not in strokes]; V2 = V[np.ix_(ns, ns)]; D2 = D[np.ix_(ns, ns)]; iu2 = np.triu_indices(len(ns), 1)
    obs2 = spearmanr(V2[iu2], D2[iu2]).correlation; null2 = []
    for _ in range(2000):
        pp = rr.permutation(len(ns)); null2.append(spearmanr(V2[iu2], D2[pp][:, pp][iu2]).correlation)
    null2 = np.array(null2)
    mantel = dict(n_signs=n, rho=float(obs), null_mean=float(null.mean()), p=float((1+(null >= obs).sum())/(1+len(null))),
                  no_strokes=dict(n_signs=len(ns), rho=float(obs2), null_mean=float(null2.mean()), p=float((1+(null2 >= obs2).sum())/(1+len(null2)))))
    print('mantel', mantel)
    # (c) calibration summary
    calib = {s: dict(mean_best=float(L[L.script == s].score.mean()), mean_ctrl=float(L[L.script == s].ctrl_best_mean.mean()),
                     share_best_above_ctrl=float((L[L.script == s].score > L[L.script == s].ctrl_best_mean).mean()),
                     n_score_ge_0_8=int((L[L.script == s].score >= .8).sum())) for s in SCRIPTS}
    print(calib)
    json.dump(dict(category_tests=tests, mantel_visual_vs_position=mantel, calibration=calib), open(f'{OUT}/lookalike_tests.json', 'w'), indent=1, default=str)
