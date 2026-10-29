"""Fetch Wikipedia article plaintext (CC BY-SA 4.0) for comparanda.
  python scripts/fetch_wiki.py ta sa fi en      random articles (original sessions; not reproducible)
  python scripts/fetch_wiki.py --pages          re-fetch the exact pages used (data_open/comparanda_pages/wiki_<lang>_pages.json);
                                                article text may have been edited since, so values can differ slightly"""
import requests, json, time, sys, os, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'comparanda_text'); os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'IndusResearchBot/0.1 (research; see github.com/thewisecrab/indus-valley-script)'}
def extracts(lang, **params):
    r = requests.get(f'https://{lang}.wikipedia.org/w/api.php', params=dict(action='query', prop='extracts', explaintext=1, format='json', exlimit=20, **params), headers=UA, timeout=30)
    return r.json().get('query', {}).get('pages', {}).values()
if sys.argv[1:2] == ['--pages']:
    for f in sorted(glob.glob(f'{ROOT}/data_open/comparanda_pages/wiki_*_pages.json')):
        lang = os.path.basename(f).split('_')[1]; meta = json.load(open(f)); ids = [m['pageid'] for m in meta]; got = {}
        for i in range(0, len(ids), 20):
            for p in extracts(lang, pageids='|'.join(map(str, ids[i:i + 20]))):
                if p.get('extract'): got[p['pageid']] = p['extract']
            time.sleep(0.5)
        open(f'{OUT}/wiki_{lang}.txt', 'w').write('\n\n'.join(got[i] for i in ids if i in got)); json.dump(meta, open(f'{OUT}/wiki_{lang}_pages.json', 'w'))
        print(lang, len(got), 'of', len(ids), 'pages')
    sys.exit()
for lang in sys.argv[1:]:
    txt = []; n = 0; meta = []
    while sum(map(len, txt)) < 300000 and n < 60:
        n += 1
        for p in extracts(lang, generator='random', grnnamespace=0, grnlimit=20):
            if p.get('extract'): txt.append(p['extract']); meta.append(dict(pageid=p['pageid'], title=p['title']))
        time.sleep(0.5)
    open(f'{OUT}/wiki_{lang}.txt', 'w').write('\n\n'.join(txt)); json.dump(meta, open(f'{OUT}/wiki_{lang}_pages.json', 'w'))
    print(lang, len(meta), sum(map(len, txt)))
