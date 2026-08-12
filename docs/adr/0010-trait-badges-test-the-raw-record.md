# 0010 — Trait badges test the raw record, in one fixed field

## Status
Accepted (2026-08-12)

## Context
`computeTraits()` awards the badges shown on a manager's profile and on the
Awards Wall. They are meant to be *facts* — `CONTEXT.md` distinguishes them from
judged metrics on exactly that basis. Three things stopped them being facts.

### "January Man · Wins in the bracket" went to a manager who has never won one
The test was `pg && me.postPct >= 0.6`. But `postPct` is not a percentage:

```js
postPct: shrink(0.5 * o.papp + o.pw, o.seasons, mPostVal, K_POST),
```

It holds **0.5 per playoff appearance plus 1 per playoff win, per season**,
regressed toward the league mean. So merely reaching the bracket contributes 0.5
and nearly clears a 0.6 "rate" threshold on its own, and for a short career the
league prior clears it unaided. The badge went to **11 of 17 owners**, including:

| owner | playoff record | raw % |
|---|---|---|
| Azer Sabanovic | 0-1 | **0%** |
| Gavin Spurrier | 1-2 | 33% |
| Nick Drake / RC Muncy | 1-1 | 50% |
| Leo Thaweechok / Adam Boggess | 5-5 | 50% |
| Tate Grainger | 4-5 | 44% |

The POSTSEASON grade axis reads the same field correctly — as a value to
percentile-rank, which is what it is. Only the badge misread it as a rate.

### Badges tested regressed rates while the profile printed raw ones beside them
`Ringless`, `January Man` and `Regular` all tested `pfMetrics`' shrunk values,
while `pfBuild` prints the raw rate in the stat boxes on the same card. Seven of
seventeen owners carried a badge that contradicted their own displayed numbers.
The sharpest: Gavin Spurrier, raw 57.7% win rate and no ring, but *no* `Ringless`
badge, because his shrunk rate is 53.8%.

### Rank badges meant different things for different people
`Big Bat` and `Wire Hawk` ranked through `pfRankScope`, so a graded manager was
ranked among the twelve graded and an ungraded one among all seventeen. Adam
Boggess is 3rd of twelve and 4th of seventeen, and wore "Top-3 scoring" on the
strength of the narrower field. This is the same defect fixed in `pfAxesForRow`
in an earlier session, still present here.

## Decision
**A badge states a fact about the record, so it tests the raw record.** Shrinkage
exists to rank careers of different lengths against each other; it has no place
in describing one. `Ringless` uses `o.w / gp`, `January Man` uses `o.pw / pg`,
`Regular` uses `o.papp / o.seasons`.

**A fact needs enough record to be a fact.** Every rate badge requires
`GRADE_MIN_SEASONS`; `January Man` additionally requires **four playoff games**,
so a 1-1 record cannot claim it. Absolute facts — titles, tenure — keep no floor.

**Rank badges read one fixed field.** `M.rank` over everyone with the data,
never `pfRankScope`, so "Top-3 scoring" means one thing for everybody.

Badge names and sub-labels are unchanged, so the Awards Wall needs no edit.

## Considered options
- **Rename the badge to match what it measured** — "Playoff regular" instead of
  "January Man". Rejected: the label is good and the honest fix is to measure
  what it says.
- **Keep the shrunk rates and print them on the profile too** — rejected. It
  would put two win rates on one card to defend a threshold, when the badge
  should simply describe the record the card already shows.
- **Drop `January Man`** — unnecessary; it works once it tests playoff results.

## Consequences
- `January Man` falls from 11 of 17 to **4 of 17**: Ryan Boggess (10-6), Michael
  Boggess (11-7), Justin DeCesare (5-3), Christian Winn (5-2). Every one has a
  winning playoff record.
- Seven owners change badges. Adam Boggess loses `Big Bat` to the scope fix. Azer
  Sabanovic loses all three of his, which were artefacts of a single season.
- **Four owners fall back to `Journeyman · Still writing the story` alone**, and
  for Tate Grainger (10 seasons) and Gavin Spurrier that copy now reads oddly —
  it is written for a newcomer, and they are not. The badge set has no label for
  a long-serving manager without a title or a top-3 finish. Flagged, not fixed:
  it is a copy decision, not a correctness one, and it belongs with the overhaul.
- The descriptors were audited alongside and **pass unchanged**. All seventeen
  read cleanly on the four axes ADR 0009 left ("A 2-time champion and a manager
  who shows up in January", "A points machine, but the bracket has been unkind").
- This closes the judged-metric pass opened in this session. Every surface in
  scope has been through the gate: the Franchise Grade (0006, 0009), Draft
  Rankings (0004, already passing), Steals & Busts (0008), Start & Sit (0009,
  demoted to factual) and the badges and descriptor (0010).
