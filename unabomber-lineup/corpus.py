"""Build plain-text corpora: Ted's pre-arrest writings (English, Ted-authored only), the manifesto (Washington Post 1995 text), and a lineup of other technology critics."""
import re, glob, os, json
SRC = 'sources'
def clean(t):
    t = re.sub(r'^#.*$', '', t, flags=re.M)                 # muse headers
    t = re.sub(r'\[\d+\]', '', t)                            # footnote marks
    t = re.sub(r'<[^>]+>', ' ', t); t = re.sub(r'\[\[[^\]]*\]\]', ' ', t)
    t = re.sub(r'^\s*\|.*$', '', t, flags=re.M)              # tables
    return re.sub(r'\s+', ' ', t)
def ted_letters():
    s = open(f'{SRC}/ted-kaczynski-david-kaczynski-letters-to-from-david-kaczynski.muse').read()
    s = s[s.index('** Letters from before'):s.index('** Letters After')]
    parts = re.split(r'^(\*{3,4} .*)$', s, flags=re.M)
    keep, cur_ted, out = [], False, []
    for i in range(1, len(parts), 2):
        h, body = parts[i], parts[i + 1]
        if h.startswith('*** '):
            cur_ted = bool(re.match(r'\*\*\* (From Ted|Letter from Ted|Letters Ted sent)', h)); top = h
            sub_ok = True
        else:  # **** subsection
            sub_ok = not re.search(r'translation|original mix|spanish|notes|comments|advertisement|sherman to ted', h, re.I) or re.search(r'Ted to Sherman', h)
        if cur_ted and sub_ok and ('**** ' not in h or sub_ok):
            out.append((top, clean(body)))
    return out
if __name__ == '__main__':
    os.makedirs('analysis/corpus', exist_ok=True)
    L = ted_letters(); txt = ' '.join(b for _, b in L)
    # drop Spanish-heavy passages crudely: sentences with many Spanish function words
    sents = re.split(r'(?<=[.!?])\s+', txt); es = re.compile(r'\b(que|los|las|del|por|para|una|pero|muy|est[aá])\b', re.I)
    txt = ' '.join(x for x in sents if len(es.findall(x)) < 2)
    extra = ['ted-kaczynski-letter-to-the-editor-of-the-saturday-review-on-privacy', 'ted-kaczynski-letter-to-the-editor-of-the-chicago-daily-news-on-population-control',
             'ted-kaczynski-letter-to-editor-on-the-population-problem', 'ted-kaczynski-letter-to-the-editor-on-scientific-development',
             'ted-kaczynski-s-letter-of-resignation-from-his-professorship-at-berkeley', 'ted-kaczynski-s-letter-to-congressman-pat-williams']
    txt += ' ' + ' '.join(clean(open(f'{SRC}/{e}.muse').read()) for e in extra)
    open('analysis/corpus/TED_letters.txt', 'w').write(txt)
    m = open(f'{SRC}/ted-kaczynski-industrial-society-and-its-future-washington-post-version.muse').read()
    open('analysis/corpus/MANIFESTO.txt', 'w').write(clean(m))
    for f in glob.glob(f'{SRC}/lineup/*.muse'):
        open('analysis/corpus/' + os.path.basename(f)[:-5] + '.txt', 'w').write(clean(open(f).read()))
    for f in sorted(glob.glob('analysis/corpus/*.txt')): print(os.path.basename(f), len(open(f).read().split()))
    print('ted letters', len(L))
