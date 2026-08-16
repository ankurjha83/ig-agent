#!/bin/zsh
set -e
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
brew list ffmpeg >/dev/null 2>&1 || brew install ffmpeg
brew list ollama >/dev/null 2>&1 || brew install ollama
ollama pull qwen2.5:14b; ollama pull llama3.1:8b
cp -n .env.example .env || true
echo "Done. Fill .env, then: python -m src.cli plan --demo && python -m src.cli produce-week --week $(date -v+Mon +%F 2>/dev/null || date +%F)"
