"""Geocode register place names against the GeoNames GB dump (download.geonames.org/export/dump/GB.zip, CC-BY 4.0),
bounded to Devon + Cornwall. Prefers civil parishes (ADM4), then populated places.
Manual fixes in geocode_manual.csv (name,lat,lon,note) override everything.
Writes places.csv: name, lat, lon, gn_name, fclass, how
"""
import csv, re, os, collections

BOX = (49.85, 51.3, -6.5, -2.85)
SKIP = {'tone', 'Tone', 'St', 'J', 'L', 'If', 'Ms.]', 'Cornubia', 'ornubia', 'Parochialis', 'Prioris', 'Magistri', 'Custodiarie'}   # OCR junk / non-place headings
PRI = {'ADM4': 0, 'PPL': 1, 'PPLA2': 1, 'PPLA3': 1, 'PPLX': 2, 'PPLL': 3, 'ADM3': 4, 'CH': 5}


def norm(s):
    s = s.lower().replace('&', 'and')
    s = re.sub(r'\bsaint\b|\bst\b\.?', 'st', s)
    s = re.sub(r"[^a-z ]+", ' ', s.replace('-', ' '))
    return re.sub(r'\s+', ' ', s).strip()


def clean(p):
    p = re.sub(r'^(?:A[.-]?\s*[DJ][.-]?\s*|Ajg-\s*|Nota\.?\s*|Sl\s+|Tit\s+)', '', p)     # "A.D." / "Nota" margins
    p = re.sub(r'^(?:[IJLWPKJjkfIL]{1,3}[-.]?\s+|[IJ]{1,2}[jk]?-?(?=[A-Z])|If-?\s+|Jj?i?(?=[a-z]))', '', p)  # margin glyphs
    p = re.sub(r'^[^A-Za-z]*(?:[A-Z][-*^■£«_]+\s+)?', '', p)     # OCR margin junk like "J- "
    p = re.sub(r'\s+', ' ', p).strip(" .,-'")
    if p.isupper() or re.match(r'^[A-Z][A-Z]+[A-Za-z]*$', p.replace('l', 'L')):
        p = p.title()
    p = re.sub(r'^Ll', 'L', p); p = re.sub(r'^Rr', 'B', p)
    p = p.replace('GrL', 'G').replace('ANA', 'ana').replace('Lam ana', 'Lamana')
    if re.search(r'[a-z][A-Z]', p.replace('Mc', '')):
        p = '-'.join(w.capitalize() if w.isalpha() else w for w in p.split('-')) if '-' in p else p.title()
    return p


def load_gn():
    idx = collections.defaultdict(list)
    for r in csv.reader(open(os.path.join(os.path.dirname(__file__) or '.', 'gn/GB.txt'), encoding='utf-8'),
                        delimiter='\t', quoting=csv.QUOTE_NONE):
        lat, lon = float(r[4]), float(r[5])
        if not (BOX[0] < lat < BOX[1] and BOX[2] < lon < BOX[3]) or r[7] not in PRI:
            continue
        names = {r[1], r[2]} | set(r[3].split(',') if r[3] else [])
        for n in names:
            if n:
                idx[norm(n)].append((PRI[r[7]], lat, lon, r[1], r[7], r[11]))
    return idx


def variants(n):
    v = [n]
    b = norm(n)
    v += [b, re.sub(r'\b(bishop|monachorum|abbot|prior|regis|episcopi)\b', '', b).strip()]
    m = re.match(r'(.+?) (st .+)$', b)               # "Exeter St Kerrian" style
    v += [b.replace(' ', ''), b.split(' ')[0]] if ' ' in b and not b.startswith('st ') else []
    b2 = re.sub(r' (in|by) [a-z ]+$', '', b)
    v += [b2, re.sub(r'^st ', '', b2), re.sub(r'^st ', '', b2).replace(' ', '')]
    # common OCR confusions
    for a, c in (('tj', 'u'), ('ji', 'h'), ('tt', 'i'), ('lt', 'it'), ('kl', 'il'), ('l', 'i'), ('bb', 'bu'), ('cn', 'un'), ('x', 'n'), ('ee', 'er'), ('tg', 'ig'), ('rr', 're'), ('k', 'r'), ('dt', 'di')):
        if a in b2:
            v.append(b2.replace(a, c)); v.append(re.sub(r'^st ', '', b2.replace(a, c)))
    return [norm(x) for x in dict.fromkeys(v) if x]


if __name__ == '__main__':
    idx = load_gn()
    manual = {}
    if os.path.exists('geocode_manual.csv'):
        for r in csv.DictReader(open('geocode_manual.csv')):
            manual[r['name']] = r
    rows = list(csv.DictReader(open('institutions.csv')))
    names = sorted({clean(r['place']) for r in rows if r['place']})
    keys = list(idx)
    out, miss = [], []
    for n in names:
        if n in SKIP:
            miss.append(n); continue
        if n in manual:
            m = manual[n]
            out.append(dict(name=n, lat=m['lat'], lon=m['lon'], gn_name=m.get('note', ''), fclass='manual', how='manual'))
            continue
        hit = None
        for k, v in enumerate(variants(n)):
            if v in idx:
                c = sorted(idx[v])[0]
                hit = dict(name=n, lat=c[1], lon=c[2], gn_name=c[3], fclass=c[4], how='exact' if k < 2 else f'variant:{v}')
                break
        if not hit:
            import difflib
            for v in variants(n)[:4] + [re.sub(r'^st ', '', norm(n))]:
                cand = difflib.get_close_matches(v, keys, n=1, cutoff=0.86)
                if cand:
                    c = sorted(idx[cand[0]])[0]
                    hit = dict(name=n, lat=c[1], lon=c[2], gn_name=c[3], fclass=c[4], how=f'fuzzy:{cand[0]}')
                    break
        if hit:
            out.append(hit)
        else:
            miss.append(n)
    # county (GeoNames admin2: D4 Devon, C6 Cornwall, M3 Somerset ...) from the nearest settlement point
    pts = [(v[1], v[2], v[5]) for vs in idx.values() for v in vs if v[4] in ('ADM4', 'PPL', 'PPLX')]
    for o in out:
        la, lo = float(o['lat']), float(o['lon'])
        o['a2'] = min(pts, key=lambda p: (p[0] - la) ** 2 + ((p[1] - lo) * 0.64) ** 2)[2]
    with open('places.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['name', 'lat', 'lon', 'gn_name', 'fclass', 'how', 'a2'])
        w.writeheader(); w.writerows(out)
    print(len(names), 'names;', len(out), 'located;', len(miss), 'missing')
    print(miss)
