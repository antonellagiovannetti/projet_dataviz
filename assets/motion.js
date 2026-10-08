/* Route motion follows committed Dash content, never chart/filter mutations. */
(() => {
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const mobile = window.matchMedia('(max-width:740px)');
  let body, nav, indicator, routes = [], displayedPage = null;
  let entryTimer, recoveryTimer, resizeFrame;

  function currentPage() {
    const hash = window.location.hash.slice(1);
    return routes.includes(hash) ? hash : 'overview';
  }

  function currentChapter() {
    return body?.querySelector(':scope > .chapter-content');
  }

  function clearMotion() {
    window.clearTimeout(entryTimer);
    window.clearTimeout(recoveryTimer);
    currentChapter()?.classList.remove('chapter-entering', 'chapter-leaving');
  }

  function moveIndicator(page, reveal = false) {
    const link = document.getElementById(`nav-${page}`);
    if (!nav || !indicator || !link) return;
    const inset = 10;
    indicator.style.width = `${Math.max(0, link.offsetWidth - 2 * inset)}px`;
    indicator.style.transform = `translateX(${link.offsetLeft + inset}px)`;
    nav.classList.add('has-moving-indicator');
    // Scroll only the horizontal menu; never move the document to the header.
    if (reveal && nav.scrollWidth > nav.clientWidth) {
      const left = link.offsetLeft;
      if (left < nav.scrollLeft || left + link.offsetWidth > nav.scrollLeft + nav.clientWidth) {
        nav.scrollTo({left: Math.max(0, left - (nav.clientWidth - link.offsetWidth) / 2),
                      behavior: reducedMotion.matches ? 'instant' : 'smooth'});
      }
    }
  }

  function chapterCommitted() {
    const chapter = currentChapter();
    const page = chapter?.dataset.chapter;
    if (!page || page !== currentPage()) return;
    moveIndicator(page);
    if (page === displayedPage) return; // Filters and glossary search stay still.
    const previousPage = displayedPage;
    clearMotion();
    displayedPage = page;
    if (previousPage && !reducedMotion.matches) {
      const direction = routes.indexOf(page) >= routes.indexOf(previousPage) ? 1 : -1;
      chapter.style.setProperty('--chapter-enter-x', `${direction * (mobile.matches ? 12 : 20)}px`);
      chapter.classList.add('chapter-entering');
      entryTimer = window.setTimeout(() => chapter.classList.remove('chapter-entering'), 460);
    }
  }

  window.addEventListener('hashchange', () => {
    if (window.location.hash === '#main-content') return;
    const page = currentPage();
    clearMotion(); // A rapid click or Back cancels the previous route's effects.
    moveIndicator(page, true);
    if (page === displayedPage) return;
    // The new chapter starts at the top, while its own entrance supplies motion.
    window.scrollTo({top: 0, behavior: 'instant'});
    const chapter = currentChapter();
    if (chapter && !reducedMotion.matches) {
      const direction = routes.indexOf(page) >= routes.indexOf(displayedPage) ? 1 : -1;
      chapter.style.setProperty('--chapter-exit-x', `${-direction * (mobile.matches ? 6 : 10)}px`);
      chapter.classList.add('chapter-leaving');
      // Leave readable content if a server request is slow or fails.
      recoveryTimer = window.setTimeout(() => chapter.classList.remove('chapter-leaving'), 1200);
    }
    chapterCommitted(); // Also handles a cached/very fast render before hashchange.
  });

  function initialize() {
    const drawer = document.querySelector('.filter-drawer');
    if (drawer && !drawer.dataset.initialized) {
      drawer.open = !mobile.matches;
      drawer.dataset.initialized = 'true';
    }
    if (!body) {
      body = document.getElementById('page-body');
      if (body) {
        nav = document.querySelector('.topbar nav');
        indicator = document.getElementById('nav-indicator');
        routes = Array.from(nav.querySelectorAll('.nav-link'), link => link.hash.slice(1));
        // The keyed chapter wrapper changes only when the route changes.
        new MutationObserver(chapterCommitted).observe(body, {childList: true});
        new ResizeObserver(() => {
          window.cancelAnimationFrame(resizeFrame);
          resizeFrame = window.requestAnimationFrame(() => moveIndicator(currentPage()));
        }).observe(nav);
        chapterCommitted();
      }
    }
    if (body && drawer) bootstrap.disconnect();
  }

  const bootstrap = new MutationObserver(initialize);
  // Plotly needs a fresh width after a previously hidden analysis is revealed.
  document.addEventListener('toggle', event => {
    if (event.target.matches?.('.exploration-section') && event.target.open) {
      window.requestAnimationFrame(() => window.dispatchEvent(new Event('resize')));
    }
  }, true);
  bootstrap.observe(document.documentElement, {childList: true, subtree: true});
  initialize();
  mobile.addEventListener('change', event => {
    const drawer = document.querySelector('.filter-drawer');
    if (drawer) drawer.open = !event.matches;
  });
  reducedMotion.addEventListener('change', () => {
    clearMotion();
    moveIndicator(currentPage());
  });
})();
