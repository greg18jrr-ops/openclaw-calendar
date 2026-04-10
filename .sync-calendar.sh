#!/bin/zsh
set -e
cd /Users/austinhuang/.openclaw/workspace/openclaw-calendar
python3 scripts/generate.py
git add schedules/jobs.json docs/index.html .sync-calendar.sh
if ! git diff --cached --quiet; then
  git commit -m 'chore: sync openclaw cron jobs'
fi
git push
