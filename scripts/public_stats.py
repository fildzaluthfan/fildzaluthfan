import json
import sys
from pathlib import Path
from subprocess import check_output
from urllib.parse import urlencode

owner = sys.argv[1]


def github(path, *options):
    return json.loads(check_output(["gh", "api", path, *options]))


def count_search(resource, query):
    params = urlencode({"q": query, "per_page": 1})
    result = github(f"search/{resource}?{params}")
    if result["incomplete_results"]:
        raise ValueError(f"Incomplete results for {query}")
    return result["total_count"]


pages = github(f"users/{owner}/repos?type=owner&per_page=100", "--paginate", "--slurp")
stars = sum(repo["stargazers_count"] for page in pages for repo in page if not repo["fork"])
rows = [
    ("Stars earned", stars),
    ("Public commits indexed by GitHub", count_search("commits", f"author:{owner}")),
    ("Public pull requests opened", count_search("issues", f"is:pr author:{owner}")),
    ("Public issues opened", count_search("issues", f"is:issue author:{owner}")),
]
parts = ['''<svg xmlns="http://www.w3.org/2000/svg" width="445" height="182" viewBox="0 0 445 182" role="img" aria-labelledby="title">
<title id="title">GitHub Pulse</title>
<style>text{font:14px system-ui,sans-serif;fill:#57606a}.title{font-size:19px;font-weight:600;fill:#0969da}@media(prefers-color-scheme:dark){text{fill:#c9d1d9}.title{fill:#58a6ff}}</style>
<rect x=".5" y=".5" width="444" height="181" rx="6" fill="none" stroke="#8c959f"/>
<text class="title" x="22" y="32">GitHub Pulse</text>''']
for index, (label, total) in enumerate(rows):
    y = 64 + index * 30
    parts.append(f'<text x="22" y="{y}">{label}</text><text x="422" y="{y}" text-anchor="end">{total:,}</text>')
parts.append("</svg>")
Path("dist/github-stats.svg").write_text("\n".join(parts) + "\n")
