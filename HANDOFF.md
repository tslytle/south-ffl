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

## Still open (next round of the grilling session)
These were queued but not yet asked/answered when the session paused to move machines:
- The 2020 Round 16 / Pick 8 mystery pick is effectively closed as "slot known (Revenge Tour's
  traded-away/orphaned pick), player unrecoverable from ESPN data" — revisit only if the user
  turns up a memory or record of who was actually drafted there.
- Anything else surfaced once "rock-solid the existing draft-prep tools" (agreed scope for the
  pre-draft data-analysis tier) gets audited in detail — that audit hadn't started yet.

## Environment notes for a fresh Claude Code session
- This repo has no `.claude/settings.local.json` yet — none of the Mac session's local
  permissions carry over; expect normal permission prompts on the PC.
- `index.html` is the single self-contained site file (~2.5MB). No build step, no backend.
- Draft night countdown target: `new Date("2026-09-07T18:00:00-05:00")`.
