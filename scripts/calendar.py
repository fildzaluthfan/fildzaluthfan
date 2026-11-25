import json
import sys
from datetime import date
from pathlib import Path

calendar = json.load(sys.stdin)["weeks"]
colors = {
    "NONE": "#577161",
    "FIRST_QUARTILE": "#d9f2a6",
    "SECOND_QUARTILE": "#b4e84c",
    "THIRD_QUARTILE": "#8fc22f",
    "FOURTH_QUARTILE": "#5f8a14",
}
total = sum(day["contributionCount"] for week in calendar for day in week["contributionDays"])
width = 40 + 14 * len(calendar)
heading = f"{total} contributions in the last year"
parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 188" role="img" aria-labelledby="title">
<title id="title">{heading}</title>
<defs><linearGradient id="surface" x2="1" y2="1" gradientUnits="objectBoundingBox">
<stop stop-color="#526f58"/><stop offset="1" stop-color="#243f32"/></linearGradient></defs>
<style>
text {{ font-family: system-ui, sans-serif; fill: white }}
@media (prefers-reduced-motion: no-preference) {{
.day {{ transform-box: fill-box; transform-origin: center; animation: appear .2s ease-out backwards; animation-delay: var(--delay) }}
@keyframes appear {{ from {{ opacity: 0; transform: scale(.4) }} }}
}}
</style>
<rect width="{width}" height="188" rx="24" fill="url(#surface)"/>
<text x="20" y="34" font-size="18" font-weight="650">{heading}</text>''']
previous_month = None
for index, week in enumerate(calendar):
    days = week["contributionDays"]
    first = date.fromisoformat(days[0]["date"])
    x = 20 + 14 * index
    if first.month != previous_month and first.day <= 7 and index <= len(calendar) - 3:
        parts.append(f'<text x="{x}" y="61" font-size="11">{first:%b}</text>')
    previous_month = first.month
    parts.append(f'<g style="--delay:{12 * index}ms">')
    for day in days:
        row = (date.fromisoformat(day["date"]).weekday() + 1) % 7
        color = colors[day["contributionLevel"]]
        parts.append(f'<rect class="day" x="{x}" y="{72 + 14 * row}" width="11" height="11" rx="3" fill="{color}"/>')
    parts.append("</g>")
parts.append("</svg>")
Path("assets/activity.svg").write_text("\n".join(parts) + "\n")
