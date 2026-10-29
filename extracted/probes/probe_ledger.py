"""Run fragments 053 (append_audit) and 054 (verify_chain) against PostgreSQL 16."""
import asyncio, hashlib, json, uuid, sys
import asyncpg
import os
from pathlib import Path
X = str(Path(__file__).resolve().parent.parent) + '/'
T = str(uuid.uuid4())

class DB:
    def __init__(self, pool): self.pool = pool
    async def fetch(self, q, *a):
        async with self.pool.acquire() as c: return await c.fetch(q, *a)

async def main():
    pool = await asyncpg.create_pool(os.environ['PROBE_DSN'])
    ns = {}
    exec(open(X + '053-audit-ledger.py').read(), ns)
    ns2 = {'GENESIS': ns['GENESIS'], 'db': DB(pool), 'hashlib': hashlib, 'json': json}
    exec(open(X + '054-audit-verify.py').read(), ns2)
    append_audit, verify_chain = ns['append_audit'], ns2['verify_chain']

    # L1: entries without before/after payloads, sequential transactions
    t1 = str(uuid.uuid4())
    for _ in range(3):
        async with pool.acquire() as c:
            async with c.transaction():
                await append_audit(c, t1, 'technical', None, 'view', None, None, None, None)
    print('L1 sequential, no payload        ->', await verify_chain(t1))

    # L2: one override entry carrying before/after JSON, as override_row() writes it
    t2 = str(uuid.uuid4())
    async with pool.acquire() as c:
        async with c.transaction():
            await append_audit(c, t2, 'technical', None, 'override', 'technical.compliance_rows',
                               str(uuid.uuid4()), {'human_status': None}, {'human_status': 'compliant'})
    print('L2 one override with payload     ->', await verify_chain(t2))

    # L3: two overlapping transactions (A starts first, B commits first)
    t3 = str(uuid.uuid4())
    a = await pool.acquire(); b = await pool.acquire()
    ta = a.transaction(); await ta.start(); await a.fetchval('select now()')   # fixes A's now()
    await asyncio.sleep(0.05)
    async with b.transaction():
        await append_audit(b, t3, 'technical', None, 'view', None, None, None, None)
    await append_audit(a, t3, 'technical', None, 'view', None, None, None, None)
    await ta.commit(); await pool.release(a); await pool.release(b)
    print('L3 overlapping transactions      ->', await verify_chain(t3))

    # L4: rewrite the timestamp of the middle entry of L1 (keeping order) as a superuser
    async with pool.acquire() as c:
        rows = await c.fetch('select id, ts from audit.ledger where tender_id=$1 order by ts, id', t1)
        await c.execute('alter table audit.ledger disable trigger audit_no_update')
        await c.execute("update audit.ledger set ts = ts - interval '1 microsecond' where id=$1", rows[1]['id'])
        await c.execute('alter table audit.ledger enable trigger audit_no_update')
    print('L4 timestamp altered after write ->', await verify_chain(t1))
    await pool.close()
asyncio.run(main())
