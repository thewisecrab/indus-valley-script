#!/usr/bin/env bash
# Fetch the inputs this project reads into ./data (git-ignored). Run from the repo root.
# Openly hosted sources are downloaded. Restricted ones are cloned only where the upstream host serves them
# publicly; check each upstream licence yourself (see DATA_POLICY.md). Books are NOT downloaded.
set -euo pipefail
mkdir -p data && cd data
clone () { # url dir commit
  [ -d "$2/.git" ] || git clone --quiet "$1" "$2"
  [ -n "${3:-}" ] && git -C "$2" checkout --quiet "$3" || true
  echo "ok  $2 ($(git -C "$2" rev-parse --short HEAD))"
}
# --- corpora (restricted terms: private research use; do not redistribute) ---
clone https://github.com/joyboseroy/indus_decipher joyboseroy_indus_decipher cd60034        # M77 export: ASI copyright
clone https://github.com/yajnadevam/lipi lipi_repo fc8813a                                  # no licence; ICIT-derived
# the scripts read a flat data/lipi/ folder (as in the original analysis); copy the needed files out of the app tree
mkdir -p lipi
for f in src/assets/data/{inscriptions.csv,xlits.csv,decipher.csv,words.csv,lexicons.json,synonym_groups.json,unknown.txt,Notes.txt} \
         glossing.csv src/pages/index.vue src/scripts/index/filter.js; do cp "lipi_repo/$f" lipi/; done
echo "ok  lipi/ (flat copy of lipi_repo data files)"
clone https://github.com/field-cady/indus_valley_script_corpus field-cady_indus_valley_script_corpus 3030826
clone https://github.com/yajnadevam/indus-website yajnadevam_indus-website 2434249          # GPL-3; SK font All Rights Reserved
# --- open ---
clone https://github.com/mayig/indus-valley-script-corpus mayig_indus-valley-script-corpus ad2f1e2   # MIT
clone https://github.com/isramos/indus-script-sign-merging isramos_indus-script-sign-merging 0759bd6  # GPL-3
clone https://github.com/elamicon/elamicon elamicon_repo 69b4cc2                              # GPL-2
mkdir -p weights lexicons fonts_open zenodo/dravidian_db_22682542 vidyut toy ../map
curl -sfL https://richardsproat.com/indus_weights/weights.xml -o weights/weights.xml && echo "ok  weights/weights.xml (GPL-3)"
curl -sfL https://raw.githubusercontent.com/sanskrit-lexicon/csl-orig/master/v02/mw/mw.txt -o lexicons/mw.txt && echo "ok  lexicons/mw.txt (CC BY-SA 4.0)"
for l in en fi tr id hu; do
  curl -sfL "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/$l/${l}_50k.txt" -o "lexicons/freq_$l.txt" && echo "ok  lexicons/freq_$l.txt (CC BY-SA 4.0)"
done
for f in NotoSansBrahmi NotoSansCuneiform NotoSansEgyptianHieroglyphs NotoSansLinearA NotoSansCyproMinoan NotoSansLinearB NotoSansAnatolianHieroglyphs NotoSansPhoenician NotoSansOldPersian; do
  curl -sfL "https://github.com/notofonts/notofonts.github.io/raw/main/fonts/$f/hinted/ttf/$f-Regular.ttf" -o "fonts_open/$f-Regular.ttf" && echo "ok  fonts_open/$f-Regular.ttf (SIL OFL 1.1)" || echo "    get $f-Regular.ttf from https://github.com/notofonts (OFL) into data/fonts_open/"
done
# Dravidian DB v1.2 (CC BY 4.0), Zenodo record 22682542: fetch the files the scripts read and verify Zenodo's md5 checksums
python - <<'PY' || echo "    Dravidian DB: download the files of https://zenodo.org/records/22682542 into data/zenodo/dravidian_db_22682542/"
import hashlib, json, urllib.request
D = "zenodo/dravidian_db_22682542"; WANT = {"README.md", "Wordlist-metadata.json", "dedr_entry_v11.csv", "forms.csv", "languages.csv", "parameters.csv", "pdr_04.csv"}
rec = json.load(urllib.request.urlopen("https://zenodo.org/api/records/22682542"))
for f in rec["files"]:
    if f["key"] not in WANT: continue
    b = urllib.request.urlopen(f["links"]["self"]).read()
    algo, want = f["checksum"].split(":", 1)
    assert hashlib.new(algo, b).hexdigest() == want, f["key"] + " checksum mismatch"
    open(f"{D}/{f['key']}", "wb").write(b)
print("ok  " + D + " (CC BY 4.0, checksums verified)")
PY
python - <<'PY' || echo "    vidyut data: run python -c \"import vidyut; vidyut.download_data('data/vidyut')\""
import vidyut; vidyut.download_data('vidyut'); print('ok  vidyut data (MIT)')
PY
cp ../data_open/toy/toy_corpus.csv toy/ 2>/dev/null || true
# Sproat (2014) non-linguistic symbol corpora (Apache-2.0), used by scripts/emblem_tests.py
mkdir -p sproat_nonling && ( cd sproat_nonling && curl -sfLO https://richardsproat.com/data/non-linguistic-symbols/corpora.zip && unzip -o -q corpora.zip && echo "ok  sproat_nonling/corpora (Apache-2.0)" ) || echo "    get corpora.zip from https://richardsproat.com/data/non-linguistic-symbols/ into data/sproat_nonling/"
# Epigraphic Database Heidelberg inscriptions (CC BY-SA 4.0; database frozen since Dec 2021), used by emblem_tests2.py.
# The Wikipedia title samples used there ship in data_open/comparanda_short/ (CC BY-SA 4.0).
mkdir -p comparanda_short && curl -sfL https://edh.ub.uni-heidelberg.de/data/download/edh_data_text.csv -o comparanda_short/edh_data_text.csv && echo "ok  comparanda_short/edh_data_text.csv (EDH, CC BY-SA 4.0)" || echo "    get edh_data_text.csv from https://edh.ub.uni-heidelberg.de/data/download into data/comparanda_short/"
# Wikipedia comparanda text (CC BY-SA 4.0), used by emblem_tests.py and structure_ling.py
( cd .. && python scripts/fetch_wiki.py --pages >/dev/null 2>&1 && echo "ok  comparanda_text (Wikipedia, CC BY-SA 4.0)" ) || echo "    run python scripts/fetch_wiki.py --pages"
# --- session 7 positive control (positive_control/): correct keys for deciphered scripts ---
mkdir -p ../positive_control/data/oracc && cp ../positive_control/data_open/m77_line_length_distribution.json ../positive_control/data_open/dcs_SHA256SUMS ../positive_control/data/ && cp ../positive_control/data_open/oracc_SHA256SUMS ../positive_control/data/oracc/SHA256SUMS
# Digital Corpus of Sanskrit (O. Hellwig; CC BY 4.0): the exact 517 CoNLL-U files listed, with SHA-256, in
# positive_control/data_open/dcs_SHA256SUMS (Manusmrti 12, Hitopadesa 5, Rgveda 500 = RV 1.1-6.59), pinned to commit 8aeed5a.
python - <<'PY' || echo "    DCS: see positive_control/README.md"
import hashlib, os, urllib.parse, urllib.request
D = '../positive_control/data/dcs'; BASE = 'https://raw.githubusercontent.com/OliverHellwig/sanskrit/8aeed5a1343d0e48b64eb32af8c00e8c6eb29359/dcs/data/conllu/files/'
bad = 0
for line in open('../positive_control/data/dcs_SHA256SUMS', encoding='utf-8'):
    h, rel = line.rstrip('\n').split('  ', 1); out = f'{D}/{rel}'
    if not (os.path.exists(out) and hashlib.sha256(open(out, 'rb').read()).hexdigest() == h):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        b = urllib.request.urlopen(BASE + urllib.parse.quote(rel)).read(); open(out, 'wb').write(b)
    bad += hashlib.sha256(open(out, 'rb').read()).hexdigest() != h
print(f'ok  positive_control/data/dcs (DCS, CC BY 4.0; {bad} checksum mismatches)')
PY
# ORACC JSON (CC0 per each file's metadata; ORACC site licence CC BY-SA 3.0): SAAo SAA 1, 5, 10 and RINAP 4.
# CAVEAT: the ORACC server does not send its intermediate TLS certificate (InCommon RSA Server CA 2), so plain curl
# fails certificate verification. We downloaded with `curl -k` (verification DISABLED) and check the files against the
# SHA-256 values in positive_control/data_open/oracc_SHA256SUMS instead. If your system has that intermediate installed,
# drop the -k.
( mkdir -p ../positive_control/data/oracc && cd ../positive_control/data/oracc && \
  for z in saao-saa01 saao-saa05 saao-saa10 rinap-rinap4; do
    [ -f "$z.zip" ] || curl -sfL --retry 2 "https://oracc.museum.upenn.edu/json/$z.zip" -o "$z.zip" || curl -sfLk --retry 2 "https://oracc.museum.upenn.edu/json/$z.zip" -o "$z.zip"
  done && grep -E 'saao-saa0[15]|saao-saa10|rinap-rinap4' SHA256SUMS | sha256sum -c --quiet - && echo "ok  positive_control/data/oracc (ORACC; SHA-256 verified)" ) \
  || echo "    ORACC: download saao-saa01/05/10 and rinap-rinap4 .zip from https://oracc.museum.upenn.edu/json/ into positive_control/data/oracc/ and check SHA256SUMS"
cat <<'MSG'

Restricted inputs that are NOT fetched (obtain lawfully; see DATA_POLICY.md):
  - Mahadevan 1977, The Indus Script: Texts, Concordance and Tables (MASI 77), (c) ASI. Needed for object types,
    plate crops and the M77 OCR scripts. Place the PDF under data/books/masi77/ and adjust the paths in ocr_m77_*.py.
  - Parpola 1994, Deciphering the Indus Script, (c) CUP. Used only for page-cited claims (already in the claims table).
MSG
