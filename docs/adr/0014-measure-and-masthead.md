# 0014 — A header never spans wider than the thing it introduces

## Status
Accepted (2026-08-12)

Annotated by ADR 0022 (2026-08-15): the measure rule stands (still with no
instance, per 0021). The masthead half is narrowed by the session's one-masthead-
per-screen rule in CONTEXT.md: a group view carries one masthead, not one per level.

> **Superseded in application by ADR 0021 (2026-08-15).** The measure rule below is
> sound and still governs where a constraint goes. Its one instance is gone: `#board`
> no longer caps itself at 720px, because that cap was paid in the **collapsed** state —
> the state eleven of twelve boards are in by default — where it left Champions as the
> single short bar in a column of full-width ones. **What survives:** the rule itself,
> the masthead treatment, the remainder-row logic, and the left spine, which ADR 0021
> leans on as the reason not to centre the narrower measure instead.

## Context
On Champions, three widths stacked vertically: the page container at 1080, the board
header at 1040, and the list itself at 720, centred inside the header. Three left
edges and three right edges in one column of the page. This was the single largest
source of the "uneven" feeling — more than any type or colour problem, because it is
structural and the eye reads it before it reads anything else.

Separately, the board header was a filled `--raise` card with a 12px radius sitting
directly above another filled card. Matching their widths alone would have half-fixed
it: two stacked boxes at the same width is still two boxes.

## Decision
**The measure rule.** A header never spans wider than the thing it introduces. Where a
panel is narrower than its route, the constraint lives on the **disclosure**, not on
the panel, so header and panel share both edges by construction.

**The masthead.** `summary.subhead` is bare: no background, no border, no radius, a
hairline rule beneath. Hover moves to `border-bottom-color`.

This is not a new register. `summary.sechead`, one level up, already read exactly this
way — `background:none; border-radius:0; padding:0 0 var(--sp-4); border-bottom:1px
solid var(--line)`. The board header simply never inherited it.

**Remainder rows centre; whole groups do not.** Where a grid's last row is short, the
remainder centres. Where a group is *entirely* a remainder, it keeps the left spine.

## Consequences

### The measure problem was one board, not a pattern
`#champboard` is the only panel in the file with a narrower centred measure. Worth
recording, because the rule sounds systemic and its current application is a single
line. Verified after: header and panel both at `x=496, right=1216` on desktop, both
334px on the phone.

> *ADR 0021: that single line is now deleted and the rule has no instance at all. The
> observation above is what should have prompted the question — a rule whose entire
> application is one board is a rule worth asking whether that board needs it.*

### Centring a remainder needs flex, not grid
An `auto-fill`/`auto-fit` grid sizes its tracks against the **container**, so a short
last row is pinned to the first tracks with nowhere to go. Flex with each item sized as
an exact fraction of the row fixes it without stretching: a full row consumes 100% and
has no free space, so `justify-content:center` is a no-op there and the left spine is
untouched; only a partial row has slack, and that slack centres. `--cols` is explicit
per breakpoint because the fraction has to know it.

### A group that is entirely a remainder must not centre
The first version of this was **worse than what it replaced**. Season has two doors,
Records and Rules have one — with nothing above them to be a remainder of, centring
detached them from their own left-aligned group labels and read as broken. The test is
"fewer items than columns", which `:has()` asks directly, with the threshold moving
with `--cols`. Measured at 375 / 700 / 900 / 1265: every full row starts at indent 0,
every remainder centres, no horizontal overflow.

### The left spine is now load-bearing
Several decisions in this ADR and in 0012 assume a single left edge running down the
page. Anything that centres a block — or introduces a second measure — should be
checked against that, because the spine is what makes the remaining ragged right edges
read as deliberate negative space rather than as unfinished layout.
