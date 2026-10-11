"""Step 1: reproduce the paper's regional test (cereals, 1250-1350 vs 1351-1450, bootstrap BCa)."""
import numpy as np, pandas as pd, json
from scipy.stats import bootstrap
from load import load
d = load(); d = d[d.cereals.notna()]
d['per'] = np.where(d.Year <= 1350, 'pre', 'post')
d = d[(d.Year >= 1250) & (d.Year <= 1450)]
rng = np.random.default_rng(0)
def diffmean(a, b, axis=-1): return np.mean(b, axis=axis) - np.mean(a, axis=axis)
rows = []
for reg, g in d.groupby('region'):
    pre = g[g.per == 'pre'].cereals.values; post = g[g.per == 'post'].cereals.values
    # variant A: pool all samples (what the replication file most directly supports)
    res = bootstrap((pre, post), diffmean, n_resamples=10000, method='BCa', confidence_level=0.95, random_state=rng)
    res90 = bootstrap((pre, post), diffmean, n_resamples=10000, method='BCa', confidence_level=0.90, random_state=rng)
    # variant B: equal weight per site (site means per period, sites present in both periods)
    sm = g.groupby(['site', 'per']).cereals.mean().unstack()
    both = sm.dropna()
    rows.append(dict(region=reg, sites=g.site.nunique(), n_pre=len(pre), n_post=len(post), sites_both=len(both),
                     diff=float(diffmean(pre, post)), lo95=res.confidence_interval.low, hi95=res.confidence_interval.high,
                     lo90=res90.confidence_interval.low, hi90=res90.confidence_interval.high,
                     diff_sitewise=float((both['post'] - both['pre']).mean()) if len(both) else np.nan))
r = pd.DataFrame(rows).sort_values('diff')
def cat(x):
    if x.lo95 > 0: return '1 sig. increase'
    if x.hi95 < 0: return '4 sig. decrease'
    return '2 n.s. increase' if x['diff'] > 0 else '3 n.s. decrease'
r['scenario'] = r.apply(cat, axis=1)
pd.set_option('display.width', 200)
print(r.round(2).to_string(index=False))
r.to_csv('regional_cereals.csv', index=False)
print(r.scenario.value_counts().sort_index())
