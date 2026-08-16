# 0012 — Every colour has one job, and mint's job is interaction

## Status
Accepted (2026-08-12)

Annotated by ADR 0022 (2026-08-15): every role stands. Several VALUES moved —
--muted, --faint, --neg, --rust, --silver-ink, and the elevation tokens — because
the new lighter grounds sank them below AA. The role table survives value changes
by design; that is what a role table is for.

## Context
The palette was disciplined — measured, AA-clean in both themes — and still read as
clashing, which was the complaint that started the visual pass ("sometimes colors
clash"). The cause was not the values. It was that no colour had a job.

Mint was the worst offender because it had the most jobs. It painted **42 static-text
rules** — every small uppercase label on the site, the eyebrows, `.pfbody h4`,
`footer .fn`, `.rec-card h3`, the Champions team names, the Notes & Methodology
headings — plus **26 fills and borders**: rank bars, head-to-head bars, legend
swatches, decorative card top-edges, the avatar initials fallback. On the Champions
board a single row carried gold, white, mint and gold again, and mint there meant
nothing at all, because mint was also the colour of structure.

A colour that appears on everything cannot signal anything.

## Decision
Five roles. Every use of colour answers to one of them.

| role | token(s) | job |
|---|---|---|
| **interaction** | `--accent` | links, controls, focus rings, hover. Nothing else, ever. |
| **ceremony** | `--gold*` | champions, trophies, editorial eyebrows |
| **sign** | `--pos` / `--neg` | signed quantities only |
| **podium** | gold / silver / bronze `-ink`/`-soft`/`-line` | placement only |
| **encoding** | `--enc*` | "this is category N" — legends, category tags, chart series, row-state markers |

**Encoding is a real role and the file already knew it.** A comment near
`lazyBoard("rules", …)` describes three rule-change families each with "its own chip
colour reused from elsewhere on the page". The role table simply never named it, and
`--accent2` — the token doing that work — looked like a hue with no purpose. It is now
`--enc`, with one sentence that says what it does. `--accent2-dk` was deleted; it had
never been referenced.

Structural furniture — dividers, card edges, rules — is `--line`. It is not a role,
it is the absence of one, and that is the point: most edges should not be coloured.

## Consequences

### `--pos` and `--accent` are the same colour, and stay that way
`#2FDA87` in dark; `#0C6B4C` against `#0B6B4E` in light — indistinguishable in both.
Shifting `--pos` was the obvious fix and it is worse: every light-theme green far
enough from the accent to be told apart has to stop being green (teal `#146B6B`,
olive `#3F6B22`), which adds a hue to a page whose problem is clashing colour.

The rule leans on **shape** instead: interaction mint always sits on a control, and
bare numeric text is never a control. That is only true because the 42 static-text
rules moved — it would have been a lie before. **If mint is ever put back on
non-interactive text, this rule collapses and the collision becomes real.**

### `-ink` variants are for text on a tint, and must actually differ
Painting `--enc` text on `--enc-soft` measured 3.87 — a failure, and exactly the fill
trap ADR 0011 warns about, walked into fresh. The cause: `--enc-ink` had been left
identical to `--enc`. `--gold-ink` already had a light-on-tint value in dark
(`#F7CD73`); the encoding role now has one too (`#A5DCF5`). **An `-ink` token that
equals its base token is a bug waiting for a chip.**

### Gold and rust keep their encoding work
The rules-change chips use blue/gold/rust as a three-family category set. Forcing them
onto `--enc` derivatives needs three distinguishable blues or two new hues. Adding
hues to fix clashing colour is the wrong trade, so the chips stay and "ceremony only"
is understood as "never interaction" rather than "never anything else".

### Exceptions to the interaction rule exist, and both are about backgrounds
`.skiplink` (`background:#2FDA87`) and `.backpill` (mint-filled) keep non-mint focus
rings, because a mint ring on a mint ground is invisible. Commented in place.

### The sweep is what keeps this honest
Every commit in the pass measured all four combinations — {375px, 2048px} × {dark,
light} — at zero. See ADR 0005, and note the parser bug found and fixed in the same
session: baselines recorded before 2026-08-12 were measured with a broken
`color(srgb …)` parser and are only trustworthy over plain `rgb()`/`rgba()`.
