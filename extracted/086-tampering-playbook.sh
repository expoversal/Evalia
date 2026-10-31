# 1. Verify the WORM bundle (independent of live DB)
python tools/verify_audit.py --bundle /mnt/worm/audit/<tender>/ --pubkey seal.pub.pem
#  -> PASS = the exported history is intact

# 2. Verify the live DB chain
psql -c "SELECT audit.verify_chain('<tender-id>')"
#  -> if this returns ok=true AND the last_entry_hash matches the
#     live DB's head, the live DB is consistent with itself

# 3. Compare head-to-head
python tools/compare_chain_heads.py \
  --bundle /mnt/worm/audit/<tender>/ \
  --live-dsn $DATABASE_URL \
  --tender <tender-id>
#  -> identifies the first divergent entry between the live DB and the
#     last verified checkpoint
