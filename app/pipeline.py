import asyncio
from app import search, relevance, storage, emailer
from app.config import settings


async def run_pipeline() -> dict:
    print("[pipeline] Starting job search pipeline")

    # Step 1: Get active search queries from DB
    queries = await storage.get_active_queries()
    if not queries:
        print("[pipeline] No active queries found")
        return {"status": "no_queries", "new_jobs": 0, "sent": 0}

    print(f"[pipeline] Searching with {len(queries)} queries: {queries}")

    # Step 2: Fetch jobs from SerpAPI (sync, run in thread pool)
    loop = asyncio.get_event_loop()
    raw_jobs = await loop.run_in_executor(None, search.search_all_queries, queries)
    print(f"[pipeline] Found {len(raw_jobs)} total jobs from SerpAPI")

    # Step 3: Deduplicate against seen jobs
    seen_ids = await storage.get_seen_job_ids()
    new_jobs = [j for j in raw_jobs if j["job_id"] not in seen_ids]
    print(f"[pipeline] {len(new_jobs)} new jobs after dedup")

    if not new_jobs:
        print("[pipeline] No new jobs to process")
        return {"status": "ok", "new_jobs": 0, "sent": 0}

    # Step 4: Score with Claude
    scored_jobs = await loop.run_in_executor(None, relevance.score_jobs, new_jobs)

    # Step 5: Filter by min score
    relevant_jobs = [j for j in scored_jobs if j["score"] >= settings.min_score]
    print(f"[pipeline] {len(relevant_jobs)} jobs above score threshold {settings.min_score}")

    # Step 6: Save all scored jobs (even below threshold) to DB
    await storage.save_jobs(scored_jobs)

    # Step 7: Send email digest with relevant jobs only
    sent = 0
    if relevant_jobs:
        sorted_jobs = sorted(relevant_jobs, key=lambda x: x["score"], reverse=True)
        await loop.run_in_executor(None, emailer.send_digest, sorted_jobs)
        sent = len(sorted_jobs)

    print(f"[pipeline] Done. Saved {len(scored_jobs)} jobs, sent digest with {sent}")
    return {"status": "ok", "new_jobs": len(scored_jobs), "sent": sent}
