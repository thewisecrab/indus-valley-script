"""Re-OCR the text-number + code strip of Mahadevan 1977 Texts pages at 300 dpi (crop x=320..730 @150dpi)."""
import sys, os, pymupdf, numpy as np, glob
from rapidocr_onnxruntime import RapidOCR
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pdf = glob.glob(f'{ROOT}/data/books/masi77*/*.pdf')[0]; out = f'{ROOT}/data/books/ocr_m77_codes'; os.makedirs(out, exist_ok=True)
ocr = RapidOCR(); doc = pymupdf.open(pdf)
a, b = int(sys.argv[1]), int(sys.argv[2])
for p in range(a, b + 1):
    fn = f'{out}/p{p:04d}.txt'
    if os.path.exists(fn): continue
    r = doc[p].rect; s = 72/150
    clip = pymupdf.Rect(320*s, 0, 730*s, r.height)
    pix = doc[p].get_pixmap(dpi=300, clip=clip)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)[:, :, :3]
    res, _ = ocr(img)
    with open(fn, 'w') as f:
        for box, txt, conf in (res or []):
            # convert back to 150-dpi page coords
            f.write(f"{int(box[0][0]/2+320)}\t{int(box[0][1]/2)}\t{txt}\t{float(conf):.2f}\n")
print('done', a, b)
