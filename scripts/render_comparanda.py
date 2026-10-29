"""Session 4: render open sign repertoires for visual look-alike comparison.
- Egyptian hieroglyphs, cuneiform (Neo-Assyrian-style Unicode forms, NOT archaic), Brahmi, Linear A: Noto fonts (SIL OFL 1.1)
- Linear Elamite: elamicon FontForge glyph sources (github elamicon/elamicon @69b4cc2; GPL-2 + Liberation exceptions)
Not covered (no open glyph source found): Proto-Elamite (elamicon builds it from a signlist.pdf not in the repo),
archaic/proto-cuneiform forms, South Indian megalithic graffiti marks."""
import os, re, json, glob, unicodedata, numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = f'{ROOT}/paper/evidence/comparanda'
F = f'{ROOT}/data/fonts_open'
def render_font(path, script, filt):
    tt = TTFont(path); cmap = tt.getBestCmap(); font = ImageFont.truetype(path, 96)
    os.makedirs(f'{OUT}/{script}', exist_ok=True); idx = {}
    for cp in sorted(cmap):
        try: name = unicodedata.name(chr(cp))
        except ValueError: continue
        if not filt(name): continue
        im = Image.new('L', (200, 200), 255); d = ImageDraw.Draw(im); d.text((20, 20), chr(cp), font=font, fill=0)
        a = np.array(im)
        if (a < 128).sum() < 20: continue
        fn = f'{OUT}/{script}/U{cp:05X}.png'; im.save(fn); idx[f'U+{cp:05X}'] = dict(file=fn, name=name)
    json.dump(idx, open(f'{OUT}/{script}/index.json', 'w'), indent=0); print(script, len(idx))
render_font(f'{F}/NotoSansEgyptianHieroglyphs-Regular.ttf', 'egyptian', lambda n: n.startswith('EGYPTIAN HIEROGLYPH ') and 'FORMAT' not in n)
render_font(f'{F}/NotoSansCuneiform-Regular.ttf', 'cuneiform', lambda n: n.startswith('CUNEIFORM SIGN') or n.startswith('CUNEIFORM NUMERIC'))
render_font(f'{F}/NotoSansBrahmi-Regular.ttf', 'brahmi', lambda n: n.startswith('BRAHMI') and 'VOWEL SIGN' not in n and 'VIRAMA' not in n and 'SIGN' not in n.split('BRAHMI ')[1][:4] or n.startswith('BRAHMI NUMBER') or n.startswith('BRAHMI DIGIT'))
render_font(f'{F}/NotoSansLinearA-Regular.ttf', 'linear_a', lambda n: n.startswith('LINEAR A'))
# Linear Elamite from elamicon .glyph spline sources
def parse_glyph(p):
    t = open(p).read()
    m = re.search(r'\nFore\nSplineSet\n(.*?)EndSplineSet', t, re.S)
    if not m: return None
    contours = []; cur = []; last = None
    for line in m.group(1).splitlines():
        tok = line.split()
        if not tok: continue
        op = tok[-2] if tok[-1].lstrip('-').isdigit() or ',' in tok[-1] else tok[-1]
        nums = [float(x) for x in tok if re.match(r'^-?\d+(\.\d+)?$', x)]
        if 'm' in tok:
            if cur: contours.append(cur)
            x, y = nums[0], nums[1]; cur = [(x, y)]; last = (x, y)
        elif 'l' in tok:
            x, y = nums[0], nums[1]; cur.append((x, y)); last = (x, y)
        elif 'c' in tok:
            x1, y1, x2, y2, x3, y3 = nums[:6]; x0, y0 = last
            for t_ in np.linspace(0, 1, 12)[1:]:
                mt = 1 - t_
                cur.append((mt**3*x0 + 3*mt*mt*t_*x1 + 3*mt*t_*t_*x2 + t_**3*x3, mt**3*y0 + 3*mt*mt*t_*y1 + 3*mt*t_*t_*y2 + t_**3*y3))
            last = (x3, y3)
    if cur: contours.append(cur)
    return contours
os.makedirs(f'{OUT}/linear_elamite', exist_ok=True); idx = {}
for p in sorted(glob.glob(f'{ROOT}/data/elamicon_repo/fonts/original/elamicon.sfdir/uni*.glyph')):
    cs = parse_glyph(p)
    if not cs: continue
    pts = np.array([q for c in cs for q in c]); x0, y0 = pts.min(0); x1, y1 = pts.max(0); s = 160/max(x1-x0, y1-y0, 1)
    acc = np.zeros((200, 200), bool)
    for c in cs:
        if len(c) < 3: continue
        im = Image.new('1', (200, 200), 0); ImageDraw.Draw(im).polygon([(20+(x-x0)*s, 180-(y-y0)*s) for x, y in c], fill=1)
        acc ^= np.array(im)
    if acc.sum() < 20: continue
    name = os.path.basename(p)[:-6]; fn = f'{OUT}/linear_elamite/{name}.png'
    Image.fromarray(np.where(acc, 0, 255).astype(np.uint8)).save(fn); idx[name] = dict(file=fn, name='elamicon ' + name)
json.dump(idx, open(f'{OUT}/linear_elamite/index.json', 'w'), indent=0); print('linear_elamite', len(idx))
