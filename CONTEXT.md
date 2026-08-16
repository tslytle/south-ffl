# South FFL — Glossary

## Authoritative copy
The single working copy of the site is **this git repository** (`github.com/tslytle/south-ffl`, `index.html` at repo root). Prior to 2026-08-11 the project existed as loose file snapshots (a Mac working folder, a PC transfer zip, a `deploy/` folder) with no version control; these are now retired in favor of git history. "Authoritative" means: this is the only copy anyone should edit.

## ADP (Average Draft Position)
Crowd-sourced consensus of *where players actually get drafted* across many real draft rooms. Sourced from ESPN's public draft-room pool (`refresh-adp.py`). Distinct from ECR — ADP reflects draft-room behavior, not analyst opinion of player quality.

## ECR (Expert Consensus Rank) / Tier
Analyst-driven ranking, distinct from ADP. South FFL's `TIER_2026` is sourced from **FantasyPros' half-PPR consensus rankings** (`ecrData`, scoring `"HALF"`), not hand-curated and not ESPN-derived (ESPN's public endpoint has no half-PPR rank field — only STANDARD/PPR/ELIMINATION/SUPERFLEX). FantasyPros' own `tier` field (gap-based clustering over ~84 experts' ranks) is used directly rather than South FFL computing its own clustering.

## Value / Reach
Existing derived tag on the draft cheat sheet: `delta = ADP − expertRank`, thresholded at `max(3, 10% of rank)`. "Value" = falls later than ranked (good value if still there); "Reach" = drafted earlier than ranked. Already algorithmic, not manual — noted here because tier-sourcing changes (see ADR 0003) feed this calculation's `expertRank` input.

## Going rate / over the going rate (Draft Rankings)
The **going rate** is what a pick at that slot was worth in that season — a smooth curve fitted,
within each season, over what all of that year's picks actually returned. Deliberately
**position-blind**: one curve for slot N, never one per position, because a per-position curve
would only ever compare a quarterback to other quarterbacks taken there and "took a QB too early"
could never register as a loss. **Over the going rate** is a single pick's return minus its going
rate; a class's figure is the plain sum across all sixteen picks, so trading up is charged the
higher expectation it bought and forgoing a 16th-rounder forgoes about nothing.

A pick's **return** is his *whole NFL season* (weeks 1-17) as value over positional replacement,
**floored at zero** and **regardless of who ended up holding him** — the board judges the pick, not
the season that followed it. The floor is what stops a pick costing more than the pick: replacement
is free, so a man who finished below it would simply not have been used. It also removes an
indefensible position bias — value is bounded below by −replacement, and QB replacement runs ~290
against a back's ~130, which put nine quarterbacks in the ten worst picks of all time. Nothing about who was dropped, started, benched or traded enters, which is what
makes it a ranking of drafts rather than of management. K and D/ST are in: a kicker taken in the
ninth round is a real and gradeable decision, and a 16-pick draft graded on 11 picks isn't one.
Replacement is `replacementAt()` cut at `STARTS_BAR`, extended to 12 K and 12 D/ST and drawn over
every NFL player rather than only the rostered pool.

Because replacement is recomputed under each season's own rulebook the figure is already
era-comparable — measured, the half-PPR era runs about 5% hotter than 0-PPR against a 17% swing
*inside* a single era — so "+340" means roughly the same thing in any year. The 100-centred score
(`100 + 15z` within season) is what the all-time list sorts on, not a claim the headline number
can't already make. Per ADR 0015, which supersedes ADR 0004. Distinct from **Value / Reach**
above, which is a pre-draft ADP tag on the cheat sheet and unrelated.

## Scope tiers: pre-draft, archive, in-season
Three-tier scope. **Pre-draft tier**: data-correctness and draft-prep-tool fixes (ADP refresh, tiers, cheat sheet, known data gaps) — the concrete deliverable ahead of draft night, Sept 7 2026. **Archive tier**: analytics and presentation over the settled 2014-2025 record (Draft Rankings, manager grade, Steals & Busts, the visual system) — correctness matters, urgency does not; needs no 2026 data. Named 2026-08-12, after two sessions' worth of work had landed here without the two-tier model having a bucket for it. **In-season backlog**: net-new features (live stats, weekly recaps) that need actual 2026 game data to mean anything — explicitly deferred.

## Franchise Grade
The 55-99 figure on a manager's profile, formerly "manager grade". It measures **franchise achievement** — what this franchise won — not managerial skill: bracket outcomes and regular-season record dominate the weighting, and a title is acknowledged in the code's own comment as the noisiest thing on the record. Renamed per ADR 0006 because the old label invited an argument the weighting could not win ("I'm the better manager, I just lost a bracket") and which was correct. **Four axes, every one of them an achievement**: HARDWARE, POSTSEASON, SCORING, WINNING. `LONGEVITY` (tenure, not managing) went in ADR 0006; `LINEUPS` (measurably noise) and `ACTIVITY` (real, but process rather than achievement) went in ADR 0009. Only managers with at least `GRADE_MIN_SEASONS` (3) seasons are graded — a sample-size requirement, not a reward for tenure; short-tenure grades are marked as small samples. Distinct from a **trait badge**, which describes rather than ranks: a threshold over the **raw** career record, shared with the Awards Wall. Badges never test the regressed rates the grade ranks on — shrinkage is for comparing careers of different lengths, not for describing one — and every rate badge carries a minimum-seasons floor so a fact isn't asserted on two games (ADR 0010).

## Judged metric
Any site number that ranks or grades people rather than reporting a fact — the manager grade and its axes, Draft Rankings' score, Steals & Busts, Start & Sit. Distinct from a **factual extreme** (Record Book highs and lows), which is just the archive sorted and needs no defence. Every judged metric owes **defensibility** (a manager who disputes it can be walked through the reasoning) and **transparency** (the UI shows its work, weights included). The third bar depends on which of two kinds it is, and they cannot be held to the same evidence (ADR 0016).

An **estimating metric** claims to measure something outside itself — Franchise Grade claims to measure franchise achievement — so it can be checked against that thing, and must be: **valid**, meaning it measurably correlates with what it claims to measure. Validity is the gate for this kind; an axis that cannot produce a correlation defending its own existence gets dropped or reweighted, which is how ADR 0009 killed `LINEUPS`. ADR 0004's five-candidate comparison is the house method.

A **defining metric** *is* the definition of the thing rather than an estimate of it — Draft Rankings' going rate defines what a good draft is, and deliberately excludes everything that happened after draft day. There is nothing external to correlate it against, and correlating it with team success would only reward it for measuring what it exists to ignore. It clears instead: **well-defined**, **robust** (the ranking does not move when an arbitrary modelling choice changes), and **face-valid** (it reads right to the people it judges). Face validity is the gate for this kind — the Ermin-2023 absurdity was caught by a human read that every correlation had passed.

## Role table
The five jobs colour is allowed to do, per ADR 0012: **interaction** (`--accent`, mint — links, controls, focus, hover, and nothing else), **ceremony** (`--gold*`), **sign** (`--pos`/`--neg`, signed quantities only), **podium** (the metals, placement only) and **encoding** (`--enc*` — "this is category N": legends, category tags, chart series, row-state markers). Structural furniture is `--line`, which is the absence of a role rather than one of them. The table's load-bearing claim is that mint means *you can touch this*; it holds only because 42 static-text rules stopped being mint, and it would collapse the moment mint is put back on something inert. Distinct from a **judged metric**, which is about whether a number may be asserted; the role table is about whether a colour may be used.

## Measure
The width of the thing a header introduces. ADR 0014's rule — a header never spans wider than its own content — means the constraint lives on the disclosure rather than the panel, so a board's header and its panel share both edges by construction. Related: the **left spine**, the single left edge running down the page, which is what makes the remaining ragged right edges read as deliberate rather than unfinished. A remainder row may centre; a group that is entirely a remainder may not, because it has nothing to be a remainder of.

## Plate
The shared ground every manager mark sits on — one background, one ring, one circular mask, one optical size, across the manager grid, the profile, the champion rows, the awards wall, the hub masthead and the id chip. Dark in both themes, and not by preference: the previously unplated marks are white artwork on transparent PNGs drawn for a dark ground, so a light plate erases them, while photographs carry their own background and survive either. The initials fallback is the same plate with ink letters, so a manager with no logo reads as a considered mark rather than a missing asset. Genuinely dark artwork remains the weak case (one logo), fixable only with a re-cut asset.

## Elevation
Whether a fill sits above or below the ground it is on, and by how much — a measured property, not an impression. Per ADR 0022, anything that reads as a container clears **1.5:1** against what it actually sits on (in light, the bounding hairline carries this duty), and a control's boundary clears **3:1** against its own fill. The ladder runs sunken → ground → surface → raise, and every fill picks a direction; there is no neutral third option. Elevation alternates with **role, not depth**: a closed board is a control and is raised; open, it is content and drops to the ground, freeing the level below it to rise again.

## Container vocabulary
The six things a piece of content may live in, replacing the single all-purpose bubble: **raised control** (tap it and it navigates), **chip** (a fact attached to a control, never free-floating), **editorial block** (no box; hairline rules), **bare figure** (a statistic is number + label, never a box), **plate** (the manager mark, protected), **person** (a card-grid cell with no card; the plate does the work). A container is chosen by what the content *is*, and the container is shaped by the text — never the text poured into the container.

## Reference mapping
Which outside voice governs which register, settled 2026-08-15: **Letterboxd** owns the editorial register and the card grids; **Sleeper** owns product chrome (elevation, chips, controls, phone composition); **ESPN and FantasyPros** are density benchmarks only — information per row, never appearance. Judged on desktop; the phone is *composed*, not squeezed — it may look different, never crushed.

## Closed-state fact
What a collapsed board says instead of prose: its size — `12 seasons · 2014–2025`, `1,138 games · boxscores from 2018`. The description moves to the opened state, where it is orientation rather than an obstacle. Makes every closed bar the same height **by construction** rather than by a rule someone maintains. Corollary, **one masthead per screen**: a group view orients the reader once; per-panel kickers go where they duplicate the group's.

## Soft freeze
From ~2026-09-03 until draft night: data-refresh commits (`refresh-adp.py`, `refresh-tiers.py`, cheat-sheet corrections) still land; code and layout changes stop. `main` is the deploy branch and GitHub Pages serves it directly, so every push is a live publish with no staging step — the freeze is the substitute for one.
