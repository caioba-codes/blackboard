"""Banner relevance: does a candidate photo's title/description/tags name the query's subject?

Whole words only ("formula" never matches "formulary"), simple plural folding, and generic
photo words (page, sheet, macro, notebook...) do not count unless they are all the query has.
"""
import re

STOP = set('a an the of on in with and or for to at by from into over under its their is are as this that'.split())
GENERIC = set('''page pages sheet sheets formula formulas formulae paper papers graph graphs close closeup up macro
view views photo photos photograph image images picture pictures desk dark board boards notes note notebook
notebooks detail background shot top'''.split())
BOARD = re.compile(r'\b(chalk|chalkboards?|blackboards?|slates?|classrooms?|whiteboards?)\b', re.I)

def stem(w):
    if len(w) > 4 and w.endswith('ies'): return w[:-3] + 'y'
    if len(w) > 4 and re.search(r'(ss|ch|sh|x|z)es$', w): return w[:-2]
    if len(w) > 3 and w.endswith('s') and not w.endswith('ss'): return w[:-1]
    return w

def words(text, keep=lambda w: True):
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text or '')  # split CamelCase file names
    return [stem(w) for w in re.findall(r'[^\W_]+', text.lower()) if keep(w)]

def terms(subject):
    """Subject terms of a query, in order; generic words only when nothing else is left."""
    seen = []
    for w in words(subject, lambda w: w not in STOP and len(w) > 1):
        if w not in seen: seen.append(w)
    specific = [w for w in seen if w not in GENERIC]
    return specific or seen

def needed(subject_terms):
    return 1 if len(subject_terms) <= 1 else 2

def hits(subject, text):
    have = set(words(text))
    return [w for w in terms(subject) if w in have]

def score(subject, *texts):
    """Matched subject terms (list) or None when the candidate is off-topic or a board photo."""
    hay = ' '.join(t or '' for t in texts)
    if BOARD.search(hay) and not BOARD.search(subject): return None
    hit = hits(subject, hay)
    return hit if len(hit) >= needed(terms(subject)) else None

def rank_key(subject, title, hit):
    """Sort key: terms named in the title first (long museum descriptions match anything), then total."""
    return (-len(hits(subject, title)), -len(hit))
