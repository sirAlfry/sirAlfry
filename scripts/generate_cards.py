#!/usr/bin/env python3
"""
Genera in locale le card SVG del profilo (repo "pinnati" + linguaggi più usati)
al posto dell'istanza pubblica di github-readme-stats, che è in pausa.

Usa solo la libreria standard di Python e l'API REST di GitHub.
- In GitHub Actions legge il token da GITHUB_TOKEN (limite 1000 richieste/ora).
- In locale funziona anche senza token (limite 60 richieste/ora: bastano).

Uso:  python scripts/generate_cards.py
Output: assets/cards/pin-<repo>.svg  e  assets/cards/top-langs.svg
"""
from __future__ import annotations

import json
import os
import sys
import textwrap
import urllib.request
from html import escape
from pathlib import Path

# ----------------------------------------------------------------- configurazione
USERNAME = os.environ.get("CARDS_USER", "sirAlfry")

PINNED = [
    "retro-arcade-collection-phaser",
    "Japanese-Garden",
    "retro-arcade-collection",
    "Inventory",
    "retro-arcade-collection-unity",
    "il-prezzo-invisibile-del-prompt",
    "dehazing-project",
    "astar-to-wumpus",
]

# Descrizioni usate quando il repository non ne ha una impostata su GitHub
# (quella di GitHub, se presente, ha sempre la precedenza).
DESCRIPTIONS = {
    "retro-arcade-collection-phaser": "9 classici arcade in un launcher synthwave, AI Minimax imbattibile, PWA giocabile offline",
    "Japanese-Garden": "Giardino low poly del periodo Edo esplorabile in prima persona",
    "retro-arcade-collection": "L'edizione originale desktop in Pygame, con motore AI condiviso e test",
    "Inventory": "Inventario in prima persona con drag & drop e item come ScriptableObject",
    "retro-arcade-collection-unity": "La collezione Retro Arcade portata in Unity",
    "il-prezzo-invisibile-del-prompt": "Opera audiovisiva interattiva sull'impatto ambientale dell'IA",
    "dehazing-project": "Rimozione della nebbia da una singola foto con Dark Channel Prior e Guided Filter",
    "astar-to-wumpus": "A* e IDA* in Prolog, ASP con Clingo e agenti CLIPS per il mondo del Wumpus",
}

# Linguaggi "di contorno" che gonfierebbero la classifica (shader importati da
# Unity, file di progetto, markup...). Togli una voce se vuoi vederla comparire.
EXCLUDE_LANGS = {"ShaderLab", "HLSL", "GLSL", "Mathematica", "Wolfram Language", "Batchfile", "Dockerfile", "Makefile"}
LANGS_COUNT = 8

# Tema "radical" (stessi colori della card originale)
BG, TITLE, TEXT, ICON = "#141321", "#fe428e", "#a9fef7", "#f8d847"
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Sans-Serif"

# Colori ufficiali GitHub Linguist (sottoinsieme); gli altri ricevono un grigio
LANG_COLORS = {
    "C#": "#178600", "C": "#555555", "C++": "#f34b7d", "Python": "#3572A5",
    "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "HTML": "#e34c26",
    "CSS": "#663399", "Processing": "#0096D8", "Prolog": "#74283c",
    "CLIPS": "#00A300", "Answer Set Programming": "#A9CC29", "ShaderLab": "#222c37",
    "HLSL": "#aace60", "GLSL": "#5686a5", "Java": "#b07219", "Shell": "#89e051",
    "PowerShell": "#012456", "Dockerfile": "#384d54", "Jupyter Notebook": "#DA5B0B",
    "TeX": "#3D6117", "Go": "#00ADD8", "Rust": "#dea584", "Lua": "#000080",
    "Visual Basic .NET": "#945db7", "xBase": "#403a40", "Razor": "#512be4",
    "SCSS": "#c6538c", "Vue": "#41b883", "PHP": "#4F5D95", "Kotlin": "#A97BFF",
    "Mathematica": "#dd1100", "Batchfile": "#C1F12E", "Makefile": "#427819",
}

OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "cards"


# ----------------------------------------------------------------- API GitHub
def api(path: str):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "profile-cards-generator")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


# ----------------------------------------------------------------- SVG helpers
REPO_ICON = ('<path fill-rule="evenodd" d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 '
             '110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 '
             '.208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 '
             '00-.25-.25h-3.5a.25.25 0 00-.25.25z"/>')
STAR_ICON = ('<path fill-rule="evenodd" d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 '
             '4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"/>')
FORK_ICON = ('<path fill-rule="evenodd" d="M5 3.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm0 2.122a2.25 2.25 0 10-1.5 0v.878A2.25 2.25 0 '
             '005.75 8.5h1.5v2.128a2.251 2.251 0 101.5 0V8.5h1.5a2.25 2.25 0 002.25-2.25v-.878a2.25 2.25 0 10-1.5 0v.878a.75.75 0 '
             '01-.75.75h-4.5A.75.75 0 015 6.25v-.878zm3.75 7.378a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm3-8.75a.75.75 0 100-1.5.75.75 0 000 1.5z"/>')


def card(width: int, height: int, body: str, label: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">
  <title>{escape(label)}</title>
  <style>
    .title {{ font: 600 18px {FONT}; fill: {TITLE}; }}
    .desc  {{ font: 400 13px {FONT}; fill: {TEXT}; }}
    .stat  {{ font: 600 14px {FONT}; fill: {TEXT}; }}
    .lang  {{ font: 400 11px {FONT}; fill: {TEXT}; }}
    .icon  {{ fill: {ICON}; }}
  </style>
  <rect x="0.5" y="0.5" rx="4.5" width="{width - 1}" height="{height - 1}" fill="{BG}"/>
{body}
</svg>
"""


def human(n: int) -> str:
    return f"{n / 1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def pin_card(repo: dict) -> str:
    name = repo["name"]
    desc = repo.get("description") or "Nessuna descrizione"
    lines = textwrap.wrap(desc, 55)[:3]
    if len(textwrap.wrap(desc, 55)) > 3:
        lines[-1] = lines[-1][:52].rstrip() + "…"
    height = 105 + max(2, len(lines)) * 18  # minimo 2 righe: griglia uniforme

    body = [f'  <g transform="translate(25,35)"><svg class="icon" x="0" y="-13" width="16" height="16" viewBox="0 0 16 16">{REPO_ICON}</svg>',
            f'    <text class="title" x="25" y="0">{escape(name)}</text></g>']
    body.append('  <text class="desc" x="25" y="65">' + "".join(
        f'<tspan x="25" dy="{0 if i == 0 else "1.35em"}">{escape(l)}</tspan>' for i, l in enumerate(lines)) + "</text>")

    y = height - 18
    x = 25
    stats = []
    lang = repo.get("language")
    if lang:
        color = LANG_COLORS.get(lang, "#858585")
        stats.append(f'<circle cx="{x + 6}" cy="-5" r="6" fill="{color}"/><text class="stat" x="{x + 18}" y="0">{escape(lang)}</text>')
        x += 18 + int(len(lang) * 8.2) + 20
    stats.append(f'<svg class="icon" x="{x}" y="-16" width="16" height="16" viewBox="0 0 16 16">{STAR_ICON}</svg>'
                 f'<text class="stat" x="{x + 22}" y="0">{human(repo["stargazers_count"])}</text>')
    x += 22 + len(human(repo["stargazers_count"])) * 9 + 20
    stats.append(f'<svg class="icon" x="{x}" y="-16" width="16" height="16" viewBox="0 0 16 16">{FORK_ICON}</svg>'
                 f'<text class="stat" x="{x + 22}" y="0">{human(repo["forks_count"])}</text>')
    body.append(f'  <g transform="translate(0,{y})">' + "".join(stats) + "</g>")
    return card(400, height, "\n".join(body), f"{name}: {desc}")


def top_langs_card(totals: dict[str, int]) -> str:
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:LANGS_COUNT]
    total = sum(v for _, v in ranked) or 1
    width, bar_w = 400, 350
    rows = (len(ranked) + 1) // 2
    height = 90 + rows * 25

    body = ['  <text class="title" x="25" y="35">Linguaggi più usati</text>',
            '  <mask id="bar"><rect x="25" y="55" width="350" height="8" rx="5" fill="#fff"/></mask>',
            '  <g mask="url(#bar)">']
    x = 25.0
    for lang, val in ranked:
        w = bar_w * val / total
        body.append(f'    <rect x="{x:.2f}" y="55" width="{w + 0.5:.2f}" height="8" fill="{LANG_COLORS.get(lang, "#858585")}"/>')
        x += w
    body.append("  </g>")
    for i, (lang, val) in enumerate(ranked):
        cx = 25 + (i % 2) * 175
        cy = 90 + (i // 2) * 25
        body.append(f'  <circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{LANG_COLORS.get(lang, "#858585")}"/>'
                    f'<text class="lang" x="{cx + 15}" y="{cy}">{escape(lang)} {val * 100 / total:.2f}%</text>')
    label = "Linguaggi più usati: " + ", ".join(f"{l} {v * 100 / total:.1f}%" for l, v in ranked)
    return card(width, height, "\n".join(body), label)


# ----------------------------------------------------------------- main
def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    errors = 0

    for name in PINNED:
        try:
            repo = api(f"/repos/{USERNAME}/{name}")
            repo["description"] = repo.get("description") or DESCRIPTIONS.get(name)
            if repo.get("language") in EXCLUDE_LANGS:  # es. Unity -> ShaderLab: usa il primo linguaggio "vero"
                langs = api(f"/repos/{USERNAME}/{name}/languages")
                repo["language"] = next((l for l in langs if l not in EXCLUDE_LANGS), repo["language"])
            (OUT_DIR / f"pin-{name}.svg").write_text(pin_card(repo), encoding="utf-8", newline="\n")
            print(f"ok   pin-{name}.svg")
        except Exception as exc:  # una card mancante non deve bloccare le altre
            errors += 1
            print(f"ERR  {name}: {exc}", file=sys.stderr)

    try:
        repos = api(f"/users/{USERNAME}/repos?per_page=100&type=owner")
        totals: dict[str, int] = {}
        for r in repos:
            if r["fork"] or r["archived"]:
                continue
            for lang, size in api(f"/repos/{USERNAME}/{r['name']}/languages").items():
                if lang not in EXCLUDE_LANGS:
                    totals[lang] = totals.get(lang, 0) + size
        (OUT_DIR / "top-langs.svg").write_text(top_langs_card(totals), encoding="utf-8", newline="\n")
        print("ok   top-langs.svg  ->", ", ".join(sorted(totals, key=totals.get, reverse=True)[:LANGS_COUNT]))
    except Exception as exc:
        errors += 1
        print(f"ERR  top-langs: {exc}", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
