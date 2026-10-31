#!/usr/bin/env bash
# ops/daily/02-verify-chain.sh
set -euo pipefail

LOG=ops/logs/chain-verify-$(date -u +%Y-%m-%d).log
psql -c "SELECT audit.verify_chain(id) FROM core.tenders WHERE state IN ('tech_sealed','commercial_sealed','awarded');" \
  | tee "$LOG"

# fail if any tender returned ok=false
if grep -q "ok.*false" "$LOG"; then
  echo "CHAIN INTEGRITY FAILURE — escalating to §09.1" >&2
  exit 1
fi
