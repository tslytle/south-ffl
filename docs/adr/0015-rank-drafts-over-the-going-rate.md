# 0015 — Rank drafts on what each pick returned over the going rate for its slot

## Status
Accepted (2026-08-14). Supersedes ADR 0004 entirely and ADR 0008 for Steals & Busts.
**Two preconditions in "The robustness gate" below must pass before the board ships.**

> **Amended 2026-08-15 by ADR 0017.** The defensive exclusion below — *"defences are graded in
> Draft Rankings and excluded from Steals & Busts"* — is reversed, and the diagnosis it rests on
> (nflverse carrying ~11% more sacks and ~23% more fumble recoveries than ESPN) was wrong. The
> 11.8% median season error was real and independently reproduced; its cause was two missing
> scoring rules, not a noisier feed. Corrected, that error is 1.1% median and defences clear the
> bar this ADR set. **Everything else here stands**, including the reasoning that drew the line at
> a measured error bar in the first place — ADR 0017 re-applies that same test rather than
> relaxing it.

## Context

ADR 0004 ranked a draft on the value its picks produced *while on the drafting team's own
roster*, over replacement, prorated by weeks held. Re-measured on 2026-08-14 against a harness
that reproduces the shipped board exactly (138 rows, 0 mismatches), that metric has four defects,
three of them mechanical and one structural.

1. **It credits the draft for men the team let go and won back off the wire.** 3,661 points,
   2.2% of everything credited. The current **#1 draft all-time** — 2021 The Asparagus' — includes
   177.9 points from Carson Wentz, who was never on that team's week-1 roster. ADR 0004's own
   comment states the principle ("the pick didn't earn that, the pickup did") and Steals & Busts
   enforces it; Draft Rankings never did. 13 picks across 2018-2025 were cut before kickoff and
   re-claimed later, including the Justin Jefferson 2020 case the comment is written about.
2. **It charges IR weeks for a roster spot that does not exist.** Checked across every team-week:
   the IR slot is a 17th place *on top of* the 16, so an injured man on IR costs nothing and the
   metric bills him at full replacement anyway. Worth up to **140.9 value** on one row against
   season standard deviations of 120-185. Worse, this league recorded **zero** IR usage before
   2021 and 3.4% of roster-weeks in 2025 — an era artefact inside a metric whose stated purpose
   is era-neutrality.
3. **Where you picked never enters.** A class built from picks 1/24/25 is judged identically to
   one built from 12/13/36.
4. **The structural one: it does not rank drafts.** It ranks what a class *delivered to a roster*,
   which is a joint measurement of drafting and of holding. Every mechanical defect above is a
   symptom — each is a place where roster history leaked into a number about draft day. ADR 0004
   spent its whole alternatives table trying to tune that leak down to zero (+0.13 against roster
   moves) rather than removing its cause.

The user's instruction, which decides this: *"Do not do any rankings based on how the draft
directly contributed to the team's success. I just want to know how you'd rank their draft."*

## Decision

**A pick's return** is his whole NFL season, weeks 1-17, as **value over positional replacement**,
regardless of who held him. Replacement is `replacementAt()` at `STARTS_BAR` — the measured
flex-inclusive start counts, ~12 QB / 29 RB / 31 WR / 12 TE — extended with **12 K and 12 D/ST**,
and drawn over **every NFL player who played** rather than only the ~300 who got rostered. (The
old rostered-pool line carried a measured bias: the man at the bar was often rostered only 12 of
17 weeks, understating the line by up to 1.42×.)

VOR rather than points because points make every question's answer a quarterback: in 2023, **9 of
the top 12 scorers were QBs; by VOR it is 4**, and McCaffrey goes 5th to 1st. Scarcity is the
subtraction.

**A pick can never cost more than the pick**, so a return is floored at zero.
*Added 2026-08-14, after the first board was built and its bust list looked wrong.* Replacement is
free by definition, so a man who finished below it would simply not have been used: the pick bought
an option nobody exercised, worth nothing rather than less than nothing.

The evidence was a bias no one could defend. Unfloored, value is bounded below by −replacement, and
QB replacement runs ~290 against a running back's ~130 — so an injured quarterback was charged about
160 points more than an injured back for the identical outcome of producing nothing. **Nine of the
ten worst picks in league history were quarterbacks.** Floored, none are, and the list reads as
wasted premium picks: Jonathan Taylor at 1, McCaffrey at 1 twice, Adrian Peterson at 1, Justin
Jefferson at 1. That is what a bust is.

ADR 0004 refused this floor and was right to *for the metric it had*: there, flooring made cutting a
bust free and erased the cost of holding a below-replacement man in a roster spot all year. Neither
survives into a board that reads no rosters. The curve is fitted on **floored** values — fit it on
raw ones and it stays negative through the late rounds, so a pick that returned nothing at 190 would
score *positive* for beating a negative going rate.

The cost is real and is not hidden: a man who finished a shade under replacement and a man who never
played are now the same number, separable only by the games printed beside them. And the bottom of
the class board is measurably less stable across fit families than it was (6-7 of 10 shared, against
9-10) because flooring compresses the downside.

**The going rate** for a pick is what that slot returned in that season — a smooth curve fitted
within each season over all of its picks. **Position-blind on purpose.** A per-position curve
would compare a quarterback only to quarterbacks taken at that slot, so "took a QB too early"
could never register as a loss; position-blind is what makes it register, because you spent pick
26 and pick 26 is graded against everything pick 26 could have bought.

**Over the going rate** is return minus going rate, per pick. A class is the **plain sum** across
its picks: trading up is charged the higher expectation it bought, and forgoing a 16th-rounder
forgoes about nothing, which is the right answer for 2020 *All I Do Is Winn* and its 15 picks.

**K and D/ST are in.** A 16-pick draft graded on 11 picks is not a graded draft, and spending pick
100 on a kicker when picks around 100 returned a startable receiver is a real, gradeable mistake
that the going rate prices correctly.

**Except that a defence cannot be a bust.** Skill players and kickers reproduce ESPN's own points
exactly (100.0% of 23,668 player-weeks). Defences do not, and it is not fixable from this source:
the categories are all correct — regression puts defensive TDs at 5.997, return TDs at 5.991, and
every category *not* in this rulebook at ~0.03 — and the yards-allowed ladder reproduces exactly,
but nflverse's play-by-play build carries ~11% more sacks and ~23% more fumble recoveries than
ESPN's feed. Summing player rows instead is identical to the team file (11.8% either way);
excluding opponent defensive scores from points-allowed only reaches 10.3%. **Median season error
11.8%, 90th percentile 21%.**

What that error reaches decides where defences are allowed:

| board | what one D/ST error moves |
|---|---|
| Draft Rankings — 16 picks, season sd **230** class points | **0.65 score points** (median), **1.11** (90th pct), against scores spanning 61-136 |
| Steals & Busts — one pick, D/ST VOR spread only 40-60 points | **20-40% of the spread** |

So **defences are graded in Draft Rankings and excluded from Steals & Busts**; kickers are in
both. This is not the old `SKILL` convention returning — it is a scope drawn where the data can
carry the claim and stopped where it cannot. The cost is an asymmetry that "How this works" has to
state plainly: a defence can sink your draft class but can never appear as a bust.

**Presentation.** The headline is the surplus itself — `+340 over the going rate` — with the
in-season standing beside it, because the number the old board led with was unintelligible and
that was half of why this rebuild happened. Each row also carries the class's **best and worst
single pick**, replacing the raw class total (which answered the roster question this ADR
removes). **Games played** is printed on every pick: it covers injury, suspension, benching and a
rookie who never dressed with one fact, and asserts no cause — ADR 0010's lesson that a badge
should test the raw record. The 100-centred score (`100 + 15z` within season) survives only as
what the all-time list sorts on.

**Data.** Whole-season values for every player come from **nflverse**, which this project already
trusts for schedules, weekly rosters and player ids, and against which all 1,361 archive names
already resolve. `stats_player_week_YYYY.csv` and `stats_team_week_YYYY.csv` are public, need no
authentication, cover 1999-2025, and carry **every category this league scores** including the
kicker distance buckets and all defensive categories; yards-allowed falls out of joining a game to
its opponent's offensive line. Fantasy points are computed from raw stats under **this league's
own rulebook per season**, not taken from anyone else's arithmetic. This retires the authenticated
ESPN browser pull that was scoped for the 2014-2017 gap, and it lands as a re-runnable
`refresh-*.py` script reviewed via `git diff`, per ADR 0002.

**Baked into `index.html`:** every drafted player plus the top 60 at each position each season —
the smallest table from which the whole board can be rebuilt in the browser, which is the actual
transparency requirement. The line never sits past 31, so 60 is provably sufficient; the refresh
script computes the line over the full population and asserts the baked subset reproduces it, so
the saving cannot silently change an answer.

**Steals & Busts moves to the same basis**, and both its filters go. `cashed` (held from week one,
for most of the weeks he was worth holding) is roster management wearing a draft badge. `usable`
is not wrong but **obsolete**: it existed because `gain = posSlot − posFinDr` inflated meaningless
climbs, and under going-rate there is no rank subtraction — a WR40 has low VOR by definition, so a
worthless climb cannot produce a large surplus. A steal is simply the pick furthest above its
going rate; a bust, furthest below. This is the class metric with the sum removed, which is why
the two boards cannot drift.

## Considered options, and the one that was already rejected

**ADR 0008 already rejected this design and must be answered.** Its option D was
`pts − expected at slot`, thrown out on evidence: the expectation did not fall monotonically even
smoothed over ±2 slots (35% inversions at WR, 29% at RB, 25% at QB), raw and smoothed versions
shared only 7 of 12 names, and "eight seasons is not enough data to estimate a per-slot
expectation this way."

Every one of those measurements was taken under conditions this ADR changes, each for an
independent reason:

| ADR 0008 option D | here |
|---|---|
| expectation fitted **per position** (~460 picks each) | **position-blind**, ~192 picks/season pooled |
| currency was **raw points** | **VOR**, which is what makes position-blind pooling coherent |
| raw slot averages, or ±2 smoothing | a **fitted smooth curve** |
| 8 seasons | **12** |

**Measured 2026-08-14, and the obvious explanation is wrong.** The working assumption while this
was being designed was that position-blind pooling on VOR would be what smoothed the curve — more
data per slot, no quarterback distorting a slot's average. It is not. Fitted as a **rolling median
over ±12 picks**, position-blind and on VOR, the curve still inverts **22-26% of adjacent slots in
every season from 2018-2025** — barely better than ADR 0008's 25-35% per-position on raw points.
ADR 0008's objection reproduces almost intact under the conditions that were supposed to dissolve
it.

What actually defeats it is the **fit family**. The same picks fitted as a smooth parametric
curve (least squares on log slot) invert **0 times out of ~165 adjacent slots, in all eight
seasons**. So "a fitted smooth curve" is not a refinement of ADR 0008's ±2 smoothing — it is the
whole of the difference, and this ADR depends on it. A local-window fit is not an acceptable
implementation of this decision.

Pooling and VOR still earn their place: VOR is what makes a position-blind curve *coherent* (a
board of raw points is a board of quarterbacks — in 2023, 9 of the top 12 scorers are QBs and by
VOR it is 4), and twelve seasons beat eight. But they are not what makes the curve monotone.

**Best available** was the other candidate for the baseline and was rejected structurally, not
empirically: pick 1 can only tie or lose (the best man available *is* the best man), and pick 192
can only tie or win. The board would fill with late-round lottery tickets.

**ADP as the baseline** was rejected because it grades timing rather than outcome, and because
this league's own draft board is its revealed ADP and is already in the file. No historical ADP
exists here in any case — `ADP_2026` is a cheat-sheet input.

## The robustness gate

This is a **defining metric** (ADR 0016), so robustness replaces correlation as its evidence, and
ADR 0008's rejection makes it load-bearing rather than ceremonial. Two hard preconditions, both to
be measured on real data before the board ships:

1. **The fitted going-rate curve is monotone decreasing** across the slot range, in every season.
2. **The top 10 and bottom 10 are stable across three different fit families.** If the board moves
   with the curve, the board is measuring the curve.

**Both measured 2026-08-14 on 2018-2025 skill picks, both pass** — with the caveat above that only
a smooth parametric fit clears the first one.

| fit | inversions per season | |
|---|---|---|
| rolling median ±12 | 22-26% | **fails** |
| log-linear least squares | **0 of ~165, all 8 seasons** | passes |
| isotonic | 0 (by construction) | passes |

Stability between the two fits that clear precondition 1: **top 10 identical, bottom 10 identical,
Spearman 0.975** across the whole board. ADR 0008's option D managed 7 of 12 shared names between
its raw and smoothed versions; this is the measurement that says the objection has been answered
rather than ignored.

If either had failed, ADR 0008 was right about this design and it would not ship on this basis.
The gate is re-run on the full board — all twelve seasons, K and D/ST included — before release,
since these numbers are from a prototype covering skill picks from 2018 on.

A third check is the gate under ADR 0016 and is not automatable: the top and bottom ten are put in
front of the user, and they read right or the metric goes back. The Ermin-2023 absurdity passed
every correlation ADR 0004 ran and was caught by a human read.

## Consequences

- **The board grows to 140 rows.** The new metric reads no roster data at all, so the two
  team-years excluded for corrupted roster records (2014 and 2015 *Beasts of the Middle East*)
  come back, and the board stops having an exclusion to explain.
- **The 2020 Round 16 / Pick 8 hole stops mattering.** A missing pick at slot 192 forgoes a going
  rate of approximately nothing.
- **Two long-disclosed data gaps close as a side effect**: 2-point conversions (uncounted for
  2014-2017) and K/D-ST on the coarse whole-season basis. All twelve seasons land on one
  measurement, which was the point of the 2014-2017 work that ADR 0004 could not finish.
- **A team that drafted brilliantly and traded everyone away in October still has the best draft.**
  This is the direct and intended consequence of judging the pick rather than the season.
- **Correlation with wins will fall**, and that is the metric working. It deliberately ignores
  everything after draft day. ADR 0004's +0.43 is not a bar this metric is held to, and re-running
  the house method against it would fail the metric for doing what it was asked to do.
- **Roster-move neutrality stops being evidence of anything.** It is now true by construction, not
  by tuning, so it cannot defend the metric the way it defended ADR 0004's choice.
- The year's draft board gains a going rate and a surplus on **every** pick, so "walk me through
  it" has an answer for a disputed middle pick and not only for the two extremes. ADR 0005 already
  found that grid too wide once, so it is held to the same 375px check.
  - **Reversed on the visible half, 2026-08-15 (`8c1f6f3`), at Justin's call.** The surplus is no
    longer printed on the board: the board records what happened round by round and does not grade
    it, and a coloured number on all 192 cells was the sharpest thing on a page whose job there is
    the record. **The reasoning above still holds and is still served** — each cell keeps a tooltip
    carrying the slot's going rate and what the man returned, so "walk me through a disputed middle
    pick" still has its answer, one hover away instead of always on. The metric is untouched:
    `draftPicksPriced()` is unchanged and Draft Rankings and Steals & Busts are unaffected.
    **Anyone tempted to put it back on by default should read this bullet as a decision, not an
    omission.** The 375px check still applies and still passes; the grid is 1478px, exactly as
    before, because `col.tmcol` is a fixed 120px.
  - **And given a control the same day (`f723253`), because a hover is not a thing a phone has.**
    Leaving the figure in a `title` made it unreachable on the devices this site is actually read
    on — opt-in on a desktop, gone on a phone. `#ratebtn` above the board reveals all 192 at once.
    It is a **board-level** toggle rather than a target per cell for three measured reasons: the
    cell's own tap already belongs to the player link, the non-link area of a 120px cell is about
    20px tall, and 192 cells each carrying a 44px target would grow the 1478px grid. Off remains
    the default, so the paragraph above still describes what the board does when you arrive at it.
- **2014's defensive scoring is unknown and immaterial — closed 2026-08-14.** The change log says
  2015 "added extra defensive and return scoring categories" without naming them, so 2014 is the
  modern set minus some subset and nobody has the settings page. It was closed by measurement rather
  than by discovery, which is the stronger result: stripping *every* uncertain category moves no 2014
  class score by more than **1 point**, and the only order change is between two teams the board
  already ties at 108. A missing category subtracts from every defence at once, so the replacement
  line drops with it and most of the difference cancels before reaching a class; what survives is one
  pick in sixteen. Measured magnitude: those categories are worth a median of 6 and at most 28 points
  to any drafted 2014 defence, against a season averaging 90. The board only becomes sensitive to
  per-club differences of ~10 points a season, which a category change cannot produce.
- **Era comparability is measured, not assumed** — for 2018-2025. The half-PPR era runs ~5% hotter
  than 0-PPR on total drafted VOR, against a 17% swing inside a single era. **2014's whole-block
  yardage scoring is a far larger rulebook difference and is not yet checked**; the same
  measurement is re-run once all twelve seasons are in, and if 2014-2017 do not sit in the same
  band this ADR needs an answer it does not currently have.
