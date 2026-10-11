# Reanalyzed — data and code

Data and analysis code behind the YouTube channel **Reanalyzed** (@reanalyzed). Each folder is one episode. Everything shown on screen with "see description" should be reproducible from here. If you find an error, please open an issue; corrections are logged at the bottom of each episode section and pinned under the video.

## Episode 1 — Did the Black Death Really Kill Half of Europe? (`ep01-black-death/`)

Two witnesses from the same hills in Devon:

1. **The register of John de Grandisson, bishop of Exeter (1327–1369)** — every institution of a new priest to a benefice in Devon and Cornwall, parsed from the 1899 printed edition and placed on a map (`register/`).
2. **The 2022 European pollen study** (Izdebski et al., *Nature Ecology & Evolution* 6, 297–306, doi:10.1038/s41559-021-01652-4), whose only English sites are bogs in Devon — re-run and checked for pseudo-replication (`pollen/`).

### Main results

| Claim in the video | Number | Where |
|---|---|---|
| New priests in 1349 vs a normal year | 375 by our parse (editor's monthly figures sum to 396; Gasquet 382) vs ~30/yr in 1340–47 → "more than ten times" | `register/feasibility_results.json` (`validation`, `per_year`) |
| Peak month | March 1349: 53 (editor: 60) | `monthly_1348_09_to_1350_06` |
| Entries giving a reason for the vacancy | Jan 1345–Jun 1348: 41 of 92 · 1349: 26 of 375 | `cause_stated` |
| Parish churches that got a new priest, Nov 1348–Dec 1349 | ~250 (251 located; 265 incl. unlocated) of ~550–600 named in the register → "about four in ten" | `parish_churches_nov48_dec49` |
| Rough share of parish priests who died | ~40–49% of churches × 80–90% of vacancies being deaths (rate from Lincoln, York, Ely; Wood et al. 2003) ≈ 31–44%. Rough: some churches never appear in the register (pushes it down), some replacements came after 1349 (pushes it up), pluralism | narrated "between a third and two in five" |
| Place of institution, Nov 1348–Dec 1349 | Chudleigh 352 · Clyst 26 · Exeter 2 | `place_of_institution_nov48_dec49` |
| Second outbreak | Oct 1361–Jul 1362: 161 institutions (≈2/month normal); excess ≈ 0.4 of 1348–49 (0.39–0.49 depending on window) | `second_wave` |
| Pollen: regions with a clear cereal change, 1250–1350 vs 1351–1450 | 9 with a simple pooled test (p < 0.05); 5 clear under all three corrections for non-independent samples (site-clustered SEs with small-sample t; mixed model with random slope; mixed model with random intercept): shrank — France: Central, Germany: South-West, Greece; grew — Baltic: South, Poland | `pollen/mixed_results.csv` |
| Detection simulation | If Devon's grain pollen had dropped as much as south-west Germany's (−0.25 SD), these 13 bogs sampled as they are (8 with one sample before and one after) show a clear drop in 24% of 2,000 runs with the site-clustered test (false alarms 2.5%) and 25% with the study's simple pooled test (false alarms 2.9%). This describes the sampling design; Devon's real 95% interval (−0.26 to +0.46) only just reaches −0.25. Variance components from a Devon fit with a boundary/convergence warning; dating error not modelled | `pollen/power_sim.py`, `power_sim.json` |
| Devon pollen | change +0.10 SD (95% CI −0.26 to +0.46, 13 sites, clustered); power to detect a drop the size of south-west Germany's (−0.25 SD) ≈ 0.29 | `pollen/mixed.py` |

Not a result of ours: England's 40–55% comes from Horrox, *The Black Death* (1994), p. 3, summarising several independent kinds of evidence.

### Caveats (also in the video)
- The register records **institutions**, not deaths. Most entries in 1349 give no reason; some vacancies were resignations (e.g. East Budleigh, April 1349).
- Dates are when the new man came before the bishop (almost always at Chudleigh), typically weeks after a vacancy.
- Beneficed clergy are not the population.
- The printed edition is an 1899 English calendar of a Latin manuscript; our parse comes from OCR and misses some entries.
- Geocoding uses GeoNames plus manual fixes; ~8% of place names are unplaced.
- Mixed-model fits often report convergence or boundary warnings (recorded in `mixed_results.csv`): every random-intercept fit and 9 of 21 random-slope fits, including south-west Germany and Poland. All five headline regions also pass the warning-free site-clustered test. An earlier version of our check (one vote per site, `sitelevel.py`) loses power and is not used for headline claims.
- Grain pollen measures fields, not deaths (Curtis 2022, doi:10.1038/s41559-022-01862-4).

### Reproduce
Python 3 with pandas, numpy, scipy, statsmodels, openpyxl (matplotlib + ffmpeg for the map animation).

```bash
# register
cd ep01-black-death/register
# GeoNames gazetteer (CC BY 4.0), not redistributed here:
curl -O https://download.geonames.org/export/dump/GB.zip && mkdir -p gn && unzip -o GB.zip -d gn
python3 parse.py      # grandisson_pt3_djvu.txt -> institutions.csv
python3 geocode.py    # -> places.csv
# pollen data: download Supplementary Data from the Izdebski et al. 2022 article page and save as
#   ep01-black-death/pollen/izdebski2022_supp_data.xlsx
python3 analyze.py    # -> feasibility_results.json, first_institution_1348_49.csv
cd ../pollen
python3 reproduce.py  # paper's regional comparison
python3 mixed.py      # pseudo-replication checks -> mixed_results.csv
python3 power_sim.py  # detection simulation -> power_sim.json (~5 min)
python3 sitelevel.py; python3 audit.py
```

### Sources
- F. C. Hingeston-Randolph (ed.), *The Register of John de Grandisson, Bishop of Exeter (1327–1369)*, Part III (1899). Public domain; OCR text from archive.org (`registerofjohnde03exet`), included as `register/grandisson_pt3_djvu.txt`.
- Izdebski, A. et al. (2022), *Nature Ecology & Evolution* 6, 297–306 (data not redistributed here).
- Wood, Ferrell & DeWitte-Aviña (2003), *Human Biology* 75(4), 427–448.
- R. Horrox, *The Black Death* (Manchester UP, 1994).
- F. A. Gasquet, *The Great Pestilence* (1893).
- GeoNames (geonames.org), CC BY 4.0.
- Natural Earth (public domain) for the coastline in `sw_land.json`.

### Corrections log
- (none yet)

## Licence
Code: MIT. Our derived data (CSV/JSON): CC BY 4.0 — please credit "Reanalyzed". Third-party material keeps its own licence (the 1899 register text is public domain; GeoNames-derived coordinates are CC BY 4.0).
