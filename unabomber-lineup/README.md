# Unabomber authorship lineup (Reanalyzed, episode 3)

Question: using the same kinds of writing the FBI held in 1996, does a standard stylometric test pick Ted Kaczynski as the author of *Industrial Society and Its Future* (1995)?

## Texts (not redistributed — copyrighted; all read from thetedkarchive.com library pages, `.muse` plain text)
- Manifesto: `ted-kaczynski-industrial-society-and-its-future-washington-post-version`
- Kaczynski letters (pre-arrest, Ted-authored only, English): `ted-kaczynski-david-kaczynski-letters-to-from-david-kaczynski` (section "Letters from before Ted's arrest"), plus six letters to editors/officials 1969–91 (see `corpus.py`)
- Kaczynski 1971 essay (FBI "T-2"): extracted from `james-r-fitzgerald-the-ted-unabom-and-cabin-documents` §6, where it is printed in full
- Kaczynski later essays (control only; not used in the 1996 lineup): see `corpus.py`
- Lineup: Goodman (Growing Up Absurd), Postman (Amusing Ourselves to Death; Technopoly), Berry (The World-Ending Fire), Sale (Rebels Against the Future), Illich (Shadow Work), Mumford (Technics and Civilization), Zerzan (Elements of Refusal; Future Primitive), Perlman (Against His-story), Abbey (The Monkey Wrench Gang)

## Method
Burrows' Delta and cosine Delta; features = N most frequent words (100–500) or a fixed function-word list (`funcwords.py`); chunks of 1,000–3,000 words, up to 30 random chunks per author; manifesto compared with each author's centroid.

## Results
- Letters only (`robust_letters_only.json`, 72 runs): Kaczynski never first (ranks 4–9); Goodman first 58, Berry 13, Postman 1.
- With the 1971 essay (`robust.json`, 60 runs per method): cosine — essay first 60/60; classic — first 23/60, top-3 60/60 (Goodman first 36).
- Function words only (`funcwords.json`): cosine — essay first 18/18.
- Caveats: genre (letters vs essay) and topic (the 1971 essay shares the manifesto's subject) both matter; the lineup is a convenience sample of available texts; some lineup texts are much later (Berry 2017 collection) or fiction (Abbey).
- "eat your cake and have it" vs "have your cake and eat it", Google Books Ngram en-US 1970–95: 8.6% eat-first (`ngram_quirks.json`; use the case-insensitive "(All)" series only).
