"""Session 6: language-vs-emblem battery. Compares the Indus corpora with
  (a) real NON-linguistic symbol systems: Sproat (2014) corpora (Apache-2.0; richardsproat.com/data/non-linguistic-symbols):
      Pictish symbols, Mesopotamian kudurru deity symbols, Vinca signs, Pennsylvania barn stars, totem poles,
      weather-icon sequences, Asian emoticons (document = text);
  (b) linguistic comparanda: Wikipedia text (scripts/fetch_wiki.py; English, Finnish, Sanskrit, Tamil), as words and as
      characters, cut into contiguous windows whose lengths follow the Indus (M77) length distribution;
  (c) synthetic non-linguistic generators fitted to Indus: memoryless unigram, positional slot (first/middle/last
      unigrams), and order-1 Markov.
Every system is subsampled to the same token budget (800, the size of the smallest real corpus) 50 times.
Measures (each vs the system's own within-text shuffle where marked):
  Hcond_ratio   bigram conditional entropy / within-text-shuffled value (order dependence)
  edge_MI_gain  I(sign; text-initial) + I(sign; text-final) minus the shuffled value, bits
  rep_rate      share of texts (>= 2 tokens) containing a repeated symbol
  zipf_slope    log-log rank-frequency slope, top 50 ranks
  types_800     symbol types per 800 tokens
  mean_len      mean text length (tokens)
Output: outputs/emblem/emblem_measures.csv, emblem_summary.json"""
import os, sys, glob, json, math, random, re, collections
import xml.etree.ElementTree as ET
import numpy as np, pandas as pd, regex
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, f'{ROOT}/scripts')
OUT = f'{ROOT}/outputs/emblem'; os.makedirs(OUT, exist_ok=True)
BUDGET, REPS = 800, 50
def indus():
    D = f'{ROOT}/data/joyboseroy_indus_decipher/data'
    m = pd.read_csv(f'{D}/m77_indusscript_real_corpus.csv', dtype=str).fillna('')
    m77 = list(dict.fromkeys(tuple(s.split()) for s, dmg in zip(m.sign_sequence, m.damaged) if dmg != 'True' and 'MSg0' not in s.split()))
    import claim_harness as C
    d = C.load_corpus(); d = d[~d.text.str.contains(r'000|999|/') & (d.text.str.len() > 0)]
    icit = list(dict.fromkeys(tuple(s) for s in d.signs))
    return {'Indus M77 (dedup)': m77, 'Indus ICIT (dedup)': icit}
def sproat():
    out = {}
    for f in sorted(glob.glob(f'{ROOT}/data/sproat_nonling/corpora/*.xml')):
        name = os.path.basename(f)[:-4]
        if name == 'IndusBarSeals': continue
        r = ET.parse(f).getroot(); T = []
        for d in r.iter('document'):
            s = tuple(x.findtext('title', '').strip() for x in d.iter('symbol'))
            if s: T.append(s)
        out[f'NL {name}'] = T
    return out
def linguistic(lengths, rng):
    out = {}
    for lang in ['en', 'fi', 'sa', 'ta']:
        p = f'{ROOT}/data/comparanda_text/wiki_{lang}.txt'
        if not os.path.exists(p): continue
        txt = open(p, encoding='utf-8').read()
        for unit in ['words', 'chars']:
            toks = [w.lower() for w in regex.findall(r'[\p{L}\p{M}]+', txt)] if unit == 'words' else [c for c in regex.findall(r'\X', txt) if regex.match(r'[\p{L}]', c)]
            T = []; i = 0
            while i < len(toks) and len(T) < 6000:
                L = rng.choice(lengths); T.append(tuple(toks[i:i + L])); i += L + rng.randint(0, 3)
            out[f'L {lang} {unit}'] = T
    return out
def synthetic(ref, rng, n=4000):
    lengths = [len(s) for s in ref]; uni = collections.Counter(x for s in ref for x in s)
    first = collections.Counter(s[0] for s in ref if len(s) > 1); last = collections.Counter(s[-1] for s in ref if len(s) > 1)
    mid = collections.Counter(x for s in ref for x in s[1:-1]); big = collections.defaultdict(collections.Counter)
    for s in ref:
        for a, b in zip(s, s[1:]): big[a][b] += 1
    draw = lambda c: rng.choices(list(c), weights=c.values())[0]
    mem = [tuple(draw(uni) for _ in range(rng.choice(lengths))) for _ in range(n)]
    def slot():
        L = rng.choice(lengths)
        if L == 1: return (draw(uni),)
        return (draw(first),) + tuple(draw(mid) if mid else draw(uni) for _ in range(L - 2)) + (draw(last),)
    def markov():
        L = rng.choice(lengths); s = [draw(first) if L > 1 else draw(uni)]
        while len(s) < L: s.append(draw(big[s[-1]]) if big[s[-1]] else draw(uni))
        return tuple(s)
    return {'SYN memoryless (Indus unigrams)': mem, 'SYN positional slots (Indus)': [slot() for _ in range(n)], 'SYN order-1 Markov (Indus)': [markov() for _ in range(n)]}
def sub(T, rng):
    T = list(T); rng.shuffle(T); out = []; c = 0
    for s in T:
        if c >= BUDGET: break
        out.append(s); c += len(s)
    return out
def wshuf(T, rng): return [tuple(rng.sample(s, len(s))) for s in T]
def hcond(T):
    big = collections.Counter(); fst = collections.Counter()
    for s in T:
        for a, b in zip(s, s[1:]): big[(a, b)] += 1; fst[a] += 1
    n = sum(big.values()); return -sum(c / n * math.log2(c / fst[a]) for (a, b), c in big.items()) if n else float('nan')
def mi(pairs):
    n = len(pairs); 
    if not n: return 0.0
    px = collections.Counter(a for a, _ in pairs); py = collections.Counter(b for _, b in pairs); pxy = collections.Counter(pairs)
    return sum(c / n * math.log2(c * n / (px[a] * py[b])) for (a, b), c in pxy.items())
def edge(T):
    T = [s for s in T if len(s) >= 2]
    return mi([(x, i == 0) for s in T for i, x in enumerate(s)]) + mi([(x, i == len(s) - 1) for s in T for i, x in enumerate(s)])
def zipf(T):
    c = np.array(sorted(collections.Counter(x for s in T for x in s).values(), reverse=True)[:50], float)
    if len(c) < 5: return float('nan')
    return float(np.polyfit(np.log(np.arange(1, len(c) + 1)), np.log(c), 1)[0])
def measures(T, rng):
    sh = [wshuf(T, rng) for _ in range(3)]
    h = hcond(T); hs = np.nanmean([hcond(x) for x in sh])
    two = [s for s in T if len(s) >= 2]
    return dict(Hcond_ratio=h / hs if hs else float('nan'), edge_MI_gain=edge(T) - np.mean([edge(x) for x in sh]),
                rep_rate=float(np.mean([len(set(s)) < len(s) for s in two])) if two else float('nan'), zipf_slope=zipf(T),
                types_800=len({x for s in T for x in s}), mean_len=float(np.mean([len(s) for s in T])))
def main():
    rng = random.Random(0); systems = indus(); lengths = [len(s) for s in systems['Indus M77 (dedup)']]
    systems.update(sproat()); systems.update(linguistic(lengths, rng)); systems.update(synthetic(systems['Indus M77 (dedup)'], rng))
    rows = []
    for name, T in systems.items():
        reps = [measures(sub(T, random.Random(i)), random.Random(100 + i)) for i in range(REPS)]
        df = pd.DataFrame(reps); grp = name.split(' ')[0] if name.split(' ')[0] in ('NL', 'L', 'SYN') else 'Indus'
        row = dict(system=name, group={'NL': 'non-linguistic (real)', 'L': 'linguistic', 'SYN': 'synthetic non-linguistic', 'Indus': 'Indus'}[grp],
                   n_texts_total=len(T), tokens_total=sum(len(s) for s in T))
        for c in df.columns:
            row[c] = round(float(df[c].mean()), 4); row[c + '_lo'] = round(float(df[c].quantile(.025)), 4); row[c + '_hi'] = round(float(df[c].quantile(.975)), 4)
        rows.append(row); print(name, {k: row[k] for k in df.columns}, flush=True)
    R = pd.DataFrame(rows); R.to_csv(f'{OUT}/emblem_measures.csv', index=False)
    M = ['Hcond_ratio', 'edge_MI_gain', 'rep_rate', 'zipf_slope', 'types_800']
    summ = {}
    for ind in ['Indus M77 (dedup)', 'Indus ICIT (dedup)']:
        x = R.set_index('system').loc[ind]; s = {}
        for m in M:
            nl = R[R.group == 'non-linguistic (real)'][m]; li = R[R.group == 'linguistic'][m]
            s[m] = dict(indus=float(x[m]), nonling_range=[float(nl.min()), float(nl.max())], ling_range=[float(li.min()), float(li.max())],
                        inside_nonling=bool(nl.min() <= x[m] <= nl.max()), inside_ling=bool(li.min() <= x[m] <= li.max()))
        summ[ind] = s
    # leave-one-system-out nearest-centroid classification on z-scored measures (real NL vs L only)
    K = R[R.group.isin(['non-linguistic (real)', 'linguistic'])].reset_index(drop=True)
    Z = (R[M] - K[M].mean()) / K[M].std()
    correct = 0
    for i in range(len(K)):
        tr = K.drop(i); zi = Z.loc[R.system == K.system[i]].values[0]
        cen = {g: Z.loc[R.system.isin(tr[tr.group == g].system)].mean().values for g in tr.group.unique()}
        pred = min(cen, key=lambda g: np.linalg.norm(zi - cen[g])); correct += pred == K.group[i]
    cen = {g: Z.loc[R.system.isin(K[K.group == g].system)].mean().values for g in K.group.unique()}
    cls = {s: min(cen, key=lambda g: np.linalg.norm(Z.loc[R.system == s].values[0] - cen[g])) for s in R.system if s not in set(K.system)}
    summ['nearest_centroid'] = dict(loso_accuracy_on_known_systems=f'{correct}/{len(K)}', assignment_of_other_systems=cls, measures=M)
    json.dump(summ, open(f'{OUT}/emblem_summary.json', 'w'), indent=1); print(json.dumps(summ, indent=1))
def mi_decay():
    """MI between symbols d = 1..4 apart, within texts of >= 6 tokens, minus the within-text-shuffled MI (20 shuffles).
    Only systems with >= 100 such texts. A decay that stays above 0 beyond d = 1 indicates longer-range dependency."""
    rng = random.Random(0); systems = indus(); lengths = [len(s) for s in systems['Indus M77 (dedup)'] if len(s) >= 6]
    systems.update(sproat()); systems.update(linguistic(lengths, rng)); rows = []
    for name, T in systems.items():
        L = [s for s in T if len(s) >= 6]
        if len(L) < 100: continue
        L = L[:400] if len(L) > 400 else L
        row = dict(system=name, n_texts=len(L))
        for dd in range(1, 5):
            obs = mi([(s[i], s[i + dd]) for s in L for i in range(len(s) - dd)])
            nul = [mi([(s[i], s[i + dd]) for s in wshuf(L, random.Random(k)) for i in range(len(s) - dd)]) for k in range(20)]
            row[f'MI_gain_d{dd}'] = round(obs - float(np.mean(nul)), 4); row[f'MI_gain_d{dd}_z'] = round((obs - np.mean(nul)) / (np.std(nul) or 1e-9), 1)
        rows.append(row); print(row, flush=True)
    pd.DataFrame(rows).to_csv(f'{OUT}/emblem_mi_decay.csv', index=False)
if __name__ == '__main__':
    main(); mi_decay()
