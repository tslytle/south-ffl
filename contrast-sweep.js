/* ─────────────────────────────────────────────────────────────────────────────
   contrast-sweep.js — the ADR 0005 bar, measured rather than asserted.

   ADR 0005 fixed a floor: every text-bearing element on the page clears WCAG AA
   against its COMPOSITED background — alpha tints resolved against whatever is
   actually behind them — in both themes. This is the tool that checks it. It was
   rebuilt from scratch on 2026-08-12 because the original sweep wasn't kept, and
   it immediately found 396 real failures the first pass had never seen.

   ── Running it ──────────────────────────────────────────────────────────────
   Serve the file and open it in a browser (`python -m http.server 8765` from the
   repo root, then http://127.0.0.1:8765/index.html). Paste this whole file into
   the console, then:

       __runAll()                          // sweeps every route at the current theme+width

   Do that for each combination you care about. The minimum honest set is four:
   {375px, 1265px} x {dark, light}. Toggle with `document.getElementById('themetoggle').click()`
   and resize the actual viewport — not the zoom.

   ── Four traps, each of which produced a wrong answer before it was fixed ────

   1. ASSERT THE VIEWPORT. Below 761px the standings and ledger become a card
      layout with transparent cells, which is a genuinely different set of
      composited backgrounds — not a narrower version of the same one. The first
      run of this looked like a clean no-op purely because the window was still
      at 375px from an earlier check. `__runAll()` returns `w` for this reason:
      read it before believing the number next to it.

   2. RUN IT TWICE. Each pass expands the disclosures inside the view it is
      sweeping, so pass 1 measures ~21k elements and pass 2 — which inherits
      everything pass 1 opened — measures ~59k. The draft-pick lines that failed
      in 2026-08 only exist in the second population.

   3. `color(srgb r g b / a)` IS NOT `rgb()`. Chrome returns Color 4 syntax for
      some computed backgrounds (`.recjump` is one), with components in 0..1
      rather than 0..255. A naive number-scrape reads white as near-black and
      invents a failure. `parse()` below handles both.

   4. GRADIENTS CANNOT BE COMPOSITED STATICALLY. `backgroundColor` is transparent
      on a gradient-painted element, so the walk lands on the wrong ancestor and
      reports nonsense — the medal chips read 1.09 that way, when ADR 0005 in fact
      tuned them deliberately with `--on-metal`. Those elements are counted as
      `gradientSkipped` and excluded, NOT failed. If that count moves a lot,
      something started or stopped using a gradient and wants eyes on it.

   ── The baseline, 2026-08-12, after the day's six commits ───────────────────
       1265px dark  59,753 checked   0 failures
       1265px light 59,753 checked   0 failures
        375px dark  59,501 checked   0 failures   (396 before the fix in this commit)
        375px light 59,501 checked   0 failures
   Treat any non-zero as a regression, and check `gradientSkipped` (~245 dark,
   ~231 light) hasn't moved much either.
   ───────────────────────────────────────────────────────────────────────────── */

window.__sweep = (opts) => {
  const parse = c => {
    if (!c) return null;
    const m = c.match(/[\d.]+/g);
    if (!m) return null;
    const isColorFn = /^color\(/i.test(c.trim());   /* color(srgb r g b / a) — 0..1 */
    const k = isColorFn ? 255 : 1;
    return { r: +m[isColorFn ? 1 : 0] * k, g: +m[isColorFn ? 2 : 1] * k,
             b: +m[isColorFn ? 3 : 2] * k,
             a: m.length > (isColorFn ? 4 : 3) ? +m[isColorFn ? 4 : 3] : 1 };
  };
  const over = (f, b) => ({ r: f.r * f.a + b.r * (1 - f.a), g: f.g * f.a + b.g * (1 - f.a),
                            b: f.b * f.a + b.b * (1 - f.a), a: 1 });
  const lum = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return .2126 * f(c.r) + .7152 * f(c.g) + .0722 * f(c.b); };
  const ratio = (a, b) => { const L1 = lum(a), L2 = lum(b);
    return (Math.max(L1, L2) + .05) / (Math.min(L1, L2) + .05); };

  /* walk up stacking alpha layers until something opaque stops it */
  const bgOf = el => {
    const stack = []; let n = el, img = false;
    while (n && n.nodeType === 1) {
      const cs = getComputedStyle(n);
      if (cs.backgroundImage && cs.backgroundImage !== 'none') img = true;
      const c = parse(cs.backgroundColor);
      if (c && c.a > 0) { stack.push(c); if (c.a >= 1) break; }
      n = n.parentElement;
    }
    if (!stack.length) return { bg: { r: 255, g: 255, b: 255, a: 1 }, img };
    let acc = stack[stack.length - 1];
    for (let i = stack.length - 2; i >= 0; i--) acc = over(stack[i], acc);
    return { bg: acc, img };
  };
  const sel = el => {
    let s = el.tagName.toLowerCase();
    if (el.className && typeof el.className === 'string')
      s += '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.');
    return s;
  };

  const seen = {}; let checked = 0, grad = 0, failCount = 0;
  document.querySelectorAll('body *').forEach(el => {
    if (!el.offsetParent && getComputedStyle(el).position !== 'fixed') return;   /* visible only */
    const txt = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('');
    if (!txt) return;                                    /* own text, not a container's */
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.opacity === '0') return;
    const fg = parse(cs.color); if (!fg) return;
    const { bg, img } = bgOf(el);
    checked++;
    if (img) { grad++; return; }                          /* trap 4 */
    const size = parseFloat(cs.fontSize), bold = +cs.fontWeight >= 700;
    const need = (size >= 24 || (size >= 18.66 && bold)) ? 3 : 4.5;   /* AA, large-text rule */
    const r = +ratio(fg, bg).toFixed(2);
    if (r < need) {
      failCount++;
      const k = sel(el);
      if (!seen[k] || seen[k].r > r) seen[k] = { r, need, txt: txt.slice(0, 20) };
    }
  });
  return { view: opts && opts.view, checked, gradientSkipped: grad, failCount,
           worst: Object.entries(seen).sort((a, b) => a[1].r - b[1].r).slice(0, 12) };
};

window.__runAll = () => {
  const theme = document.documentElement.getAttribute('data-theme') || '?';
  const views = [...document.querySelectorAll('section.uroute')].map(s => s.id);
  const res = [];
  const back = document.getElementById('uback'); if (back) back.click();     /* the hub route */
  res.push(window.__sweep({ view: 'hub' }));
  views.forEach(id => {
    const a = document.querySelector('a[href="#' + id + '"]'); if (a) a.click();
    document.querySelectorAll('section.uroute.uactive details').forEach(d => d.open = true);
    res.push(window.__sweep({ view: id }));
  });
  return {
    theme, w: innerWidth,                                  /* trap 1: always read w */
    checked: res.reduce((n, r) => n + r.checked, 0),
    fails: res.reduce((n, r) => n + r.failCount, 0),
    gradientSkipped: res.reduce((n, r) => n + r.gradientSkipped, 0),
    perView: res.map(r => [r.view, r.checked, r.failCount]),
    worst: res.flatMap(r => r.worst.map(w => [r.view, w[0], w[1].r, w[1].need, w[1].txt]))
              .sort((a, b) => a[2] - b[2]).slice(0, 12)
  };
};
