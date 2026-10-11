<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Sol website slice notes

## Part A — base-game scope, 11 October 2026

The ledger retains 187 base-game features at the original audited game commit
`dd29d91`, with 13 guide gaps and six source/document discrepancies. Optional
rows are removed by their existing status/area fields; the Mods menu,
resource-pack plan and dimension plans are excluded by their evidence and
request IDs. Mixed entries retain their base-game behavior and source locations.
The generated controls contain only retained features. Inventory Pack and boat
packing remain ordinary base-game terms.

The optional Jade Willow gallery, catalog, scripts, captures and reproduction
tools are removed from the current tree, as required by the newer base-game-only
scope. Their original data, licences and provenance remain recoverable from
Git commit `493c52c`; no hidden unfiltered ledger or gallery copy was made.
Unrelated performance evidence is preserved.

`bash tools/verify_wiki.sh` passed: original catalogs, 33 unit tests, feature and
guide freshness, 37 recipes, repository links, 571 staged files, staged links
and the new base-game regression. Browser capture is deferred to the parent;
this helper has no sockets. No game source re-audit or gameplay capture was run.

## Part B — home, navigation and article layout

The biome page is preserved as `atlas.html`. All twelve HTML pages share category
navigation; atlas pages also share an Atlas subnavigation with an exact current
page. The home links the four written guides and labels Blocks, Mobs, Building,
Exploration and Troubleshooting as Not written yet. No optional category exists.
The four guide articles have titles, breadcrumbs and expandable contents.
`data/search.js` holds 320 offline records from existing base-game data.

The private local Git directory is `.cache/sol-history.git`, because the sandbox
blocks writes to the worktree Git metadata in the standalone repository. The
normal `.git` pointer stays unchanged. A bundle will carry both commits to the
parent. Browser checks and runner support were prepared but not executed: this
helper must not open sockets. Parent owns actual captures and integration.

Static header/category/search validation passed for all twelve pages and 320
records. The final full gate result and integration commands are recorded in
the uncommitted `SOL_WEBSITE_HANDOFF.md`. The pre-existing private performance
archive was not changed by this scoped slice; its publication exclusions remain
in force. Guide-gap ranks are unique positive priorities with stable references
to the written guides, so optional task removal does not relabel guide IDs.
