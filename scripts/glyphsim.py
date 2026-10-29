"""Shared glyph-image normalisation and similarity (chamfer + HOG), mirror-invariant."""
import numpy as np, cv2
from PIL import Image
S = 48
def _hogc(img):
    a = img.astype(float); gy, gx = np.gradient(cv2.GaussianBlur(a, (5, 5), 1.0))
    mag = np.hypot(gx, gy); ang = (np.arctan2(gy, gx) % np.pi) / np.pi * 9
    b = np.minimum(ang.astype(int), 8); H = np.zeros((6, 6, 9))
    for i in range(6):
        for j in range(6):
            sl = (slice(i * 8, i * 8 + 8), slice(j * 8, j * 8 + 8))
            H[i, j] = np.bincount(b[sl].ravel(), weights=mag[sl].ravel(), minlength=9)
    return H.ravel()
class _H:
    def compute(self, img): return _hogc(img)
_hog = _H()
def norm(path_or_img, thr=128):
    im = path_or_img if isinstance(path_or_img, Image.Image) else Image.open(path_or_img)
    a = np.array(im.convert('L')) < thr
    ys, xs = np.where(a)
    if len(ys) == 0: return None
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.uint8)
    h, w = a.shape; s = (S - 4) / max(h, w)
    r = cv2.resize(a * 255, (max(1, int(round(w * s))), max(1, int(round(h * s)))), interpolation=cv2.INTER_AREA)
    out = np.zeros((S, S), np.uint8); y0 = (S - r.shape[0]) // 2; x0 = (S - r.shape[1]) // 2; out[y0:y0 + r.shape[0], x0:x0 + r.shape[1]] = r
    return (out > 60).astype(np.uint8)
def feats(b):
    if b is None: return None
    dt = cv2.distanceTransform((1 - b).astype(np.uint8), cv2.DIST_L2, 3)
    h = _hog.compute((b * 255).astype(np.uint8)).ravel(); h = h / (np.linalg.norm(h) + 1e-9)
    hf = _hog.compute((b[:, ::-1] * 255).astype(np.uint8)).ravel(); hf = hf / (np.linalg.norm(hf) + 1e-9)
    dtf = cv2.distanceTransform((1 - b[:, ::-1]).astype(np.uint8), cv2.DIST_L2, 3)
    return dict(b=b, dt=dt, hog=h, bf=b[:, ::-1], dtf=dtf, hogf=hf, ink=b.sum() / b.size)
def _chamfer(a, dta, b, dtb):
    da = (dtb[a > 0]).mean() if a.sum() else 99; db = (dta[b > 0]).mean() if b.sum() else 99
    return (da + db) / 2
def sim(fa, fb):
    """similarity in [0,1]; max over mirror of b"""
    if fa is None or fb is None: return np.nan
    c1 = _chamfer(fa['b'], fa['dt'], fb['b'], fb['dt']); c2 = _chamfer(fa['b'], fa['dt'], fb['bf'], fb['dtf'])
    h1 = float(fa['hog'] @ fb['hog']); h2 = float(fa['hog'] @ fb['hogf'])
    s1 = 0.5 * np.exp(-c1 / 3) + 0.5 * h1; s2 = 0.5 * np.exp(-c2 / 3) + 0.5 * h2
    return float(max(s1, s2))
def hog_matrix(F):
    return np.stack([f['hog'] for f in F]), np.stack([f['hogf'] for f in F])
