"""Files are the database. Everything under brands/<id>/queue/."""
import json, datetime as dt
from pathlib import Path

def qdir(brand): p = Path(brand["_dir"]) / "queue"; p.mkdir(exist_ok=True); return p

def save_variants(brand, slot_id, variants: list[dict], guardian: list[dict]):
    (qdir(brand) / f"{slot_id}.variants.json").write_text(json.dumps({"slot_id": slot_id, "variants": variants, "guardian": guardian, "created": dt.datetime.utcnow().isoformat()}, indent=2, ensure_ascii=False))

def load_variants(brand, slot_id):
    p = qdir(brand) / f"{slot_id}.variants.json"
    return json.loads(p.read_text()) if p.exists() else None

def approve(brand, slot_id, producer_id, approver_id, png_path: str):
    v = load_variants(brand, slot_id)
    chosen = next(x for x in v["variants"] if x["producer_id"] == producer_id)
    rec = {"slot_id": slot_id, "producer_id": producer_id, "approver": str(approver_id), "approved_at": dt.datetime.utcnow().isoformat(),
           "content_hash": chosen["content_hash"], "caption": chosen["caption"]["full_text"], "png": png_path,
           "publish_at_local": chosen.get("publish_at_local"), "template_id": chosen["render"]["template_id"],
           "rejected_in_favour": [x["producer_id"] for x in v["variants"] if x["producer_id"] != producer_id], "status": "approved"}
    (qdir(brand) / f"{slot_id}.approved.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False))
    return rec

def reject(brand, slot_id, approver_id, reason=""):
    (qdir(brand) / f"{slot_id}.rejected.json").write_text(json.dumps({"slot_id": slot_id, "approver": str(approver_id), "reason": reason, "at": dt.datetime.utcnow().isoformat()}))

def pending_publish(brand):
    out = []
    for p in qdir(brand).glob("*.approved.json"):
        r = json.loads(p.read_text())
        if r.get("status") == "approved": out.append((p, r))
    return out

def log_publish(brand, rec: dict):
    with open(Path(brand["_dir"]) / "publish_log.jsonl", "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def load_plan(brand, week_start: str):
    p = qdir(brand) / f"plan-{week_start}.json"
    return json.loads(p.read_text()) if p.exists() else None
