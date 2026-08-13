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

   If you cannot resize the viewport — an automated browser often reports success
   while `window.innerWidth` stays put, which silently makes every "phone" run a
   desktop one — use a same-origin iframe instead. Media queries inside an iframe
   evaluate against the IFRAME's width, so this is a real 375px measurement:

       const f = document.createElement('iframe');
       f.src = '/index.html'; f.width = 375; f.height = 740;
       document.body.appendChild(f);
       // then inject this file into f.contentDocument and call
       // f.contentWindow.__runAll()

   Whichever route you take, WAIT FOR THE STATE TO SETTLE before believing a
   number. Theme toggles, routing and lazy boards all land a beat after the click,
   and reads taken mid-flight have produced confident nonsense more than once —
   a "dark" page measured while still light, a 217,391px document that collapses
   to 2,282px once routing applies.

   ── Seven traps, each of which produced a wrong answer before it was fixed ───

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

   5. A POPULATION THIS CANNOT REACH IS NOT A POPULATION THAT PASSES. Twice now
      the honest-looking zero was just an unswept surface: first the phone card
      layout (396 failures), then the manager profile modal, which is not on any
      route and only exists after a card is clicked. It held real failures for its
      whole life. `__runAll` opens one profile now — but the lesson generalises to
      anything reached only by interaction. If you add such a surface, add it here.

   6. `bgOf` WALKS DOM ANCESTORS, WHICH IS NOT ALWAYS WHAT IS PAINTED BEHIND. For
      an absolutely- or fixed-positioned element the visual backdrop can be a
      SIBLING. `.pfclose` floats over `.pfmask`, a 55% black scrim, but its DOM
      parent is the light card — so this reported 1.06 where the real ratio was
      ~3.9. Still a failure, so the fix was real, but the NUMBER was fiction.
      Treat any implausible extreme on a positioned element as suspect and check
      it by hand before chasing it.

   7. PSEUDO-ELEMENTS ARE NOT IN THIS POPULATION AT ALL, and two of them were
      failing. The scan reads element TEXT NODES; `::before`, `::after` and
      `::placeholder` have none, so nothing they render is ever measured. The
      whole file contains exactly two that draw text and set a colour, and both
      were below AA when finally checked by hand: `#searchinput::placeholder`
      (4.17) and the standings/ledger card stat labels, `td[data-l]::before`
      (3.93 in dark). Both fixed 2026-08-12. **If you add a pseudo-element that
      renders text, measure it by hand — this tool will report zero either way.**
      The enumerating query is: rules whose selector matches `::(before|after|
      placeholder)` and whose body sets `color` with a non-empty `content`.

   ── The baseline, end of 2026-08-12, after the visual polish pass ───────────
   Two passes per combination, profile-modal included:
       2048px dark  23,842 checked   0 failures
       2048px light 62,048 checked   0 failures
        375px dark  23,578 checked   0 failures
        375px light 61,784 checked   0 failures

   The dark/light counts differ by design, not by accident: light was measured
   second in each pair, so it inherits every disclosure the dark run opened —
   that is trap 2 doing its job, not a discrepancy to chase.

   The bar is zero, in all four. Treat any non-zero as a regression.

   `gradientSkipped` sits at 325 (2048px dark). Watch it as well as the failure
   count: it is the number of elements this tool declined to judge, so a jump
   means something started painting a gradient and quietly left the sweep's
   coverage — the same class of blind spot as trap 5, arriving by a different
   door.

   These supersede the earlier 59,753 / 59,501 figures, which predate both the
   profile-modal sweep and the color(srgb …) parser fix and are not comparable.
   ───────────────────────────────────────────────────────────────────────────── */

window.__sweep = (opts) => {
  const parse = c => {
    if (!c) return null;
    const isColorFn = /^color\(/i.test(c.trim());   /* color(srgb r g b / a) — 0..1 */
    /* Drop the colour-space keyword before scraping numbers. Scraping the whole
       string and then skipping one number is what the first version did, and it
       was wrong twice over: `srgb` contains no digit, so nothing was there to
       skip — r took g's value, b took the ALPHA, and alpha fell back to 1. The
       .recjump bar, at color(srgb .07 .09 .157 / .92), measured as a saturated
       rgb(24,40,235); every ratio computed against it was fiction. (Skipping one
       would have been right only for a space whose name ends in a digit, e.g.
       display-p3 — hence the trap. Removing the keyword handles both.) */
    const body = isColorFn ? c.trim().replace(/^color\(\s*[\w-]+/i, '') : c;
    const m = body.match(/[\d.]+/g);
    if (!m || m.length < 3) return null;
    const k = isColorFn ? 255 : 1;
    return { r: +m[0] * k, g: +m[1] * k, b: +m[2] * k,
             a: m.length > 3 ? +m[3] : 1 };
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

  /* TRAP 5: the manager profile modal is not on any route. It only exists once a
     card is clicked, so for its whole life it sat outside this sweep — and it was
     holding two real failures the entire time: the season list's champion row wore
     a --gold-soft fill that pushed its PF figure to 4.34, and .pfclose floated over
     the scrim with a white tint under a white glyph. Sweeping the routes and
     calling the page clean was true and useless. Open one profile and sweep it too.

     Do NOT take that as licence to trust every number this reports inside the
     modal. A hand-rolled scanner run here claimed eleven further failures — the
     manager's own name at 1.09 — and every one was fiction: .pfheromain paints a
     THEME-DEPENDENT gradient, so an ancestor walk lands on .pfhero's dark colour
     underneath it. That is trap 4, and this tool already handles it by counting
     those elements as gradientSkipped. The scanner that did not was the problem. */
  const card = document.querySelector('.mgrcard');
  if (card) {
    const people = document.querySelector('a[href="#people"]'); if (people) people.click();
    const first = document.querySelector('.mgrcard');
    if (first) {
      first.click();
      res.push(window.__sweep({ view: 'profile-modal' }));
      const x = document.querySelector('.pfclose'); if (x) x.click();
    }
  }
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
