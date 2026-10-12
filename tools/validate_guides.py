#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate the player guides, their recipe data and their ledger links.

Checks the guide schema, that every cited ledger feature exists, that planned
features are only mentioned inside planned notes, that figures exist with the
declared size, that every owned feature links back to its guide, that the
generated pages exactly match a fresh render, and that every page links to the
guides index. With --game, also checks every recipe (names, sections and
amounts) against the recipe registry in an exported game snapshot.
"""

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_guides  # noqa: E402  (sibling tool module)
import validate_features  # noqa: E402

ROOT = build_guides.ROOT
BLOCK_TYPES = ("p", "h", "steps", "list", "note", "keys", "figure", "recipes", "controls-all")
NOTE_KINDS = tuple(build_guides.NOTE_LABELS)
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
PAGE = re.compile(r"guide-[a-z0-9]+(?:-[a-z0-9]+)*\.html")
LINK = re.compile(r"\{\{(?:guide:)?([a-z0-9-]+)(?:\|[^}]*)?\}\}")
PIECES_PER_BLOCK = 8
# The count closing one (item, count) pair; items may themselves contain parentheses.
AMOUNT = re.compile(r",\s*((?:\d+|BLOCK)(?:\s*[*/]\s*(?:\d+|BLOCK))?)\)")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def strings(block):
    """Yield every text field of one block."""
    for key in ("text", "caption", "alt"):
        if isinstance(block.get(key), str):
            yield block[key]
    for item in block.get("items", []):
        yield item
    for row in block.get("rows", []):
        yield from row


def validate_block(ctx, guide, section, block, where):
    require(block.get("t") in BLOCK_TYPES, f"{where}: unknown block type {block.get('t')!r}")
    kind = block["t"]
    if kind in ("p", "h"):
        require(validate_features.text(block.get("text")), f"{where}: empty text")
    if kind in ("steps", "list"):
        require(block.get("items") and all(validate_features.text(item) for item in block["items"]),
                f"{where}: empty list item")
    if kind == "note":
        require(block.get("kind") in NOTE_KINDS, f"{where}: unknown note kind")
        require(validate_features.text(block.get("text")), f"{where}: empty note")
    if kind == "keys":
        require(block.get("rows") and all(len(row) == 2 and all(validate_features.text(cell) for cell in row)
                                          for row in block["rows"]), f"{where}: key rows need [key, action]")
    if kind == "figure":
        source = ROOT / block.get("src", "")
        require(source.is_file() and source.suffix == ".webp", f"{where}: figure image missing")
        require(validate_features.text(block.get("alt"), 400) and len(block["alt"]) >= 20,
                f"{where}: figure needs real alt text")
        require(validate_features.text(block.get("caption")), f"{where}: figure needs a caption")
        width, height = block.get("size", [1280, 720])
        try:
            from PIL import Image
        except ImportError:  # the gate image has Pillow; skip the dimension check without it
            return
        with Image.open(source) as image:
            require(image.size == (width, height), f"{where}: {source.name} is {image.size}, not {width}x{height}")
    if kind == "recipes":
        wanted = block.get("names")
        known = {recipe["name"] for recipe in ctx.recipes["recipes"]}
        require(wanted is None or set(wanted) <= known, f"{where}: unknown recipe names")
        sections = {section_["key"] for section_ in ctx.recipes["sections"]}
        require(set(block.get("sections", [])) <= sections, f"{where}: unknown recipe section")
    # Planned features may only be named inside notes explicitly labelled planned.
    for value in strings(block):
        for target in LINK.findall(value):
            feature = ctx.features.get(target)
            if feature and feature["status"] == "planned":
                require(kind == "note" and block.get("kind") == "planned",
                        f"{where}: planned feature {target} mentioned outside a planned note")


def validate_guides(guides, ledger, recipes):
    ctx = build_guides.Context(guides, ledger, recipes)
    for key in ("schema", "title", "description", "headline", "lead", "comingLead", "updated", "guides"):
        require(key in guides, f"guides.json is missing {key}")
    require(guides["schema"] == 1, "unsupported guides schema")
    ranks = {gap["rank"] for gap in ledger["guideGaps"]}
    owner = {}
    seen_pages, seen_ids = set(), set()
    for index, guide in enumerate(guides["guides"], 1):
        where = f"guide {guide.get('id')}"
        for key in ("id", "page", "number", "kicker", "title", "headline", "summary", "lead", "readTime",
                    "audience", "updated", "state", "covers", "owns", "verification", "sections"):
            require(key in guide, f"{where}: missing {key}")
        require(SLUG.fullmatch(guide["id"]) and guide["id"] not in seen_ids, f"{where}: id must be a unique slug")
        require(PAGE.fullmatch(guide["page"]) and guide["page"] not in seen_pages, f"{where}: page name")
        seen_ids.add(guide["id"])
        seen_pages.add(guide["page"])
        require(guide["number"] == index, f"{where}: guides must be numbered 1..n in order")
        require(guide.get("gap") is None or guide["gap"] in ranks, f"{where}: unknown ledger gap rank")
        require(guide["state"] in ("partial", "complete"), f"{where}: state")
        for key in ("method", "limits"):
            require(validate_features.text(guide["verification"].get(key)), f"{where}: verification {key}")
        require("play" in guide["verification"]["limits"].lower(),
                f"{where}: verification must say whether the guide was play-tested")
        for item in guide["covers"]:
            require(item in ctx.features, f"{where}: unknown covered feature {item}")
        require(set(guide["owns"]) <= set(guide["covers"]), f"{where}: owns must be a subset of covers")
        require(set(guide.get("partial", [])) <= set(guide["owns"]), f"{where}: partial must be owned")
        for item in guide["owns"]:
            require(item not in owner, f"{where}: {item} is also owned by {owner.get(item)}")
            require(ctx.features[item]["status"] != "planned", f"{where}: planned feature {item} cannot be owned")
            owner[item] = guide["id"]
            linked = ctx.features[item].get("guide", {})
            expected = "partial" if item in guide.get("partial", []) else "complete"
            require(linked.get("page") == guide["page"] and linked.get("state") == expected,
                    f"{where}: ledger entry {item} is not linked; run python3 tools/link_guides.py")
        for slug in guide.get("next", []):
            require(slug in ctx.by_slug and slug != guide["id"], f"{where}: unknown next guide {slug}")
        section_ids = set()
        for section in guide["sections"]:
            require(SLUG.fullmatch(section["id"]) and section["id"] not in section_ids, f"{where}: section id")
            section_ids.add(section["id"])
            require(validate_features.text(section["title"]) and section["blocks"], f"{where}: empty section")
            for position, block in enumerate(section["blocks"], 1):
                validate_block(ctx, guide, section, block, f"{where} / {section['id']} #{position}")
    return ctx


def validate_recipes(recipes):
    require(recipes["schema"] == 1 and recipes["piecesPerBlock"] == PIECES_PER_BLOCK, "recipes: schema")
    sections = {section["key"] for section in recipes["sections"]}
    names = [recipe["name"] for recipe in recipes["recipes"]]
    require(len(names) == len(set(names)), "recipes: duplicate recipe names")
    for recipe in recipes["recipes"]:
        where = f"recipe {recipe['name']}"
        require(recipe["section"] in sections, f"{where}: unknown section")
        require(isinstance(recipe["quantity"], int) and recipe["quantity"] > 0, f"{where}: quantity")
        require(recipe["inputs"] and all(isinstance(count, int) and count > 0 for _, count in recipe["inputs"]),
                f"{where}: inputs")
        require(re.fullmatch(r"crates/.+\.rs:\d+-\d+", recipe["evidence"]), f"{where}: evidence location")
        require(".rs" not in recipe.get("notes", ""), f"{where}: notes are for players, keep source paths in evidence")
    return len(names)


def parse_registry(source):
    """Return (name, category, ingredient counts, output counts) per RECIPES entry."""
    start = source.index("pub static RECIPES")
    body = source[start:source.index("\n];", start)]

    def amount(expression):
        expression = expression.strip().replace("BLOCK", str(PIECES_PER_BLOCK))
        match = re.fullmatch(r"(\d+)(?:\s*([*/])\s*(\d+))?", expression)
        require(match, f"cannot read amount {expression!r}")
        if match[2] is None:
            return int(match[1])
        return int(match[1]) * int(match[3]) if match[2] == "*" else int(match[1]) // int(match[3])

    entries = []
    for chunk in re.split(r"\n    Recipe \{", body)[1:]:
        name = re.search(r'name: "([^"]+)"', chunk)[1]
        category = re.search(r"category: RecipeCategory::(\w+)", chunk)[1]

        def counts(label):
            listed = re.search(rf"{label}: &\[(.*?)\],\n", chunk, re.S)[1]
            return [amount(value) for value in AMOUNT.findall(listed)]

        entries.append((name, category, counts("ingredients"), counts("outputs")))
    return entries


def check_game(recipes, snapshot):
    source = (snapshot / "crates/voxelgame-core/src/inventory.rs").read_text(encoding="utf-8")
    section_of = {"Timber": "timber", "Fire": "fire", "Materials": "materials", "Tools": "tools"}
    registry = parse_registry(source)
    require(len(registry) == len(recipes["recipes"]), "recipe count differs from the game registry")
    for (name, category, ingredients, outputs), recipe in zip(registry, recipes["recipes"]):
        require(name == recipe["name"], f"recipe order or name differs: {name} / {recipe['name']}")
        require(section_of[category] == recipe["section"], f"{name}: section differs")
        require(ingredients == [count for _, count in recipe["inputs"]], f"{name}: ingredient amounts differ")
        require(outputs == [recipe["quantity"]], f"{name}: output amount differs")
    return len(registry)


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


def check_pages(pages):
    for name, html in pages.items():
        require((ROOT / name).read_text(encoding="utf-8") == html,
                f"{name} is stale: run python3 tools/build_guides.py")
    extra = {path.name for path in ROOT.glob("guide-*.html")} - set(pages)
    require(not extra, f"guide pages without data: {sorted(extra)}")
    for page in sorted(ROOT.glob("*.html")):
        parser = NavLinks()
        parser.feed(page.read_text(encoding="utf-8"))
        require("guides.html" in parser.links, f"{page.name}: main navigation must link guides.html")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, help="exported snapshot of the audited game commit")
    args = parser.parse_args()
    guides, ledger, recipes = build_guides.load()
    ctx = validate_guides(guides, ledger, recipes)
    recipe_count = validate_recipes(recipes)
    pages = build_guides.render_all(guides, ledger, recipes)
    check_pages(pages)
    summary = (f"PASS: {len(guides['guides'])} guides, {len(pages)} pages current, "
               f"{sum(len(g['owns']) for g in guides['guides'])} ledger features linked, {recipe_count} recipes")
    del ctx
    if args.game:
        summary += f", {check_game(recipes, args.game.resolve())} recipes match the game registry"
    print(summary)


if __name__ == "__main__":
    main()
