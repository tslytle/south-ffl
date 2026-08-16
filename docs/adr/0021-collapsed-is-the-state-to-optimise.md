# 0021 — The collapsed board is the state worth optimising, so no board keeps its own measure

## Status
Accepted (2026-08-15). Supersedes ADR 0014's application to `#board`; the measure rule
itself stands.

## Context
ADR 0014 established the measure rule — *a header never spans wider than the thing it
introduces* — and applied it to the one board with a narrower measure. Champions caps
its list at 720px so the year, the name and the record read as one plaque line, so the
cap moved off the panel and up onto the disclosure, giving header and list the same two
edges instead of three.

That is correct about edges and it fixed the board it was looking at. **It optimised the
open state.** Eleven of the twelve boards on this site are collapsed `<details>`, and a
group view opens on nothing but header bars — four of them under The Managers, three at
1040px and Champions alone at 720. Reported, immediately after the chip work in ADR
0020, as "I want the bars to be the same length and for everything to match".

The measure rule was never wrong. What was wrong was assuming the cost of a board's own
measure is paid only while that board is open. It is paid in the default state of the
page, by every board next to it, all the time.

## Decision
**`#board details.sub{max-width:720px}` is deleted.** Every top-level board is the full
width of its route, so every collapsed header bar shares both edges with every other.

**The measure rule survives unchanged** — a header still never spans wider than what it
introduces. It now has no instance, because no board narrows its own panel. If one ever
does, the rule says where the constraint goes; this ADR says to think hard before
adding the constraint at all.

## Consequences

### The plaque line does spread, and that is the price
At 1040 the record sits about 520px from the name rather than about 200px. It was worth
looking at both before choosing: the spread is real, but the row keeps a gold year at
the left, a right-aligned record column and a full-row hover, so it lands as a
three-column leaderboard rather than as drifting text — the same shape The Ledger uses
directly beneath it, in the same group. The alternative fixes were all worse:

- **720 centred inside 1040** is what ADR 0014 removed. Three left edges again, and it
  breaks the left spine that ADR 0014's own last section calls load-bearing.
- **720 left-aligned inside 1040** keeps the spine and leaves 320px of dead space on
  every row, which reads as unfinished rather than as measured.
- **Full-width header over a 720 body** matches the bars and reintroduces the exact
  ragged edge ADR 0014 existed to remove, one state later.

### The invariant, and how to check it
Sweep every route and group every top-level `summary.subhead` by its `(x, right)` pair:
it returns **one pair over 16 panels** (172→1212 at 1265px). That is the test for this
ADR. It is the same shape of check as ADR 0020's chip-variant count and it fails the
moment a board re-narrows itself.

### The frame comment keeps a failure mode with no instance
The `--bbleed` outline comment explains that a padding-plus-negative-margin bleed was
rejected because a capped box cannot be widened by a negative margin, and Champions was
the capped box. There is no capped box left. The reasoning is kept and annotated rather
than deleted: the property that made the outline right — it costs the layout nothing, so
boards already at `need == avail` do not gain a scrollbar — is still the reason the
frame works, and any future measured board would hit the same wall.

### Measured after
ADR 0005's sweep at zero in all four combinations — {375px, 2048px} × {dark, light},
two passes each. `gradientSkipped` 325 dark / 311 light, unmoved from the 2026-08-12
baseline. The phone is unaffected either way: 720px never bound below 760px.
