"""Relabel Carlson links. Rare signs (no distributional rank) get a visual-only rank among all 631 W renders.
Also writes a 40-pair hand-check montage: the 20 lowest-p links with freq >= 3, plus 20 random links."""
import pandas as pd, numpy as np, json, sys, os
sys.path.insert(0, 'scripts'); import glyphsim as G
from PIL import Image, ImageDraw
d = pd.read_csv('outputs/signmap/concordance_links_scored.csv')
gM = json.load(open('paper/evidence/glyphs/index.json')); gW = json.load(open('paper/evidence/glyphs_W/index.json'))
FM = {k: G.feats(G.norm(v['file'])) for k, v in gM.items()}
FW = {k: G.feats(G.norm(v['file'])) for k, v in gW.items()}
FW = {k: v for k, v in FW.items() if v is not None}
def vrank(m, w):
    if FM.get(m) is None or w not in FW: return np.nan
    s = {k: G.sim(FM[m], f) for k, f in FW.items()}
    order = sorted(s, key=lambda k: -s[k]); return order.index(w) + 1
d['visual_rank_among_W'] = [vrank(m, w) for m, w in zip(d.M, d.W)]
def lab(r):
    if not np.isnan(r.rank_among_W):
        return r.confidence
    v = r.visual_rank_among_W
    if np.isnan(v): return 'untestable (no glyph)'
    if v <= 5: return 'rare sign: visual-only support (visual rank <= 5)'
    if v <= 25: return 'rare sign: weak visual support (rank 6-25)'
    return 'rare sign: untestable distributionally; visual evidence weak'
d['confidence'] = d.apply(lab, axis=1)
d.to_csv('outputs/signmap/concordance_links_scored.csv', index=False)
print(d.confidence.value_counts().to_string())
rng = np.random.default_rng(4)
d = d[d.M.isin(gM) & d.W.isin(gW)]
low = d[(d.freqM >= 3) & (d.freqW >= 3)].nsmallest(20, 'p_link_raw')
rnd = d.drop(low.index).sample(20, random_state=4)
hc = pd.concat([low.assign(set='lowest-p'), rnd.assign(set='random')])
W_, H_ = 150, 120; im = Image.new('L', (W_*8, H_*5*2//1), 255); dr = ImageDraw.Draw(im)
for i, r in enumerate(hc.itertuples()):
    x = (i % 8)*W_; y = (i//8)*H_
    for j, f in enumerate([gM[r.M]['file'], gW[r.W]['file']]):
        g = Image.open(f).convert('L'); g.thumbnail((W_//2-6, H_-30)); im.paste(g, (x+j*W_//2+3, y+3))
    dr.text((x+3, y+H_-26), f'{i}:{r.M}/{r.W}', fill=0); dr.text((x+3, y+H_-14), r.set[:6], fill=0)
im = im.crop((0, 0, W_*8, H_*5)); im.save('outputs/signmap/handcheck_montage.png')
hc.to_csv('outputs/signmap/handcheck_pairs.csv', index=False)
