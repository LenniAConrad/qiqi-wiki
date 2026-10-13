// SPDX-License-Identifier: GPL-3.0-only
'use strict';
const atlas = window.ISLAND_ATLAS;
const islands = atlas?.islands ?? [];
const $ = selector => document.querySelector(selector);
const dialog = $('#detail');
const search = $('#search');
const sort = $('#sort');
const number = new Intl.NumberFormat('en', { maximumFractionDigits: 1 });
let visible = [];
let selectedId = null;
let selectedView = 'map';
let returnFocus = null;
const el = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};
const nameOrder = (a, b) => a.name.localeCompare(b.name, 'en');
const axisLength = island => Math.max(...island.sizeMetres);
const km = metres => `${number.format(metres / 1000)} km`;
const metres = value => `${number.format(value)} m`;
const viewName = view => view.tabLabel || ({map:'Map', panorama:'Panorama', temperature:'Temperature', moisture:'Moisture', elevation:'Elevation', biomes:'Biomes'}[view.type]) || view.label;
const coordinates = values => values.map(number.format).join(' / ');
function imageFor(island, view, eager) {
  const image = el('img');
  const variants = window.ISLAND_THUMBNAILS?.[view.image];
  if (variants) {
    // Set selection hints before src so a full-size request is never started.
    image.sizes = view.type === 'map'
      ? '(max-width: 650px) 32vw, (max-width: 1440px) 16vw, 226px'
      : '(max-width: 650px) 57vw, (max-width: 1440px) 28vw, 402px';
    image.srcset = variants.map(([width, path]) => `${path} ${width}w`).join(', ');
  }
  image.src = variants?.[0]?.[1] || view.image;
  image.alt = view.alt || `${island.name} island — ${view.label}`;
  if (view.width) image.width = view.width;
  if (view.height) image.height = view.height;
  image.loading = eager ? 'eager' : 'lazy';
  image.decoding = 'async';
  return image;
}
function render() {
  const words = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  visible = islands.filter(island => words.every(word => `${island.name} ${island.shape} ${island.description} ${island.seed} ${island.tier || ''}`.toLocaleLowerCase().includes(word)));
  visible.sort((a, b) => (sort.value === 'largest' ? axisLength(b) - axisLength(a) : sort.value === 'smallest' ? axisLength(a) - axisLength(b) : 0) || nameOrder(a, b));
  const fragment = document.createDocumentFragment();
  for (const [index, island] of visible.entries()) {
    const article = el('article', 'card'); article.dataset.island = island.id;
    const previews = el('div', 'island-previews');
    for (const type of ['map', 'panorama']) {
      const view = island.views.find(view => view.type === type); if (!view) continue;
      const button = el('button', 'island-preview'); button.type = 'button'; button.dataset.view = type;
      button.setAttribute('aria-label', `Explore ${island.name} island — ${viewName(view)}`);
      const frame = el('span', 'island-preview-image'); frame.append(imageFor(island, view, index < 2));
      const label = el('span', 'island-preview-label');
      const arrow = el('span', '', '↗'); arrow.setAttribute('aria-hidden', 'true');
      label.append(el('span', '', viewName(view)), arrow); button.append(frame, label);
      button.addEventListener('click', () => openIsland(island.id, type)); previews.append(button);
    }
    const line = el('div', 'card-topline');
    line.append(el('span', '', 'Island shape'), el('span', '', `${km(axisLength(island))} planned long axis`));
    article.append(previews, line, el('h3', '', island.name), el('p', '', island.description), el('div', 'island-card-location', `Seed ${island.seed} · Centre X / Z ${coordinates(island.centerMetres)} m`));
    fragment.append(article);
  }
  $('#grid').replaceChildren(fragment);
  $('#result-count').textContent = atlas ? `${visible.length} of ${islands.length} island shapes` : 'The island catalog could not be loaded. Reload this page to try again.';
  $('#empty').hidden = visible.length !== 0 || !atlas;
}
function fact(label, value) {
  const node = el('div'); node.append(el('dt', '', label), el('dd', '', value)); return node;
}
function selectView(type) {
  const island = islands.find(island => island.id === selectedId); if (!island) return;
  const view = island.views.find(view => view.type === type) || island.views[0];
  selectedView = view.type;
  const image = $('#detail-image');
  image.src = view.image; image.alt = view.alt || `${island.name} island — ${view.label}`;
  if (view.width) image.width = view.width;
  if (view.height) image.height = view.height;
  $('#original-image').href = view.image;
  $('#original-image').setAttribute('aria-label', `Open full-size ${viewName(view).toLocaleLowerCase()} of ${island.name} island`);
  for (const button of $('#view-controls').children) button.setAttribute('aria-pressed', String(button.dataset.view === view.type));
  const details = [view.label];
  if (view.northUp) details.push('North up');
  if (view.extentMetres) details.push(`${Array.isArray(view.extentMetres) ? view.extentMetres.map(km).join(' × ') : km(view.extentMetres)} ${view.type === 'panorama' ? 'terrain' : 'map'} span`);
  if (view.metresPerPixel) details.push(`${number.format(view.metresPerPixel)} m per pixel`);
  if (view.type === 'panorama' && view.sampleSpacingMetres) details.push(`Source samples every ${number.format(view.sampleSpacingMetres)} m`);
  if (view.cameraMetres) details.push(`Camera X / Y / Z ${coordinates(view.cameraMetres)} m`);
  if (view.width && view.height) details.push(`${number.format(view.width)} × ${number.format(view.height)} pixels`);
  $('#view-description').textContent = `${details.join(' · ')}${view.description ? `. ${view.description}` : ''}`;
  const legend = view.legend;
  $('#view-legend').hidden = !legend;
  $('#legend-title').textContent = legend?.title || `${viewName(view)} legend`;
  $('#legend-stops').replaceChildren(...(legend?.stops || []).map(stop => {
    const item = el('li'); const swatch = el('span', 'island-legend-swatch');
    swatch.style.backgroundColor = stop.color; swatch.setAttribute('aria-hidden', 'true');
    item.append(swatch, el('span', '', stop.label)); return item;
  }));
  $('#legend-note').textContent = legend?.note || '';
  $('#legend-note').hidden = !legend?.note;
}
function openIsland(id, type = 'map') {
  const island = islands.find(island => island.id === id); if (!island) return;
  const restoreViewFocus = dialog.open && $('#view-controls').contains(document.activeElement);
  if (!dialog.open) returnFocus = document.activeElement;
  selectedId = id;
  $('#detail-title').textContent = island.name;
  $('#detail-category').textContent = 'Island shape';
  const list = visible.some(item => item.id === id) ? visible : [...islands].sort(nameOrder);
  $('#detail-number').textContent = `${list.findIndex(item => item.id === id) + 1} / ${list.length}`;
  $('#detail-description').textContent = island.description;
  const facts = [fact('World seed', island.seed), fact('Island centre · X / Z', `${coordinates(island.centerMetres)} m`), fact('World generation', String(atlas.generatorVersion)), fact('Planned long × short axes', [...island.sizeMetres].sort((a,b) => b-a).map(metres).join(' × '))];
  if (Number.isFinite(island.areaKm2)) facts.push(fact('Sampled dry land', `${number.format(island.areaKm2)} km²`));
  if (island.tier) facts.push(fact('Island scale', island.tier));
  $('#detail-facts').replaceChildren(...facts);
  $('#view-controls').replaceChildren(...island.views.map(view => {
    const button = el('button', '', viewName(view)); button.type = 'button'; button.dataset.view = view.type;
    button.addEventListener('click', () => selectView(view.type)); return button;
  }));
  selectView(type);
  if (!dialog.open) { dialog.showModal(); document.body.classList.add('modal-open'); }
  if (restoreViewFocus) $('#view-controls [aria-pressed=true]').focus({ preventScroll: true });
  dialog.scrollTop = 0;
}
function navigate(direction) {
  const list = visible.some(island => island.id === selectedId) ? visible : [...islands].sort(nameOrder);
  if (!list.length) return;
  const index = list.findIndex(island => island.id === selectedId);
  openIsland(list[(index + direction + list.length) % list.length].id, selectedView);
}
function followHash() {
  const id = new URLSearchParams(location.hash.slice(1)).get('island');
  if (id) openIsland(id);
}
search.addEventListener('input', render);
sort.addEventListener('change', render);
$('#reset-filters').addEventListener('click', () => { search.value = ''; sort.value = 'name'; render(); search.focus(); });
$('#close-detail').addEventListener('click', () => dialog.close());
dialog.addEventListener('close', () => {
  document.body.classList.remove('modal-open');
  if (returnFocus?.isConnected && returnFocus !== document.body) returnFocus.focus({ preventScroll: true });
});
dialog.addEventListener('click', event => {
  if (event.target !== dialog) return;
  const rect = dialog.getBoundingClientRect();
  if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
});
$('#previous').addEventListener('click', () => navigate(-1));
$('#next').addEventListener('click', () => navigate(1));
document.addEventListener('keydown', event => {
  if (dialog.open && ['ArrowRight', 'ArrowLeft'].includes(event.key)) { event.preventDefault(); navigate(event.key === 'ArrowRight' ? 1 : -1); }
  else if (event.key === '/' && !dialog.open && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) { event.preventDefault(); search.focus(); }
});
window.addEventListener('hashchange', followHash);
if (atlas) {
  $('#shape-count').textContent = String(islands.length);
  $('#view-count').textContent = `${new Set(islands.flatMap(island => island.views.map(view => view.type))).size} views`;
  $('#generation').textContent = String(atlas.generatorVersion).padStart(2, '0');
  $('#notes-generation').textContent = String(atlas.generatorVersion);
}
render();
followHash();
