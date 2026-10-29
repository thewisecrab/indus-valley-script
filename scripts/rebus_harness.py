"""Rebus/logographic key test (Dravidian and controls), strict protocol as claim_harness part C.
Hypothesis form: each frequent sign = one short root (2-4 reduced chars) drawn from the language's own lexicon.
Score = share of adjacent sign pairs (within damage-free segments) whose concatenated values are an attested lexeme
(=a 'compound' or derived word) in the same lexicon. Fit on 80% of texts by hill-climbing, report held-out score;
compare real vs shuffled corpora and Dravidian vs other lexicons. Also: degenerate check (single-sign 'readability' is 100% by
construction for any word-valued key), and Parpola-seeded numeral+fish compounds vs the Dravidian DB."""
import sys, os, json, random, collections, re
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(__file__)); import claim_harness as h
ROOT = h.ROOT; OUT = f'{ROOT}/outputs/claims'
def lex_drav():
    d = pd.read_csv(f'{ROOT}/data/zenodo/dravidian_db_22682542/forms.csv', dtype=str, keep_default_na=False)
    ws = {h.collapse(h.red_lat(re.sub(r'[^\w]', '', w))) for w in d.Form}
    return ws | h.lex_pdr()
CACHE = {}
def lexicons():
    if CACHE: return CACHE
    full = {'dravidian_DEDR_forms+PDR': lex_drav(), 'sanskrit_MW': h.lex_sanskrit(), 'finnish': h.lex_freq('fi'), 'turkish': h.lex_freq('tr'),
            'hungarian': h.lex_freq('hu'), 'indonesian': h.lex_freq('id'), 'english': h.lex_freq('en')}
    full['markov_nonsense'] = h.lex_random({w for w in full['dravidian_DEDR_forms+PDR'] if 2 <= len(w) <= 10}, seed=1)
    counts = {l: min(sum(1 for w in v if len(w) == l) for v in full.values()) for l in range(2, 11)}
    for k, v in full.items(): CACHE[k] = h.stratified(v, counts)
    CACHE['_counts'] = counts
    return CACHE
def corpus_pairs(seqs):
    return [list(zip(s, s[1:])) for s in seqs]
def fit(args):
    lname, kind, seed, iters, topk = args
    L = lexicons()[lname]; rng = random.Random(seed)
    seqs = h.texts_for_tests(2, 12)
    if kind == 'shuffled_within': seqs = h.shuffle_within(seqs, random.Random(seed + 100))
    elif kind == 'shuffled_global': seqs = h.shuffle_global(seqs, random.Random(seed + 200))
    rng.shuffle(seqs); cut = int(.8 * len(seqs)); tr, te = seqs[:cut], seqs[cut:]
    inv = sorted(w for w in L if 2 <= len(w) <= 4)
    freq = collections.Counter(x for s in tr for x in s); top = [s for s, _ in freq.most_common(topk)]
    key = {s: rng.choice(inv) for s in freq}
    P = [p for s in tr for p in zip(s, s[1:])]
    byS = collections.defaultdict(list)
    for i, (a, b) in enumerate(P): byS[a].append(i); byS[b].append(i)
    ok = lambda a, b: (key[a] + key[b]) in L or h.collapse(key[a] + key[b]) in L
    cur = [ok(a, b) for a, b in P]; tot = sum(cur)
    for _ in range(iters):
        s = rng.choice(top); old = key[s]; key[s] = rng.choice(inv)
        idx = set(byS[s]); new = {i: ok(*P[i]) for i in idx}; dlt = sum(new[i] - cur[i] for i in idx)
        if dlt >= 0:
            for i, v in new.items(): cur[i] = v
            tot += dlt
        else: key[s] = old
    Pt = [p for s in te for p in zip(s, s[1:])]
    te_ok = [ok(a, b) if a in key and b in key else False for a, b in Pt]
    return dict(lexicon=lname, corpus=kind, seed=seed, train=tot / len(P), heldout=float(np.mean(te_ok)), n_train_pairs=len(P), n_test_pairs=len(Pt), iters=iters)
if __name__ == '__main__':
    L = lexicons()
    print('stratum counts', L['_counts'])
    jobs = [(l, c, s, 4000, 150) for l in [k for k in L if not k.startswith('_')] for c in ['real', 'shuffled_within', 'shuffled_global'] for s in (0, 1)]
    rows = []
    with Pool(6) as p:
        for r in p.imap_unordered(fit, jobs):
            rows.append(r); print(r, flush=True)
    R = pd.DataFrame(rows); R.to_csv(f'{OUT}/F_rebus_fitted.csv', index=False)
    S = R.groupby(['lexicon', 'corpus']).heldout.mean().unstack().round(4); S.to_csv(f'{OUT}/F_rebus_summary.csv'); print(S)
    # Parpola-seeded compounds: numeral + fish (M059 / W220)
    D = lexicons()['dravidian_DEDR_forms+PDR']; Dfull = lex_drav()
    nums = {1: ['or', 'oru'], 2: ['ir', 'iru'], 3: ['mu', 'mun'], 4: ['nal', 'nan'], 5: ['cai', 'aintu', 'ancu'], 6: ['aru'], 7: ['ilu', 'elu'], 8: ['ittu', 'ettu']}
    att = {k: [v + 'min' for v in vs if h.collapse(v + 'min') in Dfull or (v + 'min') in Dfull] for k, vs in nums.items()}
    json.dump(dict(note='Parpola 1994 numeral+fish compounds (aru-min etc.) looked up in full Dravidian DB forms (reduced alphabet)', attested=att,
                   min_in_db=('min' in Dfull)), open(f'{OUT}/F_parpola_compounds.json', 'w'), indent=1)
    print(att, 'min' in Dfull)
