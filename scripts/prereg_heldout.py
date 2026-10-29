"""Session 6: pre-registered held-out tests of the positive structural hypotheses.
Predictions, sign sets, splits and pass rules are fixed in prereg/PREREG_session6_heldout.md and
prereg/sign_sets_session6.json, committed BEFORE this script was run on real data.
Usage: python scripts/prereg_heldout.py            (real data; needs lipi + CISI corpora from fetch_data.sh)
       python scripts/prereg_heldout.py --selftest  (synthetic data only; checks the machinery)"""
import os, sys, json, random, re
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, f'{ROOT}/scripts')
SETS = json.load(open(f'{ROOT}/prereg/sign_sets_session6.json'))
NPERM = 2000; MIN_REL = 5; ALPHA = 0.05

def S(name, scheme): return set(SETS[name][scheme])
# ---------- statistics (seqs are tuples in reading order) ----------
def st_pos(seqs, A, where):
    k = 0
    for s in seqs:
        for i, x in enumerate(s):
            if x in A: k += (i == 0) if where == 'initial' else (i == len(s) - 1) if where == 'final' else (i == len(s) - 2)
    return k
def st_bigram(seqs, A, B): return sum(1 for s in seqs for i in range(len(s) - 1) if s[i] in A and s[i + 1] in B)
def st_order(seqs, I, T):
    k = 0
    for s in seqs:
        ii = [i for i, x in enumerate(s) if x in I]; tt = [i for i, x in enumerate(s) if x in T]
        k += max(ii) < min(tt)
    return k
def hypotheses(scheme):
    T, I, PT = S('TERMINAL', scheme), S('INITIAL', scheme), S('PRE-TERMINAL', scheme)
    N, J, D, TW, F = S('NUMERAL', scheme), S('M342', scheme), S('M267', scheme), S('M099', scheme), S('M059', scheme)
    return [  # id, description, relevant-text filter, statistic
        ('H1', 'terminal-class signs are text-final', lambda s: bool(set(s) & T), lambda q: st_pos(q, T, 'final')),
        ('H2', 'initial-class signs are text-initial', lambda s: bool(set(s) & I), lambda q: st_pos(q, I, 'initial')),
        ('H3', 'pre-terminal-class signs are penultimate', lambda s: len(s) >= 3 and bool(set(s) & PT), lambda q: st_pos(q, PT, 'penult')),
        ('H4', 'jar sign M342 is text-final', lambda s: bool(set(s) & J), lambda q: st_pos(q, J, 'final')),
        ('H5', 'M267 is text-initial', lambda s: bool(set(s) & D), lambda q: st_pos(q, D, 'initial')),
        ('H6', 'M267 is immediately followed by M099 (unit)', lambda s: bool(set(s) & D) and bool(set(s) & TW), lambda q: st_bigram(q, D, TW)),
        ('H7', 'a stroke numeral immediately precedes the fish M059', lambda s: bool(set(s) & N) and bool(set(s) & F), lambda q: st_bigram(q, N, F)),
        ('H8', 'initial-class tokens all precede terminal-class tokens', lambda s: bool(set(s) & I) and bool(set(s) & T) and not (set(s) & I & T), lambda q: st_order(q, I, T)),
    ]
def perm_test(rel, stat, seed):
    obs = stat(rel); rng = random.Random(seed); ge = 0; null = []
    for _ in range(NPERM):
        v = stat([tuple(rng.sample(s, len(s))) for s in rel]); null.append(v); ge += v >= obs
    return obs, float(np.mean(null)), (1 + ge) / (1 + NPERM)
def bh(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p); q = np.empty(n)
    q[o] = np.minimum.accumulate((p[o] * n / np.arange(1, n + 1))[::-1])[::-1]; return np.minimum(q, 1)
def run(splits):
    rows = []
    for split, (scheme, kind, seqs) in splits.items():
        seqs = sorted({tuple(s) for s in seqs if len(s) >= 2})   # unique texts within split, length >= 2
        for k, (hid, desc, filt, stat) in enumerate(hypotheses(scheme)):
            rel = [s for s in seqs if filt(s)]
            if len(rel) < MIN_REL:
                rows.append(dict(split=split, kind=kind, scheme=scheme, hypothesis=hid, description=desc, n_texts_split=len(seqs), n_relevant=len(rel),
                                 observed=np.nan, null_mean=np.nan, ratio=np.nan, p=np.nan, verdict='insufficient data')); continue
            obs, nm, p = perm_test(rel, stat, seed=1000 * k + 7)
            v = 'pass' if p < ALPHA else 'FAIL'
            rows.append(dict(split=split, kind=kind, scheme=scheme, hypothesis=hid, description=desc, n_texts_split=len(seqs), n_relevant=len(rel),
                             observed=obs, null_mean=round(nm, 2), ratio=round(obs / nm, 2) if nm else np.nan, p=p, verdict=v if kind == 'primary' else v.lower() + ' (exploratory)'))
    R = pd.DataFrame(rows); m = R.kind.eq('primary') & R.p.notna()
    R.loc[m, 'q_BH_primary'] = bh(R.loc[m, 'p'])
    return R

def load_real():
    import claim_harness as C
    d = C.load_corpus(); d = d[~d.text.str.contains(r'000|999|/') & (d.text.str.len() > 0)]
    d['seq'] = [tuple('W' + x.zfill(3) for x in s) for s in d.signs]
    typ = d.type.str.split(':').str[0].str.upper()
    sp = {}
    R = lambda *rs: list(d.seq[d.region.isin(rs)])
    sp['ICIT region: Lower Indus'] = ('W', 'primary', R('Lower Indus'))
    sp['ICIT region: Inter-Riverine'] = ('W', 'primary', R('Inter-Riverine'))
    sp['ICIT region: Gujarat/Kutch'] = ('W', 'primary', R('Gujarat/Kutch'))
    sp['ICIT region: Eastern Headwaters + Upper Indus'] = ('W', 'primary', R('Eastern Headwaters', 'Upper Indus'))
    sp['ICIT region: West/foreign (Persian Gulf, Mesopotamia, Iranian Plateau, Central Asia)'] = ('W', 'exploratory', R('Persian Gulf', 'Mesopotamia', 'Iranian Plateau', 'Central Asia'))
    sp['ICIT object: SEAL'] = ('W', 'primary', list(d.seq[typ == 'SEAL']))
    sp['ICIT object: TAB (tablets)'] = ('W', 'primary', list(d.seq[typ == 'TAB']))
    sp['ICIT object: POT (pottery)'] = ('W', 'primary', list(d.seq[typ == 'POT']))
    sp['ICIT object: other (TAG, MISC, BNGL, ROD, IMPL, BEAD)'] = ('W', 'primary', list(d.seq[typ.isin(['TAG', 'MISC', 'BNGL', 'ROD', 'IMPL', 'BEAD'])]))
    c = pd.read_csv(f'{ROOT}/data/joyboseroy_indus_decipher/data/cisi_real_corpus.csv', dtype=str).fillna('')
    c = c[c.damaged == 'False']
    cis = [tuple(reversed(s.split())) for s in c.sign_sequence if 'P000' not in s.split()]
    sp['CISI/mayig transcription: Mohenjo-daro seals'] = ('P', 'primary', cis)
    return sp

def selftest():
    rng = random.Random(3); T = sorted(S('TERMINAL', 'W')); I = sorted(S('INITIAL', 'W')); mid = [f'W{i:03d}' for i in range(900, 960)]
    good = [tuple([rng.choice(I)] + rng.sample(mid, rng.randint(0, 3)) + [rng.choice(T)]) for _ in range(300)]
    noise = [tuple(rng.sample(good[i], len(good[i]))) for i in range(300)]
    R = run({'synthetic structured': ('W', 'primary', good), 'synthetic shuffled': ('W', 'primary', noise)})
    print(R[['split', 'hypothesis', 'n_relevant', 'observed', 'null_mean', 'p', 'verdict']].to_string())
    g = R[R.split == 'synthetic structured'].set_index('hypothesis'); n = R[R.split == 'synthetic shuffled'].set_index('hypothesis')
    assert all(g.loc[h, 'verdict'] == 'pass' for h in ['H1', 'H2', 'H8']), 'structured data should pass H1, H2, H8'
    assert (n.loc[['H1', 'H2', 'H8'], 'verdict'] != 'pass').sum() >= 2, 'shuffled data should mostly fail'
    print('selftest ok')

if __name__ == '__main__':
    if '--selftest' in sys.argv: selftest(); sys.exit()
    R = run(load_real()); out = f'{ROOT}/outputs/prereg'; os.makedirs(out, exist_ok=True)
    R.to_csv(f'{out}/prereg_heldout_results.csv', index=False)
    P = R[R.kind == 'primary']; summ = {}
    for h, g in P.groupby('hypothesis'):
        suff = g[g.verdict != 'insufficient data']
        summ[h] = dict(description=g.description.iloc[0], splits_sufficient=int(len(suff)), passed=int((suff.verdict == 'pass').sum()),
                       failed=sorted(suff.split[suff.verdict == 'FAIL']), insufficient=sorted(g.split[g.verdict == 'insufficient data']),
                       passed_BH=int((suff.q_BH_primary < ALPHA).sum()),
                       overall=('replicated' if len(suff) and (suff.verdict == 'pass').all() else 'partially replicated' if (suff.verdict == 'pass').any() else 'not replicated'))
    json.dump(summ, open(f'{out}/prereg_heldout_summary.json', 'w'), indent=1)
    print(R[['split', 'hypothesis', 'n_relevant', 'observed', 'null_mean', 'p', 'verdict']].to_string()); print(json.dumps(summ, indent=1))
