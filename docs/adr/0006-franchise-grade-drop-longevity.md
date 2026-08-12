# 0006 — Rename the manager grade to Franchise Grade, and drop the Longevity axis

## Status
Accepted (2026-08-12)

## Context
Two problems with the same root, both surfaced while setting a standard for what the site is
allowed to judge (see `CONTEXT.md`, *Judged metric*).

**The label contradicted the weighting.** The comment above `pfWeights()` says "A franchise is
judged first on what it won," and the weights follow through — bracket outcomes 38, team quality
36, lineup skill 16, context 10. That is a measure of franchise achievement. It rendered on a
manager profile as a *manager* grade, which invites an argument the weighting cannot win: "I'm
the better manager, I just lost a three-week single-elimination bracket." That objection is
correct, and the same comment concedes the point — a title is "the noisiest thing on the record."
A grade that can be defeated by reading its own source comment is not defensible.

**`LONGEVITY` carried weight but no information.** Measured across the twelve graded managers it
takes four distinct values, six of them tied at the 75th percentile, and correlates **0.07** with
win rate. It costs a manager who joined later roughly 6% of his grade for having joined later.
The `pfWeights()` comment already argues against exactly this — "a manager should not climb for
merely persisting" — and then books 6 points for persisting. `ACTIVITY` was measured alongside it
and behaves differently: **0.39** with win rate, 0.11 with titles.

## Decision
- **Rename to Franchise Grade.** The numbers don't change meaning; the label starts matching them.
- **Drop `LONGEVITY`** from `pfWeights()` and `pfAxesForRow()`. **Keep `ACTIVITY`** — 0.39 clears
  the validity gate, 0.07 does not.
- **Renormalise proportionally**, not by reassigning the 6 points to chosen axes. Effective
  weights become HARDWARE 21.3, POSTSEASON 19.1, SCORING 20.2, WINNING 18.1, LINEUPS 17.0,
  ACTIVITY 4.3. *Implementation note:* `pfGradeForAxes()` already divides by `wsum`, so deleting
  the `LONGEVITY` entry **is** proportional renormalisation — the remaining integers can stay
  20/18/19/17/16/4 and produce these figures exactly. Only UI that displays weights as
  percentages needs the new numbers written out.
- **Keep `GRADE_MIN_SEASONS = 3`**, and mark short-tenure grades as a small sample in the UI.
- **Remove `LONGEVITY`'s `DESC`/`FLAW` entries**, which become unreachable once the axis is gone.

## Considered options
- **+3 `SCORING` / +3 `LINEUPS`** — rejected. It puts `SCORING` at 22, above `HARDWARE` at 20, so
  points scored would outrank titles won. That may be a defensible philosophy, but it is a
  different grade, and it should be argued for on its own rather than ride along inside a
  redistribution.
- **All 6 to `LINEUPS`** — rejected for the same reason, more sharply.
- **Drop `ACTIVITY` too** — rejected. It passes the gate; removing it would be taste, not
  evidence.
- **Raise `GRADE_MIN_SEASONS` to 4-5** — rejected. It fixes small-sample noise by excluding
  people, and in a seventeen-person league being ungraded reads as being left out. Disclosing the
  sample size costs nothing and matches the transparency bar.

## Consequences
- The grade board's top 8 is unchanged; 9-12 reorder. **Every** manager's rank bars move, because
  the percentile field is unchanged but the weighted mean over it is not.
- The generated one-line scouting descriptor picks a manager's best and worst *axis*. With
  `LONGEVITY` gone, whoever had tenure sitting in the "worst axis" slot now gets a different, and
  possibly sharper, sentence written about them by name. Every descriptor needs re-reading after
  the change, not just the arithmetic.
- Percentile axes are relative by construction, so the graded field always spans a similar range
  regardless of absolute quality. That was already true and is unchanged here.
- Not pursued: reweighting `HARDWARE` downward to reflect bracket noise. Q31 settled that this
  measures achievement, and under that reading the noise is part of what happened, not an error
  to correct.
