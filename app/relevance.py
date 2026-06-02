import json
import anthropic
from app.config import settings
from app.profile import USER_PROFILE

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = f"""You are a recruiter assistant evaluating job listings for a senior EPM/OneStream professional.

{USER_PROFILE}

For each job, respond with a JSON object: {{"score": <0-100>, "reason": "<1-2 sentence explanation>"}}
"""


def score_jobs(jobs: list[dict]) -> list[dict]:
    if not jobs:
        return []

    messages = []

    # Build one message per job
    for i, job in enumerate(jobs):
        job_text = (
            f"Job #{i+1}\n"
            f"Title: {job['title']}\n"
            f"Company: {job['company']}\n"
            f"Location: {job['location']}\n"
            f"Description: {job['description']}\n"
        )
        messages.append({"role": "user", "content": job_text})
        messages.append({"role": "assistant", "content": '{"score":'})

    # Use a single multi-turn conversation for batch scoring
    scored = []
    for i, job in enumerate(jobs):
        job_text = (
            f"Title: {job['title']}\n"
            f"Company: {job['company']}\n"
            f"Location: {job['location']}\n"
            f"Description: {job['description'][:2000]}\n"
            f"\nRespond with JSON only: {{\"score\": <0-100>, \"reason\": \"...\"}}"
        )
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=200,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": job_text}],
            )
            text = response.content[0].text.strip()
            # Extract JSON even if wrapped in ```
            if "```" in text:
                text = text.split("```")[1].replace("json", "").strip()
            data = json.loads(text)
            job["score"] = int(data.get("score", 0))
            job["score_reason"] = data.get("reason", "")
        except Exception as e:
            print(f"[relevance] Scoring error for '{job['title']}': {e}")
            job["score"] = 0
            job["score_reason"] = "Scoring failed"
        scored.append(job)

    return scored
