# 0003 — Source draft tiers from FantasyPros half-PPR ECR instead of hand-curation

## Status
Accepted (2026-08-11)

## Context
`TIER_2026` was hand-curated with no source and no refresh path, and would drift stale the same way `ADP_2026` did before its refresh pipeline existed. The user wanted tiers based on ESPN half-PPR rankings, but research confirmed ESPN's public draft-pool endpoint (the one `refresh-adp.py` already calls) only exposes `STANDARD`/`PPR`/`ELIMINATION`/`SUPERFLEX` rank types — no half-PPR field — and no league ID or auth exists in the codebase to query league-scoped ESPN data instead.

Alternatives considered: (a) FantasyPros half-PPR consensus rankings, (b) find the real ESPN league ID and use league-scoped ranks, (c) approximate half-PPR by averaging ESPN's STANDARD and PPR fields. FantasyPros was chosen: their `half-point-ppr-cheatsheets.php` page is fetchable with a plain unauthenticated request (confirmed 200 OK, not disallowed by robots.txt) and embeds a full `ecrData` JSON blob — 841 players, `scoring: "HALF"` confirmed, including a `tier` field already computed via their own 84-expert consensus (gap-based clustering), so no separate tiering algorithm needs to be built.

## Decision
Fetch `TIER_2026` from FantasyPros' embedded `ecrData` (extracted via regex + JSON parse from the half-PPR rankings page HTML), using their `tier` field directly rather than computing our own clustering over ADP or another source.

## Consequences
- Tiers become refreshable pre-draft, same as ADP, rather than a manual snapshot that goes stale.
- Dependency on an undocumented internal page variable (`ecrData`), not a stable public API — the extraction script must fail loudly if the shape changes, not silently produce garbage.
- Matches the site's existing analytical rigor (value/reach is already algorithmic; tiers were the one remaining hand-curated draft-prep input).
- Not pursued: ESPN league-scoped ranks (no league ID in codebase, would need one supplied) and self-computed clustering (redundant with what FantasyPros already provides).

## Correction (2026-08-11, during `refresh-tiers.py` implementation)
The single "all positions" page named above (`half-point-ppr-cheatsheets.php`) does embed
`ecrData` with a `tier` field, but that page's `position_id` is `"ALL"` and the tier is a
**global cross-position tier** — RB/WR dominate the earliest tiers by positional scarcity, so
e.g. the #1 overall-ranked QB was landing in "tier 3" purely because four RBs and four WRs
ranked above him overall. Using it directly per-position, as originally planned, would have
misrepresented the site's per-position groupings (QB tier 1 is supposed to mean "the best
available QBs," not "players who happen to be QBs and are also globally elite").

The actual fix: FantasyPros' *position-specific* draft cheatsheets compute `tier` within that
position instead — `qb-cheatsheets.php` (QB has no PPR variant, since QB scoring doesn't depend
on receptions) and `half-point-ppr-{rb,wr,te}-cheatsheets.php`. `refresh-tiers.py` pulls from
those four URLs, not the single all-positions one. The rest of this ADR's reasoning (use
FantasyPros' `tier` field directly, don't build separate clustering) still holds — only the
specific URL(s) changed.
