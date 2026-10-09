// SPDX-License-Identifier: GPL-3.0-only
'use strict';
(() => {
  const bodies = window.SCALE_ATLAS.bodies.map(body => ({
    ...body,
    width: body.sideKm || body.radiusKm * 2,
    area: body.kind === 'map' ? body.sideKm ** 2 : 4 * Math.PI * body.radiusKm ** 2
  }));
  const byId = new Map(bodies.map(body => [body.id, body]));
  const world = byId.get('voxelgame');
  const q = selector => document.querySelector(selector);
  const svg = q('#scale-diagram');
  const modeControl = q('#scale-mode');
  const focusControl = q('#scale-focus');
  const selection = q('#scale-selection');
  const marks = q('#scale-marks');
  const labels = q('#scale-labels');
  const ruler = q('#scale-ruler');
  const ns = 'http://www.w3.org/2000/svg';
  const params = new URLSearchParams(location.search);
  const initialIds = (params.get('show') || 'sun,voxelgame,earth,minecraft').split(',').filter(id => byId.has(id));
  let visible = new Set(['voxelgame', ...initialIds]);
  let mode = params.get('mode') === 'area' ? 'area' : 'width';
  let zoom = 1, cameraX = 0, cameraY = 0, width = 1000, height = 560, frame = 0;
  let layout = [], totalWidth = 0, maxDiameter = 0, baseScale = 1;
  const pointers = new Map();
  const imageNodes = new Map();
  const failures = new Set();
  const number = (value, digits = 0) => value.toLocaleString('en-US', { maximumFractionDigits: digits });
  const element = (name, attributes, parent, text) => {
    const node = document.createElementNS(ns, name);
    for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, String(value));
    if (text !== undefined) node.textContent = text;
    parent.appendChild(node);
    return node;
  };
  const diameter = body => mode === 'width' ? body.width : 2 * Math.sqrt(body.area / Math.PI);
  const source = body => body.kind === 'map'
    ? body.id === 'voxelgame' ? '#scale-sources' : 'https://docs.papermc.io/paper/reference/server-properties/#max-world-size'
    : 'https://nssdc.gsfc.nasa.gov/planetary/factsheet/' + body.id + 'fact.html';
  function remember() {
    const url = new URL(location.href);
    url.searchParams.set('show', [...visible].join(','));
    url.searchParams.set('mode', mode);
    // Direct file viewing remains usable when the browser disallows history changes.
    try { history.replaceState(null, '', url); } catch { /* URL is optional state. */ }
  }
  function buildLayout() {
    const active = bodies.filter(body => visible.has(body.id)).sort((a, b) => diameter(b) - diameter(a));
    maxDiameter = Math.max(...active.map(diameter));
    const gap = maxDiameter * 0.065;
    let edge = 0;
    layout = active.map(body => {
      const d = diameter(body), item = { body, x: edge + d / 2, d };
      edge += d + gap;
      return item;
    });
    totalWidth = edge - gap;
    baseScale = Math.min((width - 54) / totalWidth, (height - 190) / maxDiameter);
  }
  function fitAll() {
    buildLayout(); zoom = 1; cameraX = totalWidth / 2; cameraY = 0; schedule();
  }
  function focus(id) {
    const item = layout.find(item => item.body.id === id);
    if (!item) return;
    cameraX = item.x; cameraY = 0;
    zoom = Math.min(4000, Math.min(width - 76, height - 190) / (item.d * baseScale));
    schedule();
    q('#scale-status').textContent = item.body.name + ' in focus. All visible objects still use the same scale.';
  }
  function refreshControls() {
    modeControl.value = mode;
    selection.querySelectorAll('button').forEach(button => button.setAttribute('aria-pressed', String(visible.has(button.dataset.body))));
    const previous = focusControl.value;
    focusControl.replaceChildren(...layout.map(({ body }) => {
      const option = document.createElement('option'); option.value = body.id; option.textContent = body.name; return option;
    }));
    focusControl.value = visible.has(previous) ? previous : 'voxelgame';
    q('#scale-view-title').textContent = mode === 'width' ? 'TRUE WIDTHS · SIDE BY SIDE' : 'EQUAL-AREA DISKS · SIDE BY SIDE';
    q('#scale-mode-note').textContent = mode === 'width'
      ? 'Planet diameters and flat map sides share one linear scale. Maps are squares; no body is enlarged for visibility. Select a focus target to inspect the smallest objects.'
      : 'Every disk represents the entire surface or map area. Its radius is √(area / π), so these are not physical planet diameters. Textures identify the objects; they do not change the comparison.';
    const metric = mode === 'area' ? 'area' : 'width';
    const mc = byId.get('minecraft');
    q('#scale-status').textContent = 'Voxelgame’s theoretical map has ' + number(world[metric] / mc[metric], 2) + '× Minecraft’s ' + (mode === 'area' ? 'area.' : 'width.');
    q('#scale-svg-title').textContent = mode === 'area' ? 'Entire planetary surfaces and map areas as equal-area disks' : 'Actual mean planetary diameters and flat square map widths';
    q('#scale-svg-desc').textContent = layout.map(({ body }) => body.name + ': ' + number(mode === 'area' ? body.area : body.width, 2) + (mode === 'area' ? ' square kilometres' : ' kilometres')).join('; ') + '. All objects share one scale. Arrow keys pan; plus/minus zoom; Escape fits all.';
  }
  function changeSelection(ids) {
    visible = new Set(['voxelgame', ...ids]); fitAll(); refreshControls(); remember();
  }
  for (const body of bodies) {
    const button = document.createElement('button');
    button.type = 'button'; button.dataset.body = body.id; button.textContent = body.name;
    button.disabled = body.id === 'voxelgame';
    button.setAttribute('aria-label', body.name + (button.disabled ? ', always shown as the reference' : ', toggle visibility'));
    button.onclick = () => {
      const next = new Set(visible); if (next.has(body.id)) next.delete(body.id); else next.add(body.id);
      changeSelection([...next]);
    };
    selection.appendChild(button);
    const row = document.createElement('tr');
    row.dataset.body = body.id;
    if (body.id === 'voxelgame') row.className = 'reference-row';
    const name = document.createElement('th'); name.scope = 'row';
    const compare = document.createElement('button'); compare.type = 'button'; compare.textContent = body.name;
    compare.onclick = () => {
      changeSelection(['voxelgame', body.id]);
      focusControl.value = body.id;
      q('#comparison').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
      modeControl.focus({ preventScroll: true });
    };
    const link = document.createElement('a'); link.href = source(body); link.textContent = 'source';
    link.setAttribute('aria-label', body.name + ' measurement source');
    const kind = document.createElement('span'); kind.className = 'world-kind';
    kind.textContent = body.id === 'voxelgame' ? 'Theoretical square envelope' : body.kind === 'map' ? 'Maximum Java border · square' : body.kind === 'star' ? 'Mean diameter · sphere' : 'Mean diameter · sphere, no rings';
    name.append(compare, link, kind); row.appendChild(name);
    for (const value of [number(body.width, 3), number(body.area), number(world.area / body.area, 4) + '×']) {
      const cell = document.createElement('td'); cell.textContent = value; row.appendChild(cell);
    }
    q('#scale-table').appendChild(row);
  }
  function imageFor(body) {
    let node = imageNodes.get(body.id);
    if (node) return node;
    node = document.createElementNS(ns, 'image');
    node.setAttribute('href', 'images/scale/' + body.id + '.webp?v=natural-2');
    node.setAttribute('preserveAspectRatio', 'none');
    node.dataset.body = body.id;
    if (body.kind === 'map') node.setAttribute('class', 'game-map');
    node.addEventListener('error', () => {
      failures.add(body.id);
      q('#scale-status').textContent = 'Texture unavailable for ' + [...failures].map(id => byId.get(id).name).join(', ') + '. Size outlines remain accurate.';
    });
    const title = document.createElementNS(ns, 'title'); title.textContent = body.name; node.appendChild(title);
    imageNodes.set(body.id, node); return node;
  }
  function draw() {
    frame = 0;
    const oldBase = baseScale;
    width = svg.clientWidth; height = svg.clientHeight;
    if (!width || !height) return;
    buildLayout();
    if (!Number.isFinite(oldBase)) fitAll();
    svg.setAttribute('viewBox', '0 0 ' + width + ' ' + height);
    for (const id of ['#scale-frame', '#scale-grid-rect']) {
      q(id).setAttribute('width', width); q(id).setAttribute('height', height);
    }
    marks.replaceChildren(); labels.replaceChildren(); ruler.replaceChildren();
    const s = baseScale * zoom, cy = (height - 140) / 2 - cameraY * s;
    const candidates = [];
    for (const { body, x, d } of layout) {
      const cx = width / 2 + (x - cameraX) * s, r = d * s / 2;
      if (cx + r < 0 || cx - r > width || cy + r < 0 || cy - r > height) continue;
      const group = element('g', { 'data-object': body.id }, marks);
      const square = body.kind === 'map' && mode === 'width';
      const shape = square
        ? element('rect', { x: cx - r, y: cy - r, width: 2*r, height: 2*r }, group)
        : element('circle', { cx, cy, r }, group);
      shape.setAttribute('fill', body.id === 'voxelgame' ? '#6f987b' : '#87917c');
      // Circle clipping turns the original illustrative map into an equal-area disk.
      const clipId = 'body-clip-' + body.id;
      const clip = element('clipPath', { id: clipId }, group); clip.appendChild(shape.cloneNode());
      const image = imageFor(body);
      for (const [key, value] of Object.entries({ x:cx-r, y:cy-r, width:2*r, height:2*r, 'clip-path':'url(#'+clipId+')' })) image.setAttribute(key, String(value));
      group.appendChild(image);
      if (cx >= 5 && cx <= width-5 && cy+r < height-65 && cy+r > 0) candidates.push({ body, cx, y:cy+r });
    }
    // Text stays screen-sized; collision lanes avoid misrepresenting tiny bodies as larger.
    const lanes = Array(5).fill(-Infinity);
    for (const item of candidates.sort((a,b)=>a.cx-b.cx)) {
      const textWidth = item.body.name.length*7.4+12;
      const left = Math.max(8, Math.min(width-textWidth-8, item.cx-textWidth/2));
      const lane = lanes.findIndex(right => left >= right+9);
      if (lane < 0) continue; // Names always remain in the focus control and full table.
      lanes[lane] = left+textWidth;
      const y = Math.min(height-46, Math.max(cy+maxDiameter*s/2+22, item.y+22)+lane*19);
      element('path',{d:'M '+item.cx+' '+(item.y+3)+' L '+(left+textWidth/2)+' '+(y-12),class:'body-guide'},labels);
      element('text',{x:left+textWidth/2,y,'text-anchor':'middle',class:'body-label'},labels,item.body.name);
    }
    const targetKm = Math.min(110, width*.3)/s;
    const power = 10**Math.floor(Math.log10(targetKm));
    const lengthKm = [1,2,5,10].filter(value=>value*power<=targetKm).pop()*power;
    const sx=18, sy=height-18;
    element('path',{d:'M '+sx+' '+(sy-5)+' V '+sy+' H '+(sx+lengthKm*s)+' V '+(sy-5),fill:'none',stroke:'#edf0e3','stroke-width':1.5},ruler);
    element('text',{x:sx,y:sy-12},ruler,number(lengthKm,2)+' km'+(mode==='area'?' · equivalent disk':''));
    q('#scale-zoom').textContent=number(zoom,1)+'×';
  }
  function schedule() { if (!frame) frame=requestAnimationFrame(draw); }
  function zoomAt(factor, px=width/2, py=(height-140)/2) {
    const s=baseScale*zoom, next=Math.max(.25,Math.min(4000,zoom*factor));
    const newScale=baseScale*next;
    cameraX+=(px-width/2)*(1/s-1/newScale);
    cameraY+=(py-(height-140)/2)*(1/s-1/newScale);
    zoom=next; schedule();
  }
  q('#scale-in').onclick=()=>zoomAt(1.6);
  q('#scale-out').onclick=()=>zoomAt(1/1.6);
  q('#scale-fit').onclick=()=>{fitAll();refreshControls();};
  q('#scale-focus-go').onclick=()=>focus(focusControl.value);
  q('#scale-fullscreen').onclick=async()=>{
    try { if(document.fullscreenElement) await document.exitFullscreen(); else await q('#comparison').requestFullscreen(); }
    catch { q('#scale-status').textContent='Fullscreen is unavailable in this browser. Zoom and focus controls still work.'; }
  };
  document.addEventListener('fullscreenchange',()=>{q('#scale-fullscreen').textContent=document.fullscreenElement?'Collapse':'Expand';schedule();});
  if (!q('#comparison').requestFullscreen) q('#scale-fullscreen').hidden=true;
  modeControl.onchange=()=>{mode=modeControl.value;fitAll();refreshControls();remember();};
  document.querySelectorAll('[data-preset]').forEach(button=>button.onclick=()=>{
    const preset=button.dataset.preset;
    changeSelection(preset==='overview'?['sun','earth','minecraft']:preset==='games'?['earth','minecraft']:bodies.filter(b=>preset==='all'||b.kind==='planet').map(b=>b.id));
  });
  svg.addEventListener('wheel',event=>{
    event.preventDefault();const rect=svg.getBoundingClientRect();
    const delta=event.deltaY*(event.deltaMode===1?16:event.deltaMode===2?height:1);
    zoomAt(Math.exp(-Math.max(-150,Math.min(150,delta))*.005),event.clientX-rect.left,event.clientY-rect.top);
  },{passive:false});
  svg.addEventListener('keydown',event=>{
    if(['+','=','-','ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Escape'].includes(event.key))event.preventDefault();
    const step=50/(baseScale*zoom);
    if(event.key==='+'||event.key==='=')zoomAt(1.6);
    else if(event.key==='-')zoomAt(1/1.6);
    else if(event.key==='Escape')fitAll();
    else if(event.key==='ArrowLeft')cameraX-=step;
    else if(event.key==='ArrowRight')cameraX+=step;
    else if(event.key==='ArrowUp')cameraY-=step;
    else if(event.key==='ArrowDown')cameraY+=step;
    schedule();
  });
  svg.addEventListener('pointerdown',event=>{
    if(event.button!==0)return;
    svg.setPointerCapture(event.pointerId);pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
  });
  svg.addEventListener('pointermove',event=>{
    if(!pointers.has(event.pointerId))return;
    const old=pointers.get(event.pointerId),next={x:event.clientX,y:event.clientY};
    if(pointers.size===2){
      const other=[...pointers.entries()].find(([id])=>id!==event.pointerId)[1];
      const before=Math.hypot(old.x-other.x,old.y-other.y),after=Math.hypot(next.x-other.x,next.y-other.y);
      const rect=svg.getBoundingClientRect();
      if(before>2)zoomAt(after/before,(old.x+other.x)/2-rect.left,(old.y+other.y)/2-rect.top);
      cameraX-=(next.x-old.x)/(2*baseScale*zoom);cameraY-=(next.y-old.y)/(2*baseScale*zoom);
    }else{cameraX-=(next.x-old.x)/(baseScale*zoom);cameraY-=(next.y-old.y)/(baseScale*zoom);}
    pointers.set(event.pointerId,next);schedule();
  });
  ['pointerup','pointercancel','lostpointercapture'].forEach(type=>svg.addEventListener(type,event=>pointers.delete(event.pointerId)));
  // Image errors are reported; they must never silently change the true-scale geometry.
  width=svg.clientWidth;height=svg.clientHeight;fitAll();refreshControls();draw();
  new ResizeObserver(schedule).observe(svg);
})();
