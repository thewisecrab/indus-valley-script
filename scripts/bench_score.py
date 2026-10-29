"""Session 6: open claim-scoring benchmark. Scores ANY proposed sign->value key against the project's null models.
Usage: python scripts/bench_score.py bench/my_key.csv bench/my_key.meta.json [--quick]
Submission: CSV with columns sign_id,value (sign_id W### for ICIT/Wells, or M### for Mahadevan 1977); meta JSON with
  name, author, language, lexicon (built-in name or path to a UTF-8 word list, one word per line), inherent_vowel ("" or e.g. "a").
Tests (all on unique texts, reading order):
  T1 fixed-key readability: share of fully-valued texts (2-12 signs) whose concatenated value string segments completely
     into lexicon words (>= 2 letters), real order vs 5 within-text shuffles, 5 global shuffles and 5 permuted keys.
  T2 cross-lexicon control: the same readability with every other built-in lexicon (length-matched subsamples).
  T3 fitted-noise calibration: a key with the SAME value inventory hill-climbed (2,000 steps) to a within-text-shuffled
     corpus; the submission should beat it on held-out real texts.
  T4 per-sign leave-one-out (loo_signs.py statistic, syllabic mode): for each sign in >= 5 texts, its value vs every other
     value in the key; BH q.
  T5 free parameters: valued signs, distinct values, log2 of the number of possible assignments.
A key 'beats the nulls' only if T1 real > every shuffle and permuted key (rank p < .05 against the 15 nulls is impossible
with 15 draws, so the rule is: real above all 15), T1 real above every T2 lexicon, real held-out > T3, and >= 1 sign with
T4 q < .05. Output: bench/results/<name>.json"""
import os, sys, json, random, math, collections, re
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, f'{ROOT}/scripts')
import claim_harness as C
def red(v): return C.collapse(C.red_lat(v))
def corpus(scheme):
    if scheme == 'W':
        d = C.load_corpus(); d = d[~d.text.str.contains(r'000|999|/') & (d.text.str.len() > 0)]
        return sorted({tuple('W' + x.zfill(3) for x in s) for s in d.signs if 2 <= len(s) <= 12})
    m = pd.read_csv(f'{ROOT}/data/joyboseroy_indus_decipher/data/m77_indusscript_real_corpus.csv', dtype=str).fillna('')
    return sorted({tuple('M' + t[3:].zfill(3) for t in s.split()) for s, dmg in zip(m.sign_sequence, m.damaged)
                   if dmg != 'True' and 'MSg0' not in s.split() and 2 <= len(s.split()) <= 12})
def builtin_lexicons():
    import rebus_harness as Rb
    return {'sanskrit_MW': C.lex_sanskrit(), 'proto_dravidian_PDR': C.lex_pdr(), 'dravidian_DEDR_forms+PDR': Rb.lex_drav(),
            'finnish': C.lex_freq('fi'), 'turkish': C.lex_freq('tr'), 'hungarian': C.lex_freq('hu'), 'indonesian': C.lex_freq('id'), 'english': C.lex_freq('en')}
def items(seq, key, iv):
    out = []
    for i, s in enumerate(seq):
        if i and iv: out.append((iv, True))
        out += [(c, False) for c in key[s]]
    res = []
    for c, o in out:
        if res and res[-1][0] == c and not o: continue
        res.append((c, o))
    return res
def readable(seqs, key, T, iv):
    v = [s for s in seqs if all(key.get(x) for x in s)]
    return (float(np.mean([C.segmentable(items(s, key, iv), T) for s in v])) if v else float('nan')), len(v)
def main(csv, meta, quick=False):
    M = json.load(open(meta)); K = pd.read_csv(csv, dtype=str, keep_default_na=False)
    scheme = K.sign_id.iloc[0][0]; assert scheme in 'MW' and K.sign_id.str[0].eq(scheme).all(), 'sign_id must be all W### or all M###'
    key = {s: red(v) for s, v in zip(K.sign_id, K.value) if red(v)}; iv = red(M.get('inherent_vowel', '') or '')
    seqs = corpus(scheme); LX = builtin_lexicons()
    lexname = M['lexicon']
    W = LX[lexname] if lexname in LX else {red(w.strip()) for w in open(lexname, encoding='utf-8') if red(w.strip())}
    W = {w for w in W if len(w) >= 2}; T = C.trie(W)
    nrep = 2 if quick else 5; res = dict(name=M['name'], author=M.get('author', ''), language=M.get('language', ''), lexicon=lexname, scheme=scheme,
                                          n_texts_corpus=len(seqs), valued_signs=len(key))
    real, nv = readable(seqs, key, T, iv); res['T1'] = dict(real=real, n_fully_valued_texts=nv)
    res['T1']['shuffled_within'] = [readable(C.shuffle_within(seqs, random.Random(i)), key, T, iv)[0] for i in range(nrep)]
    res['T1']['shuffled_global'] = [readable(C.shuffle_global(seqs, random.Random(10 + i)), key, T, iv)[0] for i in range(nrep)]
    signs = list(key); vals = [key[s] for s in signs]; pk = []
    for i in range(nrep):
        v = vals[:]; random.Random(20 + i).shuffle(v); pk.append(readable(seqs, dict(zip(signs, v)), T, iv)[0])
    res['T1']['permuted_key'] = pk
    nulls = res['T1']['shuffled_within'] + res['T1']['shuffled_global'] + pk
    res['T1']['real_above_all_nulls'] = bool(all(real > x for x in nulls))
    # T2: length-matched comparison across lexicons
    allx = dict(LX); allx['_submission'] = W
    counts = {l: min(sum(1 for w in v if len(w) == l) for v in allx.values()) for l in range(2, 11)}
    sub = {k: C.stratified(v, counts) for k, v in allx.items()}
    res['T2'] = {k: readable(seqs, key, C.trie(v), iv)[0] for k, v in sub.items()}
    res['T2']['submission_lexicon_is_best'] = bool(all(res['T2']['_submission'] >= v for k, v in res['T2'].items() if k != '_submission'))
    # T3: fitted-noise key with the same value inventory, scored on held-out real texts
    rng = random.Random(1); idx = list(range(len(seqs))); rng.shuffle(idx); cut = int(.8 * len(seqs))
    train = [seqs[i] for i in idx[:cut]]; test = [seqs[i] for i in idx[cut:]]
    shtrain = C.shuffle_within(train, random.Random(2)); top = [s for s, _ in collections.Counter(x for s in shtrain for x in s if x in key).most_common(150)]
    fk = dict(zip(signs, random.Random(3).sample(vals, len(vals))))
    sh_v = [s for s in shtrain if all(x in key for x in s)]; inv = collections.defaultdict(list)
    for i, s in enumerate(sh_v):
        for x in set(s): inv[x].append(i)
    cur = [C.segmentable(items(s, fk, iv), T) for s in sh_v]
    for it in range(300 if quick else 2000):   # swap-only hill-climb (keeps the value multiset), incremental scoring
        a = rng.choice(top); b = rng.choice(top)
        if a == b: continue
        fk[a], fk[b] = fk[b], fk[a]; ch = sorted(set(inv[a]) | set(inv[b]))
        new = {i: C.segmentable(items(sh_v[i], fk, iv), T) for i in ch}
        if sum(new[i] - cur[i] for i in ch) >= 0:
            for i, v in new.items(): cur[i] = v
        else: fk[a], fk[b] = fk[b], fk[a]
    res['T3'] = dict(submission_heldout=readable(test, key, T, iv)[0], fitted_to_shuffled_heldout=readable(test, fk, T, iv)[0])
    res['T3']['submission_beats_fitted_noise'] = bool(res['T3']['submission_heldout'] > res['T3']['fitted_to_shuffled_heldout'])
    # T4: per-sign LOO (syllabic mode of loo_signs.py)
    import loo_signs as LS
    df = LS.run_condition(key, 'syl', seqs, {w for w in W if len(w) >= 4}, 'submission', procs=8)
    res['T4'] = dict(signs_tested=int(len(df)), p_lt_05=int((df.p_alt < .05).sum()), q_lt_05=int((df.q_alt < .05).sum()),
                     mean_p_alt=float(df.p_alt.mean()) if len(df) else None, min_possible_p=1 / max(1, len(set(vals))))
    nvals = len(set(vals)); res['T5'] = dict(valued_signs=len(key), distinct_values=nvals, log2_assignments=round(len(key) * math.log2(max(nvals, 1)), 1),
                                            inherent_vowel=iv)
    res['beats_all_nulls'] = bool(res['T1']['real_above_all_nulls'] and res['T2']['submission_lexicon_is_best'] and res['T3']['submission_beats_fitted_noise'] and res['T4']['q_lt_05'] >= 1)
    os.makedirs(f'{ROOT}/bench/results', exist_ok=True)
    out = f"{ROOT}/bench/results/{re.sub(r'[^A-Za-z0-9_.-]', '_', M['name'])}.json"; json.dump(res, open(out, 'w'), indent=1); print(json.dumps(res, indent=1)); return res
if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], '--quick' in sys.argv)
