# Pre-registration, session 8: is the Indus corpus a fixed-field administrative notation ("cargo tag")?

Written 30 October 2026 (IST) **before** any of the tests below were run. The script that runs them is `scripts/structured_notation.py`; its outputs go to `outputs/structured_notation/`. Nothing in this file is changed after the results exist; deviations are listed in the results file.

## The proposal under test

Diener, Ł. (2026). *Excel in Clay II: The Meluhha Operating System: A Mathematical Reconstruction of the Indus Valley Non-Linguistic Cargo-Tag Database.* Zenodo preprint, version 2.1 (June 2026), CC BY 4.0, doi:10.5281/zenodo.20688721 (PDF `indus_whitepaper_EN_v2_1.pdf`, 135,208 bytes, SHA-256 `fabd03f0…a323c2e7`). Its statistics are taken from Kriger, B. & Hunt, T. A. (2026). *Positional constraints, sequence uniqueness, and stroke numerals in Indus seal inscriptions from Mohenjo-Daro: a statistical analysis.* Zenodo preprint, CC BY 4.0, doi:10.5281/zenodo.19103880, which analyses 179 Mohenjo-daro unicorn seals from M. Carlson's open CISI digitisation (github.com/mayig/indus-valley-script-corpus, MIT). We have the same corpus (commit ad2f1e2), so those numbers can be replicated directly.

Claims (Diener 2026, §§1.2, 3, 10; Appendix A–B):
- **(a)** A rigid five-field record P1–P5 (issuer icon, commodity root, attribute, numeral tariff field, terminal operator); "Friedman χ²(4) = 14.7, p = 0.005" for positional entropy variation (Kriger & Hunt §5.2: 5-sign texts, n = 35).
- **(b)** 98.31% sequence uniqueness at Mohenjo-daro (n = 179) is "structurally incompatible with any natural language".
- **(c)** Stroke numerals concentrate in P4 (45.71%) and the two-stroke sign dominates (66.91%, 103/154), which "excludes" natural counting.
- **(d)** Faunal icons lock the permitted numeral ("tariff") tiers: unicorn k = 1–5, gaur k = 2–3, elephant and rhinoceros k ≥ 4.
- **(e)** The jar sign (Mahadevan 342) is a terminal closing ("COMMIT") operator.

## Data

- **Indus.** I1: the 179 CISI/mayig Mohenjo-daro unicorn seals (Kriger & Hunt's corpus), in reading order (the JSON is in visual left-to-right order of the sealing; reading is right-to-left, so we reverse). I2: ICIT-derived *lipi* texts (unique, clean). I3: Mahadevan 1977 (unique, undamaged). I2 and I3 are restricted inputs; only aggregate statistics are published.
- **Comparison, deciphered and short.** Latin owner's/maker's stamps on objects from the Epigraphic Database Heidelberg (EDH genre "titpossfabr", mostly personal names; words and letters); Wikipedia article titles in Finnish, Tamil and Sanskrit (words; many are names); Sanskrit word-aligned spans (DCS, aksharas as signs) and Neo-Assyrian Akkadian word-aligned spans (ORACC SAA 1/5, cuneiform graphemes as signs), cut to the M77 length distribution exactly as in the positive control.
- **Comparison, non-linguistic.** Sproat's seven open non-linguistic corpora (Pictish, kudurru, Vinča, barn stars, totem poles, weather icons, Asian emoticons).
- **Comparison, linguistic windows.** Wikipedia running text (English, Finnish) as words and as letters, cut into windows with the M77 length distribution.

## Tests, statistics and decision rules

All p-values are one-sided unless stated, from 2,000 permutations (CRC32-seeded RNGs, sorted iteration), and Benjamini–Hochberg corrected across every p-value in this pre-registration. "Supported" needs BH q < .05 **and** the stated comparison condition. A claim can be supported as a **fact about the corpus** and still fail as **evidence for the proposed interpretation**; we report the two separately.

**A1. Positional entropy profile (claim a, replication and generalisation).** For texts of exactly 5 signs: plug-in Shannon entropy of the sign at each position. Statistic: variance of the five entropies. Null: within-text shuffles (the text composition is kept, position is destroyed). Run on I1 (n = 35), I2 and I3, and on each comparison corpus by subsampling 35 five-token texts 200 times (statistic as a z-score against that subsample's own shuffles; median over subsamples).
- *Prediction if (a) is right:* Indus z is significant and larger than the z of every linguistic comparison corpus at the same n.
- *Our expectation:* significant for Indus (we already know initial and final signs are restricted), but also large for short linguistic texts with fixed formulae (stamps, names), so not discriminating.

**A2. Rigid five-field fit (claim a).** Each sign type is assigned to one of five ordered fields by hill-climbing (20,000 steps) on 80% of the texts to maximise the share of texts that are valid records. A *strict* record has strictly increasing fields (each field used at most once, so at most 5 signs); a *relaxed* record has non-decreasing fields. Score: valid share on the held-out 20%, real order vs within-text shuffles of the held-out texts (same assignment). The same procedure is run on every comparison corpus with the same number of texts and the Indus length distribution. Also reported: the share of texts longer than 5 signs (which no strict five-field record can hold).
- *Prediction if (a) is right:* the Indus held-out strict share is high, clearly above its shuffles, and above every linguistic comparison corpus.
- *Decision:* not supported if any linguistic comparison corpus reaches the Indus held-out strict share (within the 95% range over 5 seeds), or if the real-vs-shuffle gain is not significant.

**B. Sequence uniqueness (claim b).** Share of texts whose sign sequence occurs only once in a sample of 179 texts drawn with the I1 length distribution (500 draws per corpus). We also replicate Kriger & Hunt's global-shuffle null (reported 91.2%).
- *Prediction if (b) is right:* every natural-language comparison corpus, including the name and title corpora, has median uniqueness below 98.31%.
- *Decision:* the "incompatible with natural language" inference is **not supported** if at least one natural-language corpus reaches a median of ≥ 98.31% at matched n and lengths.
- *Our expectation:* names and titles reach it easily.

**C. Stroke numerals (claim c).** Stroke signs by Carlson's descriptions: short P121–P126 (1–6 strokes) and tall P144, P145, P147, P150 and P151 (1, 2, 3, 4 and 5 strokes). Kriger & Hunt's exact set (P121–P124, P144–P151) is also run for replication.
- C1: share of stroke signs at position 4 of 5-sign texts, against within-text shuffles; I1, I2 and I3.
- C2: share of two-stroke signs among stroke tokens, and how much of it comes from the two-stroke sign inside the fixed initial pair with the diamond sign (M267+M099 / P385+P122).
- The inference that "2" dominance "excludes" counting is **untestable** with corpus statistics alone; we say so.
- *Prediction if (c) is right:* C1 significant in all three corpora.

**D. Tariff locking (claim d).** ICIT seals whose field symbol is unicorn (Bull1*), gaur, elephant or rhinoceros, and whose text has at least one stroke numeral; k = the stroke count of the numeral sign (the largest one, if there are several). Test: motif × k independence (permutation chi-square, 10,000 permutations).
- *Prediction if (d) is right:* significant association, ≥ 80% of elephant and rhinoceros texts with k ≥ 4, and ≥ 80% of gaur texts with k ∈ {2, 3}.
- *Decision:* supported only if all three hold.

**E. Terminal jar sign (claim e).** E1: share of jar tokens (M342 / W740 / P324) that are text-final, against within-text shuffles. E2: for comparison, the share of the most strongly final token type in each comparison corpus that is final (a grammatical suffix or a fixed closing word also gives this).
- *Prediction if (e) is right:* E1 significant.
- *Interpretation:* E1 is necessary for "closing operator" but equally predicted by a linguistic suffix or a name-final element, so it cannot by itself support (e) over a linguistic reading. If E2 shows comparable terminal concentration in linguistic corpora, (e)'s functional reading is labelled **untestable** with our data.

**Not tested (no open data).** Physical arguments (moulded jar stamps, Lothal tags, goblets, Gadd seal 1) and the deficit sign 142 (Diener's numbering is not stated precisely enough to map).

## Optional benchmark

Proto-cuneiform administrative texts (CDLI) as a known accounting system, if openly licensed and cleanly fetchable. If not, this is skipped and said so.
