#!/bin/bash
set -e
cd /Users/austinhuang/.openclaw/workspace/openclaw-calendar
git rebase --abort || true
git fetch origin main
git reset --hard origin/main
python3 scripts/generate.py
git add -A
if ! git diff --cached --quiet; then
  git commit -m 'chore: sync openclaw cron jobs'
fi
git push
