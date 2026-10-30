# Test your own Indus reading: the shuffle benchmark

`tools/evaluate_key.py` checks any proposed reading of the Indus script with one simple question:

> **Does the proposal read the real inscriptions better than the same inscriptions with their signs put in a random order?**

A key that really reads a script should lose a lot when the sign order is destroyed. We checked that premise on scripts that are already read (the positive control, `positive_control/README.md`). Real Sanskrit and Akkadian texts, cut to Indus-like lengths of about 4 signs, read with the correct values, lose 17–25 points on our strongest measure when their signs are shuffled. They still lose 21–34 points when every sign is kept in its usual position (first, middle or last) and only the sequences are destroyed.

The benchmark does **not** certify a decipherment. Passing is necessary, not sufficient.

## What you need

1. A copy of this repository and the inputs: `pip install -r requirements.txt`, then `bash scripts/fetch_data.sh`. The Indus corpora are not shipped (see `DATA_POLICY.md`); the fetch script tells you how to get them.
2. **Either** a sign→value key **or** your per-inscription readings.

### Format (a): a sign→value key

`my_key.csv`:

```
sign_id,value
W740,ja
W002,ka
...
```

- `sign_id` is `W###` (ICIT/Wells numbers, scored on the ICIT-derived texts) or `M###` (Mahadevan 1977 numbers, scored on M77). Use one scheme per file.
- `value` is your reading of the sign. Signs without a value are allowed. In the default reading rule, only texts whose signs all have values are scored.

`my_key.meta.json`:

```json
{
  "name": "my_key_v1",
  "author": "Your name",
  "language": "Sanskrit",
  "lexicon": "sanskrit_MW",
  "reading_rule": "concat",
  "inherent_vowel": "",
  "alphabet": "slp1"
}
```

- `lexicon`: a built-in name (`sanskrit_MW`, `proto_dravidian_PDR`, `english`, `finnish`, `turkish`, `hungarian`, `indonesian`) or the path to your own UTF-8 word list (one word per line, relative to the meta file).
- `reading_rule`: `concat` (values joined as they are), `inherent` (an optional vowel, given in `inherent_vowel`, may be inserted between signs), or `lipi` (Yajnadevam's rule from the *lipi* repository).
- `alphabet`: `slp1` for Sanskrit in SLP1, `latin` for anything else. Everything is reduced to the same 3-vowel alphabet before matching, so small spelling differences do not matter.
- `vidyut_parse` (optional): `true` or `false`. It defaults to `true` when `language` contains "Sanskrit".

Run:

```
python tools/evaluate_key.py key my_key.csv my_key.meta.json
```

### Format (b): per-inscription readings

This is for proposals whose readings are adjusted inscription by inscription (word division, sandhi, inserted vowels), so a sign→value key does not capture them.

`my_readings.csv`:

```
inscription_id,reading,units
1.1,hara,ha|ra
2.5,ama aYjAna,a|ma|aY|jA|na
```

- `inscription_id` is the ICIT/*lipi* inscription ID.
- `reading` is your reading as you publish it.
- `units` (optional) is the same reading split per sign, in reading order, joined by `|`. If you leave it out, give your sign→value key with `--align-key my_key.csv`. Each reading is then split per sign automatically, by the minimum edit distance between the reading and the key values.

Run:

```
python tools/evaluate_key.py readings my_readings.csv my_readings.meta.json --align-key my_key.csv
```

## What it measures

| Measure | What passes |
|---|---|
| M1 | The whole reading splits into words of the full lexicon. |
| M2 | The same, with a 4,361-word subsample of the lexicon stratified by word length (fair across lexicons of different sizes). |
| M3 | Sanskrit only: the reading gets a complete morphological parse from vidyut 0.4. This is the strongest measure, and it is the primary one when available. |

Each measure is computed on the real inscriptions and compared with these nulls:

- **Within-text shuffle:** each text's signs are put in a random order.
- **Positional re-deal:** signs are re-dealt across texts within their position class (first / middle / last). Every sign keeps its usual position, but the sequences are destroyed. This catches readings that only fit the script's positional habits, for example by giving signs that usually stand last a word-final form.
- **Interior-only shuffle:** first and last signs are kept and the middle is shuffled; scored on texts of 4 or more signs.
- **Global shuffle:** all signs are re-dealt into texts of the same lengths.
- **Permuted key** (key mode): the same values given to the wrong signs.

The defaults are 200 shuffles per null and 100 permuted keys. p is one-sided, (1 + #null ≥ real)/(N + 1), and Benjamini–Hochberg q is computed across all the tests in a run. The run is deterministic: every random draw is seeded with a CRC32 of its label.

In readings mode there are three tests:

- **R2 (piece shuffle).** The per-sign pieces of each published reading are shuffled. A reading tuned to its neighbours will lose here even if it has nothing to do with the signs, so this mostly measures how fluent the readings are.
- **R2m (mismatch control).** The same readings, each re-cut against a *different* inscription of the same length, are shuffled in the same way. If R2 and R2m lose the same amount, R2 is not evidence that the readings belong to their inscriptions.
- **R3 (the fair test).** The value each sign actually gets in the readings (its most frequent piece) is learned from 80% of inscriptions and used to read the other 20% (held out) mechanically. R3b allows each sign its two most frequent pieces.

## The verdict

The output (`bench/results/evaluate_key/<name>.md` and `.json`) gives one of three verdicts, worded with calibrated confidence:

- **NO SUPPORT FROM SIGN ORDER.** Shuffled inscriptions read as well as the real ones (or the difference is not significant). This does not show that every value is wrong; it shows that the test gives no evidence that the proposal reads the inscriptions.
- **WEAK.** Real order helps, but by less than half of what correct keys lose under the same null, or the effect mostly disappears under the positional controls.
- **PASSES THIS TEST.** The order effect is at least half of a correct key's under every null, positional controls included. Next steps: inscriptions not used to build the proposal (new finds, held-out sites), independent review, and agreement with archaeological context.

There are also two warnings. A **ceiling warning** appears when 95% or more of the real texts already pass a measure, so nearly anything passes. A **permuted-key warning** appears when wrong sign–value pairs score almost as well as the real ones.

## Example results (aggregate statistics only)

| Proposal | Mode | Primary measure: real vs within-shuffle | Verdict |
|---|---|---|---|
| Yajnadevam key (*lipi* @ fc8813a) | key | M3 parse 0.579 vs 0.591 (drop −0.012) | No support from sign order |
| Yajnadevam published readings (*lipi* @ fc8813a, 1,694 readings) | readings, R3 held-out | M3 0.541 vs 0.403 (drop +0.139); positional re-deal drop +0.046, interior-only +0.073 (correct keys: at least +0.209 and +0.159) | Weak: largely positional |
| Field-Cady Proto-Dravidian syllables (open, MIT) | key | M2 0.399 vs 0.432 (drop −0.033) | No support from sign order |
| Toy demo (`bench/examples/toy_key.csv`, offline) | key | 5 texts | Runs offline with `--corpus toy`; for checking the tool only |

The full tables are in `bench/results/evaluate_key/`. The Yajnadevam key and readings are not redistributed (the *lipi* repository has no licence); only the scores are.

## Offline demo

```
python tools/evaluate_key.py key bench/examples/toy_key.csv bench/examples/toy_key.meta.json --corpus toy --nshuf 20 --nperm 10
```

## Submitting a result

Open an issue or pull request with your key or readings (or a link to them), the meta file, and the output `.md`. We will run it against the same nulls and publish the result, whichever way it goes.
