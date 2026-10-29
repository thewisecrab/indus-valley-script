"""Parse OCR of Mahadevan 1977 'Texts' pages (PDF idx 50-173) -> text number + 6-digit code
(cols 5-10: type, side, field symbol(2), line, direction). Pairs each code with the text number at
the same y (±25px) to its left; codes with no number on their row inherit the last number (extra side/line).
Output: outputs/m77_codes_ocr.csv. Validation: number must exist in M77 export and sequence must be monotonic."""
import glob, re, os, csv, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O = f'{ROOT}/data/books/ocr_m77'
m77 = set()
for r in csv.DictReader(open(f'{ROOT}/data/joyboseroy_indus_decipher/data/m77_indusscript_real_corpus.csv')):
    m77.add(int(r['inscription_id'].split('.')[0]))
rows = []; last = None
for p in range(50, 174):
    f = f'{O}/p{p:04d}.txt'
    if not os.path.exists(f): continue
    toks = []
    for line in open(f):
        x, y, t, c = line.rstrip('\n').split('\t')
        t = t.replace(' ', '').replace('O', '0').replace('o', '0').replace('Q', '0').replace('C', '0').replace('l', '1').replace('I', '1')
        if re.fullmatch(r'\d{10}', t):  # merged 'number code'
            toks.append((int(float(x)), int(float(y)), t[:4], float(c))); toks.append((int(float(x)) + 210, int(float(y)), t[4:], float(c)))
        else:
            toks.append((int(float(x)), int(float(y)), t, float(c)))
    nums = [(x, y, int(t)) for x, y, t, c in toks if re.fullmatch(r'\d{4}', t) and int(t) in m77]
    codes = [(x, y, t, c) for x, y, t, c in toks if re.fullmatch(r'\d{6}', t)]
    codes.sort(key=lambda z: (z[0] // 700, z[1]))  # column-major
    for x, y, t, c in codes:
        cand = [n for n in nums if abs(n[1] - y) <= 25 and 0 < x - n[0] < 400]
        if cand:
            num = min(cand, key=lambda n: x - n[0])[2]; inherited = False
        else:
            num = last; inherited = True
        if num is None: continue
        last = num
        rows.append(dict(page=p, textnum=num, code=t, inherited=inherited, ocr_conf=round(c, 3),
                         obj_type=t[0], side=t[1], field_symbol=t[2:4], line=t[4], direction=t[5]))
# monotonic check
bad = 0; prev = 0
for r in rows:
    r['nonmonotonic'] = r['textnum'] < prev; bad += r['nonmonotonic']; prev = max(prev, r['textnum'])
os.makedirs(f'{ROOT}/outputs', exist_ok=True)
with open(f'{ROOT}/outputs/m77_codes_ocr.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
covered = {r['textnum'] for r in rows if not r['inherited']}
print('code rows', len(rows), 'textnums with own code', len(covered), 'of M77', len(m77), 'nonmonotonic', bad)
print('obj_type', collections.Counter(r['obj_type'] for r in rows if r['side'] in '01'))
print('direction', collections.Counter(r['direction'] for r in rows))
print('missing ranges sample', sorted(m77 - covered)[:20])
# validation vs M77 export reading_direction (R-L <-> code 1)
exp = {}
for r in csv.DictReader(open(f'{ROOT}/data/joyboseroy_indus_decipher/data/m77_indusscript_real_corpus.csv')):
    exp.setdefault(int(r['inscription_id'].split('.')[0]), set()).add(r['reading_direction'])
agree = tot = 0; cc = collections.Counter()
for r in rows:
    if r['inherited']: continue
    e = exp.get(r['textnum'], set()); cc[(r['direction'], tuple(sorted(e)))] += 1
print('direction code vs export reading_direction', cc.most_common(10))
# domain validity + single-sign check (dir code 3 'single sign in line' vs export line length)
exp_len = collections.defaultdict(list)
for r in csv.DictReader(open(f'{ROOT}/data/joyboseroy_indus_decipher/data/m77_indusscript_real_corpus.csv')):
    exp_len[int(r['inscription_id'].split('.')[0])].append(len(r['sign_sequence'].split()))
valid = lambda r: r['obj_type'] in '12345679' and r['side'] in '0123456' and r['line'] in '01239' and r['direction'] in '0123459'
V = [r for r in rows if valid(r)]
print('domain-valid rows', len(V), 'of', len(rows))
tp = fp = fn = tn = 0
for r in V:
    if r['inherited'] or r['line'] not in '0' or r['side'] not in '0': continue
    L = exp_len.get(r['textnum'])
    if not L or len(L) != 1: continue
    single = L[0] == 1; d3 = r['direction'] == '3'
    tp += single and d3; fp += d3 and not single; fn += single and not d3; tn += (not single) and (not d3)
print('single-sign check  dir3&len1', tp, 'dir3&len>1', fp, 'len1&not3', fn, 'neither', tn)
with open(f'{ROOT}/outputs/m77_codes_ocr_valid.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(V[0])); w.writeheader(); w.writerows(V)
