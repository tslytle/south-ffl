# 0020 — There is one chip, and rows keep only what is local to them

## Status
Accepted (2026-08-15)

Annotated by ADR 0022 (2026-08-15): the shared rule stands; the elevation change is
token-only and moved no geometry. The chip-variant count remains the test.

## Context
Nine rows on this site do the same job — a strip of small controls, most of them behind
an uppercase caption. Every one of them had been drawn on its own terms:

| row | size | weight | padding | radius | height |
|---|---|---|---|---|---|
| `.drdivsel` | 11 | 700 | 5/12 | 12px | 25 |
| `.mgrsort` | 12.5 | 600 | 6/11 | 8px | 29 |
| `.recjump` | 12.5 | 600 | 6/11 | 8px | 29 |
| `.subnav` | 12.5 | 600 | 7/12 | 8px | 31 |
| `.allctl` | 12.5 | 700 | 7/13 | 8px | 31 |
| `.wkbar` | 12.5 | 600 | 7/6 | 8px | 31 |
| `.drtabs` | 12.5 | 700 | 8/16 | pill | 33 |
| `.rpick` | 15 | 600 | 9/15 | 8px | 39 |
| `.yearpick` | 15 | 600 | 9/15 | 8px | 39 |

Five heights, three radii, two sizes, two weights. The captions were split two ways as
well — 700/.11em/`--muted` on the two jump bars, 600/.08em/`--faint` on the four
pickers — and the phone had a third set of rules that re-inflated `.rpick` and
`.yearpick` back to 15px, copying the desktop unevenness onto the small screen.

**This needs no measuring to see, because the rows stack.** `#matchups` printed SEASON
at 39px directly above JUMP TO WEEK at 31px. Draft Night printed four 33px pills
directly above nine 25px division chips. The Managers view printed IN HERE at 31px a
hundred pixels above SORT BY at 29px. Reported as "the tabs look uneven and not clean",
which is exactly what it is: nothing about those pairs differs in kind, so nothing
about them should differ in size.

`.allctl` also spent a **full accent fill on hover** while every other row tinted only
its edge and text — so a chip that was not selected wore the selected treatment, in the
one row that has no selected state to confuse it with.

## Decision
**One rule sets chip geometry and all three states.** 12.5px/600, `6px 12px`,
`min-height:32px`, `--r-sm`, `--surface` on `--line`, centred flex. Hover tints border
and text; **hover never fills**, because a fill is what `on` means. Selected is
`--accent` fill with `--accent` *border* — not `transparent`, which made the chosen
chip the one chip in the row with no edge.

**12.5px because it is on the scale.** Six of the nine already used it and it is a step
in ADR 0013; 13px would have split the difference by inventing a value. The two rows
that lose a size are the year and round pickers, which keep their legibility from
`min-height` and horizontal padding rather than from type.

**`min-height`, not padding alone.** That is what makes the height a promise: a week
number and the words "Manager Profiles" land on the same 32px whatever they contain.

**A row keeps only what is genuinely local to it** — its gap, whether it is sticky, the
week bar's `min-width`, and `.recjump`'s `--raise` fill. Ordering carries this: the
shared block is declared first and every local rule matches it at (0,1,1), so a local
declaration wins without needing extra specificity.

**One caption, typography only.** 11px/700/.11em/uppercase/`--muted`. Whether a caption
sits inline or on its own line above the row stays with the row, because the two sticky
bars depend on that distinction.

## Consequences

### The invariant is checkable, and should be checked
Sweeping every route and grouping every visible chip by
`(height, size, weight, radius, family)` returns **one variant over 208 chips**, and
every caption returns one variant over 16. That query is the test for this ADR — it is
cheaper than reading nine rules, and it fails loudly the moment a tenth row is added
with its own geometry. In dark it returns one variant on three border colours, all
intended: `--line`, `--accent` for the selected chip, and the 50% gold that marks
playoff weeks on `.mwkbar .po`.

### The phone rule got smaller, not bigger
Every chip is centred flex at 32px on the desktop side now, so the ≤760px touch rule
only has to raise one number for the nine; the four non-chips it also covers (`.slink`,
`.clear`, `.nflstep`, `h2grid-wrap > summary`) still need the whole treatment. The two
media queries that re-inflated `.rpick` and `.yearpick` to 15px are gone — the 44px
touch target already gives the thumb what those were reaching for.

### It costs a hierarchy that was not being read
`.drtabs` was the loudest row on the site — a 700-weight pill in `--body` — and it is
now the same chip as a division filter beneath it. The claim is that the accent fill
carries "you are here" on its own, and that a tab strip does not additionally need to
out-weigh the filter under it. If a view ever genuinely needs two ranks of control, the
second rank should be a **new documented step in this system**, not a row that quietly
re-specifies its own padding.

### Nothing here gives `.subnav` a current-panel state
It remains a jump bar: it scrolls to a panel and never marks which one you are in. That
is unchanged by this ADR and still worth doing — the styling hook (`.on`) now exists
and is shared, so it is a script change rather than a CSS one.

### Measured after
ADR 0005's sweep at zero in all four combinations — {375px, 2048px} × {dark, light},
two passes each. `gradientSkipped` 325 dark / 311 light, unmoved from the 2026-08-12
baseline.
