"""Digit-template OCR for Mahadevan 1977 Texts pages (text no. + 6-digit code).
Stage 1 (extract): per page, find row bands in the number/code strip, split glyphs by column projection, save normalized 24x16 glyph bitmaps.
Stage 2 (train): label glyphs from rows where RapidOCR gave a valid number+code with exactly 10 glyphs -> per-digit templates (kNN).
Stage 3 (decode): classify every row; accept text numbers that exist in M77 and fit the monotonic sequence."""
import sys, os, glob, pickle, csv, re, collections
import numpy as np, pymupdf
from scipy import ndimage
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f'{ROOT}/data/books/m77_digit'
pdf = glob.glob(f'{ROOT}/data/books/masi77*/*.pdf')[0]
DPI = 300; F = DPI / 150
def norm(g):
    ys, xs = np.where(g)
    g = g[ys.min():ys.max()+1, xs.min():xs.max()+1].astype(float)
    zy, zx = 24 / g.shape[0], 16 / g.shape[1]
    z = ndimage.zoom(g, (zy, zx), order=1)[:24, :16]
    out = np.zeros((24, 16)); out[:z.shape[0], :z.shape[1]] = z
    return out
def extract(p, doc):
    pix = doc[p].get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY)
    G = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w)
    xs_ = []
    fn = f'{ROOT}/data/books/ocr_m77/p{p:04d}.txt'
    for line in open(fn):
        x, y, t, c = line.rstrip('\n').split('\t')
        if len(t.replace(' ', '')) == 4 and int(x) < 900 and int(y) > 230: xs_.append(int(x))
    xnum = int(np.median(xs_)) if xs_ else 372
    x0, x1 = int((xnum - 42) * F), int((xnum + 488) * F)
    B = G[:, x0:x1] < 170
    rowp = ndimage.binary_dilation(B.sum(1) > 1, iterations=8)
    lab, n = ndimage.label(rowp); rows = []
    for i in range(1, n + 1):
        ys = np.where(lab == i)[0]; y0, y1 = ys.min(), ys.max()
        if y1 - y0 < 12 * F or y0 < 230 * F: continue
        band = B[y0:y1+1]
        colp = ndimage.binary_dilation(band.sum(0) > 0, iterations=1)
        cl, m = ndimage.label(colp); glyphs = []; spans = []
        for j in range(1, m + 1):
            xs = np.where(cl == j)[0]; a0, a1 = xs.min(), xs.max()
            if spans and a0 - spans[-1][1] < 15 and a1 - spans[-1][0] < 75: spans[-1][1] = a1
            else: spans.append([a0, a1])
        for a0, a1 in spans:
            xs = np.arange(a0, a1 + 1)
            g = band[:, xs.min():xs.max()+1]
            if g.sum() < 15: continue
            glyphs.append((int(xs.min() + x0), norm(g), int(g.shape[0]), int(g.shape[1])))
        rows.append(dict(page=p, y=int(y0 / F), glyphs=glyphs, xnum=xnum))
    return rows
if __name__ == '__main__':
    a, b = int(sys.argv[1]), int(sys.argv[2]); doc = pymupdf.open(pdf)
    for p in range(a, b + 1):
        fn = f'{OUT}/p{p:04d}.pkl'
        if os.path.exists(fn): continue
        pickle.dump(extract(p, doc), open(fn, 'wb'))
    print('done', a, b)
