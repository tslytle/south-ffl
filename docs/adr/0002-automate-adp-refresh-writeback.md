# 0002 — Automate ADP refresh write-back instead of manual editing

## Status
Accepted (2026-08-11)

## Context
`refresh-adp.py` already fetches ESPN's live ADP and diffs it against the page's embedded `ADP_2026`, but deliberately stops at printing a report — updating `ADP_2026`, the two "captured [date]" labels, and the ADP-derived value/reach tags was left as a manual hand-edit. The pre-draft refresh needs to run again ~Sept 4–5, 2026, editing roughly 250 values by hand — exactly the kind of place a transcription mistake creeps into what's supposed to be an accurate league record.

## Decision
Extend the refresh tooling to write the update back into `index.html` directly (new `ADP_2026` values, updated "captured" date labels, recomputed value/reach tags), rather than requiring a manual edit pass. Review happens via `git diff` before committing — git (ADR 0001) is what makes this safe to automate, since any bad write is trivially visible and revertible.

## Consequences
- Removes a recurring manual-edit risk on a data source explicitly prioritized as "must be correct."
- Adds a small amount of script complexity (safe in-place editing of embedded JS constants inside an HTML file) — must fail loudly on unexpected shape, not silently corrupt the page.
- Establishes a pattern (fetch → write → `git diff` review → commit) that the FantasyPros tier refresh (ADR 0003) also follows.
