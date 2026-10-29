"""Numeral + W700 formula on tablets vs Harappan weight classes."""
import re, json, collections, os
import pandas as pd, numpy as np
from scipy.stats import chisquare
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = pd.read_csv(f'{ROOT}/data/lipi/inscriptions.csv', dtype=str, keep_default_na=False)
LONG = {'031': 1, '032': 2, '033': 3, '034': 4, '035': 5}
SHORT = {'001':1,'002':2,'003':3,'004':4,'005':5,'006':6,'007':7,'014':4,'015':5,'016':6,'017':7,'018':8,'019':9,'020':10}
c = collections.Counter(); bytype = collections.Counter(); sites = collections.Counter(); ex = collections.Counter()
for r in d.itertuples():
    s = list(reversed(re.findall(r'\d+', r.text)))
    for i, x in enumerate(s):
        if x != '700': continue
        nb = [s[j] for j in (i - 1, i + 1) if 0 <= j < len(s)]
        for y in nb:
            if y in LONG: c[('long', LONG[y])] += 1; bytype[r.type] += 1; sites[r.site] += 1; ex[r.text] += 1
            if y in SHORT: c[('short', SHORT[y])] += 1
tok700 = sum(len(re.findall(r'\b700\b', t)) for t in d.text)
long_vals = {k[1]: v for k, v in c.items() if k[0] == 'long'}
obs = np.array([long_vals.get(v, 0) for v in (2, 3, 4)])
res = dict(W700_tokens=tok700, numeral_adjacent_to_700=dict((f'{a}{b}', v) for (a, b), v in sorted(c.items())), types=dict(bytype.most_common(6)),
           sites=dict(sites.most_common(5)), top_texts=dict(ex.most_common(8)),
           chisq_uniform_2_3_4=dict(stat=float(chisquare(obs).statistic), p=float(chisquare(obs).pvalue)),
           binary_prediction='if values were binary weight multiples, 2 and 4 should dominate 3; observed long-stroke counts 2:%d 3:%d 4:%d' % tuple(obs),
           weight_classes='see anchors_summary.json: ratio classes 1,2,(8/3),4,8,16,32,64,...; no x3 class except 8/3 (12 weights)')
json.dump(res, open(f'{ROOT}/outputs/anchors/w700_vs_weights.json', 'w'), indent=1); print(json.dumps(res, indent=1))
