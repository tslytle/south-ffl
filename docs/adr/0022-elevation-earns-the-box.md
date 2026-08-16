# 0022 — Elevation is measured, and every box has to earn it

## Status
Accepted (2026-08-15). Annotates 0005, 0011, 0012, 0013, 0014, 0020 and 0021 in place;
supersedes none of them.

## Context
Reported as "there is a lot of stuff that doesn't look right," which is not a defect
report, and the session's job was to find the defect underneath it. Measured, it was
one number: **`--surface` sat at 1.08:1 against `--bg`, and `--line` — the border meant
to rescue it — at 1.37:1 against the ground it outlined.** No container on the site was
visibly *on* anything. Twelve sessions of consistency work (one chip variant, one
`(x, right)` pair, zero header drift) were being spent inside a frame nobody could see.

ADR 0005's sweep never caught it and structurally never could: it measures **text
against its own background**. A container against the page is a different population,
the same way the phone card layout was in the 396-failure incident — a blind spot in
the instrument, not a lapse in running it.

A second finding rode along: the site has **one container idea**. The same rounded,
bordered box wraps a nav control, a person, a single statistic, a season row and a
methodology note. When everything is a box, nothing has a hierarchy, and the text is
poured into containers rather than the container being shaped by what it holds — which
is why `90–71` wrapped mid-record on a profile tile and one long name broke a grid row.

Three directions were prototyped on one surface — the current language with only its
contrast corrected (control), a no-container hairline language (Letterboxd-faithful),
and a two-register hybrid — then the hybrid was chosen and proved across six surfaces
including the deepest nesting the site has. The reference mapping is in `CONTEXT.md`.

## Decision

### The floors
1. **Surface separation ≥ 1.5:1** — anything that reads as a container measures at
   least 1.5:1 against the ground it actually sits on. In light, where white cards on a
   near-white page cannot clear a fill floor without going muddy, the bounding hairline
   carries the duty instead and is held to the same 1.5:1.
2. **Control boundary ≥ 3:1** — the boundary of an interactive control (ring, border)
   against the control's own fill, per WCAG 1.4.11.
3. **Text stays at ADR 0005's floor**, re-baselined against the new grounds.

Every colour is measured against the ground it actually sits on — the tuning of this
change failed its own gate eleven times in prototype and three more in port, and every
failure was this same mistake: a value tuned against `--bg` sitting on `--raise`, or on
a `.14` tint that lifted the ground just enough to sink the text below AA.

### The ladder (dark)
`--bg` #0B0F1C → `--surface` #26334F (1.52:1) → `--raise` #2D3A59, with `--soft` at
#0B101E genuinely *below* surface — sunken fills sink, raised fills rise, and the two
directions are not interchangeable. `--muted`/`--faint` lightened to clear AA on the
new grounds (the old values measured 4.41:1 and 3.69:1 on the new surface);
`--neg`/`--rust`/`--silver-ink` lightened for the same reason; the silver and rust
tints thinned from .14 to .10 because text sitting on them could not otherwise clear.
`--plate` is deliberately **not** on the ladder — dark in both themes, protected, and
identified by its ring rather than its fill.

### The container vocabulary
The single bubble is replaced by six containers, and elevation alternates with **role,
not depth**:

- **raised control** — you tap it and it navigates; the only passive claim to `--raise`
- **chip** — a fact attached to a control; never floats free
- **editorial block** — no box at all; hairline rules; mastheads, notes, method
- **bare figure** — a statistic is number + label divided by rules, never a box
- **plate** — the manager mark, unchanged
- **person** — a card-grid cell with no card; the plate does the work

A closed board is a control and is raised; the moment it opens it becomes content,
drops to the page ground, and is bounded by rules — which is what frees the level below
it to be raised again without inventing a third surface.

## Consequences

### What this annotates
- **0005** — floor stands; its blind spot (containers) is now covered by floor 1 above.
- **0011** — dark remains the default and the design target; light is held to
  "no defect" and separates by hairline rather than fill.
- **0012** — the role table stands in every role; several *values* moved (`--neg`,
  `--rust`, `--silver-ink`, `--muted`, `--faint`) to stay legal on the new grounds.
- **0013** — the eight-value scale stands untouched.
- **0014 / 0021** — measure rule and equal bars stand; the closed-state fact (see
  `CONTEXT.md`) will make equal heights hold by construction when it lands.
- **0020** — the shared chip rule stands; token-only change, geometry untouched.

### What it costs
`#26334F` is a long way from `#121828`; the navy reads lighter than every screenshot in
the record. Muted and faint converge (physics: both must clear 4.5:1 on the lightest
ground they share). The two-way ladder means any new fill must decide whether it sinks
or rises — there is no neutral third option, on purpose.

### Measured after
ADR 0005 sweep **zero in all four combinations** — {375px, 1580px} × {dark, light},
two passes each. (The desktop pass ran at 1580 rather than the baseline's 2048; the
2048 re-run happened 2026-08-16 with the profile rebuild, zero in all four.) `gradientSkipped` 325 dark. ADR 0021's invariant holds: one `(x, right)`
pair over 16 panels. Token ratios on the served file: surface/bg 1.52, muted/raise
4.96, faint/raise 4.68, enc/raise 4.86. One accepted exception: the H2H legend swatch
`i.self` sits on `--bg` at ground level and is bounded by its existing inset
`--line` ring instead of by fill.

### Still to port
This ADR lands the language's token layer site-wide. The per-surface vocabulary — the
closed-state fact on all 16 bars, one masthead per screen, the conditional jump bar
with current-panel state, the `.backpill` deletion (contingent on the jump bar), the
manager grid and profile rebuild — follows surface by surface, gated by the same three
floors. The prototype (`_spine-preview.html`, untracked) is the reference until then.
