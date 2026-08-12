# 0009 — Drop Lineups and Activity: the Franchise Grade is four achievement axes

## Status
Accepted (2026-08-12)

## Context
ADR 0006 established that this grade measures **franchise achievement** and
renamed it accordingly. Auditing the remaining axes against the validity gate in
`CONTEXT.md` found two that don't belong, for two different reasons.

### LINEUPS was noise
`LINEUPS` scored a manager on points left on the bench per week — the difference
between his started lineup and the best legal lineup that roster could have
fielded. It read like the least luck-dependent signal on the sheet. It is the
opposite. Across **1,374 graded manager-weeks**:

| statistic | value |
|---|---|
| observed between-manager spread | 3.13 pts/wk |
| chance spread, 4,000 label permutations | median 3.34, 95th pct 4.76 |
| p(chance ≥ observed) | **0.61** |
| between-manager mean square | 103.0 |
| within-manager mean square | 125.9 |
| intraclass correlation | **−0.002** |

The observed spread is *smaller* than the median spread produced by dealing the
same weeks out at random, and between-manager variance is lower than
within-manager variance. None of the week-to-week variation is attributable to
who is managing. Hindsight-optimal lineups are decided by which bench player
happened to explode.

It was not a basis problem. `capture%` (actual/optimal) correlates **−0.99** with
points-left, and a fully opportunity-normalised measure — where the lineup sat
between the worst and best legal lineups — correlated **+0.04** with win rate.
The underlying weekly quantity carries no manager signal in any scaling.

This axis carried weight 16, **17.0% of the grade**.

### ACTIVITY is real but is not achievement
`ACTIVITY` measures roster moves per 14 games, and unlike `LINEUPS` it measures
something genuinely stable: split-half correlation between a manager's odd-year
and even-year rates is **0.82** (Spearman-Brown reliability **0.90**), with a
season-to-season intraclass correlation of **0.348**. Ermin Cerimovic sits at
6.6/8.6 moves per 14 games; Abbas Hussain at 42.5/39.0. Those are real people
managing differently, consistently, for a decade.

It fails on relevance instead. A move rate is *process*, not achievement. Its
0.39 correlation with win rate is the argument against keeping it, not for it:
winning is already measured directly by `WINNING`, so `ACTIVITY` contributes a
noisier second copy of information the grade already holds exactly. When the
target is directly observable, adding a correlate can only introduce error.

## Decision
The Franchise Grade is **four axes, all achievement**: HARDWARE 27.0%, SCORING
25.7%, POSTSEASON 24.3%, WINNING 23.0%. As in ADR 0006 the surviving integers
are untouched and sum to 74 deliberately, because `pfGradeForAxes` divides by the
weight sum.

`hasLineup` is removed from the four grading gates, since no axis reads lineup
data any more. This does not change who is graded: all five ungraded owners also
fail the three-season floor, so the field stays at twelve.

Both metrics remain **visible as facts** — points left on the bench on the Start
& Sit board, moves in the Ledger and the "Wire Hawk" trait badge. Only the grade
claim is withdrawn. That is the demote-to-factual default: "Ermin made one move
all year" is worth showing; "and therefore his franchise achieved less" is the
part the data won't support.

## Considered options
- **Keep `LINEUPS` at a reduced weight** — rejected. An axis with zero
  information should carry zero weight, not less weight.
- **Replace `LINEUPS`** with a blunder count (started a player who scored zero;
  benched a man who doubled the starter) — genuinely promising, and deliberately
  not attempted here. The lesson of this ADR is that a plausible lineup metric
  can be pure luck, so any replacement must clear the same permutation test
  *before* it is wired into the grade.
- **Keep `ACTIVITY`** because it measures a real trait — rejected on relevance,
  as above. Note this is a judgement about what the grade is *for*, not a
  measurement finding; the measurement came out in `ACTIVITY`'s favour.

## Consequences
- Seven of twelve managers change rank. Michael Boggess 3→2 (+6.6 points, the
  largest single move), Christian Winn 6→8, Colin Moore 10→12, Ermin Cerimovic
  12→10, Abbas Hussain 7→6, Tate Grainger 8→7, Justin DeCesare 2→3.
- The radar chart is now a four-spoke diamond rather than a hexagon. `pfRadar`
  was already written off `axes.length`, so it needed no change.
- The scouting descriptor's `DESC`/`FLAW` tables lose their `LINEUPS` and
  `ACTIVITY` lines, so a manager whose best or worst axis was one of those gets
  a different sentence.
- `pfMetrics` still computes `lineup`, `hasLineup` and `moves` — the profile stat
  boxes and Start & Sit read them — but the `pct("lineup")` branch of its `pool`
  helper is now inert. Commented as such rather than removed, to keep this change
  scoped to the grade.
- The grade is now entirely outcome-based. That is the point: it says one thing,
  and every axis is a thing the franchise actually did.
