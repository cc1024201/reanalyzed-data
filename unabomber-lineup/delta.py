"""Burrows' Delta lineup: which author's known writing is closest to the 1995 manifesto?"""
import re, glob, os, json, numpy as np, collections
C = 'analysis/corpus'
def toks(t):
    t = re.sub(r'Letter from T\. Kaczynski to [^.]*T-\d+\.|Original link: \[now dead\]|ENVELOPE.*?(?=[A-Z][a-z])', ' ', t)
    return re.findall(r"[a-z]+(?:'[a-z]+)?", t.lower().replace('’', "'"))
GROUP = {'john-zerzan': 'Zerzan', 'neil-postman': 'Postman', 'kirkpatrick-sale': 'Sale', 'lewis-mumford': 'Mumford', 'fredy-perlman': 'Perlman',
         'paul-goodman': 'Goodman', 'ivan-illich': 'Illich', 'edward-abbey': 'Abbey', 'wendell-berry': 'Berry', 'TED_letters': 'Kaczynski (letters)', 'TED_later': 'Kaczynski (later essays)', 'TED_1971': 'Kaczynski (1971 essay)', 'MANIFESTO': 'MANIFESTO'}
import sys
EXCL = set(sys.argv[1].split(',')) if len(sys.argv) > 1 and sys.argv[1] else set()
NOPRON = len(sys.argv) > 2 and sys.argv[2] == 'nopron'
PRON = set('i me my mine myself you your yours yourself we us our ours he him his she her hers they them their it its'.split())
docs = collections.defaultdict(list)
for f in glob.glob(f'{C}/*.txt'):
    b = os.path.basename(f)[:-4]; g = next((v for k, v in GROUP.items() if b.startswith(k)), None)
    if g and g not in EXCL: docs[g] += [w for w in toks(open(f).read()) if not (NOPRON and w in PRON)]
CH = 2000
chunks = [(g, w[i:i + CH]) for g, w in docs.items() for i in range(0, len(w) - CH + 1, CH)]
def run(N, rng=None, cap=40):
    # cap chunks per author so big books don't dominate
    r = np.random.default_rng(rng); sel = []
    for g in docs:
        cs = [c for c in chunks if c[0] == g]; idx = r.permutation(len(cs))[:cap] if g != 'MANIFESTO' else range(len(cs)); sel += [cs[i] for i in idx]
    allw = collections.Counter(w for g, c in sel if g != 'MANIFESTO' for w in c); mfw = [w for w, _ in allw.most_common(N)]
    X = np.array([[collections.Counter(c)[w] / CH for w in mfw] for _, c in sel]); lab = [g for g, _ in sel]
    ref = np.array([l != 'MANIFESTO' for l in lab]); mu, sd = X[ref].mean(0), X[ref].std(0) + 1e-12; Z = (X - mu) / sd
    authors = sorted(set(l for l in lab if l != 'MANIFESTO'))
    cent = {a: Z[[i for i, l in enumerate(lab) if l == a]].mean(0) for a in authors}
    M = Z[[i for i, l in enumerate(lab) if l == 'MANIFESTO']]
    D = {a: np.abs(M - cent[a]).mean(1) for a in authors}   # per manifesto chunk
    # leave-one-out accuracy on known chunks
    ok = 0; n = 0
    for i, l in enumerate(lab):
        if l == 'MANIFESTO': continue
        best = None
        for a in authors:
            ids = [j for j, m in enumerate(lab) if m == a and j != i]
            d = np.abs(Z[i] - Z[ids].mean(0)).mean()
            if best is None or d < best[0]: best = (d, a)
        ok += best[1] == l; n += 1
    return authors, D, ok / n
if __name__ == '__main__':
    print({g: len(w) for g, w in docs.items()})
    res = {}
    for N in (100, 200, 300, 500):
        authors, D, acc = run(N, 0)
        whole = {a: float(D[a].mean()) for a in authors}; win = collections.Counter(min(authors, key=lambda a: D[a][k]) for k in range(len(D[authors[0]])))
        rank = sorted(whole, key=whole.get)
        print(N, 'LOO acc %.2f' % acc, 'ranking:', [(a, round(whole[a], 3)) for a in rank][:5], 'chunk wins:', dict(win))
        res[N] = dict(acc=acc, whole=whole, wins=dict(win))
    json.dump(res, open('analysis/delta_%s%s.json' % ('without_later' if EXCL else 'with_later', '_nopron' if NOPRON else ''), 'w'), indent=1)
    for N, v in res.items(): rk = sorted(v['whole'], key=v['whole'].get); print(N, [(i + 1, a) for i, a in enumerate(rk) if 'Kacz' in a], rk[:3])
