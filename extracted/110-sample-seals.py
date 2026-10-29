def sample_seals(month: str, n: int = 5) -> list[str]:
    seed = int(hashlib.sha256(f"{month}-seal-sample".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    sealed = [s["id"] for s in query(
        f"SELECT id FROM technical.seals WHERE signed_at LIKE '{month}%' "
        f"AND revoked_at IS NULL")]
    return rng.sample(sealed, min(n, len(sealed)))
