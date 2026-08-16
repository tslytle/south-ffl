# 0013 — Eight values, eleven names: the type scale re-cut

## Status
Accepted (2026-08-12)

Annotated by ADR 0022 (2026-08-15): the eight-value structure stands untouched by
the elevation change.

## Context
Asked where the site looked wrong, the answer included "sometimes text looks wonky or
uneven". The cause was mechanical and visible in the token block:

```
9px  10px  11px  12.5px  13.5px  15px      17px  20px  25px  30px  (40px hero)
```

Six steps inside six pixels, then a jump to even intervals above. Ratios at the small
end ran 1.08–1.14 — below the threshold at which a size difference reads as
deliberate. So on a dense surface nothing looked bigger than its neighbour; it looked
*slightly off*. Two different systems sharing one file.

The file had also already conceded the bottom of the scale: a `max-width:760px` block
nudged `--t-micro` to 10.5px, with the note that 9px "is legible on a desktop monitor
and not on a phone held at arm's length".

## Decision
Eight values on a ~1.2 ratio, carrying all eleven existing names:

| value | names | used for |
|---|---|---|
| 11px | `--t-micro`, `--t-tiny` | eyebrows, pills, table headings, badges |
| 12.5px | `--t-fine`, `--t-small` | captions, sub-values, secondary text |
| 15px | `--t-base`, `--t-body` | table body, dense lists, prose |
| 18px | `--t-lead` | lead figures, small headings |
| 22px | `--t-h4` | card headings |
| 27px | `--t-h3` | panel headings |
| 33px | `--t-h2` | section titles |
| 44px | `--t-hero` | the one display size |

**Names outnumber values on purpose.** `micro`/`tiny` were 1px apart, `fine`/`small`
1.5px, `base`/`body` 1.5px — never distinguishable. Collapsing the pairs onto a shared
value keeps the intent the names carry and avoids renaming 371 declarations. 9px is
gone entirely, and the phone override with it.

## Consequences

### It propagated cleanly, because the file was already disciplined
371 font-size declarations read from tokens; only 8 were hardcoded px. Six moved onto
the scale. Two stayed, both with reasons already written down: `.ticker-dot` at 8px is
a bullet glyph rather than text, and `select` at 16px under `@media (hover:none)` is
the iOS zoom-on-focus fix.

### Everything got slightly bigger, and the dense surfaces absorbed it
Measured at 375px across all eighteen views: **no page-level horizontal overflow
anywhere**. One regression, on Rules — cells overflowing their content box went from 2
(worst 3px) to 5 (worst 6px) inside 65px cells. Text wraps, nothing clips, left alone.

### The draft cheat sheet is structurally unchanged
309 rows, 6 sections, 56 tiers, 4 cliff markers, 18 distinct shapes, same row width —
identical before and after, proved by driving both builds in parallel iframes. Row
height goes 32px → 34px. On the one surface read under time pressure that is a gain,
not a cost, so it takes no local override. **If a future change to this scale hurts
that board's density, the board gets the override — the scale does not get
compromised** (ADR 0007 restyles the cheat sheet, it does not redesign it).

### The phone was measurable for the first time
`resize_window` reports success while `window.innerWidth` stays at desktop, so every
"phone" check before this was silently a desktop one. A same-origin iframe evaluates
media queries against its own width; the recipe is in HANDOFF. This is the first
change in the file's history verified at 375px *and* 2048px in *both* themes.
