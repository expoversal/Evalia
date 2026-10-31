#!/usr/bin/env bash
# ops/weekly/02-anchor-reconcile.sh
# Compare last 7 days of internal manifests against the anchor.

for manifest in $(find /mnt/worm/audit -name MANIFEST.json -mtime -7); do
  manifest_sha=$(sha256sum "$manifest" | cut -d' ' -f1)

  # verify RFC 3161
  openssl ts -verify -data "$manifest" -in "${manifest%.json}.tsr" \
    -CAfile /etc/ssl/tsa-chain.pem -untrusted /etc/ssl/tsa-intermediate.pem \
    || { echo "RFC3161 FAIL: $manifest"; continue; }

  # verify rekor inclusion
  python tools/verify_rekor.py --manifest "$manifest" \
    --proof "${manifest%.json}.rekor.json" \
    || { echo "REKOR FAIL: $manifest"; continue; }

  echo "OK: $manifest_sha $(basename $(dirname $manifest))"
done
