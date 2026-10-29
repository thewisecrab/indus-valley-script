"""Render Wells/ICIT sign glyphs from the SK Indus Script font (Shabir Kumbhar 2017, 'All Rights Reserved' -> PRIVATE use)
using the GLYPHID->codepoint table in yajnadevam/indus-website population-script.sql (GLYPHID = Wells number)."""
import os, re, json
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = f'{ROOT}/data/yajnadevam_indus-website'
sql = open(f'{W}/population-script.sql').read()
m = {int(a): int(b, 16) for a, b in re.findall(r'\((\d+),"&#x([0-9A-F]+);"\)', sql)}
font = ImageFont.truetype(f'{W}/src/assets/fonts/sk_indus_script-webfont.ttf', 120)
OUT = f'{ROOT}/paper/evidence/glyphs_W'; idx = {}
for g, cp in m.items():
    im = Image.new('L', (200, 200), 255); d = ImageDraw.Draw(im); d.text((100, 100), chr(cp), font=font, fill=0, anchor='mm')
    bb = Image.eval(im, lambda v: 255 - v).getbbox()
    if not bb: continue
    im = im.crop((max(0, bb[0] - 6), max(0, bb[1] - 6), min(200, bb[2] + 6), min(200, bb[3] + 6)))
    fn = f'W{g:03d}.png'; im.save(f'{OUT}/{fn}'); idx[f'W{g:03d}'] = dict(file=f'paper/evidence/glyphs_W/{fn}', codepoint=hex(cp))
json.dump(idx, open(f'{OUT}/index.json', 'w'), indent=0); print(len(m), 'rendered', len(idx))
