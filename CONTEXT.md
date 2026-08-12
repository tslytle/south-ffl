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

## Pre-draft tier vs. in-season backlog
Two-tier scope agreed for this project. **Pre-draft tier**: data-correctness and draft-prep-tool fixes only (ADP refresh, tiers, cheat sheet, known data gaps) — the concrete deliverable ahead of draft night, Sept 7 2026. **In-season backlog**: net-new analytical features (live stats, weekly recaps) that need actual 2026 game data to mean anything — explicitly deferred, not part of this deliverable.
