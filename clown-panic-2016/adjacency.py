"""Did the 2016 clown wave spread state-to-state like a contagion between neighbours, or jump like news?
For each state's first report: was a neighbouring state already reporting? Compare with random orderings (same dates, shuffled states)."""
import csv, json, random, collections, datetime as dt
ADJ = {'AL':'FL GA MS TN','AK':'','AZ':'CA CO NM NV UT','AR':'LA MO MS OK TN TX','CA':'AZ NV OR','CO':'AZ KS NE NM OK UT WY','CT':'MA NY RI','DE':'MD NJ PA',
'DC':'MD VA','FL':'AL GA','GA':'AL FL NC SC TN','HI':'','ID':'MT NV OR UT WA WY','IL':'IA IN KY MO WI','IN':'IL KY MI OH','IA':'IL MN MO NE SD WI','KS':'CO MO NE OK',
'KY':'IL IN MO OH TN VA WV','LA':'AR MS TX','ME':'NH','MD':'DC DE PA VA WV','MA':'CT NH NY RI VT','MI':'IN OH WI','MN':'IA ND SD WI','MS':'AL AR LA TN',
'MO':'AR IA IL KS KY NE OK TN','MT':'ID ND SD WY','NE':'CO IA KS MO SD WY','NV':'AZ CA ID OR UT','NH':'MA ME VT','NJ':'DE NY PA','NM':'AZ CO OK TX UT',
'NY':'CT MA NJ PA VT','NC':'GA SC TN VA','ND':'MN MT SD','OH':'IN KY MI PA WV','OK':'AR CO KS MO NM TX','OR':'CA ID NV WA','PA':'DE MD NJ NY OH WV',
'RI':'CT MA','SC':'GA NC','SD':'IA MN MT ND NE WY','TN':'AL AR GA KY MO MS NC VA','TX':'AR LA NM OK','UT':'AZ CO ID NM NV WY','VT':'MA NH NY',
'VA':'DC KY MD NC TN WV','WA':'ID OR','WV':'KY MD OH PA VA','WI':'IA IL MI MN','WY':'CO ID MT NE SD UT'}
ADJ = {k: set(v.split()) for k, v in ADJ.items()}
for k, v in ADJ.items():
    for n in v: assert k in ADJ[n], (k, n)
R = list(csv.DictReader(open('research/sightings.csv')))
first = {}
for r in R:
    s = r['us_state']
    if not s or s == 'PR': continue
    if r['outcome'] == 'hoax or false report' and r['place'] == 'Green Bay': continue   # film marketing stunt, not part of the wave
    if s not in first or r['date'] < first[s]: first[s] = r['date']
order = sorted(first.items(), key=lambda x: (x[1], x[0]))
def frac(order, cut=None):
    seen = set(); res = []
    for s, d in order:
        prior = {x for x, dd in order if dd < d}       # states reporting strictly earlier
        if prior: res.append((s, d, bool(ADJ[s] & prior)))
    return res
obs = frac(order)
def phase(res, lo, hi): x = [a for s, d, a in res if lo <= d <= hi]; return sum(x), len(x)
PH = [('2016-08-01', '2016-09-27'), ('2016-09-28', '2016-10-31')]   # before / after national attention takes off (Google Trends rises from 28 Sep)
print('states', len(order))
out = {}
for lo, hi in PH:
    k, n = phase(obs, lo, hi)
    # null: keep the date sequence, shuffle which state gets which date (within all 51)
    sims = []
    rng = random.Random(1)
    states = [s for s, _ in order]; dates = [d for _, d in order]
    for _ in range(20000):
        sh = states[:]; rng.shuffle(sh); o2 = list(zip(sh, dates)); k2, n2 = phase(frac(o2), lo, hi); sims.append(k2 / n2 if n2 else 0)
    p = sum(1 for x in sims if x >= k / n) / len(sims)
    out[f'{lo}..{hi}'] = dict(adjacent=k, n=n, share=k / n, null_mean=sum(sims) / len(sims), p_ge=p)
    print(lo, hi, f'{k}/{n} = {k/n:.2f} adjacent; random ordering mean {sum(sims)/len(sims):.2f}; P(random >= observed) = {p:.4f}')
for s, d, a in obs: print(d, s, 'neighbour' if a else 'JUMP')
json.dump(dict(phases=out, order=order, detail=obs), open('analysis/adjacency.json', 'w'), indent=1)
