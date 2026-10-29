"""Session 7: extends emblem_tests.py with SHORT REAL TEXTS (true text boundaries) as linguistic comparanda, and tests
how stable the language-vs-non-linguistic classification of the Indus corpora is.
New linguistic comparanda (both openly licensed):
  - Epigraphic Database Heidelberg (EDH) Latin inscriptions, CC BY-SA 4.0 (edh_data_text.csv, field atext with the
    editors' expansions removed, i.e. words as abbreviated on the object): (a) owner's/maker's inscriptions on objects
    (EDH genre 'titpossfabr': stamps on tiles, amphorae, lamps, etc.), as words and as letters; (b) all genres, words.
    Only texts without lacunae or uncertain readings are kept.
  - Wikipedia article titles (fi, ta, sa; all-titles-in-ns0 dumps, CC BY-SA 4.0), as words.
Non-linguistic systems, Indus corpora and synthetic generators are as in emblem_tests.py (same measures, same
800-token budget, 50 subsamples). We found no further openly licensed non-linguistic sequence corpus; The Session's
tune data were not used because their licence forbids processing with large-language-model tools.
Stability: three classifiers (nearest centroid, 1-NN, 3-NN; z-scored measures) x six measure sets (all five, and
each one dropped) x three reference sets (window comparanda only, short texts only, both), each with
leave-one-system-out accuracy and the Indus assignment; plus 500 random drops of 25% of the known systems.
Output: outputs/emblem/emblem_measures_v2.csv, emblem_stability.json"""
import os, sys, re, gzip, json, random, itertools
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import emblem_tests as E
ROOT = E.ROOT; OUT = E.OUT; D = f'{ROOT}/data/comparanda_short'
M = ['Hcond_ratio', 'edge_MI_gain', 'rep_rate', 'zipf_slope', 'types_800']
def edh():
    d = pd.read_csv(f'{D}/edh_data_text.csv', dtype=str, usecols=['hd_nr', 'i_gattung', 'atext']).dropna(subset=['atext'])
    d = d[~d.atext.str.contains(r'[\[\]<>#?!{}]|---|\+')]
    def toks(t):
        t = re.sub(r'\([^)]*\)', '', t); t = re.sub(r'\s*/+\s*', lambda m: ' ' if ' ' in m.group(0) else '', t)
        return tuple(w.lower() for w in re.findall(r'[A-Za-z]+', t))
    d['w'] = d.atext.map(toks); d = d[d.w.map(len) >= 1]
    st = d[d.i_gattung.fillna('').str.startswith('titpossfabr')]
    rng = random.Random(5); allw = list(d.w); rng.shuffle(allw)
    return {'L Latin owner/maker inscriptions (EDH) words': list(st.w), 'L Latin owner/maker inscriptions (EDH) letters': [tuple(''.join(w)) for w in st.w],
            'L Latin inscriptions, all genres (EDH) words': allw[:6000]}
def titles():
    out = {}
    for l in ['fi', 'ta', 'sa']:
        saved = f'{ROOT}/data_open/comparanda_short/wiki_titles_{l}.txt'   # the exact sample used (dumps change over time)
        if os.path.exists(saved):
            out[f'L Wikipedia titles {l} words'] = [tuple(x.rstrip('\n').split(' ')) for x in open(saved, encoding='utf-8') if x.strip()]; continue
        p = f'{D}/{l}_titles.gz'
        if not os.path.exists(p): continue
        T = [tuple(w.lower() for w in re.split(r'_+', x.strip()) if w) for x in gzip.open(p, 'rt', encoding='utf-8') if x.strip() and x.strip() != 'page_title']
        T = [t for t in T if t]; random.Random(6).shuffle(T); out[f'L Wikipedia titles {l} words'] = T[:6000]
        os.makedirs(os.path.dirname(saved), exist_ok=True); open(saved, 'w', encoding='utf-8').write(''.join(' '.join(t) + '\n' for t in T[:6000]))
    return out
def classify(Z, K, test, cfg):
    kind, k = cfg
    ref = Z.loc[K.system]; g = K.group.values
    if kind == 'centroid':
        cen = {c: ref[g == c].mean().values for c in set(g)}; return min(cen, key=lambda c: np.linalg.norm(Z.loc[test].values - cen[c]))
    dist = np.linalg.norm(ref.values - Z.loc[test].values, axis=1); nn = np.argsort(dist)[:k]
    v = pd.Series(g[nn]).value_counts(); return v.index[0] if (len(v) == 1 or v.iloc[0] > v.iloc[1]) else g[nn[0]]
def main():
    old = pd.read_csv(f'{OUT}/emblem_measures.csv')
    new = {}; new.update(edh()); new.update(titles())
    rows = []
    for name, T in new.items():
        reps = [E.measures(E.sub(T, random.Random(i)), random.Random(100 + i)) for i in range(E.REPS)]
        df = pd.DataFrame(reps); row = dict(system=name, group='linguistic (short real texts)', n_texts_total=len(T), tokens_total=sum(len(s) for s in T))
        for c in df.columns:
            row[c] = round(float(df[c].mean()), 4); row[c + '_lo'] = round(float(df[c].quantile(.025)), 4); row[c + '_hi'] = round(float(df[c].quantile(.975)), 4)
        rows.append(row); print(name, {k: row[k] for k in df.columns}, flush=True)
    old.loc[old.group == 'linguistic', 'group'] = 'linguistic (running-text windows)'
    R = pd.concat([old, pd.DataFrame(rows)], ignore_index=True); R.to_csv(f'{OUT}/emblem_measures_v2.csv', index=False)
    IND = ['Indus M77 (dedup)', 'Indus ICIT (dedup)']; SYN = list(R.system[R.group == 'synthetic non-linguistic'])
    refsets = {'windows': ['non-linguistic (real)', 'linguistic (running-text windows)'], 'short_texts': ['non-linguistic (real)', 'linguistic (short real texts)'],
               'both': ['non-linguistic (real)', 'linguistic (running-text windows)', 'linguistic (short real texts)']}
    msets = {'all5': M, **{f'drop_{m}': [x for x in M if x != m] for m in M}}
    cfgs = {'nearest_centroid': ('centroid', 0), '1-NN': ('knn', 1), '3-NN': ('knn', 3)}
    res = []; R2 = R.set_index('system')
    for rs, groups in refsets.items():
        K = R[R.group.isin(groups)].reset_index(drop=True).copy(); K['group'] = np.where(K.group.str.startswith('linguistic'), 'linguistic', 'non-linguistic')
        for ms, cols in msets.items():
            Z = (R2[cols] - K.set_index('system')[cols].mean()) / K.set_index('system')[cols].std()
            for cn, cfg in cfgs.items():
                acc = sum(classify(Z, K.drop(i), K.system[i], cfg) == K.group[i] for i in range(len(K)))
                res.append(dict(reference=rs, measures=ms, classifier=cn, n_known=len(K), loso_correct=int(acc),
                                **{s: classify(Z, K, s, cfg) for s in IND + SYN}))
    S = pd.DataFrame(res)
    # random 25% drops of known systems, all5 + both + each classifier
    K = R[R.group.isin(refsets['both'])].reset_index(drop=True).copy(); K['group'] = np.where(K.group.str.startswith('linguistic'), 'linguistic', 'non-linguistic')
    rng = np.random.default_rng(9); drops = {s: {c: [] for c in cfgs} for s in IND}
    for _ in range(500):
        keep = K.drop(rng.choice(len(K), len(K) // 4, replace=False)).reset_index(drop=True)
        if keep.group.nunique() < 2: continue
        Z = (R2[M] - keep.set_index('system')[M].mean()) / keep.set_index('system')[M].std()
        for c, cfg in cfgs.items():
            for s in IND: drops[s][c].append(classify(Z, keep, s, cfg))
    summ = dict(n_known_systems={rs: int(R.group.isin(g).sum()) for rs, g in refsets.items()},
                n_configs=len(S), share_of_configs_assigning_linguistic={s: round(float((S[s] == 'linguistic').mean()), 3) for s in IND + SYN},
                loso_accuracy_range=[int(S.loso_correct.min()), int(S.loso_correct.max())], loso_accuracy_by_reference={rs: f"{int(g.loso_correct.min())}-{int(g.loso_correct.max())} of {int(g.n_known.iloc[0])}" for rs, g in S.groupby('reference')},
                all5_both=S[(S.measures == 'all5') & (S.reference == 'both')].to_dict('records'),
                random_drop_25pct_share_linguistic={s: {c: round(float(np.mean([x == 'linguistic' for x in v])), 3) for c, v in d.items()} for s, d in drops.items()},
                ranges={m: {g: [float(R[R.group == g][m].min()), float(R[R.group == g][m].max())] for g in ['non-linguistic (real)', 'linguistic (running-text windows)', 'linguistic (short real texts)']} for m in M})
    S.to_csv(f'{OUT}/emblem_stability_configs.csv', index=False)
    json.dump(summ, open(f'{OUT}/emblem_stability.json', 'w'), indent=1, default=str); print(json.dumps({k: v for k, v in summ.items() if k != 'all5_both'}, indent=1, default=str))
if __name__ == '__main__':
    main()
