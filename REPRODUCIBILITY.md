# Reproducing the analyses

Tested on Linux with Python 3.13 (box environment, 29 Oct 2026, IST). Seeds are fixed in every script, so outputs should match to rounding. The HMM and BPE fits use hmmlearn and numpy random states.

## 1. Environment

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

## 2. Inputs

```bash
bash scripts/fetch_data.sh
```

This creates `data/`, which is git-ignored. Restricted items need your own lawful copy; see `DATA_POLICY.md`.

| Analysis | Needs |
|---|---|
| Structure, classes, segmentation, entropy (`structure*.py`, `nsb_entropy.py`) | M77 export, lipi `inscriptions.csv`; object types from `outputs/m77_codes_digitocr.csv`, which needs your own MASI 77 scan + `m77_digits*.py` |
| Session-5 replications (`compare_replications.py`, `compare_sigil_hmm.py`) | M77 export, lipi texts, M77 object codes (as above) |
| Claims harness and LOO (`claim_harness.py`, `rebus_harness.py`, `claims_table.py`, `loo_signs.py`, `loo_hand.py`) | lipi `xlits.csv`, Field-Cady mapping, Dravidian DB, csl-orig MW, FrequencyWords, vidyut |
| Concordance and sign map (`concordance.py`, `sign_map_full.py`) | mayig corpus, M77 crops (`m77_glyph_crops.py` from your scan), SK font renders (`render_w_glyphs.py`) |
| Look-alikes (`render_comparanda.py`, `lookalikes.py`) | Noto fonts, elamicon, M77 crops |
| Anchors (`anchors.py`, `w700_weights.py`) | weights.xml, lipi texts |
| Map DB (`build_map.py`) | all of the above; schema and seed tables ship in `map/` |
| Pre-registered held-out tests, robustness (`prereg_heldout.py`, `robustness_schemes.py`) | M77 export, lipi texts, mayig corpus, isramos merge file (GPL-3) |
| Non-linguistic comparison (`emblem_tests.py`) | Sproat corpora (fetched; Apache-2.0), M77 export, lipi texts, Wikipedia comparanda (`fetch_wiki.py --pages`) |
| Short-text comparanda and classifier stability (`emblem_tests2.py`, session 7) | everything `emblem_tests.py` needs, plus the EDH CSV (fetched; CC BY-SA 4.0) and `data_open/comparanda_short/wiki_titles_*.txt` (shipped; CC BY-SA 4.0) |
| Shuffle-test positive control (`positive_control/scripts/pc_*.py`, session 7) | DCS CoNLL-U (fetched, CC BY 4.0, SHA-256 checked against `positive_control/data_open/dcs_SHA256SUMS`), ORACC SAAo/RINAP JSON (fetched, CC0 per metadata, SHA-256 checked), vidyut data, *lipi* texts and key (Indus row only), M77 line-length distribution (shipped, aggregate only) |
| Strict look-alike controls (`lookalikes_strict.py`, session 7) | M77 plate crops and SK-font W renders (private), elamicon glyphs, Noto fonts (fetched; OFL) |
| Benchmark (`bench_score.py`) | lipi texts, the lexicons above |
| Open sign list (`open_signlist.py`) | only files in this repository |

## 3. Order

```text
build_map.py → structure.py → structure2.py → structure3_dedup.py → structure_ling.py → sign_table.py
claim_harness.py → rebus_harness.py → parse_test_vidyut.py → anchors.py → w700_weights.py
m77_glyph_crops.py → render_w_glyphs.py → glyphsim.py → concordance.py → concordance_relabel.py
claims_table.py → loo_signs.py → loo_global_calibration.py → loo_hand.py → structure4_be.py → nsb_entropy.py
render_comparanda.py → lookalikes.py → sign_map_full.py → make_figures.py
compare_replications.py → compare_sigil_hmm.py → prior_work_matrix.py
prereg_heldout.py → robustness_schemes.py → emblem_tests.py → bench_score.py → open_signlist.py
run_claim_seeds.sh → seed_spread.py
run_claim_seeds_extra.sh 5 19 49 → seed_claims_extended.py      (session 7: 20 LOO / 50 rebus replicates)
lookalikes_strict.py → h7_posthoc.py → emblem_tests2.py            (session 7)
positive_control/scripts/pc_data.py → pc_run.py → pc_summary.py   (session 7 positive control)
```

`run_all.py` runs the early pipeline. `scripts/indus_lib.py` holds the shared loaders and measures. After `loo_signs.py`, run `loo_global_calibration.py` to add the global calibration block to `outputs/claims/loo_phonetic_summary.json`.

## 4. Checks against the committed outputs

| Quantity | File | Value |
|---|---|---|
| Concordance top-1 (5-fold CV) | `outputs/signmap/concordance_accuracy.json` | 0.847 |
| HMM gain, dedup seals (K = 5) | `outputs/structure/structure3_dedup.json` | about 0.38 nats/token |
| Yadav-style bigram perplexity, M77 dedup | `outputs/compare/replications.json` | 31.33 |
| Nair-style H_cond, ICIT dedup undamaged | same | 3.433 bits |

## 4a. Fresh-clone check (29 October 2026, IST)

We cloned this repository into an empty directory, built a new virtual environment from `requirements.txt` (Python 3.13.5), ran `scripts/fetch_data.sh`, then ran each script. Result:

| Script(s) | From a fresh clone | Matches the committed outputs? |
|---|---|---|
| `tests/smoke_test.py` | runs (offline, no data needed) | yes, exactly |
| `run_all.py`, `run_all.py --toy` | runs | yes, byte-identical (`outputs/M77`, `icitweb`, `cisi_mayig`, `TOY`, `summary*.json`) |
| `prior_work_matrix.py` | runs | yes |
| `loo_global_calibration.py --check` | runs | yes, exactly (all 40 conditions and the Mann–Whitney p) |
| `claim_harness.py`, `rebus_harness.py`, `parse_test_vidyut.py`, `loo_signs.py` | run | session 5: only partly (hash-order dependence, see below). Session 6: deterministic; two runs under `PYTHONHASHSEED` = 1 and 2 give byte-identical outputs |
| `anchors.py`, `w700_weights.py` | run | yes, except that a local run writes the full ICIT texts that the committed files redact. **Do not commit those files**; `tools/check_public.py` flags them |
| `build_map.py`, `sign_table.py`, `claims_table.py`, `loo_hand.py` | run (session 7 fresh clone of ff98449, empty environment). `build_map.py` now imports the 88 Commons/Met images from `data_open/images/*/manifest.csv` | `sign_table.py`, `claims_table.py`, `loo_hand.py`: byte-identical. The map differs from the private one only where restricted inputs add rows (sources 61 vs 79; sites 52 vs 55, because Chanhu-daro and the M77 OS/WA classes come from the restricted OCR; leads 0 by design) |
| `structure*.py`, `nsb_entropy.py`, `compare_replications.py`, `compare_sigil_hmm.py` | **do not run**: they need `outputs/m77_codes_digitocr.csv`, the M77 object-type codes, which come from OCR of the printed Mahadevan 1977 concordance and are not redistributed | – |
| concordance, glyph and look-alike scripts | need the M77 plate crops (your own scan) and the SK font | – |

**Determinism and seed spread (fixed in session 6).** Earlier versions iterated over Python sets of strings and used `hash()`, so the Markov-nonsense control lexicon and the fitted rebus keys changed with Python's per-process hash seed. Session 6 sorts before sampling and derives seeds with `zlib.crc32`; reruns are now byte-identical under any `PYTHONHASHSEED`. The canonical run (replicate 0) changed 33 of 173 tracked metrics relative to the session-5 committed values. All are control values; the published-key values are unchanged. Examples: Markov-nonsense fixed-key segmentability 0.863 → 0.786, fitted Dravidian rebus key 0.073 → 0.068, Markov-nonsense rebus key 0.107 → 0.089. `scripts/run_claim_seeds.sh` reruns parts B, C, the rebus fits and the per-sign LOO for replicates 1–4 (`INDUS_LEXSEED=k`), and `scripts/seed_spread.py` writes the canonical value, mean, min and max of every metric, with the session-5 value alongside, to `outputs/claims/seed_spread.csv`. The spread is substantial for the fitted keys: e.g. the Dravidian rebus score is 0.068–0.157 over five seeds, and the one-sided Mann–Whitney p for Yajnadevam vs the shuffle-fitted key is 0.004–0.99. See manuscript §4.6 and §4.9.

**Session 7.**
- `scripts/run_claim_seeds_extra.sh 5 19 49` adds two sets of replicates: replicates 5–19 of the rebus fits and per-sign LOO, and replicates 20–49 of the rebus fits only.
  - It takes about 3 minutes per LOO replicate and about 10 seconds per rebus-only replicate.
  - It writes to `outputs/claims/seeds/s<k>/`, which is not committed.
  - `scripts/seed_claims_extended.py` summarises the replicates with medians and 2.5–97.5% intervals in `outputs/claims/seed_claims_extended.json`.
- `anchors.py` previously re-drew its Gulf bigram null on every run. It is now seeded (`random.seed(0)`): the null mean is 0.796 (0.687–0.885), where earlier runs gave about 0.793 (0.681–0.901).
- `lookalikes_strict.py` is deterministic: two runs gave identical JSON. It needs the private plate crops and W-font renders, so it does not run from a fresh clone.
- `h7_posthoc.py` needs the ICIT data, which `fetch_data.sh` fetches.
- **Positive control.** `fetch_data.sh` downloads the 517 DCS files, pinned to commit 8aeed5a, and the four ORACC zips into `positive_control/data/`, then checks them against the SHA-256 lists shipped in `positive_control/data_open/`.
  - **TLS caveat:** the ORACC server does not send its intermediate certificate, so the original download used `curl -k` (no certificate verification). `fetch_data.sh` tries a verified download first and falls back to `-k`. Integrity therefore rests on the SHA-256 check, not on TLS.
  - From freshly fetched files, `pc_data.py` rebuilt all five corpora byte-identically on 29 October 2026.
  - `pc_run.py` (200/200/100 nulls at seed 0, 50/50/20 at seeds 1–4) is slow. It was not re-run in the fresh-clone check.
- `emblem_tests2.py` needs the EDH CSV (fetched by `fetch_data.sh`) and the saved Wikipedia title samples in `data_open/comparanda_short/`. Like `emblem_tests.py`, it also needs the M77 export. Reruns from the saved samples are byte-identical.

`lookalikes.py` also used `hash()` for its control draws. After the fix only the random-control columns move (by under 0.012 in the share of signs above control); the category tests and the Mantel test are unchanged.

`scripts/fetch_data.sh` now copies the *lipi* data files into the flat `data/lipi/` folder that the scripts read. It also downloads the Dravidian DB files from Zenodo and checks their checksums. Earlier versions left both steps to the user.

## 5. Manuscript

```bash
cd paper
python -c "import pypandoc; pypandoc.convert_file('manuscript_public.md','html',format='markdown',outputfile='manuscript_public.html',extra_args=['--standalone','--embed-resources','--css=style.css','--metadata','lang=en'])"
google-chrome --headless --no-sandbox --disable-gpu --no-pdf-header-footer --print-to-pdf=manuscript_public.pdf manuscript_public.html
```

## Known differences

- Our EBUDS-like corpus has 1,849 texts against Yadav's 1,548, because their damage filter was stricter.
- Our ICIT dedup has 2,273 texts against Nair's 1,916.
- Fuls' positional formula is approximated (abstract only).
