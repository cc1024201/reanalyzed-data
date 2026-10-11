"""Parse Bishop Grandisson's Register of Institutions (Hingeston-Randolph ed., pt. III, 1899;
archive.org id registerofjohnde03exet, djvu OCR) into one row per institution/collation.

The edition's layout: blank-line separated paragraphs —
  heading   e.g. "Ashburton [Aspertone, MS.], V."   /  "Exeter ; St. Martin's, R."
  cause     e.g. "On the death of" + name (optional; usually absent)
  entry     e.g. "Sir Richard Yurl, priest, was inst. (at Chudleigh), 1 Jan., 1348-9 ; Patrons, ..."

Output institutions.csv: idx, line, place, place_raw, benefice, cause, date (ISO, new-style year), year_src, text
cause: death / resignation / exchange / ... / '' (not stated)
"""
import re, csv, datetime as dt

SRC = 'grandisson_pt3_djvu.txt'
L0, L1 = 9000, 28180         # Register of Institutions in this volume (1327 .. 1369); editor's appendix lists and index follow ~27935+
MONTHS = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7,
          'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}

raw = [re.sub(r'[ \t]+', ' ', l).strip() for l in open(SRC, encoding='utf-8')][L0:L1]

verb = re.compile(r'\b(?:was|were)\s+(?:inst\b|inst[,.]|instituted|collated|admitted|preferred)', re.I)
date_re = re.compile(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?'
                     r'(?:\s*,?\s*(1[34]\d\d)(?:\s*-\s*(\d{1,2}))?)?', re.I)
cause_re = re.compile(r'^\W{0,3}\d*\.?\s*On the (death|Resignation|Exchange|Cession|Promotion|Deprivation)', re.I)
skip_re = re.compile(r'INSTITUTIONS,?\s*ETC|^\d{3,4} THE REGISTER|^THE REGISTER', re.I)
benef_re = re.compile(r'[,;]\s*(R|V)\.?\s*$|[,;]?\s*—\s*$|\bMS\.\]')

# pontifical-year running heads ("INSTITUTIONS, ETC. — ANNO 22°."): Grandisson's year N runs ~18 Oct (1326+N) .. 17 Oct (1327+N)
anno_re = re.compile(r'INSTITUTIONS,?\s*ETC\.?,?\s*[—-]+\s*ANNO\s*(\d{1,2})')
anno_at, cur_anno = {}, None
# paragraphs with their first line number
paras, cur, start = [], [], None
for i, ln in enumerate(raw):
    am = anno_re.search(ln)
    if am:
        a = int(am.group(1))
        if cur_anno is None or 0 <= a - cur_anno <= 1:   # ignore OCR misreads that jump
            cur_anno = a
    anno_at[i] = cur_anno
    if not ln or skip_re.search(ln):
        if cur and not ln:
            paras.append((start, cur)); cur = []
        continue
    if not cur:
        start = i
    cur.append(ln)
if cur:
    paras.append((start, cur))


def is_heading(lines):
    t = ' '.join(lines)
    if len(lines) > 3 or len(t) > 170 or verb.search(t) or cause_re.match(t):
        return False
    if re.match(r'^\W{0,4}(Sir|Master|Brother|Dom|John|William|Letters|Mandate|See|The following)\b', t):
        return False
    return bool(benef_re.search(t))


rows, head, cause = [], ('', ''), ''
y, m = None, None
for start, lines in paras:
    t = ' '.join(lines)
    if is_heading(lines):
        # keep only the place line(s): drop Latin month/year rubrics and margin junk merged into the paragraph
        k = max(j for j, l in enumerate(lines) if benef_re.search(l) or j == 0)
        hl = lines[k] if (k > 0 or len(lines) == 1) else ' '.join(lines)
        if k > 0 and not re.match(r'^\W*[A-Z][a-z]', hl) and len(hl) < 60:
            hl = lines[k - 1] + ' ' + hl
        hl = re.sub(r'^.*?\b(?:[a-z]*bris|[a-z]*ii|Aprilis|[Mm]aii|[Jj]unii|[Jj]ulii|incipien\w*|inripi\w*)\W+(?=[A-Z])', '', hl)
        hl = re.sub(r'^(?:(?!St[.-]|ST[.-])[^A-Za-z]*[A-Za-z]{0,3}[^A-Za-z\s]+\s*)+(?=[A-Z][a-zA-Z])', '', hl)
        head, cause = (hl, re.sub(r'\[.*$|[,;:].*$', '', hl)), ''
        continue
    c = cause_re.match(t)
    if c:
        cause = c.group(1).lower()
        if not verb.search(t):
            continue
    for vm in verb.finditer(t):
        dm = date_re.search(t[vm.end():vm.end() + 220])
        if not dm:
            continue
        d, mon = int(dm.group(1)), MONTHS[dm.group(2)[:3].lower()]
        src = 'inferred'
        if dm.group(3):
            yy = int(dm.group(3)) + (1 if dm.group(4) else 0)   # "1348-9" old style -> 1349
            y, src = yy, 'explicit'
        elif y is not None and m is not None and mon < m - 3:
            y += 1
        m = mon
        if y is None:
            continue
        try:
            iso = dt.date(y, mon, d).isoformat()
        except ValueError:
            continue
        # anchor inferred years to the page's pontifical year (allow ~2 months slack for out-of-order entries)
        an = anno_at.get(start)
        if src == 'inferred' and an:
            lo, hi = dt.date(1326 + an, 10, 18) - dt.timedelta(days=60), dt.date(1327 + an, 10, 17) + dt.timedelta(days=60)
            if not (lo <= dt.date(y, mon, min(d, 28)) <= hi):
                for yy in (1326 + an, 1327 + an):
                    try:
                        cand = dt.date(yy, mon, d)
                    except ValueError:
                        continue
                    if lo <= cand <= hi:
                        y, iso, src = yy, cand.isoformat(), 'anno'
                        break
        bm = re.search(r'[,;]\s*(R|V)\.?\s*$', head[0])
        rows.append(dict(line=L0 + start + 1, place=head[1].strip(), place_raw=head[0], benefice=bm.group(1) if bm else 'other',
                         cause=cause, date=iso, year_src=src, text=t[:600]))
        break   # one institution per paragraph unless it clearly holds two (handled below)
    else:
        continue
    # paragraphs like Ashburton's "inst. 1 Jan., and the Benefice was soon vacant again; for X was inst. 11 Jan."
    extra = list(verb.finditer(t))[1:]
    for vm in extra:
        if 'vacant again' in t or 'again vacant' in t:
            dm = date_re.search(t[vm.end():vm.end() + 120])
            if dm:
                mon = MONTHS[dm.group(2)[:3].lower()]
                rows.append(dict(rows[-1], date=dt.date(y, mon, int(dm.group(1))).isoformat(), year_src='inferred',
                                 text=t[max(0, vm.start() - 90):vm.end() + 80]))

# drop duplicates: the same R/V benefice instituted twice on the same day is a cross-reference
# (e.g. Ashburton's "Yurl was inst. 1 Jan., and the Benefice was soon vacant again"), not a new event
seen, kept = set(), []
for r in rows:
    k = (re.sub(r'\[[^\]]*\]', '', r['place_raw']).lower(), r['date'])
    if r['benefice'] in ('R', 'V') and k in seen:
        continue
    seen.add(k); kept.append(r)
rows = kept
# broader cause flag: any reason mentioned in the entry paragraph (exchange, resignation, death), not only headings
for r in rows:
    t = r['text'].lower()
    r['cause_any'] = r['cause'] or next((c for c, kw in (('exchange', 'exchang'), ('resignation', 'resign'),
                                                          ('death', 'died'), ('death', 'death'), ('deprivation', 'depriv')) if kw in t), '')

with open('institutions.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['idx'] + list(rows[0]))
    w.writeheader()
    for k, r in enumerate(rows):
        w.writerow(dict(idx=k, **r))
print(len(rows), 'rows;', sum(1 for r in rows if not r['place']), 'without heading')
