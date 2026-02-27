#!/usr/bin/env python3
"""
generate.py - Generate a 7-day weekly calendar HTML from jobs.json
Outputs: docs/index.html
"""

import json
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from croniter import croniter

DISPLAY_TZ = ZoneInfo("Asia/Taipei")
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
HOURS = list(range(0, 24))

def get_week_range():
    """Return Monday to Sunday of current week in display TZ."""
    now = datetime.now(DISPLAY_TZ)
    monday = now - timedelta(days=now.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    return [monday + timedelta(days=i) for i in range(7)]

def get_occurrences(job, week_days):
    """Return list of (day_index, hour, minute) for job in the current week."""
    cron_expr = job["cron"]
    job_tz = ZoneInfo(job.get("tz", "UTC"))
    results = []

    week_start = week_days[0].astimezone(job_tz) - timedelta(hours=1)
    week_end = week_days[-1].astimezone(job_tz) + timedelta(hours=25)

    try:
        it = croniter(cron_expr, week_start)
        while True:
            next_run = it.get_next(datetime).replace(tzinfo=job_tz)
            if next_run > week_end:
                break
            # Convert to display TZ
            next_display = next_run.astimezone(DISPLAY_TZ)
            day_idx = next_display.weekday()  # 0=Mon
            if 0 <= day_idx <= 6:
                results.append((day_idx, next_display.hour, next_display.minute))
    except Exception:
        pass

    return results

def generate_html(jobs, week_days):
    now = datetime.now(DISPLAY_TZ)
    week_label = f"{week_days[0].strftime('%Y/%m/%d')} – {week_days[6].strftime('%Y/%m/%d')}"

    # Build event grid: grid[day][hour] = list of jobs
    grid = [[[] for _ in range(24)] for _ in range(7)]
    for job in jobs:
        for (day_idx, hour, minute) in get_occurrences(job, week_days):
            grid[day_idx][hour].append(job)

    # Tag colors for legend
    tag_colors = {}
    for job in jobs:
        tag_colors[job["tag"]] = job["color"]

    day_headers = "".join(
        f'<th class="day-header{"today" if week_days[i].date() == now.date() else ""}">'
        f'{DAYS[i]}<br><span class="day-date">{week_days[i].strftime("%m/%d")}</span></th>'
        for i in range(7)
    )

    rows = ""
    for hour in HOURS:
        cells = ""
        for day in range(7):
            events = grid[day][hour]
            if events:
                event_html = "".join(
                    f'<div class="event" style="background:{j["color"]}" title="{j["description"]}">'
                    f'{j["name"]}</div>'
                    for j in events
                )
                cells += f'<td class="cell has-event">{event_html}</td>'
            else:
                cells += '<td class="cell"></td>'
        rows += f'<tr><td class="hour-label">{hour:02d}:00</td>{cells}</tr>'

    legend = "".join(
        f'<span class="legend-item"><span class="legend-dot" style="background:{color}"></span>{tag}</span>'
        for tag, color in tag_colors.items()
    )

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🦞 OpenClaw Calendar</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0d1117; color: #e6edf3; }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 24px 16px; }}
    h1 {{ font-size: 1.6rem; margin-bottom: 4px; }}
    h1 span {{ font-size: 1rem; color: #8b949e; font-weight: normal; margin-left: 8px; }}
    .meta {{ color: #8b949e; font-size: 0.85rem; margin-bottom: 16px; }}
    .legend {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 20px; }}
    .legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 0.85rem; }}
    .legend-dot {{ width: 12px; height: 12px; border-radius: 3px; }}
    .calendar {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 700px; }}
    th, td {{ border: 1px solid #21262d; }}
    .corner {{ width: 52px; background: #161b22; }}
    .day-header {{ background: #161b22; text-align: center; padding: 8px 4px; font-size: 0.85rem; font-weight: 600; min-width: 120px; }}
    .day-header.today {{ background: #1f3a5f; color: #58a6ff; }}
    .day-date {{ font-size: 0.75rem; font-weight: normal; color: #8b949e; }}
    .day-header.today .day-date {{ color: #58a6ff; }}
    .hour-label {{ width: 52px; text-align: right; padding: 0 8px; font-size: 0.72rem; color: #8b949e; background: #161b22; vertical-align: top; padding-top: 4px; white-space: nowrap; }}
    .cell {{ height: 36px; padding: 2px; vertical-align: top; background: #0d1117; }}
    .cell:hover {{ background: #161b22; }}
    .has-event {{ background: #0d1117; }}
    .event {{ border-radius: 4px; padding: 2px 5px; font-size: 0.72rem; font-weight: 500; color: #fff; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: default; opacity: 0.92; }}
    .event:hover {{ opacity: 1; }}
    footer {{ margin-top: 24px; text-align: center; color: #8b949e; font-size: 0.8rem; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>🦞 OpenClaw Calendar <span>{week_label}</span></h1>
    <p class="meta">顯示時區：Asia/Taipei ・ 更新時間：{now.strftime("%Y-%m-%d %H:%M")} CST</p>
    <div class="legend">{legend}</div>
    <div class="calendar">
      <table>
        <thead>
          <tr><th class="corner"></th>{day_headers}</tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    <footer>自動產生 by <a href="https://github.com/greg18jrr-ops/openclaw-calendar" style="color:#58a6ff">openclaw-calendar</a> ・ 🦞 OpenClaw</footer>
  </div>
</body>
</html>"""

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)

    with open(os.path.join(repo_root, "schedules", "jobs.json")) as f:
        jobs = json.load(f)

    week_days = get_week_range()
    html = generate_html(jobs, week_days)

    out_path = os.path.join(repo_root, "docs", "index.html")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(html)

    print(f"✅ Generated: {out_path}")

if __name__ == "__main__":
    main()
