"""Topic-free check: restrict features to a fixed list of English function words (no nouns/verbs/adjectives)."""
import sys, json, collections, itertools, numpy as np
sys.argv = ['x']; import robust as R
FW = set("""a about above after again against all am an and any are as at be because been before being below between both but by can could did do does doing down during
each few for from further had has have having he her here hers herself him himself his how i if in into is it its itself just me more most my myself no nor not now of off
on once only or other our ours ourselves out over own same she should so some such than that the their theirs them themselves then there these they this those through to too
under until up upon very was we were what when where which while who whom why will with would you your yours yourself yourselves also although however therefore thus whether
yet either neither though unless whereas since may might must shall one ones""".split())
def run(N, CH, seed, metric, use1971=True, cap=30):
    r = np.random.default_rng(seed); sel = []
    for g, w in R.docs.items():
        if g == 'K-1971' and not use1971: continue
        cs = [w[i:i + CH] for i in range(0, len(w) - CH + 1, CH)]
        idx = range(len(cs)) if g in ('MANIFESTO', 'K-1971') else r.permutation(len(cs))[:cap]
        sel += [(g, collections.Counter(cs[i]), len(cs[i])) for i in idx]
    tot = collections.Counter()
    for g, c, n in sel:
        if g != 'MANIFESTO': tot.update(c)
    mfw = [w for w, _ in tot.most_common() if w in FW][:N]
    X = np.array([[c[w] / n for w in mfw] for _, c, n in sel]); lab = np.array([g for g, _, _ in sel]); ref = lab != 'MANIFESTO'
    Z = (X - X[ref].mean(0)) / (X[ref].std(0) + 1e-12); M = Z[lab == 'MANIFESTO'].mean(0); out = {}
    for a in sorted(set(lab[ref])):
        c = Z[lab == a].mean(0); out[a] = float(np.abs(M - c).mean()) if metric == 'delta' else float(1 - M @ c / np.linalg.norm(M) / np.linalg.norm(c))
    return out
rows = []
for use, N, CH, seed, m in itertools.product((False, True), (50, 100, 150), (1000, 2000), range(3), ('delta', 'cosine')):
    d = run(N, CH, seed, m, use); rk = sorted(d, key=d.get)
    rows.append(dict(with1971=use, N=N, CH=CH, seed=seed, metric=m, first=rk[0], rank_letters=rk.index('K-letters') + 1, rank_1971=(rk.index('K-1971') + 1) if use else None))
json.dump(rows, open('analysis/funcwords.json', 'w'), indent=0)
for use in (False, True):
    for m in ('delta', 'cosine'):
        X = [x for x in rows if x['with1971'] == use and x['metric'] == m]
        print('with1971' if use else 'letters ', m, len(X), 'first', dict(collections.Counter(x['first'] for x in X)), 'letters rank', dict(collections.Counter(x['rank_letters'] for x in X)), ('1971 rank ' + str(dict(collections.Counter(x['rank_1971'] for x in X)))) if use else '')
