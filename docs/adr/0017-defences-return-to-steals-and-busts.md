# 0017 — Defences return to Steals & Busts

## Status
Accepted (2026-08-15). Reverses the defensive exclusion in ADR 0015; that ADR stands in every
other respect. Rests on the defensive scoring correction made the same day (commit `97e9838`).

## Context

ADR 0015 put defences on Draft Rankings and kept them off Steals & Busts. That was not a
convention or a preference — it was a scope drawn at a measured error bar, and the ADR said so:
*"a scope drawn where the data can carry the claim and stopped where it cannot."* It accepted a
named cost: **a defence can sink your draft class but can never appear as a bust.**

The measurement it rested on:

| | ADR 0015 (2026-08-14) |
|---|---|
| D/ST season error | median **11.8%**, 90th pct **21%** |
| what it moves on Draft Rankings | 0.65 score points (median), against scores spanning 61-136 |
| what it moves on Steals & Busts | **20-40% of the D/ST spread** |

It also recorded a diagnosis: nflverse's play-by-play build "carries ~11% more sacks and ~23% more
fumble recoveries than ESPN's feed". That diagnosis was wrong, and it is why the error looked
irreducible rather than fixable. Both facts about sacks and fumble recoveries are true; neither
was the cause.

## What changed

`refresh-players.py --verify` was documented as re-scoring 2018-2025 against the league export and
reporting the agreement. It had never run — the flag was a no-op identical to `--dry-run`, and the
"100.0%" in its header was a one-off measurement from authoring time. Written for real, it walks
all 24,857 roster-weeks the export recorded and re-scores each from raw nflverse stats.

**It reproduced ADR 0015's number exactly before changing anything** — 12.8% mean, 11.8% median
absolute error per club-season, against the ADR's median 11.8%. The two measurements agree, which
is what makes the improvement below a real change rather than a different yardstick.

It also showed the thing no season-level check could: the residual was **one-sided**. Computed was
never meaningfully *high*. A noisier feed is wrong in both directions; only a missing scoring
category can subtract from every defence at once. Two were missing:

* **Yards allowed are NET of sack yardage.** nflverse keeps sack yards in their own column rather
  than netting them out of `passing_yards`, so summing passing and rushing gave every offence more
  yards than it gained and dropped the defence a ladder step. Alone: 63% → 88% of club-weeks exact.
* **A fumble returned for a touchdown is a defensive score** that nflverse files outside
  `def_tds`. The same column also holds an offence's touchdown on its own recovered fumble, so it
  is capped at the opponent fumbles that defence actually recovered.

Neither is a fitted correction. Both are definitions, and the second is the defensive half of a
rule this codebase had already recovered for players.

| | before | after |
|---|---|---|
| D/ST season error, mean absolute | 12.8% | **1.9%** |
| median | 11.8% | **1.1%** |
| club-weeks exact to the point | 63.2% | **91.5%** |
| mean signed residual per club-week | −0.82 | **−0.11** |
| share of the best-to-twelfth D/ST spread (mean 66 pts) | ~25% | **~4%** |

## Decision

**Defences are judged on Steals & Busts, at every position's own going rate, exactly as kickers
and skill players are.** One line comes out of `draftValue()` and `D/ST` goes into `POS_ORDER`.

ADR 0015's test is not being loosened; it is being re-applied to better data and passing. The
error is now ~4% of the D/ST spread where the ADR required better than 20-40%, and the asymmetry
it named as its cost — sink a class, never appear as a bust — no longer has to be paid.

Note what this is mechanically: **a filter coming off, not a measure being extended.** Steals &
Busts is `draftPicksPriced()` read one pick at a time, the same arithmetic Draft Rankings sums.
Defences were already being priced and then discarded at the last step.

## Why this clears the bar

Draft Rankings is a **defining metric** (ADR 0016), so the gate is face validity, robustness and
well-definedness — not correlation.

**Face-valid.** The board's own answers, unprompted:

| | pick | over the going rate |
|---|---|---|
| 2019 Patriots D/ST | 145 | **+99** |
| 2017 Jaguars D/ST | 151 | **+88** |
| 2022 Patriots D/ST | 192 | **+67** |
| 2015 Bills D/ST | 70 | **−21** |
| 2015 Dolphins D/ST | 107 | **−18** |

The 2019 Patriots and 2017 Jaguars are the two defences anyone in this league would name, both
taken in the last third of a draft. The 2015 Bills — Rex Ryan's first year, taken in the sixth
round on hype — is the bust a manager would name. This is the check that caught the Ermin-2023
absurdity every correlation had passed, and it reads right.

**Robust.** Re-ranked with ±2 points of noise, which is the whole remaining residual: the three
defensive steals do not move at all; the busts move only in their third card, between two 2015
defences already within a point of each other.

**Bounded, and stated rather than hidden.** About 8% of club-weeks are still one yards-allowed
ladder step out and nobody has isolated why. What that can move is a **sign**: 8 of the 178
defences sit within 2.5 points of their going rate and 2 within half a point, so a defence that
close to the line may read as a small steal or a small bust depending on the residual. It cannot
turn one kind of story into the other, and the page says so.

**It does not crowd the board.** The best defensive pick of all time ranks 41st among 2,239 picks,
and the columns take three per position regardless.

## Scope

**The waiver board is untouched and still excludes defences and kickers.** Those values come from
the league export directly and are never reconstructed, so nothing here bears on that exclusion —
it rests on its own reasoning and would need its own decision.

## Consequences

* Six new cards on Steals & Busts (three per column), and defences now reachable on the
  per-manager panel.
* A manager can now be shown a defensive bust. That is the point.
* If the remaining 8% is ever isolated, the honest place to record it is here, not by quietly
  changing the number in the page's margin.
* `--verify` now fails on one-sided D/ST bias, so neither corrected rule can be reverted quietly.
  Proved by fault injection: removing either one exits 1.
