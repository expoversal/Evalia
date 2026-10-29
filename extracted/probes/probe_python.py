"""Audit probes for pure-Python DeepSeek fragments. Synthetic data only. See README.md."""
import re, json, hashlib, asyncio, traceback, types
from typing import Literal
from dataclasses import dataclass
from decimal import Decimal
from pydantic import BaseModel
from pathlib import Path
X = str(Path(__file__).resolve().parent.parent) + '/'
def load(fn, **extra):
    ns = dict(extra); exec(compile(open(X + fn).read(), fn, 'exec'), ns); return ns
def show(tag, fn):
    try: print(tag, '->', fn())
    except Exception as e: print(tag, '-> EXCEPTION', type(e).__name__ + ':', e)

# 006 + 008 verify_evidence
m = load('006-criterion-score-models.py')
v = load('008-verify-evidence.py', CriterionScore=m['CriterionScore'])
C = types.SimpleNamespace
def p008(chunks, quotes):
    s = m['CriterionScore'](criterion_id='C1', score=7, confidence='high', rationale='r',
        evidence=[m['Evidence'](quote=q, doc_id='bid.pdf', page=p) for q, p in quotes])
    r = v['verify_evidence'](s, chunks)
    return dict(kept=len(r.evidence), confidence=r.confidence, missing=r.missing_info)
show('P008a real quote, one chunk', lambda: p008([C(doc_id='bid.pdf', text='We completed three hospitals since 2021.')], [('three hospitals', 3)]))
show('P008b invented quote', lambda: p008([C(doc_id='bid.pdf', text='We completed three hospitals since 2021.')], [('five hospitals', 3)]))
show('P008c real quote from 1st of 2 chunks of same document', lambda: p008([C(doc_id='bid.pdf', text='We completed three hospitals since 2021.'), C(doc_id='bid.pdf', text='Our safety record is clean.')], [('three hospitals', 3)]))

# 009 aggregate
a = load('009-aggregate-with-gates.py', CriterionScore=m['CriterionScore'])
rub = C(gates=[], criteria=[C(id='C1', type='scored', weight=50), C(id='C3', type='scored', weight=50)])
sc = {'C1': m['CriterionScore'](criterion_id='C1', score=7, confidence='high', rationale='', evidence=[]),
      'C3': m['CriterionScore'](criterion_id='C3', score=None, confidence='low', rationale='insufficient evidence', evidence=[])}
show('P009a aggregate as written', lambda: a['aggregate'](sc, rub))
a['evaluate_gates'] = lambda gates, scores: {}
show('P009b with a stub evaluate_gates, one criterion unscored', lambda: a['aggregate'](sc, rub))

# 014 check_bq
b = load('014-check-bq.py', BaseModel=BaseModel)
R = b['BQRow']
rows = [R(item='1.1', description='Excavation', unit='m3', qty=100, rate=12.5, amount=1250),
        R(item='1.2', description='Concrete', unit='m3', qty=40, rate=180, amount=7400)]
show('P014 extension error (40 x 180 = 7200, stated 7400)', lambda: b['check_bq'](rows))
import inspect
show('P014 parameters of check_bq (no stated total, no tender BQ)', lambda: list(inspect.signature(b['check_bq']).parameters))

# 015 flag_abnormal_rates
f = load('015-flag-abnormal-rates.py')
show('P015a five bidders, one at 50% of median', lambda: f['flag_abnormal_rates']({'A':{'x':100},'B':{'x':105},'C':{'x':98},'D':{'x':110},'E':{'x':50}}))
show('P015b three bidders (typical small tender)', lambda: f['flag_abnormal_rates']({'A':{'x':100},'B':{'x':105},'E':{'x':50}}))

# 021 dedup: thresholds collapsed
d = load('021-dedup-requirements.py', re=re)
Rq = lambda t, ref: types.SimpleNamespace(requirement_text=t, category='financial', clause_ref=ref, cross_refs=[], source_quote=t)
reqs = [Rq('Average annual turnover not less than S$10 million over three financial years', 'ITT 5.1'),
        Rq('Average annual turnover not less than S$1 million over three financial years', 'ITT 5.2')]
show('P021a dedup as written (re not imported)', lambda: load('021-dedup-requirements.py')['dedup'](reqs, None))
show('P021b two different turnover thresholds', lambda: [(r.requirement_text, r.cross_refs) for r in d['dedup'](reqs, None)])

# 024 prompt B2 used with str.format, as 007 does with SCORING_PROMPT
for fn in ['019-prompt-1a-candidate-detection.txt','020-prompt-1b-structured-extraction.txt','023-prompt-b1-navigation.txt','024-prompt-b2-compliance-resolver.txt']:
    t = open(X+fn).read()
    keys = set(re.findall(r'\{([a-z_]+)\}', t))
    show(f'P{fn[:3]} str.format() with its own placeholders', lambda: (t.format(**{k:'x' for k in keys}), 'ok')[1])

# 046 + 048 require_read('dynamic') as used by 055 and 064
from fastapi import HTTPException
pol = load('046-auth-policy.py')
jwt_ns = load('047-auth-jwt.py', AuthError=Exception)
src = open(X+'048-auth-deps.py').read().replace('from app.auth.jwt import Claims, verify\n','').replace('from app.auth.policy import READ_POLICY, WRITE_POLICY, Role\n','').replace('from app.db import db\n','')
dn = {'Claims': jwt_ns['Claims'], 'verify': jwt_ns['verify'], 'READ_POLICY': pol['READ_POLICY'], 'WRITE_POLICY': pol['WRITE_POLICY'], 'Role': pol['Role'], 'db': None}
exec(src, dn)
async def try_role(role, scope):
    u = jwt_ns['Claims'](sub='u', email='e', role=role, envelope_scope=scope, exp=0)
    try:
        await dn['require_read']('dynamic')(user=u, tender_id='t'); return 'allowed'
    except HTTPException as e: return e.status_code
show('P055 require_read("dynamic") per role', lambda: {r.value: asyncio.run(try_role(r.value, 'technical')) for r in pol['Role']})
show('P047 JWT issue/verify round trip', lambda: jwt_ns['verify'](jwt_ns['issue'](jwt_ns['Claims'](sub='u', email='e', role='auditor', exp=4102444800), 's'), 's').role)

# 050 Merkle: odd-leaf duplication
mk = load('050-sealing-merkle.py')
L = [b'a', b'b', b'c']
show('P050a root([a,b,c]) == root([a,b,c,c])', lambda: mk['merkle_root'](L) == mk['merkle_root'](L + [b'c']))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
k = Ed25519PrivateKey.generate()
rows_ = [{'bidder': 'A', 'status': 'compliant'}, {'bidder': 'B', 'status': 'not_addressed'}]
sp = mk['sign_seal'](rows_, 't', 'technical', None, 'k1', k)
show('P050b seal verifies on original snapshot', lambda: mk['verify_seal'](sp, rows_, k.public_key()))
show('P050c seal verifies on altered snapshot', lambda: mk['verify_seal'](sp, [rows_[0], {'bidder':'B','status':'compliant'}], k.public_key()))

# 073 award formulas: ties and unreviewed scores
fm = load('073-award-formulas.py')
def pkg(i, price, hs=8):
    return {'bidder_id': i, 'bidder_name': i, 'gates_passed': True, 'evaluated_price': price,
            'compliance': [{'mandatory': True, 'status': 'compliant'}],
            'criterion_scores': [{'weight': 100, 'human_score': hs}]}
show('P073a QFM, identical bids: (bidder, final, rank)', lambda: [(r.bidder_id, str(r.final_score), r.rank) for r in fm['qfm']([pkg('A', 1000000), pkg('B', 1000000)], {'scale_max': 10})])
show('P073b LCP, identical prices: (bidder, rank)', lambda: [(r.bidder_id, r.rank) for r in fm['lcp']([pkg('A', 1000000), pkg('B', 1000000)], {})])
show('P073c unreviewed criterion (human_score None) -> technical_score', lambda: str(fm['_base_result'](pkg('A', 1, hs=None)).technical_score))

# 128 frost_ceremony import
show('P128 import tools/frost_ceremony.py', lambda: load('128-frost-ceremony.py') and 'imported')
# 091 FROST library
show('P091 import frost_ed25519', lambda: __import__('frost_ed25519'))
# 097 rekor verifier library
show('P097 import sigstore_rekor_verify', lambda: __import__('sigstore_rekor_verify'))
# 017 Docling API
