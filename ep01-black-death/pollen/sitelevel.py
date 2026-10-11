"""Step 3 (after independent review): treat each SITE, not each sample, as one piece of evidence.
Samples from one core are not independent, and well-sampled cores dominate a pooled average.
Also: per-site standardisation means a site with exactly one sample per century can only show direction:
its change comes out at about +/-1.41 SD (or 0, or a fraction when cereal taxa disagree), whatever the real change.
'Clear' in the narration = t-test over sites, p < 0.05. BCa intervals with only 4 sites are unreliable
(e.g. Norway's interval excludes zero but 3 of its 4 sites are one-sample-per-century sites)."""
import numpy as np, pandas as pd, json
from scipy import stats
from scipy.stats import bootstrap
from load import load
d = load(); d = d[d.cereals.notna() & (d.Year >= 1250) & (d.Year <= 1450)].copy()
d['per'] = np.where(d.Year <= 1350, 'pre', 'post')
n = d.groupby(['site', 'per']).size().unstack(fill_value=0)
sm = d.groupby(['region', 'site', 'per']).cereals.mean().unstack().dropna()
sm['delta'] = sm.post - sm.pre; s = sm.reset_index()
s['rich'] = s.site.map(lambda x: n.loc[x, 'pre'] >= 2 and n.loc[x, 'post'] >= 2)
s['one_each'] = s.site.map(lambda x: n.loc[x, 'pre'] == 1 and n.loc[x, 'post'] == 1)
rng = np.random.default_rng(2); rows = []
sw = s[s.region == 'Sweden'].delta.values
for reg, g in s.groupby('region'):
    x = g.delta.values
    t = stats.ttest_1samp(x, 0) if len(x) > 1 else None
    bc = bootstrap((x,), np.mean, n_resamples=10000, method='BCa', random_state=rng).confidence_interval if len(x) > 2 else None
    w = stats.ttest_ind(x, sw, equal_var=False, alternative='greater') if reg != 'Sweden' else None
    rows.append(dict(region=reg, sites=len(x), rich_sites=int(g.rich.sum()), thin_sites=int((~g.rich).sum()), one_each_sites=int(g.one_each.sum()),
                     mean=x.mean(), lo95=bc.low if bc else np.nan, hi95=bc.high if bc else np.nan, t_p=t.pvalue if t else np.nan,
                     better_than_sweden_p=w.pvalue if w else np.nan))
r = pd.DataFrame(rows)
# Holm correction across the 20 comparisons with Sweden
m = r.better_than_sweden_p.notna(); p = r.loc[m, 'better_than_sweden_p'].values; order = np.argsort(p); k = len(p)
holm = np.empty(k); run = 0
for i, j in enumerate(order): run = max(run, min(1, (k - i) * p[j])); holm[j] = run
r.loc[m, 'holm_p'] = holm
r['sig_site_level'] = np.where(r.t_p < 0.05, np.where(r['mean'] < 0, 'decline', 'rise'), '')
r = r.sort_values('mean'); pd.set_option('display.width', 220)
print(r.round(3).to_string(index=False))
print('thin sites (<2 samples in at least one century):', int((~s.rich).sum()), 'of', len(s))
oe = s[s.one_each]; print('sites with exactly one sample per century (direction only):', len(oe), '| change values:', oe.delta.round(2).value_counts().to_dict())
# Europe-wide on rich sites only
rich = s[s.rich].delta; print('Europe mean, sites with >=2 samples per period:', round(rich.mean(), 3), 'frac down', round((rich < 0).mean(), 3), 'n', len(rich))
r.to_csv('sitelevel_results.csv', index=False)

# 25-year bins (site-equal means) for the two "possible decline" regions — used for the
# "in France the decline may have begun earlier" line. Coarse: median sample spacing ~50 yr.
for reg in ['France: Central', 'Greece']:
    g = d[d.region == reg].copy(); g['bin'] = (g.Year // 25 * 25).astype(int)
    b = g.groupby(['bin', 'site']).cereals.mean().groupby('bin').mean().round(2)
    print(reg, '25-yr bins:', b.to_dict())
