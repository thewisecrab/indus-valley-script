"""Integrate session-3 results into map/indus_map.sqlite."""
import sqlite3, json, os, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
c = sqlite3.connect(f'{ROOT}/map/indus_map.sqlite')
TYPES = {'1':'seal','2':'sealing','3':'miniature tablet','4':'pottery graffito','5':'copper tablet','6':'bronze implement','7':'ivory/bone rod','9':'miscellaneous'}
def fclass(f):
    f = int(f)
    return ('animal' if 1 <= f <= 35 else 'reptile/fish/bird' if f <= 43 else 'tree/leaf' if f <= 46 else 'anthropomorphic' if f <= 59
            else 'scene' if f <= 81 else 'symbol/motif' if 82 <= f <= 98 else 'damaged' if f == 99 else 'none' if f == 0 else 'unassigned')
SRC = [('m77_digit_ocr', 'Mahadevan 1977 Texts: 6-digit codes re-read by per-glyph kNN digit classifier (this project, session 3)', '1977/2026',
        'https://archive.org/details/masi77indusscripttextsconcordancestablesiravathammahadevan_410_D', 'derived OCR', 'ASI copyright -> private research use', 'yes'),
       ('vidyut', 'vidyut 0.4 (ambuda-org) Sanskrit segmenter/lexicon data', '2025', 'https://github.com/ambuda-org/vidyut', 'software+data', 'MIT', 'yes'),
       ('wiki_comparanda', 'Random Wikipedia articles (ta, sa, fi, en) via MediaWiki API', '2026', 'https://www.mediawiki.org/wiki/API:Random', 'text', 'CC BY-SA 4.0', 'yes')]
for s in SRC: c.execute('INSERT OR REPLACE INTO sources VALUES (?,?,?,?,?,?,?)', s)
d = pd.read_csv(f'{ROOT}/outputs/m77_codes_digitocr.csv', dtype=str)
d = d[d.code.str.fullmatch(r'\d{6}')]
d['object_id'] = 'M77:' + d.textnum; d['obj_type'] = d.code.str[0].map(TYPES); d['side'] = d.code.str[1]; d['field_symbol'] = d.code.str[2:4]
d['field_class'] = d.field_symbol.apply(fclass); d['line'] = d.code.str[4]; d['direction'] = d.code.str[5]; d['source_id'] = 'm77_digit_ocr'
d[['object_id', 'textnum', 'code', 'obj_type', 'side', 'field_symbol', 'field_class', 'line', 'direction', 'src', 'page', 'source_id']].to_sql('m77_codes_digit', c, if_exists='replace', index=False)
n = 0
for r in d.itertuples():
    if str(r.inherited) == 'True': continue
    n += c.execute('UPDATE objects SET object_type=?, motif=COALESCE(motif, ?) WHERE object_id=? AND object_type IS NULL',
                   (r.obj_type, f'M77 field symbol {r.field_symbol} ({r.field_class})', r.object_id)).rowcount
for f, t in [('sign_classes_M77.csv', 'sign_classes'), ('sign_table.csv', 'sign_table'), ('linguistic_measures.csv', 'linguistic_measures')]:
    p = f'{ROOT}/outputs/structure/{f}'
    if os.path.exists(p): pd.read_csv(p).astype(str).to_sql(t, c, if_exists='replace', index=False)
for cid, f in [('C7', 'outputs/claims/E_vidyut_parse.json'), ('C_rebus', 'outputs/claims/F_rebus_summary.csv'), ('C_parpola_fish', 'outputs/claims/F_parpola_compounds.json')]:
    c.execute('DELETE FROM claim_tests WHERE claim_id=? AND test=?', (cid, os.path.basename(f)))
    c.execute('INSERT INTO claim_tests VALUES (?,?,?,?)', (cid, os.path.basename(f), open(f'{ROOT}/{f}').read(), '2026-10-29 IST'))
for topic, f, lab in [('w700_tablet_formula_vs_weights', 'outputs/anchors/w700_vs_weights.json', 'session3'), ('structure_classes', 'outputs/structure/classes_summary.json', 'session3'),
                      ('structure2_seg_hmm_ling', 'outputs/structure/structure2_summary.json', 'session3')]:
    if os.path.exists(f'{ROOT}/{f}'):
        c.execute('DELETE FROM anchor_results WHERE topic=?', (topic,)); c.execute('INSERT INTO anchor_results VALUES (?,?,?)', (topic, open(f'{ROOT}/{f}').read(), lab))
c.commit()
print('objects typed:', n, 'digit codes:', len(d), pd.read_sql("select object_type, count(*) n from objects where corpus='M77' group by 1", c).to_dict('records'))
