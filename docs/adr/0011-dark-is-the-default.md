# 0011 — Dark is the default, at every OS setting

## Status
Accepted (2026-08-12)

Annotated by ADR 0022 (2026-08-15): dark remains the default and is now explicitly
the design target; light is held to "no defect, no ugliness" and separates its
containers by hairline rather than fill.

## Context
The dark palette shipped inside `@media (prefers-color-scheme:dark)`. That made
the archive a **light document that went dark when the reader's OS asked** — the
conventional arrangement, and the right one for a page whose design is drawn on
paper.

The overhaul stopped being that page. The hub's eighteen doors, the board panels,
the `--raise` fills, the three-colour split (mint for interaction, gold for
editorial voice, neutral for structure) and every weight decision in the uniform
shell were designed, measured and looked at against the dark ground. Light was
kept working, but it stopped being what the design was *for*. Q18 in the grilling
session settled the intent — "dark is the design's home, light stays supported" —
and this records the implementation and its consequences.

## Decision
The dark palette applies at `:root:not([data-theme="light"])` with **no media
query**. At every OS setting — dark, light, or no preference expressed — the
archive opens dark. The toggle is the only thing that changes it, and the choice
persists in `localStorage`, applied before first paint by the no-flash script in
`<head>`.

Light is not deprecated. It is a supported theme, held to the same WCAG AA floor
as dark (ADR 0005), and every sweep runs both.

## Consequences

### A reader who runs their phone in light mode now gets a dark page
This is the deliberate part, and it is the whole cost of the decision. The
archive no longer honours `prefers-color-scheme: light` on first visit; it honours
an explicit choice, once made, forever. Accepted because the audience arrives from
a group-chat link, looks for ninety seconds, and should see the thing as designed —
and because one tap on a labelled control reverses it permanently.

### The toggle's `resolved()` had to move with the stylesheet, or the first click is a no-op
`resolved()` answered "what is the reader looking at?" with the OS preference,
which was correct while the palette followed the OS. Under this decision a
light-mode reader looks at a *dark* page while `resolved()` says "light", so the
first click would set `data-theme="dark"` — changing nothing visible — and they
would have to click twice. It now answers `dark` for "no explicit choice yet",
matching the stylesheet by construction.

**Anything that infers the current theme must read `[data-theme]` and default to
dark, never `matchMedia`.** That is the trap this decision leaves behind.

### Specificity is unchanged, so print still works
A media query contributes no specificity, so moving the block out of one leaves it
at `(0,2,0)` — exactly what it was. The print stylesheet's `:root:root` (also
`(0,2,0)`, later in the file) still forces paper-and-ink for a dark reader's
printout.

### The AA floor is what gates any future palette work, and it now has a tool
ADR 0005's floor — every text-bearing element clears AA against its *composited*
background, in both themes — was the stated risk of this change. It held: all four
combinations measure zero failures.

| | checked | failures |
|---|---|---|
| 1265px dark | 59,753 | 0 |
| 1265px light | 59,753 | 0 |
| 375px dark | 59,501 | 0 |
| 375px light | 59,501 | 0 |

The sweep is checked in as **`contrast-sweep.js`**. Use it for anything that
touches colour. Two findings from rebuilding it are worth carrying forward:

- **The original sweep only ever saw one width.** It counted 21,341 elements,
  almost exactly a single desktop pass (21,545). The phone card layout is a
  different population, not a narrower one — and it was hiding **396 real
  failures**, fixed in the same session.
- **A background tint is expensive on the dark ground.** `--gold-soft` is 14% and
  it costs roughly 1.7 ratio points. Painting it behind a champion row sank 467
  elements below AA on desktop and 396 on the phone. Mark rows with an edge, a
  border or a chip — not a fill — unless a sweep says otherwise.

## Alternatives considered
**Dark unless the OS explicitly prefers light** (`@media (prefers-color-scheme:light)`
carrying the light palette). Respects a stated preference, and in practice changes
almost nothing: essentially every current OS reports light or dark rather than no
preference, so light-mode readers would have continued to see light and the
decision would have been cosmetic. Rejected as not implementing Q18.

**Leave it as it was.** Defensible — the flip is the lowest-visual-payoff item on
the overhaul list, since the people who look at this most already run dark. Done
anyway because it is the last thing standing between the design's intent and what
a first-time visitor actually sees, and because the sweep made the risk
measurable rather than theoretical.
