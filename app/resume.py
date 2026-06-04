import os
import anthropic
from app.config import settings

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

ADAPT_SYSTEM = """You are an expert resume writer specializing in EPM/OneStream roles.
Your task is to adapt the candidate's master resume to a specific job posting.

Follow these steps in order:

STEP 1 — Standard adaptation:
- Rewrite the second line (title/tagline) to match the job title and key requirements
- Update the PROFILE section to emphasize skills mentioned in the JD
- Reorder or rephrase bullet points to highlight the most relevant experience first
- Add or emphasize keywords from the JD for ATS optimization
- Keep all facts accurate — do not invent experience or skills

STEP 2 — Achievement enhancement (only if Performance Review is provided):
- Review the candidate's Performance Review for achievement bullets
- For the most recent job position in the resume, identify bullets that are weaker or more generic
- Replace up to 3 of those weak bullets with stronger, more specific achievement bullets from the Performance Review
- Choose achievements most relevant to the target job description
- Preserve the original bullet formatting exactly

FORMATTING RULES (must be followed exactly):
- Keep the EXACT same Markdown structure as the input resume
- Name stays as **ALL CAPS BOLD** on line 1
- Title on line 2 as **bold**
- Contact info unchanged
- Section headers as **ALL CAPS BOLD**
- Company lines as **Company**   Location
- Dates on their own line
- Job roles as ***bold italic***
- Job descriptions as *italic*
- Bullets with leading "  - "
- Skill lines as **Label:**  text
- Output ONLY the adapted resume in Markdown, no commentary, no code fences
"""


def _load_master_resume() -> str:
    path = settings.resume_path
    if not os.path.exists(path):
        repo_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "resume.md"
        )
        if os.path.exists(repo_path):
            with open(repo_path, "r") as f:
                return f.read()
        return "# Resume not found\n\nPlease upload your resume to /data/resume.md"
    with open(path, "r") as f:
        return f.read()


def _load_perf_review() -> str:
    path = settings.perf_review_path
    if not os.path.exists(path):
        repo_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "perf_review.md"
        )
        if os.path.exists(repo_path):
            with open(repo_path, "r") as f:
                return f.read()
        return ""
    with open(path, "r") as f:
        return f.read()


def adapt_resume(job: dict) -> str:
    master = _load_master_resume()
    perf_review = _load_perf_review()

    job_context = (
        f"Job Title: {job.get('title', '')}\n"
        f"Company: {job.get('company', '')}\n"
        f"Location: {job.get('location', '')}\n\n"
        f"Job Description:\n{job.get('description', '')}"
    )

    perf_section = (
        f"\n\n---\n\nHere is the candidate's Performance Review "
        f"(use for achievement bullet selection):\n\n{perf_review}"
        if perf_review.strip()
        else ""
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": ADAPT_SYSTEM,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Here is the job posting:\n\n{job_context}\n\n"
                    f"---\n\nHere is the master resume:\n\n{master}"
                    f"{perf_section}\n\n"
                    f"Please adapt the resume for this position."
                ),
            }
        ],
    )
    return response.content[0].text
