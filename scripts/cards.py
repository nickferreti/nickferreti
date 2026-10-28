"""Render the profile stats and languages cards with private contributions.

The public github-readme-stats instance only sees public repositories, so this
script asks the API with the owner's token and draws cards in the same style.

Usage: GH_TOKEN=... python scripts/cards.py <login> <output-dir>
"""

import json
import math
import os
import sys
import urllib.request
from datetime import date
from html import escape
from pathlib import Path

API = "https://api.github.com"

THEMES = {
    "dark": {"bg": "#0D1117", "title": "#818CF8", "icon": "#06B6D4", "text": "#C9D1D9", "ring": "#4F46E5"},
    "light": {"bg": "#FFFEFE", "title": "#4F46E5", "icon": "#0891B2", "text": "#434D58", "ring": "#4F46E5"},
}

ICONS = {
    "commit": "M11.93 8.5a4.002 4.002 0 0 1-7.86 0H.75a.75.75 0 0 1 0-1.5h3.32a4.002 4.002 0 0 1 7.86 0h3.32a.75.75 0 0 1 0 1.5Zm-1.43-.75a2.5 2.5 0 1 0-5 0 2.5 2.5 0 0 0 5 0Z",
    "pr": "M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.25 2.25 0 0 1 1.5 3.25Zm5.677-.177L9.573.677A.25.25 0 0 1 10 .854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 0 0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 0-.354ZM3.75 2.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm0 9.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm8.25.75a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0Z",
    "merge": "M5.45 5.154A4.25 4.25 0 0 0 9.25 7.5h1.378a2.251 2.251 0 1 1 0 1.5H9.25A5.734 5.734 0 0 1 5 7.123v3.505a2.25 2.25 0 1 1-1.5 0V5.372a2.25 2.25 0 1 1 1.95-.218ZM4.25 13.5a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm8.5-4.5a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5ZM5 3.25a.75.75 0 1 0 0 .005V3.25Z",
    "review": "M1.75 1h12.5c.966 0 1.75.784 1.75 1.75v8.5A1.75 1.75 0 0 1 14.25 13H8.061l-2.574 2.573A1.458 1.458 0 0 1 3 14.543V13H1.75A1.75 1.75 0 0 1 0 11.25v-8.5C0 1.784.784 1 1.75 1ZM1.5 2.75v8.5c0 .138.112.25.25.25h2a.75.75 0 0 1 .75.75v2.19l2.72-2.72a.749.749 0 0 1 .53-.22h6.5a.25.25 0 0 0 .25-.25v-8.5a.25.25 0 0 0-.25-.25H1.75a.25.25 0 0 0-.25.25Zm5.28 1.72a.75.75 0 0 1 0 1.06L5.31 7l1.47 1.47a.751.751 0 0 1-.018 1.042.751.751 0 0 1-1.042.018l-2-2a.75.75 0 0 1 0-1.06l2-2a.75.75 0 0 1 1.06 0Zm2.44 0a.75.75 0 0 1 1.06 0l2 2a.75.75 0 0 1 0 1.06l-2 2a.751.751 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042L10.69 7 9.22 5.53a.75.75 0 0 1 0-1.06Z",
    "flame": "M9.533.753V.752c.217 2.385 1.463 3.626 2.653 4.81C13.37 6.74 14.498 7.863 14.498 10c0 3.5-3 6-6.5 6S1.5 13.512 1.5 10c0-1.298.536-2.56 1.425-3.286.376-.308.862 0 1.035.454C4.46 8.487 5.581 8.419 6 8c.282-.282.341-.811-.003-1.5C4.34 3.187 7.035.75 8.77.146c.39-.137.726.194.763.607ZM7.998 14.5c2.832 0 5-1.98 5-4.5 0-1.463-.68-2.19-1.879-3.383l-.036-.037c-1.013-1.008-2.3-2.29-2.834-4.434-.322.256-.63.579-.864.953-.432.696-.621 1.58-.046 2.73.473.947.67 2.284-.278 3.232-.61.61-1.545.84-2.403.633a2.79 2.79 0 0 1-1.436-.874A3.198 3.198 0 0 0 3 10c0 2.53 2.164 4.5 4.998 4.5Z",
    "repo": "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z",
}

# Linguist colors for the languages likely to show up; anything else is grey.
LANGUAGE_COLORS = {
    "Python": "#3572A5",
    "TypeScript": "#3178C6",
    "JavaScript": "#F1E05A",
    "Vue": "#41B883",
    "PHP": "#4F5D95",
    "Blade": "#F7523F",
    "Java": "#B07219",
    "Kotlin": "#A97BFF",
    "Dart": "#00B4AB",
    "Go": "#00ADD8",
    "C#": "#178600",
    "C++": "#F34B7D",
    "C": "#555555",
    "Svelte": "#FF3E00",
    "MDX": "#FCB32C",
}

# Markup, config and generated code would bury the languages actually written.
IGNORED_LANGUAGES = {
    "HTML", "CSS", "SCSS", "Less", "Jupyter Notebook", "Shell", "Dockerfile",
    "Makefile", "PLpgSQL", "Just", "Procfile", "Batchfile", "PowerShell", "Mako",
}

# Vendored upstream code: its bytes are not the owner's languages.
EXCLUDED_REPOS = {"VendeAI/chatwoot"}

FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Sans-Serif"


def request(path, body=None):
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(body).encode() if body else None,
        headers={
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-cards",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def search_count(kind, query):
    return request(f"/search/{kind}?q={query}&per_page=1")["total_count"]


def graphql(query, **variables):
    data = request("/graphql", {"query": query, "variables": variables})
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    return data["data"]


def fetch_stats(login):
    year_start = f"{date.today().year}-01-01T00:00:00Z"
    user = graphql(
        """
        query($login: String!, $from: DateTime!) {
          user(login: $login) {
            name
            followers { totalCount }
            repositoriesContributedTo(first: 1, includeUserRepositories: true,
              contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]) { totalCount }
            repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
              nodes { stargazerCount }
            }
            contributionsCollection(from: $from) {
              contributionCalendar { totalContributions }
            }
          }
        }
        """,
        login=login,
        **{"from": year_start},
    )["user"]
    return {
        "name": user["name"] or login,
        "commits": search_count("commits", f"author:{login}"),
        "prs": search_count("issues", f"is:pr+author:{login}"),
        "merged": search_count("issues", f"is:pr+author:{login}+is:merged"),
        "reviews": search_count("issues", f"is:pr+reviewed-by:{login}+-author:{login}"),
        "issues": search_count("issues", f"is:issue+author:{login}"),
        "stars": sum(repo["stargazerCount"] for repo in user["repositories"]["nodes"]),
        "followers": user["followers"]["totalCount"],
        "contributed_to": user["repositoriesContributedTo"]["totalCount"],
        "year_contributions": user["contributionsCollection"]["contributionCalendar"]["totalContributions"],
    }


def fetch_languages(login):
    """Bytes per language over owned repos plus organization repos contributed to."""
    data = graphql(
        """
        query($login: String!) {
          user(login: $login) {
            repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
              nodes { nameWithOwner }
            }
            repositoriesContributedTo(first: 100, includeUserRepositories: false,
              contributionTypes: [COMMIT, PULL_REQUEST]) {
              nodes { nameWithOwner owner { __typename } }
            }
          }
        }
        """,
        login=login,
    )["user"]
    repos = {repo["nameWithOwner"] for repo in data["repositories"]["nodes"]}
    repos |= {
        repo["nameWithOwner"]
        for repo in data["repositoriesContributedTo"]["nodes"]
        if repo["owner"]["__typename"] == "Organization"
    }
    totals = {}
    for repo in sorted(repos - EXCLUDED_REPOS):
        for language, size in request(f"/repos/{repo}/languages").items():
            if language not in IGNORED_LANGUAGES:
                totals[language] = totals.get(language, 0) + size
    return sorted(totals.items(), key=lambda item: item[1], reverse=True)


def rank(stats):
    """Same weights and medians as github-readme-stats with all commits counted."""

    def exponential_cdf(x):
        return 1 - 2 ** -x

    def log_normal_cdf(x):
        return x / (1 + x)

    weighted = [
        (2, exponential_cdf(stats["commits"] / 1000)),
        (3, exponential_cdf(stats["prs"] / 50)),
        (1, exponential_cdf(stats["issues"] / 25)),
        (1, exponential_cdf(stats["reviews"] / 2)),
        (4, log_normal_cdf(stats["stars"] / 50)),
        (1, log_normal_cdf(stats["followers"] / 10)),
    ]
    percentile = (1 - sum(w * v for w, v in weighted) / sum(w for w, _ in weighted)) * 100
    for threshold, level in zip(
        [1, 12.5, 25, 37.5, 50, 62.5, 75, 87.5, 100],
        ["S", "A+", "A", "A-", "B+", "B", "B-", "C+", "C"],
    ):
        if percentile <= threshold:
            return level, percentile
    return "C", percentile


def card(width, height, title, body, theme, extra_css=""):
    colors = THEMES[theme]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" role="img" aria-labelledby="title">
  <title id="title">{escape(title)}</title>
  <style>
    .header {{ font: 600 18px {FONT}; fill: {colors["title"]}; animation: fadeIn 0.8s ease-in-out forwards; }}
    .stat {{ font: 600 14px {FONT}; fill: {colors["text"]}; }}
    .bold {{ font-weight: 700; }}
    .icon {{ fill: {colors["icon"]}; }}
    .lang {{ font: 600 13px {FONT}; fill: {colors["text"]}; }}
    .stagger {{ opacity: 0; animation: fadeIn 0.3s ease-in-out forwards; }}
    @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation-duration: 0s !important; animation-delay: 0s !important; }} }}
    {extra_css}
  </style>
  <rect x="0.5" y="0.5" rx="4.5" width="{width - 1}" height="{height - 1}" fill="{colors["bg"]}" />
  <text x="25" y="35" class="header">{escape(title)}</text>
{body}
</svg>
"""


def stats_card(stats, theme):
    colors = THEMES[theme]
    year = date.today().year
    rows = [
        ("commit", "Total Commits", stats["commits"]),
        ("pr", "Pull Requests Opened", stats["prs"]),
        ("merge", "Pull Requests Merged", stats["merged"]),
        ("review", "Pull Requests Reviewed", stats["reviews"]),
        ("flame", f"Contributions in {year}", stats["year_contributions"]),
        ("repo", "Contributed To", stats["contributed_to"]),
    ]
    lines = []
    for index, (icon, label, value) in enumerate(rows):
        y = 70 + index * 25
        lines.append(
            f'  <g class="stagger" style="animation-delay: {450 + index * 150}ms" transform="translate(25, {y})">\n'
            f'    <svg class="icon" viewBox="0 0 16 16" width="16" height="16" y="-12.5"><path fill-rule="evenodd" d="{ICONS[icon]}" /></svg>\n'
            f'    <text class="stat" x="25">{label}:</text>\n'
            f'    <text class="stat bold" x="230">{value:,}</text>\n'
            "  </g>"
        )
    level, percentile = rank(stats)
    radius = 40
    circumference = 2 * math.pi * radius
    offset = circumference * percentile / 100
    ring = f"""  <g transform="translate(395, 125)">
    <circle r="{radius}" stroke="{colors["ring"]}" stroke-opacity="0.2" stroke-width="6" />
    <circle class="ring" r="{radius}" stroke="{colors["ring"]}" stroke-width="6" stroke-linecap="round"
      stroke-dasharray="{circumference:.2f}" stroke-dashoffset="{circumference:.2f}" transform="rotate(-90)" />
    <text class="rank" text-anchor="middle" dominant-baseline="central">{level}</text>
  </g>"""
    css = (
        f".rank {{ font: 800 24px {FONT}; fill: {colors['text']}; opacity: 0; animation: fadeIn 0.3s 0.6s ease-in-out forwards; }}\n"
        f"    .ring {{ animation: ring 1s ease forwards; }}\n"
        f"    @keyframes ring {{ to {{ stroke-dashoffset: {offset:.2f}; }} }}"
    )
    body = "\n".join(lines) + "\n" + ring
    return card(467, 220, f"{stats['name']}'s GitHub Stats", body, theme, css)


def languages_card(languages, theme, limit=6):
    colors = THEMES[theme]
    top = languages[:limit]
    total = sum(size for _, size in top) or 1
    rows = []
    for index, (language, size) in enumerate(top):
        share = 100 * size / total
        color = LANGUAGE_COLORS.get(language, "#858585")
        rows.append(
            f'  <g class="stagger" style="animation-delay: {450 + index * 150}ms" transform="translate(25, {55 + index * 40})">\n'
            f'    <text class="lang" y="12">{escape(language)}</text>\n'
            f'    <text class="lang" x="300" y="12" text-anchor="end">{share:.2f}%</text>\n'
            f'    <rect y="20" rx="4" width="275" height="8" fill="{colors["ring"]}" fill-opacity="0.15" />\n'
            f'    <svg class="grow" y="20" width="{max(275 * share / 100, 8):.2f}" height="8"><rect rx="4" width="100%" height="8" fill="{color}" /></svg>\n'
            "  </g>"
        )
    css = (
        ".grow { animation: grow 0.6s ease-in-out forwards; }\n"
        "    @keyframes grow { from { width: 0; } }"
    )
    return card(350, 65 + len(top) * 40, "Most Used Languages", "\n".join(rows), theme, css)


def main():
    login, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    stats = fetch_stats(login)
    languages = fetch_languages(login)
    for theme in THEMES:
        (out / f"stats-{theme}.svg").write_text(stats_card(stats, theme))
        (out / f"langs-{theme}.svg").write_text(languages_card(languages, theme))
    print(json.dumps({"stats": stats, "rank": rank(stats), "languages": languages[:6]}, indent=2))


if __name__ == "__main__":
    main()
