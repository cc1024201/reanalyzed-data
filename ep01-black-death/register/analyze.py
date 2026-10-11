"""Analysis of the Exeter institutions data (1339–1353) for episode 1.
Run from register/:  python3 analyze.py   ->  feasibility_results.json, first_institution_1348_49.csv
"""
import json, sys
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, '.')
from geocode import clean

d = pd.read_csv('institutions.csv').fillna('')
pl = pd.read_csv('places.csv').set_index('name')
d['name'] = d.place.map(clean)
d = d[~d.place_raw.str.contains('Hants|Bosham|Sussex', regex=True)]
d = d.join(pl[['lat', 'lon', 'gn_name', 'a2']], on='name')
d['county'] = d.a2.map({'D4': 'Devon', 'C6': 'Cornwall'})
d['dt'] = pd.to_datetime(d.date, errors='coerce')
d = d[d.dt.notna()]
d['ym'] = d.dt.dt.to_period('M')
d['parish_church'] = d.benefice.isin(['R', 'V'])
sub = d.place_raw.str.replace(r'\[[^\]]*\]', '', regex=True).str.extract(r';\s*([^,]*)', expand=False).fillna('')
d['key'] = d.gn_name.fillna(d.name) + ' | ' + sub.str.replace(r'-?on-(the-)?', ' on ', regex=True).str.replace(r'\W+', ' ', regex=True).str.strip()
out = {}

# 1. monthly counts vs. the 1899 editor's own monthly counts (preface pp. lxv–lxvi) — validation of the parse
editor = {'1349-01': 31, '1349-02': 35, '1349-03': 60, '1349-04': 53, '1349-05': 48, '1349-06': 46,
          '1349-07': 37, '1349-08': 16, '1349-09': 23, '1349-10': 16, '1349-11': 17, '1349-12': 14}
mc = d.groupby('ym').size()
val = pd.DataFrame({'ours': [int(mc.get(pd.Period(k), 0)) for k in editor], 'editor': list(editor.values())}, index=list(editor))
out['validation'] = dict(ours=int(val.ours.sum()), editor=int(val.editor.sum()), by_month=val.to_dict('index'))
out['monthly_1348_09_to_1350_06'] = {str(k): int(v) for k, v in mc.loc['1348-09':'1350-06'].items()}
out['n_rows_used'] = len(d)

# 2. baseline
yr = d.groupby(d.dt.dt.year).size()
out['per_year'] = {int(k): int(v) for k, v in yr.items()}
out['baseline_1340_47_mean'] = float(yr.loc[1340:1347].mean())

# 3. stated causes: (a) "On the death/Resignation of" headings only; (b) any reason in the entry (exchange, resigned, died)
d['stated'] = d.cause != ''
d['stated_any'] = d.cause_any != ''
def rate(m):
    x = d[m]; return dict(n=int(len(x)), heading=int(x.stated.sum()), any_reason=int(x.stated_any.sum()))
out['cause_stated'] = {'1340-44': rate((d.dt >= '1340') & (d.dt < '1345')), '1345-48H1': rate((d.dt >= '1345') & (d.dt < '1348-07')),
                       '1349': rate(d.dt.dt.year == 1349)}
plague = d[(d.dt >= '1348-11-01') & (d.dt < '1350-01-01')]
out['plague_n'] = len(plague)
out['plague_cause_any'] = plague.cause_any.replace('', 'not stated').value_counts().to_dict()

# 4. parish churches (rectories/vicarages) and repeat institutions
pc = plague[plague.parish_church & plague.lat.notna()]
out['parish_churches_nov48_dec49'] = int(pc.key.nunique())
out['parish_churches_1349'] = int(pc[pc.dt.dt.year == 1349].key.nunique())
rep = pc.groupby('key').agg(n=('idx', 'size'), dates=('date', list)).query('n >= 2')
out['repeat_parishes_auto'] = int(len(rep))
out['parish_church_share_of_1349'] = dict(parish=int((d.parish_church & (d.dt.dt.year == 1349)).sum()), all=int((d.dt.dt.year == 1349).sum()))

# 5. spread: first plague-era institution per located parish church
loc = pc.sort_values('dt').groupby('key').first()
loc['days'] = (loc.dt - pd.Timestamp('1348-11-01')).dt.days
r = stats.spearmanr(loc.lon, loc.days)
out['first_date_vs_lon'] = dict(rho=round(float(r.statistic), 3), p=float(r.pvalue), n=int(len(loc)))
out['median_first_date'] = {c: str((pd.Timestamp('1348-11-01') + pd.Timedelta(days=float(v))).date())
                            for c, v in loc.groupby('county').days.median().items()}

# 6. is the "east→west wave" separable from distance to the bishop? Institutions Oct 1348–Aug 1349 took place at Chudleigh.
chud, exeter = (50.603, -3.600), (50.7236, -3.5275)
def km(p, la, lo):
    return np.hypot((la - p[0]) * 111.2, (lo - p[1]) * 111.2 * np.cos(np.radians(50.6)))
loc['dist_km'] = km(chud, loc.lat, loc.lon)
loc['dist_exeter_km'] = km(exeter, loc.lat, loc.lon)
def partial(y, x, z):
    Z = np.c_[np.ones(len(z)), z]
    ry = y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]; rx = x - Z @ np.linalg.lstsq(Z, x, rcond=None)[0]
    r = stats.spearmanr(rx, ry); return dict(rho=round(float(r.statistic), 3), p=float(r.pvalue))
out['collinearity'] = dict(dist_vs_lon=round(float(stats.spearmanr(loc.dist_km, loc.lon).statistic), 3),
                           dist_chudleigh_vs_dist_exeter=round(float(stats.spearmanr(loc.dist_km, loc.dist_exeter_km).statistic), 3))
r = stats.spearmanr(loc.dist_km, loc.days)
out['first_date_vs_dist'] = dict(rho=round(float(r.statistic), 3), p=float(r.pvalue))
out['partial_lon_given_dist'] = partial(loc.days.values, loc.lon.values, loc.dist_km.values)
out['partial_dist_given_lon'] = partial(loc.days.values, loc.dist_km.values, loc.lon.values)
dv = loc[loc.county == 'Devon']
out['devon_only'] = dict(n=int(len(dv)), lon=round(float(stats.spearmanr(dv.lon, dv.days).statistic), 3), lon_p=float(stats.spearmanr(dv.lon, dv.days).pvalue),
                         partial_lon_given_dist=partial(dv.days.values, dv.lon.values, dv.dist_km.values))
# distance bands, by county: same distance from the bishop, either side of the Tamar
loc['band'] = pd.cut(loc.dist_km, [0, 20, 40, 60, 80, 200], labels=['0-20', '20-40', '40-60', '60-80', '80+'])
bands = loc.groupby(['band', 'county'], observed=True).days.agg(['size', 'median']).reset_index()
out['median_days_by_band_county'] = [dict(band=str(b.band), county=b.county, n=int(b['size']),
                                          median=str((pd.Timestamp('1348-11-01') + pd.Timedelta(days=float(b['median']))).date())) for _, b in bands.iterrows()]
mid = loc[(loc.dist_km >= 40) & (loc.dist_km < 80)]
out['band_40_80'] = {c: dict(n=int(len(g)), median_day=float(g.days.median()),
                             median_date=str((pd.Timestamp('1348-11-01') + pd.Timedelta(days=float(g.days.median()))).date()))
                     for c, g in mid.groupby('county')}
where = plague.text.str.extract(r'\(at ([A-Z][a-z]+)', expand=False).str[:4]
out['place_of_institution_nov48_dec49'] = where.value_counts().to_dict()
loc[['lat', 'lon', 'county', 'date', 'days', 'dist_km', 'cause', 'name']].to_csv('first_institution_1348_49.csv')

# 7. counties
ct2 = pd.crosstab(d.dt.dt.year, d.county)
out['county_per_year'] = {c: {int(k): int(v) for k, v in ct2[c].items()} for c in ct2}
out['county_ratio_1349_vs_1340_47'] = {c: round(ct2.loc[1349, c] / ct2.loc[1340:1347, c].mean(), 1) for c in ct2}

# 8. Devon pollen sites (Izdebski et al. 2022) — nearest parish church with a plague-period institution
sys.path.insert(0, '../pollen')
import os
cwd = os.getcwd(); os.chdir('../pollen')
from load import load
p = load(); os.chdir(cwd)
dev = p[p.region == 'England: Devon']
sites = dev.groupby('site').agg(name=('Name', 'first'), lat=('Latitude', 'first'), lon=('Longitude', 'first'),
                                cereal_n=('cereals', lambda s: int(s.notna().sum())))
res = []
for s, r in sites.iterrows():
    dd = km((r.lat, r.lon), loc.lat.values, loc.lon.values)
    j = int(np.argmin(dd))
    res.append(dict(site=s, name=r['name'], cereal_samples=int(r.cereal_n), nearest=loc.index[j], km=round(float(dd[j]), 1)))
out['devon_pollen_nearest_parish'] = res
json.dump(out, open('feasibility_results.json', 'w'), indent=1, default=str)
print(json.dumps({k: out[k] for k in ['validation', 'cause_stated', 'parish_churches_nov48_dec49', 'parish_churches_1349', 'median_first_date',
                                      'collinearity', 'partial_lon_given_dist', 'devon_only', 'band_40_80', 'county_ratio_1349_vs_1340_47']}, indent=1, default=str))
for x in res:
    print(x)

# 9. the second pestilence, 1361–62 (same register, same clerks)
def wave(a, b):
    w = d[(d.dt >= a) & (d.dt < b)]
    rv = w[w.parish_church]
    return dict(n=int(len(w)), months=int(len(pd.period_range(a, pd.Timestamp(b) - pd.Timedelta(days=1), freq='M'))),
                stated=int((w.cause != '').sum()), death=int((w.cause == 'death').sum()),
                rv_n=int(len(rv)), rv_stated=int((rv.cause != '').sum()), rv_death=int((rv.cause == 'death').sum()), rv_resign=int((rv.cause == 'resignation').sum()))
out['wave_1348_49'] = wave('1348-11-01', '1350-01-01')
out['wave_1361_62'] = wave('1361-10-01', '1362-08-01')
out['between_1352_60'] = wave('1352-01-01', '1361-01-01')
out['pre_1345_48H1'] = wave('1345-01-01', '1348-07-01')
base2 = len(d[(d.dt.dt.year >= 1354) & (d.dt.dt.year <= 1360)]) / 84
ex1 = out['wave_1348_49']['n'] - out['wave_1348_49']['months'] * out['baseline_1340_47_mean'] / 12
ex2 = out['wave_1361_62']['n'] - out['wave_1361_62']['months'] * base2
out['second_wave'] = dict(baseline_per_month_1354_60=round(base2, 2), excess_1348_49=round(ex1, 1), excess_1361_62=round(ex2, 1), ratio=round(ex2 / ex1, 2),
                          monthly={str(k): int(v) for k, v in mc.loc['1361-06':'1362-12'].items()})
editor61 = {'1361-10': 12, '1361-11': 24, '1361-12': 20, '1362-01': 28, '1362-02': 26, '1362-03': 24, '1362-04': 15, '1362-05': 7}
out['second_wave']['editor_vs_ours'] = {k: dict(editor=v, ours=int(mc.get(pd.Period(k), 0))) for k, v in editor61.items()}
json.dump(out, open('feasibility_results.json', 'w'), indent=1, default=str)
print(json.dumps({k: out[k] for k in ['wave_1348_49', 'wave_1361_62', 'between_1352_60', 'pre_1345_48H1', 'second_wave']}, indent=1))
