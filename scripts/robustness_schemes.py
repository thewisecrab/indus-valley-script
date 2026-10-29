"""Session 6: robustness of the headline structural results across three transcriptions (M77, ICIT, CISI/mayig)
and sign-inventory (merge) schemes. Statistics are the pre-registered H1-H8 (scripts/prereg_heldout.py) plus the
bigram conditional-entropy gap against within-text shuffles. All texts (all sites), unique texts of length >= 2.
Schemes:
  native      each corpus's own sign list (M77: Mahadevan; ICIT: Wells/ICIT; CISI: Parpola inclusive allographs)
  parpola     every sign mapped to the Parpola sign that subsumes it (Carlson/mayig concordance, MIT) when that
              mapping is unique: Wells variants and Mahadevan signs sharing one Parpola sign are merged
  allograph   finer: CISI allograph-level transcription (isramos/indus-script-sign-merging derived file, GPL-3);
              not available for M77 or ICIT (n/a)
  numerals    native, with all stroke numerals collapsed into one NUM token
Output: outputs/robustness/robustness_table.csv, robustness_summary.json"""
import os, sys, json, glob, random, collections, math
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, f'{ROOT}/scripts')
import prereg_heldout as PR
OUT = f'{ROOT}/outputs/robustness'; os.makedirs(OUT, exist_ok=True)
SETS = PR.SETS; NPERM = 1000

# concordance from mayig features
m2p, w2p = collections.defaultdict(set), collections.defaultdict(set)
for fp in sorted(glob.glob(f'{ROOT}/data/mayig_indus-valley-script-corpus/features/P*.json')):
    j = json.load(open(fp))
    for w in j.get('wells_graphemes', []): w2p[w].add(j['id'])
    for m in j.get('mahadevan_graphemes', []): m2p[m].add(j['id'])
def corpora():
    D = f'{ROOT}/data/joyboseroy_indus_decipher/data'
    m = pd.read_csv(f'{D}/m77_indusscript_real_corpus.csv', dtype=str).fillna('')
    m77 = [tuple('M' + t[3:].zfill(3) for t in s.split()) for s, dmg in zip(m.sign_sequence, m.damaged) if dmg != 'True' and 'MSg0' not in s.split()]
    import claim_harness as C
    d = C.load_corpus(); d = d[~d.text.str.contains(r'000|999|/') & (d.text.str.len() > 0)]
    icit = [tuple('W' + x.zfill(3) for x in s) for s in d.signs]
    out = {'M77': ('M', m77), 'ICIT': ('W', icit)}
    for name, f in [('CISI', f'{D}/cisi_real_corpus.csv'), ('CISI_allograph', f'{ROOT}/data/isramos_indus-script-sign-merging/data/derived/cisi_real_corpus_allograph.csv')]:
        c = pd.read_csv(f, dtype=str).fillna(''); c = c[c.damaged == 'False']
        out[name] = ('P', [tuple(reversed(s.split())) for s in c.sign_sequence if not any(t.startswith('P000') for t in s.split())])
    return out
NUMS = {sch: set(SETS['NUMERAL'][sch]) for sch in 'MWP'}
def mapper(scheme, sch):
    if scheme in ('native', 'allograph'): return lambda t: t
    if scheme == 'numerals': return lambda t: 'NUM' if t.split('_')[0] in NUMS[sch] else t
    if scheme == 'parpola':
        M = m2p if sch == 'M' else w2p if sch == 'W' else {}
        return lambda t: (next(iter(M[t])) if len(M.get(t, ())) == 1 else t) if sch != 'P' else t
def mapped_sets(f, sch):
    """map each frozen sign set through the scheme; allograph tokens (P121_1) match their base sign"""
    return {k: {f(x) for x in v[sch]} for k, v in SETS.items()}
def hyps(Sm, base):
    has = lambda s, A: any(base(x) in A for x in s)
    T, I, PT, N, J, Dm, TW, F = (Sm[k] for k in ['TERMINAL', 'INITIAL', 'PRE-TERMINAL', 'NUMERAL', 'M342', 'M267', 'M099', 'M059'])
    def pos(q, A, w):
        k = 0
        for s in q:
            for i, x in enumerate(s):
                if base(x) in A: k += (i == 0) if w == 'i' else (i == len(s) - 1) if w == 'f' else (i == len(s) - 2)
        return k
    big = lambda q, A, B: sum(1 for s in q for i in range(len(s) - 1) if base(s[i]) in A and base(s[i + 1]) in B)
    def order(q):
        k = 0
        for s in q:
            ii = [i for i, x in enumerate(s) if base(x) in I]; tt = [i for i, x in enumerate(s) if base(x) in T]; k += max(ii) < min(tt)
        return k
    return [('H1', lambda s: has(s, T), lambda q: pos(q, T, 'f')), ('H2', lambda s: has(s, I), lambda q: pos(q, I, 'i')),
            ('H3', lambda s: len(s) >= 3 and has(s, PT), lambda q: pos(q, PT, 'p')), ('H4', lambda s: has(s, J), lambda q: pos(q, J, 'f')),
            ('H5', lambda s: has(s, Dm), lambda q: pos(q, Dm, 'i')), ('H6', lambda s: has(s, Dm) and has(s, TW), lambda q: big(q, Dm, TW)),
            ('H7', lambda s: has(s, N) and has(s, F), lambda q: big(q, N, F)),
            ('H8', lambda s: has(s, I) and has(s, T) and not any(base(x) in I and base(x) in T for x in s), order)]
def hcond(seqs):
    big = collections.Counter(); first = collections.Counter()
    for s in seqs:
        for a, b in zip(s, s[1:]): big[(a, b)] += 1; first[a] += 1
    n = sum(big.values()); return -sum(c / n * math.log2(c / first[a]) for (a, b), c in big.items())
def main():
    rows = []
    for cname, (sch, seqs0) in corpora().items():
        for scheme in (['allograph'] if cname == 'CISI_allograph' else ['native', 'parpola', 'numerals']):
            f = mapper(scheme, sch)
            seqs = sorted({tuple(f(t) for t in s) for s in seqs0 if len(s) >= 2})
            Sm = mapped_sets(f, sch)
            base = (lambda x: x.split('_')[0]) if cname == 'CISI_allograph' else (lambda x: x)
            corpus_label = 'CISI' if cname.startswith('CISI') else cname
            types = len({t for s in seqs for t in s})
            for k, (hid, filt, stat) in enumerate(hyps(Sm, base)):
                rel = [s for s in seqs if filt(s)]
                if len(rel) < PR.MIN_REL:
                    rows.append(dict(corpus=corpus_label, scheme=scheme, n_texts=len(seqs), sign_types=types, test=hid, n_relevant=len(rel), verdict='insufficient data')); continue
                obs = stat(rel); rng = random.Random(1000 * k + 7); null = [stat([tuple(rng.sample(s, len(s))) for s in rel]) for _ in range(NPERM)]
                p = (1 + sum(v >= obs for v in null)) / (1 + NPERM); nm = float(np.mean(null))
                rows.append(dict(corpus=corpus_label, scheme=scheme, n_texts=len(seqs), sign_types=types, test=hid, n_relevant=len(rel), observed=obs,
                                 null_mean=round(nm, 2), ratio=round(obs / nm, 2) if nm else np.nan, p=p, verdict='pass' if p < .05 else 'FAIL'))
            # conditional entropy gap
            h = hcond(seqs); rng = random.Random(5); hs = [hcond([tuple(rng.sample(s, len(s))) for s in seqs]) for _ in range(200)]
            rows.append(dict(corpus=corpus_label, scheme=scheme, n_texts=len(seqs), sign_types=types, test='Hcond_gap_bits', n_relevant=len(seqs),
                             observed=round(h, 3), null_mean=round(float(np.mean(hs)), 3), ratio=round(h / np.mean(hs), 3),
                             p=(1 + sum(v <= h for v in hs)) / 201, verdict='pass' if (1 + sum(v <= h for v in hs)) / 201 < .05 else 'FAIL'))
            print(cname, scheme, len(seqs), types, flush=True)
    R = pd.DataFrame(rows); R.to_csv(f'{OUT}/robustness_table.csv', index=False)
    suff = R[R.verdict != 'insufficient data']
    summ = dict(cells=int(len(R)), sufficient=int(len(suff)), passed=int((suff.verdict == 'pass').sum()),
                failed=suff[suff.verdict == 'FAIL'][['corpus', 'scheme', 'test', 'n_relevant', 'observed', 'null_mean', 'p']].to_dict('records'),
                by_test={t: f"{int((g.verdict == 'pass').sum())}/{len(g)}" for t, g in suff.groupby('test')})
    json.dump(summ, open(f'{OUT}/robustness_summary.json', 'w'), indent=1, default=float)
    print(R.to_string()); print(json.dumps(summ, indent=1, default=float))
if __name__ == '__main__': main()
