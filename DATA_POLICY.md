# Data policy: what is in this repository, what is not, and why

Rule: we publish code, our own text, and **derived statistics** (sign IDs with counts, test statistics, model scores). We do **not** publish transcribed corpora, scans, OCR or glyph images whose rights holders have not licensed them for redistribution.

## Excluded (restricted)

| Input | Why it is excluded | How to obtain it |
|---|---|---|
| M77 machine-readable export (`joyboseroy/indus_decipher`, `m77_indusscript_real_corpus.csv`) | Mahadevan 1977 is © Archaeological Survey of India. The repo is MIT-licensed, but its converter docstring says the data was extracted from indusscript.in through a logged-in session, so the rights are unclear. | `scripts/fetch_data.sh` clones it into `data/` (not committed). Your use is your responsibility. |
| *lipi* (`yajnadevam/lipi`): ICIT-derived inscription texts, sign key (`xlits.csv`), readings | The repository has no licence, and the ICIT database (Wells & Fuls) is not open. | Cloned by `fetch_data.sh`. |
| `field-cady/indus_valley_script_corpus` copy of the lipi data | MIT-licensed, but derived from lipi (no licence). We redistribute only the Field-Cady optimal-transport mapping values in `all_proposals_public.csv` (MIT). | Cloned by `fetch_data.sh`. |
| Yajnadevam/lipi sign-value key | No licence. Values are redacted in `outputs/claims/all_proposals_public.csv`, `outputs/structure/sign_table_public.csv`, `outputs/signmap/sign_map_full_public.csv` and the manuscript appendix. The per-sign test statistics are kept. | lipi `xlits.csv` |
| Scans and OCR of Mahadevan 1977 (MASI 77) and Parpola 1994 (CUP) | In copyright. Includes our OCR derivatives: `outputs/m77_codes*.csv` (object codes), `outputs/m77_field_symbols.csv`. | Obtain the books lawfully. The OCR scripts (`ocr_m77_*.py`, `parse_m77_*.py`, `m77_digits*.py`) re-create the derivatives from your own copy. |
| Plate and sign-list crops (`paper/evidence/glyphs/`, Mahadevan 2015 chart crops, Parpola Fig. 15.2 crops) | Copyright: ASI, RMRL, CUP. | Re-create with `m77_glyph_crops.py` from your own copy. |
| SK Indus Script font renders (`glyphs_W/`) | The font is "All Rights Reserved". | `render_w_glyphs.py`, using the font from yajnadevam/indus-website |
| Manuscript figures 7 and 8 | Built from the crops and renders above. | Omitted from `manuscript_public.pdf`. |
| SQLite map `map/indus_map.sqlite` | Contains the corpora. | Rebuild with `scripts/build_map.py` after fetching. |
| 3- and 4-gram counts and branching-entropy segments for real corpora (`ngrams_3/4.csv`, `segments_branching_entropy.csv`) | With a mean text length of about 4, long n-grams with counts reconstruct many complete texts. We excluded them as a precaution; unigram, positional and bigram tables are included. | Re-run `scripts/structure.py`. |
| `outputs/claims/A_reproduction.csv`, `A_substitutions.csv` | Contain Yajnadevam's per-inscription readings (lipi). | Re-run `claim_harness.py`. |
| Complete ICIT texts of 4 or more signs quoted as examples in `outputs/anchors/anchors_summary.json` and `w700_vs_weights.json` | These are transcribed lipi texts. They are replaced by "[ICIT text of N signs redacted]"; counts are kept. | Re-run `anchors.py`. |
| `outputs/comparanda/sim_matrix.npy` | 10 MB, derived from the M77 crops. Omitted for size and provenance. | Re-run `lookalikes.py`. |
| Copyrighted paper PDFs used for the literature review | Not ours to redistribute. | Citations in the manuscript; open URLs in `scripts/fetch_data.sh`. |

## Included

- **Derived statistics from restricted corpora:** sign frequencies, positional profiles, bigram counts, class tables, concordance scores, leave-one-out test statistics, replication results. These are facts about the corpora, not the corpora themselves.
- **Sign descriptions:** in `sign_classes_M77.csv` and `sign_map_full_public.csv`, from M. Carlson's `mayig/indus-valley-script-corpus` (MIT).
- **`data_open/images/met/`:** Metropolitan Museum Open Access, CC0.
- **`data_open/images/commons/`:** Wikimedia Commons; each file keeps its own licence (CC0, PD, CC BY, CC BY-SA). See ATTRIBUTION.md. These files are not covered by the MIT or CC BY grants.
- **`positive_control/data_open/m77_line_length_distribution.json`:** counts of M77 line lengths only (aggregate; no texts).
- **`data_open/toy/`:** a hand-made toy corpus (ours, CC BY 4.0).

## Openly licensed inputs fetched, not committed

| Input | Licence | Note |
|---|---|---|
| Dravidian Database v1.2 (Merriam & Fuls 2026), Zenodo 22682542 | CC BY 4.0 | Fetched rather than committed because of size (29 MB). Cite it if used. |
| `weights.xml` (Sproat, Indus weights from Hemmy and HARP) | **GPL-3** | Fetched, not committed. Our `w700_weights.py` only reads it, and our outputs are statistics, so we do not think GPL applies to this repo. If you redistribute `weights.xml` with the code, that file stays GPL-3. |
| yajnadevam/indus-website (ICIT-style texts, SK font) | **GPL-3** code; font All Rights Reserved | Read only. Nothing is copied into this repo. |
| isramos/indus-script-sign-merging | **GPL-3** | Consulted only. No code copied. |
| Digital Corpus of Sanskrit (O. Hellwig), 517 CoNLL-U files (session 7 positive control) | CC BY 4.0 | Fetched by `fetch_data.sh`, pinned to commit 8aeed5a and checked against `positive_control/data_open/dcs_SHA256SUMS`. Cite Hellwig, DCS. |
| ORACC JSON: SAAo SAA 1, 5, 10 and RINAP 4 (session 7 positive control) | CC0 per each file's metadata; ORACC site licence CC BY-SA 3.0 | Fetched, not committed. We credit ORACC and the volume editors (Parpola; Lanfranchi & Parpola; Leichty). Downloaded with `curl -k` because the server omits its intermediate certificate, so integrity rests on `positive_control/data_open/oracc_SHA256SUMS`. |
| elamicon (Linear Elamite glyphs) | **GPL-2** | Glyphs were rendered for private comparison only. Rendered images are not committed. |
| Noto fonts | SIL OFL 1.1 | Fetched |
| csl-orig Monier-Williams | CC BY-SA 4.0 | Fetched |
| FrequencyWords | MIT code; content CC BY-SA 4.0 | Fetched |
| vidyut data | MIT | `vidyut.download_data` |
| Wikipedia random-page text (comparanda) | CC BY-SA 4.0 | `fetch_wiki.py`. Text is not committed. |

**GPL note.** No GPL code is copied into this repository. Our scripts only read GPL-licensed data files at run time, so MIT for code and CC BY 4.0 for results is consistent. If a GPL-3 file is later bundled, it must keep its GPL licence. Bundling GPL code would require GPL for the combined work.

## Before pushing

Run `python tools/check_public.py`. It fails if a restricted file name, path, glyph image, font, or a long run of corpus-like sign sequences appears in tracked files.
