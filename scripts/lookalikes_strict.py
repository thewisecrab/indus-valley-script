"""Session 7: stricter controls for the Linear Elamite look-alike signal (session-6 finding: mean best-match 0.663 vs
0.627 for size-matched random glyphs from other scripts). Strictly VISUAL resemblance; no reading or link implied.
Comparison scripts: the five of lookalikes.py plus five more Noto (SIL OFL 1.1) repertoires: Cypro-Minoan, Linear B,
Anatolian hieroglyphs, Phoenician and Old Persian cuneiform (later than the Indus script; used as style controls).
No open glyph source was found for Proto-Elamite or proto-cuneiform (see render_comparanda.py).
For each target script T, statistic = mean over query signs of the best similarity to any glyph of T. Nulls:
  N1 size-matched random glyphs from all other scripts (as in lookalikes.py);
  N2 complexity-matched: each glyph of T is replaced by a random one of its 10 nearest non-T glyphs in a
     complexity space (ink share, connected components, holes, skeleton end points, skeleton junctions, skeleton
     length, aspect ratio; rank-normalised);
  N3 query specificity: the same N2 advantage computed with query glyphs drawn from each OTHER script instead of the
     Indus signs. If T beats its matched controls for arbitrary queries too, the advantage is a property of T's
     glyph style, not of an Indus-T resemblance.
Queries: M77 sign crops (private), all signs and with stroke numerals excluded; and, as a rendering check, the Wells/ICIT
signs rendered from a modern font (SK Indus Script font, private renders). Per-sign advantages (best match minus the
sign's mean N2 control best) are also summarised (median, share > 0, 10% trimmed mean, by complexity tercile). 1,000 null draws; BH over target scripts.
Output: outputs/comparanda/lookalikes_strict.json, lookalikes_strict_table.csv"""
import os, sys, json, random, unicodedata, zlib
import numpy as np, pandas as pd, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import glyphsim as G
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = f'{ROOT}/outputs/comparanda'
CMP = f'{ROOT}/paper/evidence/comparanda'; F = f'{ROOT}/data/fonts_open'
NEW = {'cypro_minoan': ('NotoSansCyproMinoan', 'CYPRO-MINOAN SIGN'), 'linear_b': ('NotoSansLinearB', 'LINEAR B'),
       'anatolian': ('NotoSansAnatolianHieroglyphs', 'ANATOLIAN HIEROGLYPH'), 'phoenician': ('NotoSansPhoenician', 'PHOENICIAN LETTER'),
       'old_persian': ('NotoSansOldPersian', 'OLD PERSIAN SIGN')}
SCRIPTS = ['linear_elamite', 'egyptian', 'cuneiform', 'brahmi', 'linear_a'] + list(NEW)
NDRAW, K = 1000, 10
def render(script, font, prefix):
    if os.path.exists(f'{CMP}/{script}/index.json'): return
    from fontTools.ttLib import TTFont
    path = f'{F}/{font}-Regular.ttf'; cmap = TTFont(path).getBestCmap(); fnt = ImageFont.truetype(path, 96)
    os.makedirs(f'{CMP}/{script}', exist_ok=True); idx = {}
    for cp in sorted(cmap):
        name = unicodedata.name(chr(cp), '')
        if not name.startswith(prefix): continue
        im = Image.new('L', (200, 200), 255); ImageDraw.Draw(im).text((20, 20), chr(cp), font=fnt, fill=0)
        if (np.array(im) < 128).sum() < 20: continue
        fn = f'{CMP}/{script}/U{cp:05X}.png'; im.save(fn); idx[f'U+{cp:05X}'] = dict(file=fn, name=name)
    json.dump(idx, open(f'{CMP}/{script}/index.json', 'w'), indent=0)
def thin(b):  # Zhang-Suen thinning on a 0/1 array
    s = np.pad(b.astype(np.uint8), 1); changed = True
    while changed:
        changed = False
        for step in (0, 1):
            P = [np.roll(np.roll(s, dy, 0), dx, 1) for dy, dx in [(1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1)]]
            # neighbours P2..P9 clockwise from north: north is row-1 -> roll(+1) brings row-1 into place
            p2, p3, p4, p5, p6, p7, p8, p9 = P
            Bn = sum(P); seq = [p2, p3, p4, p5, p6, p7, p8, p9, p2]
            A = sum(((seq[i] == 0) & (seq[i + 1] == 1)).astype(int) for i in range(8))
            c = (p2 * p4 * p6 == 0) if step == 0 else (p2 * p4 * p8 == 0)
            d = (p4 * p6 * p8 == 0) if step == 0 else (p2 * p6 * p8 == 0)
            m = (s == 1) & (Bn >= 2) & (Bn <= 6) & (A == 1) & c & d
            if m.any(): s[m] = 0; changed = True
    return s[1:-1, 1:-1]
def complexity(b):
    b = b.astype(np.uint8); n, _ = cv2.connectedComponents(b, connectivity=8)
    nb, _ = cv2.connectedComponents(1 - np.pad(b, 1), connectivity=4); holes = nb - 2
    sk = thin(b); nbh = cv2.filter2D(sk.astype(np.float32), -1, np.ones((3, 3), np.float32), borderType=cv2.BORDER_CONSTANT) - sk
    ends = int(((sk == 1) & (nbh == 1)).sum()); junc = int(((sk == 1) & (nbh >= 3)).sum())
    ys, xs = np.where(b); ar = (np.ptp(xs) + 1) / (np.ptp(ys) + 1)
    return [b.mean(), n - 1, holes, ends, junc, int(sk.sum()), np.log(ar)]
def load():
    for s, (f, p) in NEW.items(): render(s, f, p)
    gM = json.load(open(f'{ROOT}/paper/evidence/glyphs/index.json'))
    FM = {k: G.feats(G.norm(v['file'])) for k, v in sorted(gM.items())}; FM = {k: v for k, v in FM.items() if v is not None}
    GL = []
    for s in SCRIPTS:
        for k, v in sorted(json.load(open(f'{CMP}/{s}/index.json')).items()):
            f = G.feats(G.norm(v['file']))
            if f is not None: GL.append((s, k, f))
    return FM, GL
def simmat(Q, Gf):
    return np.array([[G.sim(q, g) for g in Gf] for q in Q])
if __name__ == '__main__':
    FM, GL = load()
    cls = pd.read_csv(f'{ROOT}/outputs/structure/sign_classes_M77.csv', dtype=str)
    strokes = set(cls.sign[cls.cls == 'NUMERAL-STROKE'])
    Ms = list(FM); Ms_ns = [m for m in Ms if m not in strokes]
    gscript = np.array([g[0] for g in GL]); Gf = [g[2] for g in GL]
    print('glyphs per script', {s: int((gscript == s).sum()) for s in SCRIPTS}, 'Indus queries', len(Ms), 'excl strokes', len(Ms_ns), flush=True)
    Cx = np.array([complexity(g[2]['b']) for g in GL], float)
    R = np.argsort(np.argsort(Cx, 0), 0) / len(Cx)          # rank-normalised complexity
    CxM = np.array([complexity(FM[m]['b']) for m in Ms], float)
    A = simmat([FM[m] for m in Ms], Gf)                       # Indus x glyphs
    gW = json.load(open(f'{ROOT}/paper/evidence/glyphs_W/index.json')) if os.path.exists(f'{ROOT}/paper/evidence/glyphs_W/index.json') else {}
    FW = [G.feats(G.norm(os.path.join(ROOT, v['file']))) for k, v in sorted(gW.items())]; FW = [f for f in FW if f is not None]
    AW = simmat(FW, Gf) if FW else None; print('W font queries', len(FW), flush=True)
    terc = np.digitize(CxM[:, 5], np.quantile(CxM[:, 5], [1/3, 2/3]))  # skeleton-length terciles of the Indus signs
    rng = np.random.default_rng(7)
    # other-script query sets: up to 150 glyphs per script
    qidx = {s: np.sort(rng.choice(np.where(gscript == s)[0], min(150, (gscript == s).sum()), replace=False)) for s in SCRIPTS}
    QA = {s: simmat([Gf[i] for i in qidx[s]], Gf) for s in SCRIPTS}
    res, rows = {}, []
    for T in SCRIPTS:
        tcol = np.where(gscript == T)[0]; pool = np.where(gscript != T)[0]
        d = ((R[tcol][:, None, :] - R[pool][None, :, :]) ** 2).sum(-1); nn = pool[np.argsort(d, 1)[:, :K]]
        r = random.Random(zlib.crc32(T.encode()))
        N1 = [np.array(r.sample(list(pool), len(tcol))) for _ in range(NDRAW)]
        N2 = [np.array([nn[i, r.randrange(K)] for i in range(len(tcol))]) for _ in range(NDRAW)]
        def stat(M):  # M: queries x glyphs
            obs = M[:, tcol].max(1).mean(); n1 = np.array([M[:, c].max(1).mean() for c in N1]); n2 = np.array([M[:, c].max(1).mean() for c in N2])
            return obs, n1, n2
        out = {}
        qsets = [('indus_all', A), ('indus_no_strokes', A[[Ms.index(m) for m in Ms_ns]])] + ([('indus_W_font_renders', AW)] if AW is not None else [])
        # per-sign advantage of the M77 crops against N2
        best = A[:, tcol].max(1); ctrl = np.mean([A[:, c].max(1) for c in N2[:200]], 0); adv = best - ctrl
        srt = np.sort(adv); trim = srt[int(.1 * len(srt)):int(.9 * len(srt))].mean()
        per_sign = dict(median=round(float(np.median(adv)), 4), share_positive=round(float((adv > 0).mean()), 3), trimmed_mean_10pct=round(float(trim), 4),
                        by_complexity_tercile={['simple', 'middle', 'complex'][t]: round(float(adv[terc == t].mean()), 4) for t in range(3)})
        for qname, M in qsets:
            obs, n1, n2 = stat(M)
            out[qname] = dict(n_queries=int(M.shape[0]), mean_best=round(float(obs), 4), N1_mean=round(float(n1.mean()), 4), N1_p=float((1 + (n1 >= obs).sum()) / (1 + NDRAW)),
                              N2_mean=round(float(n2.mean()), 4), N2_p=float((1 + (n2 >= obs).sum()) / (1 + NDRAW)), advantage_N2=round(float(obs - n2.mean()), 4),
                              z_N2=round(float((obs - n2.mean()) / (n2.std() + 1e-12)), 2))
        qadv = {}
        for S in SCRIPTS:
            if S == T: continue
            obs, n1, n2 = stat(QA[S]); qadv[S] = round(float(obs - n2.mean()), 4)
        ia = out['indus_no_strokes']['advantage_N2']
        out['other_script_queries_advantage_N2'] = qadv; out['per_sign_advantage_M77_crops'] = per_sign
        out['indus_advantage_rank_among_query_sets'] = f"{1 + sum(v >= ia for v in qadv.values())} of {1 + len(qadv)}"
        out['complexity_T_median'] = dict(zip(['ink', 'components', 'holes', 'ends', 'junctions', 'skeleton_len', 'log_aspect'], np.round(np.median(Cx[tcol], 0), 3).tolist()))
        res[T] = out
        rows.append(dict(script=T, n_glyphs=len(tcol), **{f'{q}_{k}': v for q in ['indus_all', 'indus_no_strokes', 'indus_W_font_renders'] if q in out for k, v in out[q].items() if k != 'n_queries'},
                         indus_rank_among_query_sets=out['indus_advantage_rank_among_query_sets'],
                         max_other_query_advantage=max(qadv.values()), median_other_query_advantage=float(np.median(list(qadv.values())))))
        print(T, out['indus_no_strokes'], out['indus_advantage_rank_among_query_sets'], flush=True)
    D = pd.DataFrame(rows)
    for q in [x for x in ['indus_all', 'indus_no_strokes', 'indus_W_font_renders'] if f'{x}_N2_p' in D]:
        p = D[f'{q}_N2_p'].values; o = np.argsort(p); m = len(p); qv = np.empty(m); prev = 1
        for rank, i in reversed(list(enumerate(o, 1))): prev = min(prev, p[i] * m / rank); qv[i] = prev
        D[f'{q}_N2_q_BH'] = qv
    D.to_csv(f'{OUT}/lookalikes_strict_table.csv', index=False)
    json.dump(dict(scripts=res, indus_complexity_median=dict(zip(['ink', 'components', 'holes', 'ends', 'junctions', 'skeleton_len', 'log_aspect'], np.round(np.median(CxM, 0), 3).tolist())),
                   n_draws=NDRAW, k_nearest=K, label='visual resemblance only; no reading or historical link implied'),
              open(f'{OUT}/lookalikes_strict.json', 'w'), indent=1)
    print(D[['script', 'n_glyphs', 'indus_no_strokes_mean_best', 'indus_no_strokes_N1_mean', 'indus_no_strokes_N1_p', 'indus_no_strokes_N2_mean', 'indus_no_strokes_N2_p', 'indus_no_strokes_N2_q_BH', 'indus_rank_among_query_sets']].to_string())
