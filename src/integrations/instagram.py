"""Instagram Graph API content publishing (image + carousel). Requires public image URLs."""
import time, httpx
from src.config import env
G = "https://graph.facebook.com/v21.0"

def _tok(): return env("IG_LONG_LIVED_TOKEN")

def publish_image(ig_user_id: str, image_url: str, caption: str) -> dict:
    r = httpx.post(f"{G}/{ig_user_id}/media", data={"image_url": image_url, "caption": caption, "access_token": _tok()}, timeout=60); r.raise_for_status()
    cid = r.json()["id"]
    _wait(cid)
    r = httpx.post(f"{G}/{ig_user_id}/media_publish", data={"creation_id": cid, "access_token": _tok()}, timeout=60); r.raise_for_status()
    mid = r.json()["id"]
    r = httpx.get(f"{G}/{mid}", params={"fields": "permalink", "access_token": _tok()}, timeout=60)
    return {"media_id": mid, "permalink": r.json().get("permalink")}

def _wait(cid, tries=20):
    for _ in range(tries):
        r = httpx.get(f"{G}/{cid}", params={"fields": "status_code", "access_token": _tok()}, timeout=60)
        if r.json().get("status_code") == "FINISHED": return
        time.sleep(3)
    raise RuntimeError("container not ready")

def me(ig_user_id: str) -> dict:
    return httpx.get(f"{G}/{ig_user_id}", params={"fields": "username,followers_count", "access_token": _tok()}, timeout=60).json()

def insights(media_id: str) -> dict:
    r = httpx.get(f"{G}/{media_id}/insights", params={"metric": "reach,saved,shares,likes,comments", "access_token": _tok()}, timeout=60)
    return {d["name"]: d["values"][0]["value"] for d in r.json().get("data", [])}
