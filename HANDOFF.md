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
- **2020 missing draft pick (round 16, overall #192)**: confirmed medium-high confidence it
  belongs to **"The Revenge Tour" (Alen Huseinbegovic)** — every other team has exactly one
  round-16 pick logged, Revenge Tour has none, and this is reinforced by a directly-evidenced
  round-10 trade (Christian Winn's "All I Do Is Winn" turn at pick #119 was made by Revenge Tour
  — Dallas Goedert — matching the user's own recollection). **Still open: what player Revenge
  Tour actually took with pick #192** — not yet known, needs the user's memory/records or a real
  ESPN league-ID lookup (none exists in the codebase currently).
- **Backups**: retire `.BACKUP-before-*.html` files once current state is committed to git —
  agreed, not yet executed as of this handoff.

## Still open (next round of the grilling session)
These were queued but not yet asked/answered when the session paused to move machines:
- Confirm the player taken with 2020 pick #192 (Revenge Tour), or accept "team known, player
  unknown" as the final state of that record.
- Implementation specifics for the ADP write-back script (ADR 0002) — not yet built.
- Implementation specifics for the FantasyPros tier-refresh script (ADR 0003) — not yet built;
  extraction pattern is documented in ADR 0003 (`ecrData` regex + JSON parse off
  `fantasypros.com/nfl/rankings/half-point-ppr-cheatsheets.php`).
- Executing the backup cleanup (delete `.BACKUP-*.html` files) now that git covers history.
- Anything else surfaced once "rock-solid the existing draft-prep tools" (agreed scope for the
  pre-draft data-analysis tier) gets audited in detail — that audit hadn't started yet.

## Environment notes for a fresh Claude Code session
- This repo has no `.claude/settings.local.json` yet — none of the Mac session's local
  permissions carry over; expect normal permission prompts on the PC.
- `index.html` is the single self-contained site file (~2.5MB). No build step, no backend.
- Draft night countdown target: `new Date("2026-09-07T18:00:00-05:00")`.
