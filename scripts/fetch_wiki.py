"""Fetch random Wikipedia article plaintext (CC BY-SA 4.0) for comparanda: ta, sa, fi, en, hi."""
import requests, json, time, sys, os
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'comparanda_text')
UA = {'User-Agent': 'IndusResearchBot/0.1 (private research; contact via owner)'}
for lang in sys.argv[1:]:
    txt = []; n = 0; meta = []
    while sum(map(len, txt)) < 300000 and n < 60:
        r = requests.get(f'https://{lang}.wikipedia.org/w/api.php', params=dict(action='query', prop='extracts', explaintext=1, generator='random',
            grnnamespace=0, grnlimit=20, format='json', exlimit=20), headers=UA, timeout=30)
        n += 1
        for p in r.json().get('query', {}).get('pages', {}).values():
            if p.get('extract'): txt.append(p['extract']); meta.append(dict(pageid=p['pageid'], title=p['title']))
        time.sleep(0.5)
    open(f'{OUT}/wiki_{lang}.txt', 'w').write('\n\n'.join(txt)); json.dump(meta, open(f'{OUT}/wiki_{lang}_pages.json', 'w'))
    print(lang, len(meta), sum(map(len, txt)))
