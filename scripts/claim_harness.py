"""Claim-scoring harness (session 2). Tests Yajnadevam's sign key (lipi repo, commit fc8813a).
A: mechanical reproduction & consistency of published readings
B: fixed-key lexical segmentability, real vs shuffled sign order vs permuted key
C: key FITTING on 80% / held-out 20%: real vs shuffled corpora x Sanskrit vs other lexicons
D: free-parameter accounting
All numbers written to outputs/claims/*.json|csv. Usage: python claim_harness.py [A|B|C|D|all] [--quick]
"""
import sys, re, json, random, unicodedata, collections, os
from multiprocessing import Pool
import pandas as pd, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# session 6: INDUS_LEXSEED selects a replicate (control lexicons, length-matched subsamples, shuffles, hill-climb seeds);
# 0 = canonical run. INDUS_CLAIMS_OUT redirects outputs (used for the seed replicates).
LEXSEED = int(os.environ.get('INDUS_LEXSEED', '0'))
OUT = os.environ.get('INDUS_CLAIMS_OUT') or os.path.join(ROOT, 'outputs', 'claims'); os.makedirs(OUT, exist_ok=True)
LIPI = os.path.join(ROOT, 'data', 'lipi')
LEX = os.path.join(ROOT, 'data', 'lexicons')

# ---------- key & corpus ----------
def load_key():
    x = pd.read_csv(f'{LIPI}/xlits.csv', dtype=str, keep_default_na=False)
    m = {r.sign: {'xlit': r.xlit, 'canonical': r.canonical} for r in x.itertuples()}
    # replicate mkregex(): signs with empty xlit inherit from canonical decomposition (reversed)
    for s, e in m.items():
        if not e['xlit'] and e['canonical']:
            lit = ''.join(m[c]['xlit'] for c in reversed(e['canonical'].split('-')) if c in m)
            e['xlit'] = lit
    return {s: e['xlit'] for s, e in m.items()}

def mech(signs_reading_order, key):
    """replicates lipi index.vue xlitize(): inherent-a rule; returns (str, optional-mask list)"""
    items = []  # list of (char, optional)
    prev = None
    for i, s in enumerate(signs_reading_order):
        v = key.get(s, '')
        if i > 0:
            if re.match(r'^.*([iu]|an|as)$', prev) is None and re.match(r'^[aiu]$', v) is None and not prev.endswith('.'):
                items.append(('a', True))
        items += [(c, False) for c in v]
        prev = (prev or '') + v if i else v
    if re.match(r'.*([iu]|an|as)$', prev or '') is None:
        items.append(('a', True))
    return items

def load_corpus():
    d = pd.read_csv(f'{LIPI}/inscriptions.csv', dtype=str, keep_default_na=False)
    d['signs'] = d.text.apply(lambda t: list(reversed(re.findall(r'\d+', t))))  # reading order, as lipi xlitize()
    return d

# ---------- phonological reduction to a shared 3-vowel alphabet ----------
SLP_MAP = {'A':'a','I':'i','U':'u','e':'i','o':'u','E':'ai','O':'au','f':'r','F':'r','x':'l','X':'l',
           'K':'k','G':'g','N':'n','C':'c','J':'j','Y':'n','w':'t','W':'t','q':'d','Q':'d','R':'n',
           'T':'t','D':'d','P':'p','B':'b','S':'s','z':'s','M':'m','H':'','L':'l'}
ALPHA = set('aiukgcjtdnpbmyrlvsh')
def red_slp(s):
    return ''.join(SLP_MAP.get(c, c) for c in s if c in SLP_MAP or c in ALPHA)
LAT_MAP = {'e':'i','o':'u','y':'i','w':'v','f':'p','z':'s','x':'ks','q':'k','ş':'s','ç':'c','ğ':'g','ı':'i','ö':'u','ü':'u','ä':'a','å':'u','é':'i','á':'a','ó':'u','ő':'u','ű':'u','í':'i','ú':'u'}
def red_lat(w):
    w = w.lower()
    out = ''.join(LAT_MAP.get(c, c) for c in w)
    out = unicodedata.normalize('NFKD', out); out = ''.join(c for c in out if c in ALPHA)
    return out
def collapse(s):  # collapse geminates for symmetry
    return re.sub(r'(.)\1+', r'\1', s)

def skel(s):
    return re.sub('[aiu]', '', s)

# ---------- lexicons ----------
def lex_sanskrit():
    ws = set()
    for line in open(f'{LEX}/mw.txt', encoding='utf8'):
        m = re.match(r'<L>[^<]*<pc>[^<]*<k1>([^<]+)', line)
        if m: ws.add(collapse(red_slp(m.group(1))))
    return ws
def lex_freq(l):
    ws = set()
    for line in open(f'{LEX}/freq_{l}.txt', encoding='utf8'):
        w = line.split(' ')[0]
        if w.isalpha(): ws.add(collapse(red_lat(w)))
    return ws
def lex_pdr():
    d = pd.read_csv(f'{ROOT}/data/zenodo/dravidian_db_22682542/pdr_04.csv', dtype=str, keep_default_na=False)
    return {collapse(red_lat(re.sub(r'[^A-Za-zāīūēōḷṭṇṛḍṉṟḻñṅśṣ]', '', w))) for w in d.simplified}
def lex_random(ref, seed=0):
    """order-2 char Markov strings trained on ref, same size & length dist (a 'language' with no meaning)"""
    rng = random.Random(seed); ref = sorted(ref); tr = collections.defaultdict(collections.Counter)  # session 6: sorted (was list(set): hash-order dependent)
    for w in ref:
        w2 = '^^' + w + '$'
        for i in range(2, len(w2)): tr[w2[i-2:i]][w2[i]] += 1
    out = set()
    while len(out) < len(ref):
        ctx = '^^'; w = ''
        while len(w) < 15:
            c = rng.choices(list(tr[ctx]), weights=tr[ctx].values())[0]
            if c == '$': break
            w += c; ctx = ctx[1] + c
        if len(w) >= 2: out.add(w)
    return out
def sized(ws, n, seed=0, minlen=2, maxlen=10):
    ws = sorted(w for w in ws if minlen <= len(w) <= maxlen)
    rng = random.Random(seed)
    return set(rng.sample(ws, min(n, len(ws))))

def trie(ws):
    t = {}
    for w in ws:
        n = t
        for c in w: n = n.setdefault(c, {})
        n['$'] = 1
    return t

def segmentable(items, T):
    """items: list of (char, optional). True if whole sequence can be covered by lexicon words,
    optional chars may be dropped."""
    n = len(items); reach = [False]*(n+1); reach[0] = True
    for i in range(n):
        if not reach[i]: continue
        # walk trie; states = set of (pos, node)
        stack = [(i, T)]
        seen = set()
        while stack:
            p, node = stack.pop()
            if (p, id(node)) in seen: continue
            seen.add((p, id(node)))
            if '$' in node and p > i: reach[p] = True
            if p < n:
                c, opt = items[p]
                if c in node: stack.append((p+1, node[c]))
                if opt: stack.append((p+1, node))
    # optional trailing char may be dropped
    j = n
    while j > 0 and not reach[j] and items[j-1][1]: j -= 1
    return reach[n] or reach[j]

def red_items(items):
    out = []
    for c, o in items:
        r = SLP_MAP.get(c, c) if c in SLP_MAP else (c if c in ALPHA else '')
        for ch in r: out.append((ch, o))
    # collapse geminates
    res = []
    for c, o in out:
        if res and res[-1][0] == c: continue
        res.append((c, o))
    return res

# ---------- A ----------
def levenshtein(a, b):
    prev = list(range(len(b)+1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j]+1, cur[j-1]+1, prev[j-1]+(ca != cb)))
        prev = cur
    return prev[-1]

def part_A(seed=0):
    key = load_key(); d = load_corpus()
    pub = d[(d.sanskrit != '') & ~d.sanskrit.str.startswith('ref:')].copy()
    pub = pub[~pub.text.str.contains(r'000|999|/')]
    rng = random.Random(seed)
    rows = []
    allmech = [''.join(c for c, _ in mech(s, key)) for s in pub.signs]
    vals = list(key.values()); signs = list(key.keys())
    perm = vals[:]; rng.shuffle(perm); pkey = dict(zip(signs, perm))
    for (i, r), m in zip(pub.iterrows(), allmech):
        p = collapse(red_slp(r.sanskrit)); mm = collapse(red_slp(m))
        o = rng.choice(allmech); om = collapse(red_slp(o))
        pm = collapse(red_slp(''.join(c for c, _ in mech(r.signs, pkey))))
        ps, ms = skel(p), skel(mm)
        rows.append(dict(id=r.id, n=len(r.signs), pub=r.sanskrit, mech=m,
            skel_exact=ps == ms, skel_nld=levenshtein(ps, ms)/max(1, len(ps), len(ms)),
            base_other_nld=levenshtein(ps, skel(om))/max(1, len(ps), len(skel(om))),
            base_permkey_nld=levenshtein(ps, skel(pm))/max(1, len(ps), len(skel(pm))),
            len_pub=len(ps), len_mech=len(ms)))
    R = pd.DataFrame(rows); R.to_csv(f'{OUT}/A_reproduction.csv', index=False)
    # consonant substitution matrix via alignment (skeletons)
    sub = collections.Counter()
    for r in R.itertuples():
        a, b = skel(collapse(red_slp(r.mech))), skel(collapse(red_slp(r.pub)))
        # DP alignment backtrace
        D = [[0]*(len(b)+1) for _ in range(len(a)+1)]
        for i in range(len(a)+1): D[i][0] = i
        for j in range(len(b)+1): D[0][j] = j
        for i in range(1, len(a)+1):
            for j in range(1, len(b)+1):
                D[i][j] = min(D[i-1][j]+1, D[i][j-1]+1, D[i-1][j-1]+(a[i-1] != b[j-1]))
        i, j = len(a), len(b)
        while i or j:
            if i and j and D[i][j] == D[i-1][j-1]+(a[i-1] != b[j-1]): sub[(a[i-1], b[j-1])] += 1; i -= 1; j -= 1
            elif i and D[i][j] == D[i-1][j]+1: sub[(a[i-1], '-')] += 1; i -= 1
            else: sub[('-', b[j-1])] += 1; j -= 1
    S = pd.DataFrame([dict(key=k[0], pub=k[1], n=v) for k, v in sub.items()]).sort_values('n', ascending=False)
    S.to_csv(f'{OUT}/A_substitutions.csv', index=False)
    tot = S.n.sum(); ident = S[S.key == S.pub].n.sum()
    res = dict(n_published_readings=len(R), skel_exact_rate=float(R.skel_exact.mean()),
               mean_skel_nld=float(R.skel_nld.mean()), mean_nld_vs_random_other_text=float(R.base_other_nld.mean()),
               mean_nld_vs_permuted_key=float(R.base_permkey_nld.mean()),
               aligned_consonant_identity_rate=float(ident/tot), consonant_insertions=int(S[S.key=='-'].n.sum()),
               consonant_deletions=int(S[S.pub=='-'].n.sum()), substitutions=int(S[(S.key!=S.pub)&(S.key!='-')&(S.pub!='-')].n.sum()),
               aligned_pairs=int(tot), top_nonidentity=S[S.key != S.pub].head(15).to_dict('records'),
               by_length=R.groupby('n').skel_exact.agg(['mean', 'count']).reset_index().to_dict('records'))
    json.dump(res, open(f'{OUT}/A_summary.json', 'w'), indent=1)
    return res

# ---------- B / C shared ----------
def texts_for_tests(min_len=2, max_len=12):
    d = load_corpus()
    t = d[~d.text.str.contains(r'000|999|/') & (d.text.str.len() > 0)]
    seqs = [tuple(s) for s in t.signs if min_len <= len(s) <= max_len]
    return sorted(set(seqs))  # unique texts only

def shuffle_within(seqs, rng):
    out = []
    for s in seqs:
        s = list(s); rng.shuffle(s); out.append(tuple(s))
    return out
def shuffle_global(seqs, rng):
    pool = [x for s in seqs for x in s]; rng.shuffle(pool); out = []; k = 0
    for s in seqs: out.append(tuple(pool[k:k+len(s)])); k += len(s)
    return out

LEXCACHE = {}
def stratified(ws, counts, seed=0):
    rng = random.Random(seed); out = set()
    by = collections.defaultdict(list)
    for w in ws: by[len(w)].append(w)
    for l, n in counts.items():
        pool = sorted(by[l]); out.update(rng.sample(pool, min(n, len(pool))))
    return out
def get_lexicons():
    """length-matched lexicons: for each word length 2..10, every lexicon contributes the same number of
    (randomly sampled) distinct reduced forms = min over lexicons. Also keeps FULL MW for the claim's own condition."""
    if LEXCACHE: return LEXCACHE
    full = {'sanskrit_MW': lex_sanskrit(), 'proto_dravidian_PDR': lex_pdr(), 'finnish': lex_freq('fi'),
            'turkish': lex_freq('tr'), 'indonesian': lex_freq('id'), 'hungarian': lex_freq('hu'), 'english': lex_freq('en')}
    LEXCACHE['_full_MW'] = full['sanskrit_MW']
    mk = lex_random({w for w in full['sanskrit_MW'] if 2 <= len(w) <= 10}, seed=0 + 1000 * LEXSEED)
    full['markov_nonsense'] = mk
    counts = {l: min(sum(1 for w in v if len(w) == l) for v in full.values()) for l in range(2, 11)}
    for k, v in full.items(): LEXCACHE[k] = stratified(v, counts, seed=1000 * LEXSEED)
    LEXCACHE['_N'] = sum(counts.values()); LEXCACHE['_counts'] = counts
    return LEXCACHE

def score(seqs, key, T):
    return float(np.mean([segmentable(red_items(mech(s, key)), T) for s in seqs]))

def part_B(seed=0):
    key = load_key(); L = get_lexicons(); rng = random.Random(seed)
    seqs = texts_for_tests()
    signs = list(key); vals = [key[s] for s in signs]
    res = {'n_texts_unique': len(seqs), 'lexicon_size_each': L['_N'], 'length_counts': L['_counts'], 'full_MW_size': len(L['_full_MW']), 'rows': []}
    for lname in ['_full_MW'] + [k for k in L if not k.startswith('_')]:
        T = trie(L[lname])
        real = score(seqs, key, T)
        sw = [score(shuffle_within(seqs, random.Random(seed+i)), key, T) for i in range(3)]
        sg = [score(shuffle_global(seqs, random.Random(seed+10+i)), key, T) for i in range(3)]
        pk = []
        for i in range(3):
            v = vals[:]; random.Random(seed+20+i).shuffle(v); pk.append(score(seqs, dict(zip(signs, v)), T))
        res['rows'].append(dict(lexicon=lname, real=real, shuffled_within_mean=float(np.mean(sw)),
                                shuffled_global_mean=float(np.mean(sg)), permuted_key_mean=float(np.mean(pk))))
        print(res['rows'][-1], flush=True)
    json.dump(res, open(f'{OUT}/B_fixed_key_segmentability.json', 'w'), indent=1)
    return res

# ---------- C: fit keys ----------
def fit_run(args):
    lname, corpus_kind, seed, iters, topk = args
    L = get_lexicons(); T = trie(L[lname]); rng = random.Random(seed)
    key0 = load_key(); seqs = texts_for_tests(2, 8)
    if corpus_kind == 'shuffled_within': seqs = shuffle_within(seqs, random.Random(seed+100))
    elif corpus_kind == 'shuffled_global': seqs = shuffle_global(seqs, random.Random(seed+200))
    rng.shuffle(seqs); cut = int(.8*len(seqs)); train, test = seqs[:cut], seqs[cut:]
    freq = collections.Counter(x for s in train for x in s)
    top = [s for s, _ in freq.most_common(topk)]
    signs = list(key0); vals = [key0[s] for s in signs]; rng.shuffle(vals); key = dict(zip(signs, vals))
    inv = collections.defaultdict(list)
    for i, s in enumerate(train):
        for x in set(s): inv[x].append(i)
    cur = [segmentable(red_items(mech(s, key)), T) for s in train]; tot = sum(cur)
    pool = [v for v in vals if v]  # value inventory = Yajnadevam's own value multiset
    for it in range(iters):
        a = rng.choice(top)
        if rng.random() < .5:
            b = rng.choice(top); newa, newb = key[b], key[a]; changed = {a: newa, b: newb}
        else:
            changed = {a: rng.choice(pool)}
        old = {k: key[k] for k in changed}; key.update(changed)
        idx = set(); [idx.update(inv[k]) for k in changed]
        new = {i: segmentable(red_items(mech(train[i], key)), T) for i in idx}
        delta = sum(new[i] - cur[i] for i in idx)
        if delta >= 0:
            for i, v in new.items(): cur[i] = v
            tot += delta
        else: key.update(old)
    tr = tot/len(train); te = score(test, key, T)
    yk_tr, yk_te = score(train, key0, T), score(test, key0, T)
    return dict(lexicon=lname, corpus=corpus_kind, seed=seed, train=tr, heldout=te, n_train=len(train),
                n_test=len(test), yajnadevam_key_train=yk_tr, yajnadevam_key_heldout=yk_te, iters=iters, topk=topk)

def part_C(iters=2000, seeds=(0, 1), topk=150, procs=4):
    L = get_lexicons()
    jobs = [(l, c, s, iters, topk) for l in [k for k in L if not k.startswith('_')]
            for c in ['real', 'shuffled_within', 'shuffled_global'] for s in seeds]
    with Pool(procs) as p:
        rows = []
        for r in p.imap_unordered(fit_run, jobs):
            rows.append(r); print(r, flush=True)
            pd.DataFrame(rows).to_csv(f'{OUT}/C_fitted_keys.csv', index=False)
    pd.DataFrame(rows).sort_values(['lexicon', 'corpus', 'seed']).to_csv(f'{OUT}/C_fitted_keys.csv', index=False)  # session 6: stable row order
    return rows

def part_D():
    key = load_key()
    x = pd.read_csv(f'{LIPI}/xlits.csv', dtype=str, keep_default_na=False)
    d = load_corpus()
    pub = d[(d.sanskrit != '') & ~d.sanskrit.str.startswith('ref:')]
    used = collections.Counter(s for ss in d.signs for s in ss)
    res = dict(signs_in_key=len(x), signs_with_direct_value=int((x.xlit != '').sum()),
               signs_value_via_canonical_decomposition=int(((x.xlit == '') & (x.canonical != x.sign) & (x.canonical != '')).sum()),
               signs_noncanonical=int((x.canonical != x.sign).sum()),
               distinct_values=int(len(set(v for v in key.values() if v))),
               sign_types_in_corpus=len(used),
               sign_types_in_corpus_with_value=int(sum(1 for s in used if key.get(s))),
               published_readings_nonref=len(pub), ref_rows=int(d.sanskrit.str.startswith('ref:').sum()),
               value_length_dist=collections.Counter(len(v) for v in key.values() if v).most_common(),
               notes='Additional unquantified freedoms: optional inherent-a (regex "a?"), key letter -> multiple published phonemes (see A_substitutions), word segmentation and sandhi choice per reading, choice of dictionary (MW) sense.')
    json.dump(res, open(f'{OUT}/D_free_parameters.json', 'w'), indent=1, default=str)
    return res

if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    quick = '--quick' in sys.argv
    if what in ('A', 'all'): print(json.dumps(part_A(), indent=1)[:3000])
    if what in ('D', 'all'): print(json.dumps(part_D(), indent=1, default=str))
    if what in ('B', 'all'): part_B(seed=100 * LEXSEED)
    if what in ('C', 'all'): part_C(iters=300 if quick else 2000, seeds=(2 * LEXSEED,) if quick else (2 * LEXSEED, 2 * LEXSEED + 1))
