"""Scan the repository for restricted files and patterns. Exit 1 if anything is found.
Checks: forbidden paths and names; image files outside the allowed folders; fonts; SQLite; restricted file names;
lipi/Yajnadevam key-value patterns; long corpus-like sign sequences (>= 6 consecutive sign IDs on one line, which
would indicate transcribed texts); M77 OCR markers; Parpola OCR; files over 5 MB."""
import os, re, sys, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    files = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split('\n')
except Exception:
    files = [os.path.relpath(os.path.join(d, f), ROOT) for d, _, fs in os.walk(ROOT) if '.git' not in d for f in fs]
files = [f for f in files if f]
SELF = {'tools/check_public.py', '.gitignore', 'DATA_POLICY.md', 'tools/build_public_repo.py'}
bad = []
FORBID_PATH = [r'(^|/)data/', r'paper/evidence', r'glyphs(_W)?/', r'mahadevan2015/', r'parpola_fig15_2/', r'_private', r'\.sqlite$',
               r'outputs/m77_codes', r'outputs/m77_field_symbols', r'A_reproduction', r'A_substitutions', r'(^|/)all_proposals\.csv$',
               r'(^|/)sign_map_full\.csv$', r'(^|/)sign_table\.(csv|md)$', r'handcheck_montage', r'sim_matrix', r'\.(ttf|otf|woff2?)$',
               r'inscriptions\.csv$', r'xlits\.csv$', r'm77_indusscript', r'indus_website_real_corpus', r'cisi_real_corpus', r'ocr_m77/', r'ocr_parpola',
               r'_djvu\.txt$', r'(?<!TOY)/ngrams_[34]\.csv$', r'(?<!TOY)/segments_branching_entropy\.csv$', r'\.pdf$(?<!manuscript_public\.pdf)']
IMG_OK = ('data_open/images/', 'paper/figures/')
SIGN = r'(?:M\d{3}|W\d{3}|MSg\d+|P\d{3})'
SEQ = re.compile(rf'{SIGN}(?:[ \t-]+{SIGN}){{5,}}')  # space/hyphen-joined runs = transcribed texts
RAWNUM = re.compile(r'\b\d{3}(?:[ -]\d{3}){5,}\b|[+\]\[]\d{3}(?:-\d{3}){3,}')  # lipi/ICIT raw form
TEXT_PATTERNS = [(re.compile(r'Sanskrit syllabic value\(s\) W\d'), 'lipi key value'),
                 (re.compile(r'\bW\d{3}=[a-zA-Z]{1,4}\b(?!\d)(?=[ ,;|]|$)(?!.*Carlson)'), 'lipi-style W=value'),
                 (re.compile(r'Suomalainen Tiedeakatemia|MEMOIRS OF THE ARCHAEOLOGICAL SURVEY'), 'book OCR text'),
                 (SEQ, 'long sign sequence (corpus-like)'), (RAWNUM, 'raw ICIT-style number run')]
for f in files:
    p = os.path.join(ROOT, f)
    if not os.path.isfile(p): continue
    for pat in FORBID_PATH:
        if re.search(pat, f): bad.append((f, f'forbidden path /{pat}/')); break
    if re.search(r'\.(png|jpe?g|gif|tiff?|svg|webp)$', f, re.I) and not f.startswith(IMG_OK): bad.append((f, 'image outside allowed folders'))
    if os.path.getsize(p) > 5_000_000: bad.append((f, 'file > 5 MB'))
    if f in SELF or not re.search(r'\.(csv|md|txt|json|py|sh|cff|html|yml|yaml)$', f): continue
    try: txt = open(p, encoding='utf-8', errors='ignore').read()
    except Exception: continue
    for rx, what in TEXT_PATTERNS:
        for line in txt.splitlines():
            if rx.search(line) and not (what.startswith('lipi-style') and 'Carlson' in line):
                bad.append((f, f'{what}: {line[:90]!r}')); break
if bad:
    print('RESTRICTED CONTENT FOUND:'); [print(' -', f, '|', w) for f, w in bad]; sys.exit(1)
print(f'clean: {len(files)} files checked, no restricted files or patterns found')
