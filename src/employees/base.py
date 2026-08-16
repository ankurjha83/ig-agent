import json
from typing import Optional
from src.config import AGENTS_DIR

def system_prompt(role: str) -> str:
    common = (AGENTS_DIR / "_common.md").read_text()
    role_md = (AGENTS_DIR / f"{role}.md").read_text()
    return common + "\n\n" + role_md + "\n\nReply with ONLY the JSON object specified above. No prose."

def brand_context(brand: dict, sku: Optional[str] = None) -> str:
    b = {k: v for k, v in brand.items() if not k.startswith("_")}
    prod = None
    if sku:
        prod = next((p for p in brand["_products"]["products"] if p["sku"] == sku), None)
    return "brand.json:\n" + json.dumps(b, ensure_ascii=False) + "\n\nproduct:\n" + json.dumps(prod, ensure_ascii=False)
