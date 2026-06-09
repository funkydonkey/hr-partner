import hashlib
import serpapi
from app.config import settings


def _make_job_id(title: str, company: str, url: str) -> str:
    raw = f"{title}|{company}|{url}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


_LOCATION_GL = {
    "united kingdom": "gb", "uk": "gb", "england": "gb",
    "germany": "de", "deutschland": "de",
    "netherlands": "nl", "holland": "nl",
    "france": "fr",
    "belgium": "be",
    "switzerland": "ch",
    "austria": "at",
    "sweden": "se",
    "denmark": "dk",
    "norway": "no",
    "poland": "pl",
    "spain": "es",
    "italy": "it",
    "ireland": "ie",
    "portugal": "pt",
    "czech republic": "cz",
    "europe": "gb",  # use google.co.uk as EU proxy
}


def search_jobs(query: str, location: str = "") -> list[dict]:
    client = serpapi.Client(api_key=settings.serpapi_key)
    params = {"engine": "google_jobs", "q": query, "hl": "en"}
    if location:
        params["location"] = location
        gl = _LOCATION_GL.get(location.lower())
        if gl:
            params["gl"] = gl
    results = client.search(**params)
    jobs_results = results.get("jobs_results", [])

    jobs = []
    for item in jobs_results:
        title = item.get("title", "")
        company = item.get("company_name", "")
        location = item.get("location", "")
        description = item.get("description", "")

        url = ""
        apply_options = item.get("apply_options", [])
        if apply_options:
            url = apply_options[0].get("link", "")
        if not url:
            url = item.get("share_link", "")

        source = "other"
        url_lower = url.lower()
        if "linkedin.com" in url_lower:
            source = "LinkedIn"
        elif "indeed.com" in url_lower:
            source = "Indeed"
        elif "glassdoor.com" in url_lower:
            source = "Glassdoor"
        elif "google.com/search" in url_lower:
            source = "Google Jobs"

        jobs.append({
            "job_id": _make_job_id(title, company, url),
            "title": title,
            "company": company,
            "location": location,
            "description": description[:3000],
            "url": url,
            "source": source,
            "query": f"{query} [{params.get('location', 'global')}]" if location else query,
        })

    return jobs


def search_all_queries(queries: list[dict]) -> list[dict]:
    all_jobs: list[dict] = []
    seen_ids: set[str] = set()

    for q in queries:
        query = q["query"]
        location = q.get("location", "")
        try:
            jobs = search_jobs(query, location)
            for job in jobs:
                if job["job_id"] not in seen_ids:
                    seen_ids.add(job["job_id"])
                    all_jobs.append(job)
        except Exception as e:
            loc_info = f" [{location}]" if location else ""
            print(f"[search] Error for query '{query}'{loc_info}: {e}")

    return all_jobs
