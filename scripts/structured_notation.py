"""Session 8: pre-registered tests of the fixed-field administrative-notation ("cargo tag") proposal.
Pre-registration: prereg/session8_structured_notation_prereg.md (committed before this script was run).
Proposal: Diener (2026), Zenodo doi:10.5281/zenodo.20688721, with statistics from Kriger & Hunt (2026),
doi:10.5281/zenodo.19103880 (179 Mohenjo-daro unicorn seals of M. Carlson's open CISI digitisation, MIT).
Tests: A1 positional entropy profile, A2 rigid five-field fit, B sequence uniqueness, C stroke numerals,
D motif x numeral ('tariff locking'), E terminal jar sign. Indus corpora: I1 CISI/mayig MD unicorn seals (reading order =
reversed JSON order), I2 ICIT/lipi (unique clean texts), I3 M77 (unique undamaged). Comparison corpora: EDH Latin
owner's/maker's stamps and all-genre inscriptions, Wikipedia titles, Sanskrit (DCS) and Akkadian (ORACC) word-aligned
spans, Wikipedia running-text windows, Sproat's non-linguistic corpora.
Deterministic: random.Random(zlib.crc32(label)), sorted iteration. BH across all p-values.
Output: outputs/structured_notation/{results.json, A1_positional_entropy.csv, A2_field_fit.csv,
B_uniqueness.csv, C_numerals.json, D_tariff.json, E_terminal.csv} (aggregate statistics only).
Usage: python scripts/structured_notation.py [--quick]"""
import os, sys, json, glob, math, zlib, random, collections, argparse
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, f'{ROOT}/scripts')
OUT = f'{ROOT}/outputs/structured_notation'; os.makedirs(OUT, exist_ok=True)
ap = argparse.ArgumentParser(); ap.add_argument('--quick', action='store_true'); A = ap.parse_args()
NPERM = 200 if A.quick else 2000; NSUB = 50 if A.quick else 200; NDRAW = 100 if A.quick else 500; HC = 4000 if A.quick else 20000
R = lambda label: random.Random(zlib.crc32(label.encode()))
PVALS = []   # (test, label, p)
def pv(test, label, p): PVALS.append((test, label, float(p))); return float(p)

# ---------------- corpora ----------------
def mayig(keep_damaged=True):
    T = []
    for f in sorted(glob.glob(f'{ROOT}/data/mayig_indus-valley-script-corpus/corpus/*/*.json')):
        for side in json.load(open(f)):
            g = [x['id'] for x in side['graphemes']]
            if g and (keep_damaged or 'P000' not in g): T.append((side['id'], tuple(reversed(g))))   # reading order
    return T
def icit_full():
    import claim_harness as C
    d = C.load_corpus(); d = d[~d.text.str.contains(r'000|999|/') & (d.text.str.len() > 0)].copy()
    d['seq'] = d.signs.map(lambda s: tuple('W' + x.zfill(3) for x in s)); return d
def m77():
    m = pd.read_csv(f'{ROOT}/data/joyboseroy_indus_decipher/data/m77_indusscript_real_corpus.csv', dtype=str).fillna('')
    return list(dict.fromkeys(tuple('M' + t[3:].zfill(3) for t in s.split()) for s, dmg in zip(m.sign_sequence, m.damaged) if dmg != 'True' and 'MSg0' not in s.split() and s.strip()))
M77LENS = [int(k) for k, v in json.load(open(f'{ROOT}/positive_control/data/m77_line_length_distribution.json'))['counts'].items() for _ in range(v) if 2 <= int(k) <= 12]
def spans(name, n=8000):
    """word-aligned spans of the positive-control corpora (aksharas / cuneiform graphemes as signs), M77 length distribution"""
    T = json.load(open(f'{ROOT}/positive_control/outputs/corpora/{name}.json')); r = R(f'spans|{name}'); out = []
    T = [t for t in T if len(t['signs']) >= 2]
    byL = collections.defaultdict(list)
    for ti, t in enumerate(T):
        st = t['word_starts'] + [len(t['signs'])]
        for i in range(len(st) - 1):
            for k in range(i + 1, len(st)):
                L = st[k] - st[i]
                if L > 12: break
                byL[L].append((ti, st[i], st[k]))
    for _ in range(n):
        L = r.choice(M77LENS)
        if byL[L]: ti, a, b = r.choice(byL[L]); out.append(tuple(T[ti]['signs'][a:b]))
    return out
def comparison():
    import emblem_tests as E, emblem_tests2 as E2
    C = {}
    for k, v in E2.edh().items(): C[k] = [tuple(x) for x in v]
    for k, v in E2.titles().items(): C[k] = [tuple(x) for x in v]
    C['L Sanskrit DCS word-aligned spans (aksharas)'] = spans('sanskrit_classical')
    C['L Akkadian ORACC word-aligned spans (graphemes)'] = spans('akkadian_NA_letters')
    for k, v in E.linguistic(M77LENS, R('windows')).items(): C[k + ' windows'] = [tuple(x) for x in v]
    for k, v in E.sproat().items(): C[k] = [tuple(x) for x in v]
    return C
def group(name): return 'indus' if name.startswith('I') else ('nonling' if name.startswith('NL') else 'ling')
UNIQUE_BY_CONSTRUCTION = lambda name: 'titles' in name

# ---------------- helpers ----------------
def H(xs):
    c = collections.Counter(xs); n = len(xs); return -sum(v / n * math.log2(v / n) for v in c.values())
def wshuf(T, r): return [tuple(r.sample(list(s), len(s))) for s in T]
def bh(ps):
    ps = np.asarray(ps, float); n = len(ps); o = np.argsort(ps); q = np.empty(n); prev = 1.0
    for rank, i in reversed(list(enumerate(o, 1))): prev = min(prev, ps[i] * n / rank); q[i] = prev
    return q
def matched(T, lens, r):
    """sample texts without replacement so that their lengths follow `lens` (one text per entry). If a length is short of
    texts, the rest are taken from the nearest available length (longer first, then shorter). None if too few texts."""
    if len(T) < len(lens): return None
    byL = collections.defaultdict(list)
    for t in T: byL[len(t)].append(t)
    for L in sorted(byL): r.shuffle(byL[L])
    used = collections.Counter(); out = []
    for L in sorted(lens):
        for d in [0] + [x for k in range(1, 20) for x in (k, -k)]:
            if used[L + d] < len(byL.get(L + d, [])): out.append(byL[L + d][used[L + d]]); used[L + d] += 1; break
    return out if len(out) == len(lens) else None

# ---------------- A1 positional entropy ----------------
def a1_stat(T5): return float(np.var([H([t[i] for t in T5]) for i in range(5)]))
def a1(name, T, r):
    T5 = [t for t in T if len(t) == 5]
    if len(T5) < 35: return None
    row = dict(corpus=name, group=group(name), n5=len(T5), entropies_reading_order=[round(H([t[i] for t in T5]), 3) for i in range(5)])
    if name.startswith('I'):
        obs = a1_stat(T5); null = [a1_stat(wshuf(T5, r)) for _ in range(NPERM)]
        row.update(var_full=round(obs, 4), null_mean_full=round(float(np.mean(null)), 4), p_full=pv('A1', name, (1 + sum(x >= obs for x in null)) / (NPERM + 1)))
    zs = []
    for k in range(NSUB):
        S = r.sample(T5, 35); obs = a1_stat(S); null = [a1_stat(wshuf(S, r)) for _ in range(100)]
        zs.append((obs - np.mean(null)) / (np.std(null) + 1e-12))
    row.update(z_n35_median=round(float(np.median(zs)), 3), z_n35_iqr=[round(float(np.percentile(zs, 25)), 3), round(float(np.percentile(zs, 75)), 3)])
    return row

# ---------------- A2 rigid five-field fit ----------------
def valid(seq, F, strict):
    last = -1
    for x in seq:
        f = F[x]
        if (f <= last) if strict else (f < last): return False
        last = f
    return True
def fit_fields(train, r, strict, steps=HC):
    types = sorted({x for t in train for x in t}); pos = collections.defaultdict(list)
    for t in train:
        for i, x in enumerate(t): pos[x].append(i / (len(t) - 1) if len(t) > 1 else 0.5)
    F = {x: min(4, int(np.mean(pos[x]) * 5)) for x in types}            # start: mean relative position, 5 bins
    inv = collections.defaultdict(list)
    for i, t in enumerate(train):
        for x in set(t): inv[x].append(i)
    cur = [valid(t, F, strict) for t in train]
    for _ in range(steps):
        x = r.choice(types); old = F[x]; F[x] = r.randrange(5)
        if F[x] == old: continue
        new = {i: valid(train[i], F, strict) for i in inv[x]}
        if sum(new.values()) >= sum(cur[i] for i in inv[x]):
            for i, v in new.items(): cur[i] = v
        else: F[x] = old
    return F, float(np.mean(cur))
def a2(name, T, r, n=1000, lens=None, seeds=5):
    rows = []
    for s in range(seeds):
        rs = R(f'A2|{name}|{s}')
        S = matched(T, lens if lens is not None else [rs.choice(M77LENS) for _ in range(n)], rs)
        if S is None: return None
        rs.shuffle(S); cut = int(.8 * len(S)); tr, te = S[:cut], S[cut:]
        for strict in (True, False):
            F, trs = fit_fields(tr, rs, strict)
            te2 = [t for t in te if all(x in F for x in t)]
            if len(te2) < 20: continue
            real = float(np.mean([valid(t, F, strict) for t in te2]))
            null = [float(np.mean([valid(t, F, strict) for t in wshuf(te2, rs)])) for _ in range(200)]
            rows.append(dict(corpus=name, group=group(name), seed=s, strict=strict, n=len(S), train_valid=round(trs, 4), heldout_texts_all_types_seen=len(te2),
                             heldout_coverage=round(len(te2) / len(te), 3), heldout_valid=round(real, 4), shuffled_valid=round(float(np.mean(null)), 4),
                             gain=round(real - float(np.mean(null)), 4), p=(1 + sum(x >= real for x in null)) / 201, share_len_gt5=round(float(np.mean([len(t) > 5 for t in S])), 3)))
    return rows

# ---------------- B uniqueness ----------------
def uniq(S): return len(set(S)) / len(S)
def b(name, T, lens, r):
    vals = []
    for k in range(NDRAW):
        S = matched(T, lens, r)
        if S is None: return None
        vals.append(uniq(S))
    S = matched(T, lens, R(f'Blen|{name}'))
    return dict(corpus=name, group=group(name), unique_by_construction=UNIQUE_BY_CONSTRUCTION(name), mean_len_sampled=round(float(np.mean([len(t) for t in S])), 2),
                target_mean_len=round(float(np.mean(lens)), 2), median=round(float(np.median(vals)), 4),
                lo95=round(float(np.percentile(vals, 2.5)), 4), hi95=round(float(np.percentile(vals, 97.5)), 4),
                share_draws_ge_0_9831=round(float(np.mean([v >= 0.9831 for v in vals])), 3))

if __name__ == '__main__':
    res = dict(prereg='prereg/session8_structured_notation_prereg.md', quick=A.quick)
    I1 = mayig(); I1t = [t for _, t in I1]; I1clean = [t for _, t in mayig(False)]
    D = icit_full(); I2 = list(dict.fromkeys(D.seq)); I3 = m77()
    IND = {'I1 CISI/mayig MD unicorn seals (n=179, as Kriger & Hunt)': I1t, 'I1 without damaged texts': I1clean, 'I2 ICIT/lipi unique': I2, 'I3 M77 unique': I3}
    COMP = comparison()
    res['corpus_sizes'] = {k: len(v) for k, v in {**IND, **COMP}.items()}
    # ---- replication of Kriger & Hunt on I1 (their numbers are in visual left-to-right order = reversed reading order)
    five = [t for t in I1t if len(t) == 5]
    rep = dict(n=len(I1t), tokens=sum(map(len, I1t)), types=len({x for t in I1t for x in t}), distinct_sequences=len(set(I1t)),
               uniqueness_distinct_over_n=round(len(set(I1t)) / len(I1t), 4), n5=len(five),
               entropy_visual_order=[round(H([t[::-1][i] for t in five]), 2) for i in range(5)],
               entropy_reading_order=[round(H([t[i] for t in five]), 2) for i in range(5)])
    r = R('B|KH-global-null'); gl = []
    for _ in range(NPERM):
        pool = [x for t in I1t for x in t]; r.shuffle(pool); k = 0; S = []
        for t in I1t: S.append(tuple(pool[k:k + len(t)])); k += len(t)
        gl.append(uniq(S))
    rep['global_shuffle_null_uniqueness_mean'] = round(float(np.mean(gl)), 4); rep['global_shuffle_null_95'] = [round(float(np.percentile(gl, 2.5)), 4), round(float(np.percentile(gl, 97.5)), 4)]
    rep['p_real_uniqueness_above_global_null'] = pv('B', 'I1 vs global-shuffle null (K&H replication)', (1 + sum(x >= rep['uniqueness_distinct_over_n'] for x in gl)) / (NPERM + 1))
    res['kriger_hunt_replication'] = rep
    # ---- A1
    A1 = [x for x in (a1(k, v, R(f'A1|{k}')) for k, v in {**IND, **COMP}.items()) if x]
    pd.DataFrame(A1).to_csv(f'{OUT}/A1_positional_entropy.csv', index=False); print('A1 done', flush=True)
    # ---- A2 (n = 1000, M77 lengths; and K&H scale: n = 179 with I1 lengths)
    A2 = []
    for k, v in {**{k: v for k, v in IND.items() if not k.startswith('I1')}, **COMP}.items():
        x = a2(k, v, R(f'A2|{k}')); A2 += x or []; print('A2', k, 'ok' if x else 'skip', flush=True)
    I1L = [len(t) for t in I1clean if len(t) >= 2]
    for k, v in {'I1 without damaged texts': [t for t in I1clean if len(t) >= 2], **COMP}.items():
        x = a2(k + ' [n=K&H scale]', v, R(f'A2s|{k}'), lens=I1L); A2 += x or []
    A2d = pd.DataFrame(A2)
    A2d.to_csv(f'{OUT}/A2_field_fit.csv', index=False)
    for (c, st), g in A2d.groupby(['corpus', 'strict']):
        if c.startswith('I'): pv('A2', f'{c} strict={st} (seed-median p)', float(np.median(g.p)))
    # ---- B uniqueness at K&H scale
    I1lens = [len(t) for t in I1t]
    # NOT de-duplicated Indus texts here (uniqueness is about repeats); ICIT and M77 as transcribed, plus the ICIT Mohenjo-daro seals
    I2all = list(D.seq); I2md = list(D[(D.site == 'Mohenjo-daro') & D.type.str.startswith('SEAL')].seq)
    mm = pd.read_csv(f'{ROOT}/data/joyboseroy_indus_decipher/data/m77_indusscript_real_corpus.csv', dtype=str).fillna('')
    I3all = [tuple(s.split()) for s, dmg in zip(mm.sign_sequence, mm.damaged) if dmg != 'True' and 'MSg0' not in s.split() and s.strip()]
    BIN = {'I2 ICIT/lipi all texts (not de-duplicated)': I2all, 'I2 ICIT/lipi Mohenjo-daro seals': I2md, 'I3 M77 all undamaged lines (not de-duplicated)': I3all}
    res['corpus_sizes'].update({k: len(v) for k, v in BIN.items()})
    B = [x for x in (b(k, v, I1lens, R(f'B|{k}')) for k, v in {**BIN, **COMP}.items()) if x]
    pd.DataFrame(B).to_csv(f'{OUT}/B_uniqueness.csv', index=False); print('B done', flush=True)
    # ---- C stroke numerals
    PSTROKE = {'P121': 1, 'P122': 2, 'P123': 3, 'P124': 4, 'P125': 5, 'P126': 6, 'P144': 1, 'P145': 2, 'P147': 3, 'P150': 4, 'P151': 5}
    KH_SET = {'P121', 'P122', 'P123', 'P124', 'P144', 'P145', 'P146', 'P147', 'P148', 'P149', 'P150', 'P151'}
    WSTROKE = {'W001': 1, 'W002': 2, 'W003': 3, 'W004': 4, 'W014': 4, 'W005': 5, 'W015': 5, 'W006': 6, 'W016': 6, 'W031': 1, 'W032': 2, 'W033': 3, 'W034': 4, 'W035': 5}
    MSTROKE = {'M097': 1, 'M098': 1, 'M099': 2, 'M100': 2, 'M102': 3, 'M103': 3, 'M104': 4, 'M105': 4, 'M106': 5, 'M107': 5, 'M108': 6, 'M109': 6, 'M086': 1, 'M087': 2, 'M089': 3, 'M095': 4, 'M096': 5}
    Cres = {}
    for name, T, S in [('I1 (K&H set)', I1t, {x: (2 if x in ('P122', 'P145') else 0) for x in KH_SET}), ('I1', I1t, PSTROKE), ('I2', I2, WSTROKE), ('I3', I3, MSTROKE)]:
        T5 = [t for t in T if len(t) == 5]; r = R(f'C|{name}')
        def share_by_pos(TT): return [float(np.mean([t[i] in S for t in TT])) for i in range(5)]
        obs = share_by_pos(T5); null = [share_by_pos(wshuf(T5, r)) for _ in range(NPERM)]
        toks = [x for t in T for x in t if x in S]; two = [x for x in toks if S.get(x) == 2]
        init_pair = {'I1 (K&H set)': ('P385', 'P122'), 'I1': ('P385', 'P122'), 'I2': ('W861', 'W002'), 'I3': ('M267', 'M099')}[name]
        two_in_pair = sum(1 for t in T for i in range(len(t) - 1) if (t[i], t[i + 1]) == init_pair)
        Cres[name] = dict(n5=len(T5), stroke_share_of_texts_by_reading_position=[round(x, 3) for x in obs],
                          p_reading_position2=pv('C1', f'{name} reading pos 2 (= visual pos 4)', (1 + sum(n[1] >= obs[1] for n in null)) / (NPERM + 1)),
                          p_reading_position4=pv('C1', f'{name} reading pos 4 (Diener P4)', (1 + sum(n[3] >= obs[3] for n in null)) / (NPERM + 1)),
                          stroke_tokens=len(toks), two_stroke_tokens=len(two), two_stroke_share=round(len(two) / max(1, len(toks)), 4),
                          two_stroke_tokens_inside_initial_diamond_pair=two_in_pair, initial_pair=list(init_pair))
    json.dump(Cres, open(f'{OUT}/C_numerals.json', 'w'), indent=1); print('C done', flush=True)
    # ---- D motif x numeral (ICIT)
    def motif(s):
        s = str(s)
        return 'unicorn' if s.startswith('Bull1') else {'Gaur': 'gaur', 'Elep': 'elephant', 'Rhin': 'rhinoceros'}.get(s)
    Dd = D.assign(motif=D.symbol.map(motif)).dropna(subset=['motif'])
    Dd = Dd.assign(k=Dd.seq.map(lambda t: max([WSTROKE[x] for x in t if x in WSTROKE], default=0)))
    Dk = Dd[Dd.k > 0]
    tab = pd.crosstab(Dk.motif, Dk.k)
    def chi2(m, k):
        t = pd.crosstab(m, k).values.astype(float); e = t.sum(1, keepdims=True) * t.sum(0, keepdims=True) / t.sum()
        return float(((t - e) ** 2 / np.where(e > 0, e, 1)).sum())
    obs = chi2(Dk.motif.values, Dk.k.values); r = R('D'); kk = list(Dk.k.values); null = []
    for _ in range(10000 if not A.quick else 1000):
        r.shuffle(kk); null.append(chi2(Dk.motif.values, np.array(kk)))
    Dres = dict(n_texts_with_motif=int(len(Dd)), n_with_numeral=int(len(Dk)), crosstab={m: {int(c): int(v) for c, v in row.items()} for m, row in tab.iterrows()},
                chi2=round(obs, 2), p_perm=pv('D', 'motif x k independence', (1 + sum(x >= obs for x in null)) / (len(null) + 1)))
    for m in ['elephant', 'rhinoceros']:
        g = Dk[Dk.motif == m]; Dres[f'{m}_share_k_ge_4'] = round(float((g.k >= 4).mean()), 3) if len(g) else None; Dres[f'{m}_n'] = int(len(g))
    g = Dk[Dk.motif == 'gaur']; Dres['gaur_share_k_2_or_3'] = round(float(g.k.isin([2, 3]).mean()), 3) if len(g) else None; Dres['gaur_n'] = int(len(g))
    g = Dk[Dk.motif == 'unicorn']; Dres['unicorn_k_variance'] = round(float(g.k.var()), 3); Dres['unicorn_n'] = int(len(g))
    Dres['share_with_numeral_by_motif'] = {m: round(float((g.k > 0).mean()), 3) for m, g in Dd.groupby('motif')}
    json.dump(Dres, open(f'{OUT}/D_tariff.json', 'w'), indent=1); print('D done', flush=True)
    # ---- E terminal jar
    E = []
    for name, T, jar in [('I1', I1t, 'P324'), ('I2', I2, 'W740'), ('I3', I3, 'M342')]:
        T2 = [t for t in T if len(t) >= 2]; r = R(f'E|{name}')
        fin = lambda TT: sum(1 for t in TT for i, x in enumerate(t) if x == jar and i == len(t) - 1) / max(1, sum(1 for t in TT for x in t if x == jar))
        obs = fin(T2); null = [fin(wshuf(T2, r)) for _ in range(NPERM)]
        E.append(dict(corpus=name, token=jar, tokens=sum(1 for t in T for x in t if x == jar), share_of_all_tokens=round(sum(1 for t in T for x in t if x == jar) / sum(map(len, T)), 4),
                      final_share=round(obs, 4), shuffled_final_share=round(float(np.mean(null)), 4), p=pv('E1', name, (1 + sum(x >= obs for x in null)) / (NPERM + 1))))
    for name, T in COMP.items():
        T2 = [t for t in T if len(t) >= 2]; c = collections.Counter(x for t in T2 for x in t); fc = collections.Counter(t[-1] for t in T2)
        cand = [(fc[x] / c[x], x) for x in sorted(c) if c[x] >= 20]
        if not cand: continue
        sh, x = max(cand); exp = float(np.mean([1 / len(t) for t in T2 for y in t if y == x]))
        E.append(dict(corpus=name, token='(most final type, freq >= 20)', tokens=c[x], share_of_all_tokens=round(c[x] / sum(c.values()), 4), final_share=round(sh, 4), shuffled_final_share=round(exp, 4), p=None))
    pd.DataFrame(E).to_csv(f'{OUT}/E_terminal.csv', index=False)
    # ---- BH across all p-values
    q = bh([p for _, _, p in PVALS]); res['pvalues'] = [dict(test=t, label=l, p=round(p, 5), q_BH=round(float(qq), 5)) for (t, l, p), qq in zip(PVALS, q)]
    res['A1'] = A1; res['A2_summary'] = A2d.groupby(['corpus', 'group', 'strict']).agg(heldout_valid=('heldout_valid', 'median'), shuffled_valid=('shuffled_valid', 'median'),
                 gain=('gain', 'median'), gain_min=('gain', 'min'), gain_max=('gain', 'max'), coverage=('heldout_coverage', 'median'), share_len_gt5=('share_len_gt5', 'median')).reset_index().to_dict('records')
    res['B'] = B; res['C'] = Cres; res['D'] = Dres; res['E'] = E
    json.dump(res, open(f'{OUT}/results.json', 'w'), indent=1, default=str); print('ALL DONE', flush=True)
