"""A producer = prompt + model. Several producers run on the same slot for A/B/C."""
import json, hashlib
from typing import Optional
from src.employees.base import system_prompt, brand_context
from src.integrations.llm import complete_json

def produce(brand: dict, slot: dict, producer: dict, revision_note: Optional[str] = None, previous: Optional[dict] = None) -> dict:
    user = brand_context(brand, slot.get("product_sku"))
    user += "\n\nslot:\n" + json.dumps(slot, ensure_ascii=False)
    if revision_note:
        user += f"\n\nHUMAN REVISION NOTE: {revision_note}\nPrevious output:\n{json.dumps(previous, ensure_ascii=False)}"
    out = complete_json(producer["provider"], producer["model"], system_prompt("producer"), user)
    out["producer_id"] = producer["id"]
    out["model"] = f'{producer["provider"]}:{producer["model"]}'
    out["slot_id"] = slot["slot_id"]
    cap = out.get("caption", {})
    if "full_text" not in cap or not cap["full_text"]:
        cap["full_text"] = "\n\n".join(x for x in [cap.get("hook", ""), cap.get("body", ""), cap.get("cta", ""),
                                                   " ".join(cap.get("hashtags", []))] if x)
        out["caption"] = cap
    out["content_hash"] = hashlib.sha256(cap["full_text"].encode()).hexdigest()[:16]
    return out
