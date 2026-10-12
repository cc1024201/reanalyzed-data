# The 2016 clown panic, mapped (Reanalyzed, episode 4)

- `incidents_2016.csv` — 222 media-reported incidents (Aug–Oct 2016), US and abroad: date (incident date, or publication date where only that is known — see `date_basis`), place, approximate coordinates, type, outcome as reported, source URL. Personal names removed. **A sample of what got reported, not a census of police calls.**
- First report per US state = earliest row per `us_state` (excluding the 1 Aug Green Bay "Gags" film-marketing stunt and Puerto Rico).
- `adjacency.py` / `adjacency.json` — is the order in which states first reported more neighbour-to-neighbour than random orderings of the same dates?
- Google Trends CSVs — our own download (2026-10-12): US daily "clown", "creepy clown", "clown sightings" (Jul–Dec 2016); daily "clown" for world, GB, SE, AU; US monthly 2004–2026. Values are relative (0–100) and sampled.

Results (cut-off 28 Sep 2016):
- Before: 19 of 23 new states bordered a reporting state (random orderings: 58%; P≈0.0006); first-report date vs distance from Greenville SC, Spearman ρ≈0.56. But reports also appeared far away early (Ohio 30 Aug, Arizona 10 Sep).
- After: no geographic pattern (ρ≈0); 20 states first reported 3–5 Oct, the days US searches peaked (4 Oct). Daily new states vs searches: r≈0.6 same day, ≈0.7 with states one day ahead.
- An earlier version of this dataset searched nearby states harder than distant ones and overstated the "wave from Greenville". A symmetric search added 24 earlier reports, mostly far from Greenville.

If you know an earlier 2016 report for any state, open an issue with a source.
