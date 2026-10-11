"""Step 2: our own checks on top of the reproduction.
 (a) Is the between-region variation real, or could noise alone produce it?  (site-label permutation)
 (b) Europe-wide average change (each site weighted equally)
 (c) For each region: could it have declined as much as Sweden did?  (bootstrap of region minus Sweden)
 (d) Fragility: does the region's verdict survive dropping any single site?"""
import numpy as np, pandas as pd, json
from load import load
rng = np.random.default_rng(1)
d = load(); d = d[d.cereals.notna() & (d.Year >= 1250) & (d.Year <= 1450)].copy()
d['per'] = np.where(d.Year <= 1350, 'pre', 'post')
sm = d.groupby(['region', 'site', 'per']).cereals.mean().unstack().dropna()
sm['delta'] = sm['post'] - sm['pre']; s = sm.reset_index()[['region', 'site', 'delta']]
out = {}
# (a) permutation test on between-region variance of regional mean deltas (site-weighted)
def between_var(df):
    m = df.groupby('region').delta.mean(); n = df.groupby('region').size()
    return float(np.average((m - df.delta.mean()) ** 2, weights=n))
obs = between_var(s); perm = []
for _ in range(10000):
    t = s.copy(); t['region'] = rng.permutation(t.region.values); perm.append(between_var(t))
perm = np.array(perm); out['heterogeneity'] = dict(observed=obs, perm_mean=float(perm.mean()), p=float((perm >= obs).mean()), n_sites=len(s))
# (b) Europe-wide mean of site deltas
bs = [rng.choice(s.delta.values, len(s)).mean() for _ in range(10000)]
out['europe_mean'] = dict(mean=float(s.delta.mean()), lo95=float(np.percentile(bs, 2.5)), hi95=float(np.percentile(bs, 97.5)),
                          frac_sites_down=float((s.delta < 0).mean()))
# region-weighted (each region equal)
rm = s.groupby('region').delta.mean(); out['europe_mean']['region_weighted'] = float(rm.mean())
# (c) compare each region to Sweden (site-level bootstrap)
sw = s[s.region == 'Sweden'].delta.values; rows = []
for reg, g in s.groupby('region'):
    x = g.delta.values; boot = np.array([rng.choice(x, len(x)).mean() - rng.choice(sw, len(sw)).mean() for _ in range(10000)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    # (d) leave-one-site-out
    loo = [np.delete(x, i).mean() for i in range(len(x))] if len(x) > 1 else [x.mean()]
    rows.append(dict(region=reg, sites=len(x), delta=x.mean(), vs_sweden_lo=lo, vs_sweden_hi=hi,
                     less_hit_than_sweden=bool(lo > 0), loo_min=min(loo), loo_max=max(loo), sign_flips=bool(min(loo) < 0 < max(loo))))
c = pd.DataFrame(rows).sort_values('delta'); out['regions'] = c.round(3).to_dict('records')
pd.set_option('display.width', 200); print(c.round(2).to_string(index=False))
print(json.dumps({k: v for k, v in out.items() if k != 'regions'}, indent=1))
json.dump(out, open('audit_results.json', 'w'), indent=1)
