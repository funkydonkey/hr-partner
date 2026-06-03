import asyncio
import os
import re
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, HTTPException, Header
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from typing import Optional, Annotated

from app import storage, pipeline, resume as resume_module
from app.docx_builder import build_docx
from app.scheduler import create_scheduler
from app.config import settings

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

scheduler = create_scheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await storage.init_db()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="HR Partner", lifespan=lifespan)


# --- Health ---

@app.get("/health")
async def health():
    return {"status": "ok"}


# --- Manual trigger (token-protected) ---

@app.post("/run")
async def run_now(authorization: Annotated[Optional[str], Header()] = None):
    token = (authorization or "").replace("Bearer ", "").strip()
    if token != settings.run_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await pipeline.run_pipeline()
    return result


# --- Dashboard ---

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    jobs = await storage.get_recent_jobs(limit=50)
    return templates.TemplateResponse("index.html", {"request": request, "jobs": jobs})


# --- Search Queries CRUD ---

@app.get("/queries", response_class=HTMLResponse)
async def queries_page(request: Request, saved: Optional[str] = None):
    queries = await storage.get_queries()
    return templates.TemplateResponse(
        "queries.html", {"request": request, "queries": queries, "saved": saved}
    )


@app.post("/queries/add")
async def add_query(query: Annotated[str, Form()]):
    query = query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    await storage.add_query(query)
    return RedirectResponse("/queries?saved=1", status_code=303)


@app.post("/queries/{query_id}/update")
async def update_query(
    query_id: int,
    query: Annotated[str, Form()],
    active: Annotated[Optional[str], Form()] = None,
):
    await storage.update_query(query_id, query.strip(), active == "on")
    return RedirectResponse("/queries?saved=1", status_code=303)


@app.post("/queries/{query_id}/delete")
async def delete_query(query_id: int):
    await storage.delete_query(query_id)
    return RedirectResponse("/queries", status_code=303)


# --- Resume Adaptation ---

@app.post("/jobs/{job_id}/prepare-resume")
async def prepare_resume(job_id: str):
    job = await storage.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check if already generated
    existing = await storage.get_adapted_resume(job_id)
    if existing:
        return RedirectResponse(f"/jobs/{job_id}/resume", status_code=303)

    # Run adaptation in background thread (blocking Claude call)
    loop = asyncio.get_event_loop()
    adapted = await loop.run_in_executor(None, resume_module.adapt_resume, job)
    await storage.save_adapted_resume(job_id, adapted)
    return RedirectResponse(f"/jobs/{job_id}/resume", status_code=303)


@app.get("/jobs/{job_id}/resume", response_class=HTMLResponse)
async def view_resume(request: Request, job_id: str):
    job = await storage.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    adapted = await storage.get_adapted_resume(job_id)
    return templates.TemplateResponse(
        "resume.html", {"request": request, "job": job, "resume_md": adapted}
    )


@app.get("/jobs/{job_id}/resume/download")
async def download_resume_docx(job_id: str):
    job = await storage.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    adapted = await storage.get_adapted_resume(job_id)
    if not adapted:
        raise HTTPException(status_code=404, detail="Resume not generated yet")

    loop = asyncio.get_event_loop()
    docx_bytes = await loop.run_in_executor(None, build_docx, adapted)

    company_slug = re.sub(r'[^a-z0-9]+', '_', job.get('company', 'company').lower()).strip('_')
    filename = f"resume_{company_slug}.docx"

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- Resume file management ---

@app.get("/resume/edit", response_class=HTMLResponse)
async def edit_resume_page(request: Request):
    path = settings.resume_path
    if not os.path.exists(path):
        repo_path = os.path.join(BASE_DIR, "data", "resume.md")
        content = open(repo_path).read() if os.path.exists(repo_path) else ""
    else:
        content = open(path).read()
    return templates.TemplateResponse(
        "resume_edit.html", {"request": request, "content": content}
    )


@app.post("/resume/edit")
async def save_resume(content: Annotated[str, Form()]):
    os.makedirs(os.path.dirname(settings.resume_path), exist_ok=True)
    with open(settings.resume_path, "w") as f:
        f.write(content)
    return RedirectResponse("/resume/edit?saved=1", status_code=303)
