# 0018 — Defences on the waiver board, kickers not

## Status
Accepted (2026-08-15). Retires the `SKILL` convention, which ADR 0015 and ADR 0017 had already
overruled in part. Companion to ADR 0017, on a **different** basis — see "Not the same reason".

## Context

`SKILL` was one line and one comment, older than any ADR that touched it:

> *Kickers and defences are streamed, not valued — nobody in this league remembers where a kicker
> went in the draft or who dropped which D/ST. They're kept out of both hindsight boards so the
> lists are about the players people actually argue over.*

That is a claim about **what is interesting**, not about what can be measured. It has been losing
ground ever since: ADR 0015 overruled its first half by putting kickers in Draft Rankings ("a
sixteen-pick draft graded on eleven picks is not a graded draft"), and ADR 0017 put defences on
Steals & Busts. What was left was defences and kickers on the waiver board.

The user asked for defences there too. `SKILL` is now unreferenced and is deleted.

## Not the same reason as ADR 0017

ADR 0017 turned on **reconstruction accuracy**: defences could only be rebuilt from public stats
to within 12%, and fixing that took it to 2%. **None of that applies here.** Waiver values are
read straight out of the league export — the points ESPN actually awarded, week by week, to men on
rosters. Nothing is reconstructed, so nothing was ever inaccurate.

What gates this board is a different thing entirely, and it is the reason the change is not simply
"delete the filter".

## The actual constraint

A wire value is *points minus the replacement at that position that same week* — the board's own
header: "what he gave you above what was sitting there for free". That replacement is read off the
**rostered pool**, because the export only records rostered men; the genuinely free agent is
invisible to it. So the proxy is the best man past the startable bar among those rostered.

**A position can only be priced here if the rostered pool reliably runs past its bar.** If it does
not, there is nobody past the bar, the code falls back to the worst rostered man at that position,
and the subtraction silently becomes "minus the worst starter" — which flatters every pickup at
that spot. Deleting the filter without checking this would have credited defences and kickers with
close to their raw points and put them at the top of the board for the wrong reason. That is
exactly the failure the header warns about: "Raw points flattered the wrong moves."

Measured over all 136 wire weeks, 2018-2025:

| position | bar | rostered, thinnest week | median | weeks with nobody past the bar |
|---|---|---|---|---|
| QB | 12 | — | 22.9 | **0** |
| **D/ST** | 12 | 14 | 19 | **0** |
| **K** | 12 | 12 | 14 | **31 — 22.8%** |

## Decision

**Defences are priced on the waiver board. Kickers are not**, and that asymmetry is a measurement
rather than a preference: in nearly a quarter of weeks the league did not roster a thirteenth
kicker, so there was no replacement to measure against.

`WIRE_POS` carries this and states the numbers. If kicker rosters ever deepen, re-run the count —
**do not add K on the grounds that D/ST is there.**

`BAR_POS` is introduced alongside `LINEUP` so the D/ST bar is **measured rather than assumed**.
Every team looks like it starts exactly one defence; counted, it is 11.76 to 12.00 per week, which
rounds to 12 in all eight seasons. It is kept out of `LINEUP` itself because `LINEUP` drives
`replacementAt()`'s flex model, which is a skill-position idea a defence has no business in.

## Consequences

* 403 defensive pickups and 363 defensive drops enter the board. Defences are 23.5% of all wire
  moves and take 32% of the top fifty — a modest skew, not a takeover, and the visible board caps
  at three per position regardless. The skew is real and explicable: a defence is cheap to acquire
  early and a good one gets held all year, which is what the board is built to reward.
* **The Record Book's "Best pickup ever" changes hands**, from Kyren Williams (2023, +123.7) to
  the **2018 Bears D/ST**, claimed in week 2 and held all sixteen weeks for +139.0. Face-valid:
  that was the best fantasy defence of its season by a distance, and picking it up in week 2 is
  the kind of move the card exists to celebrate. "The costliest cut" is unchanged.
* That card's copy loses its pronoun — "the weeks he was held" reads wrong once the answer is the
  Bears.
* Start & Sit is unaffected: it takes the same `startsBar()` but gates its own pool on `LINEUP`,
  so the added D/ST bar is inert there. Verified — its skill bars are unchanged at QB 12, RB 29,
  WR 31, TE 12.
