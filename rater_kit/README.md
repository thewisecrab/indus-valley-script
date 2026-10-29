# Blind human check of sign concordance links (rater kit)

**Status:** prepared in session 6. **No one has been recruited yet.** Every visual judgement in the paper so far was made by the project's AI research assistant, and this kit is meant to replace those judgements with independent human ones.

## What you judge

`REVIEW_SHEET.csv` lists 60 items in random order. Each item pairs a Mahadevan 1977 sign number (M###) with a Wells/ICIT sign number (W###). There are two kinds of item:

- **40 items** are concordance links drawn from M. Carlson's hand-matched M↔W concordance. The AI assistant judged these in our paper; this sheet does not show its judgements.
- **20 items** are decoys: a randomly chosen W sign that is *not* linked to that M sign.

The sheet does not say which items are which. The answer key (`ANSWER_KEY.csv`) is held back until the ratings are in. Its SHA-256 is published in `ANSWER_KEY.sha256`, so anyone can check afterwards that the key was not changed.

## What you need (we cannot supply the images)

- The M sign images: Mahadevan, I. 1977. *The Indus Script: Texts, Concordance and Tables* (MASI 77), sign list on book pp. 32–35. Use your own lawful copy.
- The W sign images: Wells, B. K. 2015, *The Archaeology and Epigraphy of Indus Writing*, sign list, or the ICIT sign list. Use your own lawful copy.

We do not redistribute either set of images, because both are under copyright.

## Protocol

1. Work alone. Before you finish, do not look at our paper's Fig. 7, `handcheck_pairs.csv`, `outputs/signmap/` or any M↔W concordance (including Carlson's): the decoys can be identified from the concordance, so consulting it breaks the blinding.
2. For each item, compare the two signs and fill in a judgement: `same sign`, `variant of same sign`, `different sign` or `cannot tell`. Add a confidence from 1 (low) to 3 (high) and, optionally, a note.
3. Do not change the item order. Avoid doing all 60 items in one sitting if you are getting tired.
4. Send the completed sheet as a GitHub issue on this repository titled "Rater sheet: <handle>", with the CSV attached. Please also state your background (e.g. epigrapher, archaeologist, interested non-specialist).

## Scoring (`score_raters.py`, run after the key is released)

Per rater:

- **Accuracy on decoys:** the share of decoys judged `different sign`.
- **Agreement with Carlson on the 40 links:** `same sign` or `variant` counts as agreement.
- **Agreement with the AI judgements:** Cohen's kappa.

Across raters: Fleiss' kappa. A rater who calls more than half of the decoys "same" or "variant" is reported separately.

## Pre-stated thresholds

The AI-made check is **confirmed** only if, across at least two independent raters:

- the median agreement with the AI judgements on the 40 links is ≥ 80%, and
- the median decoy accuracy is ≥ 80%.

Any other outcome is reported as **not confirmed**.
