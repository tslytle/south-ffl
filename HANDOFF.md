# Session handoff — continue on PC

This picks up a `/grilling` (+ domain-modeling) session about improving the South FFL site
(looks/functionality/data/data-analysis) ahead of draft night, **Monday Sept 7, 2026, 6:00 PM CDT**.
See `CONTEXT.md` and `docs/adr/` for what's already settled — read those first.

## Resolved this session
- **Repo consolidation** (ADR 0001): this git repo is now the sole working copy. The old Mac
  working folder, `deploy/` folder, and transfer-zip copies are stale/archived — don't edit them.
- **ADP refresh will be automated** (ADR 0002): write-back into `index.html`, reviewed via
  `git diff` before commit, instead of hand-editing ~250 values.
- **Draft tiers will come from FantasyPros half-PPR ECR** (ADR 0003), not hand-curated, not ESPN
  (ESPN's public endpoint has no half-PPR field). Use FantasyPros' own `tier` field directly —
  don't build a separate clustering algorithm.
- **2020 missing draft pick — corrected and closed out as far as data allows.** The prior
  session's "round 16, overall #192, Revenge Tour" note was re-derived from full ESPN Draft
  Recap screenshots (all 16 rounds, "By Round" and "By Team" views) and corrected:
  - The true gap is **Round 16, Pick 8** (ESPN's own sequential numbering skips the missing
    slot entirely, so it isn't literally "#192" — Round 16 only has 191 total picks logged,
    one short of 192).
  - **Roster totals, counted directly from the "By Team" view:**
    - **The Revenge Tour** — 16/16, complete. They picked up compensating extra picks in
      rounds 2 (×3), 4 (×2), and 10 (×2) that exactly offset having zero picks in rounds 1, 3,
      6, and 16. Confirmed via a directly-evidenced round-10 trade (Dallas Goedert, pick #119,
      matching the user's recollection of a trade with Christian Winn's "All I Do Is Winn").
    - **All I Do Is Winn** — 15/16, genuinely short one player. They have zero picks in rounds
      2, 4, and 10 (the same three rounds where Revenge Tour gained extras) but only 2 extra
      3rd-round picks in return — a real 3-for-2 consolidation trade, not a data error. They
      **do** have a Round 16 pick (Jared Goff, #190).
    - Team Brax independently re-verified as 16/16 complete (same compensating-trade pattern,
      rounds 1 and 6).
  - **Conclusion:** by elimination from the Round 16 team list (11 of 12 teams present; Revenge
    Tour is the one absent), the blank Round 16 / Pick 8 slot structurally traces back to
    Revenge Tour's draft position — consistent with the original hypothesis. But since Revenge
    Tour's roster is already complete without it, this reads as a pick they traded away
    pre-draft that was never actually used/recorded by whoever received it (orphaned/forfeited
    in the live 2020 draft), not a genuine "17th player" waiting to be identified.
  - **Still open:** the player, if one was ever actually drafted there, isn't recoverable from
    ESPN's data — it has no player or team attached at all. Would need the user's own memory or
    a leaguemate's records; no ESPN league-ID API lookup exists in the codebase currently.
- **Backups retired.** Once the tier/ADP refresh work was committed (satisfying the "once
  current state is committed to git" precondition), deleted all four stale loose files from the
  parent folder: `index_9-dark_3-improved.BACKUP-before-reorg.html`,
  `index_9-dark_3-improved.backup-before-webp.html`, `South-FFL-Website.zip`, and
  `index_9-dark_3-improved.html` (the pre-git working copy) — all superseded by this git repo
  per ADR 0001. The parent folder now contains only `south-ffl/` (this repo) and unrelated
  session files (`.claude/`, `skills-lock.json`).
- **`refresh-tiers.py` built (ADR 0003)** — and the ADR's original plan had a real bug, caught
  before it shipped: the single "all positions" page ADR 0003 named
  (`half-point-ppr-cheatsheets.php`, `position_id: "ALL"`) has a *global cross-position* `tier`
  field, not a per-position one — RB/WR dominate the early tiers by scarcity, so e.g. the #1
  overall QB was landing in "tier 3". Switched to FantasyPros' actual per-position draft
  cheatsheets instead (`qb-cheatsheets.php` for QB — standard scoring, since QB output doesn't
  depend on PPR; `half-point-ppr-{rb,wr,te}-cheatsheets.php` for the rest), each with a properly
  position-scoped `tier`. Verified against a live render (56 tier dividers, sane groupings).
  Scope intentionally matches the prior hand-curated depth (QB 20 / RB 40 / WR 45 / TE 20,
  K/DST untiered) — the script derives that cutoff from the current file rather than hardcoding
  it, so it won't silently drift if the depth is changed deliberately later.
- **`refresh-adp.py` retrieved from the Mac and rebuilt (ADR 0002)** — the version that existed
  was report-only (never wrote back), pointed at the old pre-git filename
  (`index_9-dark_3-improved.html`), and fetched ESPN's *full-PPR* ADP (`leaguedefaults/3`). Two
  real findings came out of rebuilding it:
  - **The site's ADP source and its own labeling disagreed.** `ADP_2026`'s comment and the UI
    tooltip both said "PFF" (pff.com/fantasy/rankings/draft), while ADR 0002/`CONTEXT.md` both
    described ADP as ESPN-sourced. User's call: switch to ESPN half-PPR — done, both the source
    comment and the UI tooltip (`Consensus ADP (PFF, ...)` → `(ESPN, ...)`) now match reality.
  - **ESPN *does* have a public half-PPR ADP endpoint**, contrary to ADR 0003's research (which
    only checked `playerRankType` labels — true STANDARD/PPR/ELIMINATION/SUPERFLEX, no HALF
    variant there). `leaguedefaults/8` ("FFL Half PPR Scoring") exists and its
    `scoringSettings.scoringItems` confirm 0.5 points/reception — genuinely half-PPR, just
    mislabeled `playerRankType: "PPR"` in ESPN's own metadata. The script verifies that
    0.5-points-per-reception setting itself before trusting any ADP from that id, so if ESPN
    ever renumbers/repurposes it, the script fails loudly instead of silently mislabeling
    full-PPR data as half-PPR. (Doesn't retroactively change ADR 0003's FantasyPros-for-tiers
    decision — that was about the *tier* field specifically, which ESPN's endpoint still doesn't
    expose at all.)
  - Verified against a live render alongside the tier refresh — value/reach delta tags (184 of
    them) recompute correctly, since they're derived live from `ADP_2026` in JS, nothing extra
    needed writing back for those.
  - **Process note, for whoever reads this next:** mid-session, `git checkout -- index.html`
    was run to fix a bug in the ADP script and accidentally discarded the *already-written*,
    not-yet-committed tier refresh along with it (both lived in the same uncommitted
    `index.html`). Recovered by re-running both scripts — but the lesson holds: don't
    blanket-revert a file with mixed uncommitted work, `git stash` or a scoped patch instead.
- **A serious bug in `refresh-tiers.py`/`refresh-adp.py` themselves, caught before shipping
  further.** Both used a single whole-document regex
  (`(?:/\*[\s\S]*?\*/\s*\n)*const NAME = `) to strip/replace the source comment above
  `ADP_2026`/`TIER_2026`. The lazy `[\s\S]*?` inside a repeated group can backtrack across huge
  unrelated spans — on a live run it matched from near the top of the `<style>` block all the
  way down to `const TIER_2026 =`, and `re.sub` replaced that entire span (fonts/CSS/JS
  preamble) with a two-line comment, silently deleting ~2MB of the file. Not caught by the
  script (no shape/size sanity check existed) — caught by chance while eyeballing line numbers
  during the tools audit below. Fixed by replacing the regex with a bounded backward scan from
  the known declaration position (`strip_preceding_comments()` in both scripts) that can only
  ever touch the comment block(s) directly above the target `const`. Verified via a scratch-copy
  test (both scripts, run twice each) before reapplying to the real file. **Lesson:** a
  whole-document regex with a lazy wildcard inside a repeated group is not safe for
  find-and-replace on a large file, even when it "worked" on the first try — test idempotency
  (run twice) and diff `--stat` byte/line counts before trusting a write-back script.

## Started this session: auditing the draft-prep tools ("rock-solid" pass)
Scope, per `CONTEXT.md`: data-correctness and draft-prep-tool fixes only — `CHEAT`,
`DEPTH_TEAMS`, `ADP_2026`, `TIER_2026`, and the value/reach/cliff logic that reads them. Not a
UI/feature audit.

**Checked and clean:**
- `CHEAT`: position-rank sequences, team abbreviations (all 32 valid), bye-week ranges,
  duplicate names/ranks within a position — all clean, no issues found.
- `CHEAT` internal bye-week consistency (every player's bye matches their own listed team's true
  bye, per `DEPTH_TEAMS`) — zero mismatches.
- `DEPTH_TEAMS`: exactly 32 teams, no duplicate/missing abbreviations vs. `NFL_LOGO`.
- Draft night countdown target (`2026-09-07T18:00:00-05:00`) — confirmed Sept 7, 2026 actually
  is a Monday, matches "Monday Sept 7" everywhere else in the docs.
- 40 players present in `DEPTH_TEAMS` but absent from `CHEAT` (backup QBs, TE2s, kickers) —
  spot-checked several for hidden name-typos against `CHEAT`; none found. This is intentional
  scope (`CHEAT` only ranks the draftable/fantasy-relevant depth per position), not a bug.

**Found and fixed:** `CHEAT` had **A.J. Brown listed at `PHI`/bye 10** — stale. He was traded
Philadelphia → New England on 2026-06-01 (confirmed via live web search against SI, NBC Sports,
ESPN, NFL.com, Yahoo — not assumed from training-data knowledge, which predates the trade and
would have said PHI). `DEPTH_TEAMS` already had this correct (`NE`, bye 11) — cross-referencing
the two datasets against each other is what surfaced it; internal-consistency checks on `CHEAT`
alone did not (his stale entry was self-consistent, just outdated). Corrected to
`["A.J. Brown","NE",11]`. This was the only mismatch between the two datasets — confirmed
isolated, not a systemic staleness problem, by re-running the same cross-check after the fix
(zero remaining mismatches).

**Found and fixed:** player-link resolution had a real, if minor, gap. `dstTeam()` (used by
`pLink()`/`cheatLink()` to route D/ST rows to the team's actual page instead of a name search)
only ever handled short 2-3 letter abbreviations (the 2014-2015 archive's "Sea D/ST" style).
`CHEAT.DST` names defences by mascot only ("Broncos D/ST"), longer than any real abbreviation,
so the short-code path silently failed for all 22 team-defense rows on the current draft cheat
sheet — every one fell through to a generic name search instead of linking to the team's real
page. Fixed by adding `MASCOT_ABBR` (built once from `DEPTH_TEAMS`, which already has mascot →
abbreviation pairs) as a second lookup path in `dstTeam()`. Verified live: all 6 sampled D/ST
links now resolve to real team pages (e.g. `pro-football-reference.com/teams/den/2026.htm`)
instead of a broken search. Doesn't touch the archive short-code behavior at all.

**Also checked:** `LINK_TO` is hardcoded to `"pfr"` (not a runtime toggle) — all player links go
to Pro-Football-Reference except where `ESPN_VERIFIED` explicitly overrides per-name (plausibly
deliberate: PFR has no game-log page yet for players before their season starts, so
`ESPN_VERIFIED` exists specifically to bypass that for current-year draft prep — not flagged as
a bug). 285/309 `CHEAT` names resolve to a direct profile link; the remaining 24 (22 were the
now-fixed D/ST rows, plus 2 real players — Treylon Burks, Jaylin Lane — with no `PFR`/`ESPN`
entry yet) degrade gracefully to a name search, a reasonable fallback for genuinely uncovered
players. No duplicate IDs found in `ESPN_VERIFIED` (would indicate two players sharing one
profile page). `CHEAT` has zero null overall-rank values, so the value/reach threshold math
(`max(3, round(orank*0.10))`) never hits its one real edge case (`orank` coercing to 0 in JS
arithmetic if null) — confirmed via data, not just code-reading.

**Audit is in a good stopping place, not fully exhaustive.** Two real bugs found and fixed
(stale A.J. Brown team/bye, broken D/ST links) plus the earlier regex bug in the refresh
scripts. Everything checked came back clean or got fixed — no more known open threads in this
area, but this wasn't an exhaustive line-by-line review of the ~2.5MB file, just the data
structures and code paths most directly tied to pre-draft correctness.

## New feature this session: Draft Rankings
Every team's draft, every year, ranked best-to-worst by total fantasy points scored **while on
the drafting team's own roster** — a player taken, dropped, and later a star elsewhere earns the
drafting team nothing (that's Steals & Busts' job, above). Lives under Draft, Rosters & Trades →
Draft Rankings. Best 10 / Worst 10 shown by default, full list (138 of 140 team-drafts — two
excluded, see below) behind a collapsed "all 138" disclosure. Each row links through to that
year's actual draft board.

**Methodology went through two real revisions before landing where it is now — worth knowing the
history if this gets touched again:**
1. First version summed a player's *entire season* regardless of who held him — wrong, since it
   credited the drafting team for points scored elsewhere after being dropped.
2. Fixed for 2018-2025 (scans each team's own week-by-week roster via `rosterAt`, only counts
   weeks that team actually held him). 2014-2017 initially got a coarser stand-in (whole-season
   in/out based on the end-of-season snapshot) since this file has no week-by-week roster history
   that far back.
3. **User asked for the 2014-2017 gap closed properly rather than left coarse — done.** Pulled
   real per-game box scores directly from ESPN's core stats API (`site.web.api.espn.com/.../
   athletes/{id}/gamelog?season=Y`), independent of the fantasy platform's shorter data
   retention, and applied this league's own scoring rules by hand per game. Combined with
   week-by-week roster membership (`mRoster`, which *does* go back to 2014 even though this
   file's own `ROSTERS.S` doesn't) to attribute each player's weeks to whichever team actually
   held him. All of this ran through the user's authenticated ESPN session via the Claude in
   Chrome browser tool — SWID/espn_s2 cookies were never seen or persisted, only used live,
   read-only, in-browser.

**2014's scoring formula had to be reverse-engineered, not guessed — and was confirmed exactly.**
The site's `SCORING_CHANGES` comment already noted 2014 used "whole points per block of yards"
before 2015's fractional rates, but not the exact block sizes. Solved by algebra against known
season totals: `trunc(passYds/25) + trunc(rushYds/10) + trunc(recYds/10)`, truncated toward zero
**per game** (not floored, and not summed-then-truncated at the season level — per-game trunc
was the only formulation that reproduced known totals exactly). Validated against multiple
players with zero error (Julio Jones, Marshawn Lynch exact; one WR off by exactly 2, consistent
with an untracked 2-point conversion, not a formula error).

**Known, disclosed limits remaining (all called out directly in the page's "How this works"):**
- 2-point conversions aren't in the gamelog stats source and go uncounted for 2014-2017 — a
  handful of isolated 2-point misses, not a systemic gap.
- Kickers and D/ST for 2014-2017 still use the older, coarser whole-season method (full season
  if on the roster when it ended, nothing if not) — real per-week K/D-ST stats (field-goal
  distance buckets from `gamelog`'s `fieldgoals` category; points+yards allowed would need a
  team-boxscore-per-game pull, `site.web.api.espn.com/.../summary?event={id}`, `totalYards`)
  were scoped out as a materially bigger lift for a smaller share of total points. Picked up
  precisely for QB/RB/WR/TE only, which is ~87.5% of roster composition (11 of 16 spots).
- Some ESPN athlete IDs return no gamelog data for **any** season, not just 2014-2017-specific
  gaps (confirmed via direct testing, e.g. Rob Gronkowski's id 13229 fails at every season
  queried) — a real per-player ESPN data hole, not a bug here. Those specific picks fall back to
  the same season-total-if-on-final-roster method as K/D-ST.
- Two team-years are excluded entirely, not shown as a misleading number: 2014 and 2015 "Beasts
  of the Middle East" both have corrupted roster records at the source — 2014's snapshot is
  empty, 2015's is full of players retired years before that season (LaDainian Tomlinson, Randy
  Moss, Donovan McNabb) — confirmed via two independent ESPN data paths (the old snapshot check
  and the new week-by-week `mRoster` pull agree it's broken), not a computation bug. Checked all
  44 2014-2017 team-years for the same pattern; nothing else came back suspicious.

Final per-team-year totals for 2014-2017 are baked into `DRAFT_TOTALS_2014_2017` (replaced the
old raw per-player `SEASON_PTS_2014..2017` tables entirely — nothing else in the file referenced
them, confirmed by grep before removing). `draftRankings()`'s static-year branch is now a direct
lookup into that table instead of a runtime snapshot-based calculation.

## Session 2 (PC): full data + visual audit, Draft Rankings and manager grade rebuilt

### Draft Rankings ranked hoarding, not drafting — rebuilt (ADR 0004)
User's flag: Ermin's 2023 team went 5-9 and its draft still came out **2nd best all-time**. It
wasn't a one-off. The old metric summed every point every drafted player scored while on the
drafting roster, which measured three wrong things:
- **It paid for not touching the waiver wire.** Across the 96 team-drafts from 2018-2025 the raw
  total correlated **-0.41** with roster moves. Ermin 2023 made one move all year and carried two
  kickers and two defences week 1 → week 17 (467 pts), plus Stafford at 282.8 while starting
  three times. 1,054 of his 2,323.9 "draft points" never reached a starting lineup.
- **It rewarded bulk over usefulness** (a bench QB out-banked a starting RB2).
- **It couldn't compare eras** — 17 of the old bottom 20 rows were 2014-2017, an artefact of the
  rulebook, not bad drafting.

Now: **value over replacement** per skill pick (K/DST excluded, matching `SKILL`), prorated by
weeks held, measured against the same `replacementAt()`/`STARTS_BAR` line Steals & Busts uses;
then **z-scored within its own season** and shown as `100 + 15z`. Negatives are kept deliberately
— flooring at 0 re-introduces a churn signal. Five candidate bases were measured before choosing
(table in ADR 0004); VOR-with-negatives is the only one effectively neutral on roster moves
(+0.13) and it tracks wins best (+0.43 vs +0.29 for the old sum).

Result: Ermin 2023 → **37 / 138, score 109, 3rd of 12 that year** — right, given that team was
4th in the league in points scored and lost on schedule luck. 2014-2017 now hold 8 of the top 20
and 8 of the bottom 20 (was 2 and 17). Rows carry `basis: "por" | "total"` plus `score`, `z`,
`inSeason`, `of`; the old `seasonOnly` flag is gone (nothing outside the renderer read it).

**Still coarse:** 2014-2017 can't be measured against replacement — no week-by-week bench data in
this file — so they keep the raw whole-class totals as their value basis, labelled as such on
every row. Closing it means re-pulling per-*player* weekly box scores for those four seasons (the
same ESPN lift already scoped out once for K/D-ST) and baking per-pick rather than per-team.

### Data audit — the archive is clean
Wrote a reconciliation harness (loads the page's own JS in a Node VM with a DOM stub, so the real
functions can be re-run out of band). Checked and clean:
- **Weekly lineup data reconciles exactly with the standings.** For all 8 live seasons, summing
  each team's starters over the regular-season weeks equals its `SEASONS` points-for **to the
  cent**, every team, every year.
- **`ARCH.G` reconciles exactly with the standings too** — W/L/PF/PA per team per season, once
  `resultOf()`'s 2014 tiebreaks are applied (the two whole-number ties in 2014 are already
  handled correctly by `TIEBREAK_WINNER`; a naive check flags them as 4 mismatches, they aren't).
- 1,138 games is exactly right (counted from `ARCH.G`). 17 owners, 12 seasons: right.
- DRAFTS: no duplicate or missing overall picks, no player drafted twice in a year, no unknown
  positions, every drafting team present in both `SEASONS` and `ROSTERS`. The only uneven pick
  count is 2020 "All I Do Is Winn" at 15 — the known, documented missing slot.
- No player name resolves to two different ids **within the same season** (cross-season reuse is
  by design), so the name-keyed point sums can't silently merge two men.
- `OWNERS` covers every team name that ever appears; no team claimed by two owners.

### Visual audit — five real defects, all fixed (ADR 0005)
Measured computed foreground against the *composited* background (alpha tints resolved, gradient
stops taken at their darkest) for all 21,341 text-bearing elements, in both themes.
- **Draft Rankings tables were 1,478px wide for five columns** — they reused `.board`, which is
  fixed-sized for the twelve-round draft grid. Half a screen of sideways scroll on desktop, five
  screens on a phone. New `.drtable` modifier sizes to content: now 986px (fits) on desktop and
  330px on mobile.
- **The 1st/2nd/3rd medal chips took white ink on metal** — 1.67:1 (silver, light) to 3.77:1
  (gold). `--on-chip`'s dark-fill-in-light-mode premise doesn't hold for metal. New `--on-metal`.
- **`textOn()` had no sRGB gamma decode**, so it put white on five clubs' BYE chips that needed
  dark (Miami 3.95, Cincinnati/Denver 3.37, Carolina 4.03, Chargers 4.28). Now picks by real
  contrast ratio; all 32 clubs pass.
- **`--muted`/`--faint` sat under AA** — 3.79:1 at worst in light mode, across thousands of
  elements. Nudged in both themes.
- **Three prose links (`nflverse` ×2) had no colour rule** and rendered browser-default `#0000EE`,
  1.88:1 on dark. Added a base `a{color:var(--accent)}` floor.
- Translucent tints (`.sswk.flip`, `.ssflag`) now paint over `var(--surface)` so a tinted card
  keeps its own base instead of letting the panel behind show through.
- Copy fix: the full board's heading said "all 140"; it renders 138.
- **Both themes now measure zero AA failures.** Treat that as the standing bar.

Also checked and clean: no duplicate element ids, no `NaN`/`undefined`/`[object Object]` anywhere
in the rendered text, no heading-level skips, one `<h1>`, no images missing `alt`, no page-level
horizontal overflow at 1265px or 375px, no console errors.

**Standings overflow — traced properly and fixed.** First pass reported this as a general
`.stand` overflow; it isn't. Closed, every standings table is *exactly* its scroller's width.
The overflow only appears when a row's **DRAFT** disclosure is opened: those pick lines were
`white-space:nowrap` inside the OWNER cell, so they set that column's minimum and pushed the
table 16-49px past its scroller in 7 of the 12 seasons — which is what clipped MOVES. Three
changes, in order of what each buys:
- `.dpicks li` no longer forces `nowrap` (and the name gets `min-width:0`), so a long name wraps
  rather than widening the table. This alone takes worst-case overflow to **0** — it's the
  safety net that guarantees the table can always fit.
- `.stand` non-name cells go from 9px to 7px of side padding, returning ~48px to the OWNER
  column, so in practice **nothing has to wrap**: 0 wrapped lines out of 2,239 with every row in
  every season expanded at once.
- `.dpicks .dm` (the `WR Ind` badge) keeps `nowrap` so it can't split across lines, and `.do`'s
  left padding drops 10px → 6px. The now-redundant phone overrides for both were removed.

Verified across all 12 seasons in three states — all closed, one open, all twelve open —
overflow 0 in every case.

### Manager grade: every profile read "1st in points/game" — one-line bug, three fixes
Reported from a profile screenshot; the cause was a single mis-indexed sum in the league-average
points-per-game table:

```js
s.t.forEach(row => { if(row.length > 3){ pf += row[3]; g += row[0] + row[1]; } });
```

A season row is `[team, W, L, PF, PA, ...]`, so games is `row[1]+row[2]`. This added the team
**name** to the wins — string concatenation — so `pf/g` was `NaN` for every season, and the
`if(LG_PPG[s.y])` guard below treats `NaN` as falsy, so `relPf`/`relG` never accumulated for
anybody. Two consequences, one visible and one not:
- Every manager's era-relative points-per-game was identically **0**, and since ties share the
  best rank, every profile reported **"1st/12"** for scoring.
- SCORING is **19% of the manager grade**, so a fifth of every grade sat pinned at the 50th
  percentile — fully weighted, carrying zero information.

Fixed to `row[1]+row[2]`. League averages now compute and show the half-PPR step they exist to
cancel: **95.9 pts/game in 2020 → 107.4 in 2021**. Points-per-game ranks 1-12 with real spread,
and the era adjustment visibly works — a raw 103.8 ranks 5th, behind a 102.0, because those
seasons skew to the higher-scoring years.

**Two further defects found while auditing the grade, both fixed in the same commit:**
- `pfAxesForRow` drew its percentiles from all **17** owners while the grade ranked itself
  "Nth of **12**" and the bars beside it read `/12` — the same number reached against two
  different fields. `pfRankScope`'s own comment already claimed the bars used the field "the
  grade itself is drawn from"; they didn't. `pfAxesForRow(me)` now scopes through
  `pfRankScope`, so a graded manager is measured against the graded twelve and only an ungraded
  one falls back to the full roll. Worth up to 2.5 grade points; sharpest case sat at the 41st
  percentile for longevity against everyone and the **17th** against his actual field.
- `pfMetrics`' `rank()` used `indexOf` on a sorted array, returning `-1` (rank 0) for any value
  not found by exact identity. Replaced with the count-how-many-beat-you form `pfRankScope`
  already used, so the two agree by construction.

Net: the grade board's top 8 is unchanged; 9-12 reorder (Ermin 9th→12th, Braxton 12th→10th,
Alen 10th→9th). **Every** manager's rank bars change. Shipped as `dca48e1`.

## Session 3 (PC, 2026-08-12): judged-metric pass, then the overhaul begins

A `/grill-with-docs` session. The scope decided was two things: audit the logic behind
everything the site *judges*, then a complete visual and navigational overhaul. Audience was
pinned as **league members on phones, arriving from a group-chat link, ninety seconds of
attention** — that answer decided most of what follows. See ADRs 0006-0010 and `CONTEXT.md`.

### Vocabulary and scope, now written down
`CONTEXT.md` gained four entries: the **Archive tier** (analytics over the settled 2014-2025
record — two sessions of work had landed there with no bucket to put it in), the **soft freeze**
from ~Sept 3, **Franchise Grade**, and **judged metric** — the standard everything below was held
to. A judged metric must be *defensible*, *valid* and *transparent*, with **validity as the
gate**, and anything failing it gets demoted to a plain fact rather than deleted.

### The judged-metric pass — five surfaces, four defects
- **Franchise Grade** (ADR 0006, 0009). Renamed from "manager grade": the weighting always
  measured franchise achievement, and the old label invited an argument it couldn't win. Three
  axes dropped. `LONGEVITY` measured tenure (0.07 with win rate). `LINEUPS` was **noise** —
  intraclass correlation −0.002 across 1,374 graded manager-weeks, with between-manager variance
  *lower* than within-manager, and a 4,000-shuffle permutation test putting the real spread below
  chance median (p = 0.61) — and it carried 17% of the grade. `ACTIVITY` measured a genuinely
  stable trait (split-half 0.82) but a move rate is process, not achievement, and its 0.39 link to
  winning duplicates what `WINNING` measures directly. Four achievement axes remain: HARDWARE
  27.0%, SCORING 25.7%, POSTSEASON 24.3%, WINNING 23.0%.
- **Steals & Busts** (ADR 0008). `gain = posSlot − posFin` subtracted two ranks from different
  populations — drafted (~57 RBs) versus everyone rostered (~85). Le'Veon Bell was "RB4, finished
  RB82" in a year 56 RBs were drafted, and it put a torn preseason ACL (McKinnon, RB13) above
  Michael Thomas at **WR1**. Steals were provably unaffected and untouched.
- **Start & Sit** — the board passes and is unchanged; only its grade axis failed.
- **Trait badges** (ADR 0010). The worst defect of the session: "January Man · Wins in the
  bracket" was on **11 of 17 owners including one with a 0-for-career playoff record**, because
  `postPct` is not a percentage — it holds 0.5 per appearance plus 1 per win, per season,
  regressed. Now 4 of 17, all winning records. Badges now test the **raw** record with a
  minimum-seasons floor, and rank badges use one fixed field.
- **Scouting descriptors** — audited, pass unchanged on four axes.

### The overhaul, first three commits, all merged and live
Decided: dark-native app language, hub plus routed views, **all eighteen surfaces kept**, uniform
shell before bespoke depth, preserved URLs, single file and no build step retained, and the draft
cheat sheet **restyled only, never redesigned** — it is the one surface used under time pressure
on Sept 7 and it will never be rehearsed.
- **Uniform vocabulary** — `.uview/.uhead`, `.uhero`, `.ucard`, `.ustat`, `.uchip`, `.utable` +
  `.uwrap`, `.ugrid`, `.udisc`, all prefixed `u` because `.card`, `.stat` and `.chip` are taken.
  Zero raw hex, so ADR 0005's AA bar is inherited rather than re-argued. New tokens: `--t-hero`,
  a `--sp-1..6` spacing scale (the file had radius and type scales but none for spacing).
- **The hub** — eighteen doors in six groups, one tap each, on plain anchors because `openFor()`
  already opens a target's ancestors. Nav moved to the functional register (Season, Managers,
  History, Drafts, Records, Rules); section headings keep their editorial voice. A phase line
  counts down to the draft, then switches to last season's champion defending — deliberately not
  a standings snapshot, since live 2026 data doesn't exist in this file.
- **Routed views** — the six top-level sections are the six views, the hub is its own route, the
  masthead is hub-route decoration. Nothing moves in the DOM, so every URL ever pasted in the
  group chat still resolves.

### The uniform shell — four steps, all merged and live
The shell restyles the chrome all eighteen surfaces share rather than each surface's internals,
which is what makes eighteen surfaces affordable before the freeze. All four steps are scoped to
an *active routed view*, so with JS off the document is still the single scrolling page it was.

1. **A view presents as a screen, not an accordion.** A view holds exactly one top-level section,
   so that section's collapsible header is chrome with nothing to collapse into. The eyebrow,
   title and note are untouched; the chevron, hover fill, rounded summary and 56px sibling break
   go. Because the header can no longer be clicked, **the router forces the section open on
   reveal**, and a `toggle` guard reopens it if a keypress on the still-focusable `<summary>`
   shuts it. Also restored `.allctl` inside views — the routing commit had hidden Expand/Collapse
   all from the only place they mean anything.
2. **Each board reads as a titled panel** — `--raise`, `--r-md`, own hover and focus.
3. **Nested boards** (under Steals & Busts, Draft Rankings) trade their 2px left rail for a
   quieter panel: `--soft`, `--r-sm`. Indent 18px → 12px.
4. **`.subnav` loses its container and becomes chips.** It had been using `--raise` at `--r-md` —
   which step 2 had just given board panels — so content and navigation-to-content read at the
   same weight.

**Final weight ordering:** screen header (hairline) → board panel (`--raise`, 12px) → nested
panel (`--soft`, 8px) → navigation (no fill). `.allctl` was left alone; it was already in the
language.

**The one rule that governed every step: no shell change may take width from content.** Session 2
fixed standings overflow by returning ~48px to the OWNER column and those tables fit their
scrollers exactly, so panels went on headers only and never on bodies, and where padding changed
it changed *downward*. Verified each step: **twelve standings tables at 0px against their
scrollers**, page overflow 0 across all six views at 1887px and 375px, and AA clear in both
themes on every new surface pair (worst measured 5.23:1).

**Three things worth keeping in mind if this gets touched:**
1. **The router must run last.** Every draw function lays out and measures its tables while still
   visible; hide a section before layout and its tables measure zero and collapse on reveal.
   Verified: 14 tables at 1006px, none collapsed.
2. **The route click handler is on the capture phase**, so a view is revealed before the browser
   scrolls to the anchor.
3. **Routing degrades to nothing.** `body[data-route]` is the only CSS hook and only the router
   sets it, so with JS off the document is the single scrolling page it always was. Print has its
   own rule that ignores routing, or the PDF would be one screen of doors.

**Verification note.** All of the above was measured, not eyeballed — the Node VM harness for the
data and grade work, and a **published `preview.html` in a real browser** for anything visual.
That mattered: the back control measured **75×16px** on a 375px viewport, a third of the touch
minimum, and nothing in the markup or CSS looked wrong. `preview.html` is the ADR 0007 review
mechanism (Pages has no branch previews here) and is deleted in each merge commit.

## Still open
Carried forward across sessions — the first four were queued when the original session paused to
move machines; the rest are from the PC session (2026-08-11/12):
- The 2020 Round 16 / Pick 8 mystery pick is effectively closed as "slot known (Revenge Tour's
  traded-away/orphaned pick), player unrecoverable from ESPN data" — revisit only if the user
  turns up a memory or record of who was actually drafted there.
- Draft-prep tools audit (see section above) is at a good stopping point, not exhaustively
  finished — everything checked so far is clean or fixed; revisit if something new surfaces.
- Draft Rankings' remaining precision gaps (2-pt conversions, K/D-ST still coarse for 2014-2017,
  a handful of ESPN-side missing athlete IDs) are all disclosed in the UI, not hidden — see above
  for exactly what's left if someone wants to push this further.
- The two corrupted end-of-season snapshots for 2014/2015 Beasts of the Middle East are worked
  around in `DRAFT_TOTALS_2014_2017` but not fixed in `ROSTERS.S` itself — if anything else ever
  reads those snapshots directly, the same bad data is still there.
- ~~Awaiting a decision on the two "context" axes in the manager grade.~~ **Decided and shipped
  2026-08-12 — ADR 0006.** `LONGEVITY` dropped (0.07 with win rate), `ACTIVITY` kept (0.39), and
  the grade renamed **Franchise Grade** because the weighting measures franchise achievement, not
  managing. Renormalisation is proportional and automatic — `pfGradeForAxes` divides by the weight
  sum, so the survivors were left untouched and now total 94 deliberately. Top five hold; five of
  twelve change rank. Also added `GRADE_SMALL_SAMPLE = 5`, which flags rather than penalises a
  short career and currently applies to nobody (graded field runs 8-12 seasons).
- **Pre-draft refresh is not yet due.** Both scripts dry-run clean as of 2026-08-12:
  `refresh-adp.py` (ESPN half-PPR id 8 re-verified at 0.5 pts/reception, 250/250 players, largest
  move 0.8 picks) and `refresh-tiers.py` (FantasyPros updated 8/12, 125/125 in-scope matched, one
  tier change: De'Von Achane 2→3). Nothing worth writing yet — re-run both within a few days of
  **Sept 7** when the market and expert consensus have actually moved.
- **`CHEAT` and `DEPTH_TEAMS` have no refresh script.** The two scripts refresh prices and
  groupings for players already on the sheet; neither will ever notice a player changed teams,
  got hurt, or should be added. That gap is what produced the stale A.J. Brown entry. Cross-
  checking `CHEAT` against `DEPTH_TEAMS` is what caught it, and it is still a manual pass.

### Overhaul, remaining — in the order it should be done
The vocabulary, hub and router are merged and live. What's left, with the traps:
1. ~~Apply the uniform shell.~~ **Done — four steps, merged and live.** See the section above.
2. **Bespoke depth, in this order and only if time allows:** hub, Manager Profiles, Standings.
   Draft Rankings is off the list (rebuilt in ADR 0004) and so is the cheat sheet (restyle only).
3. **Dark-default theme polarity** (Q18: dark is the design's home, light stays supported). Not
   started. This is the change most likely to break ADR 0005's zero-AA-failures bar, so it needs
   the contrast sweep re-run against composited backgrounds in *both* themes before it merges.
4. **Deferred `PSTAT`/`ARCH` parse.** 1.33MB of JSON parsed before first paint, and the hub needs
   none of it. **More delicate than ADR 0007 implies:** both are `const X = {…}` object literals,
   so deferring means turning them into strings plus a lazy accessor — and the data contains
   apostrophes (`Wan'Dale Robinson`, `Le'Veon Bell`), which rules out single-quoted strings and
   pushes you to template literals across an 821KB span. That is the same shape of edit that once
   silently deleted ~2MB of this file. Wants a scratch-copy test and a byte-count diff before it
   goes near `index.html`.
5. **Copy gap, low stakes:** four owners now fall back to `Journeyman · Still writing the story`
   alone, which reads wrong for Tate Grainger at ten seasons. There is no badge for a long-serving
   manager with no title and no top-3 finish. Flagged in ADR 0010 as a copy decision, not a
   correctness one.

**Open design questions, not yet put to the user:** whether landing deep inside a long routed view
is acceptable (`#h2h` lands ~16,000px down the History view — correct, but a long scroll), and
whether "← All boards" is the right label and placement for the way home.

### The visual pass (same session, after a user screenshot)
The shell was structure. Colours and fonts were still the old system, because every shell step
deliberately reused existing tokens so ADR 0005's contrast bar could not break. A user screenshot
made that obvious, and also caught a defect four shell steps had been built on top of.

**The bug: hub doors rendered title and sub-line inline** ("Draft NightMonday, September 7").
`a.ucard{display:block}` and the door rule are BOTH 0-1-1, so source order decided, and the hub
rules sit above `.ucard` in that block. The first fix (`a.uhubdoor`) changed nothing for exactly
that reason; `a.ucard.uhubdoor` (0-2-1) wins wherever it sits. **The hub shipped with eighteen
doors verified for target resolution, tap depth, heading order, overflow at two widths and touch
targets — none of which can see a collapsed layout.**

**What changed, and why:**
- **Door titles Oswald -> Inter** at `--t-body`. Oswald is condensed display type: it carries the
  masthead at 90px and reads cramped at card size. It is fine from ~25px up, so view headers
  (30px) and board headers (25px) keep it — the earlier claim that Oswald was "arguing with
  itself" was wrong and was retracted.
- **Door fill `--surface` -> `--raise`.** On the dark ground `--surface` (#121828) sits a few
  points off `--bg` (#0B0F1C), so eighteen cards read as faint outlines.
- **Three colours, three jobs: mint = interaction, gold = editorial voice, neutral = structure.**
  `--accent` had been marking links, hover, focus AND every eyebrow, chip label and rule, so it
  signalled nothing. Eyebrows moved off accent — then off `--muted` too, because fully monochrome
  is wrong for a league trophy case — and onto `--gold-text`, which is also the masthead's italic
  FFL. Measured: 9.15/11.18 dark, 5.23/5.51 light.
- **Hub group labels** `--t-micro`/`--muted` -> `--t-fine`/`--body`; they had been quieter than the
  sub-lines inside the cards they labelled.
- **Board disclosure chevrons** moved back beside their headings (~1155px -> ~905px); the header
  text block was `flex:1` and shoved them to the panel edge.

**Still open on the visual side:**
1. **Panel text stops at ~620px inside a 1177px panel**, so every board has an empty right half.
   Panels must stay full width (the tables need it), so the fix is a two-column header or wider
   notes — not a narrower panel.
2. **Dark-default polarity flip is now LAST, not next.** The user already views in dark, so the
   flip only changes what a first-time visitor gets — lowest visual payoff of anything left, and
   the highest AA risk. Do it with the full 21,341-element sweep, not spot probes.
3. Bespoke depth (hub, Manager Profiles, Standings) is untouched.

### Working notes for whoever picks this up
- **`preview.html` is the review mechanism and it works.** Pages here is classic
  deploy-from-branch on `main` with no `.github/workflows`, so a branch has no URL. Copy the
  branch's `index.html` to `preview.html` on `main`, push, verify in a real browser, delete it in
  the merge commit. Six of these ran cleanly across this session.
- **Don't trust the Pages builds API.** For the last several deploys
  `gh api repos/tslytle/south-ffl/pages/builds` reported the previous commit as latest for ten
  minutes or more while the CDN was already serving the new file. Poll the served file instead —
  `until curl -s <url> | grep -q "<marker>"; do sleep 15; done` backgrounded — and use a marker
  string unique to the commit.
- **Measure in a browser, not by reading.** Every visual defect this session was invisible in the
  source: the back control at 75×16px, the `.subnav`/panel weight collision, and a fixed-width
  merge gate that false-positived on a `@media` breakpoint. Conversely the `.subnav` chips *looked*
  like a touch-target bug at 30px on desktop and were already fine at 44px on mobile — so measure
  before fixing, too.
- **Do the work on the branch.** One shell edit was written while still on `main` and had to be
  stashed across. On a repo where `main` is the live site that is the mistake worth not repeating.

## Environment notes for a fresh Claude Code session
- This repo still has no `.claude/settings.local.json` of its own. There is one a level up, in
  the parent `South FFL Website/` folder, which is where the PC session's permissions actually
  live — nothing carries over from the Mac session.
- `index.html` is the single self-contained site file (~2.5MB). No build step, no backend.
- Draft night countdown target: `new Date("2026-09-07T18:00:00-05:00")`.
- **`main` is the deploy branch.** GitHub Pages serves `tslytle.github.io/south-ffl` straight off
  it, so pushing `main` republishes the public site — there is no staging step. The user's
  standing preference is to commit directly to `main` rather than work on feature branches.
- **Useful trick for auditing this file:** the page's own JS can be loaded into a Node VM with a
  stubbed DOM (`document.getElementById` returning a shared stub, `window` aliased to the
  sandbox), which lets you re-run `draftRankings()`, `pfMetrics()`, `rosterAt()` etc. out of band
  against the real data. `const`/`let` at script top level land in the context's global lexical
  scope, so a later `vm.runInContext('DRAFTS')` can read them. That is how the points-per-game
  bug, the draft-ranking correlations and the standings-overflow numbers were all measured rather
  than guessed.
