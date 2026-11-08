# SPDX-License-Identifier: GPL-3.0-only
"""Markup for icons in the shared Catalogue sprite (see tools/build_catalogue_icons.py)."""
import json
from pathlib import Path

MANIFEST = json.loads((Path(__file__).resolve().parents[1] / 'data/catalogue-icons.json').read_text())
# wiki.css sizes the sprite as 16 icons per row; keep the two in step.
assert MANIFEST['columns'] == 16


def icon_html(name, extra_class=''):
    """The named block or item's Catalogue icon, or '' when the Catalogue has none."""
    index = MANIFEST['icons'].get(name)
    if index is None:
        return ''
    columns = MANIFEST['columns']
    classes = f'item-icon {extra_class}'.strip()
    return f'<span class="{classes}" style="--x:{index % columns};--y:{index // columns}" aria-hidden="true"></span>'
