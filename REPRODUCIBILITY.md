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
| Map DB (`build_map.py`) | all of the above |

## 3. Order

```text
build_map.py → structure.py → structure2.py → structure3_dedup.py → structure_ling.py → sign_table.py
claim_harness.py → rebus_harness.py → parse_test_vidyut.py → anchors.py → w700_weights.py
m77_glyph_crops.py → render_w_glyphs.py → glyphsim.py → concordance.py → concordance_relabel.py
claims_table.py → loo_signs.py → loo_global_calibration.py → loo_hand.py → structure4_be.py → nsb_entropy.py
render_comparanda.py → lookalikes.py → sign_map_full.py → make_figures.py
compare_replications.py → compare_sigil_hmm.py → prior_work_matrix.py
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
| `claim_harness.py`, `rebus_harness.py`, `parse_test_vidyut.py`, `loo_signs.py` | run | published-key results and the natural-language lexicon results of parts B, C and LOO match; **every Markov-nonsense control, and the fitted rebus keys of `rebus_harness.py` for all lexicons, vary from run to run** (see below) |
| `anchors.py`, `w700_weights.py` | run | yes, except that a local run writes the full ICIT texts that the committed files redact. **Do not commit those files**; `tools/check_public.py` flags them |
| `build_map.py`, `sign_table.py`, `claims_table.py`, `loo_hand.py` | **do not run**: they need the SQLite map, whose schema and seed tables are not yet in this repository | – |
| `structure*.py`, `nsb_entropy.py`, `compare_replications.py`, `compare_sigil_hmm.py` | **do not run**: they need `outputs/m77_codes_digitocr.csv`, the M77 object-type codes, which come from OCR of the printed Mahadevan 1977 concordance and are not redistributed | – |
| concordance, glyph and look-alike scripts | need the M77 plate crops (your own scan) and the SK font | – |

**Run-to-run variation (known issue).** The Markov-nonsense control lexicon and the fitted rebus keys depend on Python's per-process string-hash order (the code iterates over sets of strings). Different runs therefore give slightly different control values. For example, fixed-key segmentability for the Markov-nonsense lexicon was 0.863 in the committed run and 0.76–0.91 across reruns with `PYTHONHASHSEED` = 0 and 1. The real-corpus, published-key values do not change. In our fresh-clone rerun the fitted rebus scores moved by up to about 0.02 (e.g. English, real corpus: 0.094 committed, 0.101 rerun). None of the qualitative conclusions changed: no key beat all nulls in the per-sign tests, and the fitted Dravidian rebus key (0.073 in both runs) still scored below the English, Finnish, Sanskrit and Markov-nonsense keys. A fix (sorted iteration plus a fixed hash seed, then a full rerun with reported spread) is planned. Until then, set `PYTHONHASHSEED=0` for repeatable local runs.

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
