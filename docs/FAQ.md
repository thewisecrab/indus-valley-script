# Frequently asked questions

Plain answers to the objections we hear most often. Every claim links to a result in this repository. Section numbers (§) refer to the paper, `paper/manuscript_public.md`.

## What does this repository claim?

- **The sign sequences have real structure.** Some signs nearly always come first, some nearly always come last (the "jar" sign ends 72–78% of the texts it appears in), and recurring multi-sign units exist. These patterns hold up against shuffled controls, across two independent transcriptions, and on sites held out from training (§4.1–4.3, §4.13).
- **No published phonetic reading we tested beats null models.** This covers 42 hand-sourced sign-value proposals and two complete keys (§4.6, §4.9, §4.22, §4.23).
- **No statistic we know of settles whether the script writes a language.** Our measures place the Indus corpus between known writing and real non-linguistic symbol systems (§4.4, §4.15, §4.20, §4.25).

## What does it not claim?

- That the script is deciphered, or that it is close to being deciphered.
- That the script does **not** write language, or that it does.
- That any particular proposal is wrong in every value. Our tests show only that the evidence offered does not support the proposals.
- That any language (Sanskrit, Dravidian or another) was or was not spoken in the Indus civilization. That is a separate question (see "Which language did they speak?" below).

## Has anyone deciphered the Indus script?

No decipherment is generally accepted. To be convincing, a decipherment has to make predictions that can be checked against something independent: a bilingual text, new inscriptions read before they are found, or readings that fit archaeological context. Claims of the form "my readings make sense" do not meet that standard, for the reason in the next answer.

## "My readings come out as good Sanskrit (or Tamil). Isn't that proof?"

No. This is the **circularity** problem. If you choose the language first and then pick sign values until the texts read well, they will read well, whatever the texts are.

We measured this directly (§4.24, `outputs/arbitrary_text/RESULTS.md`). We drew values from the inventory of a published Sanskrit key and used the same reading rule. Values fitted on 80% of each corpus produced a complete Sanskrit grammatical parse on the held-out 20% for:
- 100% of texts made from the **US Constitution read letter by letter**;
- 92–93% of **random sign strings**;
- 96–98% of **Akkadian cuneiform**;
- 90–92% of the **Indus texts**.

Readability therefore tells you about the method's flexibility, not about the script. The Panini Protocol page made the same point (https://ugrashravas.github.io/paniniprotocol).

## "But I passed the unicity distance."

Unicity distance is the amount of ciphertext after which only one key should fit. It assumes a fixed cipher and natural-language plaintext. A method that can choose among many values per sign, insert optional vowels, and accept any string a grammar parser accepts does not meet those assumptions. In our control, fitted keys fully parsed 1,360–1,835 held-out symbols in every corpus, including English and random strings. That is several times the 475-symbol threshold that has been quoted (§4.24).

## So what would count as evidence?

Here is one test anyone can run: **a correct key should read the real sign order much better than shuffled order.** We checked this premise on scripts that have been deciphered (§4.22). At Indus text lengths, correct keys for Sanskrit and Akkadian lose 17–25 points when the signs of each text are shuffled. They still lose 21–34 points when every sign keeps its usual first, middle or last position. The published keys we tested lose nothing. Yajnadevam's published readings lose a little, mostly because of where signs stand in the text (§4.23).

You can run this on your own proposal: see [`SUBMIT_A_KEY.md`](SUBMIT_A_KEY.md). Passing is necessary, not sufficient.

## "There is no bilingual, so nothing can be known."

A bilingual (like the Rosetta Stone) is the most direct route, and none is known for the Indus script. Without one, some things *can* still be measured: sign order, position, frequency, and how texts vary by site and object type. That is what this repository does. What cannot be done without an independent anchor is **calibrating sound values**. That is why we do not, and cannot, offer readings (§6, last item).

## "The texts are too short."

They are short: about 4–5 signs on average, and most are under 6. That limits every statistical test and makes many different decipherments fit equally well. But short is not hopeless. Correct keys for known scripts, cut to the same lengths, still show large shuffle losses (§4.22), so the shuffle test has power at these lengths. Short texts also explain why so many sequences are unique; see below.

## The chronology problem

The Mature Harappan cities date to about 2600–1900 BCE. The earliest Sanskrit texts and the earliest Tamil inscriptions are much later, by several centuries in the case of Sanskrit and by well over a millennium in the case of Tamil. Any reading in a historically attested language has to explain this gap (language change, lost intermediate stages). Our tests do not depend on chronology, but readers should keep it in mind when judging a proposal.

## Which language did the Indus people speak?

Unknown. Arguments from outside the script, such as loanwords in Mesopotamian sources (for example, Mukhopadhyay 2021 on the Akkadian word for "elephant"), bear on which languages were spoken in the region. They do not show what the script encodes. Several languages may have been spoken.

## "It is not writing at all, just tags, emblems or accounting."

This is a serious hypothesis (Farmer, Sproat & Witzel 2004), and our data do not rule it out. We tested a recent detailed version, the five-field "cargo-tag database" of Diener (2026), which builds on the statistics of Kriger & Hunt (2026). The predictions were registered in advance (§4.25, `outputs/structured_notation/RESULTS.md`).

| Claim | What we found | Verdict |
|---|---|---|
| A fixed five-field record | Positional patterns are real, but owner's stamps in Latin show them more strongly; 22–52% of Indus texts are longer than five signs | Not supported |
| 98.31% unique sequences "rule out language" | Short texts in known languages are just as unique at the same sample size; shuffled Indus texts are *more* unique | Not supported |
| Numerals sit in field 4 | Numerals cluster at reading position 2, not 4. The published figure counts left to right, the opposite of the reading direction | Not supported |
| The animal on the seal fixes the numeral | No association (p = .40) | Not supported |
| The jar sign is a "closing operator" | It is strongly final, but so are suffixes and titles in known languages | Cannot be tested with these data |

Seals did have administrative uses: they turn up in most excavated buildings, and sealings closed containers and doors (Green 2021). So record-keeping is plausible. The statistics simply do not choose between a record system and short texts in a language.

## "98% of sequences are unique, which no language does."

Short texts in languages do this all the time. Names, titles and owner's marks are almost all unique. At the same sample size (179) and text lengths, Latin inscriptions are 99.4% unique, Sanskrit word groups 100%, and running-text windows 99–100%. A random shuffle of the same Indus signs gives 99.99% (§4.25).

## Where is the data? Why can't I download everything?

Some inputs (the Mahadevan 1977 concordance, ICIT-derived data, the *lipi* key values) are under copyright or have no licence. We publish only statistics derived from them, along with scripts that rebuild everything once you obtain the inputs yourself. See `DATA_POLICY.md` and `REPRODUCIBILITY.md`. Openly licensed inputs (DCS Sanskrit, ORACC, EDH, Wikipedia titles, Sproat's corpora, the US Constitution) are fetched or shipped with their licences.

## Who made this?

The repository is maintained anonymously by "Indus Valley Script project contributors". Much of the analysis code and every visual judgement were produced by an AI research assistant, and none of it has yet been checked by a human epigrapher (§6). Corrections are welcome. Open an issue with the evidence.

## References for this page

- Diener, Ł. 2026. *Excel in Clay II: The Meluhha Operating System.* Zenodo, doi:10.5281/zenodo.20688721.
- Farmer, S., R. Sproat & M. Witzel. 2004. The collapse of the Indus-script thesis. *EJVS* 11(2): 19–57.
- Green, A. S. 2021. Killing the priest-king. *Journal of Archaeological Research* 29: 153–202. doi:10.1007/s10814-020-09147-9.
- Kriger, B. & T. A. Hunt. 2026. Positional constraints, sequence uniqueness, and stroke numerals in Indus seal inscriptions from Mohenjo-Daro. Zenodo, doi:10.5281/zenodo.19103880.
- Mukhopadhyay, B. A. 2021. Ancestral Dravidian languages in Indus Civilization. *Humanities and Social Sciences Communications* 8: 193. doi:10.1057/s41599-021-00868-w.
- Ugraśravas. *The Panini Protocol.* https://ugrashravas.github.io/paniniprotocol (fetched 30 October 2026).
