# ig-agent
Faceless Instagram studio run by AI producers, approved by humans on Discord, running on a Mac mini. Multi-brand by folder. See START_HERE.md.

```
agents/          prompts (the employees' job descriptions)
brands/<id>/     brand.json products.json templates/ assets/ queue/ publish_log.jsonl insights.md
src/bot.py       Discord bot (slash commands, A/B/C approve buttons, 30-min publisher)
src/cli.py       same pipeline without Discord
src/pipeline.py  producers → guardian → render
src/employees/   producer, guardian, strategist
src/render/      Jinja2 HTML → Playwright PNG
src/integrations instagram, llm (anthropic|ollama), media_hosting (git → GitHub Pages)
public/media/    rendered outputs (served by GitHub Pages)
scripts/         setup.sh, launchd plist
```
Add a producer: edit `PRODUCERS` in `.env`. Add a brand: copy `brands/tru-harvest`.
