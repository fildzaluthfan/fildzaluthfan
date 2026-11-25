import json
import sys
from datetime import date
from pathlib import Path

calendar = json.load(sys.stdin)
weeks = calendar["weeks"]
colors = {
    "NONE": "#161b22",
    "FIRST_QUARTILE": "#033a16",
    "SECOND_QUARTILE": "#196c2e",
    "THIRD_QUARTILE": "#2ea043",
    "FOURTH_QUARTILE": "#56d364",
}
width = 56 + 13 * len(weeks)
heading = f'{calendar["totalContributions"]:,} contributions in the last year'
parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="200" viewBox="0 0 {width} 200" role="img" aria-labelledby="title">
<title id="title">{heading}</title>
<style>
text {{ font: 12px system-ui, sans-serif; fill: #f0f6fc }}
.heading {{ font-size: 16px }}
.muted {{ fill: #9198a1 }}
@media (prefers-reduced-motion: no-preference) {{
.day {{ transform-box: fill-box; transform-origin: center; animation: appear .2s ease-out backwards; animation-delay: var(--delay) }}
@keyframes appear {{ from {{ opacity: 0; transform: scale(.4) }} }}
}}
</style>
<rect width="{width}" height="200" rx="6" fill="#0d1117"/>
<text class="heading" x="1" y="18">{heading}</text>
<rect x=".5" y="32.5" width="{width - 1}" height="167" rx="6" fill="none" stroke="#3d444d"/>''']
for row, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
    parts.append(f'<text x="12" y="{76 + 13 * row}">{label}</text>')

last_month = None
for index, week in enumerate(weeks):
    days = week["contributionDays"]
    first = date.fromisoformat(days[0]["date"])
    x = 46 + 13 * index
    if first.month != last_month and index <= len(weeks) - 2:
        # Skip a one-column opening month to leave room for the next label.
        if index or len(weeks) == 1 or weeks[1]["contributionDays"][0]["date"][5:7] == first.strftime("%m"):
            parts.append(f'<text x="{x}" y="60">{first:%b}</text>')
    last_month = first.month
    parts.append(f'<g style="--delay:{12 * index}ms">')
    for day in days:
        row = (date.fromisoformat(day["date"]).weekday() + 1) % 7
        color = colors[day["contributionLevel"]]
        parts.append(f'<rect class="day" x="{x}" y="{66 + 13 * row}" width="10" height="10" rx="2" fill="{color}"/>')
    parts.append("</g>")

legend_x = width - 137
parts.append(f'<text class="muted" x="{legend_x - 5}" y="182" text-anchor="end">Less</text>')
for index, color in enumerate(colors.values()):
    parts.append(f'<rect x="{legend_x + 14 * index}" y="172" width="10" height="10" rx="2" fill="{color}"/>')
parts.append(f'<text class="muted" x="{legend_x + 70}" y="182">More</text>')
parts.append("</svg>")
Path("assets/contribution-calendar.svg").write_text("\n".join(parts) + "\n")
