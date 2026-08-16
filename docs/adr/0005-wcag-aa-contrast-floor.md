# 0005 — Hold the whole page to WCAG AA contrast, and split metal ink from chip ink

## Status
Accepted (2026-08-11)

Annotated by ADR 0022 (2026-08-15): the floor stands and is re-baselined against the
new elevation ladder. This sweep measures text against its own background and so can
never see a container against the page — that population sat at 1.08:1 for twelve
clean sessions. ADR 0022's surface-separation floor covers it.

## Context
A visual audit measured the computed foreground against the *composited* background (alpha tints
resolved against whatever they sit on, gradient stops taken at their darkest) for every
text-bearing element on the page, in both themes — 21,341 elements each. It found five distinct
failure classes, all pre-existing:

1. **The two quiet ink tokens sat just under AA in light mode.** `--faint` measured 3.79:1 on
   `--soft` and `--muted` 4.27:1 — affecting thousands of elements (secondary labels, table dim
   cells, sub-notes). `--faint` was also 4.46:1 on `--raise` in dark mode.
2. **Metal chips took white ink.** `--on-chip` exists on the premise that a chip's fill is dark
   in light mode and bright in dark mode. True for `--accent` and `--neg`; false for gold, silver
   and bronze, which are bright in *both*. The 1st/2nd/3rd medal badges ran 1.67:1 (silver, light)
   to 3.77:1 (gold). The old gradients also drew their light stop from the `--*-line` tokens,
   which in dark mode are the *darker* of the pair, so the dark ink failed at that end too.
3. **`textOn()` picked the wrong ink for five NFL clubs.** It weighted raw 0-255 channels and
   split at 0.5 — no sRGB gamma decode — so it put white on Miami teal (3.95:1), Cincinnati and
   Denver orange (3.37:1), Carolina (4.03:1) and Chargers blue (4.28:1). In all five cases the
   other ink would have passed.
4. **Translucent tints threw away their card's own surface.** `.sswk.flip` and `.ssflag` painted
   `--rust-soft` (translucent in dark mode) as the whole background, so the panel behind showed
   through, the card read lighter than its neighbours, and its labels fell to 3.9-4.3:1.
5. **Three prose links had no colour rule at all** and fell through to the browser's `#0000EE` —
   1.88:1 on the dark card.

## Decision
- Darken `--muted`/`--faint` in light mode (`#64708A`→`#58627C`, `#6E7891`→`#616B84`) and lift
  them in dark (`#8B95AD`→`#8F99B1`, `#7E89A3`→`#808BA5`), chosen so each clears 4.5:1 against
  the *worst* background it actually lands on, while keeping `--muted` visibly stronger than
  `--faint`. Same values in the print/paper block.
- Add `--on-metal:#0B0E11`, identical in both themes, and use it for every gold/silver/bronze
  fill. Derive medal gradients' light stop with `color-mix(… 72%, #fff)` from the base metal, so
  it can only ever be lighter than the base — in either theme.
- Rewrite `textOn()` to decode sRGB properly and return whichever of the two inks has the higher
  contrast ratio, rather than testing a threshold. The choice is then correct by construction.
- Paint translucent tints *over* `var(--surface)` (`linear-gradient(…) var(--surface)`) so a
  tinted card keeps its own opaque base.
- Add a base `a{color:var(--accent)}` floor. Every class-scoped link rule (`.plink`, `.topnav a`,
  `.yearnav a`, `.skiplink`) outranks it on specificity and is unaffected — verified by grouping
  every rendered anchor by computed colour before and after: only the three uncoloured ones moved.

## Consequences
- Both themes now measure **zero** AA failures across all 21,341 text-bearing elements. That is
  the standing bar: a change that reintroduces one is a regression, not a style preference.
- `--on-chip` is now only for accent/neg fills; its comment says so. Anything filled with metal
  takes `--on-metal`.
- The two quiet inks are slightly stronger than before. This is a deliberate, visible (if small)
  shift in the page's texture, not a rendering accident.
- Not pursued: raising the tiny type sizes (9-11px) that made these ratios marginal in the first
  place. Colour was the smaller, more reversible lever.
