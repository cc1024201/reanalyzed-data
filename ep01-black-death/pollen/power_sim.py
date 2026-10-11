"""Monte Carlo: if Devon's grain pollen had dropped as much as south-west Germany's (estimated from the same data),
how often would Devon's 13 bogs, sampled exactly as they are, show a clear drop (site-clustered OLS, small-sample t, p<0.05)?
Variance components (site intercept, site slope, residual) from Devon's own mixed model; design (sites, sample counts
before/after) kept as is. Writes power_sim.json."""
import json, warnings, numpy as np, pandas as pd
import statsmodels.formula.api as smf
from load import load
warnings.simplefilter('ignore')
d = load(); d = d[(d.Year >= 1250) & (d.Year <= 1450) & d.cereals.notna()].copy()
d['after'] = (d.Year > 1350).astype(int)
def prep(reg):
    g = d[d.region == reg]; return g[g.groupby('site').after.transform('nunique') == 2].copy()
dev = prep([r for r in d.region.unique() if 'Devon' in r or 'England' in r][0])
swg = prep('Germany: South-West')
eff = smf.ols('cereals ~ after', swg).fit().params['after']
m = smf.mixedlm('cereals ~ after', dev, groups=dev['site'], re_formula='~after').fit(reml=True, method='lbfgs')
cov = np.array(m.cov_re); sd_e = np.sqrt(m.scale)
rng = np.random.default_rng(1349); sites = pd.factorize(dev.site)[0]; ns = sites.max() + 1
def run(beta, N=2000):
    hits = 0; flat = 0
    for _ in range(N):
        re = rng.multivariate_normal([0, 0], cov, ns)
        y = re[sites, 0] + (beta + re[sites, 1]) * dev.after.values + rng.normal(0, sd_e, len(dev))
        g = dev.assign(y=y)
        f = smf.ols('y ~ after', g).fit(cov_type='cluster', cov_kwds={'groups': sites}, use_t=True)
        if f.pvalues['after'] < 0.05 and f.params['after'] < 0: hits += 1
    return hits / N
res = dict(devon_sites=int(ns), devon_samples=len(dev), devon_samples_per_site=dev.groupby('site').size().describe().round(2).to_dict(),
           sites_with_1_before_1_after=int((dev.groupby(['site','after']).size().unstack().eq(1).all(axis=1)).sum()),
           swg_effect=round(float(eff), 3), re_cov=np.round(cov, 4).tolist(), sd_resid=round(float(sd_e), 3),
           power_swg=run(eff), power_2x_swg=run(2 * eff), false_alarm_null=run(0.0))
json.dump(res, open('power_sim.json', 'w'), indent=1); print(json.dumps(res, indent=1))
