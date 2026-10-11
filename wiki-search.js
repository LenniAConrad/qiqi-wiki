/* SPDX-License-Identifier: GPL-3.0-only */
(() => {
  'use strict';
  // Preserve old atlas bookmarks after moving the biome gallery off the home page.
  if (new URLSearchParams(location.hash.slice(1)).has('biome') ||
      ['#catalog', '#method', '#worldgen-update'].includes(location.hash)) {
    location.replace(`atlas.html${location.hash}`);
    return;
  }
  const input = document.getElementById('wiki-search');
  const results = document.getElementById('search-results');
  const status = document.getElementById('search-status');
  const panel = document.getElementById('wiki-search-panel');
  if (!input || !Array.isArray(window.QIQI_SEARCH)) return;
  panel.hidden = false;
  const normalize = value => value.toLocaleLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
  const records = window.QIQI_SEARCH.map(record => ({ ...record, terms: normalize(`${record.title} ${record.text}`) }));
  function render() {
    results.replaceChildren();
    const query = normalize(input.value.trim()).split(/\s+/).filter(Boolean);
    if (!query.length) {
      status.textContent = 'Search guides, features, recipes and the atlas.';
      results.hidden = true;
      return;
    }
    const matches = records.filter(record => query.every(term => record.terms.includes(term)));
    matches.sort((a, b) => (a.kind === 'Guide' ? -1 : 0) - (b.kind === 'Guide' ? -1 : 0));
    results.hidden = matches.length === 0;
    status.textContent = matches.length ? `${matches.length} results${matches.length > 24 ? '; showing the first 24' : ''}.` : 'No results. Try another word.';
    for (const record of matches.slice(0, 24)) {
      const row = document.createElement('li');
      const link = document.createElement('a');
      link.href = record.href;
      link.textContent = record.title;
      const kind = document.createElement('span');
      kind.className = 'search-kind';
      kind.textContent = record.kind;
      const description = document.createElement('small');
      description.textContent = record.text;
      row.append(link, kind, description);
      results.append(row);
    }
  }
  input.addEventListener('input', render);
  input.addEventListener('keydown', event => {
    if (event.key === 'Escape') { input.value = ''; render(); }
    if (event.key === 'Enter') {
      const first = results.querySelector('a');
      if (first) first.focus();
    }
  });
  document.addEventListener('keydown', event => {
    if (event.key === '/' && !event.ctrlKey && !event.metaKey && !event.altKey &&
        !event.target.closest('input, textarea, select, [contenteditable]')) {
      event.preventDefault();
      input.focus();
    }
  });
  render();
})();
