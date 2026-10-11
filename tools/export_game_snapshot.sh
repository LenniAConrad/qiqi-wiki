#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Export the source and documents of one committed game version for auditing.
# Usage: tools/export_game_snapshot.sh GAME_REPO COMMIT DESTINATION
# Reads only committed objects, so the game checkout and its working files are
# never modified. Binary assets are omitted; evidence cites source and docs.
set -euo pipefail
repo=${1:?game repository}
commit=$(git -C "$repo" rev-parse --verify "${2:?commit}^{commit}")
dest=${3:?destination directory}
if [ -e "$dest" ] && [ -n "$(ls -A "$dest")" ]; then
  echo "Refusing to export into non-empty $dest" >&2
  exit 1
fi
mkdir -p "$dest"
paths=()
for path in crates mods src docs tools examples Cargo.toml README.md TODO.md AGENTS.md CLAUDE.md \
            CONTRIBUTING.md install.sh install-windows.ps1 install-windows.cmd Install-macOS.command \
            START-HERE-macOS.txt run.sh; do
  if git -C "$repo" cat-file -e "$commit:$path" 2>/dev/null; then paths+=("$path"); fi
done
git -C "$repo" archive "$commit" "${paths[@]}" | tar -x -C "$dest"
echo "$commit" > "$dest/SNAPSHOT_COMMIT"
echo "Exported ${#paths[@]} paths of $commit to $dest"
