from rapidfuzz import fuzz
import hashlib

def canonical_id(req) -> str:
    # normalise: lowercase, strip refs, collapse quantities to placeholders
    t = req.requirement_text.lower()
    t = re.sub(r"\d+(\.\d+)?", "#", t)
    t = re.sub(r"\b(clause|section|ref)\s*[\d\.]+", "", t)
    return hashlib.sha1(t.encode()).hexdigest()[:12]

def dedup(requirements, embed_fn, sim_threshold=0.92):
    clusters = {}
    for r in requirements:
        key = canonical_id(r)
        if key in clusters:
            clusters[key].append(r); continue
        # second pass: semantic near-dup
        matched = None
        for k, members in clusters.items():
            if r.category != members[0].category:      # never merge across categories
                continue
            if fuzz.token_set_ratio(r.requirement_text,
                                    members[0].requirement_text) > sim_threshold * 100:
                matched = k; break
        if matched:
            clusters[matched].append(r)
        else:
            clusters[key] = [r]

    merged = []
    for members in clusters.values():
        primary = members[0]
        primary.cross_refs = sorted({c for m in members for c in [m.clause_ref] + m.cross_refs})
        primary.source_quote = " || ".join(m.source_quote for m in members)
        merged.append(primary)
    return merged
