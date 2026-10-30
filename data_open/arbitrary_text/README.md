# Arbitrary-text control inputs

- `us_constitution_gutenberg5.txt`: the text of the Constitution of the United States (1787; public domain). It was taken from Project Gutenberg eBook #5 (https://www.gutenberg.org/cache/epub/5/pg5.txt, fetched 2026-10-30). The SHA-256 of the downloaded file was d177168e3f4898213dced30fbbe60d74ad08e884ed5dd86bff94a1b8836b5982. Only the constitutional text is kept, from the title line to the signatures; the Project Gutenberg header, the editor's note and the licence block were removed. No Project Gutenberg trademark material is included.

`scripts/arbitrary_text_control.py` uses this text as the "arbitrary text" in the control. See `docs/FAQ.md` and paper section 4.23.
