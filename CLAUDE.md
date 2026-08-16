# CLAUDE.md — Insta Agent (drop this in the repo root)

## What this repo is
A multi-brand, faceless-Instagram content studio: five AI "employees" (Strategist, Producer, Guardian, Publisher, Analyst) run inside a Discord server per brand; humans approve with ✅ / ✏️ / ❌ in `#review`. Read `PLAN.md` first, then `agents/*.md`, then `brands/tru-harvest/brand.json` and `products.json`. Those files are the spec; do not redesign them — implement them.

## Non-negotiables
- No publish without a ✅ from a user id in `brand.json → channels.discord.approvers`. Content is frozen (hashed) at approval.
- Guardian runs before any review card is shown to humans. BLOCKED items get no approval path.
- Never generate packaging imagery; pack shots come only from `photo_refs`.
- All facts/claims come from `products.json`; missing → `NEEDS_DATA`, never guessed.
- Everything keyed by `brand_id`; adding a brand = new folder under `brands/`, zero code changes.
- Secrets only via GitHub Actions secrets locally mirrored in `.env`; never commit tokens.
- All rendering is HTML/CSS in `brands/<id>/templates/` using CSS variables from `base.css`; Guardian verifies hex values against brand.json.

## Stack (fixed)
Python 3.12 · GitHub Actions (cron + workflow_dispatch) · Discord webhooks + interactions (buttons/modals) via a Cloudflare Worker · anthropic SDK · Playwright (HTML→PNG) · ffmpeg (reels) · GitHub Pages for public media URLs · Instagram Graph API v21+ · repo files as state (JSON/JSONL committed by Actions). No Canva, no R2, no Fly, no Higgsfield.

## Layout to build
```
src/
  bot.py               # discord client, command + reaction handlers, per-brand guild routing
  scheduler.py         # cron jobs: strategist (Sun 06:00), analyst (Sun 05:00 + 48h post hooks), token refresh, due publishes
  brand.py             # load/validate brand.json + products.json (pydantic), TODO detection
  store.py             # tables: slots, posts, approvals, publish_log, insights, costs
  employees/
    base.py            # builds prompt = agents/_common.md + agents/<name>.md + inputs; calls Claude; validates JSON output
    strategist.py producer.py guardian.py publisher.py analyst.py
  integrations/
    claude.py canva.py higgsfield.py r2.py instagram.py discord_ui.py
  cli.py               # `python -m src.cli produce --brand tru-harvest --slot 2026-08-25-01` etc. for local testing
tests/                 # unit tests for guardian checks, approval gate, hashing, brand loader
```

## Build order (mirror PLAN.md weeks)
1. `brand.py`, `store.py`, `bot.py` with channels + reaction gate + `#ops` logging. Prove: reacting ✅ as a non-approver is ignored and logged.
2. `producer.py` end-to-end for `single_image` using a real `photo_ref` (no generation yet) → Canva autofill/export → R2 → review card. Then `guardian.py`. Then `publisher.py` image publish. Then carousel, then reels + Higgsfield.
3. `analyst.py` + `insights.md` writer.
4. `strategist.py` + plan approval in `#calendar`.

## Conventions
- Each employee: `run(inputs) -> pydantic model`; retries on invalid JSON once with the validation error appended.
- Discord messages ≤ 5 bullets; JSON goes as file attachments.
- Log every Claude/Canva/Higgsfield/IG call with cost estimate to `costs` table.
- Tests must pass before any publish path is enabled (`ENABLE_PUBLISH=false` by default).
