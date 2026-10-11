#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Render the feature and guide-coverage ledger from data/features.json.

Writes features.html, which is complete without JavaScript; features.js only
adds search and status filters to the rendered articles. The output is
deterministic; tools/validate_features.py rebuilds it in memory and requires
the committed page to match exactly.
"""

import argparse
from base_game import public_ledger
from wiki_layout import header_html, footer_html
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "features.json"
GUIDES = ROOT / "data" / "guides.json"
PAGE = ROOT / "features.html"
REPOSITORY_NOTE = "private game repository"

MODE_LABELS = {"creative": "Creative", "survival": "Survival", "menu": "Menus", "any": "Any mode"}
MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")


def text(value):
    return escape(str(value), quote=False)


def attr(value):
    return escape(str(value), quote=True)


def long_date(iso_date):
    year, month, day = (int(part) for part in iso_date[:10].split("-"))
    return f"{day} {MONTHS[month - 1]} {year}"


def search_text(feature, area, status, pack):
    parts = [feature["name"], feature["summary"], area["label"], status["label"],
             feature.get("notes", ""), pack or ""]
    parts += [f"{key} {action}" for key, action in feature.get("controls", [])]
    parts += [MODE_LABELS[mode] for mode in feature.get("modes", [])]
    guide = feature.get("guide", {})
    parts += [guide.get("next", ""), guide.get("label", "")]
    return " ".join(part for part in parts if part).lower()


def guide_html(feature, guide_states):
    guide = feature.get("guide", {})
    state = guide_states[guide.get("state", "none")]
    pieces = [f'<span class="guide-state guide-{attr(state["key"])}">{text(state["label"])}</span>']
    if guide.get("page"):
        pieces.append(f'<a href="{attr(guide["page"])}">{text(guide.get("label") or guide["page"])}</a>')
    if guide.get("next"):
        pieces.append(f'<span>Next guide: {text(guide["next"])}</span>')
    return '<p class="feature-guide"><span class="field-label">Wiki</span> ' + " · ".join(pieces) + "</p>"


def feature_html(feature, area, statuses, guide_states):
    status = statuses[feature["status"]]
    pack = feature.get("pack")
    rows = [
        f'<article class="feature" id="f-{attr(feature["id"])}" data-status="{attr(status["key"])}"'
        f' data-area="{attr(area["key"])}" data-search="{attr(search_text(feature, area, status, pack))}">',
        '<div class="feature-head">'
        f'<h4>{text(feature["name"])}</h4>'
        f'<span class="status status-{attr(status["key"])}">{text(status["label"])}</span></div>',
    ]
    meta = [MODE_LABELS[mode] for mode in feature.get("modes", [])]
    if pack:
        meta.append(f"Pack: {pack}")
    if meta:
        rows.append(f'<p class="feature-meta">{text(" · ".join(meta))}</p>')
    rows.append(f'<p class="feature-summary">{text(feature["summary"])}</p>')
    controls = feature.get("controls", [])
    if controls:
        rows.append('<dl class="feature-controls">' + "".join(
            f'<div><dt><kbd>{text(key)}</kbd></dt><dd>{text(action)}</dd></div>'
            for key, action in controls) + "</dl>")
    if feature.get("notes"):
        rows.append(f'<p class="feature-notes">{text(feature["notes"])}</p>')
    rows.append(guide_html(feature, guide_states))
    evidence = "".join(f"<li><code>{text(item)}</code></li>" for item in feature["evidence"])
    backlog = feature.get("backlog", [])
    backlog_html = (f'<p>Tracked as {", ".join(f"<code>{text(item)}</code>" for item in backlog)}.</p>'
                    if backlog else "")
    rows.append(f'<details class="feature-evidence"><summary>Source evidence</summary><ul>{evidence}</ul>'
                f"{backlog_html}</details>")
    rows.append("</article>")
    return "".join(rows)


def written_guides():
    """Map ranked gap number to the guide that fills it, when guides exist."""
    if not GUIDES.is_file():
        return {}
    guides = json.loads(GUIDES.read_text(encoding="utf-8"))["guides"]
    return {guide["gap"]: guide for guide in guides if "gap" in guide}


def render_page(ledger):
    ledger = public_ledger(ledger)
    statuses = {status["key"]: status for status in ledger["statuses"]}
    guide_states = {state["key"]: state for state in ledger["guideStates"]}
    areas = ledger["areas"]
    features = ledger["features"]
    game = ledger["game"]
    audited = long_date(ledger["audited"])
    commit_short = game["commit"][:7]
    counts = {key: sum(feature["status"] == key for feature in features) for key in statuses}
    playable = counts.get("available", 0) + counts.get("partial", 0)
    guides_written = sum(feature.get("guide", {}).get("state", "none") == "complete" for feature in features)

    out = []
    add = out.append
    add("<!doctype html>\n<!-- SPDX-License-Identifier: GPL-3.0-only -->\n"
        "<!-- Generated by tools/build_features.py from data/features.json. Do not edit by hand. -->\n"
        '<html lang="en">\n<head>\n'
        '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'<meta name="description" content="{attr(ledger["description"])}">\n'
        '<meta name="theme-color" content="#253c30"><title>Features &amp; guide coverage · Qiqi wiki</title>\n'
        '<link rel="icon" href="favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="style.css">'
        '<link rel="stylesheet" href="features.css"><link rel="stylesheet" href="wiki.css">\n'
        '<script defer src="features.js"></script>\n'
        '</head>\n<body class="features-page">\n'
        '<a class="skip" href="#ledger">Skip to the feature ledger</a>\n'
        + header_html('features.html') + '\n<main>\n')
    add('<section class="intro" aria-labelledby="title"><div class="eyebrow"><span class="status-dot"></span> '
        f'FEATURE LEDGER / AUDITED {text(audited.upper())}</div><div class="intro-row">'
        f'<h1 id="title">{ledger["headline"]}</h1><p>{text(ledger["lead"])}</p></div></section>\n')
    add(f'<div class="study-meta">Voxelgame main <code>{text(commit_short)}</code> · committed '
        f'{text(long_date(game["commitDate"]))} · package {text(game["packageVersion"])} · new worlds use '
        f'generation {text(game["newWorldGeneration"])} · source audit, not a play test</div>\n')
    add('<section class="stats ledger-stats" aria-label="Ledger summary">'
        f'<div><strong>{len(features)}</strong><span>base-game features listed</span></div>'
        f'<div><strong>{playable}</strong><span>playable in the base game</span></div>'
        f'<div><strong>{counts.get("planned", 0)}</strong><span>requested and still planned</span></div>'
        "</section>\n")
    add('<section class="report-section legend-section" aria-labelledby="legend-title"><div class="section-heading">'
        '<div class="eyebrow">HOW TO READ THIS PAGE</div><h2 id="legend-title">Status means what you can do today.</h2></div>'
        f'<p class="report-lead">{text(ledger["legendLead"])}</p><dl class="status-legend">')
    for status in ledger["statuses"]:
        add(f'<div><dt><span class="status status-{attr(status["key"])}">{text(status["label"])}</span>'
            f' <span class="legend-count">{counts.get(status["key"], 0)}</span></dt>'
            f'<dd>{text(status["description"])}</dd></div>')
    add("</dl>")
    add(f'<p class="measurement-note">Guide coverage: {guides_written} of {len(features)} features have a '
        "complete practical guide so far. The ranked list below sets the writing order.</p></section>\n")

    add('<section id="ledger" class="ledger" aria-labelledby="ledger-title"><div class="section-heading">'
        '<div class="eyebrow">01 / THE LEDGER</div><div class="section-heading-row">'
        '<h2 id="ledger-title">Every system, one status.</h2>'
        '<p>Grouped by what you are trying to do.<br>Open “Source evidence” for the audited code locations.</p>'
        "</div></div>\n")
    add('<div class="toolbar" id="ledger-tools" hidden><label class="search-label"><span aria-hidden="true">⌕</span>'
        '<input id="search" type="search" placeholder="Find a feature or key…" aria-label="Search features"'
        ' autocomplete="off"><kbd aria-hidden="true">/</kbd></label></div>\n'
        '<div class="filter-row" id="ledger-filters-row" hidden><div id="filters" class="filters" role="group"'
        ' aria-label="Filter by status"><button type="button" data-status="" aria-pressed="true">All</button>')
    for status in ledger["statuses"]:
        add(f'<button type="button" data-status="{attr(status["key"])}" aria-pressed="false">{text(status["label"])}</button>')
    add('</div><p id="result-count" role="status" aria-live="polite"></p></div>\n')
    add('<nav class="report-nav area-nav" aria-label="Feature areas">' + "".join(
        f'<a href="#area-{attr(area["key"])}">{text(area["label"])}</a>' for area in areas) + "</nav>\n")
    for index, area in enumerate(areas, 1):
        members = [feature for feature in features if feature["area"] == area["key"]]
        add(f'<section class="ledger-area" id="area-{attr(area["key"])}" aria-labelledby="area-{attr(area["key"])}-title">'
            f'<div class="area-heading"><div class="eyebrow">AREA {index:02d} OF {len(areas):02d}</div>'
            f'<h3 id="area-{attr(area["key"])}-title">{text(area["label"])}</h3>'
            f'<p>{text(area["description"])}</p></div><div class="feature-list">')
        for feature in members:
            add(feature_html(feature, area, statuses, guide_states))
        add("</div></section>\n")
    add('<div id="empty" class="empty" hidden><span aria-hidden="true">⌕</span><h3>No matching features.</h3>'
        '<p>Try another word or show every status.</p><button id="reset-filters" type="button">Clear filters</button></div>\n'
        "</section>\n")

    add('<section id="next-guides" class="report-section" aria-labelledby="next-guides-title"><div class="section-heading">'
        '<div class="eyebrow">02 / WRITING ORDER</div><h2 id="next-guides-title">The guides players need next.</h2></div>'
        f'<p class="report-lead">{text(ledger["gapsLead"])}</p><ol class="priority-list gap-list">')
    by_id = {feature["id"]: feature for feature in features}
    written = written_guides()
    for gap in sorted(ledger["guideGaps"], key=lambda item: item["rank"]):
        covered = ", ".join(f'<a href="#f-{attr(item)}">{text(by_id[item]["name"])}</a>' for item in gap["covers"])
        guide = written.get(gap["rank"])
        if guide:
            badge = (f'<span class="readiness readiness-written">Written</span>')
            title = f'<a href="{attr(guide["page"])}">{text(gap["title"])}</a>'
        else:
            badge = (f'<span class="readiness readiness-{attr(gap["readiness"])}">'
                     f'{text(ledger["readiness"][gap["readiness"]])}</span>')
            title = text(gap["title"])
        add(f'<li><h3>{title} {badge}</h3><p>{text(gap["why"])}</p>'
            f'<p class="gap-covers">Covers: {covered}</p></li>')
    add("</ol></section>\n")

    if ledger.get("docNotes"):
        add('<section id="doc-notes" class="report-section" aria-labelledby="doc-notes-title"><div class="section-heading">'
            '<div class="eyebrow">03 / WHERE DOCUMENTS DISAGREE</div><h2 id="doc-notes-title">The code wins.</h2></div>'
            f'<p class="report-lead">{text(ledger["docNotesLead"])}</p><ul class="doc-notes">')
        for note in ledger["docNotes"]:
            evidence = " ".join(f"<code>{text(item)}</code>" for item in note["evidence"])
            add(f'<li><h3>{text(note["topic"])}</h3><p>{text(note["detail"])}</p><p class="note-evidence">{evidence}</p></li>')
        add("</ul></section>\n")

    add('<section id="method" class="report-section" aria-labelledby="method-title"><div class="section-heading">'
        '<div class="eyebrow">04 / METHOD &amp; LIMITS</div><h2 id="method-title">Checked against the source.</h2></div>'
        '<div class="finding-pair">')
    for block in ledger["method"]:
        add(f'<article><h3>{text(block["title"])}</h3><p>{text(block["text"])}</p></article>')
    add("</div>")
    add(f'<p class="measurement-note">Audited commit <code>{text(game["commit"])}</code> on branch '
        f'{text(game["branch"])}, committed {text(game["commitDate"])}. Evidence paths and line numbers refer to that '
        f"commit in the {REPOSITORY_NOTE}; later game changes can move them.</p>")
    add('<div class="evidence-links"><a href="data/features.json" download>Complete ledger · JSON ↓</a>'
        '<a href="guides.html#coming">Guides still to come ↗</a></div></section>\n')
    add('</main>\n' + footer_html() + '\n</body></html>\n')
    return "".join(out)


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    ledger = load()
    PAGE.write_text(render_page(ledger), encoding="utf-8")
    print(f"Wrote {PAGE.name} with {len(ledger['features'])} features")


if __name__ == "__main__":
    main()
