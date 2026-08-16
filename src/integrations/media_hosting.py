"""Instagram needs a public URL. We commit rendered files to the repo; GitHub Pages serves them."""
import subprocess
from pathlib import Path
from src.config import ROOT, env

def publish_files(paths: list[Path]) -> list[str]:
    base = env("PAGES_BASE_URL", "").rstrip("/")
    if not base: raise RuntimeError("PAGES_BASE_URL not set")
    subprocess.run(["git", "add"] + [str(p) for p in paths], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", f"media: {', '.join(p.name for p in paths)}", "--allow-empty"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    return [base + "/media/" + str(p.relative_to(ROOT / "public" / "media")) for p in paths]
