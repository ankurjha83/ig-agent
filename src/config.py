import os, json
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

def env(k, default=None):
    v = os.getenv(k, default)
    return v

BRANDS_DIR = ROOT / "brands"
PUBLIC_DIR = ROOT / "public" / "media"
AGENTS_DIR = ROOT / "agents"

def load_brand(brand_id: str) -> dict:
    d = BRANDS_DIR / brand_id
    brand = json.loads((d / "brand.json").read_text())
    products = json.loads((d / "products.json").read_text())
    brand["_dir"] = str(d)
    brand["_products"] = products
    return brand

def producers_config() -> list[dict]:
    """PRODUCERS env: JSON list of {id, provider, model}. Defaults to Claude + 2 Ollama."""
    raw = env("PRODUCERS")
    if raw:
        return json.loads(raw)
    return [
        {"id": "A-claude", "provider": "anthropic", "model": env("ANTHROPIC_MODEL", "claude-sonnet-4-5")},
        {"id": "B-qwen", "provider": "ollama", "model": env("OLLAMA_MODEL_B", "qwen2.5:14b")},
        {"id": "C-llama", "provider": "ollama", "model": env("OLLAMA_MODEL_C", "llama3.1:8b")},
    ]

def strategist_config() -> dict:
    return {"provider": env("STRATEGIST_PROVIDER", "anthropic"), "model": env("STRATEGIST_MODEL", env("ANTHROPIC_MODEL", "claude-sonnet-4-5"))}
