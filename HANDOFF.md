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

## Still open (next round of the grilling session)
These were queued but not yet asked/answered when the session paused to move machines:
- The 2020 Round 16 / Pick 8 mystery pick is effectively closed as "slot known (Revenge Tour's
  traded-away/orphaned pick), player unrecoverable from ESPN data" — revisit only if the user
  turns up a memory or record of who was actually drafted there.
- Draft-prep tools audit (see section above) is at a good stopping point, not exhaustively
  finished — everything checked so far is clean or fixed; revisit if something new surfaces.

## Environment notes for a fresh Claude Code session
- This repo has no `.claude/settings.local.json` yet — none of the Mac session's local
  permissions carry over; expect normal permission prompts on the PC.
- `index.html` is the single self-contained site file (~2.5MB). No build step, no backend.
- Draft night countdown target: `new Date("2026-09-07T18:00:00-05:00")`.
