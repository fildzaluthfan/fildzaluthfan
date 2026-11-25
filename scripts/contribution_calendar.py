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
end_longest = None
for day, _, count in days:
    streak = streak + 1 if count else 0
    if streak > longest:
        longest, end_longest = streak, day
cursor = today if today in active else today - timedelta(days=1)
current = 0
while cursor in active:
    current += 1
    cursor -= timedelta(days=1)

peak = max(count for _, _, count in days)
# Minimum-jerk interpolation starts and ends with zero velocity and acceleration.
samples = [i / 64 for i in range(65)]
ease = "linear(" + ",".join(f"{t**3 * (10 - 15*t + 6*t*t):.7f}" for t in samples) + ")"
parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="850" height="360" viewBox="0 0 850 360" role="img" aria-labelledby="title desc">
<title id="title">{calendar.heading}</title>
<desc id="desc">Each tile represents a day. Taller buildings indicate more contributions.</desc>
<style>
svg{{--ease:{ease};--bg:#fff;--ink:#24292f;--muted:#57606a;--line:#d0d7de;--l0:#ebedf0;--l1:#c6e48b;--l2:#7bc96f;--l3:#239a3b;--l4:#196127}}
@media(prefers-color-scheme:dark){{svg{{--bg:#0d1117;--ink:#e6edf3;--muted:#9198a1;--line:#30363d;--l0:#242b34;--l1:#0e4429;--l2:#006d32;--l3:#26a641;--l4:#39d353}}}}
text{{font:14px system-ui,sans-serif;fill:var(--muted)}}.value{{font-size:22px;font-weight:600;fill:var(--ink)}}
.corner-stats{{opacity:1}}.row-stats{{opacity:0}}
.value{{font-variant-numeric:tabular-nums}}
.grid{{transform:matrix(.93,.13,-.6,.62,86,119)}}
@media(prefers-reduced-motion:no-preference){{
.row-stats{{animation:row 7.2s var(--ease) both}}
.corner-stats{{animation:corners 7.2s var(--ease) both}}
@keyframes row{{0%{{opacity:1;transform:translateY(0)}}62%,100%{{opacity:0;transform:translateY(5px)}}}}
@keyframes corners{{0%,28%{{opacity:0;transform:translateY(var(--offset))}}94%,100%{{opacity:1;transform:translateY(0)}}}}
.grid{{animation:camera 7.2s var(--ease) both}}
@keyframes camera{{0%{{transform:matrix(1,0,0,1,28,114)}}100%{{transform:matrix(.93,.13,-.6,.62,86,119)}}}}
.face{{animation:rise 7.2s var(--ease) both;animation-delay:var(--delay)}}
@keyframes rise{{0%{{d:var(--flat)}}94%,100%{{d:var(--raised)}}}}
}}
</style>
<rect x=".5" y=".5" width="849" height="359" rx="16" fill="var(--bg)" stroke="var(--line)"/>
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
    parts.append(f'<g transform="translate({15 * week} {15 * row})" fill="var(--l{level})" style="--delay:{week * 8}ms">')
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
def span(end, length):
    if end is None or not length:
        return "—"
    start = end - timedelta(days=length - 1)
    return end.strftime("%b %d") if length == 1 else f"{start:%b %d} – {end:%b %d}"


details = [
    f"Jan 01 – {min(today, days[-1][0]):%b %d}",
    next((f"{day:%b %d}" for day, _, count in days if peak and count == peak), "—"),
    span(end_longest, longest),
    span(cursor + timedelta(days=current), current),
]
stats = [
    ("Year total", summary[1].replace("No", "0"), "contributions"),
    ("Busiest day", peak, "contribution" if peak == 1 else "contributions"),
    ("Longest streak", longest, "day" if longest == 1 else "days"),
    ("Current streak", current, "day" if current == 1 else "days"),
]


def stat(x, y, anchor, label, value, unit, detail):
    return (f'<g transform="translate({x} {y})" text-anchor="{anchor}"><text>{label}</text>'
            f'<text class="value" y="25">{value} <tspan font-size="13" font-weight="400">{unit}</tspan></text><text y="42" font-size="12">{detail}</text></g>')


parts.append('<g class="row-stats"><path d="M24 291H826" stroke="var(--line)"/>')
for x, data, detail in zip((25, 230, 435, 640), stats, details):
    parts.append(stat(x, 309, "start", *data, detail))
parts.append("</g>")
for x, y, anchor, offset, pair in [(825, 52, "end", "-5px", stats[:2]),
                                    (25, 248, "start", "5px", stats[2:])]:
    parts.append(f'<g class="corner-stats" style="--offset:{offset}">')
    for i, data in enumerate(pair):
        parts.append(stat(x, y + i * 58, anchor, *data, details[stats.index(data)]))
    parts.append("</g>")
parts.append("</svg>")
Path("assets/contribution-skyline.svg").write_text("\n".join(parts) + "\n")
