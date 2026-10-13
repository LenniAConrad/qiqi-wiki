// SPDX-License-Identifier: GPL-3.0-only
'use strict';
const atlas = window.BIOME_ATLAS;
const biomes = atlas.biomes;
const $ = (selector) => document.querySelector(selector);
const grid = $('#grid');
const search = $('#search');
const sort = $('#sort');
const dialog = $('#detail');
let category = 'All biomes';
let visible = [];
let selectedId = null;
const categories = ['All biomes', 'Woodlands', 'Grasslands', 'Drylands', 'Cold & alpine', 'Wetlands', 'Coasts & seas', 'Geological'];
const percent = (value) => `${value.toLocaleString('en-US', { minimumFractionDigits: value >= 1 ? 2 : 3, maximumFractionDigits: value >= 1 ? 2 : 4 })}%`;
const el = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};
for (const name of categories) {
  const button = el('button', '', name);
  button.type = 'button';
  button.setAttribute('aria-pressed', String(category === name));
  button.addEventListener('click', () => {
    category = name;
    for (const item of $('#filters').children) item.setAttribute('aria-pressed', String(item === button));
    render();
  });
  $('#filters').append(button);
}
function render() {
  const words = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  visible = biomes.filter(b => (category === 'All biomes' || b.category === category)
    && words.every(word => `${b.name} ${b.description} ${b.category} ${b.tags || ''} ${Object.values(b.habitat).filter(value => !value.startsWith('No ')).join(' ')}`.toLocaleLowerCase().includes(word)));
  visible.sort(sort.value === 'name' ? (a, b) => a.name.localeCompare(b.name)
    : sort.value === 'rare' ? (a, b) => a.count - b.count || a.name.localeCompare(b.name)
    : (a, b) => b.count - a.count || a.name.localeCompare(b.name));
  const fragment = document.createDocumentFragment();
  for (const [index, b] of visible.entries()) {
    const article = el('article', 'card');
    article.style.animationDelay = `${Math.min(index, 8) * 20}ms`;
    const button = el('button', 'card-image');
    button.type = 'button';
    button.setAttribute('aria-label', `Explore ${b.name}, rank ${b.rank}, ${percent(b.percent)} sampled coverage`);
    const img = el('img');
    window.WIKI_IMAGE_PREVIEWS.set(img, b.image, 'biomes',
      '(max-width: 650px) 88vw, (max-width: 1000px) 43vw, (min-width: 1500px) 415px, 28vw');
    img.alt = `${b.name}: ${b.description}`;
    img.width = 960; img.height = 540; img.loading = 'lazy'; img.decoding = 'async';
    const arrow = el('span', 'image-open', '↗'); arrow.setAttribute('aria-hidden', 'true');
    button.append(img, arrow); button.addEventListener('click', () => openBiome(b.id));
    const topline = el('div', 'card-topline');
    topline.append(el('span', '', `No. ${String(b.rank).padStart(2, '0')}`), el('span', '', b.category));
    const titleRow = el('div', 'card-title-row');
    titleRow.append(el('h3', '', b.name), el('span', 'percent', percent(b.percent)));
    article.append(button, topline, titleRow, el('p', '', b.description)); fragment.append(article);
  }
  grid.replaceChildren(fragment);
  $('#empty').hidden = visible.length !== 0;
  $('#result-count').textContent = `${visible.length} of ${biomes.length} biomes`;
}
function openBiome(id) {
  const b = biomes.find(item => item.id === id); if (!b) return;
  selectedId = id;
  $('#detail-image').src = b.image; $('#detail-image').alt = `${b.name}: ${b.description}`;
  $('#detail-title').textContent = b.name;
  $('#detail-category').textContent = b.category;
  $('#detail-rank').textContent = `No. ${String(b.rank).padStart(2, '0')} of ${biomes.length}`;
  $('#detail-percent').textContent = percent(b.percent);
  $('#detail-description').textContent = b.description;
  const habitat = [
    ['Shrubs & young growth', b.habitat.lowGrowth],
    ['Stone & reef groups', b.habitat.stoneGroups],
    ['Ground companions', b.habitat.groundCompanions],
    ...(b.habitat.composition ? [['Landscape pattern', b.habitat.composition]] : []),
  ];
  $('#detail-habitat').replaceChildren(...habitat.map(([label, value]) => {
    const group = el('div'); group.append(el('dt', '', label), el('dd', '', value)); return group;
  }));
  $('#original-image').href = b.image;
  $('#biome-wildlife').href = `animals.html?biome=${encodeURIComponent(b.id)}`;
  const values = [
    ['World seed', b.seed],
    ['Map destination · X Z (metres)', `${b.x} ${b.z}`],
    ['Viewpoint · X / Y / Z', `${b.camera.map(v => Number(v.toFixed(1)).toLocaleString('en-US')).join(' / ')} m`],
    ['Survey hits', `${b.count.toLocaleString('en-US')} / ${atlas.totalSamples.toLocaleString('en-US')}`],
  ];
  $('#detail-location').replaceChildren(...values.map(([label, value]) => {
    const group = el('div'); group.append(el('dt', '', label), el('dd', '', value)); return group;
  }));
  if (!dialog.open) { dialog.showModal(); document.body.classList.add('modal-open'); }
  dialog.scrollTop = 0;
}
function navigate(direction) {
  const list = visible.length && visible.some(b => b.id === selectedId) ? visible : biomes;
  const index = list.findIndex(b => b.id === selectedId);
  openBiome(list[(index + direction + list.length) % list.length].id);
}
search.addEventListener('input', render); sort.addEventListener('change', render);
$('#reset-filters').addEventListener('click', () => { search.value = ''; $('#filters button').click(); search.focus(); });
$('#close-detail').addEventListener('click', () => dialog.close());
dialog.addEventListener('close', () => document.body.classList.remove('modal-open'));
dialog.addEventListener('click', (event) => { if (event.target === dialog) { const r = dialog.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close(); } });
$('#previous').addEventListener('click', () => navigate(-1));
$('#next').addEventListener('click', () => navigate(1));
$('#hero-open').addEventListener('click', () => openBiome(atlas.featuredId));
document.addEventListener('keydown', (event) => {
  if (dialog.open && event.key === 'ArrowRight') { event.preventDefault(); navigate(1); }
  else if (dialog.open && event.key === 'ArrowLeft') { event.preventDefault(); navigate(-1); }
  else if (event.key === '/' && !dialog.open && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) { event.preventDefault(); search.focus(); }
});
const featured = biomes.find(b => b.id === atlas.featuredId);
$('#hero-image').alt = `${featured.name}: ${featured.description}`;
$('#hero-name').textContent = featured.name;
$('#sample-stat').textContent = `${(atlas.totalSamples / 1e6).toFixed(2)}M`;
render();

// Habitat links from the wildlife guide open the matching biome directly.
function openLinkedBiome() {
  const id = new URLSearchParams(location.hash.slice(1)).get('biome');
  if (id) openBiome(id);
}
window.addEventListener('hashchange', openLinkedBiome);
openLinkedBiome();
