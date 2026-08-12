# 0004 — Rank Draft Rankings on season-relative value over replacement, not raw class points

## Status
Accepted (2026-08-11)

## Context
Draft Rankings shipped ranking every team-draft on one number: the sum of every point every
drafted player scored while he sat on the drafting team's roster. The user flagged the symptom —
Ermin Cerimovic's 2023 team went 5-9 and its draft still came out **2nd best all-time**. Digging
in, that wasn't a one-off; the metric was measuring three wrong things at once. All figures below
were computed against the 96 team-drafts from 2018-2025 (the seasons with week-by-week lineup
data on file).

1. **It paid for hoarding, not for drafting.** Raw class total correlated **-0.41** with a
   manager's roster moves that season. The surest way up the board was to draft sixteen men and
   never touch the waiver wire. The 2023 example is exactly this: one roster move all year, two
   kickers and two defences carried from week 1 to week 17 (467 points of streaming positions),
   plus Matthew Stafford at 282.8 points while starting three times. Of his 2,323.9 "draft
   points", 1,054 never reached a starting lineup — 467 from K/D-ST and 587 more from skill
   players sitting on his bench.
2. **It rewarded bulk over usefulness.** A quarterback outscores any running back alive, so a
   benched QB banked more apparent draft value than a starting RB2. Steals & Busts had already
   solved this for single picks (judge each man at his own position against replacement level);
   the whole-draft board hadn't inherited it.
3. **It could not compare eras.** 2014 scored yardage in whole-number blocks, 2014-2020 paid
   0 PPR and 2021+ pays half. Ranking on raw totals let the rulebook do the sorting: seventeen
   of the old board's bottom twenty rows were 2014-2017.

Alternatives considered for the value basis, all measured:

Ranks below are Ermin 2023 among the **96 team-drafts from 2018-2025**, so the bases compare
like for like (the shipped metric put him 2nd on the full 138-row board and 2nd here too).

| basis | vs. roster moves | vs. wins | Ermin 2023 |
|---|---|---|---|
| raw class total (shipped) | **-0.41** | +0.29 | 2 / 96 |
| raw, minus K and D/ST | -0.36 | +0.31 | 19 / 96 |
| points scored in the starting lineup only | -0.22 | +0.38 | 33 / 96 |
| **value over replacement, negatives kept** | **+0.13** | **+0.43** | 42 / 96 |
| value over replacement, floored at 0 per pick | -0.04 | +0.45 | 29 / 96 |

Value over replacement with negatives kept is the only candidate that is effectively *neutral*
on roster moves — i.e. the only one that isn't secretly grading in-season management. Flooring
each pick at zero re-introduces a churn signal (cutting a bust becomes free) and erases the real
cost of holding a below-replacement player in a roster spot all year, so negatives are kept.

## Decision
**Value (2018+).** For each drafted player, points he scored *for the team that drafted him*
(weekly roster scan, unchanged) minus the replacement-level rate at his position that season,
prorated by the weeks that team actually held him. Replacement level is `replacementAt()` cut at
`STARTS_BAR` — the same line Steals & Busts holds single picks to, so the two boards can't drift.
Kickers and D/ST are excluded, matching the existing `SKILL` convention and its stated reasoning.
Position comes from `ARCH.P`, not the drafted slot, so the pick is measured against the pool it
actually belongs to.

**Score.** Value is z-scored *within its own season* and presented as `100 + 15z` — 100 is an
average draft for that year, 15 points is one standard deviation. The board sorts on this, not on
the raw figure. Population sd (÷n), not sample: the twelve teams are the whole league, not a draw
from a larger one. Each row also shows its in-season placing ("3rd of 12").

**2014-2017.** Replacement level needs to know who was on a bench in week 9, and this file has no
week-by-week roster history before 2018. Those four seasons keep the whole-class raw totals in
`DRAFT_TOTALS_2014_2017` as their value basis, z-scored within their own season the same way, and
every affected row is labelled on the board as the different measurement it is.

## Consequences
- Ermin 2023 lands at **37 / 138, score 109, 3rd of 12 that year** — which reads correctly: that
  team was 4th in the league in points scored and went 5-9 on schedule luck, so a good-not-elite
  draft is the right answer. The absurdity was the ranking, not the underlying draft.
- Era balance is fixed by construction: 2014-2017 supply 30% of rows and now hold 8 of the top 20
  and 8 of the bottom 20 (previously 2 and 17).
- The board's headline number is no longer a point total, so "best draft" now means "beat its own
  season by the widest margin". Section copy and the Best/Worst 10 subheads were rewritten to say
  so; the raw class total is still printed on every row as context.
- 2014-2017 remain on a knowingly coarser basis. This is disclosed on every row and in "How this
  works" rather than silently mixed. Closing it properly would mean re-pulling per-player weekly
  box scores for those four seasons (the ESPN work described in `HANDOFF.md`) and baking per-pick
  rather than per-team totals — the same lift already scoped out once for K/D-ST.
- `seasonOnly` on ranking rows is replaced by `basis: "por" | "total"`; rows also carry `score`,
  `z`, `inSeason` and `of`. Nothing outside `draftRankings()` and its renderer read the old shape.
