"""Positive-control corpora (session 7). Builds sign-token texts with CORRECT sign values for two deciphered scripts.

Sanskrit (Brahmi-family akshara writing): DCS (Hellwig, CC BY 4.0) sentences of Manusmrti, Hitopadesa, Rgveda.
  Unsandhied DCS tokens -> SLP1 (vidyut.lipi) -> external sandhi re-applied with vidyut's sandhi rule table (rules.csv,
  used in the joining direction; first matching rule) -> orthographic aksharas (C*V[MH~]*, trailing consonants join the
  last akshara). Each akshara is one 'sign'; the correct key maps it to its own SLP1 value.
Akkadian cuneiform: ORACC JSON (CC0 per the JSON metadata; ORACC site licence CC BY-SA 3.0), SAAo SAA 1 + SAA 5
  (Neo-Assyrian letters of Sargon II). Each grapheme is one 'sign' identified by its Unicode cuneiform glyph.
  Correct (contextual) value = the editor's reading: syllabograms -> their phonetic value; in a word containing a
  logogram, the word's normalised form (ORACC 'norm') is assigned to the first logogram and the word's other graphemes
  are silent; determinatives and numerals are silent. Words with a missing/unlemmatised grapheme break the stream.
Output: positive_control/outputs/corpora/*.json  (list of texts; each text = list of words; word = list of [sign, value])
"""
import os, re, json, zipfile, collections, unicodedata, glob
from vidyut.lipi import transliterate, Scheme
PC = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); ROOT = os.path.dirname(PC)
OUT = f'{PC}/outputs/corpora'; os.makedirs(OUT, exist_ok=True)

# ---------------- Sanskrit ----------------
RULES = {}
for line in open(f'{ROOT}/data/vidyut/sandhi/rules.csv', encoding='utf8').read().splitlines()[1:]:
    f, s, r = line.split(',')
    RULES.setdefault((f, s), r)          # first listed rule wins
VOW = set('aAiIuUfFxXeEoO')
def join2(w1, w2):
    if w1.endswith('H'): w1 = w1[:-1] + 's'   # rule table writes final visarga as s
    for k in (2, 1):
        if len(w1) < k: continue
        f = w1[-k:]
        for j in (2, 1):
            s = w2[:j]
            if (f, s) in RULES:
                r = RULES[(f, s)]
                left, _, right = r.partition(' ')
                return w1[:-k] + left, right + w2[j:] if right else w2[j:]
    return w1, w2
def final(w):
    if w.endswith('H'): w = w[:-1] + 's'
    for k in (2, 1):
        if (w[-k:], '') in RULES: return w[:-k] + RULES[(w[-k:], '')]
    return w
def sandhi_join(words):
    ws = list(words)
    for i in range(len(ws) - 1):
        ws[i], ws[i + 1] = join2(ws[i], ws[i + 1])
    ws[-1] = final(ws[-1])
    return ws
def aksharas(s):
    out, cur = [], ''
    for c in s:
        if c in VOW:
            cur += c; out.append(cur); cur = ''
        elif c in 'MH~' and out and not cur:
            out[-1] += c
        elif c.isalpha():
            cur += c
    if cur:
        if out: out[-1] += cur
        else: out.append(cur)
    return out
def build_sanskrit():
    for name, pats in {'sanskrit_classical': ['Manusmṛti', 'Hitopadeśa'], 'sanskrit_vedic': ['Ṛgveda']}.items():
        texts = []
        for p in pats:
            for fn in sorted(glob.glob(f'{PC}/data/dcs/{p}/*.conllu')):
                toks = []
                for line in open(fn, encoding='utf8'):
                    if line.startswith('# text ='):
                        toks = []
                    elif line.strip() == '' and toks:
                        texts.append(toks); toks = []
                    elif line and line[0].isdigit():
                        c = line.split('\t')
                        if '-' in c[0] or '.' in c[0]: continue
                        w = transliterate(c[1], Scheme.Iast, Scheme.Slp1)
                        w = re.sub(r"[^a-zA-Z~']", '', w).replace("'", '')
                        if w: toks.append(w)
                if toks: texts.append(toks)
        # sandhi-join, then aksharas per word-chunk; record word boundary positions (in aksharas) of the joined string
        out = []
        for ws in texts:
            if len(ws) < 1: continue
            j = [re.sub(r"[^a-zA-Z~]", "", w) for w in sandhi_join(ws)]; j = [w for w in j if w]
            # aksharas over the whole joined string; word starts = akshara index containing the first char of each word
            full = ''.join(j); ak = aksharas(full)
            # map char offsets to akshara index
            starts, pos = [], 0
            for w in j:
                starts.append(pos); pos += len(w)
            idx, c2a, p = [], [], 0
            for a_i, a in enumerate(ak):
                c2a += [a_i] * len(a)
            # aksharas() drops non-alpha; full is alpha only so lengths agree
            assert len(c2a) == len(full), (full, ak)
            wb = sorted(set(c2a[s] for s in starts if s < len(full)))
            out.append(dict(signs=ak, values=ak, word_starts=wb))
        json.dump(out, open(f'{OUT}/{name}.json', 'w'))
        print(name, len(out), 'sentences', sum(len(t['signs']) for t in out), 'aksharas',
              len(set(a for t in out for a in t['signs'])), 'akshara types')

# ---------------- Akkadian (ORACC) ----------------
def red_akk(v):
    v = unicodedata.normalize('NFC', v.lower())
    v = re.sub(r'[₀-₉0-9ₓ]', '', v)
    tr = {'š': 's', 'ṣ': 's', 'ṭ': 't', 'ḫ': 'h', 'ŋ': 'n', 'ʾ': '', "'": '', 'ā': 'a', 'â': 'a', 'ē': 'i', 'ê': 'i', 'e': 'i',
          'ī': 'i', 'î': 'i', 'ū': 'u', 'û': 'u', 'o': 'u', 'q': 'k', 'z': 's', 'w': 'v', 'y': 'i', 'j': 'i', 'g̃': 'n'}
    out = ''.join(tr.get(c, c) for c in v)
    return ''.join(c for c in out if c in 'aiukgcjtdnpbmyrlvsh')
def walk(n, acc):
    if isinstance(n, dict):
        if n.get('node') == 'l': acc.append(n); return
        for v in n.values(): walk(v, acc)
    elif isinstance(n, list):
        for v in n: walk(v, acc)
def graphemes(g, acc, det=False):
    """flatten gdl into list of (glyph, kind, value, missing)"""
    for x in g:
        if 'det' in x:
            graphemes(x.get('seq', []), acc, det=True); continue
        if 'group' in x: graphemes(x['group'], acc, det); continue
        if 'seq' in x and 'v' not in x and 's' not in x and 'n' not in x: graphemes(x['seq'], acc, det); continue
        miss = x.get('break') == 'missing'
        glyph = x.get('utf8') or x.get('s') or x.get('v') or x.get('form') or '?'
        if det: kind = 'det'
        elif x.get('n') == 'n' or 'sexified' in x: kind = 'num'
        elif x.get('role') == 'logo' or ('s' in x and 'v' not in x): kind = 'logo'
        elif 'v' in x: kind = 'syll'
        else: kind = 'other'
        acc.append((glyph, kind, x.get('v', ''), miss))
def build_akkadian(zips, name):
    texts, nwords, nbroken = [], 0, 0
    for zp, sub in zips:
        z = zipfile.ZipFile(f'{PC}/data/oracc/{zp}')
        for fn in sorted(x for x in z.namelist() if '/corpusjson/' in x):
            raw = z.read(fn)
            if not raw.strip(): continue
            d = json.loads(raw); L = []; walk(d, L)
            lines = collections.OrderedDict()
            for l in L:
                ref = l.get('ref', ''); line = ref.rsplit('.', 1)[0]
                f = l.get('f', {}); nwords += 1
                g = []; graphemes(f.get('gdl', []), g)
                norm = f.get('norm') or f.get('cf')
                bad = (not g) or any(m for *_, m in g) or not norm or f.get('lang', '').startswith('sux') or any(k == 'other' for _, k, _, _ in g)
                if bad:
                    nbroken += 1; lines.setdefault(line, []).append(None); continue
                has_logo = any(k == 'logo' for _, k, _, _ in g)
                word, first = [], True
                for glyph, kind, v, _ in g:
                    if has_logo:
                        val = red_akk(norm) if (kind == 'logo' and first) else ''
                        if kind == 'logo': first = False
                    else:
                        val = red_akk(v) if kind == 'syll' else ''
                    word.append([glyph, val])
                lines.setdefault(line, []).append(word)
            # split each line into maximal runs of good words
            for line, ws in lines.items():
                run = []
                for w in ws + [None]:
                    if w is None:
                        if run:
                            signs = [s for ww in run for s, _ in ww]; vals = [v for ww in run for _, v in ww]
                            starts, p = [], 0
                            for ww in run: starts.append(p); p += len(ww)
                            texts.append(dict(signs=signs, values=vals, word_starts=starts, src=fn.split('/')[-1][:-5] + ':' + line, whole_line=len(run) == len(ws)))
                        run = []
                    else: run.append(w)
    json.dump(texts, open(f'{OUT}/{name}.json', 'w'))
    print(name, len(texts), 'line-runs', sum(len(t['signs']) for t in texts), 'graphemes', len(set(s for t in texts for s in t['signs'])), 'glyph types', f'words {nwords} excluded(broken/unlemmatised/Sumerian) {nbroken}')
def akk_lexicon(zips, name):
    cf, norms = set(), set()
    for zp in zips:
        z = zipfile.ZipFile(f'{PC}/data/oracc/{zp}')
        for fn in z.namelist():
            if re.search(r'gloss-(akk[^/]*|qpn)\.json$', fn):
                g = json.loads(z.read(fn))
                for e in g.get('entries', []):
                    if e.get('cf'): cf.add(red_akk(e['cf']))
                    for n in e.get('norms', []) or []:
                        if n.get('n'): norms.add(red_akk(n['n']))
    coll = lambda s: re.sub(r'(.)\1+', r'\1', s)
    cf = sorted({coll(w) for w in cf if w}); norms = sorted({coll(w) for w in norms if w})
    json.dump(dict(citation_forms=cf, norms=norms), open(f'{OUT}/{name}.json', 'w'))
    print(name, 'citation forms', len(cf), 'norm forms', len(norms))

if __name__ == '__main__':
    build_sanskrit()
    build_akkadian([('saao-saa01.zip', 'saa01'), ('saao-saa05.zip', 'saa05')], 'akkadian_NA_letters')
    akk_lexicon(['saao-saa01.zip', 'saao-saa05.zip', 'saao-saa10.zip', 'rinap-rinap4.zip'], 'akk_lexicon_insample')
    akk_lexicon(['saao-saa10.zip', 'rinap-rinap4.zip'], 'akk_lexicon_heldout')
