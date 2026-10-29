"""Structural analysis (session 3). Primary corpus: M77 lines (reading order; MSg0 = damage breaker).
Replication: ICIT-derived lipi corpus via Carlson P->M / P->W concordance (unverified hand matches).
Outputs: outputs/structure/*.csv|json ; figures/*.png"""
import os, re, json, random, math, collections, sqlite3, csv
import numpy as np, pandas as pd
from scipy.stats import binomtest
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = f'{ROOT}/outputs/structure'; FIG = f'{ROOT}/figures'
rng = np.random.default_rng(0); R = random.Random(0)

# ---------------- corpora ----------------
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
codes = pd.read_csv(f'{ROOT}/outputs/m77_codes_digitocr.csv', dtype=str)
otype = {int(r.textnum): r.code[0] for r in codes.itertuples()}
m['otype'] = m.tn.map(otype)  # '1' seal, '2' sealing, '3' miniature tablet, ...
LINES = [s for ss in m.segs for s in ss]               # damage-free stretches
FULL = [ss[0] for ss, dmg in zip(m.segs, m.damaged) if not dmg and len(ss) == 1]   # complete undamaged lines
# ICIT
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
# concordance M <-> W through Parpola numbers
con = sqlite3.connect(f'{ROOT}/map/indus_map.sqlite')
cc = pd.read_sql("select parpola_id, scheme, other_id from sign_concordance where scheme in ('mahadevan','wells')", con)
p2m = cc[cc.scheme == 'mahadevan'].groupby('parpola_id').other_id.apply(list).to_dict()
p2w = cc[cc.scheme == 'wells'].groupby('parpola_id').other_id.apply(list).to_dict()
m2w = collections.defaultdict(set); m2p = collections.defaultdict(set)
for p, ms in p2m.items():
    for mm in ms:
        m2p[mm].add(p)
        for w in p2w.get(p, []): m2w[mm].add(w)
desc = dict(con.execute("select sign_id, description from signs where sign_id like 'P%'").fetchall())

# ---------------- visual classes from hand-checked plates (paper/evidence) ----------------
NUM_SHORT = {'M097':1,'M098':1,'M099':2,'M100':2,'M101':2,'M102':3,'M103':3,'M104':4,'M105':4,'M106':5,'M107':5,'M108':6,'M109':6,
             'M110':7,'M112':7,'M114':8,'M115':9,'M116':9,'M118':10,'M121':12}
NUM_LONG = {'M086':1,'M087':2,'M089':3,'M095':4,'M096':5}
NUM_OTHER = {'M111':'bracketed strokes','M113':'bracketed strokes','M117':'roofed strokes','M119':'slanted strokes','M120':'slanted strokes','M122':'bracketed strokes','M088':'long+short strokes'}
STROKES = set(NUM_SHORT) | set(NUM_LONG) | set(NUM_OTHER)

# ---------------- per-sign profile ----------------
def profile(lines, minf=1):
    f = collections.Counter(); ini = collections.Counter(); fin = collections.Counter(); med = collections.Counter(); solo = collections.Counter()
    L = collections.defaultdict(collections.Counter); Rr = collections.defaultdict(collections.Counter); pen = collections.Counter()
    for s in lines:
        n = len(s)
        for i, x in enumerate(s):
            f[x] += 1
            if n == 1: solo[x] += 1; L[x]['<S>'] += 1; Rr[x]['</S>'] += 1; continue
            if i == 0: ini[x] += 1
            elif i == n - 1: fin[x] += 1
            else: med[x] += 1
            if i == n - 2: pen[x] += 1
            L[x][s[i-1] if i else '<S>'] += 1; Rr[x][s[i+1] if i < n - 1 else '</S>'] += 1
    return f, ini, med, fin, solo, pen, L, Rr
def ent(c):
    t = sum(c.values()); return -sum(v/t*math.log2(v/t) for v in c.values()) if t else 0.0
VISUAL = [True]
def classify(lines, alpha=0.001):
    f, ini, med, fin, solo, pen, L, Rr = profile(lines)
    tot_ns = sum(ini.values()) + sum(med.values()) + sum(fin.values())
    b_ini = sum(ini.values()) / tot_ns; b_fin = sum(fin.values()) / tot_ns
    nlines = len(lines); solo_base = sum(1 for s in lines if len(s) == 1) / max(1, nlines)
    cls = {}; stats = {}
    for x, n in f.items():
        if n < 10: continue
        ns = ini[x] + med[x] + fin[x]
        p_fin = binomtest(fin[x], ns, b_fin, alternative='greater').pvalue if ns else 1
        p_ini = binomtest(ini[x], ns, b_ini, alternative='greater').pvalue if ns else 1
        sh_fin = fin[x] / ns if ns else 0; sh_ini = ini[x] / ns if ns else 0
        nxt_term = 0
        stats[x] = dict(freq=n, solo=solo[x], initial=ini[x], medial=med[x], final=fin[x], penult=pen[x], init_share=round(sh_ini, 3), final_share=round(sh_fin, 3),
                        solo_share=round(solo[x] / n, 3), H_left=round(ent(L[x]), 3), H_right=round(ent(Rr[x]), 3), n_left_types=len(L[x]), n_right_types=len(Rr[x]),
                        p_final=p_fin, p_initial=p_ini)
    # second pass: terminal set, then pre-terminal (followed by a terminal sign)
    term = {x for x, s in stats.items() if s['final_share'] >= 0.5 and s['p_final'] < alpha}
    for x, s in stats.items():
        nt = sum(v for k, v in Rr[x].items() if k in term); s['next_is_terminal_share'] = round(nt / max(1, sum(Rr[x].values())), 3)
        top_bigram = max(Rr[x].values()) / s['freq'] if Rr[x] else 0
        s['top_right_collocate_share'] = round(top_bigram, 3); s['top_right_collocate'] = Rr[x].most_common(1)[0][0] if Rr[x] else ''
        if x in term: c = 'TERMINAL'
        elif s['init_share'] >= 0.5 and s['p_initial'] < alpha: c = 'INITIAL'
        elif s['next_is_terminal_share'] >= 0.5: c = 'PRE-TERMINAL'
        elif s['solo_share'] >= 0.15 and solo[x] >= 5: c = 'STAND-ALONE'
        elif s['top_right_collocate_share'] >= 0.6 and s['top_right_collocate'] not in ('</S>',): c = 'BOUND-COLLOCATE'
        else: c = 'MEDIAL/UNSPECIFIED'
        s['positional_class'] = c
        cls[x] = 'NUMERAL-STROKE' if (x in STROKES and VISUAL[0]) else c
    return cls, stats
cls, stats = classify(LINES)
# ---------- null calibration: same rules on within-line shuffled corpora ----------
def shuf(lines, r):
    out = []
    for s in lines: s = list(s); r.shuffle(s); out.append(s)
    return out
null_counts = collections.defaultdict(list)
for k in range(30):
    c0, _ = classify(shuf(LINES, random.Random(k)))
    cnt = collections.Counter(v for v in c0.values())
    for lab in set(cls.values()) | set(cnt): null_counts[lab].append(cnt.get(lab, 0))
real_counts = collections.Counter(cls.values())
FDR = {lab: min(1.0, float(np.mean(null_counts[lab])) / real_counts[lab]) if real_counts[lab] else None for lab in real_counts}
FDR['NUMERAL-STROKE'] = None  # visual class, not inferred
# ---------- bootstrap stability ----------
B = 100; agree = collections.Counter(); seen = collections.Counter()
for b in range(B):
    idx = rng.integers(0, len(LINES), len(LINES)); cb, _ = classify([LINES[i] for i in idx])
    for x, c in cls.items():
        if x in cb: seen[x] += 1; agree[x] += cb[x] == c
stab = {x: agree[x] / B for x in cls}   # absent in a resample counts as disagreement
# ---------- replication in ICIT ----------
wcls, wstats = classify(W_FULL)
def repl(x):
    ws = [w for w in m2w.get(x, []) if w in wcls]
    if not ws: return 'n/a'
    w = max(ws, key=lambda w: wstats[w]['freq'])
    # for NUMERAL-STROKE compare the positional behaviour class instead
    return f"{w}:{wstats[w]['positional_class']}"
rows = []
for x, c in cls.items():
    s = stats[x]; fdr = FDR.get(c)
    r = repl(x); rep_same = (r != 'n/a') and (r.split(':')[1] == s['positional_class'])
    conf_dist = None if fdr is None else round(stab[x] * (1 - fdr), 3)
    rows.append(dict(sign=x, P=';'.join(sorted(m2p.get(x, []))), W=';'.join(sorted(m2w.get(x, []))), description=desc.get(sorted(m2p[x])[0], '') if m2p.get(x) else '',
                     cls=c, bootstrap_stability=round(stab[x], 3), class_FDR_null=None if fdr is None else round(fdr, 3), conf_distributional=conf_dist,
                     icit_replication=r, replicated=rep_same, **s))
T = pd.DataFrame(rows).sort_values('freq', ascending=False); T.to_csv(f'{OUT}/sign_classes_M77.csv', index=False)
# ---------- paradigmatic cohesion tests (context-vector cosine) ----------
f, ini, med, fin, solo, pen, Lc, Rc = profile(LINES)
ctx_keys = [k for k, _ in collections.Counter({k: v for x in Lc for k, v in Lc[x].items()}).most_common(60)]
ctxR_keys = [k for k, _ in collections.Counter({k: v for x in Rc for k, v in Rc[x].items()}).most_common(60)]
def vec(x):
    v = np.array([Lc[x].get(k, 0) for k in ctx_keys] + [Rc[x].get(k, 0) for k in ctxR_keys], float); n = np.linalg.norm(v); return v / n if n else v
def cohesion(group):
    V = np.array([vec(x) for x in group]); S = V @ V.T; k = len(group); return (S.sum() - k) / (k * (k - 1))
freq_signs = [x for x in f if f[x] >= 10]
def cohesion_test(group, n=5000):
    group = [x for x in group if x in freq_signs]
    obs = cohesion(group); fr = np.array([f[x] for x in freq_signs]); null = []
    order = np.argsort(fr); dec = {freq_signs[i]: j * 10 // len(order) for j, i in enumerate(order)}
    byd = collections.defaultdict(list)
    for x in freq_signs: byd[dec[x]].append(x)
    for _ in range(n):
        g = [R.choice(byd[dec[x]]) for x in group]
        if len(set(g)) < len(g): continue
        null.append(cohesion(g))
    null = np.array(null); return dict(n_signs=len(group), observed=round(float(obs), 4), null_mean=round(float(null.mean()), 4), p=float((np.sum(null >= obs) + 1) / (len(null) + 1)))
groups = {'short_stroke_numerals': [x for x in NUM_SHORT], 'long_strokes': list(NUM_LONG), 'terminal_class': list(T[T.cls == 'TERMINAL'].sign),
          'initial_class': list(T[T.cls == 'INITIAL'].sign), 'pre_terminal_class': list(T[T.cls == 'PRE-TERMINAL'].sign)}
COH = {g: cohesion_test(v) for g, v in groups.items() if len([x for x in v if x in freq_signs]) >= 3}
# ---------- numeral value check: do stroke signs differ by count in their contexts? ----------
json.dump(dict(class_counts=dict(real_counts), null_mean_counts={k: float(np.mean(v)) for k, v in null_counts.items()}, FDR=FDR,
               cohesion=COH, n_lines=len(LINES), n_full_lines=len(FULL), icit_lines=len(W_FULL),
               replication_rate={c: float(np.mean([r['replicated'] for r in rows if r['cls'] == c and r['icit_replication'] != 'n/a'])) if any(r['cls'] == c and r['icit_replication'] != 'n/a' for r in rows) else None for c in real_counts}),
          open(f'{OUT}/classes_summary.json', 'w'), indent=1, default=str)
print(real_counts, '\nFDR', FDR, '\nCOH', COH)
