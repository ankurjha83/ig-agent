# START HERE — testing today on the Mac mini (v0.3)

You have a working codebase. Three producers (A = Claude, B = Qwen 14B local, C = Llama 8B local) write the same post; you approve one in Discord. Nothing publishes until you set ENABLE_PUBLISH=true.

## Part 1 — get a first render on screen (≈40 min, no Discord, no Instagram)
1. Unzip; put the contents in `~/Desktop/Ankur Projects/Insta Agent`. Keep `product images/` there too (photos are also copied into `brands/tru-harvest/assets/products/`).
2. Terminal in that folder: `./scripts/setup.sh` — makes a venv, installs Python deps + Playwright's Chromium, installs ffmpeg and Ollama via Homebrew, pulls the two local models (≈13 GB, be patient), copies `.env.example` → `.env`.
3. Edit `.env`: paste your `ANTHROPIC_API_KEY` (only paid item; set a spend cap in the console). Leave everything else for now.
4. `source .venv/bin/activate`
5. `python -m src.cli plan --demo` → writes a 5-post demo plan for next Monday (no LLM used).
6. `python -m src.cli produce-week --week 2026-08-24` (use the Monday it printed). This runs A, B, C on each slot, Guardian-checks, renders PNGs. Open `public/media/tru-harvest/<slot>/` and look at `A-claude-v1.png`, `B-qwen-v1.png`, `C-llama-v1.png`.
7. Judge. Edit `brands/tru-harvest/brand.json → voice` and the HTML in `templates/` until you'd post it. Re-run step 6. This loop is the whole point of week 1.

## Part 2 — approvals in Discord (≈30 min)
8. discord.com/developers → New Application "Tru Harvest Studio" → Bot → copy token into `.env` `DISCORD_BOT_TOKEN`; enable **Message Content Intent**; OAuth2 → URL generator → scopes `bot` + `applications.commands`, permissions: Send Messages, Embed Links, Attach Files, Create Public Threads, Send Messages in Threads, Use Slash Commands → invite to a new server "Tru Harvest Studio".
9. Create channels `#brand #calendar #review #published #insights #ops`. Turn on Developer Mode (User Settings → Advanced), right-click each channel → Copy ID; right-click your and Swati's names → Copy ID. Paste all into `brand.json → channels.discord`.
10. `python -m src.bot` (keep the terminal open). In Discord: `/plan demo:true` → then `/produce week:2026-08-24`. Cards appear in `#review`, one thread per post, A/B/C side by side with buttons **Approve A-claude / Approve B-qwen / Approve C-llama / Reject all**. Only your two IDs can approve. `/revise slot:… note:"…"` regenerates.
11. To make it permanent on the Mac mini: `cp scripts/com.truharvest.igagent.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/com.truharvest.igagent.plist`. Logs in `/tmp/igagent.log`.

## Part 3 — real publishing to @seenfromseoul (≈45 min, when Part 2 feels good)
12. Instagram: switch @seenfromseoul to a Business account and link a Facebook Page (Instagram app → Settings → Account type & tools). Meta app IndoVista → add product "Instagram Graph API" → Graph API Explorer → permissions `instagram_basic, instagram_content_publish, instagram_manage_insights, pages_show_list, pages_read_engagement, business_management` → Generate token → exchange for a long-lived token (docs: "Long-Lived Access Tokens"). Put it in `.env` `IG_LONG_LIVED_TOKEN`. Get `ig_user_id` via `GET /me/accounts` → page → `?fields=instagram_business_account`; put in `brand.json → channels.instagram`.
13. GitHub: `git init && gh repo create ig-agent --private --source . --push` (or via web). Settings → Pages → Deploy from branch `main`, folder `/public`. Put the Pages URL in `.env` `PAGES_BASE_URL`. (Instagram must be able to fetch the image; a private repo's Pages site is public.)
14. Set `ENABLE_PUBLISH=true`. Approve one card. The publisher runs every 30 min; when the slot's time arrives it commits the PNG, pushes, publishes, and posts the link in `#published`. Set `publish_at_local` in the plan to a few minutes ahead for the first test.

## What's next after this works
Analyst (48-h stats by producer → `#insights`, `insights.md`), the LLM Strategist for real plans (`/plan` without demo already calls Claude), 5 more templates, reels via ffmpeg, carousels, then swap the handle to the brand account, then copy the folder for brand #2.

## Commands cheat-sheet
`/plan demo:true` · `/plan` (Claude) · `/produce week:YYYY-MM-DD` · `/produce slot:YYYY-MM-DD-01` · `/revise slot:… note:…` · CLI equivalents in `src/cli.py`.
