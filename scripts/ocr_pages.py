"""OCR selected PDF pages with RapidOCR (tesseract unavailable: apt mirror returned HTTP 500).
usage: ocr_pages.py PDF first last outdir [dpi]  -> outdir/p####.txt (lines: x y text conf)"""
import sys, os, pymupdf, numpy as np
from rapidocr_onnxruntime import RapidOCR
pdf, a, b, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]; dpi = int(sys.argv[5]) if len(sys.argv) > 5 else 150
os.makedirs(out, exist_ok=True); ocr = RapidOCR(); doc = pymupdf.open(pdf)
for p in range(a, min(b, len(doc) - 1) + 1):
    fn = f"{out}/p{p:04d}.txt"
    if os.path.exists(fn): continue
    pix = doc[p].get_pixmap(dpi=dpi); img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)[:, :, :3]
    res, _ = ocr(img)
    with open(fn, "w") as f:
        for box, txt, conf in (res or []):
            f.write(f"{int(box[0][0])}\t{int(box[0][1])}\t{txt}\t{float(conf):.2f}\n")
print("done", a, b)
