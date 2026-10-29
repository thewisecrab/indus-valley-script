"""Sanskrit parse test (vidyut 0.4 cheda) for Yajnadevam's key: real vs shuffled vs permuted key vs phonotactic nonsense.
Metrics per string: full_parse (every token has a pada analysis and tokens cover the string), mean token length, share of tokens <=2 chars."""
import sys, os, json, random, re, collections
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__)); import claim_harness as h
from vidyut.cheda import Chedaka
ROOT = h.ROOT; C = Chedaka(f'{ROOT}/data/vidyut')
def analyse(s):
    s = s.strip()
    if not s: return None
    toks = []
    for w in re.split(r'[\s\-—]+', s):
        if w: toks += list(C.run(w)) or [None]
    ok = all(t is not None and t.data is not None for t in toks)
    L = [len(t.text) for t in toks if t is not None]
    return dict(full_parse=ok, mean_len=float(np.mean(L)) if L else 0.0, short_share=float(np.mean([l <= 2 for l in L])) if L else 1.0, n_tok=len(toks))
def summarize(rows):
    rows = [r for r in rows if r]
    return dict(n=len(rows), full_parse=round(float(np.mean([r['full_parse'] for r in rows])), 4),
                mean_token_len=round(float(np.mean([r['mean_len'] for r in rows])), 3), short_token_share=round(float(np.mean([r['short_share'] for r in rows])), 4))
key = h.load_key(); seqs = h.texts_for_tests()
mech = lambda s, k: ''.join(c for c, _ in h.mech(s, k))
rng = random.Random(0); res = {}
res['mechanical_real'] = summarize([analyse(mech(s, key)) for s in seqs])
res['mechanical_shuffled_within'] = summarize([analyse(mech(s, key)) for s in h.shuffle_within(seqs, random.Random(1))])
res['mechanical_shuffled_global'] = summarize([analyse(mech(s, key)) for s in h.shuffle_global(seqs, random.Random(2))])
signs = list(key); vals = [key[s] for s in signs]; rng.shuffle(vals); pk = dict(zip(signs, vals))
res['mechanical_permuted_key'] = summarize([analyse(mech(s, pk)) for s in seqs])
# phonotactic nonsense matched in length: order-3 char Markov on MW headwords (SLP1, unreduced)
mw = [m.group(1) for m in re.finditer(r'<k1>([^<]+)', open(f'{ROOT}/data/lexicons/mw.txt', encoding='utf8').read())]
tr = collections.defaultdict(collections.Counter)
for w in mw[::3]:
    w2 = '^^^' + w
    for i in range(3, len(w2)): tr[w2[i-3:i]][w2[i]] += 1
def gen(L):
    ctx, out = '^^^', ''
    while len(out) < L:
        nx = tr.get(ctx)
        if not nx: ctx = '^^^'; continue
        c = rng.choices(list(nx), weights=nx.values())[0]; out += c; ctx = ctx[1:] + c
    return out
res['markov_nonsense_matched_length'] = summarize([analyse(gen(len(mech(s, key)))) for s in seqs])
d = h.load_corpus(); pub = d[(d.sanskrit != '') & ~d.sanskrit.str.startswith('ref:')]
res['published_readings_as_written'] = summarize([analyse(r) for r in pub.sanskrit])
# published readings with spaces removed (forces vidyut to segment like the mechanical strings)
res['published_readings_unsegmented'] = summarize([analyse(re.sub(r'[\s\-]', '', r)) for r in pub.sanskrit])
json.dump(res, open(f'{ROOT}/outputs/claims/E_vidyut_parse.json', 'w'), indent=1)
for k, v in res.items(): print(k, v)
