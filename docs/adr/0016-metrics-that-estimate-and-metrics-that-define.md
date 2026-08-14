# 0016 — Judged metrics split into those that estimate and those that define

## Status
Accepted (2026-08-14). Amends the *judged metric* standard set out in `CONTEXT.md` and used by
ADR 0004, 0006, 0008, 0009 and 0010.

## Context

`CONTEXT.md` required every judged metric to clear three bars — **defensible**, **valid**,
**transparent** — and spelled validity out as *"it measurably correlates with what it claims to
measure"*, naming it **the gate**: "an axis that cannot produce a correlation defending its own
existence gets dropped or reweighted." That rule has earned its place. It is why ADR 0009 killed
the `LINEUPS` axis, which carried 17% of the Franchise Grade while measuring noise (intraclass
correlation −0.002 across 1,374 manager-weeks, permutation p = 0.61).

ADR 0015 rebuilds Draft Rankings to answer one question: *how good was this draft, as a draft* —
explicitly excluding what the class went on to do for its team. The user's instruction was direct:
"Do not do any rankings based on how the draft directly contributed to the team's success."

That metric **cannot clear the validity bar as written**, and not because it is weak. There is
nothing external to correlate it against. It does not estimate a hidden quantity called draft
quality; it *is* a definition of draft quality. The only correlates available are team outcomes —
wins, points for — which the metric exists to ignore. Holding it to a correlation would reward it
precisely for leaking back in what ADR 0015 removed, and would have scored the *old*, defective
metric higher than the new one.

Two options were rejected. Finding a non-team correlate (next season's ADP, end-of-season expert
ranks) buys a number that looks like validation while measuring the same seasons — circular.
Declaring Draft Rankings not a judged metric is simply false: it ranks people by name and they
will argue with it, which is the definition.

## Decision

Judged metrics are of two kinds, and they cannot be held to the same evidence.

An **estimating metric** claims to measure something outside itself, so it can be checked against
that thing. Franchise Grade claims to measure franchise achievement; `LINEUPS` claimed to measure
lineup skill. These keep the existing bar unchanged: **defensible, valid, transparent**, with
**validity as the gate**, and ADR 0004's five-candidate comparison as the house method.

A **defining metric** is the definition of the thing rather than an estimate of it. Draft
Rankings' going rate defines what a good draft is. These clear instead:

- **Well-defined** — every input, cut and threshold is stated and none of them is arbitrary in a
  way that changes the answer.
- **Robust** — the ranking does not move when an arbitrary modelling choice changes. Refit,
  rewindow, re-specify; if the board moves, the board is measuring the model.
- **Face-valid** — it reads right to the people it judges. **This is the gate.**

Both kinds still owe defensibility and transparency; neither is relaxed.

Face validity is the gate for defining metrics because the record says so. Ermin Cerimovic's 2023
team went 5-9 and ADR 0004's predecessor put its draft **2nd best all-time**. That passed every
internal check the site could run. It was caught by a human looking at a row and saying no. A
metric that defines its own subject has no external referee, so the people it judges are the
referee, and their read is evidence rather than opinion.

## Consequences

- Deciding which kind a metric is becomes a required step in designing one, and it is not always
  obvious. The test: name the thing it claims to measure and ask whether that thing could be
  observed independently. If yes, it estimates and must correlate. If the metric *is* the only
  definition available, it defines.
- This is a **narrowing** of the old rule, not a loophole, and it can be abused. A weak estimating
  metric could reclassify itself as defining to escape a correlation it fails. The guard is that
  reclassification requires an ADR, and that a defining metric must forgo the correlate
  *deliberately and by design* — Draft Rankings does not merely fail to correlate with team
  success, it is built to exclude it.
- **Robustness testing becomes real work.** ADR 0008 rejected a per-slot expectation partly
  because raw and smoothed versions shared only 7 of 12 names — a robustness failure caught by
  accident. Under this ADR it is a named precondition, and ADR 0015 carries two hard ones.
- No existing metric changes classification. Franchise Grade and its four axes, Start & Sit and
  the trait badges all estimate and keep their bar. Draft Rankings and, under ADR 0015, Steals &
  Busts are the first defining metrics on the site.
- `CONTEXT.md`'s *judged metric* entry is rewritten to carry both kinds. The **factual extreme**
  distinction is untouched: a Record Book high is the archive sorted and is neither kind.
