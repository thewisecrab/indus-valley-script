"""Crop each M77 sign-list glyph (M1–M417) from the IA scan of Mahadevan 1977 sign list (book pp.32–35). PRIVATE use (ASI copyright)."""
import os, re, collections, subprocess, numpy as np, json
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = f'{ROOT}/data/books/masi77indusscripttextsconcordancestablesiravathammahadevan_410_D/MASI 77 Indus Script Texts Concordances & Tables Iravatham Mahadevan.pdf'
OUT = f'{ROOT}/paper/evidence/glyphs'; os.makedirs(OUT, exist_ok=True)
index = {}
for p in (43, 44, 45, 46):
    labs = []
    for l in open(f'{ROOT}/data/books/ocr_m77/p00{p}.txt'):
        x, y, t, c = l.rstrip('\n').split('\t'); m = re.fullmatch(r'(\d{1,3})\D?', t.strip())
        if m: labs.append((int(m.group(1)), int(x), int(y)))
    # rows: cluster y
    ys = sorted(y for _, _, y in labs); rows = []
    for y in ys:
        if not rows or y - rows[-1][-1] > 60: rows.append([y])
        else: rows[-1].append(y)
    rowy = [int(np.median(r)) for r in rows if len(r) >= 3]
    xs = sorted(x for _, _, x in [(0, 0, x) for _, x, _ in labs]); cols = []
    for x in xs:
        if not cols or x - cols[-1][-1] > 80: cols.append([x])
        else: cols[-1].append(x)
    colx = [int(np.median(c)) for c in cols if len(c) >= 3]
    def rc(x, y): return int(np.argmin([abs(y - r) for r in rowy])), int(np.argmin([abs(x - c) for c in colx]))
    off = collections.Counter(n - 10 * rc(x, y)[0] - rc(x, y)[1] for n, x, y in labs).most_common(1)[0][0]
    subprocess.run(['pdftoppm', '-r', '150', '-png', '-f', str(p + 1), '-l', str(p + 1), PDF, '/tmp/glp'], check=True)
    im = Image.open(f'/tmp/glp-{p+1:03d}.png').convert('L')
    sx = im.size[0] / 2481 if abs(im.size[0] - 2481) > 5 else 1
    cw = np.median(np.diff(colx)); rh = np.median(np.diff(rowy))
    nxt = {43: 111, 44: 220, 45: 330, 46: 418}[p]
    for ri, ry in enumerate(rowy):
        want = [n for n in range(off + 10 * ri, off + 10 * ri + 10) if n < nxt]
        have = {n: x for n, x, y in labs if abs(y - ry) < 60 and n in want}
        if len(have) < 2: have = {n: colx[n - off - 10 * ri] for n in want}
        hn = sorted(have)
        xs = {n: (have[n] if n in have else float(np.interp(n, hn, [have[k] for k in hn]))) for n in want}
        if len(want) < 10 and len(have) == len(want) - 1 and False: pass
        for n in want:
            i = want.index(n); left = xs[want[i-1]] if i else xs[n] - cw; right = xs[want[i+1]] if i + 1 < len(want) else xs[n] + cw
            box = (int((left + xs[n]) / 2 + 10), int(ry - rh + 45), int((xs[n] + right) / 2 + 10), int(ry - 12))
            crop = im.crop(box)
            if (np.array(crop) < 128).sum() < 5: continue
            fn = f'M{n:03d}.png'; crop.save(f'{OUT}/{fn}')
            index[f'M{n:03d}'] = dict(file=f'paper/evidence/glyphs/{fn}', pdf_page=p + 1, book_page=p - 11, box_150dpi=box, label_ocr=n in have)
    print(p, 'offset', off, 'rows', len(rowy), 'cols', len(colx))
json.dump(index, open(f'{OUT}/index.json', 'w'), indent=0)
print('cropped', len(index), 'missing', [f'M{i:03d}' for i in range(1, 418) if f'M{i:03d}' not in index][:40])
