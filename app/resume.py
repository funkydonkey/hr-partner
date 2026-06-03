import os
import anthropic
from app.config import settings

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

ADAPT_SYSTEM = """You are an expert resume writer specializing in EPM/OneStream roles.
Your task is to adapt the candidate's master resume to a specific job posting.

Rules:
- Keep all facts accurate — do not invent experience or skills
- Rewrite the second line (title/tagline) to match the job title and key requirements
- Update the PROFILE section to emphasize skills mentioned in the JD
- Reorder or rephrase bullet points to highlight the most relevant experience first
- Add or emphasize keywords from the JD for ATS optimization
- Keep the EXACT same Markdown structure and formatting as the input resume:
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
        # Fall back to repo copy during development
        repo_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "resume.md"
        )
        if os.path.exists(repo_path):
            with open(repo_path, "r") as f:
                return f.read()
        return "# Resume not found\n\nPlease upload your resume to /data/resume.md"
    with open(path, "r") as f:
        return f.read()


def adapt_resume(job: dict) -> str:
    master = _load_master_resume()
    job_context = (
        f"Job Title: {job.get('title', '')}\n"
        f"Company: {job.get('company', '')}\n"
        f"Location: {job.get('location', '')}\n\n"
        f"Job Description:\n{job.get('description', '')}"
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=ADAPT_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Here is the job posting:\n\n{job_context}\n\n"
                    f"---\n\nHere is the master resume:\n\n{master}\n\n"
                    f"Please adapt the resume for this position."
                ),
            }
        ],
    )
    return response.content[0].text
