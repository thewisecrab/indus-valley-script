"""Score completed rater sheets against the answer key (run only after ANSWER_KEY.csv is released and its SHA-256 checked).
Usage: python rater_kit/score_raters.py ANSWER_KEY.csv sheet1.csv [sheet2.csv ...]"""
import sys, hashlib, collections
import pandas as pd
key_path, sheets = sys.argv[1], sys.argv[2:]
want = open(__file__.replace('score_raters.py', 'ANSWER_KEY.sha256')).read().split()[0]
got = hashlib.sha256(open(key_path, 'rb').read()).hexdigest(); assert got == want, 'answer key does not match the published SHA-256'
K = pd.read_csv(key_path, dtype=str, keep_default_na=False).set_index('item')
J = [c for c in pd.read_csv(sheets[0], dtype=str, nrows=0).columns if c.startswith('judgement')][0]
norm = lambda v: {'same sign': 'match', 'variant of same sign': 'match', 'different sign': 'no', 'cannot tell': 'unsure'}.get(v.strip().lower(), 'unsure')
def kappa(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n; ca, cb = collections.Counter(a), collections.Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2; return (po - pe) / (1 - pe) if pe < 1 else float('nan')
rows, allj = [], {}
for s in sheets:
    S = pd.read_csv(s, dtype=str, keep_default_na=False).set_index('item'); j = S[J].map(norm); allj[s] = j
    dec = K.index[K.kind == 'decoy_random_W']; lnk = K.index[K.kind == 'carlson_link']
    ai = K.loc[lnk, 'ai_judgement'].map(lambda v: 'match' if v in ('match', 'plausible') else 'no' if v.startswith('doubtful') else 'unsure')
    rows.append(dict(sheet=s, decoy_accuracy=float((j[dec] == 'no').mean()), agree_carlson=float((j[lnk] == 'match').mean()),
                     agree_ai=float((j[lnk] == ai).mean()), kappa_vs_ai=kappa(list(j[lnk]), list(ai))))
R = pd.DataFrame(rows); print(R.to_string())
if len(sheets) >= 2:
    cats = ['match', 'no', 'unsure']; M = pd.DataFrame({c: [sum(allj[s][i] == c for s in sheets) for i in K.index] for c in cats}); n = len(sheets)
    P = ((M ** 2).sum(1) - n) / (n * (n - 1)); pj = M.sum() / (n * len(M)); Pe = (pj ** 2).sum()
    print('Fleiss kappa', round((P.mean() - Pe) / (1 - Pe), 3))
    ok = R.agree_ai.median() >= .8 and R.decoy_accuracy.median() >= .8
    print('AI-made check', 'CONFIRMED' if ok else 'NOT confirmed', '(thresholds: median agreement with AI >= 0.8 and median decoy accuracy >= 0.8, >= 2 raters)')
