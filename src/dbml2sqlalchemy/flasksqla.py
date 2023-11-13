'''
Convert plain SQLAlchemy models into FlaskSQLAlchemy models
'''

import re

INPUT = 'out/models.txt'
OUTPUT = 'out/flask-models.txt'

replacements = [ 
    ('Base.metadata,', ''), 
    ('Base', 'db.Model'),
    ('default=func.now()', 'server_default=db.func.now()'),
    ('modified = Column(DateTime)', 'modified = db.Column(db.DateTime, onupdate=db.func.now())'),
]

for item in ['Table', 'Column', 'ForeignKey', 'Index', 'relationship', 'Integer', 'String', 'Date', 'Time', 'DateTime', 'Boolean', 'JSON', 'func']:
    replacements.append((item, f'db.{item}'))

def multireplace(string, replacements, ignore_case=False):
    '''https://gist.github.com/bgusach/a967e0587d6e01e889fd1d776c5f3729'''
    if not replacements:
        return string
    
    if ignore_case:
        def normalize(s):
            return s.lower()
        re_mode = re.IGNORECASE
    else:
        def normalize(s):
            return s
        re_mode = 0

    replacements = { normalize(key): val for key, val in replacements }
    
    # longest munch
    rep_sorted = sorted(replacements, key=len, reverse=True) 

    # escape special chars
    rep_escaped = map(re.escape, rep_sorted)
    
    # union of patterns
    pattern = re.compile("|".join(rep_escaped), re_mode)

    # re.sub() fn called for every non-overlapping match: takes match_obj, returns replacement
    
    # replace match with replacement, key is normalized old string, match.group(0) is occurence
    return pattern.sub(lambda match: replacements[normalize(match.group(0))], string)

with open(INPUT, 'r') as fd, open(OUTPUT, 'w') as fh:
    text = fd.read()
    fh.write(multireplace(text, replacements))
