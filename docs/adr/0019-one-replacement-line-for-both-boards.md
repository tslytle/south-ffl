# 0019 — The waiver board prices against the NFL, not against the league's own shelf

## Status
Accepted (2026-08-15). Supersedes the positional scope of ADR 0018, which it makes moot rather
than overturns. Adds `wrep` to `PLAYER_VALUE`, written by `refresh-players.py`.

## Context

ADR 0018 put defences on the waiver board and kept kickers off, on a measurement: a wire value is
points minus the replacement at that position that week, that replacement was read off the
**rostered pool**, and in 31 of 136 weeks (22.8%) the league rostered twelve or fewer kickers — so
there was nobody past the bar and the subtraction collapsed to "minus the worst rostered kicker".

Asked to put kickers on anyway, the honest options were to accept that collapse or to fix what
caused it. This is the fix.

## The flaw ADR 0018 named but under-read

ADR 0018 treated the shallow pool as a **kicker problem**. It is not. It is a problem with the
pool itself, and kickers were merely where it became impossible to ignore.

The board asks what a pickup gave you *"above what was sitting there for free"*. The rostered pool
is, by construction, **the set of men who were not free** — every one of them was on somebody's
roster. Using it to price free agency answers a different question than the one asked, and it errs
in one direction: the pool is a subset of the league, so the man just past the bar *inside it* is
never better, and usually worse, than the man just past the bar in the NFL. Replacement came out
too low, and every wire value on the board was therefore too generous.

Measured across all 136 wire weeks, true replacement minus rostered-pool replacement:

| position | mean per week | median | weeks the true line is higher |
|---|---|---|---|
| RB | **+1.67** | +1.5 | 96% |
| WR | **+3.01** | +2.9 | 100% |
| QB | **+3.29** | +2.9 | 98% |
| TE | **+3.97** | +4.1 | 100% |

Not a rounding error and not confined to one position: on the board's own arithmetic a pickup held
sixteen weeks was over-credited by 27 points at RB and 64 at TE.

## Decision

**Replacement on the waiver board is the man just past the startable bar among every player who
took the field that week**, baked by `refresh-players.py` into `PLAYER_VALUE[y].wrep` — the same
definition `replacement_from()` already uses for the season, at the same bar, one week at a time.

Consequences of that, in order of importance:

1. **The two hindsight boards now agree on what replacement means.** Draft Rankings priced a
   season against the whole NFL while the wire priced a week against the league's own shelf. They
   were never the same yardstick and the page had not noticed.
2. **The positional constraint disappears**, so `WIRE_POS` carries all six. Kickers are on the
   board because the question now has an answer that does not depend on whether this league
   happened to roster a thirteenth kicker.
3. **A thin week stays thin.** Byes cut the NFL pool too, so the line drops with them — which is
   the "bye-week wasteland" the board's own header always asked for and the rostered pool only
   approximated.

`BAR_POS` is retired. It was introduced hours earlier by ADR 0018 purely to give the rostered pool
a D/ST bar, and nothing reads it now; `STARTS_BAR` goes back to `LINEUP`. The unread `bar` field
on each wire row goes with it.

A season with no `wrep` is **skipped**, not scored against zero — falling back would silently turn
every value into raw points, which is the failure mode this ADR exists to remove.

## Consequences

* **Every number on the waiver board moves down**, and correctly. The board is not less generous
  by taste; it was over-crediting by a measured amount.
* **"Best pickup ever" changes hands twice in one day and lands where it started.** The rostered
  pool had just handed it to the 2018 Bears D/ST at +139.0 (ADR 0018); on a true replacement line
  that defence is worth **+78.0** and **Kyren Williams 2023 returns at +102.5**, down from the
  +123.7 the old basis gave him. The D/ST pool was the shallowest of all, so defences were the
  most inflated — ADR 0018 shipped a board whose headline card was an artefact of the very flaw it
  had documented and confined to kickers.
* Defences fall back to 2 of the top 10 pickups from 4, which is what removing an artefact looks
  like. Kickers enter with 227 pickups and top out at Jason Myers 2025, +40.0 over nine weeks —
  present, plausible, and nowhere near the top of the board.
* `PLAYER_VALUE` grows 8.7KB. The file is 2.7MB and the growth is worth watching, but a weekly
  line for six positions across eight seasons is 816 numbers.
* Start & Sit is untouched. It has its own replacement bar for a different question — what you
  should have started from what you *held* — where the rostered pool is the right pool.
