"""Local testing without Discord.
  python -m src.cli plan --brand tru-harvest [--demo]
  python -m src.cli produce --brand tru-harvest --slot 2026-08-24-01
  python -m src.cli produce-week --brand tru-harvest --week 2026-08-24
  python -m src.cli approve --brand tru-harvest --slot 2026-08-24-01 --producer A-claude
  python -m src.cli publish --brand tru-harvest
"""
import argparse, json, datetime as dt
from src.config import load_brand, env
from src import pipeline, store
from src.integrations import instagram, media_hosting
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--brand", default="tru-harvest")
    ap.add_argument("--slot"); ap.add_argument("--week"); ap.add_argument("--producer"); ap.add_argument("--demo", action="store_true")
    a = ap.parse_args(); brand = load_brand(a.brand)
    if a.cmd == "plan":
        ws = dt.date.fromisoformat(a.week) if a.week else (dt.date.today() + dt.timedelta(days=(7 - dt.date.today().weekday()) % 7))
        p = pipeline.plan(brand, ws, demo=a.demo); print(json.dumps(p, indent=2, ensure_ascii=False))
    elif a.cmd in ("produce", "produce-week"):
        ws = a.week or (a.slot[:10] if a.slot else None)
        # find plan containing slot
        plans = sorted(Path(brand["_dir"], "queue").glob("plan-*.json"))
        slots = [s for pl in plans for s in json.loads(pl.read_text())["slots"]]
        todo = [s for s in slots if (a.cmd == "produce" and s["slot_id"] == a.slot) or (a.cmd == "produce-week" and s["slot_id"].startswith(ws[:7]))]
        for s in todo:
            r = pipeline.produce_slot(brand, s)
            print(s["slot_id"]); [print("  ", g["producer_id"], g["verdict"], g["reason_for_humans"]) for g in r["guardian"]]
            for k, v in r["pngs"].items(): print("   png", k, v)
    elif a.cmd == "approve":
        v = store.load_variants(brand, a.slot); png = f'public/media/{brand["brand_id"]}/{a.slot}/{a.producer}-v1.png'
        print(store.approve(brand, a.slot, a.producer, "cli", png))
    elif a.cmd == "publish":
        for p, rec in store.pending_publish(brand):
            if env("ENABLE_PUBLISH", "false").lower() != "true": print("ENABLE_PUBLISH=false; would publish", rec["slot_id"]); continue
            url = media_hosting.publish_files([Path(rec["png"])])[0]
            res = instagram.publish_image(brand["channels"]["instagram"]["ig_user_id"], url, rec["caption"])
            rec.update(status="published", **res); p.write_text(json.dumps(rec, indent=2)); store.log_publish(brand, rec); print(res)
    else: print(__doc__)

if __name__ == "__main__": main()
