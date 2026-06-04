import httpx
import os
import sys

token = os.environ["RUN_TOKEN"]
url = os.environ.get("APP_URL", "https://hr-partner.onrender.com")

print(f"Triggering pipeline at {url}/run ...")
try:
    r = httpx.post(
        f"{url}/run",
        headers={"Authorization": f"Bearer {token}"},
        timeout=300,
    )
    print(f"Status: {r.status_code}")
    print(r.text)
    sys.exit(0 if r.status_code == 200 else 1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
