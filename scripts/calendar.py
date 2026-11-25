import math
import re
import sys
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.counts = {}
        self.capture = None
        self.text = []
        self.heading = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and "data-date" in attrs:
            self.cells[attrs["id"]] = (date.fromisoformat(attrs["data-date"]), int(attrs["data-level"]))
        if tag == "h2" and attrs.get("id") == "js-contribution-activity-description":
            self.capture = "heading"
        elif tag == "tool-tip" and attrs.get("for", "").startswith("contribution-day"):
            self.capture = attrs["for"]
        else:
            return
        self.text = []

    def handle_data(self, data):
        if self.capture:
            self.text.append(data)

    def handle_endtag(self, tag):
        if self.capture and tag in ("h2", "tool-tip"):
            text = " ".join("".join(self.text).split())
            if self.capture == "heading":
                self.heading = text
            else:
                match = re.match(r"(No|[\d,]+) contributions? on ", text)
                if match:
                    self.counts[self.capture] = int(match[1].replace(",", "")) if match[1] != "No" else 0
            self.capture = None


calendar = CalendarParser()
calendar.feed(sys.stdin.read())
summary = re.fullmatch(r"(No|[\d,]+) contributions? in (\d{4})", calendar.heading)
days = sorted((day, level, calendar.counts[key]) for key, (day, level) in calendar.cells.items())
if not summary or len(days) < 365 or sum(d[2] for d in days) != int(summary[1].replace(",", "").replace("No", "0")):
    raise ValueError("Incomplete calendar or inconsistent daily contribution counts")

today = datetime.now(ZoneInfo("Asia/Jakarta")).date()
active = {day for day, _, count in days if count}
longest = streak = 0
for day, _, count in days:
    streak = streak + 1 if count else 0
    longest = max(longest, streak)
cursor = today if today in active else today - timedelta(days=1)
current = 0
while cursor in active:
    current += 1
    cursor -= timedelta(days=1)

peak = max(count for _, _, count in days)
parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="850" height="360" viewBox="0 0 850 360" role="img" aria-labelledby="title desc">
<title id="title">Contribution Skyline · {calendar.heading}</title>
<desc id="desc">Each tile represents a day. Taller buildings indicate more contributions.</desc>
<style>
svg{{--bg:#fff;--ink:#24292f;--muted:#57606a;--line:#d0d7de;--l0:#ebedf0;--l1:#c6e48b;--l2:#7bc96f;--l3:#239a3b;--l4:#196127}}
@media(prefers-color-scheme:dark){{svg{{--bg:#0d1117;--ink:#e6edf3;--muted:#9198a1;--line:#30363d;--l0:#242b34;--l1:#0e4429;--l2:#006d32;--l3:#26a641;--l4:#39d353}}}}
text{{font:14px system-ui,sans-serif;fill:var(--muted)}}.headline{{font-size:22px;font-weight:650;fill:var(--ink)}}.value{{font-size:22px;font-weight:600;fill:var(--ink)}}
.corner-stats{{opacity:1}}.row-stats{{opacity:0}}
.value{{font-variant-numeric:tabular-nums}}
.grid{{transform:matrix(.93,.13,-.6,.62,86,119)}}
@media(prefers-reduced-motion:no-preference){{
.row-stats{{animation:row 12s ease-in-out infinite}}
.corner-stats{{animation:corners 12s ease-in-out infinite}}
@keyframes row{{0%,13%,96%,100%{{opacity:1;transform:translateY(0)}}27%,81%{{opacity:0;transform:translateY(9px)}}}}
@keyframes corners{{0%,24%,88%,100%{{opacity:0;transform:translateY(var(--offset))}}40%,73%{{opacity:1;transform:translateY(0)}}}}
.grid{{animation:camera 12s ease-in-out infinite}}
@keyframes camera{{0%,12%,100%{{transform:matrix(1,0,0,1,28,114)}}38%,74%{{transform:matrix(.93,.13,-.6,.62,86,119)}}}}
.face{{animation:rise 12s ease-in-out infinite;animation-delay:var(--delay)}}
@keyframes rise{{0%,13%,96%,100%{{d:var(--flat)}}40%,73%{{d:var(--raised)}}}}
}}
</style>
<rect x=".5" y=".5" width="849" height="359" rx="16" fill="var(--bg)" stroke="var(--line)"/>
<text class="headline" x="25" y="35">Contribution Skyline</text>
<text x="825" y="34" text-anchor="end">{summary[2]}</text>
<g class="grid">''']


def path(points):
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in points) + " Z"


first = days[0][0]
sunday = first - timedelta(days=(first.weekday() + 1) % 7)
for day, level, count in days:
    week, row = divmod((day - sunday).days, 7)
    base = [(0, 0), (12, 0), (12, 12), (0, 12)]
    height = 53 * math.log1p(count) / math.log1p(peak) if peak else 0
    # Inverse camera projection of a vertical screen displacement.
    top = [(x - .6 * height / .6546, y - .93 * height / .6546) for x, y in base]
    parts.append(f'<g transform="translate({15 * week} {15 * row})" fill="var(--l{level})" style="--delay:{week * 12}ms">')
    faces = [(base, top, "")]
    if count:
        for a, b, brightness in [(1, 2, ".66"), (2, 3, ".82")]:
            faces.append(([base[a], base[b], base[b], base[a]], [top[a], top[b], base[b], base[a]], f' filter="brightness({brightness})"'))
    for flat, raised, shade in faces:
        end = path(raised)
        if count:
            parts.append(f'<path class="face" d="{end}" style="--flat:path(\'{path(flat)}\');--raised:path(\'{end}\')"{shade}/>')
        else:
            parts.append(f'<path d="{end}"/>')
    parts.append("</g>")
parts.append("</g>")
stats = [
    ("Year total", summary[1].replace("No", "0"), "contributions"),
    ("Busiest day", peak, "contribution" if peak == 1 else "contributions"),
    ("Longest streak", longest, "day" if longest == 1 else "days"),
    ("Current streak", current, "day" if current == 1 else "days"),
]


def stat(x, y, anchor, label, value, unit):
    return (f'<g transform="translate({x} {y})" text-anchor="{anchor}"><text>{label}</text>'
            f'<text class="value" y="25">{value} <tspan font-size="13" font-weight="400">{unit}</tspan></text></g>')


parts.append('<g class="row-stats"><path d="M24 291H826" stroke="var(--line)"/>')
for x, data in zip((25, 230, 435, 640), stats):
    parts.append(stat(x, 314, "start", *data))
parts.append("</g>")
for x, y, anchor, offset, pair in [(825, 60, "end", "-10px", stats[:2]),
                                    (25, 260, "start", "10px", stats[2:])]:
    parts.append(f'<g class="corner-stats" style="--offset:{offset}">')
    for i, data in enumerate(pair):
        parts.append(stat(x, y + i * 53, anchor, *data))
    parts.append("</g>")
parts.append("</svg>")
Path("assets/contribution-skyline.svg").write_text("\n".join(parts) + "\n")
