async def score_criterion(criterion, bid, retriever, llm):
    chunks = retriever.search(
        query=f"{criterion.name}: {criterion.guidance}",
        doc_ids=bid.doc_ids,
        k=12,
    )
    prompt = SCORING_PROMPT.format(
        criterion=criterion.model_dump_json(),
        evidence=render_chunks(chunks),  # includes doc_id + page per chunk
    )
    result = await llm.structured(
        model="gpt-4o",              # or any LiteLLM-supported model
        messages=[{"role": "user", "content": prompt}],
        schema=CriterionScore,
    )
    return verify_evidence(result, chunks)   # critical — see below
