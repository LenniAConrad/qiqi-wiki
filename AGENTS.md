# qiqi-wiki agent conventions

This is the owner's standalone static Voxelgame player wiki. Source baseline was copied from local qiqi-dev with its current working files, without modifying that checkout. Read WIKI_PLAN.md, README.md and NOTICE.md. Keep original assets/provenance and make only evidence-backed gameplay instructions. Planned features must stay explicitly planned until implemented and tested in the game.

Use your own worktree and exclusive agent-hub claims; never edit shared main or another agent's checkout. Land through agent-hub/bin/land with the qiqi-wiki worker configuration. Run bash tools/verify_wiki.sh before landing. Visual UI changes require actual browser review/captures at desktop/mobile sizes, keyboard and offline/static-relative-link checks. Do not launch a visible game window for screenshots; use the game's disposable headless debug workflow.

Never overwrite the original qiqi-dev checkout or normal player saves. Preserve existing galleries and data; update generation/source receipts honestly. Publish only original/licensed content and retain licence notices. Follow existing fleet quota/reset/model/spending rules. Small reviewed static commits automatically deploy via GitHub Pages; no server backend, secrets, paid API fallback or runtime build required. Update wiki coverage ledger and worker notes after each coherent unit.
