"""Row-segment Mahadevan 1977 Texts pages (projection profile on the number/code strip) and run
RapidOCR recognition-only on the number cell and the code cell of each row.
usage: ocr_m77_cells.py first last -> data/books/ocr_m77_cells/p####.tsv (y, num_text, num_conf, code_text, code_conf)"""
import sys, os, glob, pymupdf, numpy as np
from scipy import ndimage
from rapidocr_onnxruntime import RapidOCR
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pdf = glob.glob(f'{ROOT}/data/books/masi77*/*.pdf')[0]; out = f'{ROOT}/data/books/ocr_m77_cells'; os.makedirs(out, exist_ok=True)
ocr = RapidOCR(); doc = pymupdf.open(pdf); DPI = 300; f = DPI/150
def prep(g):
    g = ndimage.grey_erosion(g, size=(3, 3)); g = np.where(g < 180, 0, 255).astype(np.uint8)
    g = np.pad(g, 20, constant_values=255); return np.stack([g]*3, -1)
def rec(g):
    res, _ = ocr(prep(g), use_det=False, use_cls=False, use_rec=True)
    if not res: return '', 0.0
    t, c = res[0]; return t.replace(' ', ''), float(c)
for p in range(int(sys.argv[1]), int(sys.argv[2]) + 1):
    fn = f'{out}/p{p:04d}.tsv'
    if os.path.exists(fn): continue
    pix = doc[p].get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY)
    G = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w)
    strip = G[:, int(330*f):int(740*f)] < 160
    prof = ndimage.binary_dilation(strip.sum(1) > 2, iterations=6)
    lab, n = ndimage.label(prof)
    rows = []
    for i in range(1, n + 1):
        ys = np.where(lab == i)[0]; y0, y1 = ys.min(), ys.max()
        if y1 - y0 < 15*f or y0 < 230*f: continue
        num = rec(G[y0:y1, int(330*f):int(565*f)]); code = rec(G[y0:y1, int(565*f):int(740*f)])
        rows.append((int(y0/f), *num, *code))
    with open(fn, 'w') as fh:
        for r in rows: fh.write('\t'.join(map(str, r)) + '\n')
print('done')
