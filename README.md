# 🦞 OpenClaw Calendar

Visual 7-day weekly calendar for OpenClaw cron jobs & GitHub Actions schedules.

📅 **Live:** https://greg18jrr-ops.github.io/openclaw-calendar/

## Add a Job

Edit [`schedules/jobs.json`](schedules/jobs.json):

```json
{
  "name": "my-job",
  "description": "What it does",
  "cron": "0 9 * * *",
  "tz": "Asia/Taipei",
  "color": "#E74C3C",
  "tag": "openclaw"
}
```

The calendar auto-updates daily via GitHub Actions.
