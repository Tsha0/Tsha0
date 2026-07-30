import datetime
import json
import os
import pathlib
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).parent
USER = "Tsha0"
WIDTH = 64
FONT = 14
CH = 8.55
LINE = 22
PAD = 24
CHROME = 44

BG = "#0b0e14"
BAR = "#111722"
EDGE = "#1e2634"
DIM = "#2c3648"
FG = "#cbd5e1"
CYAN = "#22d3ee"
PINK = "#ff79c6"
GREEN = "#3ddc84"
AMBER = "#ffb86c"

FIELDS = [
    ("os", "macOS · Linux · Web"),
    ("host", "Block · Cash App"),
    ("role", "SWE Intern @ Block · SE @ McGill"),
    ("tools", "Neovim · tmux · Claude Code · Ghostty"),
    ("code", "Python · TypeScript · Kotlin · Go · Java"),
    ("based", "Montréal, QC 🇨🇦"),
]
CONTACT = [
    ("github", f"@{USER}"),
    ("web", f"{USER.lower()}.github.io"),
]


def api(path, accept="application/vnd.github+json"):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={"Accept": accept, "User-Agent": f"{USER}-profile-card"},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def fetch():
    user = api(f"/users/{USER}")
    repos, page = [], 1
    while True:
        batch = api(f"/users/{USER}/repos?per_page=100&page={page}")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return {
        "created_at": user["created_at"],
        "repos": user["public_repos"],
        "followers": user["followers"],
        "stars": sum(r["stargazers_count"] for r in repos),
        "forks": sum(r["forks_count"] for r in repos),
        "prs": api(f"/search/issues?q=author:{USER}+type:pr&per_page=1")["total_count"],
        "commits": api(
            f"/search/commits?q=author:{USER}&per_page=1",
            accept="application/vnd.github.cloak-preview+json",
        )["total_count"],
    }


def stats():
    cache = HERE / "stats.json"
    try:
        fresh = fetch()
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, TimeoutError):
        return json.loads(cache.read_text())
    cache.write_text(json.dumps(fresh, indent=2) + "\n")
    return fresh


def uptime(created_at, today):
    born = datetime.date.fromisoformat(created_at[:10])
    years = today.year - born.year
    months = today.month - born.month
    if today.day < born.day:
        months -= 1
    if months < 0:
        years -= 1
        months += 12
    plural = lambda n, word: f"{n} {word}{'' if n == 1 else 's'}"
    return f"{plural(years, 'year')}, {plural(months, 'month')}"


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


GUTTER = "·      "  # leading spaces get trimmed in SVG text, so anchor with a glyph


def cell(label, value, width):
    dots = "." * max(1, width - len(label) - len(value) - 2)
    return [(label, CYAN), (f" {dots} ", DIM), (value, PINK)]


def field(label, value):
    return [("[ ok ] ", GREEN)] + cell(label, value, WIDTH - len(GUTTER))


def plain(label, value):
    return [(GUTTER, DIM)] + cell(label, value, WIDTH - len(GUTTER))


def pair(left, right):
    half = (WIDTH - len(GUTTER) - 3) // 2
    return (
        [(GUTTER, DIM)]
        + cell(*left, half)
        + [(" │ ", DIM)]
        + cell(*right, half)
    )


def command(text):
    return [("$ ", PINK), (text, FG)]


def build(today):
    data = stats()
    fields = [("uptime", uptime(data["created_at"], today))] + FIELDS
    num = lambda key: f"{data[key]:,}"

    lines = [command("boot --profile"), []]
    lines += [field(label, value) for label, value in fields]
    lines += [[], command("contact --list")]
    lines += [plain(label, value) for label, value in CONTACT]
    lines += [[], command("gh stats")]
    lines += [
        pair(("repos", num("repos")), ("stars", num("stars"))),
        pair(("commits", num("commits")), ("prs", num("prs"))),
        pair(("followers", num("followers")), ("forks", num("forks"))),
        [],
        [("ready.", GREEN)],
    ]

    width = round(WIDTH * CH) + PAD * 2
    height = CHROME + PAD + len(lines) * LINE + PAD - 6
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="Jason Shao — profile">',
        "<defs>",
        '<filter id="glow" x="-30%" y="-30%" width="160%" height="160%">',
        '<feGaussianBlur stdDeviation="1.6" result="b"/>',
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>',
        "</filter>",
        "</defs>",
        f'<rect width="{width}" height="{height}" rx="12" fill="{BG}" stroke="{EDGE}"/>',
        f'<path d="M0 12a12 12 0 0 1 12-12h{width - 24}a12 12 0 0 1 12 12v{CHROME - 12}H0z" fill="{BAR}"/>',
        f'<line x1="0" y1="{CHROME}" x2="{width}" y2="{CHROME}" stroke="{EDGE}"/>',
        '<circle cx="22" cy="22" r="6" fill="#ff5f57"/>',
        '<circle cx="42" cy="22" r="6" fill="#febc2e"/>',
        '<circle cx="62" cy="22" r="6" fill="#28c840"/>',
        f'<text x="{width / 2}" y="27" text-anchor="middle" font-size="12.5" fill="{AMBER}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'filter="url(#glow)">{USER.lower()}@github — zsh</text>',
        f'<g font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="{FONT}" xml:space="preserve">',
    ]

    y = CHROME + PAD + FONT
    for segments in lines:
        if segments:
            spans = "".join(f'<tspan fill="{c}">{esc(t)}</tspan>' for t, c in segments)
            out.append(f'<text x="{PAD}" y="{y}">{spans}</text>')
        y += LINE

    cursor_x = PAD + 7 * CH
    out.append(
        f'<rect x="{cursor_x:.1f}" y="{y - LINE - FONT + 2}" width="{CH:.1f}" height="{FONT + 2}" '
        f'fill="{GREEN}" filter="url(#glow)">'
        '<animate attributeName="opacity" values="1;1;0;0" dur="1.1s" repeatCount="indefinite"/>'
        "</rect>"
    )
    out += ["</g>", "</svg>"]
    (HERE / "card.svg").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    build(datetime.date.today())
