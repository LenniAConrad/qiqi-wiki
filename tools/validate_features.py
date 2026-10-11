#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate the feature and guide-coverage ledger.

Checks the schema and status vocabulary, that features.html exactly matches a
fresh render of data/features.json, and that every site page links to it.
With --game, also checks that each evidence path:line exists in an exported
snapshot of the audited game commit.
"""

import argparse
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_features  # noqa: E402  (sibling tool module)

ROOT = build_features.ROOT
STATUSES = ("available", "partial", "developer", "in-development", "planned")
GUIDE_STATES = ("none", "atlas", "partial", "complete")
READINESS = ("ready", "needs-screenshots", "blocked-planned")
ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
BACKLOG = re.compile(r"(?:VOX|QW)-[A-Z0-9]+(?:-[A-Z0-9]+)*")
EVIDENCE = re.compile(r"(?P<path>[A-Za-z0-9_.][A-Za-z0-9_./-]*)(?::(?P<start>\d+)(?:-(?P<end>\d+))?)?(?: — .+)?")
HEADLINE = re.compile(r"(?:[^<>]|<br>|<em>|</em>)+")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, limit=None):
    ok = isinstance(value, str) and bool(value.strip()) and value == value.strip()
    return ok and (limit is None or len(value) <= limit)


def check_evidence(item, where):
    if item.startswith("search: "):
        require(text(item[8:]), f"{where}: empty search evidence")
        return None
    match = EVIDENCE.fullmatch(item)
    require(match, f"{where}: evidence must be path[:line[-line]] or 'search: …', got {item!r}")
    require(not match["path"].startswith("/") and ".." not in Path(match["path"]).parts,
            f"{where}: evidence path must be relative inside the game: {item!r}")
    if match["end"]:
        require(int(match["end"]) >= int(match["start"]), f"{where}: reversed line range {item!r}")
    return match


def validate_ledger(ledger):
    for key in ("schema", "title", "description", "headline", "lead", "legendLead", "gapsLead", "audited", "game",
                "method", "statuses", "guideStates", "readiness", "areas", "features", "guideGaps"):
        require(key in ledger, f"ledger is missing {key}")
    require(ledger["schema"] == 1, "unsupported ledger schema")
    for key in ("title", "description", "lead", "legendLead", "gapsLead"):
        require(text(ledger[key]), f"{key} must be non-empty trimmed text")
    require(HEADLINE.fullmatch(ledger["headline"]), "headline may only contain text, <br> and <em>")
    audited = date.fromisoformat(ledger["audited"])

    game = ledger["game"]
    require(re.fullmatch(r"[0-9a-f]{40}", game.get("commit", "")), "game.commit must be a full SHA-1")
    committed = datetime.fromisoformat(game["commitDate"])
    require(committed.tzinfo is not None, "game.commitDate needs a UTC offset")
    require(committed.date() <= audited, "game commit cannot postdate the audit")
    require(text(game.get("branch")) and text(game.get("packageVersion")), "game branch/packageVersion required")
    require(type(game.get("newWorldGeneration")) is int and game["newWorldGeneration"] > 0, "invalid generation")

    require([status.get("key") for status in ledger["statuses"]] == list(STATUSES), f"statuses must be {STATUSES}")
    for status in ledger["statuses"]:
        require(text(status.get("label")) and text(status.get("description")), f"status {status['key']} text")
    require([state.get("key") for state in ledger["guideStates"]] == list(GUIDE_STATES), "unexpected guide states")
    require(all(text(state.get("label")) for state in ledger["guideStates"]), "guide states need labels")
    require(sorted(ledger["readiness"]) == sorted(READINESS), "unexpected readiness keys")
    require(all(text(label) for label in ledger["readiness"].values()), "readiness labels required")

    area_keys = [area.get("key") for area in ledger["areas"]]
    require(len(area_keys) == len(set(area_keys)) and all(map(ID.fullmatch, area_keys)), "area keys")
    for area in ledger["areas"]:
        require(text(area.get("label")) and text(area.get("description")), f"area {area['key']} text")

    ids = set()
    for feature in ledger["features"]:
        fid = feature.get("id", "")
        where = f"feature {fid or '?'}"
        require(ID.fullmatch(fid) and fid not in ids, f"{where}: missing, malformed or duplicate id")
        ids.add(fid)
        require(feature.get("area") in area_keys, f"{where}: unknown area")
        require(feature.get("status") in STATUSES, f"{where}: unknown status")
        require(text(feature.get("name"), 80), f"{where}: name required (<= 80 chars)")
        require(text(feature.get("summary"), 600), f"{where}: summary required (<= 600 chars)")
        modes = feature.get("modes", [])
        require(isinstance(modes, list) and len(modes) == len(set(modes))
                and set(modes) <= set(build_features.MODE_LABELS), f"{where}: invalid modes")
        for control in feature.get("controls", []):
            require(isinstance(control, list) and len(control) == 2 and all(text(part, 220) for part in control),
                    f"{where}: controls are [input, action] pairs")
        evidence = feature.get("evidence")
        require(isinstance(evidence, list) and evidence, f"{where}: evidence required")
        for item in evidence:
            check_evidence(item, where)
        backlog = feature.get("backlog", [])
        require(all(isinstance(item, str) and BACKLOG.fullmatch(item) for item in backlog), f"{where}: backlog ids")
        require("pack" not in feature, f"{where}: base-game features cannot name a content pack")
        if feature["status"] == "planned":
            require(backlog, f"{where}: planned features cite the request that tracks them")
        if "notes" in feature:
            require(text(feature["notes"], 600), f"{where}: notes must be trimmed text (<= 600 chars)")
        guide = feature.get("guide", {})
        require(guide.get("state", "none") in GUIDE_STATES, f"{where}: unknown guide state")
        if feature["status"] == "planned":
            require(guide.get("state", "none") == "none", f"{where}: planned features cannot have a guide yet")
        if guide.get("page"):
            page = guide["page"].split("#", 1)[0]
            require((ROOT / page).is_file() and "/" not in page, f"{where}: guide page {page} missing")
            require(text(guide.get("label")), f"{where}: linked guides need a label")
            require(guide.get("state") in ("atlas", "partial", "complete"), f"{where}: linked guide state")
        else:
            require(guide.get("state", "none") == "none", f"{where}: guide state without a page")
        if "next" in guide:
            require(text(guide["next"], 80), f"{where}: next guide title")
    for area in area_keys:
        require(any(feature["area"] == area for feature in ledger["features"]), f"area {area} has no features")

    ranks = sorted(gap.get("rank") for gap in ledger["guideGaps"])
    require(ranks == sorted(set(ranks)) and all(type(rank) is int and rank > 0 for rank in ranks), "guide gap ranks must be unique positive integers")
    for gap in ledger["guideGaps"]:
        where = f"guide gap {gap.get('rank')}"
        require(text(gap.get("title"), 80) and text(gap.get("why"), 400), f"{where}: title/why")
        require(gap.get("readiness") in READINESS, f"{where}: readiness")
        require(gap.get("covers") and all(item in ids for item in gap["covers"]), f"{where}: unknown feature")
    for note in ledger.get("docNotes", []):
        require(text(note.get("topic"), 120) and text(note.get("detail"), 700), "doc note text")
        require(note.get("evidence"), "doc note evidence")
        for item in note["evidence"]:
            check_evidence(item, f"doc note {note['topic']}")
    if ledger.get("docNotes"):
        require(text(ledger.get("docNotesLead")), "docNotesLead required with doc notes")
    require(ledger["method"] and all(text(block.get("title")) and text(block.get("text"))
                                     for block in ledger["method"]), "method blocks")
    return ids


class NavLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "nav" and attrs.get("aria-label") == "Main":
            self.depth += 1
        elif tag == "a" and self.depth:
            self.links.append(attrs.get("href", ""))

    def handle_endtag(self, tag):
        if tag == "nav" and self.depth:
            self.depth -= 1


def check_navigation():
    for page in sorted(ROOT.glob("*.html")):
        parser = NavLinks()
        parser.feed(page.read_text(encoding="utf-8"))
        require("atlas.html" in parser.links, f"{page.name}: main navigation must link atlas.html")


def check_game(ledger, snapshot):
    marker = snapshot / "SNAPSHOT_COMMIT"
    if marker.exists():
        require(marker.read_text().strip() == ledger["game"]["commit"], "snapshot commit differs from the ledger")
    checked = 0
    items = [item for feature in ledger["features"] for item in feature["evidence"]]
    items += [item for note in ledger.get("docNotes", []) for item in note["evidence"]]
    for item in items:
        match = check_evidence(item, "evidence")
        if match is None:
            continue
        path = snapshot / match["path"]
        require(path.is_file(), f"evidence file missing in snapshot: {item}")
        if match["start"]:
            lines = path.read_text(encoding="utf-8", errors="replace").count("\n") + 1
            last = int(match["end"] or match["start"])
            require(1 <= int(match["start"]) and last <= lines, f"evidence line outside {path.name} ({lines}): {item}")
        checked += 1
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, help="exported snapshot of the audited game commit")
    args = parser.parse_args()
    ledger = build_features.load()
    ids = validate_ledger(ledger)
    require(build_features.PAGE.read_text(encoding="utf-8") == build_features.render_page(ledger),
            "features.html is stale: run python3 tools/build_features.py")
    check_navigation()
    summary = f"PASS: {len(ids)} ledger features, {len(ledger['guideGaps'])} ranked guide gaps, page current"
    if args.game:
        summary += f", {check_game(ledger, args.game.resolve())} evidence locations in the game snapshot"
    print(summary)


if __name__ == "__main__":
    main()
