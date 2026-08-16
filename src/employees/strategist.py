import json, datetime as dt
from pathlib import Path
from src.employees.base import system_prompt, brand_context
from src.integrations.llm import complete_json
from src.config import strategist_config

def plan_week(brand: dict, week_start: dt.date) -> dict:
    d = Path(brand["_dir"])
    insights = (d / "insights.md").read_text() if (d / "insights.md").exists() else "(none yet)"
    log = (d / "publish_log.jsonl").read_text() if (d / "publish_log.jsonl").exists() else ""
    recent = [json.loads(l) for l in log.splitlines()[-30:] if l.strip()]
    user = brand_context(brand) + f"\n\nweek_start: {week_start.isoformat()}\n\ninsights.md:\n{insights}\n\nrecent_posts:\n{json.dumps(recent)}"
    cfg = strategist_config()
    plan = complete_json(cfg["provider"], cfg["model"], system_prompt("strategist"), user)
    (d / "queue").mkdir(exist_ok=True)
    (d / "queue" / f"plan-{week_start.isoformat()}.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False))
    return plan

def demo_plan(brand: dict, week_start: dt.date) -> dict:
    """No-LLM plan for first dry runs."""
    slots = []
    days = ["Mon","Tue","Thu","Fri","Sat"]
    picks = [("WN-MASCRAN-250","product_hero","ingredient_truth","Cranberries: tart on purpose."),
             ("WN-MASCRAN-250","did_you_know","ingredient_truth","Very low sodium. Big on flavour."),
             ("WN-MASCRAN-250","product_hero","everyday_snacking","The 4pm snack that doesn't need justification."),
             ("WN-MASCRAN-250","did_you_know","recipes_uses","One handful of cranberries, three ways to use it."),
             ("WN-MASCRAN-250","product_hero","everyday_snacking","Masala cranberry: snack first, healthy second.")]
    for i,(sku,tpl,pillar,hook) in enumerate(picks):
        date = week_start + dt.timedelta(days=[0,1,3,4,5][i])
        slots.append({"slot_id": f"{date.isoformat()}-01","publish_at_local": f"{date.isoformat()}T12:30","pillar":pillar,"format":"single_image",
                      "template_id":tpl,"product_sku":sku,"hook":hook,"angle":"","asset_brief":"real product photo","cta":"Find us on Amazon India — link in bio.","success_metric":"saves"})
    plan = {"brand_id": brand["brand_id"], "week_start": week_start.isoformat(), "lessons_applied": ["demo plan"], "slots": slots, "discord_summary": "Demo plan: 5 single-image posts."}
    d = Path(brand["_dir"]); (d/"queue").mkdir(exist_ok=True)
    (d / "queue" / f"plan-{week_start.isoformat()}.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False))
    return plan
