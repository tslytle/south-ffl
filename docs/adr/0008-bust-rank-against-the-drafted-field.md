# 0008 — Rank a pick's finish against the field he was drafted in

## Status
**Superseded by ADR 0015 (2026-08-14)**, which moves Steals & Busts onto going-rate and removes
the rank subtraction this ADR exists to fix. Accepted 2026-08-12.

Read the *Considered options* table below before rebuilding anything here: its **option D**
(`pts − expected at slot`) is close to what ADR 0015 adopts, and it was rejected on evidence.
ADR 0015 answers that rejection point by point and turns it into two hard preconditions — the
objection is addressed, not overruled.

## Context
Steals & Busts scores every pick as `gain = posSlot - posFin`, and the card
states both numbers: "Taken RB4, finished RB82 · −78 spots".

Those two ranks came from different populations. `posSlot` ranks a pick among
the players **drafted** at his position; `posFin` ranked his points among
everyone **rostered** at it. Measured across 2018-2025 the rostered field is
1.3-1.8× larger:

| pos | avg drafted | avg rostered | ratio |
|-----|------------:|-------------:|------:|
| QB  | 21.3 | 36.5 | 1.72× |
| RB  | 57.5 | 84.9 | 1.48× |
| WR  | 67.9 | 89.6 | 1.32× |
| TE  | 19.0 | 33.9 | 1.78× |

So Le'Veon Bell was "drafted RB4, finished RB82" in a year only 56 RBs were
drafted. 47.2% of busts carried an inflated finish rank, by up to 34 places.

The distortion is not uniform — it grows as a player scores less, because a man
who scores nothing lets every one-week waiver pickup leapfrog him. That put
**Jerick McKinnon 2018** (torn ACL in August, drafted RB13) above **Michael
Thomas 2020** (drafted WR1) on the bust board. Rank inflation, not evidence.

Steals were unaffected and measured identical under every basis: at the top of
a position, everyone who outscored you was drafted too.

## Decision
Add `posFinDr`, the pick's finish ranked among the players drafted at his
position, and use it for `gain` and on the card, which now reads "Taken RB4 of
56, finished RB54 · −50 spots" — both ranks from the same 56, so the
subtraction means something.

`posFin` is kept, still ranked against everyone rostered, and still gates the
steals filter. "Could you actually have started him" is genuinely a question
about the whole pool, so that test should not move — and it doesn't: the steal
pool is unchanged at 569 picks, and the twelve names on the board are identical
in the same order.

## Considered options
Four bases were measured on the board the UI actually shows (three per position):

| basis | shares with shipped | mean draft slot | outcome |
|-------|--------------------:|----------------:|---------|
| A `slot − finAll` (shipped) | 12/12 | 7.6 | the defect |
| **B `slot − finDr`** | 6/12 | 3.0 | **adopted** |
| C `vor` (pts − replacement) | 3/12 | 16.0 | rejected |
| D `pts − expected at slot` | 8/12 | 7.9 | rejected |

- **C** produced a board of late fliers that didn't hit — Zamir White (RB23),
  Gus Edwards (RB20), A.J. Green (WR29). Those aren't busts, and it ignores
  what was paid.
- **D** was the most appealing in the abstract: it measures "paid for X, got Y"
  directly, using each slot's historical average as the expectation. It was
  rejected on evidence. The expectation should fall monotonically as the slot
  gets later; even smoothed over ±2 slots it does not — 35% inversions at WR,
  29% at RB, 25% at QB. The board it produced was also sensitive to that
  arbitrary smoothing window (raw vs smoothed shared only 7/12 names), and it
  reordered the steals board to 4/12, dropping Wan'Dale Robinson (WR65 → WR13)
  in favour of big seasons from mid-round picks. Eight seasons is not enough
  data to estimate a per-slot expectation this way.

## Consequences
- The bust board loses McKinnon 2018, Gus Edwards 2021, Antonio Brown 2019,
  Courtland Sutton 2020, Rodgers 2023, Newton 2019 and Njoku 2019; it gains
  Ridley 2021, Nabers 2025, Chubb 2023, Lamar Jackson 2025, Burrow 2025 and
  Pitts 2022. Mean draft slot of the board falls from 7.6 to 3.0.
- Two finish ranks now exist on every pick. The comment in `rankPicks` says
  which is for what; they are not interchangeable and collapsing them back into
  one would reintroduce this bug.
- The Record Book reads `HINDSIGHT`, so bust figures there move with the board.
- Not pursued: cross-position comparability. `perPos` takes three per position
  and then groups by position, so the combined ordering is never visible and
  does not need to be fair between a QB and a TE.
- The 3-per-position quota still seats a mild QB and TE entry (e.g. Kyle Pitts
  2022, −13 spots) because those positions have small drafted fields. That is a
  display quota artefact, present before this change and unaffected by it.
