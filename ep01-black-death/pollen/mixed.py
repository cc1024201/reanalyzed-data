"""Sensitivity check for pseudo-replication in Izdebski et al. (2022) regional cereal comparisons
(1250–1350 vs 1351–1450). Per region:
 (a) pooled OLS, naive SEs (~ the paper's sample-level approach)
 (b) pooled OLS, site-clustered SEs with small-sample t reference (use_t)
 (c) mixed model, random intercept + random 'after' slope by site (convergence recorded)
 (d) mixed model, random intercept only
Writes mixed_results.csv."""
import warnings
import pandas as pd, numpy as np
import statsmodels.formula.api as smf
from load import load
d = load()
d = d[(d.Year >= 1250) & (d.Year <= 1450) & d.cereals.notna()].copy()
d['after'] = (d.Year > 1350).astype(int)
rows = []
for reg, g in d.groupby('region'):
    g = g[g.groupby('site').after.transform('nunique') == 2]
    if g.site.nunique() < 3: continue
    r = dict(region=reg, sites=g.site.nunique(), samples=len(g))
    ols = smf.ols('cereals ~ after', g).fit()
    r.update(est=ols.params['after'], p_naive=ols.pvalues['after'])
    cl = smf.ols('cereals ~ after', g).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(g.site)[0]}, use_t=True)
    r.update(p_cluster_t=cl.pvalues['after'])
    for name, re_f in [('slope', '~after'), ('int', None)]:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            try:
                m = smf.mixedlm('cereals ~ after', g, groups=g['site'], re_formula=re_f).fit(reml=True, method='lbfgs')
                r[f'p_mixed_{name}'] = m.pvalues['after']; r[f'conv_{name}'] = bool(m.converged) and not any('converge' in str(x.message).lower() or 'boundary' in str(x.message).lower() for x in w)
            except Exception:
                r[f'p_mixed_{name}'] = np.nan; r[f'conv_{name}'] = False
    rows.append(r)
out = pd.DataFrame(rows).round(3)
out.to_csv('mixed_results.csv', index=False)
print(out.to_string(index=False))
for col in ['p_naive', 'p_cluster_t', 'p_mixed_slope', 'p_mixed_int']:
    sig = out[out[col] < 0.05]
    print(f'{col:14} clear: down {list(sig[sig.est < 0].region)} | up {list(sig[sig.est > 0].region)}')
