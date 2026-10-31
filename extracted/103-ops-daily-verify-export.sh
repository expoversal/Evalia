#!/usr/bin/env bash
# ops/daily/01-verify-export.sh
set -euo pipefail

YESTERDAY=$(date -u -d "yesterday" +%Y-%m-%d)
BUCKET="s3://audit-worm-prod"

# Check the export exists for every active tender
for tender in $(psql -tAc "SELECT id FROM core.tenders WHERE state IN ('tech_sealed','commercial_sealed','awarded')"); do
  PREFIX="audit/${tender}/${YESTERDAY}"
  if ! aws s3 ls "${BUCKET}/${PREFIX}/" | grep -q MANIFEST.json; then
    echo "MISSING: ${PREFIX}" >&2
    # page the on-call
    curl -X POST "$OPS_ALERT_WEBHOOK" -d "{\"severity\":\"high\",\"msg\":\"WORM export missing for tender $tender on $YESTERDAY\"}"
    exit 1
  fi
done
echo "OK: all active tenders have $YESTERDAY export"
