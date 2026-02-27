#!/usr/bin/env python3
"""
sync_jobs.py - Sync OpenClaw cron jobs → schedules/jobs.json → regenerate calendar
Run by OpenClaw cron daily.
"""

import json
import os
import subprocess
import sys

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOBS_PATH = os.path.join(REPO_DIR, "schedules", "jobs.json")

# Default color/tag mapping (by name pattern)
TAG_COLORS = {
    "openclaw": "#4A90D9",
    "github-actions": "#E67E22",
}

NAME_COLORS = {
    "daily-review":       "#4A90D9",
    "stock-forum-daily":  "#27AE60",
    "weekly-review":      "#8E44AD",
    "generate-calendar":  "#E67E22",
}

def get_openclaw_jobs():
    result = subprocess.run(
        ["openclaw", "cron", "list", "--json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(result.stdout)
    return data.get("jobs", [])

def normalize(jobs):
    # Load existing for color/tag preservation
    existing = {}
    if os.path.exists(JOBS_PATH):
        with open(JOBS_PATH) as f:
            for j in json.load(f):
                existing[j["name"]] = j

    result = []

    # GitHub Actions job (always keep)
    result.append({
        "name": "generate-calendar",
        "description": "自動產生本週曆頁面並 push 到 GitHub Pages",
        "cron": "0 0 * * *",
        "tz": "UTC",
        "color": NAME_COLORS.get("generate-calendar", "#E67E22"),
        "tag": "github-actions"
    })

    # OpenClaw jobs
    for job in jobs:
        name = job.get("name", "unknown")
        schedule = job.get("schedule", {})
        cron_expr = schedule.get("expr", "")
        tz = schedule.get("tz", "UTC") or "UTC"
        description = job.get("description", "")

        # Preserve existing color if known, else pick from map
        color = existing.get(name, {}).get("color", NAME_COLORS.get(name, "#58A6FF"))

        result.append({
            "name": name,
            "description": description,
            "cron": cron_expr,
            "tz": tz,
            "color": color,
            "tag": "openclaw"
        })

    return result

def main():
    print("🔄 Fetching OpenClaw cron jobs...")
    jobs = get_openclaw_jobs()
    print(f"   Found {len(jobs)} jobs")

    normalized = normalize(jobs)

    with open(JOBS_PATH, "w") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)
    print(f"✅ Updated: {JOBS_PATH}")

    # Regenerate calendar HTML
    generate_script = os.path.join(REPO_DIR, "scripts", "generate.py")
    subprocess.run(["python3", generate_script], check=True)

    # Git commit & push
    subprocess.run(["git", "-C", REPO_DIR, "add", "-A"], check=True)
    result = subprocess.run(
        ["git", "-C", REPO_DIR, "diff", "--cached", "--quiet"]
    )
    if result.returncode != 0:
        subprocess.run([
            "git", "-C", REPO_DIR, "commit",
            "-m", "chore: sync openclaw cron jobs"
        ], check=True)
        subprocess.run(["git", "-C", REPO_DIR, "push"], check=True)
        print("✅ Pushed to GitHub!")
    else:
        print("ℹ️  No changes to commit.")

if __name__ == "__main__":
    main()
