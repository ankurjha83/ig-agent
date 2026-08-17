"""Instagram needs a public URL. We commit rendered files to the repo; GitHub Pages serves them."""
import subprocess, time
import httpx
from pathlib import Path
from src.config import ROOT, env

def publish_files(paths: list[Path]) -> list[str]:
    base = env("PAGES_BASE_URL", "").rstrip("/")
    if not base: raise RuntimeError("PAGES_BASE_URL not set")
    subprocess.run(["git", "add"] + [str(p) for p in paths], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", f"media: {', '.join(p.name for p in paths)}", "--allow-empty"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    urls = [base + "/" + str(p.relative_to(ROOT)) for p in paths]
    _wait_for_pages(urls)
    return urls

def _wait_for_pages(urls: list[str], tries: int = 20, interval: int = 15):
    """Poll until all URLs return 200 — GitHub Pages can take up to 3 min to deploy."""
    for url in urls:
        for i in range(tries):
            try:
                r = httpx.head(url, timeout=10, follow_redirects=True)
                if r.status_code == 200:
                    break
            except Exception:
                pass
            if i < tries - 1:
                time.sleep(interval)
        else:
            raise RuntimeError(f"GitHub Pages did not serve {url} after {tries * interval}s — deploy may still be in progress")
