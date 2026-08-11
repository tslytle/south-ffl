# 0001 — Adopt the existing GitHub repo as the sole working copy

## Status
Accepted (2026-08-11)

## Context
The project existed as multiple loose, undifferentiated file snapshots with no version control:
- A Mac working folder (`South FFL Website\index_9-dark_3-improved.html`, with literal-backslash filenames from a Windows-sync artifact)
- A `deploy/` folder with absolute-URL variants
- A `South-FFL-transfer.zip` PC handoff copy
- Manual `.BACKUP-before-*.html` snapshots taken before risky edits

A byte-level diff (2026-08-11) confirmed all of these were near-duplicates — no data-loss risk, differences were cosmetic (CSS polish, absolute vs. relative OG-image URLs). Separately, a GitHub repo (`tslytle/south-ffl`) already existed with real commit history and was confirmed in sync with the newest local content (byte-identical `index.html`/`og-image.png` via a downloaded `south-ffl-main.zip`).

## Decision
Clone `github.com/tslytle/south-ffl` as the one working directory going forward. Retire the manual `.BACKUP-*.html` snapshot pattern once the current state is committed — git history replaces it. The old Mac working folder and transfer-zip copies are archived, not edited further.

## Consequences
- Single source of truth; no more "which file is current" ambiguity.
- Deploy drift (working file vs. `deploy/` folder) becomes a non-issue — there's one file, changes are reviewed via `git diff` before commit.
- Loses nothing: confirmed via diff that no unique data existed only in a since-archived copy.
- Requires discipline going forward: all edits happen in the cloned repo, not by re-copying files around.
