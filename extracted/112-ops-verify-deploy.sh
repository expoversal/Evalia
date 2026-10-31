#!/usr/bin/env bash
# ops/change/verify-deploy.sh
set -euo pipefail

echo "== 1. Chain verify all active tenders =="
psql -c "SELECT id, audit.verify_chain(id) FROM core.tenders WHERE state NOT IN ('draft');" \
  | tee /tmp/deploy-verify.txt
grep -q '"ok": false' /tmp/deploy-verify.txt && {
  echo "FAIL: chain broken after deploy"
  exit 1
}

echo "== 2. Last WORM export still matches =="
LATEST=$(aws s3 ls s3://audit-worm-prod/audit/ | tail -1 | awk '{print $2}')
python tools/verify_audit.py --bundle "/mnt/worm/${LATEST}" \
  --pubkey /etc/keys/seal-pub.pem \
  || { echo "FAIL: WORM bundle verification failed"; exit 1; }

echo "== 3. Anchors still verify =="
python tools/verify_anchors.py --bundle "/mnt/worm/${LATEST}" \
  || { echo "FAIL: anchor verification failed"; exit 1; }

echo "== 4. Smoke-test critical paths =="
curl -sf https://api/health/sealing-status  || { echo "FAIL: sealing endpoint"; exit 1; }
curl -sf https://api/health/award-status     || { echo "FAIL: award endpoint"; exit 1; }
curl -sf https://api/health/rbac-test        || { echo "FAIL: RBAC test"; exit 1; }

echo "== 5. First-hour audit review =="
sleep 3600
psql -c "SELECT action, actor, count(*) FROM audit.ledger WHERE ts > now() - interval '1 hour' GROUP BY 1,2;"
# human eye reviews output for unexpected actions

echo "OK: deploy verified"
