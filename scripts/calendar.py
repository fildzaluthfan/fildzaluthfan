import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}
        self.heading = []
        self.in_heading = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h2" and attrs.get("id") == "js-contribution-activity-description":
            self.in_heading = True
        if tag == "td" and "data-date" in attrs and "data-level" in attrs:
            self.days[date.fromisoformat(attrs["data-date"])] = int(attrs["data-level"])

    def handle_endtag(self, tag):
        if tag == "h2":
            self.in_heading = False

    def handle_data(self, data):
        if self.in_heading:
            self.heading.append(data)


calendar = CalendarParser()
calendar.feed(sys.stdin.read())
heading = " ".join("".join(calendar.heading).split())
if not re.fullmatch(r"(?:[\d,]+|No) contributions? in \d{4}", heading) or len(calendar.days) < 365:
    raise ValueError("Incomplete GitHub contribution calendar")
colors = ["#577161", "#d9f2a6", "#b4e84c", "#8fc22f", "#5f8a14"]
weeks = []
for day in sorted(calendar.days):
    if not weeks or day.weekday() == 6:
        weeks.append([])
    weeks[-1].append(day)
width = 40 + 14 * len(weeks)
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
for index, days in enumerate(weeks):
    first = days[0]
    x = 20 + 14 * index
    if first.month != previous_month and first.day <= 7 and index <= len(weeks) - 3:
        parts.append(f'<text x="{x}" y="61" font-size="11">{first:%b}</text>')
    previous_month = first.month
    parts.append(f'<g style="--delay:{12 * index}ms">')
    for day in days:
        row = (day.weekday() + 1) % 7
        color = colors[calendar.days[day]]
        parts.append(f'<rect class="day" x="{x}" y="{72 + 14 * row}" width="11" height="11" rx="3" fill="{color}"/>')
    parts.append("</g>")
parts.append("</svg>")
Path("assets/activity-calendar.svg").write_text("\n".join(parts) + "\n")
