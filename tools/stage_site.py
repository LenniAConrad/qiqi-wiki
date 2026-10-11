#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Copy exactly the published static website into a fresh directory.

GitHub Pages and the local gate both use this file set, so links can be
validated against what visitors actually receive rather than the repository.
"""

import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
# Root files published beside the pages. Markdown reports are linked from the
# pages; AGENTS.md only instructs repository maintainers.
ROOT_PATTERNS = ("*.html", "*.css", "*.js", "*.md", "favicon.svg", "LICENSE")
UNPUBLISHED = {"AGENTS.md"}
DIRECTORIES = ("data", "images", "third_party")


def stage(output):
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"Refusing to stage into non-empty directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    count = 0
    for pattern in ROOT_PATTERNS:
        for source in sorted(ROOT.glob(pattern)):
            if source.is_file() and source.name not in UNPUBLISHED:
                shutil.copy2(source, output / source.name)
                count += 1
    for name in DIRECTORIES:
        source = ROOT / name
        if source.is_dir():  # third_party is optional and may be absent.
            shutil.copytree(source, output / name)
            count += sum(1 for path in source.rglob("*") if path.is_file())
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="new or empty destination directory")
    args = parser.parse_args()
    print(f"Staged {stage(args.output.resolve())} files in {args.output}")


if __name__ == "__main__":
    main()
