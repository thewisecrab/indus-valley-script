"""Digit-template OCR, stage 2/3: label glyph rows with RapidOCR tokens (valid 4-digit text no. present in M77 +
6-digit domain-valid code on the same row), train kNN digit classifier, evaluate on held-out PAGES, decode all rows,
validate (M77 membership, monotonic order, single-sign check), write outputs/m77_codes_digitocr.csv."""
import os, glob, pickle, csv, collections, json, re
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
m77 = collections.defaultdict(list)
for r in csv.DictReader(open(f'{ROOT}/data/joyboseroy_indus_decipher/data/m77_indusscript_real_corpus.csv')):
    m77[int(r['inscription_id'].split('.')[0])].append(len(r['sign_sequence'].split()))
valid = lambda c: len(c) == 6 and c[0] in '12345679' and c[1] in '0123456' and c[4] in '01239' and c[5] in '0123459'
rows = []
for f in sorted(glob.glob(f'{ROOT}/data/books/m77_digit/p*.pkl')): rows += pickle.load(open(f, 'rb'))
def ocr_tokens(p):
    out = []
    fn = f'{ROOT}/data/books/ocr_m77/p{p:04d}.txt'
    if not os.path.exists(fn): return out
    for line in open(fn):
        x, y, t, c = line.rstrip('\n').split('\t'); t = t.replace(' ', '')
        if re.fullmatch(r'\d{10}', t): out += [(int(x), int(y), t[:4]), (int(x) + 210, int(y), t[4:])]
        else: out.append((int(x), int(y), t))
    return out
feat = lambda g: np.concatenate([g[1].ravel(), [g[2] / 40, g[3] / 40]])
X, Y, PG = [], [], []
tokcache = {}
for row in rows:
    p = row['page']; toks = tokcache.setdefault(p, ocr_tokens(p))
    near = [t for t in toks if abs(t[1] - row['y']) < 30]
    num = [t[2] for t in near if re.fullmatch(r'\d{4}', t[2]) and int(t[2]) in m77 and t[0] < row['xnum'] + 150]
    code = [t[2] for t in near if re.fullmatch(r'\d{6}', t[2]) and valid(t[2])]
    if len(row['glyphs']) == 10 and len(num) == 1 and len(code) == 1 and (num[0] + code[0]).isascii():
        for g, ch in zip(row['glyphs'], num[0] + code[0]): X.append(feat(g)); Y.append(ch); PG.append(p)
X, Y, PG = np.array(X), np.array(Y), np.array(PG, dtype=int); print('pages', collections.Counter(PG % 2))
print('labelled glyphs', len(Y), collections.Counter(Y))
# held-out evaluation: train on even pages, test on odd and vice versa
acc = []
for par in (0, 1):
    tr, te = PG % 2 != par, PG % 2 == par
    clf = KNeighborsClassifier(3).fit(X[tr], Y[tr]); acc.append((clf.predict(X[te]) == Y[te]).mean())
print('held-out-page digit accuracy (vs RapidOCR labels)', [round(a, 4) for a in acc])
clf = KNeighborsClassifier(3).fit(X, Y)
# pass 1: predict all rows
pre = []
for row in rows:
    gl = row['glyphs']
    if not gl: continue
    F_ = np.array([feat(g) for g in gl]); pred = ''.join(clf.predict(F_)); prob = clf.predict_proba(F_).max(1).min()
    xs = [g[0] for g in gl]; num = code = None
    if len(gl) == 10: num, code = pred[:4], pred[4:]
    elif len(gl) == 6 and xs[0] > (row['xnum'] + 150) * 2: code = pred
    elif len(gl) == 4 and xs[0] < (row['xnum'] + 150) * 2: num = pred
    else: continue
    pre.append(dict(page=row['page'], y=row['y'], num=int(num) if num and int(num) in m77 else None, code=code, prob=float(prob)))
# pass 2: longest strictly increasing subsequence of recognised numbers (document order) -> accepted numbers
idx = [i for i, r in enumerate(pre) if r['num'] is not None]; vals = [pre[i]['num'] for i in idx]
import bisect
tails, tidx, prev = [], [], [-1] * len(vals)
for k, v in enumerate(vals):
    j = bisect.bisect_left(tails, v)
    if j == len(tails): tails.append(v); tidx.append(k)
    else: tails[j] = v; tidx[j] = k
    prev[k] = tidx[j-1] if j else -1
keep = set(); k = tidx[-1]
while k != -1: keep.add(idx[k]); k = prev[k]
out = []; last = None
for i, r in enumerate(pre):
    if r['num'] is not None:
        if i in keep: last = r['num']; inherited = False
        else: continue
    else:
        if r['code'] is None: continue
        inherited = True
    if r['code'] is None or last is None: continue
    out.append(dict(page=r['page'], y=r['y'], textnum=last, code=r['code'], inherited=inherited, valid=valid(r['code']), min_knn_prob=round(r['prob'], 3)))
V = [r for r in out if r['valid']]
own = {r['textnum'] for r in V if not r['inherited']}
print('decoded rows', len(out), 'valid', len(V), 'texts with own code', len(own), 'of', len(m77))
# agreement with RapidOCR codes
ro = {}
for r in csv.DictReader(open(f'{ROOT}/outputs/m77_codes_ocr_valid.csv')):
    if r['inherited'] == 'False': ro.setdefault(int(r['textnum']), r['code'])
both = [(r['code'], ro[r['textnum']]) for r in V if not r['inherited'] and r['textnum'] in ro]
agree = np.mean([a == b for a, b in both]); print('agreement with RapidOCR on overlap', len(both), round(float(agree), 4))
# single-sign check
tp = fp = fn = tn = 0
for r in V:
    if r['inherited'] or r['code'][1] != '0' or r['code'][4] != '0': continue
    L = m77.get(r['textnum'])
    if not L or len(L) != 1: continue
    s1 = L[0] == 1; d3 = r['code'][5] == '3'
    tp += s1 and d3; fp += d3 and not s1; fn += s1 and not d3; tn += (not s1) and (not d3)
print('single-sign check', dict(tp=tp, fp=fp, fn=fn, tn=tn))
# merge: prefer digit-OCR; fall back to RapidOCR for texts the digit pass missed
merged = {r['textnum']: r for r in V if not r['inherited']}
added = 0
for t, c in ro.items():
    if t not in merged: merged[t] = dict(page=None, y=None, textnum=t, code=c, inherited=False, valid=True, min_knn_prob=None, src='rapidocr'); added += 1
for r in merged.values(): r.setdefault('src', 'digit_knn')
with open(f'{ROOT}/outputs/m77_codes_digitocr.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=['textnum', 'code', 'src', 'page', 'y', 'min_knn_prob', 'inherited', 'valid']); w.writeheader()
    for t in sorted(merged): w.writerow({k: merged[t].get(k) for k in w.fieldnames})
with open(f'{ROOT}/outputs/m77_codes_digitocr_allrows.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
summ = dict(labelled_glyphs=int(len(Y)), heldout_page_acc=[float(a) for a in acc], decoded_rows=len(out), valid_rows=len(V), texts_own_code_digit=len(own),
            merged_texts_with_code=len(merged), rapidocr_fallback_added=added, agreement_with_rapidocr=float(agree), n_overlap=len(both), single_sign_check=dict(tp=tp, fp=fp, fn=fn, tn=tn), m77_texts=len(m77))
json.dump(summ, open(f'{ROOT}/outputs/m77_codes_digitocr_summary.json', 'w'), indent=1); print(summ)
