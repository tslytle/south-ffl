# South FFL — Glossary

## Authoritative copy
The single working copy of the site is **this git repository** (`github.com/tslytle/south-ffl`, `index.html` at repo root). Prior to 2026-08-11 the project existed as loose file snapshots (a Mac working folder, a PC transfer zip, a `deploy/` folder) with no version control; these are now retired in favor of git history. "Authoritative" means: this is the only copy anyone should edit.

## ADP (Average Draft Position)
Crowd-sourced consensus of *where players actually get drafted* across many real draft rooms. Sourced from ESPN's public draft-room pool (`refresh-adp.py`). Distinct from ECR — ADP reflects draft-room behavior, not analyst opinion of player quality.

## ECR (Expert Consensus Rank) / Tier
Analyst-driven ranking, distinct from ADP. South FFL's `TIER_2026` is sourced from **FantasyPros' half-PPR consensus rankings** (`ecrData`, scoring `"HALF"`), not hand-curated and not ESPN-derived (ESPN's public endpoint has no half-PPR rank field — only STANDARD/PPR/ELIMINATION/SUPERFLEX). FantasyPros' own `tier` field (gap-based clustering over ~84 experts' ranks) is used directly rather than South FFL computing its own clustering.

## Value / Reach
Existing derived tag on the draft cheat sheet: `delta = ADP − expertRank`, thresholded at `max(3, 10% of rank)`. "Value" = falls later than ranked (good value if still there); "Reach" = drafted earlier than ranked. Already algorithmic, not manual — noted here because tier-sourcing changes (see ADR 0003) feed this calculation's `expertRank` input.

## Draft score / value over replacement (Draft Rankings)
Two numbers, per ADR 0004. **Value** = for each drafted skill player (K and D/ST excluded, same as
`SKILL` everywhere else), the points he scored *while on the drafting team's own roster* minus
replacement level at his position, prorated by the weeks that team held him. Replacement level is
`replacementAt()` cut at `STARTS_BAR` — the same line Steals & Busts uses, so the two boards can't
drift. Negatives are kept: holding a below-replacement man all year cost a real roster spot.
**Draft score** = that value z-scored within its own season, shown as `100 + 15z`, so 100 is an
average draft for that year. The board sorts on score, not on points. 2014-2017 have no
week-by-week bench data, so their value is the raw whole-class total from
`DRAFT_TOTALS_2014_2017` (K/DST included) — z-scored the same way but labelled on every row as
the coarser basis it is.

## Scope tiers: pre-draft, archive, in-season
Three-tier scope. **Pre-draft tier**: data-correctness and draft-prep-tool fixes (ADP refresh, tiers, cheat sheet, known data gaps) — the concrete deliverable ahead of draft night, Sept 7 2026. **Archive tier**: analytics and presentation over the settled 2014-2025 record (Draft Rankings, manager grade, Steals & Busts, the visual system) — correctness matters, urgency does not; needs no 2026 data. Named 2026-08-12, after two sessions' worth of work had landed here without the two-tier model having a bucket for it. **In-season backlog**: net-new features (live stats, weekly recaps) that need actual 2026 game data to mean anything — explicitly deferred.

## Franchise Grade
The 55-99 figure on a manager's profile, formerly "manager grade". It measures **franchise achievement** — what this franchise won — not managerial skill: bracket outcomes and regular-season record dominate the weighting, and a title is acknowledged in the code's own comment as the noisiest thing on the record. Renamed per ADR 0006 because the old label invited an argument the weighting could not win ("I'm the better manager, I just lost a bracket") and which was correct. **Four axes, every one of them an achievement**: HARDWARE, POSTSEASON, SCORING, WINNING. `LONGEVITY` (tenure, not managing) went in ADR 0006; `LINEUPS` (measurably noise) and `ACTIVITY` (real, but process rather than achievement) went in ADR 0009. Only managers with at least `GRADE_MIN_SEASONS` (3) seasons are graded — a sample-size requirement, not a reward for tenure; short-tenure grades are marked as small samples. Distinct from a **trait badge**, which describes rather than ranks: a threshold over the **raw** career record, shared with the Awards Wall. Badges never test the regressed rates the grade ranks on — shrinkage is for comparing careers of different lengths, not for describing one — and every rate badge carries a minimum-seasons floor so a fact isn't asserted on two games (ADR 0010).

## Judged metric
Any site number that ranks or grades people rather than reporting a fact — the manager grade and its axes, Draft Rankings' score, Steals & Busts, Start & Sit. Distinct from a **factual extreme** (Record Book highs and lows), which is just the archive sorted and needs no defence. Every judged metric must clear three bars: **defensible** (a manager who disputes it can be walked through the reasoning), **valid** (it measurably correlates with what it claims to measure), and **transparent** (the UI shows its work, weights included). Validity is the gate — an axis that cannot produce a correlation defending its own existence gets dropped or reweighted. ADR 0004's five-candidate comparison is the house method for meeting it.

## Soft freeze
From ~2026-09-03 until draft night: data-refresh commits (`refresh-adp.py`, `refresh-tiers.py`, cheat-sheet corrections) still land; code and layout changes stop. `main` is the deploy branch and GitHub Pages serves it directly, so every push is a live publish with no staging step — the freeze is the substitute for one.
