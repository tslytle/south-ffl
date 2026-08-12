# 0007 — Rebuild the site as a hub plus routed views in a dark-native app language

## Status
Accepted (2026-08-12)

## Context
The site is one scrolling page: six top-level `<details>` sections containing eighteen leaf
surfaces, all accordions, cross-linked by hash via `openFor()`/`openSection()`. The visual system
(navy/mint, Inter + Oswald, a 9-17px type scale) is disciplined and measures zero WCAG AA
failures in both themes, but it has no display step — nothing on the page can be large, so every
surface competes at the same volume.

The audience was pinned as **league members browsing on a phone**, typically arriving from a
group-chat link and giving it about ninety seconds. An eighteen-door accordion is the wrong shape
for that visitor: their first screen is a countdown clock, and reaching their own profile requires
knowing to open The Managers first.

Separately, `index.html` is 2.55MB, and the bulk is data rather than assets — `PSTAT` at 821KB
and `ARCH` at 507KB, inline and parsed before anything paints. Logos (`NFL_LOGO` 167KB,
`OWNER_LOGO` 165KB) and fonts (71KB) are a distant second.

## Decision
- **A hub, then routed views.** A designed front door whose hero changes by season phase
  (countdown before the draft, standings during the season, champion after it), over a directory
  to all eighteen surfaces. Top-level sections become routed screens rather than accordions.
- **All eighteen surfaces survive.** Pruning to ~12 was proposed and rejected.
- **Dark-native app language** (Linear/Vercel register), dark as default, light retained and
  supported. Motion is functional only — view transitions and state changes, `prefers-reduced-
  motion` honoured, nothing decorative.
- **Uniform shell, tiered depth.** Every surface gets the new theme, navigation and shared
  component vocabulary (table, stat block, card, chart, disclosure) before any surface gets
  bespoke layout. Bespoke queue, in order: hub, Manager Profiles, Standings.
- **Two naming registers.** Navigation is functional and thumb-sized — *Season, Managers, History,
  Drafts, Records, Rules*. Page headings and eyebrows keep the existing editorial voice.
- **The same site for every visitor.** No identity-based content. `localStorage` continues to
  remember the theme choice only.
- **Preserve today's URLs.** Old anchors redirect into the new routes; the ten-odd internal jump
  functions (`gotoRosters()`, `gotoMatchupGame()`, `jumpToDraft()`, …) are rewired rather than
  replaced.
- **Defer data parse.** Keep `PSTAT` and `ARCH` as strings and `JSON.parse` on first use, so the
  hub paints without touching either.
- **Single self-contained file, no build step, stays.** This is the constraint the rest is
  designed around, not an accident.
- **The draft cheat sheet is restyled, not redesigned** — new tokens, layout and interactions
  untouched — because it is the one surface used under time pressure on draft night, and it will
  never be rehearsed.

## Considered options
- **Refine the existing system rather than replace it** — rejected; the ask was a complete
  overhaul.
- **Editorial-almanac direction** — rejected in favour of the app language.
- **Personalised dashboard** (pick your manager, remembered, front door becomes your own page) —
  accepted, then reversed: the site should be the same experience for every visitor.
- **Prune eighteen surfaces to twelve** — rejected. All eighteen earn their place; the cost is
  absorbed by systematising the design instead.
- **`v2.html` as a parallel build** — rejected as the working method, because `refresh-adp.py` and
  `refresh-tiers.py` write to `index.html` specifically, so a long-lived second file would drift
  stale on exactly the data used to draft. Adopted narrowly as a short-lived `preview.html` for
  the pre-merge review window only, where nothing refreshes.
- **A Pages Actions workflow for branch previews** — rejected; it introduces the build step this
  ADR exists to avoid.

## Consequences
- Work happens on a feature branch merged once, a deliberate departure from the standing
  commit-straight-to-`main` preference. This is the first change that leaves the site unusable
  mid-flight.
- Pages serves `main` from the repo root and there is no `.github/workflows`, so a branch has no
  URL. Pre-merge review is done by copying the branch's file to `preview.html` on `main`, sending
  that link, and deleting it in the merge commit.
- Merge gates: zero AA failures in both themes (ADR 0005); no page-level horizontal scroll at
  375px or 1265px; every surface within two taps of the hub; the hub renders without parsing
  `PSTAT` or `ARCH`; no console errors, one `<h1>`, no heading-level skips, no
  `NaN`/`undefined`/`[object Object]` in rendered text, no duplicate element ids, no images
  missing `alt`; every preserved URL and internal jump resolves. Plus one leaguemate's unguided
  reaction to the preview link.
- Deferred parse trades a slower first open of a data-heavy view for a faster first paint. That is
  the intended trade: a slow view-open is visible and fixable, a slow first paint just loses the
  visitor.
- Metric work (ADR 0006) lands on `main` first, before the branch is cut. Dropping an axis changes
  the radar geometry, the weight chips and the grade copy, and designing the profile screen twice
  is avoidable.
