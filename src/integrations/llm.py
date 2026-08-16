"""One interface, two providers. All employees call complete_json()."""
import json, re, httpx
from src.config import env

def _strip_fences(t: str) -> str:
    t = t.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    return t

def complete_text(provider: str, model: str, system: str, user: str, max_tokens: int = 2000) -> str:
    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=env("ANTHROPIC_API_KEY"))
        r = client.messages.create(model=model, max_tokens=max_tokens, system=system,
                                   messages=[{"role": "user", "content": user}])
        return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    if provider == "ollama":
        base = env("OLLAMA_BASE_URL", "http://localhost:11434")
        payload = {"model": model, "stream": False, "format": "json",
                   "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                   "options": {"num_predict": max_tokens, "temperature": 0.7}}
        r = httpx.post(f"{base}/api/chat", json=payload, timeout=300)
        r.raise_for_status()
        return r.json()["message"]["content"]
    raise ValueError(f"unknown provider {provider}")

def complete_json(provider: str, model: str, system: str, user: str, retries: int = 1) -> dict:
    last_err = None
    for attempt in range(retries + 1):
        txt = complete_text(provider, model, system, user)
        try:
            return json.loads(_strip_fences(txt))
        except json.JSONDecodeError as e:
            last_err = e
            user = user + f"\n\nYour previous reply was not valid JSON ({e}). Reply with ONLY the JSON object."
    raise RuntimeError(f"LLM did not return JSON after retries: {last_err}")
