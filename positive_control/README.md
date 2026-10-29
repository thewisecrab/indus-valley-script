<!-- Public copy of the positive-control note; see manuscript §4.22. -->
# Positive control for the shuffle test (session 7, 29 Oct 2026, IST)

**Question (raised by a reader):** does a *correct* key for a deciphered script actually lose a lot when sign order is destroyed? If it doesn't, "Yajnadevam's key doesn't lose under shuffling" says nothing.

**Method.** We used the same three measures as the Yajnadevam test (`claim_harness.py` part B and `parse_test_vidyut.py` part E), the same nulls, and the same text count (n = 2,317):
- **M1:** the whole reading segments into words from the full dictionary.
- **M2:** the same, against a 4,361-word dictionary sample stratified by word length exactly as in `get_lexicons()`.
- **M3:** a full vidyut 0.4 morphological parse. This is Sanskrit-only; no open Akkadian parser was available.

The nulls are within-text shuffles and global shuffles (200 each for seed 0), plus a permuted (wrong) key (100). Four further text-sample seeds use 50/50/20.

All RNGs are `random.Random(int)`. p is one-sided, (1 + #null ≥ real)/(N + 1), so the smallest possible p is 0.005 at N = 200 and 0.0196 at N = 50. The Indus/Yajnadevam row was rerun with the same nulls and counts.

**Text sets for each control:**
- *full*: whole DCS sentences, or whole ORACC line runs.
- *len-matched, word-aligned*: runs of consecutive whole words whose sign count is drawn from the M77 complete-line length distribution (2–12; mean ≈ 4.2 signs, the same as the Indus test texts at 4.27).
- *len-matched, random-cut*: windows cut anywhere in the stream, as `structure2.length_matched` does.

Scripts: `scripts/pc_data.py` (corpora), `scripts/pc_run.py` (scoring), `scripts/pc_summary.py`.
Outputs: `outputs/pc_results.csv` (all seeds), `pc_summary.csv`, `pc_results_by_length.csv`, `pc_run_meta.json`.

**Reproducing.** Run `scripts/fetch_data.sh` from the repo root. It downloads the DCS files and ORACC zips into `positive_control/data/` (not redistributed here) and checks their SHA-256 hashes. Then run `python positive_control/scripts/pc_data.py`, which rebuilds `outputs/corpora/` byte-identically from the fetched files (checked 29 Oct 2026), then `pc_run.py` and `pc_summary.py`. The Indus/Yajnadevam row also needs the *lipi* data (fetched by `fetch_data.sh`; no licence, so not redistributed) and vidyut's data. The built corpora are not shipped.

## Key numbers (seed 0; drop = real − mean of null; p = one-sided, 200 shuffles)

| Script / key | Texts (mean signs) | Measure | Real | Within-shuffle | Global shuffle | Wrong key | Drop (within / global) | p |
|---|---|---|---|---|---|---|---|---|
| **Indus, Yajnadevam key** | 2,317 lipi texts (4.27) | M3 vidyut parse | 0.579 | 0.592 | 0.601 | 0.476 | **−0.013 / −0.022** | 0.96 / 1.0 |
| | | M2 seg. 4,361-word | 0.958 | 0.936 | 0.940 | 0.925 | +0.022 / +0.018 | 0.005 / 0.005 |
| | | M1 seg. full MW | 0.994 | 0.989 | 0.991 | 0.988 | +0.004 / +0.003 | 0.015 / 0.075 |
| **Sanskrit, correct key** (classical: Manu + Hitopadeśa) | word-aligned (4.17) | M3 vidyut | 0.535 | 0.334 | 0.291 | 0.043 | **+0.201 / +0.244** | 0.005 / 0.005 |
| | | M2 | 0.722 | 0.656 | 0.648 | 0.177 | +0.065 / +0.074 | 0.005 |
| | | M1 | 0.904 | 0.862 | 0.852 | 0.388 | +0.043 / +0.053 | 0.005 |
| | random-cut (4.22) | M3 vidyut | 0.428 | 0.329 | 0.297 | 0.041 | +0.099 / +0.132 | 0.005 |
| | full sentences (16.4) | M3 vidyut | 0.185 | 0.035 | 0.035 | 0.004 | +0.151 / +0.150 | 0.005 |
| **Vedic Sanskrit, correct key** (Ṛgveda) | word-aligned (4.17) | M3 vidyut | 0.530 | 0.365 | 0.314 | 0.046 | **+0.165 / +0.216** | 0.005 |
| | | M2 | 0.729 | 0.684 | 0.682 | 0.171 | +0.045 / +0.047 | 0.005 |
| | random-cut (4.21) | M2 | 0.697 | 0.702 | 0.700 | 0.170 | **−0.005 / −0.003** | 0.84 / 0.69 |
| **Akkadian cuneiform, correct (editor's) readings** (Neo-Assyrian letters SAA 1, 5) | word-aligned (4.17) | M1 seg. ORACC lexicon | 0.979 | 0.730 | 0.605 | 0.404 | **+0.249 / +0.375** | 0.005 |
| | | M1h held-out lexicon | 0.882 | 0.681 | 0.562 | 0.335 | +0.201 / +0.320 | 0.005 |
| | | M2 | 0.769 | 0.613 | 0.496 | 0.306 | +0.155 / +0.273 | 0.005 |
| **Akkadian, fixed key** (one value per sign, Yajnadevam-like) | word-aligned (4.17) | M1 | 0.855 | 0.679 | 0.598 | 0.396 | +0.176 / +0.258 | 0.005 |
| | random-cut (4.20) | M1 | 0.705 | 0.630 | 0.589 | 0.404 | +0.075 / +0.116 | 0.005 |

**Across seeds:** all five sample seeds give the same pattern.
- Vidyut drop for word-aligned Sanskrit: 0.189–0.201 (classical) and 0.135–0.165 (Vedic).
- Akkadian M1 within-shuffle drop, word-aligned: 0.245–0.260.
- Every positive-control drop is at the minimum attainable p in every seed. The one exception is Vedic random-cut M2, where the drop ranges −0.005 to +0.015, and Vedic random-cut M1, where p ≤ 0.039.

**By length (word-aligned, seed 0; `pc_results_by_length.csv`):**
- *Correct Sanskrit, vidyut within-shuffle drop:* 2 signs +0.11, 3 signs +0.21, 4 signs +0.25, 5 signs +0.27. All have p = 0.005.
- *Correct Akkadian, M1:* 2 signs +0.13, 3 signs +0.20, 4 signs +0.24, 5 signs +0.28.
- *Indus with Yajnadevam's key, vidyut:* 2 signs −0.016, 3 signs +0.013 (p = 0.21), 4 signs −0.039, 5 signs −0.016, 6–7 signs −0.017, 8–12 signs +0.011 (p = 0.42).

So short texts lose less, but a correct key still loses a lot at 3–5 signs.

## Plain answer

1. **Does a correct key lose a lot under shuffling?** Yes, on the strongest measure, the full morphological parse. Real Sanskrit read with the correct key, cut to Indus-like lengths (about 4 signs), parses 53% of the time in true order and 29–36% shuffled: a drop of about 17–24 points, roughly a third to 45% relative.
   - For cuneiform Akkadian with the editors' readings, dictionary segmentation drops 25–37 points at the same lengths. It drops 18–26 points even with a crude one-value-per-sign key.
   - Yajnadevam's key on Indus texts goes the other way: 57.9% real against 59.2% within-shuffled and 60.1% globally shuffled. p = 0.96 and 1.0 for real > shuffled.
2. **Does the premise hold for short texts?** Yes for the parse measure and for Akkadian segmentation, down to 2–3 signs, though the drop shrinks at 2 signs. **No for the weak segmentation measures in Sanskrit:**
   - With the generous Monier-Williams headword list, correct Sanskrit loses only 2–5 points (M1).
   - With the 4,361-word list, correct Vedic Sanskrit loses nothing at all when windows are cut at random places (M2 −0.005, p = 0.84).
   - So "no loss under shuffling" on M1/M2 alone would not show that a key is wrong. Only the parse measure (and segmentation for Akkadian) is a strong positive control.
3. **Something that partly undercuts our earlier wording.** With 200 shuffles instead of 3, Yajnadevam's key *does* show small, statistically significant real-order advantages on the two weak measures:
   - M2: +2.2 points, p = 0.005.
   - M1: +0.4 points, within-shuffle p = 0.015.

   The paper's statement that it "does not distinguish real from shuffled sign order on any of three measures" is therefore too strong. A better version: it shows no advantage on the full parse (it is slightly worse than shuffled), and only small advantages on the two segmentation measures. Those advantages are a third to a half of what a correct key achieves on M2 in comparable settings (+0.065 classical, +0.045 Vedic), and they come at a ceiling of 94–99% that correct Sanskrit never reaches (72–90%).

   The ceiling itself is diagnostic. The lipi reading rule, with its optional inherent *a*, lets almost any sign string segment.

## Caveats
- **Sanskrit text.** DCS gives unsandhied tokens. Sandhi was re-applied automatically with vidyut's own rule table, using the first matching rule, so it is approximate. Aksharas are orthographic syllables (C*V plus M/H, with final consonants attached). The correct "key" maps each akshara to itself. This is the ideal case: no polyphony.
- **Akkadian.** Logographic words carry their ORACC normalised form on the first logogram. Determinatives and numerals are silent. Words with missing signs, unlemmatised words, or Sumerian words break the text (31,669 of 51,245 words excluded).
- **Akkadian lexicon.** The main lexicon is in-sample: its glossaries include SAA 1/5. M1h uses only the SAA 10 and RINAP 4 glossaries and still shows drops of 20–32 points. The length-matched Akkadian lexicon has 3,612 words, not 4,361, because the Akkadian glossaries are short of 2–4-letter forms at the required counts.
- **Reading rules differ.** The controls use each script's correct reading rule, while the Indus row uses lipi's rule with optional inherent *a* (as in the original test). We did not run Sanskrit through lipi's rule. Its values are consonantal stems and the rule does not apply cleanly to aksharas.
- **Not tested.** Linear B and Old Persian were not run: no openly licensed, machine-readable corpus plus lexicon was identified within this session. Brahmi or Prakrit inscriptions were not run either: no open Prakrit lexicon or parser was found. Sanskrit aksharas stand in for the Brahmi-family case.
- **Download note.** ORACC's server does not send its intermediate TLS certificate (InCommon RSA Server CA 2), and the box could not fetch that certificate. The ORACC zips were therefore downloaded with TLS verification disabled (`curl -k`). SHA-256 hashes are in `data_open/oracc_SHA256SUMS`; the contents parse as the expected ORACC JSON with CC0 metadata.

## Sources and licences
- **Digital Corpus of Sanskrit (DCS)**, O. Hellwig, CoNLL-U files for Manusmṛti (12 files), Hitopadeśa (5) and Ṛgveda (500 hymn files, ṚV 1.1–6.59), pinned to commit 8aeed5a; the exact list with SHA-256 is `data_open/dcs_SHA256SUMS`. https://github.com/OliverHellwig/sanskrit (dcs/data/conllu/files). **CC BY 4.0** (stated in dcs/data/readme.md). Cite: Oliver Hellwig, *The Digital Corpus of Sanskrit (DCS)*, 2010–2024.
- **ORACC JSON** (https://oracc.museum.upenn.edu/json/), downloaded 29 Oct 2026.
  - Texts: `saao-saa01.zip` and `saao-saa05.zip` (SAAo: Correspondence of Sargon II, parts I–II).
  - Lexicons: those two, plus `saao-saa10.zip` (Letters from Assyrian and Babylonian Scholars) and `rinap-rinap4.zip` (Esarhaddon).
  - Also downloaded but unused: rimanum, riao, obta.
  - Licence: each JSON's metadata says **CC0**. The ORACC site licence is **CC BY-SA 3.0**, so we attribute ORACC and the SAAo/RINAP editors and treat any redistribution as CC BY-SA 3.0.
- **Monier-Williams** headwords via csl-orig (CC BY-SA 4.0) and **vidyut 0.4** (MIT): the same files as the original test.
- **Indus texts and Yajnadevam key** (lipi via field-cady copy). No licence, private use only, not redistributed: the same as the original test. M77 is used only as an aggregate line-length distribution (`data_open/m77_line_length_distribution.json`, copied to `data/` by `fetch_data.sh`).
