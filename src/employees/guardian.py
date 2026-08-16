"""Deterministic checks first; optional LLM voice score."""
import re

def check(brand: dict, out: dict) -> dict:
    checks, verdict = [], "PASS"
    cap = out.get("caption", {})
    text = " ".join([cap.get("hook", ""), cap.get("body", ""), cap.get("cta", "")] + [o.get("text", "") for o in out.get("reel", {}).get("overlays", [])])
    # 1 claims
    banned = brand["compliance"]["banned_claim_patterns"]
    hits = [p for p in banned if re.search(p, text, re.I)]
    if hits:
        verdict = "BLOCKED"; checks.append({"name": "claims", "status": "blocked", "detail": f"banned pattern(s): {hits}"})
    else:
        checks.append({"name": "claims", "status": "pass", "detail": ""})
    # 2 packaging realism
    for a in out.get("assets", []):
        if a.get("kind") in ("image", "video") and a.get("source") == "generated" and re.search(r"pouch|jar|pack|box|label", a.get("prompt", ""), re.I):
            verdict = "BLOCKED"; checks.append({"name": "packaging", "status": "blocked", "detail": "generated packaging imagery"})
    # 3 template listed
    tids = {t["id"] for t in brand["visual"]["templates"]["list"]}
    tid = out.get("render", {}).get("template_id")
    if tid not in tids:
        verdict = "BLOCKED"; checks.append({"name": "template", "status": "blocked", "detail": f"unknown template {tid}"})
    else:
        checks.append({"name": "template", "status": "pass", "detail": tid})
    # 6 limits (fix)
    fixed = False
    if len(cap.get("hook", "")) > 125:
        cap["hook"] = cap["hook"][:122].rstrip() + "…"; fixed = True
    mx = brand["content"]["hashtags"]["max_per_post"]
    if len(cap.get("hashtags", [])) > mx:
        cap["hashtags"] = cap["hashtags"][:mx]; fixed = True
    if len(cap.get("full_text", "")) > 2200:
        cap["full_text"] = cap["full_text"][:2190]; fixed = True
    if not cap.get("alt_text"):
        cap["alt_text"] = cap.get("hook", "")[:100]; fixed = True
    if fixed and verdict == "PASS":
        verdict = "FIXED"
    checks.append({"name": "limits", "status": "fixed" if fixed else "pass", "detail": ""})
    # 7 needs_data
    if out.get("needs_data"):
        verdict = "BLOCKED"; checks.append({"name": "data", "status": "blocked", "detail": str(out["needs_data"])})
    return {"slot_id": out.get("slot_id"), "producer_id": out.get("producer_id"), "verdict": verdict, "checks": checks,
            "reason_for_humans": "; ".join(c["detail"] for c in checks if c["status"] == "blocked") or "ok"}
