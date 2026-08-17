"""Discord bot: /plan, /produce, review cards with A/B/C approve buttons, scheduled publisher.
Run:  python -m src.bot
"""
import asyncio, json, datetime as dt
from pathlib import Path
import discord
from discord import app_commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.config import load_brand, env, producers_config, ROOT
from src import pipeline, store
from src.integrations import instagram, media_hosting

BRAND_ID = env("BRANDS", "tru-harvest").split(",")[0]
brand = load_brand(BRAND_ID)
CH = brand["channels"]["discord"]["channels"]
APPROVERS = {str(x) for x in brand["channels"]["discord"]["approvers"]}

intents = discord.Intents.default(); intents.message_content = True
client = discord.Client(intents=intents); tree = app_commands.CommandTree(client)

def ch(name): return client.get_channel(int(CH[name]))

class ReviewView(discord.ui.View):
    def __init__(self, slot_id: str, producer_ids: list[str]):
        super().__init__(timeout=None)
        for pid in producer_ids:
            self.add_item(ApproveBtn(slot_id, pid))
        self.add_item(RejectBtn(slot_id))

class ApproveBtn(discord.ui.Button):
    def __init__(self, slot_id, pid):
        super().__init__(label=f"Approve {pid}", style=discord.ButtonStyle.success, custom_id=f"approve:{slot_id}:{pid}")
        self.slot_id, self.pid = slot_id, pid
    async def callback(self, it: discord.Interaction):
        if str(it.user.id) not in APPROVERS:
            await it.response.send_message("Not an approver.", ephemeral=True); return
        png = f'public/media/{brand["brand_id"]}/{self.slot_id}/{self.pid}-v1.png'
        rec = store.approve(brand, self.slot_id, self.pid, it.user.id, png)
        for c in self.view.children: c.disabled = True
        await it.response.edit_message(view=self.view)
        await it.followup.send(f"✅ {self.slot_id} approved → **{self.pid}** (hash {rec['content_hash']}). Scheduled {rec['publish_at_local']}.")

class RejectBtn(discord.ui.Button):
    def __init__(self, slot_id):
        super().__init__(label="Reject all", style=discord.ButtonStyle.danger, custom_id=f"reject:{slot_id}")
        self.slot_id = slot_id
    async def callback(self, it: discord.Interaction):
        if str(it.user.id) not in APPROVERS:
            await it.response.send_message("Not an approver.", ephemeral=True); return
        store.reject(brand, self.slot_id, it.user.id)
        for c in self.view.children: c.disabled = True
        await it.response.edit_message(view=self.view); await it.followup.send(f"❌ {self.slot_id} rejected. Use `/revise` with a note to regenerate.")

async def post_review(slot: dict, result: dict):
    channel = ch("review")
    thread_msg = await channel.send(f"**{slot['slot_id']} · {slot['format']} · {slot.get('hook','')}**\n"
                                    f"Product: {slot.get('product_sku')} · Template: {slot.get('template_id')} · Time: {slot['publish_at_local']}")
    thread = await thread_msg.create_thread(name=slot["slot_id"][:90])
    ok_ids = []
    for v, g in zip(result["variants"], result["guardian"]):
        pid = v["producer_id"]; stamp = {"PASS": "🛡️ PASS", "FIXED": "🛡️ FIXED", "BLOCKED": "🛡️ BLOCKED"}[g["verdict"]]
        emb = discord.Embed(title=f"{pid}  ·  {v.get('model','')}", description=v["caption"]["full_text"][:3800])
        emb.set_footer(text=f"{stamp} — {g['reason_for_humans']}")
        files = []
        if pid in result["pngs"]:
            files = [discord.File(result["pngs"][pid])]; emb.set_image(url=f"attachment://{Path(result['pngs'][pid]).name}"); ok_ids.append(pid)
        await thread.send(embed=emb, files=files)
    for g in result["guardian"]:
        if g["producer_id"] not in [v["producer_id"] for v in result["variants"]]:
            await thread.send(f"⚠️ {g['producer_id']}: {g['reason_for_humans']}")
    if ok_ids: await thread.send("Pick one:", view=ReviewView(slot["slot_id"], ok_ids))

@tree.command(name="plan", description="Strategist: plan next week (demo=true for no-LLM plan)")
async def plan_cmd(it: discord.Interaction, demo: bool = False):
    await it.response.defer()
    ws = dt.date.today() + dt.timedelta(days=(7 - dt.date.today().weekday()) % 7)
    p = await asyncio.to_thread(pipeline.plan, brand, ws, demo)
    lines = "\n".join(f"• {s['slot_id']} {s['format']} {s.get('product_sku')} — {s['hook']}" for s in p["slots"])
    await ch("calendar").send(f"**Plan {ws}**\n{p.get('discord_summary','')}\n{lines}\nRun `/produce week:{ws}` to generate.")
    await it.followup.send(f"Plan {ws} posted to #calendar.")

@tree.command(name="produce", description="Producers A/B/C generate posts for a week or one slot")
async def produce_cmd(it: discord.Interaction, week: str = "", slot: str = ""):
    await it.response.defer()
    plans = sorted(Path(brand["_dir"], "queue").glob("plan-*.json"))
    slots = [s for pl in plans for s in json.loads(pl.read_text())["slots"]]
    todo = [s for s in slots if (slot and s["slot_id"] == slot) or (week and s["slot_id"] >= week and s["slot_id"] < (dt.date.fromisoformat(week) + dt.timedelta(days=7)).isoformat())]
    await it.followup.send(f"Producing {len(todo)} slot(s) with {[p['id'] for p in producers_config()]}…")
    for s in todo:
        r = await asyncio.to_thread(pipeline.produce_slot, brand, s)
        await post_review(s, r)

@tree.command(name="revise", description="Regenerate one slot with a note (all producers)")
async def revise_cmd(it: discord.Interaction, slot: str, note: str):
    await it.response.defer()
    plans = sorted(Path(brand["_dir"], "queue").glob("plan-*.json"))
    s = next(s for pl in plans for s in json.loads(pl.read_text())["slots"] if s["slot_id"] == slot)
    prev = store.load_variants(brand, slot)
    r = await asyncio.to_thread(pipeline.produce_slot, brand, s, note, prev)
    await post_review(s, r); await it.followup.send("Revised.")

@tree.command(name="adhoc", description="Create an ad-hoc post right now — no plan needed")
@app_commands.describe(
    sku="Product to post about",
    hook="What you want to say / the angle for this post",
    template="Template to use (default: product_hero)",
    pillar="Content pillar (default: ingredient_truth)",
)
async def adhoc_cmd(it: discord.Interaction, sku: str, hook: str,
                    template: str = "product_hero", pillar: str = "ingredient_truth"):

    if str(it.user.id) not in APPROVERS:
        await it.response.send_message("Not an approver.", ephemeral=True); return
    await it.response.defer()
    slot_id = f"adhoc-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    slot = {
        "slot_id": slot_id,
        "publish_at_local": dt.datetime.now().strftime("%Y-%m-%dT%H:%M"),
        "pillar": pillar,
        "format": "single_image",
        "template_id": template,
        "product_sku": sku,
        "hook": hook,
        "angle": "",
        "asset_brief": "real product photo",
        "cta": "Find us on Amazon India — link in bio.",
        "success_metric": "saves",
    }
    r = await asyncio.to_thread(pipeline.produce_slot, brand, slot)
    await post_review(slot, r)
    await it.followup.send(f"Ad-hoc slot `{slot_id}` posted to #review.")

@adhoc_cmd.autocomplete("sku")
async def adhoc_sku_ac(it: discord.Interaction, current: str):
    products = brand.get("_products", {}).get("products", [])
    return [
        app_commands.Choice(name=f"{p['name']} ({p['sku']})", value=p["sku"])
        for p in products
        if current.lower() in p["name"].lower() or current.lower() in p["sku"].lower()
    ][:25]

@adhoc_cmd.autocomplete("template")
async def adhoc_template_ac(it: discord.Interaction, current: str):
    templates = [t["id"] for t in brand["visual"]["templates"]["list"]]
    return [app_commands.Choice(name=t, value=t) for t in templates if current.lower() in t][:25]

@adhoc_cmd.autocomplete("pillar")
async def adhoc_pillar_ac(it: discord.Interaction, current: str):
    pillars = [p["id"] for p in brand["content"]["pillars"]]
    return [app_commands.Choice(name=p, value=p) for p in pillars if current.lower() in p][:25]

@tree.command(name="publish", description="Publish all approved-and-due slots to Instagram now")
async def publish_cmd(it: discord.Interaction):
    if str(it.user.id) not in APPROVERS:
        await it.response.send_message("Not an approver.", ephemeral=True); return
    await it.response.defer()
    await publisher_tick()
    await it.followup.send("Publish tick done — check #published and #ops.")

async def publisher_tick():
    for p, rec in store.pending_publish(brand):
        due = dt.datetime.fromisoformat(rec["publish_at_local"]) if rec.get("publish_at_local") else dt.datetime.now()
        if dt.datetime.now() < due: continue
        if env("ENABLE_PUBLISH", "false").lower() != "true":
            await ch("ops").send(f"(dry) would publish {rec['slot_id']} {rec['producer_id']}"); rec["status"] = "dry"; p.write_text(json.dumps(rec, indent=2)); continue
        try:
            url = (await asyncio.to_thread(media_hosting.publish_files, [ROOT / rec["png"]]))[0]
            res = await asyncio.to_thread(instagram.publish_image, brand["channels"]["instagram"]["ig_user_id"], url, rec["caption"])
            rec.update(status="published", published_at=dt.datetime.utcnow().isoformat(), **res)
            p.write_text(json.dumps(rec, indent=2)); store.log_publish(brand, rec)
            await ch("published").send(f"📤 {rec['slot_id']} by {rec['producer_id']} → {res.get('permalink')}")
        except Exception as e:
            await ch("ops").send(f"❌ publish failed {rec['slot_id']}: {e}")

@client.event
async def on_ready():
    await tree.sync()
    sched = AsyncIOScheduler(); sched.add_job(publisher_tick, "interval", minutes=30); sched.start()
    print(f"ready as {client.user}; producers={[p['id'] for p in producers_config()]}")

if __name__ == "__main__":
    client.run(env("DISCORD_BOT_TOKEN"))
