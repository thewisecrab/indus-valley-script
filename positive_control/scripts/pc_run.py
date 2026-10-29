"""Positive control for the Yajnadevam shuffle test (session 7).
Runs the SAME three measures used in the Yajnadevam test (claim_harness.py part B + parse_test_vidyut.py part E):
  M1 seg_full   : whole reading segmentable into words of the full dictionary (Indus/Sanskrit: Monier-Williams headwords,
                  claim_harness LEXCACHE['_full_MW']; Akkadian: ORACC glossary citation + normalised forms)
  M2 seg_lm4361 : same, with a 4,361-word dictionary sample stratified by word length exactly as claim_harness.get_lexicons()
  M3 vidyut     : vidyut 0.4 Chedaka full parse (parse_test_vidyut.analyse) -- Sanskrit only
  (Akkadian extra: M1h seg_full_heldout = dictionary from OTHER ORACC corpora only)
on real texts of deciphered scripts read with their correct key, against within-text shuffles, global shuffles and a
permuted (wrong) key -- and on the Indus texts with Yajnadevam's key for an apples-to-apples comparison.
Deterministic: every RNG is random.Random(<int>); no hash()-dependent iteration.
Usage: python pc_run.py [--nshuf 200] [--nperm 100] [--seeds 5]
"""
import os, sys, json, random, re, collections, argparse
import numpy as np, pandas as pd
from multiprocessing import Pool
PC = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); ROOT = os.path.dirname(PC)
sys.path.insert(0, f'{ROOT}/scripts'); import claim_harness as h
from vidyut.cheda import Chedaka
OUT = f'{PC}/outputs'; COR = f'{OUT}/corpora'
ap = argparse.ArgumentParser(); ap.add_argument('--nshuf', type=int, default=200); ap.add_argument('--nperm', type=int, default=100)
ap.add_argument('--seeds', type=int, default=5); ap.add_argument('--nshuf_rep', type=int, default=50); ap.add_argument('--nperm_rep', type=int, default=20); ap.add_argument('--n', type=int, default=2317); ap.add_argument('--procs', type=int, default=8)
A = ap.parse_args()

# ---------- lexicons ----------
LX = h.get_lexicons(); COUNTS = LX['_counts']
def coll(s): return re.sub(r'(.)\1+', r'\1', s)
akk_in = json.load(open(f'{COR}/akk_lexicon_insample.json')); akk_ho = json.load(open(f'{COR}/akk_lexicon_heldout.json'))
AKK_FULL = set(akk_in['citation_forms']) | set(akk_in['norms']); AKK_HO = set(akk_ho['citation_forms']) | set(akk_ho['norms'])
TRIES = {'skt_full': h.trie(LX['_full_MW']), 'skt_lm': h.trie(LX['sanskrit_MW']),
         'akk_full': h.trie(AKK_FULL), 'akk_lm': h.trie(h.stratified(AKK_FULL, COUNTS, seed=0)), 'akk_ho': h.trie(AKK_HO)}
LEXINFO = dict(skt_full=len(LX['_full_MW']), skt_lm=len(LX['sanskrit_MW']), akk_full=len(AKK_FULL),
               akk_lm=len(h.stratified(AKK_FULL, COUNTS, seed=0)), akk_ho=len(AKK_HO))
CHED = Chedaka(f'{ROOT}/data/vidyut')
def vidyut_ok(s):
    if not s: return False
    toks = list(CHED.run(s)) or [None]
    return all(t is not None and t.data is not None for t in toks)
def seg(s_red, T):  # s_red: reduced alphabet string, no optional chars
    return h.segmentable([(c, False) for c in s_red], T)

# ---------- corpora & text sets ----------
M77 = json.load(open(f'{PC}/data/m77_line_length_distribution.json'))['counts']
LENS = [int(k) for k, v in M77.items() for _ in range(v) if 2 <= int(k) <= 12]   # M77 complete-line lengths, 2..12 as in texts_for_tests
def load(name):
    T = json.load(open(f'{COR}/{name}.json'))
    return [dict(tok=list(zip(t['signs'], t['values'])), ws=t['word_starts']) for t in T if len(t['signs']) >= 2]
def textsets(texts, seed, n):
    r = random.Random(seed); out = {}
    full = [t['tok'] for t in texts if any(v for _, v in t['tok'])]
    out['full'] = [full[i] for i in sorted(r.sample(range(len(full)), min(n, len(full))))]
    # word-aligned spans: consecutive whole words, total length exactly L
    byL = collections.defaultdict(list)
    for ti, t in enumerate(texts):
        st = t['ws'] + [len(t['tok'])]
        for i in range(len(st) - 1):
            for k in range(i + 1, len(st)):
                L = st[k] - st[i]
                if L > 12: break
                if L >= 2: byL[L].append((ti, st[i], st[k]))
    r2 = random.Random(seed + 1); spans = set(); wa = []
    for L in sorted(LENS, key=lambda x: r2.random()):
        for _ in range(50):
            ti, a, b = r2.choice(byL[L])
            if (ti, a) not in spans: spans.add((ti, a)); wa.append(texts[ti]['tok'][a:b]); break
    out['lenmatch_wordaligned'] = wa[:n]
    # random-cut windows from the concatenated stream (structure2.length_matched style)
    stream = [x for t in texts for x in t['tok']]; r3 = random.Random(seed + 2); rc = []
    for _ in range(n):
        L = r3.choice(LENS); i = r3.randrange(0, len(stream) - L); rc.append(stream[i:i + L])
    out['lenmatch_randomcut'] = rc
    return out

# ---------- readers ----------
def read_skt(tokens, key):   # tokens: list of (sign, value); key None = token's own (correct) value
    return ''.join(v if key is None else key.get(s, '') for s, v in tokens)
def red_skt(s): return ''.join(c for c, _ in h.red_items([(c, False) for c in s]))
def read_akk(tokens, key): return coll(''.join(v if key is None else key.get(s, '') for s, v in tokens))

def score_set(kind, seqs, key):
    """returns dict measure -> np.bool_ array over texts"""
    if kind == 'indus':
        R = {'M1_seg_full': [], 'M2_seg_lm4361': [], 'M3_vidyut': []}
        for s in seqs:
            it = h.red_items(h.mech(s, key)); raw = ''.join(c for c, _ in h.mech(s, key))
            R['M1_seg_full'].append(h.segmentable(it, TRIES['skt_full'])); R['M2_seg_lm4361'].append(h.segmentable(it, TRIES['skt_lm']))
            R['M3_vidyut'].append(vidyut_ok(raw))
    elif kind == 'skt':
        R = {'M1_seg_full': [], 'M2_seg_lm4361': [], 'M3_vidyut': []}
        for s in seqs:
            raw = read_skt(s, key); red = red_skt(raw)
            R['M1_seg_full'].append(seg(red, TRIES['skt_full'])); R['M2_seg_lm4361'].append(seg(red, TRIES['skt_lm']))
            R['M3_vidyut'].append(vidyut_ok(raw))
    else:
        R = {'M1_seg_full': [], 'M2_seg_lm4361': [], 'M1h_seg_full_heldout_lexicon': []}
        for s in seqs:
            red = read_akk(s, key)
            R['M1_seg_full'].append(seg(red, TRIES['akk_full'])); R['M2_seg_lm4361'].append(seg(red, TRIES['akk_lm']))
            R['M1h_seg_full_heldout_lexicon'].append(seg(red, TRIES['akk_ho']))
    return {k: np.array(v, bool) for k, v in R.items()}

def shuffle_within(seqs, rng): return [tuple(rng.sample(list(s), len(s))) for s in seqs]
def shuffle_global(seqs, rng):
    pool = [x for s in seqs for x in s]; rng.shuffle(pool); out, k = [], 0
    for s in seqs: out.append(tuple(pool[k:k + len(s)])); k += len(s)
    return out
def permuted(key, rng):
    signs = sorted(key); vals = [key[s] for s in signs]; rng.shuffle(vals); return dict(zip(signs, vals))

JOB = {}
def work(arg):
    null, rep = arg; J = JOB
    if null == 'within': return score_set(J['kind'], shuffle_within(J['seqs'], random.Random(J['base'] + 10_000 + rep)), J['key'])
    if null == 'global': return score_set(J['kind'], shuffle_global(J['seqs'], random.Random(J['base'] + 20_000 + rep)), J['key'])
    if null == 'permkey': return score_set(J['kind'], J['seqs'], permuted(J['pkbase'], random.Random(J['base'] + 30_000 + rep)))

LB = [(2, 2), (3, 3), (4, 4), (5, 5), (6, 7), (8, 12), (13, 10**6)]
def run_condition(label, kind, seqs, key, pkbase, base, nshuf, nperm, rows, lenrows):
    JOB.update(kind=kind, seqs=seqs, key=key, pkbase=pkbase, base=base)
    real = score_set(kind, seqs, key)
    jobs = [('within', i) for i in range(nshuf)] + [('global', i) for i in range(nshuf)] + [('permkey', i) for i in range(nperm)]
    with Pool(A.procs) as p: res = p.map(work, jobs, chunksize=4)
    by = collections.defaultdict(list)
    for (null, _), r in zip(jobs, res): by[null].append(r)
    lens = np.array([len(s) for s in seqs])
    for m in real:
        row = dict(label, measure=m, n_texts=len(seqs), mean_len=round(float(lens.mean()), 2), real=round(float(real[m].mean()), 4))
        for null in ('within', 'global', 'permkey'):
            v = np.array([r[m].mean() for r in by[null]])
            row[f'{null}_mean'] = round(float(v.mean()), 4); row[f'{null}_lo95'] = round(float(np.percentile(v, 2.5)), 4); row[f'{null}_hi95'] = round(float(np.percentile(v, 97.5)), 4)
            row[f'drop_{null}'] = round(float(real[m].mean() - v.mean()), 4)
            row[f'p_{null}'] = round(float((1 + (v >= real[m].mean()).sum()) / (len(v) + 1)), 4)   # one-sided: null >= real
            row[f'n_{null}'] = len(v)
        rows.append(row); print({k: row[k] for k in ('corpus', 'key', 'textset', 'sample_seed', 'measure', 'real', 'within_mean', 'global_mean', 'permkey_mean', 'p_within', 'p_global')}, flush=True)
        if label.get('sample_seed', 0) == 0:
            for lo, hi in LB:
                sel = (lens >= lo) & (lens <= hi)
                if sel.sum() < 30: continue
                lr = dict(label, measure=m, len_bin=f'{lo}-{hi}' if hi != lo else str(lo), n=int(sel.sum()), real=round(float(real[m][sel].mean()), 4))
                for null in ('within', 'global', 'permkey'):
                    v = np.array([r[m][sel].mean() for r in by[null]])
                    lr[f'{null}_mean'] = round(float(v.mean()), 4); lr[f'drop_{null}'] = round(float(real[m][sel].mean() - v.mean()), 4)
                    lr[f'p_{null}'] = round(float((1 + (v >= real[m][sel].mean()).sum()) / (len(v) + 1)), 4)
                lenrows.append(lr)

if __name__ == '__main__':
    rows, lenrows = [], []
    # Indus + Yajnadevam (reference, same nulls & replicate counts)
    ykey = h.load_key(); iseqs = h.texts_for_tests()
    run_condition(dict(corpus='indus_lipi', key='yajnadevam', textset='lipi_test_texts_2317', sample_seed=0), 'indus', iseqs, ykey, ykey, 0, A.nshuf, A.nperm, rows, lenrows)
    pd.DataFrame(rows).to_csv(f'{OUT}/pc_results.csv', index=False)
    for cname, kind in [('sanskrit_classical', 'skt'), ('sanskrit_vedic', 'skt'), ('akkadian_NA_letters', 'akk')]:
        texts = load(cname)
        types = collections.defaultdict(collections.Counter)
        for t in texts:
            for s, v in t['tok']: types[s][v] += 1
        fixed = {s: sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] for s, c in types.items()}   # most frequent value per sign
        for seed in range(A.seeds):
            TS = textsets(texts, 1000 * seed + 7, A.n)
            for tsname, seqs in TS.items():
                seqs = [tuple(s) for s in seqs]
                base = 100_000 * (seed + 1)
                ns, npm = (A.nshuf, A.nperm) if seed == 0 else (A.nshuf_rep, A.nperm_rep)
                run_condition(dict(corpus=cname, key='correct', textset=tsname, sample_seed=seed), kind, seqs, None, fixed, base, ns, npm, rows, lenrows)
                if kind == 'akk':   # Yajnadevam-like fixed key: one value per sign (most frequent reading)
                    run_condition(dict(corpus=cname, key='fixed_one_value_per_sign', textset=tsname, sample_seed=seed), kind, seqs, fixed, fixed, base + 50_000, ns, npm, rows, lenrows)
                pd.DataFrame(rows).to_csv(f'{OUT}/pc_results.csv', index=False); pd.DataFrame(lenrows).to_csv(f'{OUT}/pc_results_by_length.csv', index=False)
    json.dump(dict(lexicon_sizes=LEXINFO, length_counts=COUNTS, n_shuffles_seed0=A.nshuf, n_perm_seed0=A.nperm, n_shuffles_other_seeds=A.nshuf_rep, n_perm_other_seeds=A.nperm_rep, seeds=A.seeds, n_texts=A.n,
                   m77_lengths_used=collections.Counter(LENS)), open(f'{OUT}/pc_run_meta.json', 'w'), indent=1, default=str)
