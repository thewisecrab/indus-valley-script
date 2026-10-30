"""Arbitrary-text control (session 8), mirroring the 'Panini Protocol' critique (https://ugrashravas.github.io/paniniprotocol,
fetched 2026-10-30): with enough freedom to fit sign values, can ANY text be 'read' as Sanskrit?

Same fitting freedom as claim_harness part C (session 5): sign values are drawn from Yajnadevam's own value inventory,
read with the same lipi rule (claim_harness.mech: optional inherent a) and hill-climbed (value swaps / re-draws on the 150
most frequent sign types) to maximise whole-text segmentability into the 4,361-word length-stratified Monier-Williams
sample (M2) on 80% of texts. The fitted key then reads the held-out 20% mechanically.

Corpora, all cut into texts with the length distribution of the unique Indus texts of 2..8 signs (claim_harness.texts_for_tests):
  indus_real            the Indus texts (ICIT / lipi signs, reading order)
  us_constitution_letters   the US Constitution, each letter a 'sign' (26 types), random-cut windows
  us_constitution_words     the US Constitution, each English word a 'sign' (logographic-style inventory), random-cut windows
  random_iid            sign strings drawn independently from the Indus sign frequencies (no order, no language)
  sanskrit_classical    real classical Sanskrit (DCS), each akshara a 'sign' (its own values are ignored), random-cut windows
  akkadian_graphemes    real Neo-Assyrian Akkadian (ORACC SAA letters), each grapheme a 'sign' (values ignored), random-cut windows
Measures on the held-out texts: M2 (fit lexicon), M1 (full Monier-Williams), M3 (vidyut 0.4 complete parse), and the drop under
within-text shuffling of the held-out texts read with the same fitted key (50 shuffles). 3 fitting seeds per corpus.
Deterministic: random.Random(int) everywhere, seeds from zlib.crc32 of labels; sorted iteration.
Usage: python arbitrary_text_control.py [--objective M2|M3] [--iters 3000] [--seeds 3] [--nshuf 50]
Output: outputs/arbitrary_text/fit_<objective>/results.csv, summary.json
"""
import os, sys, json, random, re, zlib, collections, argparse
import numpy as np, pandas as pd
from multiprocessing import Pool
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, f'{ROOT}/scripts')
import claim_harness as h
OUT = f'{ROOT}/outputs/arbitrary_text'; os.makedirs(OUT, exist_ok=True)
COR = f'{ROOT}/positive_control/outputs/corpora'
def crc(s): return zlib.crc32(s.encode())

_CHED = None
def vidyut_ok(s):
    global _CHED
    if _CHED is None:
        from vidyut.cheda import Chedaka; _CHED = Chedaka(f'{ROOT}/data/vidyut')
    if not s: return False
    toks = list(_CHED.run(s)) or [None]
    return all(t is not None and t.data is not None for t in toks)

def windows(stream, lens, seed):
    r = random.Random(seed); out = []
    for L in lens:
        i = r.randrange(0, len(stream) - L); out.append(tuple(stream[i:i + L]))
    return out

def build_corpora():
    indus = h.texts_for_tests(2, 8)
    lens = sorted(len(s) for s in indus); n = len(indus)
    rl = random.Random(crc('lens')); L = [rl.choice(lens) for _ in range(n)]
    C = {'indus_real': list(indus)}
    txt = open(f'{ROOT}/data_open/arbitrary_text/us_constitution_gutenberg5.txt').read().lower()
    letters = [f'L_{c}' for c in txt if 'a' <= c <= 'z']
    words = [f'W_{w}' for w in re.findall(r'[a-z]+', txt)]
    C['us_constitution_letters'] = windows(letters, L, crc('letters'))
    C['us_constitution_words'] = windows(words, L, crc('words'))
    freq = collections.Counter(x for s in indus for x in s); types = sorted(freq); wts = [freq[t] for t in types]
    ri = random.Random(crc('iid')); C['random_iid'] = [tuple(ri.choices(types, wts, k=l)) for l in L]
    sk = json.load(open(f'{COR}/sanskrit_classical.json')); C['sanskrit_classical'] = windows([f'S_{x}' for t in sk for x in t['signs']], L, crc('skt'))
    ak = json.load(open(f'{COR}/akkadian_NA_letters.json')); C['akkadian_graphemes'] = windows([f'A_{x}' for t in ak for x in t['signs']], L, crc('akk'))
    return C

POOL = None; LX = None; TR = {}
def init():
    global POOL, LX
    if POOL is None:
        key0 = h.load_key(); POOL = sorted(v for v in key0.values() if v)   # Yajnadevam's own value inventory (multiset)
        LX = h.get_lexicons(); TR['lm'] = h.trie(LX['sanskrit_MW']); TR['full'] = h.trie(LX['_full_MW'])

def seg(s, key, T): return h.segmentable(h.red_items(h.mech(s, key)), T)
def raw(s, key): return ''.join(c for c, _ in h.mech(s, key))

def fit_eval(args):
    cname, seqs, seed, iters, topk, nshuf, obj = args; init()
    f = (lambda s_, k_: seg(s_, k_, TR['lm'])) if obj == 'M2' else (lambda s_, k_: vidyut_ok(raw(s_, k_)))
    rng = random.Random(crc(f'fit|{cname}|{seed}'))
    seqs = list(seqs); rng.shuffle(seqs); cut = int(.8 * len(seqs)); train, test = seqs[:cut], seqs[cut:]
    types = sorted({x for s in seqs for x in s})
    key = {t: rng.choice(POOL) for t in types}
    freq = collections.Counter(x for s in train for x in s)
    top = [s for s, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:topk]]
    inv = collections.defaultdict(list)
    for i, s in enumerate(train):
        for x in set(s): inv[x].append(i)
    cur = [f(s, key) for s in train]; init_train = float(np.mean(cur))
    for it in range(iters):
        a = rng.choice(top)
        if rng.random() < .5:
            b = rng.choice(top); changed = {a: key[b], b: key[a]}
        else: changed = {a: rng.choice(POOL)}
        old = {k: key[k] for k in changed}; key.update(changed)
        idx = set(); [idx.update(inv[k]) for k in changed]
        new = {i: f(train[i], key) for i in idx}
        if sum(new[i] - cur[i] for i in idx) >= 0:
            for i, v in new.items(): cur[i] = v
        else: key.update(old)
    def meas(ss):
        return dict(M2=np.array([seg(s, key, TR['lm']) for s in ss]), M1=np.array([seg(s, key, TR['full']) for s in ss]),
                    M3=np.array([vidyut_ok(raw(s, key)) for s in ss]))
    real = meas(test)
    sh = [meas(h.shuffle_within(test, random.Random(crc(f'sh|{cname}|{seed}|{i}')))) for i in range(nshuf)]
    row = dict(corpus=cname, objective=obj, seed=seed, n_types=len(types), n_train=len(train), n_test=len(test), mean_len=round(float(np.mean([len(s) for s in seqs])), 3),
               iters=iters, topk=topk, train_obj_initial=round(init_train, 4), train_obj_fitted=round(float(np.mean(cur)), 4))
    for m in ('M2', 'M1', 'M3'):
        v = np.array([x[m].mean() for x in sh]); r = real[m].mean()
        row[f'heldout_{m}'] = round(float(r), 4); row[f'within_{m}'] = round(float(v.mean()), 4)
        row[f'drop_{m}'] = round(float(r - v.mean()), 4); row[f'p_{m}'] = round(float((1 + (v >= r).sum()) / (nshuf + 1)), 4)
    row['heldout_tokens_full_parse'] = int(sum(len(s) for s, ok in zip(test, real['M3']) if ok))
    print({k: row[k] for k in ('corpus', 'objective', 'seed', 'train_obj_initial', 'train_obj_fitted', 'heldout_M2', 'heldout_M1', 'heldout_M3', 'drop_M3', 'p_M3')}, flush=True)
    return row

def bh(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p); q = np.empty(n); prev = 1.0
    for rank, i in reversed(list(enumerate(o, 1))): prev = min(prev, p[i] * n / rank); q[i] = prev
    return q

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--iters', type=int, default=3000); ap.add_argument('--topk', type=int, default=150)
    ap.add_argument('--seeds', type=int, default=3); ap.add_argument('--nshuf', type=int, default=50); ap.add_argument('--procs', type=int, default=6)
    ap.add_argument('--objective', default='M2', choices=['M2', 'M3'], help='fit to M2 segmentation (as part C) or to the vidyut parse (M3)')
    ap.add_argument('--quick', action='store_true'); A = ap.parse_args()
    OUTX = f'{OUT}/fit_{A.objective}'; os.makedirs(OUTX, exist_ok=True)
    if A.quick: A.iters, A.seeds, A.nshuf = 300, 1, 5
    C = build_corpora()
    jobs = [(c, tuple(C[c]), s, A.iters, A.topk, A.nshuf, A.objective) for c in sorted(C) for s in range(A.seeds)]
    with Pool(A.procs) as p: rows = p.map(fit_eval, jobs, chunksize=1)
    df = pd.DataFrame(rows).sort_values(['corpus', 'seed'])
    pcols = [c for c in df.columns if c.startswith('p_')]
    q = bh(df[pcols].values.ravel()).reshape(len(df), len(pcols))
    for j, c in enumerate(pcols): df['q_' + c[2:]] = np.round(q[:, j], 4)
    df.to_csv(f'{OUTX}/results.csv', index=False)
    agg = df.groupby('corpus')[[c for c in df.columns if c.startswith(('heldout_', 'within_', 'drop_', 'train_obj'))]].mean().round(4)
    summ = dict(objective=A.objective, note='means over fitting seeds; per-seed rows with BH q (all p in the table) in results.csv', iters=A.iters, topk=A.topk, seeds=A.seeds,
                nshuf=A.nshuf, n_texts=len(C['indus_real']), by_corpus=agg.reset_index().to_dict('records'),
                source_paniniprotocol='https://ugrashravas.github.io/paniniprotocol (fetched 2026-10-30)')
    json.dump(summ, open(f'{OUTX}/summary.json', 'w'), indent=1)
    print(agg.to_string())
