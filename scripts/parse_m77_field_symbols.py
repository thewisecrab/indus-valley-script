"""Parse Mahadevan 1977 Appendix II 'List of field symbols' (OCR pages PDF 802-809) -> outputs/m77_field_symbols.csv
code (cols 7-8 of Texts) -> description. Codes that OCR misread are inferred from sequence (flag inferred=1). ASI copyright: private use."""
import os, re, csv, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O = f'{ROOT}/data/books/ocr_m77'
entries = []; last = 0
for p in range(802, 810):
    toks = []
    for line in open(f'{O}/p{p:04d}.txt'):
        x, y, t, c = line.rstrip('\n').split('\t'); toks.append((int(float(x)), int(float(y)), t.strip()))
    two = [x for x, y, t in toks if re.fullmatch(r'\d{2}', t)]
    if not two: continue
    cx = collections.Counter(x // 40 for x in two).most_common(1)[0][0] * 40
    code_t = [(x, y, t) for x, y, t in toks if cx - 40 <= x <= cx + 80 and len(t) <= 3 and y > 380]
    desc_t = [(x, y, t) for x, y, t in toks if cx + 120 <= x <= cx + 1500 and y > 380 and not re.fullmatch(r'[A-H]\.\s.*|[A-H]\..*', t)]
    heads = [t for x, y, t in toks if re.match(r'^[A-H]\s?[.:]', t)]
    # entry starts = code tokens, plus capitalised desc lines following a line ending in '.'
    starts = [(y, t) for x, y, t in code_t]
    desc_t.sort(key=lambda z: z[1])
    prev_end = True; code_ys = [y for y, t in starts]
    for x, y, t in desc_t:
        if prev_end and t[:1].isupper() and not any(abs(y - cy) < 25 for cy in code_ys) and x < cx + 220:
            starts.append((y, None))
        prev_end = t.rstrip().endswith(('.', ')', '}'))
    starts.sort()
    for i, (y, t) in enumerate(starts):
        y2 = starts[i + 1][0] if i + 1 < len(starts) else 10**9
        desc = ' '.join(tt for xx, yy, tt in desc_t if y - 25 <= yy < y2 - 25)
        code = int(t) if t and re.fullmatch(r'\d{2}', t) else None
        inferred = code is None or code != last + 1
        if code is None or abs(code - (last + 1)) > 3: code = last + 1
        last = code
        if code > 98: break
        entries.append(dict(code=f'{code:02d}', description=desc.strip(), inferred_code=int(inferred), pdf_page=p))
with open(f'{ROOT}/outputs/m77_field_symbols.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(entries[0])); w.writeheader(); w.writerows(entries)
print(len(entries), 'entries; inferred', sum(e['inferred_code'] for e in entries))
for e in entries[:12] + entries[-6:]: print(e['code'], e['inferred_code'], e['description'][:90])
