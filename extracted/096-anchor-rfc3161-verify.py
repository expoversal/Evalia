def verify_timestamp(manifest_bytes: bytes, tsr: dict) -> dict:
    from rfc3161ng import RemoteTimestamper
    from asn1crypto import tsp, cms
    token = tsp.TimeStampResp.load(base64.b64decode(tsr["token_der"]))
    status = token["status"]["status"].native
    if status != "granted":
        return {"ok": False, "reason": f"status={status}"}
    tst_info = token["time_stamp_token"]["content"]["encap_content_info"]["content"]
    # verify the message hash matches
    if tst_info["message_imprint"]["hashed_message"].native != \
       hashlib.sha256(manifest_bytes).digest():
        return {"ok": False, "reason": "hash mismatch"}
    gen_time = tst_info["gen_time"].native  # the timestamp
    return {"ok": True, "timestamp": gen_time.isoformat(),
            "tsa": tst_info.get("tsa", "unknown")}
