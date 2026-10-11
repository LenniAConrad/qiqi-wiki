<!-- SPDX-License-Identifier: GPL-3.0-only -->
# Streaming optimization validation — 28 September 2026

This is a public summary of the preserved `verification-20260928` record.
It describes those historical builds, not the current game.

| Check | Passed | Failed | Ignored |
| --- | ---: | ---: | ---: |
| Workspace tests | 1,189 | 0 | 18 |
| Devtools tests | 81 | 0 | 1 |
| Python debug adapter | 15 | 0 | — |

Formatting, lint, public documentation and private core documentation checks
also passed. Recorded source files remained unchanged during the checks.

Eight headless replays passed 780 commands and 118 assertions; 126 frame
captures were reviewed. A final movement and rapid-toggle smoke check passed
64 commands, with 11 additional captures reviewed. The sessions disabled save
writes. The broad replays reported empty native logs and no distant tiles in
captures with distant terrain disabled.

The village follow-up waited for two stable 120-frame windows. It retained
3,092 resident and 958 visible detailed chunks, 71 resident far tiles and the
full 128-metre detail radius, with zero edits and save writes disabled.

An interrupted preliminary check is excluded. Cold starts and newly enabled
horizons still stream asynchronously. These checks cover the recorded scenes
and discrete frames; they do not establish correctness in every world or on
every hardware configuration.

See the [optimization report](../../../PERFORMANCE_OPTIMIZATION.md) for the
measurement method and before/after results. Raw logs, source manifests and
the source patch remain in the repository archive and are excluded from Pages.
