'use strict';

(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const heroVideo = $('#hero-video');
  const heroToggle = $('#hero-toggle');
  const galleryVideo = $('#gallery-video');
  const dialog = $('#image-dialog');
  let activeScene = -1;
  let scenes = [];
  let lastImageTrigger = null;
  let heroPausedByVisitor = true;

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  function numeric(value) {
    return value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value));
  }

  function format(value, digits = 2) {
    return numeric(value) ? Number(value).toFixed(digits) : '—';
  }

  function safeMediaPath(value) {
    if (typeof value !== 'string') return '';
    const path = value.trim();
    return /^assets\/[\w./%+() -]+$/i.test(path) && !path.includes('..') ? path : '';
  }

  function updateHeroButton() {
    const paused = heroVideo.paused;
    $('.toggle-icon', heroToggle).textContent = paused ? '▶' : 'Ⅱ';
    $('.toggle-label', heroToggle).textContent = paused ? 'Play' : 'Pause';
    heroToggle.setAttribute('aria-label', `${paused ? 'Play' : 'Pause'} project introduction`);
  }

  heroToggle.addEventListener('click', () => {
    if (heroVideo.paused) {
      heroPausedByVisitor = false;
      heroVideo.play().catch(updateHeroButton);
    } else {
      heroPausedByVisitor = true;
      heroVideo.pause();
    }
  });
  heroVideo.addEventListener('play', updateHeroButton);
  heroVideo.addEventListener('pause', updateHeroButton);
  document.addEventListener('play', event => {
    if (event.target instanceof HTMLVideoElement) $$('video').forEach(video => { if (video !== event.target) video.pause(); });
  }, true);

  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) heroVideo.pause();
        else if (!reducedMotion.matches && !heroPausedByVisitor && galleryVideo.paused && heroVideo.getAttribute('src')) heroVideo.play().catch(updateHeroButton);
      });
    }, { threshold: .2 }).observe(heroVideo);
  }
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      heroVideo.pause();
      galleryVideo.pause();
    }
  });
  reducedMotion.addEventListener('change', event => {
    if (event.matches) heroVideo.pause();
  });

  function bindTabKeyboard(list, onSelect) {
    list.addEventListener('keydown', event => {
      const tabs = $$('[role="tab"]', list);
      const index = tabs.indexOf(document.activeElement);
      if (index < 0) return;
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      else if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = tabs.length - 1;
      else return;
      event.preventDefault();
      tabs[next].focus();
      onSelect(tabs[next], next);
    });
  }

  function selectResult(tab) {
    $$('.result-tab').forEach(item => {
      const selected = item === tab;
      item.setAttribute('aria-selected', selected);
      item.tabIndex = selected ? 0 : -1;
      item.classList.toggle('active', selected);
      $(`#${item.getAttribute('aria-controls')}`).hidden = !selected;
    });
  }
  $$('.result-tab').forEach(tab => tab.addEventListener('click', () => selectResult(tab)));
  bindTabKeyboard($('.result-tabs'), selectResult);

  function openImage(trigger) {
    const src = safeMediaPath(trigger.dataset.image);
    if (!src) return;
    lastImageTrigger = trigger;
    $('#dialog-image').src = src;
    $('#dialog-image').alt = trigger.dataset.title || 'DriveTTO visualization';
    $('#dialog-title').textContent = trigger.dataset.title || 'DriveTTO visualization';
    $('#dialog-description').textContent = trigger.dataset.description || '';
    dialog.showModal();
    document.body.style.overflow = 'hidden';
    $('#dialog-close').focus();
  }
  document.addEventListener('click', event => {
    const trigger = event.target.closest('.image-expand');
    if (trigger) openImage(trigger);
  });
  $('#dialog-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
  });
  dialog.addEventListener('close', () => {
    document.body.style.overflow = '';
    if (lastImageTrigger) lastImageTrigger.focus();
  });

  function sceneSummary(scene) {
    const duration = numeric(scene.duration) ? `${Number(scene.duration)} s` : scene.duration;
    return [scene.dataset || 'HUGSIM', scene.difficulty, duration,
      `RC ${format(scene.rc, 1)}`, `HD ${format(scene.hd, 1)}`].filter(Boolean).join(' · ');
  }

  function selectScene(index) {
    if (index === activeScene || !scenes[index]) return;
    activeScene = index;
    const scene = scenes[index];
    galleryVideo.pause();
    galleryVideo.src = safeMediaPath(scene.src);
    const poster = safeMediaPath(scene.poster);
    if (poster) galleryVideo.poster = poster;
    else galleryVideo.removeAttribute('poster');
    galleryVideo.setAttribute('aria-label', sceneSummary(scene));
    galleryVideo.load();
    $('#gallery-empty').hidden = true;
    $('#scene-summary').textContent = sceneSummary(scene);
    $$('.scene-tab').forEach((tab, tabIndex) => {
      const selected = tabIndex === index;
      tab.setAttribute('aria-selected', selected);
      tab.tabIndex = selected ? 0 : -1;
    });
    $('#scene-panel').setAttribute('aria-labelledby', `scene-tab-${index}`);
  }

  function renderVideos(videos) {
    scenes = Array.isArray(videos) ? videos.filter(scene => safeMediaPath(scene.src)) : [];
    const tabs = $('#scene-selectors');
    if (!scenes.length) {
      $('#gallery-empty').textContent = 'No driving scenes are available.';
      return;
    }
    tabs.replaceChildren();
    scenes.forEach((scene, index) => {
      const tab = element('button', 'scene-tab');
      tab.type = 'button';
      tab.id = `scene-tab-${index}`;
      tab.setAttribute('role', 'tab');
      tab.setAttribute('aria-selected', 'false');
      tab.setAttribute('aria-controls', 'scene-panel');
      tab.tabIndex = -1;
      const thumb = element('div', 'scene-thumb');
      const poster = safeMediaPath(scene.poster);
      if (poster) {
        const image = element('img');
        image.src = poster;
        image.alt = '';
        image.loading = 'lazy';
        thumb.append(image);
      }
      tab.append(thumb, element('em', 'scene-tab-caption', sceneSummary(scene)));
      tab.addEventListener('click', () => selectScene(index));
      tabs.append(tab);
    });
    bindTabKeyboard(tabs, (_, index) => selectScene(index));
    selectScene(0);
  }

  function renderIntroduction(intro) {
    if (!intro || !safeMediaPath(intro.src)) return;
    heroVideo.poster = safeMediaPath(intro.poster);
    const src = safeMediaPath(intro.src);
    if (heroVideo.getAttribute('src') !== src) heroVideo.src = src;
    heroVideo.muted = false;
    heroToggle.disabled = false;
  }

  function renderImages(images) {
    const root = $('#image-grid');
    root.replaceChildren();
    (Array.isArray(images) ? images : []).forEach((item, index) => {
      const src = safeMediaPath(item.src);
      if (!src) return;
      const title = item.title || `Planning example ${String(index + 1).padStart(2, '0')}`;
      const figure = element('figure', 'planning-figure');
      const button = element('button', 'image-expand');
      button.type = 'button';
      button.dataset.image = src;
      button.dataset.title = title;
      button.dataset.description = item.description || '';
      button.setAttribute('aria-label', `Enlarge ${title}`);
      const img = element('img');
      img.src = src;
      img.alt = item.description || title;
      img.loading = 'lazy';
      const indicator = element('span', 'expand-indicator', '↗');
      indicator.setAttribute('aria-hidden', 'true');
      button.append(img, indicator);
      const caption = element('figcaption');
      const top = element('div', 'image-caption-top');
      top.append(element('h3', '', title));
      if (numeric(item.score)) top.append(element('span', 'image-score', `${item.scoreLabel || 'PDMS'} ${format(item.score)}`));
      caption.append(top);
      if (item.description) caption.append(element('p', '', item.description));
      if (item.token) caption.append(element('span', 'image-token', `Token: ${item.token}`));
      const bev = safeMediaPath(item.bev);
      if (bev) {
        const views = element('div', 'image-view-controls');
        views.setAttribute('role', 'group');
        views.setAttribute('aria-label', `Image view for ${title}`);
        [['Front view', src], ["Bird’s-eye view", bev]].forEach(([label, path], viewIndex) => {
          const view = element('button', 'image-view-button', label);
          view.type = 'button';
          view.setAttribute('aria-pressed', viewIndex === 0 ? 'true' : 'false');
          view.addEventListener('click', () => {
            $$('button', views).forEach(item => item.setAttribute('aria-pressed', item === view ? 'true' : 'false'));
            img.src = path;
            img.alt = `${title}: ${label}. ${item.description || ''}`;
            button.dataset.image = path;
            button.dataset.title = `${title} · ${label}`;
            button.setAttribute('aria-label', `Enlarge ${title}: ${label}`);
          });
          views.append(view);
        });
        figure.append(views);
      }
      figure.append(button, caption);
      root.append(figure);
    });
    if (!root.children.length) root.append(element('p', 'loading-message', 'No planning visualizations are available.'));
  }

  function makeTable(rootSelector, headers, rows, rowBuilder, isFeatured) {
    const root = $(rootSelector);
    root.replaceChildren();
    if (!Array.isArray(rows) || !rows.length) {
      root.append(element('p', 'loading-message', 'No results are available for this setting.'));
      return;
    }
    const table = element('table');
    const thead = element('thead');
    const headRow = element('tr');
    headers.forEach(label => {
      const cell = element('th', '', label);
      cell.scope = 'col';
      headRow.append(cell);
    });
    thead.append(headRow);
    const tbody = element('tbody');
    rows.forEach(row => {
      const featured = isFeatured ? isFeatured(row) : false;
      const tr = element('tr', featured ? 'featured' : '');
      rowBuilder(row).forEach((value, index) => {
        const cell = element(index === 0 ? 'th' : 'td', '', value);
        if (index === 0) cell.scope = 'row';
        tr.append(cell);
      });
      tbody.append(tr);
    });
    table.append(thead, tbody);
    root.append(table);
  }

  function renderStageTable(rows, keys) {
    const root = $('#paper-navsim-table');
    root.replaceChildren();
    const table = element('table', 'component-table stage-table');
    const thead = element('thead');
    const headings = element('tr');
    ['Method', 'Stage', ...keys, 'EPDMS ↑'].forEach(label => {
      const th = element('th', '', label); th.scope = 'col'; headings.append(th);
    });
    thead.append(headings); table.append(thead);
    const tbody = element('tbody');
    rows.forEach(row => ['S1', 'S2'].forEach((stage, index) => {
      const tr = element('tr', `${row.method === 'DriveTTO' ? 'featured ' : ''}${index === 0 ? 'stage-start' : ''}`);
      if (index === 0) {
        const method = element('th', '', row.method); method.scope = 'rowgroup'; method.rowSpan = 2; tr.append(method);
      }
      tr.append(element('td', 'stage-label', stage));
      keys.forEach(key => tr.append(element('td', '', format(row.stages?.[stage]?.[key], 1))));
      if (index === 0) { const score = element('td', 'aggregate-cell', format(row.score, 1)); score.rowSpan = 2; tr.append(score); }
      tbody.append(tr);
    }));
    table.append(tbody); root.append(table);
  }

  function renderDifficultyTable(rows) {
    const root = $('#paper-hugsim-table'); root.replaceChildren();
    const table = element('table', 'component-table difficulty-table');
    const thead = element('thead'); const groups = element('tr');
    const method = element('th', '', 'Method'); method.rowSpan = 2; method.scope = 'col'; groups.append(method);
    ['RC ↑', 'HD-Score ↑'].forEach(label => { const th = element('th', 'metric-group', label); th.colSpan = 5; th.scope = 'colgroup'; groups.append(th); });
    const levels = element('tr');
    for (let group = 0; group < 2; group++) ['Easy', 'Medium', 'Hard', 'Extreme', 'Avg.'].forEach(label => {
      const th = element('th', label === 'Avg.' ? 'aggregate-cell' : '', label); th.scope = 'col'; levels.append(th);
    });
    thead.append(groups, levels); table.append(thead); const tbody = element('tbody');
    rows.forEach(row => {
      const tr = element('tr', row.method === 'DriveTTO' ? 'featured' : '');
      const th = element('th', '', row.method); th.scope = 'row'; tr.append(th);
      for (const metric of ['rc', 'hd']) {
        ['Easy', 'Medium', 'Hard', 'Extreme'].forEach(level => tr.append(element('td', '', format(row[`${metric}_breakdown`]?.[level], 1))));
        tr.append(element('td', 'aggregate-cell', format(row[metric], 1)));
      }
      tbody.append(tr);
    });
    table.append(tbody); root.append(table);
  }

  function renderResults(benchmarks = {}) {
    const navtest = Array.isArray(benchmarks.navtest) ? benchmarks.navtest : [];
    const native = navtest.find(row => /native/i.test(row.method));
    makeTable('#navtest-table', ['Method', 'PDMS ↑', 'Δ vs. native', 'p50 latency (s) ↓'], navtest, row => {
      const delta = native && numeric(native.score) && numeric(row.score) ? Number(row.score) - Number(native.score) : null;
      return [row.method, format(row.score, 4), delta === null ? '—' : `${delta > 0 ? '+' : ''}${format(delta, 4)}`, format(row.p50, 4)];
    }, row => /full/i.test(row.method));
    makeTable('#hugsim-table', ['Method / configuration', 'RC ↑', 'HD-Score ↑'], benchmarks.hugsim, row => [row.method, format(row.rc), format(row.hd)], row => /v4|DriveTTO/i.test(row.method));
    const paper = benchmarks.paper || {};
    const notes = {
      pdms: '12,146 NAVTEST scenes · NAVSIM-v1. DriveTTO’s paper value is rounded from the single-run benchmark (95.5437). AutoVLA (oracle 6) uses oracle selection over six samples.',
      navtest_epdms: '12,146 NAVTEST scenes · NAVSIM-v2 updated evaluation. DriveTTO uses the NAV2 checkpoint and shorter search schedule. Values follow the manuscript’s referenced updated-evaluation records.',
      navhard_epdms: '5,912 NAVHARD scenes · official 225-group two-stage product aggregation. Standard-input configuration. The separate 58.6 pair-history setting is not included here.'
    };
    function showBenchmark(key) {
      const keys = key === 'pdms' ? ['NC', 'DAC', 'TTC', 'Comf.', 'EP'] : ['NC', 'DAC', 'DDC', 'TL', 'EP', 'TTC', 'LK', 'HC', 'EC'];
      if (key === 'navhard_epdms') renderStageTable(paper[key], keys);
      else {
        makeTable('#paper-navsim-table', ['Method', ...keys, key === 'pdms' ? 'PDMS ↑' : 'EPDMS ↑'], paper[key], row => [row.method, ...keys.map(k => format(row.components?.[k], 1)), format(row.score, 1)], row => row.method === 'DriveTTO');
        $('#paper-navsim-table table').classList.add('component-table');
      }
      $('#paper-protocol').textContent = notes[key];
      $('#component-legend').textContent = key === 'pdms'
        ? 'NC: no-at-fault collision · DAC: drivable-area compliance · TTC: time-to-collision · Comf.: comfort · EP: ego progress. All columns: higher is better.'
        : 'NC: no-at-fault collision · DAC: drivable-area compliance · DDC: driving-direction compliance · TL: traffic-light compliance · EP: ego progress · TTC: time-to-collision · LK: lane keeping · HC: history comfort · EC: extended comfort. All columns: higher is better.';
      $$('.benchmark-switch button').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.benchmark === key)));
    }
    $$('.benchmark-switch button').forEach(button => button.addEventListener('click', () => showBenchmark(button.dataset.benchmark)));
    showBenchmark('pdms');
    renderDifficultyTable(paper.hugsim);
    const transfer = benchmarks.transfer || {};
    ['navtest', 'navhard'].forEach(benchmark => {
      makeTable(`#transfer-${benchmark}-table`, ['Base planner', 'Native ↑', 'ToAD ↑', 'DriveTTO-S ↑', 'Δ vs. Native', 'Δ vs. ToAD'], transfer[benchmark], row => [row.method, format(row.native, 4), format(row.toad, 4), format(row.drive, 4), `${row.drive >= row.native ? '+' : ''}${format(row.drive-row.native, 4)}`, `${row.drive >= row.toad ? '+' : ''}${format(row.drive-row.toad, 4)}`]);
    });
  }

  async function init() {
    try {
      const response = await fetch('assets/data/site-data.json');
      if (!response.ok) throw new Error(`Data request failed (${response.status})`);
      const data = await response.json();
      renderVideos(data.videos);
      renderIntroduction(data.intro);
      renderImages(data.images);
      renderResults(data.benchmarks);
      const overview = safeMediaPath(data.method && data.method.overview);
      if (overview) {
        $('#method-image').src = overview;
        $('.method-expand').dataset.image = overview;
        $('#method-download').href = overview;
      }
      if (data.links && typeof data.links.code === 'string' && /^https:\/\/github\.com\//.test(data.links.code)) {
        $$('a[href="https://github.com/Rtwotwo/DriveTTO"]').forEach(link => { link.href = data.links.code; });
      }
    } catch (error) {
      const status = $('#data-status');
      status.hidden = false;
      status.textContent = 'The media and benchmark data could not be loaded. Please reload this page. The results CSV is also available in Resources.';
      $('#gallery-empty').textContent = 'The scene collection could not be loaded.';
      $$('.loading-message').forEach(message => { message.textContent = 'Data could not be loaded.'; });
      console.error('DriveTTO page data:', error);
    }
  }
  init();
})();
