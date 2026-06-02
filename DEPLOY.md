# Deployment Guide — HR Partner Agent

## Prerequisites

Obtain the following API keys before starting:

| Service | Purpose | Free tier |
|---------|---------|-----------|
| [SerpAPI](https://serpapi.com) | Job search via Google Jobs | 100 searches/month |
| [Anthropic](https://console.anthropic.com) | Claude AI scoring + resume adaptation | Pay-per-use |
| [SendGrid](https://sendgrid.com) | Email digest | 100 emails/day |

---

## Step 1 — Create a Render Web Service

1. Go to [render.com](https://render.com) → **New** → **Web Service**
2. Connect your GitHub account and select the `funkydonkey/hr-partner` repository
3. Set the following:

| Field | Value |
|-------|-------|
| **Branch** | `claude/job-listing-monitor-agent-Ca5Ch` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

4. Click **Advanced** → **Add Disk**:

| Field | Value |
|-------|-------|
| **Name** | `data` |
| **Mount Path** | `/data` |
| **Size** | 1 GB |

---

## Step 2 — Set Environment Variables

In the Render service settings → **Environment**, add:

```
SERPAPI_KEY         = <your SerpAPI key>
ANTHROPIC_API_KEY   = <your Anthropic key>
SENDGRID_API_KEY    = <your SendGrid key>
EMAIL_TO            = a.molchansky@gmail.com
EMAIL_FROM          = noreply@yourdomain.com
RUN_TOKEN           = <random secret, e.g. openssl rand -hex 16>
DATABASE_PATH       = /data/jobs.db
RESUME_PATH         = /data/resume.md
MIN_SCORE           = 60
```

> **RUN_TOKEN** is used to protect the manual trigger endpoint. Generate a random string:
> ```bash
> openssl rand -hex 16
> ```

---

## Step 3 — Deploy

Click **Create Web Service**. Render will:
1. Clone the repo
2. Run `pip install -r requirements.txt`
3. Start the app with uvicorn
4. Mount the `/data` disk

Wait for the build to complete (~2 min). The service URL will look like:
`https://hr-partner-xxxx.onrender.com`

---

## Step 4 — Upload Your Resume

1. Open `https://your-service.onrender.com/resume/edit`
2. Replace the placeholder text with your actual resume in Markdown format
3. Click **Save Resume**

The resume is saved to `/data/resume.md` on the persistent disk.

---

## Step 5 — Configure SendGrid Sender

SendGrid requires a verified sender address:

1. Go to [SendGrid → Settings → Sender Authentication](https://app.sendgrid.com/settings/sender_auth)
2. Verify the email you set as `EMAIL_FROM`
3. (Optional) Verify your domain for better deliverability

---

## Step 6 — Test the Pipeline

Trigger a manual run from a terminal:

```bash
curl -X POST https://your-service.onrender.com/run \
  -H "Authorization: Bearer YOUR_RUN_TOKEN"
```

Expected response:
```json
{"status": "ok", "new_jobs": 12, "sent": 5}
```

Or use the **Run Now** button in the dashboard (it will prompt for the token).

---

## Step 7 — Verify the Schedule

The agent runs automatically at **08:00 CET** every day.

To verify the scheduler is active, check Render logs:
- Go to your service → **Logs**
- After 08:00 CET you should see: `[pipeline] Starting job search pipeline`

---

## Web Interface

| URL | Description |
|-----|-------------|
| `/` | Dashboard — all found jobs with scores |
| `/queries` | Edit search queries (add/remove/toggle) |
| `/resume/edit` | Edit master resume |
| `/jobs/{id}/prepare-resume` | Generate tailored resume for a job |
| `/jobs/{id}/resume` | View adapted resume |
| `/health` | Health check endpoint |

---

## Troubleshooting

**No email received:**
- Check SendGrid sender verification
- Check `EMAIL_FROM` matches the verified sender
- Look at Render logs for `[emailer]` entries

**SerpAPI quota exceeded:**
- 100 free searches = ~25 runs with 4 queries each
- Upgrade to paid plan or reduce the number of active queries at `/queries`

**Jobs not saving between restarts:**
- Confirm the disk is mounted at `/data` in Render settings
- `DATABASE_PATH` must be `/data/jobs.db`

**Claude API errors:**
- Check your Anthropic account has credits
- Logs will show `[relevance] Scoring error` with details

---

## Cost Estimate (monthly)

| Service | Usage | Cost |
|---------|-------|------|
| Render Web Service | Hobby plan | $7/month |
| Render Disk (1 GB) | — | $0.25/month |
| SerpAPI | 30 runs × 4 queries | Free (100 limit) |
| Anthropic Claude | ~30 runs × ~20 jobs × 500 tokens | ~$1–2/month |
| SendGrid | ~30 emails | Free |
| **Total** | | **~$8–9/month** |
