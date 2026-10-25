/* Adapt Plotly labels to their panel width; all rates and cohorts stay server-owned. */
(() => {
  const states = new WeakMap();
  const categoryPrefix = 'compact-clinical-category-';
  const copy = value => JSON.parse(JSON.stringify(value));

  function wrapNote(text, columns) {
    const words = String(text).replace(/<br\s*\/?\s*>/gi, ' ').trim().split(/[ \t]+/);
    const lines = [];
    let line = '';
    for (const word of words) {
      if (line && (line + ' ' + word).replace(/<[^>]*>/g, '').length > columns) {
        lines.push(line);
        line = word;
      } else {
        line += (line ? ' ' : '') + word;
      }
    }
    if (line) lines.push(line);
    return lines;
  }

  function desiredLayout(graph, width, clinical) {
    const layout = graph.layout;
    const annotations = copy(layout.annotations || [])
      .filter(item => !String(item.name || '').startsWith(categoryPrefix));
    const patch = {};

    if (clinical && graph.data.length === 2) {
      const narrow = width < 540;
      patch['margin.l'] = narrow ? 12 : 150;
      patch['margin.r'] = 12;
      patch['margin.t'] = narrow ? 40 : 24;
      patch['margin.b'] = 40;
      patch['xaxis.domain'] = narrow ? [0, .48] : [0, .40];
      patch['yaxis.showticklabels'] = !narrow;
      for (const item of annotations) {
        const profile = String(item.text).startsWith('●');
        const remainder = String(item.text).startsWith('◆');
        if (profile || remainder) {
          const row = Math.round(item.y);
          item.x = narrow ? .55 : (profile ? .46 : .75);
          item.y = row + (narrow ? (profile ? -.15 : .15) : 0);
        } else if (String(item.text).startsWith('Effectifs :')) {
          item.x = narrow ? .55 : .46;
          item.y = 0;
          item.yshift = -28;
          item.yref = 'paper';
          item.yanchor = 'top';
        }
      }
      if (narrow) {
        (layout.yaxis.ticktext || []).forEach((label, row) => {
          annotations.push({
            name: categoryPrefix + row, text: label, x: 0, y: row - .40,
            xref: 'paper', yref: 'y', xanchor: 'left', yanchor: 'middle',
            showarrow: false, font: {size: 10, color: '#182c47'},
          });
        });
      }
    } else {
      const usefulWidth = Math.max(100, width - (layout.margin?.l || 55) - (layout.margin?.r || 16));
      let top = 22;
      let hasNote = false;
      for (const item of annotations) {
        if (item.yref !== 'paper' || !(item.y > 1)) continue;
        hasNote = true;
        const size = item.font?.size || 9;
        const lines = wrapNote(item.text, Math.max(16, Math.floor(usefulWidth / (size * .55))));
        item.text = lines.join('<br>');
        item.y = 1.025;
        item.yanchor = 'bottom';
        top = Math.max(top, lines.length * (size + 2) + 10);
      }
      if (hasNote) patch['margin.t'] = top;
    }
    patch.annotations = annotations;
    return patch;
  }

  function adapt(wrapper, state) {
    state.pending = false;
    if (state.running || !wrapper.isConnected || !window.Plotly) return;
    const graph = wrapper.querySelector('.js-plotly-plot');
    if (!graph || !graph.layout || !graph.data) return;
    if (state.graph !== graph && typeof graph.on === 'function') {
      state.graph = graph;
      graph.on('plotly_afterplot', () => schedule(wrapper, state));
    }
    const width = wrapper.getBoundingClientRect().width;
    // Hidden tabs and empty-state figures must retain their own layout.
    if (width < 1 || !graph.data.length) return;
    const desired = desiredLayout(graph, width, wrapper.id === 'compact-profile-clinical');
    const patch = {};
    for (const [key, value] of Object.entries(desired)) {
      const current = key.split('.').reduce((object, part) => object?.[part], graph.layout);
      if (JSON.stringify(current) !== JSON.stringify(value)) patch[key] = value;
    }
    if (!Object.keys(patch).length) return;
    state.running = true;
    Promise.resolve(window.Plotly.relayout(graph, patch)).finally(() => {
      state.running = false;
    });
  }

  function schedule(wrapper, state) {
    if (state.pending || state.running) return;
    state.pending = true;
    window.requestAnimationFrame(() => adapt(wrapper, state));
  }

  function watch(wrapper) {
    let state = states.get(wrapper);
    if (!state) {
      state = {pending: false, running: false, graph: null};
      states.set(wrapper, state);
      new ResizeObserver(() => schedule(wrapper, state)).observe(wrapper);
    }
    schedule(wrapper, state);
  }

  function start(app) {
    app.querySelectorAll('.compact-graph').forEach(watch);
    // Only discover/refresh graph containers; never rescan the document on Plotly mutations.
    new MutationObserver(mutations => {
      const wrappers = new Set();
      for (const mutation of mutations) {
        const owner = mutation.target.closest?.('.compact-graph');
        if (owner) wrappers.add(owner);
        for (const node of mutation.addedNodes) {
          if (!(node instanceof Element)) continue;
          if (node.matches('.compact-graph')) wrappers.add(node);
          node.querySelectorAll('.compact-graph').forEach(wrapper => wrappers.add(wrapper));
        }
      }
      wrappers.forEach(watch);
    }).observe(app, {childList: true, subtree: true});
  }

  function bootstrap() {
    const root = document.getElementById('react-entry-point');
    if (!root) return;
    const app = root.querySelector('.compact-app');
    if (app) return start(app);
    const observer = new MutationObserver(() => {
      const mounted = root.querySelector('.compact-app');
      if (mounted) {
        observer.disconnect();
        start(mounted);
      }
    });
    observer.observe(root, {childList: true, subtree: true});
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bootstrap, {once: true});
  else bootstrap();
})();
