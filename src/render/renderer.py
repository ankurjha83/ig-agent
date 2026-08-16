"""HTML template (Jinja2) → PNG via Playwright. Templates live in brands/<id>/templates/."""
import asyncio, base64, mimetypes, shutil
from pathlib import Path
from typing import Optional
from jinja2 import Environment, FileSystemLoader
from src.config import PUBLIC_DIR, ROOT

def _data_uri(p: Path) -> str:
    mt = mimetypes.guess_type(str(p))[0] or "image/png"
    return f"data:{mt};base64," + base64.b64encode(p.read_bytes()).decode()

def _resolve_image(brand: dict, ref: Optional[str]) -> Optional[str]:
    if not ref: return None
    for cand in [Path(brand["_dir"]) / ref, ROOT / ref, ROOT / "product images" / Path(ref).name, Path(brand["_dir"]) / "assets" / "products" / Path(ref).name]:
        if cand.exists(): return _data_uri(cand)
    return None

def render_png(brand: dict, out: dict, size=(1080, 1350)) -> Path:
    tdir = Path(brand["_dir"]) / "templates"
    env = Environment(loader=FileSystemLoader(str(tdir)), autoescape=True)
    tid = out["render"]["template_id"]
    fields = dict(out["render"].get("fields", {}))
    # images → data URIs
    for k, v in list(fields.items()):
        if isinstance(v, str) and (v.endswith((".jpg", ".jpeg", ".png", ".webp"))):
            uri = _resolve_image(brand, v)
            fields[k] = uri or ""
    logo_dir = Path(brand["_dir"]) / "assets" / "logo"
    ctx = {"f": fields, "brand": brand, "css": (tdir / "base.css").read_text(),
           "logo_primary": _data_uri(logo_dir / "truharvest-primary.png") if (logo_dir / "truharvest-primary.png").exists() else "",
           "logo_white": _data_uri(logo_dir / "truharvest-white.png") if (logo_dir / "truharvest-white.png").exists() else "",
           "colorway": _colorway_hex(brand, out)}
    html = env.get_template(f"{tid}.html").render(**ctx)
    slot_dir = PUBLIC_DIR / brand["brand_id"] / out["slot_id"]
    slot_dir.mkdir(parents=True, exist_ok=True)
    png = slot_dir / f'{out["producer_id"]}-v{out.get("version",1)}.png'
    (slot_dir / f'{out["producer_id"]}-v{out.get("version",1)}.html').write_text(html)
    asyncio.run(_shoot(html, png, size))
    return png

def _colorway_hex(brand: dict, out: dict):
    sku = out.get("product_sku") or out.get("render", {}).get("fields", {}).get("sku")
    prod = next((p for p in brand["_products"]["products"] if p["sku"] == sku), None) if sku else None
    name = prod.get("colorway") if prod else None
    for cw in brand["visual"]["palette"]["colorways"]:
        if name and cw["name"] == name and cw["hex"].startswith("#"):
            return {"hex": cw["hex"], "tint": cw.get("tint", "#ffffff")}
    return {"hex": brand["visual"]["palette"]["primary"]["hex"], "tint": "#F6F1E7"}

async def _shoot(html: str, png: Path, size):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": size[0], "height": size[1]}, device_scale_factor=1)
        await pg.set_content(html, wait_until="load")
        await pg.wait_for_timeout(300)
        await pg.screenshot(path=str(png), full_page=False)
        await b.close()
