"""Orchestration used by both the CLI and the Discord bot."""
import datetime as dt, re
from pathlib import Path
from src.config import load_brand, producers_config
from src.employees import producer as P, guardian as G, strategist as S
from src.render.renderer import render_png
from src import store

def produce_slot(brand: dict, slot: dict, revision_note=None, previous=None, only_producer=None) -> dict:
    """Run all producers on one slot → render → guardian. Returns {variants, guardian, pngs}."""
    variants, verdicts, pngs = [], [], {}
    for pc in producers_config():
        if only_producer and pc["id"] != only_producer: continue
        try:
            out = P.produce(brand, slot, pc, revision_note, previous)
            out["publish_at_local"] = slot["publish_at_local"]; out["product_sku"] = slot.get("product_sku")
            out.setdefault("render", {}).setdefault("fields", {})
            f = out["render"]["fields"]
            cap_d = out.get("caption") or {}
            f.setdefault("headline", cap_d.get("hook", "")); f.setdefault("subhead", cap_d.get("body", "")[:140])
            f.setdefault("cta", cap_d.get("cta", "")); f.setdefault("fact", cap_d.get("hook", ""))
            f.setdefault("product_name", next((p["name"] for p in brand["_products"]["products"] if p["sku"] == slot.get("product_sku")), ""))
            f.setdefault("source", cap_d.get("body", "")[:200]); f.setdefault("sku", slot.get("product_sku"))
            f.setdefault("title", cap_d.get("hook", "")); f.setdefault("heading", ""); f.setdefault("body", cap_d.get("body", "")); f.setdefault("page", "1/1")
            # strip HTML tags from text fields — LLM sometimes returns <br> in headlines
            for _fld in ("headline", "subhead", "fact", "title", "heading", "body"):
                if f.get(_fld): f[_fld] = re.sub(r'<[^>]+>', ' ', f[_fld]).strip()
            # illustration_svg must be inline SVG; reject file paths returned by the LLM
            if f.get("illustration_svg") and not str(f["illustration_svg"]).strip().startswith("<"):
                f["illustration_svg"] = ""
            if not f.get("image_1"):
                for a in out.get("assets", []):
                    if a.get("kind") == "photo_ref" and a.get("url"): f["image_1"] = a["url"]; break
            if not f.get("image_1"):
                prod = next((p for p in brand["_products"]["products"] if p["sku"] == slot.get("product_sku")), None)
                if prod and prod.get("photo_refs"): f["image_1"] = prod["photo_refs"][0]
            v = G.check(brand, out); verdicts.append(v)
            if v["verdict"] != "BLOCKED":
                png = render_png(brand, out); pngs[pc["id"]] = str(png)
            variants.append(out)
        except Exception as e:
            verdicts.append({"producer_id": pc["id"], "verdict": "BLOCKED", "checks": [], "reason_for_humans": f"producer error: {e}"})
    store.save_variants(brand, slot["slot_id"], variants, verdicts)
    return {"variants": variants, "guardian": verdicts, "pngs": pngs}

def plan(brand: dict, week_start: dt.date, demo=False):
    return S.demo_plan(brand, week_start) if demo else S.plan_week(brand, week_start)
