"""Integrate session-2 structured data into map/indus_map.sqlite (run after build_map.py)."""
import sqlite3, csv, json, os, re, xml.etree.ElementTree as ET
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
c = sqlite3.connect(f'{ROOT}/map/indus_map.sqlite')
SRC = [
 ('lipi_fc8813a', 'yajnadevam/lipi GitHub repo (xlits.csv key, inscriptions.csv readings, index.vue rules), commit fc8813a 2026-08-19', '2026', 'https://github.com/yajnadevam/lipi', 'code/data', 'public repo, NO licence file -> private research use', 'yes'),
 ('m77_ocr_codes', 'Mahadevan 1977 Texts pp.39-162: text numbers + 6-digit codes, RapidOCR of IA scan masi77... (this project)', '1977/2026', 'https://archive.org/details/masi77indusscripttextsconcordancestablesiravathammahadevan_410_D', 'derived OCR', 'ASI copyright -> private research use', 'yes'),
 ('sproat_weights', 'R. Sproat, Indus weights data page + weights.xml (Hemmy 1931/1938/1940/1943 + HARP 1986-2001 data)', '2013', 'https://richardsproat.com/indus_weights/', 'dataset', 'weights.xml states GPL-3', 'yes'),
 ('kenoyer2010', 'Kenoyer J.M. 2010, Measuring the Harappan world (in Morley & Renfrew eds., The Archaeology of Measurement, CUP)', '2010', 'https://www.harappa.com/sites/default/files/pdf/Kenoyer%202010%20Measuring%20the%20Harappan%20World.pdf', 'chapter', 'author copy on harappa.com; CUP copyright -> private', 'yes'),
 ('csl_mw', 'Cologne Digital Sanskrit Dictionaries, csl-orig v02/mw/mw.txt (Monier-Williams 1899)', '2026', 'https://github.com/sanskrit-lexicon/csl-orig', 'lexicon', 'CC BY-SA 4.0 (repo)', 'yes'),
 ('freqwords', 'H. Dave, FrequencyWords 2018 50k lists (fi, tr, id, hu, en) from OpenSubtitles', '2018', 'https://github.com/hermitdave/FrequencyWords', 'lexicon', 'MIT (code); content CC BY-SA 4.0 per repo README', 'yes'),
 ('dravdb', 'Merriam & Fuls, Dravidian Database v1.2 (Zenodo 22682542)', '2026', 'https://zenodo.org/records/22682542', 'lexicon', 'CC BY 4.0', 'yes'),
]
for s in SRC: c.execute('INSERT OR REPLACE INTO sources VALUES (?,?,?,?,?,?,?)', s)
c.execute("UPDATE claims SET notes = notes || ' | session2: key+rules taken from yajnadevam/lipi fc8813a (index.vue xlitize); see outputs/claims/' WHERE claim_id='C7' AND notes NOT LIKE '%session2%'")

# --- M77 site from text-number ranges (Mahadevan 1977, CODES p.30, Code 1) ---
RANGES = [(1001,1905,'Mohenjo-daro'),(2002,2952,'Mohenjo-daro'),(3001,3513,'Mohenjo-daro'),(4001,4905,'Harappa'),(5001,5601,'Harappa'),
          (6101,6405,'Chanhu-daro'),(7001,7301,'Lothal'),(8001,8302,'Kalibangan'),(9001,9701,'Other sites (M77 class OS)'),(9801,9905,'West Asian finds (M77 class WA)')]
def site_id(name):
    r = c.execute('SELECT site_id FROM sites WHERE name=?', (name,)).fetchone()
    if r: return r[0]
    c.execute('INSERT INTO sites(name, source_id) VALUES (?,?)', (name, 'm77_ocr_codes')); return c.execute('SELECT last_insert_rowid()').fetchone()[0]
n_site = 0
for (oid,) in c.execute("SELECT object_id FROM objects WHERE corpus='M77'").fetchall():
    t = int(oid.split(':')[1])
    for a, b, name in RANGES:
        if a <= t <= b:
            c.execute('UPDATE objects SET site_id=? WHERE object_id=?', (site_id(name), oid)); n_site += 1; break

# --- M77 OCR codes ---
TYPES = {'1':'seal','2':'sealing','3':'miniature tablet','4':'pottery graffito','5':'copper tablet','6':'bronze implement','7':'ivory/bone rod','9':'miscellaneous'}
def fclass(f):
    f = int(f)
    return ('animal' if 1 <= f <= 35 else 'reptile/fish/bird' if f <= 43 else 'tree/leaf' if f <= 46 else 'anthropomorphic' if f <= 59
            else 'scene' if f <= 81 else 'symbol/motif' if 82 <= f <= 98 else 'damaged' if f == 99 else 'none' if f == 0 else 'unassigned')
c.execute('DROP TABLE IF EXISTS m77_codes')
c.execute('CREATE TABLE m77_codes (object_id TEXT, textnum INTEGER, code TEXT, obj_type TEXT, side TEXT, field_symbol TEXT, field_class TEXT, line TEXT, direction TEXT, inherited INTEGER, ocr_conf REAL, pdf_page INTEGER, source_id TEXT)')
rows = list(csv.DictReader(open(f'{ROOT}/outputs/m77_codes_ocr_valid.csv')))
for r in rows:
    c.execute('INSERT INTO m77_codes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (f"M77:{r['textnum']}", int(r['textnum']), r['code'], TYPES.get(r['obj_type']), r['side'], r['field_symbol'],
              fclass(r['field_symbol']), r['line'], r['direction'], int(r['inherited'] == 'True'), float(r['ocr_conf']), int(r['page']), 'm77_ocr_codes'))
n_type = 0
for r in rows:
    if r['inherited'] == 'True': continue
    n_type += c.execute('UPDATE objects SET object_type=?, motif=COALESCE(motif, ?) WHERE object_id=? AND object_type IS NULL',
              (TYPES.get(r['obj_type']), f"M77 field symbol {r['field_symbol']} ({fclass(r['field_symbol'])})", f"M77:{r['textnum']}")).rowcount

# --- ICIT-derived metadata from lipi (private use) ---
d = pd.read_csv(f'{ROOT}/data/lipi/inscriptions.csv', dtype=str, keep_default_na=False)
cols = ['id','cisi','region','site','type','symbol','material','dir.','complete','text']
d[cols].rename(columns={'dir.':'dir'}).assign(source_id='lipi_fc8813a').to_sql('icit_meta_lipi', c, if_exists='replace', index=False)

# --- weights ---
W = ET.parse(f'{ROOT}/data/weights/weights.xml').getroot(); wr = []
for w in W.findall('weight'):
    wr.append({k: w.findtext(k) for k in ['biblio','provenance','location','depth','catalog','material','condition','shape','value','dimensions','category']})
pd.DataFrame(wr).assign(source_id='sproat_weights').to_sql('weights', c, if_exists='replace', index=False)

# --- results tables ---
res = []
for f in ['A_summary.json', 'B_fixed_key_segmentability.json', 'D_free_parameters.json']:
    res.append(('C7', f, open(f'{ROOT}/outputs/claims/{f}').read()))
res.append(('C7', 'C_summary.csv', open(f'{ROOT}/outputs/claims/C_summary.csv').read()))
res.append(('PARPOLA', 'parpola_num_fish.json', open(f'{ROOT}/outputs/claims/parpola_num_fish.json').read()))
res.append(('MAHADEVAN', 'mahadevan_positional.json', open(f'{ROOT}/outputs/claims/mahadevan_positional.json').read()))
c.execute('DROP TABLE IF EXISTS claim_tests'); c.execute('CREATE TABLE claim_tests (claim_id TEXT, test TEXT, result TEXT, run_date TEXT)')
for r in res: c.execute('INSERT INTO claim_tests VALUES (?,?,?,?)', (*r, '2026-10-28/29 IST'))
c.execute('DROP TABLE IF EXISTS anchor_results'); c.execute('CREATE TABLE anchor_results (topic TEXT, result_json TEXT, label TEXT)')
A = json.load(open(f'{ROOT}/outputs/anchors/anchors_summary.json'))
for k, v in A.items(): c.execute('INSERT INTO anchor_results VALUES (?,?,?)', (k, json.dumps(v, default=str), None))
c.commit()
print(dict(m77_sites_set=n_site, m77_codes=len(rows), m77_object_types_set=n_type, icit_meta=len(d), weights=len(wr)))
for t in ['sources','sites','objects','m77_codes','icit_meta_lipi','weights','claim_tests','anchor_results']:
    print(t, c.execute(f'SELECT count(*) FROM {t}').fetchone()[0])
