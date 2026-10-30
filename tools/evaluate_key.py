"""evaluate_key.py (session 8): a simple shuffle benchmark for ANY proposed Indus reading.

Question it answers: does the proposal read the REAL inscriptions better than the SAME inscriptions with their signs
put in a random order? A key that really reads a script should lose a lot when sign order is destroyed. Correct keys
for real Sanskrit and Akkadian, cut to Indus-like lengths, do (positive control, positive_control/README.md).

Two input formats (docs/SUBMIT_A_KEY.md):
  key       a sign->value CSV (columns sign_id,value; sign_id W### for ICIT/Wells numbers, M### for Mahadevan 1977)
            plus a meta JSON (name, language, lexicon, reading_rule, alphabet). Every text is read mechanically.
  readings  per-inscription readings: CSV with columns inscription_id,reading[,units]. `units` (optional) is the reading
            split per sign in reading order, joined by '|'. Without `units`, the reading is split per sign automatically
            by aligning it to a sign->value key given with --align-key (minimum edit distance on a reduced alphabet).
            Shuffles permute the per-sign pieces of each reading.

Measures (the same as the Yajnadevam test and the positive control):
  M1  the whole reading splits into words of the full lexicon
  M2  the same with a length-stratified 4,361-word subsample of that lexicon (word-length counts shipped in
      positive_control/outputs/pc_run_meta.json), so lexicons of different sizes are comparable
  M3  (Sanskrit only) the reading gets a complete morphological parse from vidyut 0.4 (the strongest measure)
Nulls: within-text shuffles (signs of each text permuted), global shuffles (all signs re-dealt into texts of the same
lengths), and, in key mode, permuted keys (the same values given to the wrong signs). p is one-sided,
(1 + #null >= real) / (N + 1); Benjamini-Hochberg q across all measure x null tests of a run.
Deterministic: every RNG is random.Random(zlib.crc32(label)); iteration is over sorted lists.

Usage:
  python tools/evaluate_key.py key  KEY.csv META.json [--nshuf 200] [--nperm 100] [--procs 8] [--out DIR]
  python tools/evaluate_key.py readings READINGS.csv META.json [--align-key KEY.csv] [--nshuf 200] [--out DIR]
  python tools/evaluate_key.py key bench/examples/toy_key.csv bench/examples/toy_key.meta.json --corpus toy   (offline demo)
Output: <out>/<name>.json and <name>.md (plain-language verdict). Default out: bench/results/evaluate_key/
The Indus corpora are NOT shipped (see DATA_POLICY.md); run scripts/fetch_data.sh first. Outputs are aggregate
statistics only and are safe to publish.
"""
import os, sys, re, json, zlib, random, argparse, collections, datetime, itertools
import numpy as np, pandas as pd
from multiprocessing import Pool
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, f'{ROOT}/scripts')
import claim_harness as C

def rng_for(label): return random.Random(zlib.crc32(label.encode('utf-8')))

# ---------------- corpora ----------------
def corpus(scheme):
    """returns sorted list of (inscription_id, tuple of sign ids in reading order); unique texts of 2..12 signs."""
    if scheme == 'toy':
        p = next(q for q in [f'{ROOT}/data_open/toy/toy_corpus.csv', f'{ROOT}/data/toy/toy_corpus.csv'] if os.path.exists(q))
        d = pd.read_csv(p, dtype=str)
        return sorted((i, tuple(s.split())) for i, s in zip(d.inscription_id, d.sign_sequence) if 2 <= len(s.split()) <= 12)
    if scheme == 'W':
        d = C.load_corpus(); d = d[~d.text.str.contains(r'000|999|/') & (d.text.str.len() > 0)]
        seen, out = set(), []
        for i, s in sorted(zip(d['id'], d.signs), key=lambda r: [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', r[0])]):
            t = tuple('W' + x.zfill(3) for x in s)
            if 2 <= len(t) <= 12 and t not in seen: seen.add(t); out.append((i, t))
        return out
    m = pd.read_csv(f'{ROOT}/data/joyboseroy_indus_decipher/data/m77_indusscript_real_corpus.csv', dtype=str).fillna('')
    seen, out = set(), []
    for k, (s, dmg) in enumerate(zip(m.sign_sequence, m.damaged)):
        if dmg == 'True' or 'MSg0' in s.split(): continue
        t = tuple('M' + x[3:].zfill(3) for x in s.split())
        if 2 <= len(t) <= 12 and t not in seen: seen.add(t); out.append((f'M77row{k}', t))
    return out
def all_ids(scheme):
    """id -> sign tuple for EVERY inscription (readings mode looks texts up by id, duplicates included)."""
    if scheme == 'W':
        d = C.load_corpus(); return {i: tuple('W' + x.zfill(3) for x in s) for i, s in zip(d['id'], d.signs)}
    return dict(corpus(scheme))

# ---------------- alphabets & lexicons ----------------
def reduce_items(items, alphabet):
    """items: list of (char, optional). Reduce to the shared 3-vowel alphabet used by every test in this project."""
    if alphabet == 'slp1': return C.red_items(items)
    out = []
    for c, o in items:
        for ch in C.red_lat(c): out.append((ch, o))
    res = []
    for c, o in out:
        if res and res[-1][0] == c: continue
        res.append((c, o))
    return res
def reduce_word(w, alphabet): return C.collapse(C.red_slp(w)) if alphabet == 'slp1' else C.collapse(C.red_lat(w))
BUILTIN = {'sanskrit_MW': lambda: C.lex_sanskrit(), 'proto_dravidian_PDR': lambda: C.lex_pdr(), 'english': lambda: C.lex_freq('en'),
           'finnish': lambda: C.lex_freq('fi'), 'turkish': lambda: C.lex_freq('tr'), 'hungarian': lambda: C.lex_freq('hu'), 'indonesian': lambda: C.lex_freq('id')}
def lexicon(spec, alphabet, base_dir):
    if spec in BUILTIN: W = BUILTIN[spec]()
    else:
        p = spec if os.path.isabs(spec) else os.path.join(base_dir, spec)
        W = {reduce_word(w.strip(), alphabet) for w in open(p, encoding='utf-8') if w.strip()}
    return {w for w in W if w}   # built-in lexicons are used exactly as in claim_harness (single letters included)
def length_counts():
    return {int(k): v for k, v in json.load(open(f'{ROOT}/positive_control/outputs/pc_run_meta.json'))['length_counts'].items()}
def stratified(W, seed_label):
    counts = length_counts(); by = collections.defaultdict(list)
    for w in sorted(W): by[len(w)].append(w)
    r = random.Random(0); out = set()   # same sampler and seed as claim_harness.stratified(seed=0), so built-in results reproduce
    for L in sorted(counts): out.update(r.sample(by[L], min(counts[L], len(by[L]))))
    return out

# ---------------- reading rules ----------------
def items_for(seq, key, rule, iv, vals=None):
    """per-sign values -> list of (char, optional). vals (optional) gives the value of each position directly."""
    if vals is None: vals = [key.get(s, '') for s in seq]
    if rule == 'lipi':                                     # Yajnadevam's lipi rule (optional inherent a)
        ids = [f'#{i}' for i in range(len(seq))]
        return C.mech(ids, dict(zip(ids, vals)))
    out = []
    for i, v in enumerate(vals):
        if i and iv: out.append((iv, True))
        out += [(c, False) for c in v]
    return out
def raw_string(items): return ''.join(c for c, _ in items)

# ---------------- scoring (worker globals) ----------------
G = {}
MAX_COMBOS = 64
def init(state):
    G.clear(); G.update(state)
    if G.get('use_vidyut'):
        from vidyut.cheda import Chedaka
        G['ched'] = Chedaka(f'{ROOT}/data/vidyut')
def vidyut_ok(s):
    s = re.sub(r"[^A-Za-z~' ]", '', s).strip()
    if not s: return False
    toks = []
    for w in s.split():
        toks += list(G['ched'].run(w)) or [None]
    return all(t is not None and t.data is not None for t in toks)
def score_items(it):
    red = reduce_items(it, G['alphabet'])
    r = {'M1': C.segmentable(red, G['T_full']), 'M2': C.segmentable(red, G['T_lm'])}
    if G.get('use_vidyut'): r['M3'] = vidyut_ok(raw_string(it))
    return r
def score_key_texts(seqs, key):
    """key: sign -> list of candidate values. A text passes a measure if ANY combination of candidates passes
    (at most MAX_COMBOS combinations, in candidate order). With one value per sign this is ordinary key reading."""
    R = collections.defaultdict(list)
    for s in seqs:
        best = {}
        for combo in itertools.islice(itertools.product(*[key.get(x, ['']) for x in s]), MAX_COMBOS):
            r = score_items(items_for(s, None, G['rule'], G['iv'], list(combo)))
            for m, v in r.items(): best[m] = best.get(m, False) or v
            if all(best.values()): break
        for m, v in best.items(): R[m].append(v)
    return {k: np.array(v, bool) for k, v in R.items()}
def score_units(unit_lists):
    R = collections.defaultdict(list)
    for units in unit_lists:
        for m, v in score_items([x for u in units for x in u]).items(): R[m].append(v)
    return {k: np.array(v, bool) for k, v in R.items()}
def edge_fixed(s, r):
    """shuffle only the interior signs; the first and last stay in place (texts of <= 3 signs are unchanged).
    Controls for positional regularities: a reading that only fits the script's first/last-sign habits loses nothing here."""
    s = list(s)
    if len(s) <= 3: return tuple(s) if isinstance(s[0], str) else s
    mid = s[1:-1]; mid = r.sample(mid, len(mid)); out = [s[0]] + mid + [s[-1]]
    return tuple(out) if isinstance(s[0], str) else out
def pos_global(seqs, r):
    """re-deal tokens across texts WITHIN position classes (first / middle / last): every text keeps its length and every
    position keeps exactly the signs that occur there in the corpus, but the actual sequences are destroyed. Controls
    for positional habits at all positions (a reading tuned to where signs usually stand loses nothing here)."""
    pools = {'F': [], 'M': [], 'L': []}
    cls = lambda i, n: 'F' if i == 0 else ('L' if i == n - 1 else 'M')
    for s in seqs:
        for i, x in enumerate(s): pools[cls(i, len(s))].append(x)
    for k in sorted(pools): r.shuffle(pools[k])
    it = {k: iter(v) for k, v in pools.items()}; out = []
    for s in seqs:
        t = [next(it[cls(i, len(s))]) for i in range(len(s))]
        out.append(tuple(t) if isinstance(s, tuple) else t)
    return out
def work(job):
    kind, rep = job
    r = rng_for(f"{G['name']}|{G['tag']}|{kind}|{rep}")
    if G['mode'] == 'key':
        seqs = G['seqs']
        if kind == 'within': seqs = [tuple(r.sample(list(s), len(s))) for s in seqs]
        elif kind == 'edgefixed': seqs = [edge_fixed(s, r) for s in seqs]
        elif kind == 'posglobal': seqs = pos_global(seqs, r)
        elif kind == 'global':
            pool = [x for s in seqs for x in s]; r.shuffle(pool); out, k = [], 0
            for s in seqs: out.append(tuple(pool[k:k + len(s)])); k += len(s)
            seqs = out
        key = G['key']
        if kind == 'permkey':
            signs = sorted(key); vals = [key[s] for s in signs]; r.shuffle(vals); key = dict(zip(signs, vals))
        return kind, score_key_texts(seqs, key)
    U = G['units']        # per text, list of per-sign item lists
    if kind == 'within': U = [r.sample(u, len(u)) for u in U]
    elif kind == 'edgefixed': U = [edge_fixed(u, r) for u in U]
    elif kind == 'posglobal': U = pos_global(U, r)
    elif kind == 'global':
        pool = [x for u in U for x in u]; r.shuffle(pool); out, k = [], 0
        for u in U: out.append(pool[k:k + len(u)]); k += len(u)
        U = out
    return kind, score_units(U)
def battery(state, nshuf, nperm, procs):
    """real + within / edge-fixed / global shuffles (+ permuted keys in key mode). returns per-measure rows (p, no q yet)."""
    state = dict(state, lens=[len(x) for x in (state['seqs'] if state['mode'] == 'key' else state['units'])])
    jobs = [('real', 0)] + [('within', i) for i in range(nshuf)] + [('edgefixed', i) for i in range(nshuf)] + [('posglobal', i) for i in range(nshuf)] + [('global', i) for i in range(nshuf)] + ([('permkey', i) for i in range(nperm)] if state['mode'] == 'key' and nperm else [])
    with Pool(procs, initializer=init, initargs=(state,)) as p:
        out = p.map(work, jobs, chunksize=2)
    real = out[0][1]; nulls = collections.defaultdict(list)
    for kind, r in out[1:]: nulls[kind].append(r)
    rows = []
    for m in sorted(real):
        row = dict(test=state['tag'], measure=m, n_texts=int(len(real[m])), n_texts_4plus=int(sum(1 for L in state['lens'] if L >= 4)), real=round(float(real[m].mean()), 4))
        m4 = np.array(state['lens']) >= 4
        row['real_4plus'] = round(float(real[m][m4].mean()), 4) if m4.any() else None
        for kind in ['within', 'edgefixed', 'posglobal', 'global', 'permkey']:
            if kind not in nulls: continue
            if m4.any():
                v4 = np.array([r[m][m4].mean() for r in nulls[kind]])
                row[f'drop_{kind}_4plus'] = round(float(real[m][m4].mean() - v4.mean()), 4)
                row[f'p_{kind}_4plus'] = round(float((1 + (v4 >= real[m][m4].mean()).sum()) / (len(v4) + 1)), 4)
            v = np.array([r[m].mean() for r in nulls[kind]])
            row[f'{kind}_mean'] = round(float(v.mean()), 4); row[f'{kind}_95'] = f'{np.percentile(v, 2.5):.3f}-{np.percentile(v, 97.5):.3f}'
            row[f'drop_{kind}'] = round(float(real[m].mean() - v.mean()), 4)
            row[f'p_{kind}'] = round(float((1 + (v >= real[m].mean()).sum()) / (len(v) + 1)), 4)
            row[f'n_{kind}'] = len(v)
        rows.append(row)
    return rows

def bh(ps):
    ps = np.asarray(ps, float); n = len(ps); o = np.argsort(ps); q = np.empty(n); prev = 1.0
    for rank, i in reversed(list(enumerate(o, 1))):
        prev = min(prev, ps[i] * n / rank); q[i] = prev
    return q

# ---------------- alignment of free-text readings to signs ----------------
def lev(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1): cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]
def align(reading, seq, key, alphabet):
    """split `reading` (no spaces) into len(seq) contiguous pieces minimising sum lev(reduced value, reduced piece)."""
    s = reading; n, L = len(seq), len(s)
    rv = [reduce_word(key.get(x, ''), alphabet) for x in seq]
    INF = 10 ** 9; D = [[INF] * (L + 1) for _ in range(n + 1)]; B = [[0] * (L + 1) for _ in range(n + 1)]; D[0][0] = 0
    rc = {}
    def red(a, b):
        if (a, b) not in rc: rc[(a, b)] = reduce_word(s[a:b], alphabet)
        return rc[(a, b)]
    for i in range(1, n + 1):
        for b in range(L + 1):
            best, arg = INF, 0
            for a in range(max(0, b - 3 * max(1, len(rv[i - 1])) - 4), b + 1):
                if D[i - 1][a] >= INF: continue
                c = D[i - 1][a] + lev(rv[i - 1], red(a, b)) + (0 if b > a or not rv[i - 1] else 1)
                if c < best: best, arg = c, a
            D[i][b], B[i][b] = best, arg
    cuts = [L]
    for i in range(n, 0, -1): cuts.append(B[i][cuts[-1]])
    cuts = cuts[::-1]
    return [s[cuts[i]:cuts[i + 1]] for i in range(n)], D[n][L]

# ---------------- positive-control reference ----------------
def reference():
    pc = pd.read_csv(f'{ROOT}/positive_control/outputs/pc_summary.csv')
    pc = pc[pc.textset == 'lenmatch_wordaligned']
    ref = {}
    for r in pc.itertuples():
        m = {'M1_seg_full': 'M1', 'M2_seg_lm4361': 'M2', 'M3_vidyut': 'M3'}.get(r.measure)
        if not m: continue
        ref.setdefault(m, []).append(dict(corpus=r.corpus, key=r.key, real=r.real, within=r.within, drop_within=r.drop_within,
                                          p_within=r.p_within, mean_len=r.mean_len, drop_edgefixed=None))
    ef = f'{ROOT}/positive_control/outputs/pc_positional_nulls.csv'     # session 8: positional nulls for the same texts
    if os.path.exists(ef):
        MM = {'M1_seg_full': 'M1', 'M2_seg_lm4361': 'M2', 'M3_vidyut': 'M3'}
        for r in pd.read_csv(ef).to_dict('records'):
            for x in ref.get(MM.get(r['measure'], r['measure']), []):
                if x['corpus'] == r['corpus'] and x['key'] == r['key']:
                    x.update({k: v for k, v in r.items() if ('edgefixed' in k or 'posglobal' in k or k.endswith('4plus')) and k != 'n_texts_4plus'})
    return ref
def ref_drop(ref, m, language, kind='within'):
    rows = [x for x in ref.get(m, []) if x['key'] == 'correct' and (x['corpus'].startswith('sanskrit') if 'sanskrit' in language.lower() or m == 'M3' else True)
            and x.get(f'drop_{kind}') is not None]
    return (min(x[f'drop_{kind}'] for x in rows) if rows else None), rows

# ---------------- main ----------------
def with_q(rows):
    keys = [(i, k) for i, r in enumerate(rows) for k in ['within', 'edgefixed', 'posglobal', 'global', 'permkey', 'edgefixed_4plus', 'posglobal_4plus'] if f'p_{k}' in r]
    q = bh([rows[i][f'p_{k}'] for i, k in keys])
    for (i, k), qq in zip(keys, q): rows[i][f'q_{k}'] = round(float(qq), 4)
    return rows
def derive_key(pairs, top):
    """pairs: list of (sign tuple, list of raw pieces). Most frequent piece(s) per sign; ties broken alphabetically."""
    cnt = collections.defaultdict(collections.Counter)
    for seq, pieces in pairs:
        for x, pc in zip(seq, pieces): cnt[x][pc] += 1
    return {x: [v for v, _ in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:top]] for x, c in sorted(cnt.items())}

def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('mode', choices=['key', 'readings']); ap.add_argument('input'); ap.add_argument('meta')
    ap.add_argument('--align-key'); ap.add_argument('--corpus', default=None, help='W (ICIT/lipi), M (M77) or toy; default from sign ids (key) or W (readings)')
    ap.add_argument('--nshuf', type=int, default=200); ap.add_argument('--nperm', type=int, default=100); ap.add_argument('--procs', type=int, default=8)
    ap.add_argument('--out', default=f'{ROOT}/bench/results/evaluate_key')
    A = ap.parse_args()
    M = json.load(open(A.meta)); base = os.path.dirname(os.path.abspath(A.meta))
    name = re.sub(r'[^A-Za-z0-9_.-]', '_', M['name']); language = M.get('language', '')
    alphabet = M.get('alphabet', 'slp1' if 'sanskrit' in language.lower() else 'latin')
    rule = M.get('reading_rule', 'concat'); iv = M.get('inherent_vowel', '') or ''
    use_vidyut = bool(M.get('vidyut_parse', 'sanskrit' in language.lower())) and os.path.isdir(f'{ROOT}/data/vidyut')
    W = lexicon(M['lexicon'], alphabet, base); Wlm = stratified(W, f'{name}|lexicon')
    common = dict(name=name, alphabet=alphabet, iv=iv, use_vidyut=use_vidyut, T_full=C.trie(W), T_lm=C.trie(Wlm))
    res = dict(name=M['name'], author=M.get('author', ''), language=language, lexicon=M['lexicon'], lexicon_size=len(W), lexicon_lm_size=len(Wlm),
               alphabet=alphabet, mode=A.mode, n_shuffles=A.nshuf, run_date_ist=datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
               tool='tools/evaluate_key.py (session 8)', vidyut_parse=use_vidyut)
    rows = []
    if A.mode == 'key':
        K = pd.read_csv(A.input, dtype=str, keep_default_na=False)
        if rule == 'lipi':   # lipi's rule handles empty and '.' values itself; every text is read (as in claim_harness part B)
            key = {s: [v] for s, v in zip(K.sign_id, K.value)}
        else:
            key = {s: [v.strip()] for s, v in zip(K.sign_id, K.value) if v.strip() and v.strip() != '.'}
        scheme = A.corpus or K.sign_id.iloc[0][0]
        texts = corpus(scheme)
        seqs = [t for _, t in texts if rule == 'lipi' or all(x in key for x in t)]
        res.update(reading_rule=rule, inherent_vowel=iv, corpus=scheme, n_texts_corpus=len(texts), n_texts_scored=len(seqs),
                   valued_signs=len(key), distinct_values=len({v[0] for v in key.values()}), mean_signs_per_text=round(float(np.mean([len(x) for x in seqs])), 2))
        rows += battery(dict(common, mode='key', tag='key', rule=rule, seqs=seqs, key=key), A.nshuf, A.nperm, A.procs)
        res['primary_test'] = 'key'
    else:
        R = pd.read_csv(A.input, dtype=str, keep_default_na=False)
        scheme = A.corpus or 'W'
        ids = all_ids(scheme) if (A.align_key or scheme == 'toy' or os.path.exists(f'{ROOT}/data/lipi/inscriptions.csv')) else {}
        akey = None
        if A.align_key:
            K = pd.read_csv(A.align_key, dtype=str, keep_default_na=False); akey = {s: v for s, v in zip(K.sign_id, K.value)}
        need_align = 'units' not in R.columns or (R['units'] == '').any()
        assert not need_align or akey, 'readings without a units column need --align-key'
        recs, costs, skipped = [], [], 0
        for r in sorted(R.itertuples(), key=lambda r: r.inscription_id):
            rd = r.reading.strip(); seq = ids.get(r.inscription_id)
            if not rd: continue
            if 'units' in R.columns and r.units.strip():
                pieces = [p.strip() for p in r.units.split('|')]
                if seq is not None and len(seq) != len(pieces): seq = None
            else:
                if not seq or not (2 <= len(seq) <= 12): skipped += 1; continue
                flat = re.sub(r"[^A-Za-z~']", '', rd)
                pieces, cost = align(flat, seq, akey, alphabet); costs.append(cost / max(1, len(reduce_word(flat, alphabet))))
            if len(pieces) < 2: skipped += 1; continue
            recs.append(dict(id=r.inscription_id, seq=seq, pieces=pieces, reading=rd))
        res.update(corpus=scheme, n_readings_input=len(R), n_readings_scored=len(recs), n_skipped=skipped,
                   alignment='units column' if not need_align else f'automatic, --align-key {os.path.basename(A.align_key)}',
                   mean_alignment_cost_per_char=round(float(np.mean(costs)), 4) if costs else None,
                   mean_signs_per_text=round(float(np.mean([len(x['pieces']) for x in recs])), 2))
        init(dict(common))
        if use_vidyut:
            res['fluency'] = dict(M3_as_written=round(float(np.mean([vidyut_ok(x['reading']) for x in recs])), 4),
                                  M3_unsegmented=round(float(np.mean([vidyut_ok(''.join(x['pieces'])) for x in recs])), 4))
        U = [[[(c, False) for c in p] for p in x['pieces']] for x in recs]
        # R2: shuffle the per-sign pieces of each reading
        rows += battery(dict(common, mode='units', tag='R2_piece_shuffle', units=U), A.nshuf, 0, A.procs)
        # R2 mismatch control: each reading re-paired with a random OTHER inscription of the same sign count, re-aligned
        if akey:
            byL = collections.defaultdict(list)
            for i, t in corpus(scheme): byL[len(t)].append(t)
            r0 = rng_for(f'{name}|mismatch'); Um = []
            for x in recs:
                other = r0.choice(byL[len(x['pieces'])]) if byL[len(x['pieces'])] else None
                if other is None: continue
                pcs, _ = align(re.sub(r"[^A-Za-z~']", '', x['reading']) if need_align else ''.join(x['pieces']), other, akey, alphabet)
                Um.append([[(c, False) for c in p] for p in pcs])
            rows += battery(dict(common, mode='units', tag='R2m_mismatch_control', units=Um), A.nshuf, 0, A.procs)
        # R3: values the readings actually use, learned on 80% of inscriptions, read the held-out 20% mechanically
        paired = [x for x in recs if x['seq'] is not None]
        if paired:
            fold = lambda i: zlib.crc32(f'heldout|{i}'.encode()) % 5 == 0
            train = [(x['seq'], x['pieces']) for x in paired if not fold(x['id'])]
            seen = {x['seq'] for x in paired if not fold(x['id'])}
            hold = sorted({t for i, t in corpus(scheme) if fold(i) and t not in seen})
            for top, tag, ns in [(1, 'R3_derived_values_heldout', A.nshuf), (2, 'R3b_derived_top2_any_heldout', max(20, A.nshuf // 4))]:
                dk = derive_key(train, top)
                hs = [t for t in hold if all(x in dk for x in t)]
                res[f'{tag}_info'] = dict(train_readings=len(train), heldout_texts=len(hs), signs_with_values=len(dk))
                if len(hs) >= 30:
                    rows += battery(dict(common, mode='key', tag=tag, rule='concat', seqs=hs, key=dk), ns, ns // 2, A.procs)
            res['primary_test'] = 'R3_derived_values_heldout'
        else:
            res['primary_test'] = 'R2_piece_shuffle'
    res['results'] = with_q(rows)
    ref = reference(); res['positive_control_reference'] = {m: ref.get(m, []) for m in sorted({r['measure'] for r in rows})}
    res['verdict'] = verdict(res, rows, ref, language)
    os.makedirs(A.out, exist_ok=True)
    json.dump(res, open(f'{A.out}/{name}.json', 'w'), indent=1, default=str)
    open(f'{A.out}/{name}.md', 'w').write(report_md(res))
    print(report_md(res))

def verdict(res, rows, ref, language):
    prim_test = res['primary_test']
    by = {r['measure']: r for r in rows if r['test'] == prim_test}
    prim = 'M3' if 'M3' in by else 'M2'
    r = by[prim]; rd, _ = ref_drop(ref, prim, language)
    d, q = r['drop_within'], r['q_within']
    lines = [f'Primary test: {prim_test}, measure {prim}.']
    # positional controls: (i) re-deal signs across texts within position classes (first / middle / last);
    # (ii) shuffle only interior signs, scored on texts of >= 4 signs. Compared with what correct keys lose under the same nulls.
    ctl = []
    for kind, lab in [('posglobal', 'signs re-dealt across texts within first/middle/last position'), ('edgefixed_4plus', 'interior signs shuffled, texts of 4+ signs')]:
        dk, qk = r.get(f'drop_{kind}'), r.get(f'q_{kind}'); rk = ref_drop(ref, prim, language, kind=kind)[0]
        if dk is not None: ctl.append((lab, dk, qk, rk))
    weak_ctl = [c for c in ctl if c[2] >= 0.05 or (c[3] is not None and c[1] < 0.5 * c[3])]
    if d <= 0 or q >= 0.05:
        head = 'NO SUPPORT FROM SIGN ORDER'
        how = 'reads the shuffled inscriptions as well as or better than the real ones' if d <= 0 else 'shows no statistically reliable advantage for the real sign order'
        lines.append(f'The proposal {how} (real {r["real"]:.3f} vs within-text shuffled {r["within_mean"]:.3f}; drop {d:+.3f}, BH q = {q:.3g}).')
        if rd is not None: lines.append(f'Correct keys for real Sanskrit/Akkadian at the same text lengths lose at least {rd:+.3f} on this measure under the same shuffle (positive control).')
        lines.append('This does not show that every value in the proposal is wrong. It shows that this test gives no evidence that the proposal reads the inscriptions.')
    elif (rd is not None and d < 0.5 * rd) or weak_ctl:
        head = 'WEAK: ORDER EFFECT SMALLER THAN A CORRECT KEY OR LARGELY POSITIONAL'
        lines.append(f'Real sign order helps (drop {d:+.3f}, q = {q:.3g}; correct keys lose at least {rd:+.3f} under the same shuffle).')
        for lab, dk, qk, rk in ctl:
            lines.append(f'Positional control ({lab}): drop {dk:+.3f} (q = {qk:.3g})' + (f'; correct keys lose at least {rk:+.3f} under this control.' if rk is not None else '.'))
        lines.append('Order effects that shrink under the positional controls come from the script\'s positional habits (some signs mostly stand first or last, and a reading can give those signs word-initial or word-final forms) rather than from reading the sequence. This is not evidence of a decipherment.')
    else:
        head = 'PASSES THIS TEST'
        lines.append(f'Real sign order matters about as much as for a correct key (drop {d:+.3f}, q = {q:.3g}; positive-control minimum {rd:+.3f}), and the effect survives the positional controls: '
                     + '; '.join(f'{lab}: {dk:+.3f} (q = {qk:.3g}; correct keys at least {rk:+.3f})' for lab, dk, qk, rk in ctl) + '.')
        lines.append('Passing is necessary, not sufficient. Next checks: inscriptions not used to build the proposal (new finds, held-out sites), independent review of the readings, and agreement with archaeological context.')
    for m in sorted(by):
        if by[m]['real'] >= 0.95: lines.append(f'Ceiling warning: {by[m]["real"]:.1%} of real texts already pass {m}. When almost anything passes, the measure cannot separate a right reading from a wrong one.')
    if 'permkey_mean' in r and r['real'] - r['permkey_mean'] < 0.02:
        lines.append(f'The same values given to the wrong signs score almost as well on {prim} ({r["permkey_mean"]:.3f} vs {r["real"]:.3f}), so the specific sign-value pairs carry little weight.')
    if res['mode'] == 'readings':
        lines.append('Readings mode: R2 shuffles the per-sign pieces of each published reading. The proponent could adjust each real reading (word division, sandhi, vowels) to fit its neighbours, and shuffled pieces get no such adjustment, so R2 mostly measures how fluent the readings are. R2m checks this: the same readings re-cut against a random other inscription. R3 is the fair test: the values the readings actually give each sign are learned from 80% of inscriptions and read the other 20% (held out) mechanically.')
    return dict(label=head, primary_test=prim_test, primary_measure=prim, text=lines)

def report_md(res):
    v = res['verdict']; L = [f"# Shuffle benchmark: {res['name']}", '', f"**Verdict: {v['label']}**", '']
    L += [f'- {x}' for x in v['text']]
    L += ['', f"Mode: {res['mode']}; language: {res['language']}; lexicon: {res['lexicon']} ({res['lexicon_size']} words; length-stratified subsample {res['lexicon_lm_size']}); "
          f"mean signs per text: {res['mean_signs_per_text']}; shuffles: {res['n_shuffles']} per null (R3b: a quarter).", '']
    if 'fluency' in res: L += [f"Fluency (descriptive, no null): complete vidyut parse of the readings as written {res['fluency']['M3_as_written']:.3f}; with word spaces removed {res['fluency']['M3_unsegmented']:.3f}.", '']
    for k in [k for k in res if k.endswith('_info')]: L += [f"{k[:-5]}: {res[k]}"]
    L += ['', '| Test | Measure | n | Real | Within-shuffle (95% range) | Drop | q | Positional re-deal drop | q | Interior-only drop, 4+ signs | q | Global shuffle drop | q | Permuted key | q |', '|' + '---|' * 16]
    f = lambda r, k, fmt: (format(r[k], fmt) if r.get(k) is not None else '–')
    for r in res['results']:
        L.append(f"| {r['test']} | {r['measure']} | {r['n_texts']} | {r['real']:.3f} | {r['within_mean']:.3f} ({r['within_95']}) | {r['drop_within']:+.3f} | {r['q_within']:.3g} | "
                 f"{f(r, 'drop_posglobal', '+.3f')} | {f(r, 'q_posglobal', '.3g')} | {f(r, 'drop_edgefixed_4plus', '+.3f')} | {f(r, 'q_edgefixed_4plus', '.3g')} | {r['drop_global']:+.3f} | {r['q_global']:.3g} | "
                 + (f"{r['permkey_mean']:.3f} | {r['q_permkey']:.3g} |" if 'permkey_mean' in r else '– | – |'))
    L += ['', 'Positive control (correct keys, word-aligned texts of about 4.2 signs; positive_control/outputs/pc_summary.csv and pc_positional_nulls.csv):', '',
          '| Measure | Corpus | Key | Real | Within-shuffle | Drop | Positional re-deal drop | Interior-only drop, 4+ signs |', '|---|---|---|---|---|---|---|---|']
    g = lambda x, k: (f"{x[k]:+.3f}" if x.get(k) is not None else '–')
    for m, rows in res['positive_control_reference'].items():
        for x in rows: L.append(f"| {m} | {x['corpus']} | {x['key']} | {x['real']:.3f} | {x['within']:.3f} | {x['drop_within']:+.3f} | {g(x, 'drop_posglobal')} | {g(x, 'drop_edgefixed_4plus')} |")
    L += ['', 'M1: splits into words of the full lexicon. M2: same, 4,361-word length-stratified subsample. M3: complete vidyut Sanskrit parse. Positional re-deal: signs re-dealt across texts within first / middle / last position (keeps where each sign stands, destroys the sequences). Interior-only: first and last sign kept, middle shuffled, scored on texts of 4+ signs. '
          'p one-sided, (1 + #null >= real)/(N + 1); q = Benjamini-Hochberg across every test in this table. This benchmark never certifies a decipherment.']
    return '\n'.join(L) + '\n'

if __name__ == '__main__':
    main()
