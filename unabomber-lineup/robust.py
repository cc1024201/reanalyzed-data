"""Robustness of the 1996 lineup (letters + 1971 essay, no later essays): Delta vs cosine Delta, chunk sizes, random chunk caps."""
import re, glob, os, json, numpy as np, collections, itertools
C = 'analysis/corpus'
GROUP = {'john-zerzan': 'Zerzan', 'neil-postman': 'Postman', 'kirkpatrick-sale': 'Sale', 'lewis-mumford': 'Mumford', 'fredy-perlman': 'Perlman', 'paul-goodman': 'Goodman',
         'ivan-illich': 'Illich', 'edward-abbey': 'Abbey', 'wendell-berry': 'Berry', 'TED_letters': 'K-letters', 'TED_1971': 'K-1971', 'MANIFESTO': 'MANIFESTO'}
def toks(t):
    t = re.sub(r'Letter from T\. Kaczynski to [^.]*T-\d+\.|Original link: \[now dead\]', ' ', t)
    return re.findall(r"[a-z]+(?:'[a-z]+)?", t.lower().replace('’', "'"))
docs = collections.defaultdict(list)
for f in glob.glob(f'{C}/*.txt'):
    b = os.path.basename(f)[:-4]; g = next((v for k, v in GROUP.items() if b.startswith(k)), None)
    if g: docs[g] += toks(open(f).read())
def run(N, CH, seed, metric, cap=30):
    r = np.random.default_rng(seed); sel = []
    for g, w in docs.items():
        cs = [w[i:i + CH] for i in range(0, len(w) - CH + 1, CH)]
        if g == 'K-1971' and not cs: cs = [w]
        idx = range(len(cs)) if g in ('MANIFESTO', 'K-1971') else r.permutation(len(cs))[:cap]
        sel += [(g, collections.Counter(cs[i]), len(cs[i])) for i in idx]
    tot = collections.Counter()
    for g, c, n in sel:
        if g != 'MANIFESTO': tot.update(c)
    mfw = [w for w, _ in tot.most_common(N)]
    X = np.array([[c[w] / n for w in mfw] for _, c, n in sel]); lab = np.array([g for g, _, _ in sel])
    ref = lab != 'MANIFESTO'; Z = (X - X[ref].mean(0)) / (X[ref].std(0) + 1e-12)
    M = Z[lab == 'MANIFESTO'].mean(0)
    out = {}
    for a in sorted(set(lab[ref])):
        c = Z[lab == a].mean(0)
        out[a] = float(np.abs(M - c).mean()) if metric == 'delta' else float(1 - M @ c / np.linalg.norm(M) / np.linalg.norm(c))
    return out
if __name__ == '__main__':
    rows = []
    for N, CH, seed, metric in itertools.product((100, 200, 300, 500), (1000, 2000, 3000), range(5), ('delta', 'cosine')):
        d = run(N, CH, seed, metric); rk = sorted(d, key=d.get)
        rows.append(dict(N=N, CH=CH, seed=seed, metric=metric, first=rk[0], rank_1971=rk.index('K-1971') + 1, rank_letters=rk.index('K-letters') + 1,
                         gap=(d['K-1971'] - d['Goodman']) / d['Goodman']))
    json.dump(rows, open('analysis/robust.json', 'w'), indent=0)
    for m in ('delta', 'cosine'):
        R = [x for x in rows if x['metric'] == m]
        print(m, len(R), 'first:', dict(collections.Counter(x['first'] for x in R)), '1971 rank:', dict(collections.Counter(x['rank_1971'] for x in R)),
              'letters rank:', dict(collections.Counter(x['rank_letters'] for x in R)), 'median gap vs Goodman %.3f' % np.median([x['gap'] for x in R]))
