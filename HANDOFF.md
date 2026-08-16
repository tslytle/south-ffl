# Session handoff — continue on PC

This picks up a `/grilling` (+ domain-modeling) session about improving the South FFL site
(looks/functionality/data/data-analysis) ahead of draft night, **Monday Sept 7, 2026, 6:00 PM CDT**.
See `CONTEXT.md` and `docs/adr/` for what's already settled — read those first.

---

## The "Page build failed" mails are cancelled builds, not failed ones (`5ab49b7`)
*Diagnosed 2026-08-15 after the pattern showed up four times in a day.*

**Nothing is broken and nothing was ever lost.** Every one of the four errored builds had
`duration: 0` and an `updated_at` **exactly equal** to the `created_at` of the build that followed
it. They never ran.

**The cause is two pushes inside one build window.** A build takes 33-46s; the working rhythm here
is to push the code commit and then the HANDOFF commit about 30s later, which lands the second
push while the first build is still going. Pages cancels the in-flight build and reports the
cancellation as `Page build failed.`

The control case settles it. `ef77193` built 21:08:01 → 21:08:38, and `513fe33` was pushed at
21:08:40 — **two seconds after it finished**. Both built. Every overlap errored; the one near-miss
that cleared did not.

**Fix: make both commits, then push once.** Costs nothing and removes the cause.

**Two checks that lied during this diagnosis, both worth knowing:**

1. **A build's `commit` field is unreliable after a cancellation.** `d282b55` has **no build entry
   at all**, and the build that served it is labelled `0003ae61`. Going by SHA, the newest commit
   looks unbuilt; by content it is live. **Check content, not SHA.**
2. **Local file size never matches the live byte count.** `core.autocrlf=true`, so the working tree
   is CRLF and `index.html` reads **10,769 bytes larger** than git's copy — exactly its line count.
   Compare `git show HEAD:index.html | wc -c`, which matches `Content-Length` byte for byte.

**`.nojekyll` added**, and measured rather than assumed: the next build ran **24.4s** against a
33-46s range all week, below every prior build. Pages here runs Jekyll by default, and this repo
has no `_config.yml`, no `_layouts`, no front matter and not one Liquid tag in 10,769 lines — the
markdown under `docs/` was already being served raw, which is Jekyll copying it untouched. One
measurement, not a trend, but it shrinks the window a collision can happen in. Verified after:
`index.html` byte-identical to HEAD, `docs/adr/*.md`, `HANDOFF.md` and `og-image.png` all 200.

---

## WHERE THIS STANDS — 2026-08-15 (latest): the elevation ladder is live (ADR 0022)
*Read this first. The sections below are the same day's earlier work and still current.*

A `/grill-with-docs` session on "a lot of stuff doesn't look right" found one number under
most of it: **`--surface` at 1.08:1 against `--bg`** — no container visibly on anything, and
ADR 0005's sweep structurally blind to it (it measures text against its own background, never
a container against the page). Three directions were prototyped, the hybrid won —
**Letterboxd owns editorial, Sleeper owns product chrome** (full mapping in `CONTEXT.md`) —
and it was proved across six surfaces including the site's deepest nesting before anything
touched `main`. Prototypes are `_proto-preview.html` / `_spine-preview.html`, untracked;
delete them once the port is complete.

**What landed: the token layer, site-wide.** Dark ladder re-cut (`--surface` #26334F at
1.52:1, `--raise` above it, `--soft` genuinely below), light's `--line` made honest (1.27:1
→ 1.55:1 against a white card), and every text token that the lighter grounds sank below AA
lifted with it: `--muted`, `--faint`, `--neg`, `--rust`, `--rust-ink`, `--silver-ink`, both
`.14` tints thinned to `.10`. Both dark blocks in lockstep, checked. `--plate` untouched.

**The tuning failed its own gates fourteen times before passing, and every failure was one
mistake in different clothes: a colour measured against a ground it doesn't sit on.**
`--dim`-equivalents on raised fills, chips lighter than what they sink into, text on `.14`
tints that lift the ground just enough. The instrument that caught all of it is ADR 0022's
new floor pair: **container ≥ 1.5:1 against its actual ground, control boundary ≥ 3:1** —
the check whose absence let 1.08:1 survive twelve clean sessions.

**Measured after:** ADR 0005 sweep **0 in all four combinations, two passes each** —
{375 (iframe), 1580} × {dark, light}; desktop ran at 1580, not the baseline 2048 — **re-run
at 2048 before the freeze**. ADR 0021's invariant holds (one `(x, right)` pair over 16).
One accepted exception, named in the ADR: `i.self` sits at ground level, bounded by its ring.

**Traps this session confirmed:** the sweep must run in a *fronted* tab (a non-fronted pane
throttles rAF and the run silently stalls); `__runAll()` is synchronous — `await` masks a
30s tool timeout, so kick it and read a global; the pane screenshots composite at scroll 0,
so bring a section to the top instead of scrolling to it.

**The port landed the same day, four commits, each swept to 0 before the next began:**

| commit | what it was |
|---|---|
| `bc7ad03` | **A closed board states a fact.** All 16 bars: prose → panel body, fact chip in its place. One bar height by construction — 81.2px × 16 desktop, 136.3 × 16 phone (a zero-height pseudo flex item forces the chip onto its own row; natural wrapping left three bars tall and one short). The one kicker that duplicated its group's (Manager Profiles) is gone. |
| `e0dbb61` | **The jump bar earns its place.** Hidden while every panel is shut, appears on open, marks the panel you are IN on scroll (ADR 0020's shared `.on`, nothing new drawn). **And the `.backpill` deletion is REVERSED** — the session decision rested on my wrong reading. It is a cross-view *return stack* (jump from Record Book to a roster; pill takes you back), not scroll-to-top, and no per-view index can do that job. Its real offence — an opaque mint control sitting on table rows — is fixed with `body:has(.backpill.on){padding-bottom:86px}`. |
| `d46e9d6` | **The name leads on a manager card.** The grade left its absolute top-right mint pill (loudest thing on the card, by accident) for the footer at the record's own weight: `12 seasons · 90–71 · 96.4`. `fillGradeCells()` untouched — same `[data-grade]` hook. Footer atoms are nowrap at t-tiny; at t-fine the record broke mid-number ("88–"/"75"). Phone: grade takes its own row on every card — natural wrap left 12 of 17 two-line. |
| `90e6d89` | **A badge never decides a standings row's height.** Tagged rows ran 112px vs 89.7. The slot is on every row now; the table pays ~24px/row, weighed against widening the pinned OWNER column (which would cost a phone its second data column) and taken. |

**Then the colour pass, same day (`a75d2fc`, `c3331ab`), asked for as "more vibrance."** The
rule that made it safe: colour is encoding, never decoration (ADR 0012). The position palette
(pink QB / orange RB / cyan WR / teal TE / purple K / gold D/ST) now reaches everywhere
positions render — Steals & Busts and wire cards (whose tag used to wear the verdict tint,
saying up/down twice), the 252 draft drawers, the profile's tendency figures and fact rows.
And all 32 club abbreviations wear **generated** franchise colours: hue is the identity,
luminance is whatever the floor demands — blended until 4.7:1 against the measured worst
ground per theme. **Traps that run found, all real:** the closed profile overlay hid with
opacity alone (contents stayed tabbable and in the sweep — `visibility` now rides the fade);
`.pfdcard span` (0-1-1) silently repainted the position pill (third instance of the
caption-rule cascade shape, after `.drawtrig` and `.badge`); and the club palette failed
**only at 375px dark** because the champion row's gold fill paints on phones alone — tune
against the composited worst ground (`#494C57`), never against `--raise` raw.

**The port is COMPLETE (2026-08-16, `4c5823a`).** The profile rebuild landed: career tiles
are bare figures (transparent cells, rules not boxes, one grid serving two grounds —
the profile rail and the rules glance — with the frame closed by container top+left and
cell right+bottom at any column count), and THE BREAKDOWN is one lead sentence plus fact
rows, with the points-vs-wins comparison and both caveats surviving as notes. The rank
rails needed nothing — the token commit had already fixed their track. Swept
{375, 2048} × {dark, light}, two passes each, all zero — which also paid ADR 0022's
1580-vs-2048 debt. Both prototype files are deleted. Nothing from the 2026-08-15 design
session remains unported.

---

## 2026-08-15: every board bar the same length (ADR 0021)
*Read this first. The section below it is the same day's earlier step and still current.*

Follow-up to the chip work: "I want the bars to be the same length and for everything to match",
with a screenshot of The Managers group view. **Champions was 720px wide against 1040 for the
other three.**

That cap was deliberate — ADR 0014 put it there so the year, name and record read as one plaque
line, and moved it onto the disclosure so header and list would share both edges. **It was right
about edges and wrong about which state to optimise.** Eleven of twelve boards are collapsed by
default, so a group view is almost always four header bars and nothing else, and the cap made
Champions the one bar that did not line up.

Cap deleted. Every top-level board is now full width. **The measure rule itself stands and now
has no instance** — see ADR 0021 for why the three obvious alternatives (720 centred, 720
left-aligned, full-width header over a 720 body) are each worse, and for what the plaque line
costs at 1040.

**The other half of that report was not a bug.** The mint title and mint frame on Manager Profiles
in the screenshot is the hover state — `details.sub:has(> summary.subhead:hover)` tints the whole
outline, so the thing that lights up is the thing that opens. Working as designed; checked before
changing anything.

### The check worth reusing

Group every top-level `summary.subhead` by its `(x, right)` pair across all routes: **one pair
over 16 panels** (172→1212 at 1265px). Same shape as ADR 0020's chip-variant count, and it fails
the moment a board re-narrows itself.

ADR 0005 sweep re-run after — layout width changed, so it had to be: **zero in all four**,
`gradientSkipped` 325/311, unmoved.

---

## 2026-08-15: one chip, every row (ADR 0020)

Reported as "the tabs look uneven and not clean", with a screenshot of the Managers view. It is
not one row — **nine rows do the same job and every one was drawn on its own terms**: five heights
(25, 29, 31, 33 and 39px), three radii (8px, 12px and a pill), two font sizes, two weights, two
caption styles, and a phone rule that re-inflated two of them back to 15px.

**The complaint lands where the rows stack, which is why it reads as "uneven" rather than as any
one thing being wrong.** `#matchups` printed SEASON at 39px directly above JUMP TO WEEK at 31px.
Draft Night printed four 33px pills above nine 25px division chips. Managers printed IN HERE at
31px above SORT BY at 29px. Also found on the way: `.allctl` was the only row whose hover filled
with accent, so an unselected chip wore the selected treatment.

One shared rule now sets geometry and all three states; each row keeps only what is local to it
(gap, sticky, the week bar's `min-width`, `.recjump`'s `--raise` fill). See ADR 0020 for the size
choice, the ordering trick that lets locals win without extra specificity, and what it costs.

### The check worth reusing

**Do not verify this by reading the nine rules.** Sweep every route, group every visible chip by
`(height, fontSize, weight, radius, family)`, and count the variants — it should be **1 across
208 chips**, and captions **1 across 16**. That query is the test for ADR 0020 and it fails
loudly the moment a tenth row arrives with its own geometry. In dark it returns three border
colours on that one variant, all intended: `--line`, `--accent` for the selected chip, and the
50% gold marking playoff weeks on `.mwkbar .po`.

ADR 0005 sweep re-run after: **zero in all four** — {375px, 2048px} × {dark, light}, two passes
each, `gradientSkipped` 325/311, unmoved from baseline.

**Still open, deliberately:** `.subnav` is a jump bar, not a tab bar — it scrolls to a panel and
never marks which one you are in. The `.on` hook now exists and is shared, so giving it a
current-panel state is a script change rather than a CSS one.

---

## 2026-08-15: one replacement line for both boards (`0003ae6`, live)
*The sections below are the same day's earlier steps, and the one directly below
is **partly superseded** — read its ADR 0019 annotation before trusting its numbers.*

Asked to "add kickers to Steals & Busts too". **They were already there** — ADR 0015 put them on
the draft board and nothing ever filtered them; six kicker cards were showing (Jason Myers 2025 at
pick 184, +54, the top one). The only place kickers were missing was the **waiver half**, so this
was checked before acting rather than after.

### The thing worth carrying forward

**ADR 0018 that morning read a shallow rostered pool as a *kicker* problem. It wasn't.** The board
asks what a pickup gave you *above what was sitting there for free*, and the rostered pool is **by
construction the set of men who were not free**. It is also wrong in one direction only: a
subset's (bar+1)th man is never better than the league's, so replacement came out low and **every
wire value on the board was too generous** — not just kickers'.

Measured over all 136 weeks, true replacement minus rostered-pool replacement:

| | RB | WR | QB | TE |
|---|---|---|---|---|
| mean per week | +1.67 | +3.01 | +3.29 | **+3.97** |
| weeks the true line is higher | 96% | 100% | 98% | 100% |

On a pickup held sixteen weeks that is **27 points of over-credit at RB and 64 at TE**.

So `refresh-players.py` now bakes **`PLAYER_VALUE[y].wrep`** — the man just past the startable bar
among every player who took the field that week, the same definition `replacement_from()` already
used for the season, at the same bar. **The two hindsight boards now agree on what replacement
means; they never did, and the page had not noticed.** The positional constraint went with the
pool, so `WIRE_POS` carries all six and kickers are on the wire because the question finally has
an answer that doesn't depend on whether this league bothered to roster a thirteenth one.

### The headline card moved twice in one day and landed where it started

ADR 0018 had just given "Best pickup ever" to the **2018 Bears D/ST at +139.0**. On a true
replacement line that defence is **+78.0**, and **Kyren Williams 2023 takes it back at +102.5** —
itself down from the +123.7 the old basis gave him. **The D/ST pool was the shallowest of all, so
ADR 0018 shipped a headline that was an artefact of the very flaw it documented and confined to
kickers.** Defences fall to 2 of the top 10 pickups from 4. That is what removing an artefact
looks like, and it is the sharpest argument in the whole sequence for not stopping at the first
measurement that answers the immediate question.

### Retired

`BAR_POS`, introduced hours earlier purely to give the rostered pool a D/ST bar and unread the
moment the pool went; the unread `bar` field on each wire row; and the last of `SKILL`'s
descendants. A season with no `wrep` is **skipped, not scored against zero** — falling back would
silently turn every value into raw points, which is the failure this change exists to remove.

Verified: both boards carry all six positions; kickers enter with 227 pickups topping out at Jason
Myers 2025, +40.0 over nine weeks — present, plausible, nowhere near the top; kickers and defences
both reach the manager panels; **Start & Sit untouched**, since it prices what you should have
started from what you *held*, where the rostered pool is the right pool; `--verify` still exits 0;
no console errors. `PLAYER_VALUE` grew 8.7KB, and the 2.7MB file is worth watching.

**Second trap for the next session**, on top of the cache one below: `innerText` of a **closed
`<details>` is empty**, so a check that reads a collapsed panel reports "not rendered" and looks
like a bug. Open the ancestors first — it cost a false alarm on the manager panel here, twice.

---

## WHERE THIS STANDS — 2026-08-15: defences on the wire too, kickers measurably not (`ef77193`)
*Superseded in scope by ADR 0019 above — the kicker exclusion and the +139.0 Bears figure below
did not survive the day. The reasoning about pool depth was sound; it was aimed too narrowly.*

Asked for straight after the section below. **ADR 0018** records it. It is **not the same change
and not the same reason**, and that is the point worth carrying forward.

**ADR 0017 turned on reconstruction accuracy. None of it applies here.** Waiver values come
straight out of the league export — the points ESPN actually awarded, week by week — so nothing is
reconstructed and nothing was ever inaccurate. **Deleting the filter would still have been wrong.**

A wire value is points **minus the replacement at that position that week**, and that replacement
is read off the **rostered** pool, since the export cannot see a free agent. So a position can
only be priced here if the pool reliably runs past its startable bar. If it does not, the code
falls back to the worst rostered man and the subtraction quietly becomes *"minus the worst
starter"* — which flatters every pickup at that spot, the exact failure the board's own header
warns about. **The pool had no D/ST in it at all** (`if(!LINEUP[p[1]]) return`), so removing the
filter alone would have subtracted **zero** and handed defences their raw points.

**Measured over all 136 wire weeks, 2018-2025** — this is the load-bearing number:

| position | bar | thinnest week | median | weeks with nobody past the bar |
|---|---|---|---|---|
| QB | 12 | — | 22.9 | **0** |
| **D/ST** | 12 | 14 | 19 | **0** |
| **K** | 12 | 12 | 14 | **31 — 22.8%** |

So **defences are priced and kickers are not, and that asymmetry is a measurement rather than a
preference.** `WIRE_POS` states the numbers and says plainly: if kicker rosters ever deepen,
re-run the count — **do not add K on the grounds that D/ST is there.**

**`BAR_POS` is new, beside `LINEUP`, so the D/ST bar is measured rather than assumed.** Every team
*looks* like it starts exactly one defence; counted, it is **11.76 to 12.00** a week, rounding to
12 in all eight seasons. Kept out of `LINEUP` itself because `LINEUP` drives `replacementAt()`'s
flex model, which a defence has no business in. (My first pass hardcoded `teams.length` and I
replaced it — this repo counts rather than assumes, and `STARTS_BAR` exists for exactly that.)

**`SKILL` is deleted.** It read *"kickers and defences are streamed, not valued — nobody remembers
who dropped which D/ST"*, which is a claim about what is **interesting**, not what can be
measured; ADR 0015 and 0017 had already taken most of it. Nothing replaces it as a single rule,
deliberately — the draft board prices a season against every NFL player and can carry any
position, the wire prices a week against the rostered pool and cannot.

**One visible knock-on: the Record Book's "Best pickup ever" changes hands.** Kyren Williams
(2023, +123.7) gives way to the **2018 Bears D/ST**, claimed week 2 and held all sixteen for
**+139.0**. Face-valid — best fantasy defence of its season by a distance. Its copy also loses a
pronoun, since *"the weeks he was held"* is wrong once the answer is the Bears. "The costliest
cut" is unchanged.

Verified rather than assumed: 403 defensive pickups and 363 drops on the board; defences 23.5% of
all wire moves and 32% of the top fifty (a skew, not a takeover — explicable, since a defence is
cheap early and a good one is held all year — and the board caps at three per position anyway);
every D/ST link resolving to the right team-season page; **no kicker anywhere on it**; Start & Sit
unaffected, its skill bars still QB 12 / RB 29 / WR 31 / TE 12; no console errors.

**Note for the next session:** the local dev server serves the 2.7MB `index.html` from cache, so a
plain reload shows the OLD file and every check silently passes against stale code — it cost a
confusing "0 defensive adds" here. Append a query string (`?v=2`) rather than trusting a reload.

---

## WHERE THIS STANDS — 2026-08-15: defences are on Steals & Busts (`e8baa93`, live)
*The section below it is the same day's earlier work and is what this rests on.*

Asked for directly after the section below flagged it. **ADR 0017** records the reversal and
annotates ADR 0015, which stands in every other respect.

The exclusion was never a convention — it was a scope drawn at a measured error bar, and the
correction below moved the bar out from under it: **11.8% median season error → 1.1%**, from
20-40% of the whole D/ST spread down to about 4%. So the test is re-applied, not relaxed.

Mechanically it is **one line out of `draftValue()` and `D/ST` into `POS_ORDER`** — a filter
coming off rather than a measure being extended, since Steals & Busts is the same
`draftPicksPriced()` that Draft Rankings sums, read one pick at a time. Defences were already
being priced here and thrown away at the last step. `POS_ORDER` matters: its own comment warns
that a missing entry makes the sort key NaN and scatters the cards.

**Face validity, which is the gate for a defining metric (ADR 0016).** Unprompted, the board
returns the **2019 Patriots at pick 145 (+99)** and the **2017 Jaguars at 151 (+88)** as the top
defensive steals, and the **2015 Bills at pick 70 (−21)** — Rex Ryan's first year, taken in the
sixth on hype — as the worst. Those are the three anyone in this league would name.

**Robustness, measured rather than claimed.** Re-ranked with ±2 points of noise, which is the
entire remaining residual: the three defensive steals do not move, and the busts move only in
their third card, between two 2015 defences already within a point of each other. What the noise
*can* move is a **sign** — 8 of the 178 defences sit within 2.5 points of their going rate, 2
within half a point. **The first draft of the code comment claimed no card could change sign;
that was wrong, and measuring it rather than trusting it is what caught it.** The page now states
the limit instead of implying a precision it does not have.

**Untouched on purpose: the waiver board still excludes defences and kickers.** Those values come
from the league export directly and are never reconstructed, so nothing in the scoring correction
bears on that exclusion — it rests on its own reasoning and needs its own decision.

Verified in the browser rather than assumed: three defensive cards per column sorted last, every
D/ST link resolving to the right team-season page (PFR's `rav` for Baltimore included), defences
reaching four managers' personal panels, the record book's top steal and bust unchanged (Cooper
Kupp and Jonathan Taylor both outrank every defence), no console errors.

---

## WHERE THIS STANDS — 2026-08-15 (later): every pulled number checked, and the defences were wrong
*The sections below are the previous states of play and remain accurate for
everything they cover, **except** every "about 12%" said of defences — that number is now ~2%.*

Prompted by "I want to make sure all of the data pulled is accurate", which is five separate
pulls. Four were clean on the day. The fifth had never actually been checked.

| surface | source | verdict |
|---|---|---|
| ADP | ESPN half-PPR draft room | 250/250, mean abs move **0.4 picks**, 1 add / 1 drop at the tail |
| Tiers | FantasyPros half-PPR | 125/125 matched, **9 tier changes**, 0 added, 0 dropped |
| Cheat sheet | ESPN, `--live` | **309/309** clubs and byes agree, 0 errors, the same 11 notes |
| Schedule game ids | ESPN scoreboard | 272/272 already correct, nothing to write |
| Player values | nflverse | **`--verify` was a no-op.** Below. |

Still nothing to write for the first two — the tier moves are churn three weeks out and both
scripts have to be re-run near Sept 7 anyway. That remains the only dated work on this file.

### `--verify` did not verify (`97e9838`, live)

The docstring said it re-scored 2018-2025 against the archive and reported the agreement, "100.0%
when this was written". It was a no-op — byte-identical to `--dry-run` — and the 100.0% over
23,668 player-weeks was a one-off measurement from authoring time that nothing in the repo could
reproduce. **The load-bearing claim of the whole Draft Rankings board was unreproducible.**

Written for real it walks all **24,857 roster-weeks** the league export recorded, re-scores each
man from raw nflverse stats and compares. It found two defects on its first run.

**The defences were missing two scoring rules.** Yards allowed are NET of sack yardage and
nflverse keeps sack yards out of `passing_yards`; and a fumble returned for a touchdown is a
defensive score that nflverse files outside `def_tds`. The old header blamed the gap on a noisier
feed — "~11% more sacks and ~23% more fumble recoveries than ESPN" — and **that diagnosis was
wrong**. The tell was in the residual and nobody had ever looked at it: it was **one-sided**, with
computed never meaningfully high, which is the shape of a missing category and not of noise.
Measured per club-season, mean absolute error **12.8% → 1.9%**; 63% → **91.5%** of club-weeks now
exact. The old "about 12%" was itself accurate, which is why it survived so long.

**Travis Hunter was scored as a man who never played.** nflverse files a two-way player at his
defensive position — he is a **CB** there — so the position filter dropped all seven games of his
2025 and the board baked him at 0 points, 0 games. He played seven and was bad. That is precisely
the distinction the games column exists to draw ("a pick that returned nothing because he never
played is a different story from one that played and was bad"). His *score* does not move — 49.8
is under WR replacement (138) either way and the floor takes it to zero — but the *fact* the board
states about him does. He was the only such man in twelve seasons; checked, not assumed.

**What moved on the board.** Every class total shifted because every defence rescored. **No score
moved by more than 2 points**, the top eight all-time held their order (#9/#10 swapped), 16 of 140
in-season ranks moved. Measured by running the board's own `draftRankings()` in node against the
old and new `PLAYER_VALUE`, then confirmed against the live page. Skill agreement is **99.99%**
(22,417 of 22,419); the two stragglers are Caleb Williams 2025 wk6 and Tony Pollard 2020 wk17,
both columns the two sources file differently rather than scoring, both named in
`KNOWN_SKILL_DIFFS`.

**Proved by fault injection, not by passing**, to the standard `check-cheat.py --live` set. Five
faults: full-PPR, gross yards allowed, no fumble-return TDs, no two-way rescue, unscored PATs.
**The first design caught only three.** A rate floor cannot see a small defect — Hunter is seven
weeks out of 22,419 and clears 99.9% comfortably, which is exactly how he sat wrong for a season —
and dropping the fumble-return TD costs only 3.7 points of the D/ST rate. So the check also gates
on **one-sided D/ST bias** (the instrument that found both rules) and on **any skill disagreement
not already named**. All five now exit 1; the shipped rulebook exits 0.

**One thing this hands forward.** ADR 0015 keeps defences off Steals & Busts because a defensive
season could only be rebuilt to within 12% — a quarter of the whole spread between the best
defence in a year and the twelfth. That error is now ~2%, about a twenty-fifth of that spread, so
**the exclusion is inherited from an era that no longer exists and is due a revisit**. Not done
here, and there is a real reason for caution: ~8% of club-weeks are still one yards-allowed ladder
step out, for a cause nobody has isolated. The page now says this in the margin rather than
asserting the old number.

## WHERE THIS STANDS — 2026-08-15 (earlier): the sheet checked against the NFL, and three edges straightened
*The 2026-08-14 section below it is the previous state of play and is still
accurate for everything it covers.*

**Seven commits, all on `main` and live**, plus this file's own updates. The first two came from the
Mac that morning and were never written up here; the rest are the PC session below.

| commit | what it was |
|---|---|
| `7d9cbfd` | The three "how this works" method notes closed and demoted to asides. 2,964px of prose before the first number, handed to the reader again on every visit; 162px closed. |
| `9583c8d` | Every panel header hung off one **baseline** rather than a box. Drift was up to 24.5px across the twenty-five headers, and the `?` badge added the commit before was itself one of the offenders. 0 drift after, at both widths. |
| `3480233` | `check-cheat.py --live` — below. |
| `56e1683` | The hero band put back on the page's own left edge — below. |
| `3fef6c9` | The way out and the view's controls on one line — below. |
| `8c1f6f3` | The per-pick figure taken off the draft board — below. |
| `f723253` | …and given a control, so a phone can reach it at all — below. |

### The pre-draft tools, run 2026-08-15 — all three clean, nothing written

Three weeks out, and the state of play is that **nothing needs writing yet**, exactly as the
2026-08-12 entry predicted:
- **`refresh-adp.py --dry-run`**: 250/250, mean absolute move **0.4 picks**, median 0.2. The
  largest single move in the whole table is Stefon Diggs 144.6 → 134.5. One add, one drop, both at
  the tail: Evan Engram out, Cyrus Allen (KC rookie WR) in.
- **`refresh-tiers.py --dry-run`**: 125/125 matched, **4 tier changes** (Achane 2→3, Croskey-Merritt
  6→5, Meyers 5→6, Juwan Johnson 4→3), 0 added, 0 dropped.
- **`check-cheat.py`**: 0 errors, 0 warnings, the same 11 expected notes.

**Writing 154 sub-pick moves onto a live site three weeks early is churn**, and both scripts have to
be re-run near Sept 7 regardless. Re-run then; that is still the only dated work on this file.

**Two things in the diff were chased rather than assumed, and both came back clean.** Worth
recording because the *shape* of each looked like a defect:
- **Engram falling out of ESPN's top 250 entirely** is the shape of a man who got hurt or released.
  He didn't: active, Denver, in camp, no event — checked against live sources, not memory. ESPN's
  pool is sorted by percent-owned, so the bottom of it churns on its own.
- **Tyreek Hill, Odell Beckham Jr. and Ricky Pearsall are priced but on no CHEAT row.** Hill is the
  one that looks alarming. He is a **free agent** recovering from a dislocated knee with ACL and LCL
  tears, with no guarantee he plays a snap in 2026 — so his 169.8 is right and the sheet is right to
  omit him. Note the tell: every off-sheet name sits in a **166.8-170.2** band, which is where ESPN
  parks men who are barely drafted at all. A number in that band is not a ranking.

### `check-cheat.py --live` — and why the old check could not have caught its own worst case

The file's own docstring named the gap and never closed it: it proves the file agrees with itself,
and **`DEPTH_TEAMS` is the thing it agrees with**. A club whose bye is wrong there is wrong on every
CHEAT row that matches it, and the offline run calls all of them clean.

`--live` asks ESPN which club each man is on today and when that club is off. **All 309 rows are
covered** — K and D/ST too, since the pool carries them. Measured 2026-08-15: 309 of 309 agree, and
so do `DEPTH_TEAMS`' 32 byes.

- **The pool is requested at 1200 on purpose.** ESPN returns its whole ~1026 at that number. Ask for
  the top few hundred by ownership and you drop the tail of the sheet — which is precisely where a
  stale entry hides. At 400 the check covers 267 skill players; at 1200 it covers all 309.
- **It was proved by fault injection, not by passing.** A check that has never failed is not a
  check. Two faults were injected into a scratch copy, **each internally consistent so the offline
  pass would still call it clean**: a player who is on no depth chart moved to the wrong club *with
  that club's real bye*, and a club's bye changed in `DEPTH_TEAMS` **and** in every CHEAT row
  carrying it. Offline reported 0 errors on both. `--live` caught both and exited 1.
- **Every failure path is fatal — deliberately.** A 404 exits 2 without printing a verdict. A live
  check that degrades quietly prints the same "clean" on a day the wire is down as on a day the
  sheet is genuinely right, and nothing in the output distinguishes them.
- **The default is unchanged**: no network, no `requests` import unless `--live` is passed, same 11
  notes, same exit 0. The clean line now states which of the two things it established.

**What it still cannot see, and this is the one that matters on Sept 7:** a man who is on a roster
but ranked where he should not be. A knee that will not be right until November reads as a perfectly
ordinary WR2 from here. Reading the wire is still a human job.

### Two alignment defects, found by looking and fixed

Prompted by "I feel like there are some design and alignment flaws" — which was right.

- **The hub had two left edges 18px apart** (`56e1683`). On the spine: the nav brand, the ticker,
  the hub heading, every group label, every door. Inset 18px: the countdown card **and its green
  accent bar**, the LEAGUE HISTORY hairline and the figures strip — every visible edge the hero
  has, sitting just inside the edge the ticker directly beneath them uses. The cause was a second
  gutter: `.wrap` already owns the page gutter and `.gameBorder` added its own on top. **The tell is
  in the rule**: `background`, `border`, `border-radius` and `box-shadow` are all explicitly zeroed,
  which is what a bordered card looks like after the border comes off — the padding that cleared it
  outlived it, and the print sheet had already dropped it. One edge now, at both widths.
- **Every group view spent 153px before saying what it was** (`3fef6c9`). A 44px touch target alone
  on one line, 38px of gap, a full-width band holding nothing but three right-aligned buttons, and
  an empty corner where the two half-used rows met. One row now, nav left and controls right:
  **69px back above the fold** on all six group views, controls not moved horizontally (last
  button's right edge 1150.4 before and after). Phone stacks as before.

**Two traps worth keeping, both avoided by design rather than by luck:**
1. **One auto margin, not two.** `.allctl` already justifies its own buttons to its end, so the bar
   only pushes the group right. `space-between` would have stranded the controls at the **left** on
   the hub, where `.uback` is hidden and the row has a single child — the same shape as the
   competing auto margins that stranded the theme toggle in `f8f9a105`.
2. **The phone override sits after the rules it overrides**, not in the file's main
   `(max-width:760px)` block ~700 lines earlier, where it would have lost to the unconditional
   rules at equal specificity and never applied. That is the shape that killed the site search.

**Checked and clean while looking**, so the next session need not re-chase it: 19 views at 375px
with **0 horizontal overflow**; the panel-header baselines from `9583c8d` hold (every `h4` on Draft
Rankings at 521.2, the `?` badge taking the leading slot rather than displacing its title); the
ticker's apparently hard-cut edges are **36px gradient fades** that a JPEG flattens; Standings,
Manager Profiles and Draft Night all sit correctly on the spine.

**One thing noticed and left alone:** in `@media print`, `.allctl` is set `display:none` as
screen-only furniture at one point and `display:block !important` by a **later, more specific**
rule (`body[data-route] :is(.uhub,header.gameBorder,.allctl)`), so Expand all / Collapse all /
Download as PDF very likely print into the PDF. Not measured — emulating print media needs a tool
this session did not have — and it predates both commits above. Worth checking against a real
PDF export before the freeze.

### The draft board records; it does not grade (`8c1f6f3`)

**Justin's call, and it reverses one stated consequence of ADR 0015** — which is annotated in place
rather than left to contradict the file, so read that bullet before putting anything back.

The board printed "over the going rate" as a green or red number on all 192 cells. It is the
sharpest thing on the page and it was competing with the board's own job, which is the round-by-round
record. The judging already has two homes with their methodology attached: **Draft Rankings** for
classes and **Steals & Busts** for single picks.

- **The figure is unpublished, not deleted.** Every cell keeps its tooltip — `Pick #7 · the going
  rate here was 86 · he returned 225 over replacement in 16 games` — so ADR 0015's "walk me through
  a disputed middle pick" still has its answer, on demand rather than always on.
- **`draftPicksPriced()` is untouched.** Nothing downstream moved.

**Then the control, `f723253`, the same day — because a hover is not a thing a phone has.** The
tooltip left the figure reachable on a desktop and *gone* on the devices this site is read on, which
is not "opt-in", it is broken for the audience. `#ratebtn` sits above the board and reveals all 192.

- **Board-level, not a target per cell**, for three reasons that are measurements rather than taste:
  the cell's own tap already belongs to the **player link**; the non-link area of a 120px cell is
  about **20px** tall; and 192 cells each carrying a 44px target would grow the grid this file has
  held at **1478px** since the columns were fixed. One control also beats 192 taps while you are
  dragging a 1478px board sideways.
- **It reuses `.rpick`**, so it inherits the existing `min-height:44px` phone rule instead of
  inventing a target size. Measured at 375px: 44px tall.
- **The span renders always; a class on the table reveals it.** No redraw, and it survives a season
  switch because `drawDraft` replaces the table's `innerHTML`, never the table.
- **The label does not flip between "Show" and "Hide."** It names the control; `.on` and
  `aria-pressed` carry the state, exactly as the season pills do. A label that changes tells a
  screen reader the button's *name* changed rather than its state.
- **`.pv`, `.pv.pos` and `.pv.neg` are back** (they were deleted with the span in `8c1f6f3`, which
  was right at the time — a rule kept for markup that no longer exists is the dead weight this file
  has twice had to hunt down). So the 2026-08-14 contrast note in this file that hand-checks
  `.pv.pos` and `.pv.neg` describes live elements again, but **not the same numbers**: it recorded
  8.56 and 5.16, and they now measure clear of AA in all four combinations below. Re-measure rather
  than trusting either figure.

**The sweep, and the trap in running it.** `contrast-sweep.js`, four combinations, **0 failures**:
{375px, 1280px} × {dark, light} — 62,858 checked at 375 in each theme, 23,506 dark and 24,880 light
at 1280. Two things worth copying next time:
- **Sweeping with the figures hidden measures nothing and reports the same zero.** `showrate` has to
  be forced on before `__runAll()`. Swept off then on, `checked` went **62,666 → 62,774**, which is
  the only reason we know the spans are in the population at all. A zero from the off state would
  have been an honest-looking lie of exactly the kind trap 5 exists to warn about.
- **The desktop dark run reports its theme as `?`** because no `data-theme` attribute is set.
  That is genuinely dark: `--pos`, `--neg`, `--surface` and the body ground are identical with the
  attribute present and absent, checked rather than assumed.

**Measured after, on the served file:** 0 `.pv` spans in the DOM, all 192 pick cells still drawn,
board width **1478px at both desktop and 375px** — the figure checked on every commit since the grid
was fixed, so it provably did not move — no console errors, and 8 views at 375px with 0 horizontal
overflow. Live 45 seconds after the push, confirmed by byte-comparing the served file against HEAD.

**Environment note that cost time:** the Claude-in-Chrome screenshot path and the in-app Browser
pane fail in *opposite* ways. Chrome screenshots fine but its router will not reveal a view while
its window is hidden — a hidden tab runs no `requestAnimationFrame` and throttles timers, so view
switching silently does nothing and `await`-based measurement times out at 45s. The in-app pane
routes and measures fine at 1280 but **cannot screenshot at all**. Use the pane to measure and
Chrome to look, and bring the Chrome window to the front first. The pane also has **no top-level
`await`** — build an iframe in one call and read it in the next.

---

## WHERE THIS STANDS — 2026-08-14: the draft-ranking overhaul
*The 2026-08-12 section below it is the previous state of play and is still accurate for everything
it covers.*

**Draft Rankings and Steals & Busts were rebuilt from the question down**, in a `/grill-with-docs`
session. The old metric ranked what a class *delivered to a roster*, which is drafting and roster
management measured together. The new one ranks the draft: **what each pick returned over the going
rate for its slot**, and nothing about what happened afterwards counts. Decisions in **ADR 0015**
(the basis) and **ADR 0016** (a split in the judged-metric standard); vocabulary in `CONTEXT.md`
under *going rate* and *judged metric*.

**Eight commits, all on `main` and live.** `refresh-players.py` is new and is the data layer.

### The four things worth knowing before touching any of it

1. **The fit family is load-bearing.** ADR 0008 rejected a per-slot expectation because it would
   not fall monotonically, and it was right for a local window: fitted as a rolling median over
   ±12 picks, this same data still inverts 22-26% of adjacent slots in every season. Fitted as a
   smooth curve it inverts **none, in any season**. The comment above `goingRate()` forbids a
   rolling average in as many words. **Do not "improve" it into one.**
2. **The floor is not cosmetic.** A pick's return is floored at zero. Unfloored, nine of the ten
   worst picks in league history were quarterbacks — because value is bounded below by
   −replacement and QB replacement runs ~290 against a back's ~130. See ADR 0015; note it directly
   contradicts ADR 0004, which was right for the metric *it* had.
3. **Defences are on Draft Rankings and off Steals & Busts.** Not squeamishness: a D/ST season only
   reconstructs to within ~12%, which is under one score point on a sixteen-pick class and a fifth
   to two fifths of the whole spread on a board about single picks.
4. **`refresh-players.py` is re-runnable and self-checking.** It asserts the baked subset reproduces
   the replacement line drawn over the full population — that check caught a real defect the first
   time it ran. Cache lives in `.nflverse-cache/` and is gitignored.

### Measured, not assumed

- **Scoring**: the league's rulebook computed from nflverse raw stats reproduces the archive's own
  points for **23,668 player-weeks at 100.0%** in every season 2018-2025. Four rules had to be
  recovered from the residuals rather than read off the scoring page — a blocked field goal is a
  miss, return and own-fumble-recovery touchdowns pay 6, a kicker scores whatever he does with the
  ball in his hands, a missed PAT costs nothing.
- **ADR 0015's gate**, on the full 140-row board: log-linear **0 inversions** in all twelve seasons,
  isotonic 0, rolling median fails at 149. Top 10 stable at 9-10 of 10 across fit families,
  Spearman 0.965-0.980. Bottom 10 is 6-7 of 10 — weaker than before the floor, and recorded.
- **Contrast**: 0 failures in every combination — desktop dark 23,502 then 63,166 elements, 375px
  dark 23,190 then 24,648, light 62,854. New elements hand-checked because one is a pseudo-element
  the sweep structurally cannot see: `.pv.pos` 8.56, `.pv.neg` 5.16, `.drgm` 4.58,
  `.drgm::before` 5.32.
- **The draft grid did not move**: 1478px before and after, measured in side-by-side iframes.
  `col.tmcol` is a fixed 120px, so the per-pick surplus rides inside the column.

### What this closed, and what it opened

**Closed:** the board is 140 rows, not 138 — it reads no roster data, so the two team-years excluded
for corrupted roster records are back. All twelve seasons are on **one** measurement, which retires
the 2014-2017 coarse basis, the uncounted two-point conversions, and the coarse K/D-ST treatment in
one move. The 2020 Round 16 / Pick 8 hole stops mattering. 13KB of dead code went with it
(`rankPicks`, `STARTER_PTS_2017`, `DRAFT_TOTALS_2014_2017`).

**Open, and honest about it:**
- **2014-2017 cannot be validated directly.** The 100.0% check needs the archive's own weekly
  points, which only exist from 2018. Those four seasons rest on the rulebook being right. 2014's
  whole-block yardage was reverse-engineered in an earlier session and reproduces known totals
  exactly. **2014's defensive scoring was the last thing resting on inference and is now closed** —
  not by finding the settings page but by showing it cannot matter: strip every category whose 2014
  status is in question and no class score moves more than a point (see ADR 0015). What remains
  unvalidated is the *offensive* rulebook for 2015-2017, which is the modern one and is assumed
  unchanged.
- **The era check is 2018-2025 only.** The half-PPR era runs ~5% hotter than 0-PPR on total drafted
  VOR, against a 17% swing inside a single era — which is why the headline figure is comparable
  across years. 2014's rulebook is a far larger difference and that check has **not** been re-run
  across all twelve seasons.
- **A defence's weekly line differs from ESPN's** by ~12% on a season. Bounded, disclosed, and the
  reason defences are off Steals & Busts.
- **One drafted man in 2,239 joins by name rather than by id** (Charles Johnson 2015; nflverse
  writes "Charles D. Johnson"). The fallback is restricted to his drafted position because his
  namesake is a defensive end.

---

## WHERE THIS STANDS — end of 2026-08-12
*Read this first. Everything below it is the record of how it got here; the detail sections are
worth reading only for the area you are about to touch.*

**The overhaul is finished and live, and so is the visual polish pass on top of it.** `main` is at
`e06062c`, working tree clean, and **the served file is byte-identical to it** — 2,616,721 bytes,
sha256 `02fa621ee02bd956`, checked against the live URL. Twenty-one commits landed on 2026-08-12
for the overhaul; nineteen more the same day for the polish pass and its follow-on — see *The
visual polish pass* below, and ADRs 0012 / 0013 / 0014 for what it decided.

**The floor now measured on every commit:** `contrast-sweep.js` at **0 failures** in all four
combinations — {375px, 2048px} × {dark, light} — *including the profile modal*, which the sweep
reached for the first time this session. Load timing 151ms → 150ms against the pre-pass file.
Total cost of the whole pass: **+11,210 bytes** against a +15KB ceiling.

**The floor is only as good as the population it covers, and that population had three holes.**
Each produced an honest-looking zero: the phone card layout (396 failures, found before this
session), the profile modal (2 failures, not on any route), and **pseudo-elements, which the sweep
structurally cannot measure at all** (2 failures). All three are now closed — the first two by
extending the sweep, the third by enumerating the class by hand, since no extension can fix it.
See traps 5 and 7 in `contrast-sweep.js`.

**What shipped that day, in order:** the two-column board header · hub doors sized by a real grid
rather than by group population · the Manager Profiles rail and sparklines · pinned rank/owner
columns on the standings · the contrast bar re-measured and **396 phone AA failures fixed** ·
**dark as the default** (ADR 0011) · `check-cheat.py` and the ADP name-join fix · the
`Bridesmaid`/`Contender` badges · and **every board deferred to first reveal**, taking script time
from 578ms to 258ms.

### Nothing is blocked. What is actually left:

1. **Due before draft night — the only dated work.** Re-run within a few days of **Sept 7**, then
   review with `git diff` before committing (ADR 0001/0002 pattern).

   **PowerShell — this is the PC this file hands off to:**
   ```powershell
   python refresh-adp.py --dry-run; if ($?) { python refresh-tiers.py --dry-run }; if ($?) { python check-cheat.py --live }
   ```
   `&&` is a **parser error** in Windows PowerShell 5.1 — not a failed command, a refusal to run
   the line at all. This block used to carry the bash form below and nothing else, in a file whose
   own title says "continue on PC". Running the three separately is just as good, and better if
   you want to read each diff before going on.

   **bash / Git Bash**, if you are on the Mac or in a POSIX shell:
   ```bash
   python refresh-adp.py --dry-run && python refresh-tiers.py --dry-run && python check-cheat.py
   ```
   Only the two refresh scripts take `--dry-run`; `check-cheat.py` never writes and takes
   `--live` / `--quiet` / `--strict` instead. It exits 1 on any ERROR.
   **`--live` is the flag that matters here** (2026-08-15): without it the check can only prove the
   file agrees with itself, and `DEPTH_TEAMS` is the authority it agrees *with* — so a club whose
   bye is wrong there is wrong on every row that matches it and the run still says clean. With it,
   every club and bye is checked against ESPN's own data. It needs `requests`; the default path
   still needs nothing and touches no network.
2. **The last ~50ms of load**, if anyone cares: the draft cheat sheet, the hub hero and figures
   strip, and the two layout-reading helpers are all still eager, **on purpose**. The cheat sheet in
   particular is the one surface used under time pressure on Sept 7 and never rehearsed — do not
   defer it for ~17ms.
3. ~~**Two design questions never put to Justin**~~ — **both answered and closed 2026-08-12.**
   - *The way home* is now **"← All sections"**, matching the nav toggle's own word. ADR 0007 put
     navigation in the functional register; "All boards" was the editorial voice leaking into a
     nav control.
   - *Deep landing* needed no change, and **the concern itself was stale**: it describes the
     pre-ADR-0007 accordion, when every section shared one enormous document. Measured on the
     routed app, `#h2h` lands with the board's own masthead at the top of the screen — viewport
     y=66, just under the 53px nav — from a cold load *and* from an in-app click, in a document
     **2,282px** tall with `scrollY 733`. There is no 16,000px scroll to be deep inside any more.
     **Watch out for one measuring trap here:** read those numbers too early in the load and you
     will see `scrollY 214,182` in a 217,391px document, because the anchor jump happens before
     routing collapses the page to one view. That is a transient, not what a reader gets — the
     same "wait for the state to settle" mistake as the mid-toggle theme reads elsewhere in this
     file.
4. **Long-tail data gaps**, all disclosed in the UI and none of them blocking: the 2020 Round 16 /
   Pick 8 slot (player unrecoverable from ESPN), 2014-2017 K/D-ST still on the coarse basis, the two
   corrupted 2014/2015 *Beasts of the Middle East* snapshots worked around in `DRAFT_TOTALS_2014_2017`
   but not fixed in `ROSTERS.S` itself.
5. **Three things the visual pass left open on purpose**, none of them code the next session can
   simply fix:
   - **Leo Thaweechok's black "TK" logo.** Legible now — it has a plate and a ring where it had
     neither — but still the weakest mark on the page, because a dark logo on a dark plate is a
     losing hand. **Only a re-cut asset fixes it.** Drop a light version into `OWNER_LOGO` and
     nothing else needs to change.
   - **Rules table at 375px**: five cells overflow their content box by up to 6px. Text wraps,
     nothing clips, no page-level scroll. Cosmetic, measured, left alone.
   - **`--pos` and `--accent` are the same colour in both themes.** An accepted constraint, not an
     oversight — see ADR 0012 for why shifting it is worse than living with it, and for the one
     condition that would break it.

### Two tools and one check — use them rather than rebuilding
- **`check-cheat.py`** — the `CHEAT` vs `DEPTH_TEAMS` cross-check, written down. Before draft night
  and after any hand-edit of the sheet.
- **`contrast-sweep.js`** — the ADR 0005 floor, measured. Paste into the console on a served copy
  and run `__runAll()`. **Both widths, twice per width** — its header explains why, and the current
  zero-failure baseline is in there. It now sweeps the profile modal too, and carries **seven**
  documented traps, three of which were walked into on 2026-08-12. Two limits it cannot cover on
  its own: **every pseudo-element** — `::before`, `::after`, `::placeholder` — because it reads
  element text nodes and those have none (trap 7, with the query that enumerates them), and
  **anything reached only by interaction** that nobody has added to `__runAll` (trap 5).

**One check worth re-running after any large CSS edit** — it found two dead rules on 2026-08-12,
one of them a whole feature. Scan for a declaration inside a media query that a *later*
unconditional rule overrides at the same specificity; such a rule can never apply, and both
versions read correctly in isolation, which is why it survives review:

```
for each rule: record (selector, property, source offset, inside-media?)
flag where a media-query declaration is followed, later in the file,
by an unconditional declaration of the same property on the same selector
```

Across the whole stylesheet there were exactly two hits: `.searchbox{display}` — the site search,
invisible at every width since it was written — and `.rrow{grid-template-columns}`, deleted.

### The three things that would have shipped broken without measuring
Worth internalising, because all three were invisible in the source and two were already live:
- **396 AA failures on the phone.** ADR 0005's original sweep only ever ran at desktop width, and
  the phone card layout is a *different population*, not a narrower one.
- **A receiver with no ADP.** ESPN writes `Tre' Harris`, NFL.com and PFR write `Tre Harris`, and the
  runtime lookup is by exact name — so he silently had no price and no value/reach tag.
- **2014 and 2015 missing their playoff column** for years, because `seasonRows()` read playoff
  totals before they were summed. Deferring the draw fixed it by accident; the restored column was
  then verified against the raw game log *and* against Justin's memory.

---

## The visual polish pass — begun 2026-08-12

Ten commits, settled in a `/grill-with-docs` session and landing one at a time before the
Sept 3 soft freeze. The frame: **polish inside the existing language** (no new palette, no new
fonts), **desktop is the beauty bar and the phone stays the correctness bar**, an **explicit
two-register split** (editorial voice owns hero and board headers, product-crisp owns every data
surface), **CSS-only, zero added JS, ~+15KB ceiling**. Decisions land in ADR 0012 (colour roles),
0013 (type scale) and 0014 (measure and masthead).

**The pass is complete. Nine commits landed; one was dropped as unnecessary.**

| # | commit | what it turned out to be |
|---|---|---|
| 1 | `af32287` | `--accent2` → `--enc`. Not one dead token: **eight** live sites, five of them encoding. |
| 2 | `adf2c4b` | The role table. 37 static-text rules + 13 fills/borders. Also fixed the sweep's parser. |
| 3 | `1f3bf4d` | The type scale. Eight values, eleven names; 9px gone. |
| 4 | `b0eb4bb` | Measure + masthead. The three-width stack was **one board**, not a pattern. |
| 5 | `1aa3cd4` | Avatar plates. Root cause was one line stripping the plate from 14 of 17 marks. |
| 6 | — | **Dropped.** There are no emoji; the trophy was already an SVG behind `const TROPHY`. |
| 7 | `e22b43e` | Champion edge. There was no striping, and `.repeat` was a real undisclosed fact. |
| 8 | `f9a0105` | Nav grouping. Two competing `auto` margins had stranded the toggle mid-bar. |
| 9 | `fb02702` | Centred remainders — but only where a full row exists above them. |
| 10 | `2623976` | One focus ring for everything; hover added where missing, removed where it lied. |

**Then six more, after the pass, on the same day.** Five of them are bugs the pass surfaced but
did not itself create — the pattern worth noticing is that each was found by pulling a thread
rather than by audit:

| commit | what it was |
|---|---|
| `5f73ab8` | The profile modal's two real AA failures, **and** `__runAll` extended to sweep it. |
| `e976d66` | The awards wall: every badge was one gold pill, so gold announced the *absence* of a ring. |
| `5be6b93` | "← All sections"; the deep-landing worry measured and retired as stale. |
| `2a57e38` | `contrast-sweep.js`'s own trap 5 comment asserted a number this tool exists to disprove. |
| `883743e` | **The site search was dead at every width** — a finished feature nobody could reach. |
| `af26187` | The last media-query rule killed by a later unconditional one, found by scanning for the shape. |
| `5b17696` | This file's state of play, brought up to date. |
| `48f27cb` | `.tag.best` was mint-on-mint-tint — a violation commit 2's audits could not see. |
| `e06062c` | Card stat labels one step up **and** off the floor: `::before` had never been measured. |

Every commit verified in all four combinations — {375px, 2048px} × {dark, light} — at **0
contrast failures**, with the draft cheat sheet proved structurally identical each time.
Load timing measured against the pre-pass file at three runs each: **151ms → 150ms**. Byte
cost of the whole pass: **well under the +15KB ceiling**.

### Sweeping at phone width without a resizable browser

`contrast-sweep.js` needs a real 375px viewport, and neither the in-app browser pane nor Chrome's
`resize_window` could give one in this session — `resize_window` reports success while
`window.innerWidth` stays at the desktop value, so every "phone" measurement was silently a
desktop one. **A same-origin iframe solves it: media queries inside an iframe evaluate against the
iframe's own width.** Serve the file (`python -m http.server 8765`), open it, then from the
console:

```js
const f = document.createElement('iframe');
f.src = '/index.html'; f.width = 375; f.height = 740;
document.body.appendChild(f);
// f.contentWindow.innerWidth === 374, and (max-width:760px) matches inside it.
// Inject contrast-sweep.js into f.contentDocument and call f.contentWindow.__runAll().
```

Same trick does before/after comparison: point one iframe at `/index.html` and another at a copy
of the previous commit (`git show HEAD:index.html > _head_tmp.html`), drive both, diff the results.
That is how commit 3 proved the cheat sheet was structurally untouched.

### Found while verifying — what it was, and what happened to it

The pass's rule was: anything found mid-pass gets written down rather than fixed, because an
unplanned change to a live site three weeks from draft night is an unverified one. That held for
the duration of the pass; several entries were fixed afterwards, each with its own verified
commit.

**These entries are a mix, so read the body of each rather than trusting the heading.** Three
kinds are here: things fixed later (each says so, and several record a wrong diagnosis before the
right one — usually the more useful half), accepted constraints that are decided rather than
outstanding (`--pos`/`--accent`, the dark avatar plate, gold and rust keeping their encoding
work), and genuinely open items. **For what is actually still open, use item 5 of *What is
actually left* at the top of this file** — it is the short list, and it is maintained.

- ~~**28 AA failures in the profile modal**~~ — **fixed, and the sweep now covers that surface**
  (trap 5). Two real defects, both pre-existing: the season list's champion row wore the same gold
  tint the Champions board wore, pushing the PF figure to 4.34 (fixed with an edge, as ADR 0011
  prescribes), and `.pfclose` floated over the 55% black scrim with its own white tint lightening
  the ground to mid-grey, ~3.9 in light (fixed with a solid dark ground).

  **The lesson is about the measuring, not the fixing.** Chasing this, an ad-hoc scanner written
  in the console reported ~11 further failures in the hero band — the manager's name at "1.09" —
  and acting on them made the page genuinely worse before a screenshot caught it. `.pfheromain`
  paints a **theme-dependent `radial-gradient`**, so `backgroundColor` is transparent there and an
  ancestor walk lands on `.pfhero`'s dark colour underneath. Every one of those failures was
  fiction. **`contrast-sweep.js` already guards against exactly this — trap 4, `gradientSkipped`
  — which is why the real tool reported 28 and the throwaway one reported 39.** Do not
  re-implement the sweep in the console; run the sweep.
- **`contrast-sweep.js` was mis-parsing every `color(srgb …)` background — fixed in commit 2.**
  `parse()` scraped all numbers from the string and then skipped one for `color()` values, on the
  assumption that the colour-space keyword contributed a number. `srgb` contains no digit, so
  nothing was skipped: `r` took `g`'s value, `b` took the **alpha**, and alpha fell back to 1.
  The `.recjump` bar — `color(srgb .07 .09 .157 / .92)`, and the very element trap 3 was written
  for — measured as a saturated `rgb(24,40,235)`. Every ratio computed against it was fiction,
  and it produced one phantom failure in commit 2 (`.rlab` at a claimed 2.90; the true ratio is
  ~5.6). The fix removes the keyword instead of counting past it, which also handles a space
  whose name *does* end in a digit (`display-p3`) — the case that probably motivated the original
  offset. **Consequence: any zero-failure baseline recorded before 2026-08-12 was measured with
  this bug and is only trustworthy for elements over plain `rgb()`/`rgba()` backgrounds.**
- **`--pos` and `--accent` are the same colour in dark** (`#2FDA87`) — and in light
  (`#0C6B4C` vs `#0B6B4E`). Commit 2 decided **not** to shift it: every light-theme green far
  enough from the accent to be distinguishable has to leave green altogether (teal `#146B6B`,
  olive `#3F6B22`), which costs more than it buys on a page whose complaint is clashing colour.
  ADR 0012 records the shared value as an accepted constraint, disambiguated by shape: interaction
  mint always sits on a control, and bare numeric text is never a control. The rule holds because
  commit 2 removed mint from all 37 static-text rules — it would not have held before.
- **Gold and rust are already doing encoding work.** The rules-change chips use blue for
  format, gold for scoring and rust for the draft — a three-family category encoding, documented
  in a comment near `lazyBoard("rules", …)`. So "gold = ceremony only" is not true of the file as
  it stands, and ADR 0012 has to say what happens to that chip set.
- **The sparklines colour their newest point gold on all three charts** — emphasis, not ceremony,
  and another pre-existing exception to the same rule.
- **The avatar plate is dark in both themes, and that is forced, not chosen.** Commit 5 tried a
  light plate first — it looked excellent in the manager grid and destroyed the Champions rows.
  The two surfaces use different assets: the grid renders photographs with `object-fit:cover`
  (their own background, fine on any plate), while rows render `OWNER_LOGO` vectors, which are
  **white artwork on transparent PNGs** drawn for a dark ground. On a light plate they vanish
  completely. So a dark plate covers vectors and photographs both, and a light plate covers
  neither. The residual cost: genuinely dark artwork — Leo Thaweechok's black "TK" is the only
  one — reads dimly. It is legible now (it has a plate and a ring where before it had neither)
  but it is the weakest mark on the page. **Only a re-cut asset fixes it properly**, which Q5 put
  out of scope. If a light version of that one logo ever turns up, drop it in and nothing else
  needs to change.
- **Pseudo-elements are outside `contrast-sweep.js` entirely, and both of them were failing.**
  The scan reads element *text nodes*; a `::before` or `::placeholder` has none, so nothing they
  render has ever been measured. Found by accident — bumping the standings card stat labels one
  size step prompted a hand-check, and `td[data-l]::before` came back at **3.93 in dark** against
  4.5. The size was never the problem: they had been under the floor since they were written, at
  11px and 12.5px alike. So the class was **enumerated rather than sampled** — exactly two
  pseudo-elements in the file draw text and set a colour, and both were under:
  `#searchinput::placeholder` (4.17) and `td[data-l]::before` (3.93). Both fixed. The query that
  finds them is written into trap 7 so it can be re-run instead of rediscovered. **Any new
  text-bearing pseudo-element must be measured by hand — the tool will report zero either way.**
- **An audit keyed to token *names* misses aliases and tint variants.** `.tag.best` was
  `color:var(--pos)` on `background:var(--accent-soft)` — mint text on a mint tint, on a chip
  nobody can click. Commit 2 missed it **twice**: its text pass searched `var(--accent)` and this
  says `var(--pos)`, which is the same value under a different name; its fill pass searched
  `var(--accent)` and this says `var(--accent-soft)`. Both queries were reasonable and both were
  blind. Fixed to the neutral chip. If a future pass repaints by role, search by *resolved value*
  as well as by token name.
- **The site-wide search was dead at every width, and is now live.** Two rules with the same
  specificity and near-identical comments, written at different times: an
  `@media (min-width:760px){.searchbox{display:block}}` sitting about ten lines *above* the
  unconditional `.searchbox{display:none}` it was meant to override. Later wins, so it never
  did. Behind it: an index over every manager, every team name from any year, every season and
  all 21 sections, a `/` shortcut, an ARIA listbox — built on every page load and reachable by
  nobody. Both interaction paths were verified working before enabling it (a manager hit opens
  the profile modal; a section hit routes correctly). It stays hidden below 760px on purpose —
  the nested nav menu beats typing on a phone.
  **Making it visible surfaced a failure the sweep cannot see:** the placeholder measured 4.17
  against a required 4.5 (now `.52`, 5.05). `contrast-sweep.js` reads element *text nodes*, and
  an `<input>` has none, so `::placeholder` is outside its population entirely — check
  placeholders by hand.
- ~~**There is a hidden site-wide search in the top nav**~~ (`#searchbox`, `display:none`, holding
  `#searchinput`). Anything done to the nav in commit 8 has to account for it. — *This was the
  original sighting, written in commit 1 and left as a curiosity for seven commits. It was noted,
  worked around in the nav commit, and never asked the obvious follow-up question: why is a
  finished feature set to `display:none`? Worth remembering as the cheapest kind of miss —
  the evidence was in hand the whole time and only wanted one more question.*

---

## Resolved this session
- **Repo consolidation** (ADR 0001): this git repo is now the sole working copy. The old Mac
  working folder, `deploy/` folder, and transfer-zip copies are stale/archived — don't edit them.
- **ADP refresh will be automated** (ADR 0002): write-back into `index.html`, reviewed via
  `git diff` before commit, instead of hand-editing ~250 values.
- **Draft tiers will come from FantasyPros half-PPR ECR** (ADR 0003), not hand-curated, not ESPN
  (ESPN's public endpoint has no half-PPR field). Use FantasyPros' own `tier` field directly —
  don't build a separate clustering algorithm.
- **2020 missing draft pick — corrected and closed out as far as data allows.** The prior
  session's "round 16, overall #192, Revenge Tour" note was re-derived from full ESPN Draft
  Recap screenshots (all 16 rounds, "By Round" and "By Team" views) and corrected:
  - The true gap is **Round 16, Pick 8** (ESPN's own sequential numbering skips the missing
    slot entirely, so it isn't literally "#192" — Round 16 only has 191 total picks logged,
    one short of 192).
  - **Roster totals, counted directly from the "By Team" view:**
    - **The Revenge Tour** — 16/16, complete. They picked up compensating extra picks in
      rounds 2 (×3), 4 (×2), and 10 (×2) that exactly offset having zero picks in rounds 1, 3,
      6, and 16. Confirmed via a directly-evidenced round-10 trade (Dallas Goedert, pick #119,
      matching the user's recollection of a trade with Christian Winn's "All I Do Is Winn").
    - **All I Do Is Winn** — 15/16, genuinely short one player. They have zero picks in rounds
      2, 4, and 10 (the same three rounds where Revenge Tour gained extras) but only 2 extra
      3rd-round picks in return — a real 3-for-2 consolidation trade, not a data error. They
      **do** have a Round 16 pick (Jared Goff, #190).
    - Team Brax independently re-verified as 16/16 complete (same compensating-trade pattern,
      rounds 1 and 6).
  - **Conclusion:** by elimination from the Round 16 team list (11 of 12 teams present; Revenge
    Tour is the one absent), the blank Round 16 / Pick 8 slot structurally traces back to
    Revenge Tour's draft position — consistent with the original hypothesis. But since Revenge
    Tour's roster is already complete without it, this reads as a pick they traded away
    pre-draft that was never actually used/recorded by whoever received it (orphaned/forfeited
    in the live 2020 draft), not a genuine "17th player" waiting to be identified.
  - **Still open:** the player, if one was ever actually drafted there, isn't recoverable from
    ESPN's data — it has no player or team attached at all. Would need the user's own memory or
    a leaguemate's records; no ESPN league-ID API lookup exists in the codebase currently.
- **Backups retired.** Once the tier/ADP refresh work was committed (satisfying the "once
  current state is committed to git" precondition), deleted all four stale loose files from the
  parent folder: `index_9-dark_3-improved.BACKUP-before-reorg.html`,
  `index_9-dark_3-improved.backup-before-webp.html`, `South-FFL-Website.zip`, and
  `index_9-dark_3-improved.html` (the pre-git working copy) — all superseded by this git repo
  per ADR 0001. The parent folder now contains only `south-ffl/` (this repo) and unrelated
  session files (`.claude/`, `skills-lock.json`).
- **`refresh-tiers.py` built (ADR 0003)** — and the ADR's original plan had a real bug, caught
  before it shipped: the single "all positions" page ADR 0003 named
  (`half-point-ppr-cheatsheets.php`, `position_id: "ALL"`) has a *global cross-position* `tier`
  field, not a per-position one — RB/WR dominate the early tiers by scarcity, so e.g. the #1
  overall QB was landing in "tier 3". Switched to FantasyPros' actual per-position draft
  cheatsheets instead (`qb-cheatsheets.php` for QB — standard scoring, since QB output doesn't
  depend on PPR; `half-point-ppr-{rb,wr,te}-cheatsheets.php` for the rest), each with a properly
  position-scoped `tier`. Verified against a live render (56 tier dividers, sane groupings).
  Scope intentionally matches the prior hand-curated depth (QB 20 / RB 40 / WR 45 / TE 20,
  K/DST untiered) — the script derives that cutoff from the current file rather than hardcoding
  it, so it won't silently drift if the depth is changed deliberately later.
- **`refresh-adp.py` retrieved from the Mac and rebuilt (ADR 0002)** — the version that existed
  was report-only (never wrote back), pointed at the old pre-git filename
  (`index_9-dark_3-improved.html`), and fetched ESPN's *full-PPR* ADP (`leaguedefaults/3`). Two
  real findings came out of rebuilding it:
  - **The site's ADP source and its own labeling disagreed.** `ADP_2026`'s comment and the UI
    tooltip both said "PFF" (pff.com/fantasy/rankings/draft), while ADR 0002/`CONTEXT.md` both
    described ADP as ESPN-sourced. User's call: switch to ESPN half-PPR — done, both the source
    comment and the UI tooltip (`Consensus ADP (PFF, ...)` → `(ESPN, ...)`) now match reality.
  - **ESPN *does* have a public half-PPR ADP endpoint**, contrary to ADR 0003's research (which
    only checked `playerRankType` labels — true STANDARD/PPR/ELIMINATION/SUPERFLEX, no HALF
    variant there). `leaguedefaults/8` ("FFL Half PPR Scoring") exists and its
    `scoringSettings.scoringItems` confirm 0.5 points/reception — genuinely half-PPR, just
    mislabeled `playerRankType: "PPR"` in ESPN's own metadata. The script verifies that
    0.5-points-per-reception setting itself before trusting any ADP from that id, so if ESPN
    ever renumbers/repurposes it, the script fails loudly instead of silently mislabeling
    full-PPR data as half-PPR. (Doesn't retroactively change ADR 0003's FantasyPros-for-tiers
    decision — that was about the *tier* field specifically, which ESPN's endpoint still doesn't
    expose at all.)
  - Verified against a live render alongside the tier refresh — value/reach delta tags (184 of
    them) recompute correctly, since they're derived live from `ADP_2026` in JS, nothing extra
    needed writing back for those.
  - **Process note, for whoever reads this next:** mid-session, `git checkout -- index.html`
    was run to fix a bug in the ADP script and accidentally discarded the *already-written*,
    not-yet-committed tier refresh along with it (both lived in the same uncommitted
    `index.html`). Recovered by re-running both scripts — but the lesson holds: don't
    blanket-revert a file with mixed uncommitted work, `git stash` or a scoped patch instead.
- **A serious bug in `refresh-tiers.py`/`refresh-adp.py` themselves, caught before shipping
  further.** Both used a single whole-document regex
  (`(?:/\*[\s\S]*?\*/\s*\n)*const NAME = `) to strip/replace the source comment above
  `ADP_2026`/`TIER_2026`. The lazy `[\s\S]*?` inside a repeated group can backtrack across huge
  unrelated spans — on a live run it matched from near the top of the `<style>` block all the
  way down to `const TIER_2026 =`, and `re.sub` replaced that entire span (fonts/CSS/JS
  preamble) with a two-line comment, silently deleting ~2MB of the file. Not caught by the
  script (no shape/size sanity check existed) — caught by chance while eyeballing line numbers
  during the tools audit below. Fixed by replacing the regex with a bounded backward scan from
  the known declaration position (`strip_preceding_comments()` in both scripts) that can only
  ever touch the comment block(s) directly above the target `const`. Verified via a scratch-copy
  test (both scripts, run twice each) before reapplying to the real file. **Lesson:** a
  whole-document regex with a lazy wildcard inside a repeated group is not safe for
  find-and-replace on a large file, even when it "worked" on the first try — test idempotency
  (run twice) and diff `--stat` byte/line counts before trusting a write-back script.

## Started this session: auditing the draft-prep tools ("rock-solid" pass)
Scope, per `CONTEXT.md`: data-correctness and draft-prep-tool fixes only — `CHEAT`,
`DEPTH_TEAMS`, `ADP_2026`, `TIER_2026`, and the value/reach/cliff logic that reads them. Not a
UI/feature audit.

**Checked and clean:**
- `CHEAT`: position-rank sequences, team abbreviations (all 32 valid), bye-week ranges,
  duplicate names/ranks within a position — all clean, no issues found.
- `CHEAT` internal bye-week consistency (every player's bye matches their own listed team's true
  bye, per `DEPTH_TEAMS`) — zero mismatches.
- `DEPTH_TEAMS`: exactly 32 teams, no duplicate/missing abbreviations vs. `NFL_LOGO`.
- Draft night countdown target (`2026-09-07T18:00:00-05:00`) — confirmed Sept 7, 2026 actually
  is a Monday, matches "Monday Sept 7" everywhere else in the docs.
- 40 players present in `DEPTH_TEAMS` but absent from `CHEAT` (backup QBs, TE2s, kickers) —
  spot-checked several for hidden name-typos against `CHEAT`; none found. This is intentional
  scope (`CHEAT` only ranks the draftable/fantasy-relevant depth per position), not a bug.

**Found and fixed:** `CHEAT` had **A.J. Brown listed at `PHI`/bye 10** — stale. He was traded
Philadelphia → New England on 2026-06-01 (confirmed via live web search against SI, NBC Sports,
ESPN, NFL.com, Yahoo — not assumed from training-data knowledge, which predates the trade and
would have said PHI). `DEPTH_TEAMS` already had this correct (`NE`, bye 11) — cross-referencing
the two datasets against each other is what surfaced it; internal-consistency checks on `CHEAT`
alone did not (his stale entry was self-consistent, just outdated). Corrected to
`["A.J. Brown","NE",11]`. This was the only mismatch between the two datasets — confirmed
isolated, not a systemic staleness problem, by re-running the same cross-check after the fix
(zero remaining mismatches).

**Found and fixed:** player-link resolution had a real, if minor, gap. `dstTeam()` (used by
`pLink()`/`cheatLink()` to route D/ST rows to the team's actual page instead of a name search)
only ever handled short 2-3 letter abbreviations (the 2014-2015 archive's "Sea D/ST" style).
`CHEAT.DST` names defences by mascot only ("Broncos D/ST"), longer than any real abbreviation,
so the short-code path silently failed for all 22 team-defense rows on the current draft cheat
sheet — every one fell through to a generic name search instead of linking to the team's real
page. Fixed by adding `MASCOT_ABBR` (built once from `DEPTH_TEAMS`, which already has mascot →
abbreviation pairs) as a second lookup path in `dstTeam()`. Verified live: all 6 sampled D/ST
links now resolve to real team pages (e.g. `pro-football-reference.com/teams/den/2026.htm`)
instead of a broken search. Doesn't touch the archive short-code behavior at all.

**Also checked:** `LINK_TO` is hardcoded to `"pfr"` (not a runtime toggle) — all player links go
to Pro-Football-Reference except where `ESPN_VERIFIED` explicitly overrides per-name (plausibly
deliberate: PFR has no game-log page yet for players before their season starts, so
`ESPN_VERIFIED` exists specifically to bypass that for current-year draft prep — not flagged as
a bug). 285/309 `CHEAT` names resolve to a direct profile link; the remaining 24 (22 were the
now-fixed D/ST rows, plus 2 real players — Treylon Burks, Jaylin Lane — with no `PFR`/`ESPN`
entry yet) degrade gracefully to a name search, a reasonable fallback for genuinely uncovered
players. No duplicate IDs found in `ESPN_VERIFIED` (would indicate two players sharing one
profile page). `CHEAT` has zero null overall-rank values, so the value/reach threshold math
(`max(3, round(orank*0.10))`) never hits its one real edge case (`orank` coercing to 0 in JS
arithmetic if null) — confirmed via data, not just code-reading.

**Audit is in a good stopping place, not fully exhaustive.** Two real bugs found and fixed
(stale A.J. Brown team/bye, broken D/ST links) plus the earlier regex bug in the refresh
scripts. Everything checked came back clean or got fixed — no more known open threads in this
area, but this wasn't an exhaustive line-by-line review of the ~2.5MB file, just the data
structures and code paths most directly tied to pre-draft correctness.

## New feature this session: Draft Rankings
Every team's draft, every year, ranked best-to-worst by total fantasy points scored **while on
the drafting team's own roster** — a player taken, dropped, and later a star elsewhere earns the
drafting team nothing (that's Steals & Busts' job, above). Lives under Draft, Rosters & Trades →
Draft Rankings. Best 10 / Worst 10 shown by default, full list (138 of 140 team-drafts — two
excluded, see below) behind a collapsed "all 138" disclosure. Each row links through to that
year's actual draft board.

**Methodology went through two real revisions before landing where it is now — worth knowing the
history if this gets touched again:**
1. First version summed a player's *entire season* regardless of who held him — wrong, since it
   credited the drafting team for points scored elsewhere after being dropped.
2. Fixed for 2018-2025 (scans each team's own week-by-week roster via `rosterAt`, only counts
   weeks that team actually held him). 2014-2017 initially got a coarser stand-in (whole-season
   in/out based on the end-of-season snapshot) since this file has no week-by-week roster history
   that far back.
3. **User asked for the 2014-2017 gap closed properly rather than left coarse — done.** Pulled
   real per-game box scores directly from ESPN's core stats API (`site.web.api.espn.com/.../
   athletes/{id}/gamelog?season=Y`), independent of the fantasy platform's shorter data
   retention, and applied this league's own scoring rules by hand per game. Combined with
   week-by-week roster membership (`mRoster`, which *does* go back to 2014 even though this
   file's own `ROSTERS.S` doesn't) to attribute each player's weeks to whichever team actually
   held him. All of this ran through the user's authenticated ESPN session via the Claude in
   Chrome browser tool — SWID/espn_s2 cookies were never seen or persisted, only used live,
   read-only, in-browser.

**2014's scoring formula had to be reverse-engineered, not guessed — and was confirmed exactly.**
The site's `SCORING_CHANGES` comment already noted 2014 used "whole points per block of yards"
before 2015's fractional rates, but not the exact block sizes. Solved by algebra against known
season totals: `trunc(passYds/25) + trunc(rushYds/10) + trunc(recYds/10)`, truncated toward zero
**per game** (not floored, and not summed-then-truncated at the season level — per-game trunc
was the only formulation that reproduced known totals exactly). Validated against multiple
players with zero error (Julio Jones, Marshawn Lynch exact; one WR off by exactly 2, consistent
with an untracked 2-point conversion, not a formula error).

**Known, disclosed limits remaining (all called out directly in the page's "How this works"):**
- 2-point conversions aren't in the gamelog stats source and go uncounted for 2014-2017 — a
  handful of isolated 2-point misses, not a systemic gap.
- Kickers and D/ST for 2014-2017 still use the older, coarser whole-season method (full season
  if on the roster when it ended, nothing if not) — real per-week K/D-ST stats (field-goal
  distance buckets from `gamelog`'s `fieldgoals` category; points+yards allowed would need a
  team-boxscore-per-game pull, `site.web.api.espn.com/.../summary?event={id}`, `totalYards`)
  were scoped out as a materially bigger lift for a smaller share of total points. Picked up
  precisely for QB/RB/WR/TE only, which is ~87.5% of roster composition (11 of 16 spots).
- Some ESPN athlete IDs return no gamelog data for **any** season, not just 2014-2017-specific
  gaps (confirmed via direct testing, e.g. Rob Gronkowski's id 13229 fails at every season
  queried) — a real per-player ESPN data hole, not a bug here. Those specific picks fall back to
  the same season-total-if-on-final-roster method as K/D-ST.
- Two team-years are excluded entirely, not shown as a misleading number: 2014 and 2015 "Beasts
  of the Middle East" both have corrupted roster records at the source — 2014's snapshot is
  empty, 2015's is full of players retired years before that season (LaDainian Tomlinson, Randy
  Moss, Donovan McNabb) — confirmed via two independent ESPN data paths (the old snapshot check
  and the new week-by-week `mRoster` pull agree it's broken), not a computation bug. Checked all
  44 2014-2017 team-years for the same pattern; nothing else came back suspicious.

Final per-team-year totals for 2014-2017 are baked into `DRAFT_TOTALS_2014_2017` (replaced the
old raw per-player `SEASON_PTS_2014..2017` tables entirely — nothing else in the file referenced
them, confirmed by grep before removing). `draftRankings()`'s static-year branch is now a direct
lookup into that table instead of a runtime snapshot-based calculation.

## Session 2 (PC): full data + visual audit, Draft Rankings and manager grade rebuilt

### Draft Rankings ranked hoarding, not drafting — rebuilt (ADR 0004)
User's flag: Ermin's 2023 team went 5-9 and its draft still came out **2nd best all-time**. It
wasn't a one-off. The old metric summed every point every drafted player scored while on the
drafting roster, which measured three wrong things:
- **It paid for not touching the waiver wire.** Across the 96 team-drafts from 2018-2025 the raw
  total correlated **-0.41** with roster moves. Ermin 2023 made one move all year and carried two
  kickers and two defences week 1 → week 17 (467 pts), plus Stafford at 282.8 while starting
  three times. 1,054 of his 2,323.9 "draft points" never reached a starting lineup.
- **It rewarded bulk over usefulness** (a bench QB out-banked a starting RB2).
- **It couldn't compare eras** — 17 of the old bottom 20 rows were 2014-2017, an artefact of the
  rulebook, not bad drafting.

Now: **value over replacement** per skill pick (K/DST excluded, matching `SKILL`), prorated by
weeks held, measured against the same `replacementAt()`/`STARTS_BAR` line Steals & Busts uses;
then **z-scored within its own season** and shown as `100 + 15z`. Negatives are kept deliberately
— flooring at 0 re-introduces a churn signal. Five candidate bases were measured before choosing
(table in ADR 0004); VOR-with-negatives is the only one effectively neutral on roster moves
(+0.13) and it tracks wins best (+0.43 vs +0.29 for the old sum).

Result: Ermin 2023 → **37 / 138, score 109, 3rd of 12 that year** — right, given that team was
4th in the league in points scored and lost on schedule luck. 2014-2017 now hold 8 of the top 20
and 8 of the bottom 20 (was 2 and 17). Rows carry `basis: "por" | "total"` plus `score`, `z`,
`inSeason`, `of`; the old `seasonOnly` flag is gone (nothing outside the renderer read it).

**Still coarse:** 2014-2017 can't be measured against replacement — no week-by-week bench data in
this file — so they keep the raw whole-class totals as their value basis, labelled as such on
every row. Closing it means re-pulling per-*player* weekly box scores for those four seasons (the
same ESPN lift already scoped out once for K/D-ST) and baking per-pick rather than per-team.

### Data audit — the archive is clean
Wrote a reconciliation harness (loads the page's own JS in a Node VM with a DOM stub, so the real
functions can be re-run out of band). Checked and clean:
- **Weekly lineup data reconciles exactly with the standings.** For all 8 live seasons, summing
  each team's starters over the regular-season weeks equals its `SEASONS` points-for **to the
  cent**, every team, every year.
- **`ARCH.G` reconciles exactly with the standings too** — W/L/PF/PA per team per season, once
  `resultOf()`'s 2014 tiebreaks are applied (the two whole-number ties in 2014 are already
  handled correctly by `TIEBREAK_WINNER`; a naive check flags them as 4 mismatches, they aren't).
- 1,138 games is exactly right (counted from `ARCH.G`). 17 owners, 12 seasons: right.
- DRAFTS: no duplicate or missing overall picks, no player drafted twice in a year, no unknown
  positions, every drafting team present in both `SEASONS` and `ROSTERS`. The only uneven pick
  count is 2020 "All I Do Is Winn" at 15 — the known, documented missing slot.
- No player name resolves to two different ids **within the same season** (cross-season reuse is
  by design), so the name-keyed point sums can't silently merge two men.
- `OWNERS` covers every team name that ever appears; no team claimed by two owners.

### Visual audit — five real defects, all fixed (ADR 0005)
Measured computed foreground against the *composited* background (alpha tints resolved, gradient
stops taken at their darkest) for all 21,341 text-bearing elements, in both themes.
- **Draft Rankings tables were 1,478px wide for five columns** — they reused `.board`, which is
  fixed-sized for the twelve-round draft grid. Half a screen of sideways scroll on desktop, five
  screens on a phone. New `.drtable` modifier sizes to content: now 986px (fits) on desktop and
  330px on mobile.
- **The 1st/2nd/3rd medal chips took white ink on metal** — 1.67:1 (silver, light) to 3.77:1
  (gold). `--on-chip`'s dark-fill-in-light-mode premise doesn't hold for metal. New `--on-metal`.
- **`textOn()` had no sRGB gamma decode**, so it put white on five clubs' BYE chips that needed
  dark (Miami 3.95, Cincinnati/Denver 3.37, Carolina 4.03, Chargers 4.28). Now picks by real
  contrast ratio; all 32 clubs pass.
- **`--muted`/`--faint` sat under AA** — 3.79:1 at worst in light mode, across thousands of
  elements. Nudged in both themes.
- **Three prose links (`nflverse` ×2) had no colour rule** and rendered browser-default `#0000EE`,
  1.88:1 on dark. Added a base `a{color:var(--accent)}` floor.
- Translucent tints (`.sswk.flip`, `.ssflag`) now paint over `var(--surface)` so a tinted card
  keeps its own base instead of letting the panel behind show through.
- Copy fix: the full board's heading said "all 140"; it renders 138.
- **Both themes now measure zero AA failures.** Treat that as the standing bar.

Also checked and clean: no duplicate element ids, no `NaN`/`undefined`/`[object Object]` anywhere
in the rendered text, no heading-level skips, one `<h1>`, no images missing `alt`, no page-level
horizontal overflow at 1265px or 375px, no console errors.

**Standings overflow — traced properly and fixed.** First pass reported this as a general
`.stand` overflow; it isn't. Closed, every standings table is *exactly* its scroller's width.
The overflow only appears when a row's **DRAFT** disclosure is opened: those pick lines were
`white-space:nowrap` inside the OWNER cell, so they set that column's minimum and pushed the
table 16-49px past its scroller in 7 of the 12 seasons — which is what clipped MOVES. Three
changes, in order of what each buys:
- `.dpicks li` no longer forces `nowrap` (and the name gets `min-width:0`), so a long name wraps
  rather than widening the table. This alone takes worst-case overflow to **0** — it's the
  safety net that guarantees the table can always fit.
- `.stand` non-name cells go from 9px to 7px of side padding, returning ~48px to the OWNER
  column, so in practice **nothing has to wrap**: 0 wrapped lines out of 2,239 with every row in
  every season expanded at once.
- `.dpicks .dm` (the `WR Ind` badge) keeps `nowrap` so it can't split across lines, and `.do`'s
  left padding drops 10px → 6px. The now-redundant phone overrides for both were removed.

Verified across all 12 seasons in three states — all closed, one open, all twelve open —
overflow 0 in every case.

### Manager grade: every profile read "1st in points/game" — one-line bug, three fixes
Reported from a profile screenshot; the cause was a single mis-indexed sum in the league-average
points-per-game table:

```js
s.t.forEach(row => { if(row.length > 3){ pf += row[3]; g += row[0] + row[1]; } });
```

A season row is `[team, W, L, PF, PA, ...]`, so games is `row[1]+row[2]`. This added the team
**name** to the wins — string concatenation — so `pf/g` was `NaN` for every season, and the
`if(LG_PPG[s.y])` guard below treats `NaN` as falsy, so `relPf`/`relG` never accumulated for
anybody. Two consequences, one visible and one not:
- Every manager's era-relative points-per-game was identically **0**, and since ties share the
  best rank, every profile reported **"1st/12"** for scoring.
- SCORING is **19% of the manager grade**, so a fifth of every grade sat pinned at the 50th
  percentile — fully weighted, carrying zero information.

Fixed to `row[1]+row[2]`. League averages now compute and show the half-PPR step they exist to
cancel: **95.9 pts/game in 2020 → 107.4 in 2021**. Points-per-game ranks 1-12 with real spread,
and the era adjustment visibly works — a raw 103.8 ranks 5th, behind a 102.0, because those
seasons skew to the higher-scoring years.

**Two further defects found while auditing the grade, both fixed in the same commit:**
- `pfAxesForRow` drew its percentiles from all **17** owners while the grade ranked itself
  "Nth of **12**" and the bars beside it read `/12` — the same number reached against two
  different fields. `pfRankScope`'s own comment already claimed the bars used the field "the
  grade itself is drawn from"; they didn't. `pfAxesForRow(me)` now scopes through
  `pfRankScope`, so a graded manager is measured against the graded twelve and only an ungraded
  one falls back to the full roll. Worth up to 2.5 grade points; sharpest case sat at the 41st
  percentile for longevity against everyone and the **17th** against his actual field.
- `pfMetrics`' `rank()` used `indexOf` on a sorted array, returning `-1` (rank 0) for any value
  not found by exact identity. Replaced with the count-how-many-beat-you form `pfRankScope`
  already used, so the two agree by construction.

Net: the grade board's top 8 is unchanged; 9-12 reorder (Ermin 9th→12th, Braxton 12th→10th,
Alen 10th→9th). **Every** manager's rank bars change. Shipped as `dca48e1`.

## Session 3 (PC, 2026-08-12): judged-metric pass, then the overhaul begins

A `/grill-with-docs` session. The scope decided was two things: audit the logic behind
everything the site *judges*, then a complete visual and navigational overhaul. Audience was
pinned as **league members on phones, arriving from a group-chat link, ninety seconds of
attention** — that answer decided most of what follows. See ADRs 0006-0010 and `CONTEXT.md`.

### Vocabulary and scope, now written down
`CONTEXT.md` gained four entries: the **Archive tier** (analytics over the settled 2014-2025
record — two sessions of work had landed there with no bucket to put it in), the **soft freeze**
from ~Sept 3, **Franchise Grade**, and **judged metric** — the standard everything below was held
to. A judged metric must be *defensible*, *valid* and *transparent*, with **validity as the
gate**, and anything failing it gets demoted to a plain fact rather than deleted.

### The judged-metric pass — five surfaces, four defects
- **Franchise Grade** (ADR 0006, 0009). Renamed from "manager grade": the weighting always
  measured franchise achievement, and the old label invited an argument it couldn't win. Three
  axes dropped. `LONGEVITY` measured tenure (0.07 with win rate). `LINEUPS` was **noise** —
  intraclass correlation −0.002 across 1,374 graded manager-weeks, with between-manager variance
  *lower* than within-manager, and a 4,000-shuffle permutation test putting the real spread below
  chance median (p = 0.61) — and it carried 17% of the grade. `ACTIVITY` measured a genuinely
  stable trait (split-half 0.82) but a move rate is process, not achievement, and its 0.39 link to
  winning duplicates what `WINNING` measures directly. Four achievement axes remain: HARDWARE
  27.0%, SCORING 25.7%, POSTSEASON 24.3%, WINNING 23.0%.
- **Steals & Busts** (ADR 0008). `gain = posSlot − posFin` subtracted two ranks from different
  populations — drafted (~57 RBs) versus everyone rostered (~85). Le'Veon Bell was "RB4, finished
  RB82" in a year 56 RBs were drafted, and it put a torn preseason ACL (McKinnon, RB13) above
  Michael Thomas at **WR1**. Steals were provably unaffected and untouched.
- **Start & Sit** — the board passes and is unchanged; only its grade axis failed.
- **Trait badges** (ADR 0010). The worst defect of the session: "January Man · Wins in the
  bracket" was on **11 of 17 owners including one with a 0-for-career playoff record**, because
  `postPct` is not a percentage — it holds 0.5 per appearance plus 1 per win, per season,
  regressed. Now 4 of 17, all winning records. Badges now test the **raw** record with a
  minimum-seasons floor, and rank badges use one fixed field.
- **Scouting descriptors** — audited, pass unchanged on four axes.

### The overhaul, first three commits, all merged and live
Decided: dark-native app language, hub plus routed views, **all eighteen surfaces kept**, uniform
shell before bespoke depth, preserved URLs, single file and no build step retained, and the draft
cheat sheet **restyled only, never redesigned** — it is the one surface used under time pressure
on Sept 7 and it will never be rehearsed.
- **Uniform vocabulary** — `.uview/.uhead`, `.uhero`, `.ucard`, `.ustat`, `.uchip`, `.utable` +
  `.uwrap`, `.ugrid`, `.udisc`, all prefixed `u` because `.card`, `.stat` and `.chip` are taken.
  Zero raw hex, so ADR 0005's AA bar is inherited rather than re-argued. New tokens: `--t-hero`,
  a `--sp-1..6` spacing scale (the file had radius and type scales but none for spacing).
- **The hub** — eighteen doors in six groups, one tap each, on plain anchors because `openFor()`
  already opens a target's ancestors. Nav moved to the functional register (Season, Managers,
  History, Drafts, Records, Rules); section headings keep their editorial voice. A phase line
  counts down to the draft, then switches to last season's champion defending — deliberately not
  a standings snapshot, since live 2026 data doesn't exist in this file.
- **Routed views** — the six top-level sections are the six views, the hub is its own route, the
  masthead is hub-route decoration. Nothing moves in the DOM, so every URL ever pasted in the
  group chat still resolves.

### The uniform shell — four steps, all merged and live
The shell restyles the chrome all eighteen surfaces share rather than each surface's internals,
which is what makes eighteen surfaces affordable before the freeze. All four steps are scoped to
an *active routed view*, so with JS off the document is still the single scrolling page it was.

1. **A view presents as a screen, not an accordion.** A view holds exactly one top-level section,
   so that section's collapsible header is chrome with nothing to collapse into. The eyebrow,
   title and note are untouched; the chevron, hover fill, rounded summary and 56px sibling break
   go. Because the header can no longer be clicked, **the router forces the section open on
   reveal**, and a `toggle` guard reopens it if a keypress on the still-focusable `<summary>`
   shuts it. Also restored `.allctl` inside views — the routing commit had hidden Expand/Collapse
   all from the only place they mean anything.
2. **Each board reads as a titled panel** — `--raise`, `--r-md`, own hover and focus.
3. **Nested boards** (under Steals & Busts, Draft Rankings) trade their 2px left rail for a
   quieter panel: `--soft`, `--r-sm`. Indent 18px → 12px.
4. **`.subnav` loses its container and becomes chips.** It had been using `--raise` at `--r-md` —
   which step 2 had just given board panels — so content and navigation-to-content read at the
   same weight.

**Final weight ordering:** screen header (hairline) → board panel (`--raise`, 12px) → nested
panel (`--soft`, 8px) → navigation (no fill). `.allctl` was left alone; it was already in the
language.

**The one rule that governed every step: no shell change may take width from content.** Session 2
fixed standings overflow by returning ~48px to the OWNER column and those tables fit their
scrollers exactly, so panels went on headers only and never on bodies, and where padding changed
it changed *downward*. Verified each step: **twelve standings tables at 0px against their
scrollers**, page overflow 0 across all six views at 1887px and 375px, and AA clear in both
themes on every new surface pair (worst measured 5.23:1).

**Three things worth keeping in mind if this gets touched:**
1. **The router must run last.** Every draw function lays out and measures its tables while still
   visible; hide a section before layout and its tables measure zero and collapse on reveal.
   Verified: 14 tables at 1006px, none collapsed.
2. **The route click handler is on the capture phase**, so a view is revealed before the browser
   scrolls to the anchor.
3. **Routing degrades to nothing.** `body[data-route]` is the only CSS hook and only the router
   sets it, so with JS off the document is the single scrolling page it always was. Print has its
   own rule that ignores routing, or the PDF would be one screen of doors.

**Verification note.** All of the above was measured, not eyeballed — the Node VM harness for the
data and grade work, and a **published `preview.html` in a real browser** for anything visual.
That mattered: the back control measured **75×16px** on a 375px viewport, a third of the touch
minimum, and nothing in the markup or CSS looked wrong. `preview.html` is the ADR 0007 review
mechanism (Pages has no branch previews here) and is deleted in each merge commit.

## Still open
*Superseded by "WHERE THIS STANDS" at the top of this file, which is the current state. This list
is the longer history of each thread — kept for the detail, not as the to-do.* Carried forward
across sessions — the first four were queued when the original session paused to move machines;
the rest are from the PC session (2026-08-11/12):
- The 2020 Round 16 / Pick 8 mystery pick is effectively closed as "slot known (Revenge Tour's
  traded-away/orphaned pick), player unrecoverable from ESPN data" — revisit only if the user
  turns up a memory or record of who was actually drafted there.
- Draft-prep tools audit (see section above) is at a good stopping point, not exhaustively
  finished — everything checked so far is clean or fixed; revisit if something new surfaces.
- Draft Rankings' remaining precision gaps (2-pt conversions, K/D-ST still coarse for 2014-2017,
  a handful of ESPN-side missing athlete IDs) are all disclosed in the UI, not hidden — see above
  for exactly what's left if someone wants to push this further.
- The two corrupted end-of-season snapshots for 2014/2015 Beasts of the Middle East are worked
  around in `DRAFT_TOTALS_2014_2017` but not fixed in `ROSTERS.S` itself — if anything else ever
  reads those snapshots directly, the same bad data is still there.
- ~~Awaiting a decision on the two "context" axes in the manager grade.~~ **Decided and shipped
  2026-08-12 — ADR 0006.** `LONGEVITY` dropped (0.07 with win rate), `ACTIVITY` kept (0.39), and
  the grade renamed **Franchise Grade** because the weighting measures franchise achievement, not
  managing. Renormalisation is proportional and automatic — `pfGradeForAxes` divides by the weight
  sum, so the survivors were left untouched and now total 94 deliberately. Top five hold; five of
  twelve change rank. Also added `GRADE_SMALL_SAMPLE = 5`, which flags rather than penalises a
  short career and currently applies to nobody (graded field runs 8-12 seasons).
- **Pre-draft refresh is not yet due.** Both scripts dry-run clean as of 2026-08-12:
  `refresh-adp.py` (ESPN half-PPR id 8 re-verified at 0.5 pts/reception, 250/250 players, largest
  move 0.8 picks) and `refresh-tiers.py` (FantasyPros updated 8/12, 125/125 in-scope matched, one
  tier change: De'Von Achane 2→3). Nothing worth writing yet — re-run both within a few days of
  **Sept 7** when the market and expert consensus have actually moved.
- ~~**Standings scroll sideways on a tablet, and nothing is pinned when they do.**~~ **Fixed
  2026-08-12 — RK and OWNER are pinned.** See the section below; the write-up here is kept because
  the measurements behind the decision are worth having. Found 2026-08-12
  while verifying the two-column header; present on the live site, so it predates that change.
  Sessions 2 and 3 measured standings at 1887px and 375px and got 0 both times — the band between
  the phone card layout (≤760px) and a comfortable desktop was never checked. What is actually
  there, measured across it:
  - The division-era seasons (2019-2025) carry **13 columns** — `Div`, `Home`, `Away`, `Strk` on
    top of the nine every season has. At their min-content widths that table is **825px** and
    cannot shrink further. 2014-2018 have nine columns, fit, and are fine everywhere.
  - It misses its scroller by **146px at 768px** (9 of 12 tables) and by **14px at 900px** (7 of
    12). It fits from roughly **914px** up. `.tw` is `overflow-x:auto`, page overflow is 0 at every
    width, and the table really does scroll — so nothing is unreachable, and the 14px is cosmetic.
  - **The real defect is that neither `RK` nor `OWNER` is sticky**, so scrolling right to read
    Moves or Strk scrolls the owner names off screen. The archive already has this pattern:
    `.ledger th.l/td.l` pin left at `--sp` zero (line ~1007) and `.board td.rdc` pins the rank
    gutter (~1117). Standings — the most-read table on the site — is the one that doesn't.
  - **The phone override already assumes it.** Line ~2162 resets `.stand td.l` to
    `position:static` alongside `.ledger`'s, which only makes sense if `.stand td.l` were sticky
    above the breakpoint. It isn't. Someone expected this.
  - **Not a padding fix.** Session 2 already spent that budget going 9px → 7px; 12 non-name columns
    at 7px only hold 168px of padding total, and 146px of it cannot come back.
  - **Two ways to close it, and it is a design call, not a correctness one:** pin the OWNER column
    (watch the interaction — a sticky cell needs an opaque background, and `.stand tr.top1` is gold
    and rows tint on hover, so a flat `--surface` fill like `.ledger`'s would knock the champion
    row's first cell out of its own colour), or raise the card-layout breakpoint from 760px to
    ~914px so tablets get the phone treatment instead of a squeezed table. Worth asking which.
- **`CHEAT` and `DEPTH_TEAMS` still have no *refresh* script — but the cross-check is automated
  now.** The two refresh scripts keep prices and groupings current for players already on the
  sheet; neither will ever notice a player changed teams, got hurt, or should be added. That gap
  produced the stale A.J. Brown entry, and cross-checking `CHEAT` against `DEPTH_TEAMS` is what
  caught it. **`check-cheat.py`** (2026-08-12) is that pass written down — read-only, no network.
  Run it before draft night and after any hand-edit:

  ```bash
  python check-cheat.py --live
  ```

  It exits 1 on any ERROR. **`--live` (2026-08-15) is what changed here.** Without it the check can
  only tell you the file disagrees with itself — and it leans on `DEPTH_TEAMS` to do that, so a
  wrong bye *there* passes on every row. With it, all 309 rows have their club and bye checked
  against ESPN, which is the traded-player case automated rather than left to a human. What is
  **still** a human job is the part no roster feed exposes: whether a man is ranked where he should
  be. An injury reads as an ordinary row from either mode, and that still wants a live search
  rather than memory (training data confidently says PHI).

### Overhaul, remaining — in the order it should be done
The vocabulary, hub and router are merged and live. What's left, with the traps:
1. ~~Apply the uniform shell.~~ **Done — four steps, merged and live.** See the section above.
2. ~~**Bespoke depth:** hub, Manager Profiles, Standings.~~ **All three done 2026-08-12** — see the
   three sections above. Each turned out to be a structural defect rather than a restyle: doors
   sized by group population, a rail that stretched and stranded, a table that scrolled with
   nothing pinned. Draft Rankings was already off the list (rebuilt in ADR 0004) and so is the
   cheat sheet (restyle only).
3. ~~**Dark-default theme polarity** (Q18).~~ **Done 2026-08-12 — see the section below.** The
   sweep that gated it is checked in as **`contrast-sweep.js`**, with its four traps and the
   zero-failure baseline in its header; use it for anything that touches colour.
4. ~~**Deferred `PSTAT`/`ARCH` parse.**~~ **Don't. Measured 2026-08-12 and it is the wrong target.**
   ADR 0007's premise — 1.33MB parsed before first paint, the hub needs none of it — is true about
   bytes and wrong about cost. Instrumented copy of the real file (`performance.mark()` around each
   declaration and each `<script>` block, served locally, marks read from the page):
   - `const PSTAT = {…}`, 802KB of JSON: **5.0ms**. `const ARCH = {…}`, 495KB: **2.5ms**. Together
     **7.5ms**, about **1.6% of script time**. Engines parse object literals far faster than the
     size suggests; `JSON.parse` of the same payloads re-run in-page is ~7ms each.
   - The whole data block — `SEASONS` through `ROSTERS`, every table and lookup — is **83.7ms**.
   - **The first `<script>` block is 458.7ms of 461ms of total script time.** Every other block on
     the page is ≤1.3ms. Of that 458.7ms, ~375ms is the code *after* the data: the draw functions
     building all eighteen boards at load.

   So the ~7.5ms deferral was going to be bought with the single riskiest edit on the list — the
   821KB template-literal transform, the same shape of edit that once silently deleted ~2MB of this
   file. Not worth it. **The real target is the ~320ms of eager drawing** in that same block, on a
   route (the hub) that displays none of it. Numbers above are a 20-core desktop; a phone will be
   several times slower in absolute terms but the proportions are what matter.

5. ~~**Deferring the draw work.**~~ **Done 2026-08-12 — all of it.** Scoped first, then shipped in
   four commits: the trades/steals/records dependency chain, the rest of the IIFE boards, the bare
   `drawX()` calls, and the multi-line `innerHTML` assignments. **29 board functions across 17
   sections; 578ms → 258ms of script time**, ~55%. See the four sections below for the mechanism,
   the three hazards it hit, and the latent 2014/2015 bug it turned up. The scoping notes that
   follow are kept because they are still the right map of where the time was:

   The cost is real but it is *diffuse*, and the code is not shaped for a cheap fix. Per-span, from
   the same instrumented copy (marks at 25 top-level statement boundaries through the block):
   `~91ms` NFL schedule + draft rankings + scoring rulebook + **trades**, `~63ms` rosters/matchups
   setup, `~32ms` steals & busts + waivers, `~28ms` start & sit + grade cells, then a long tail of
   3-17ms spans. There is no single hotspot to lift out.

   **The blocker is that each board's IIFE both computes and renders, and some of them hand globals
   to boards further down.** Two confirmed, and their own comments say so:
   - `TRADE_DEALS` is assigned inside the trades IIFE (~line 8523) and read by the record book
     (~8922). Its declaration is commented "handed to the record book further down".
   - `HINDSIGHT` is assigned inside the steals/busts IIFE (~8796) and read by the record book
     (~8993-9013), with the same comment.

   So deferring a board is not "move the call later" — it is splitting compute from render for
   every board in the chain, or the record book renders against `[]` and `null` and silently loses
   rows. That is the whole reason this looks cheaper than it is.

   **The design that would work** — and what was actually built, minus the idle drain, which turned
   out to be unnecessary once the router, `beforeprint` and Expand-all covered every path: register
   each board in a `Map` keyed by section id and let the router draw the view it is revealing. The
   compute/render split proved unnecessary too; a board that hands globals downward simply pulls its
   own dependencies in (`records` calls `drawBoard("trades")` and `drawBoard("steals")`).

   **Two constraints not to trip over.** ADR 0007's note that "the router must run last, because a
   draw measures its tables while visible" applies to a *specific* few: the only layout reads in
   the whole block are at lines ~6739, ~7033, ~7408 and ~9116+ (`getBoundingClientRect`,
   `scrollWidth`/`clientWidth` for the swipe hints and scroll-spy). None of them are inside the
   heavy spans, so the expensive boards are safe to defer — but those four must stay eager or move
   to reveal-time, never to an idle drain while their view is `display:none`, or they measure zero.
   **On the payoff, which could not be measured from here and had to be asked for.** Neither browser
   available to a session reports `paint` entries — `document.visibilityState` is `hidden` in both
   the in-app pane and the CDP-driven Chrome tab — so First Contentful Paint is unmeasurable without
   help. Justin ran it in a normal window, and the answer **changed the recommendation**: FCP is
   **312ms** unthrottled and **420ms at 6x CPU**, i.e. never blocked, so ADR 0007's framing (and the
   first pass of this one) was aimed at the wrong metric. `domInteractive` is **697ms / 2,990ms** —
   ~2.6 seconds on a mid-range phone where the page is painted but the main thread is locked. That
   is what the refactor bought back. **If you need a paint number, ask for it; do not infer one.**
6. ~~**Copy gap:** owners falling back to `Journeyman · Still writing the story` alone.~~
   **Closed 2026-08-12 — `Bridesmaid · Lost the Alma Bowl`.** The handoff said four owners; it was
   **eight**, and they split cleanly: five are one- or two-season careers, for whom "still writing
   the story" is exactly right, and three were long careers with real near-misses — Tate Grainger
   (10 seasons, 0-3-0), Ermin Cerimovic (11, 0-2-0), Colin Moore (11, 0-1-2), between them six
   trips to the Alma Bowl and six losses. `Ringless` never reached them: it wants a .550 record and
   all three are sub-.500. Nothing in the set had any concept of a runner-up.

   Added as the **third branch of the hardware chain**, so a man with a ring can never be a
   bridesmaid by construction. Shipped first at `o.p[1] >= 1`, then **narrowed the same day to
   `o.p[1] >= 2`** on Justin's call, because at one final it also caught Alen Huseinbegovic (12
   seasons, 0-1-0), who already wore `Wire Hawk + Original` — a badge landing on a third of the
   league says less than one marking a specific kind of career.

   It is now **Tate Grainger** (0-3-0) and **Ermin Cerimovic** (0-2-0), and since every holder has
   two or more, the descriptor went back to the plural it was drafted with: **`Bridesmaid · Alma
   Bowls, no rings`**.

   **Colin Moore then got his own branch rather than a widened one.** Narrowing Bridesmaid dropped
   him back to `Journeyman`, and the tempting fix — `o.p[1] + o.p[2] >= 2` on the Bridesmaid branch
   — was declined: a bridesmaid is the *runner-up*, and Colin has been to one Alma Bowl and finished
   third twice, so both the name and the plural descriptor would have been false for him, and both
   would have had to be softened for everyone to accommodate him. His is a different fact, so it is
   a **fourth branch**: `else if(o.p[1] + o.p[2] >= 2)` → **`Contender · Podiums, never a ring`**
   (Justin's copy). Two podiums is the floor, so the plural is always true of whoever wears it, and
   silver and bronze count alike on purpose — the badge is about being repeatedly in the reckoning.

   **The hardware chain is now four branches and strictly exclusive**, verified: Dynasty → Champion
   → Bridesmaid → Contender, nobody holding two, everyone holding at least one badge overall. Tate
   and Ermin never reach the fourth branch because the third claims them. `Journeyman · Still
   writing the story` now sits **only on the five one- and two-season careers**, which is precisely
   the reading it was written for.

**Open design questions, not yet put to the user:** whether landing deep inside a long routed view
is acceptable (`#h2h` lands ~16,000px down the History view — correct, but a long scroll), and
whether "← All boards" is the right label and placement for the way home.

### The visual pass (same session, after a user screenshot)
The shell was structure. Colours and fonts were still the old system, because every shell step
deliberately reused existing tokens so ADR 0005's contrast bar could not break. A user screenshot
made that obvious, and also caught a defect four shell steps had been built on top of.

**The bug: hub doors rendered title and sub-line inline** ("Draft NightMonday, September 7").
`a.ucard{display:block}` and the door rule are BOTH 0-1-1, so source order decided, and the hub
rules sit above `.ucard` in that block. The first fix (`a.uhubdoor`) changed nothing for exactly
that reason; `a.ucard.uhubdoor` (0-2-1) wins wherever it sits. **The hub shipped with eighteen
doors verified for target resolution, tap depth, heading order, overflow at two widths and touch
targets — none of which can see a collapsed layout.**

**What changed, and why:**
- **Door titles Oswald -> Inter** at `--t-body`. Oswald is condensed display type: it carries the
  masthead at 90px and reads cramped at card size. It is fine from ~25px up, so view headers
  (30px) and board headers (25px) keep it — the earlier claim that Oswald was "arguing with
  itself" was wrong and was retracted.
- **Door fill `--surface` -> `--raise`.** On the dark ground `--surface` (#121828) sits a few
  points off `--bg` (#0B0F1C), so eighteen cards read as faint outlines.
- **Three colours, three jobs: mint = interaction, gold = editorial voice, neutral = structure.**
  `--accent` had been marking links, hover, focus AND every eyebrow, chip label and rule, so it
  signalled nothing. Eyebrows moved off accent — then off `--muted` too, because fully monochrome
  is wrong for a league trophy case — and onto `--gold-text`, which is also the masthead's italic
  FFL. Measured: 9.15/11.18 dark, 5.23/5.51 light.
- **Hub group labels** `--t-micro`/`--muted` -> `--t-fine`/`--body`; they had been quieter than the
  sub-lines inside the cards they labelled.
- **Board disclosure chevrons** moved back beside their headings (~1155px -> ~905px); the header
  text block was `flex:1` and shoved them to the panel edge.

**Still open on the visual side:**
1. ~~**Panel text stops at ~620px inside a 1177px panel**, so every board has an empty right half.~~
   **Done — the board header is two columns.** See the section below.
2. **Dark-default polarity flip is now LAST, not next.** The user already views in dark, so the
   flip only changes what a first-time visitor gets — lowest visual payoff of anything left, and
   the highest AA risk. Do it with the full 21,341-element sweep, not spot probes.
3. Bespoke depth (hub, Manager Profiles, Standings) is untouched.

### The two-column board header (2026-08-12, same session)
The empty right half is closed. A board panel runs the full width of its view because the tables
inside need it; the header only ever filled the left 647px of 1040, because `.subnote` is capped at
76ch and the eyebrow, heading and note stack. Sixteen boards therefore opened with half a panel of
nothing, and the chevron sat in the middle of it.

The header is now a three-track grid — title block, note, chevron — applied at `min-width:900px`
only, so the phone keeps the stacked header it already had. **No markup changed:** all sixteen
top-level headers and all nine nested ones are `div > (eyebrow) + heading + note`, so
`display:contents` on that div promotes the three children into the summary's own grid. The nested
boards under Steals & Busts and Draft Rankings get the same treatment and the same rule.

**Two things worth knowing if this gets touched:**
- **The chevron went back to the trailing edge, and that is not a reversal of `5651d12`.** That
  commit fixed a control stranded ~500px out in blank panel. There is no blank panel now — the
  chevron sits against the note it follows, and all twenty-five land on one vertical line.
- **A spanning grid item grows every row it spans, and that was a real defect, caught by
  measuring.** The note spans both rows, so a tall note grew both, and the extra height landed
  *between the eyebrow and the heading*: 4px on a two-line note, 12px on three, 33px on Matchups'
  six, and a nested heading pushed 82px down its own panel — the title block visibly loosening as
  the note beside it got longer. `grid-template-rows:min-content 1fr` plus `align-self:start` on the
  heading pins row 1 to the eyebrow and lets the `1fr` row absorb the excess. Gap is now a constant
  4px on all twenty-five headers at every width tested. This was invisible in a screenshot until you
  knew to look, and invisible in the source entirely.

**Verified on the real file** (served over `python -m http.server` and loaded in a browser — see the
working note below), at 375 / 900 / 1265 / 2048px, across all six views, both themes:
- Page overflow **0** at every width, in every view.
- Standings tables **0px** against their scrollers at 1265 and 2048 — the "no shell change may take
  width from content" rule holds. This touches the summary only.
- All 25 headers: zero clipped, zero notes overflowing the panel, zero title/note overlap, chevron
  1px inside the padding edge, eyebrow-to-heading a constant 4px.
- Note measure 537px (~80 characters) at the wrap's full 1040px, 425px at a 900px viewport. The
  1 : 1.35 column ratio is chosen for exactly that — handing the note every leftover pixel would
  run the line past 100 characters.
- Contrast unchanged, because no colour or background changed: worst pair is the gold eyebrow in
  light mode at **5.23:1**, the same figure ADR 0005 recorded for it.
- Below 900px the rule does not apply at all — headers measure `display:flex`, exactly as before.

**One pre-existing defect found, not fixed, not caused by this:** at a **900px viewport** the 2025
standings table overflows its scroller by **14px** (15px at 899). Confirmed present on the live site
at the same width before this change, so it predates it. Sessions 2 and 3 verified standings at 1887
and 375px, which is why it was never seen — the breakpoint band between the phone overrides and the
desktop layout was never measured.

### The hub: a door is a door (2026-08-12, same session)
First pass at bespoke depth, and it turned out to be one defect rather than a redesign. `.ugrid`
uses `repeat(auto-fit, …)`, which collapses the empty tracks in a short row and hands their width
to whatever is in it. On the hub that made **a door's size an accident of how many siblings its
group had**: Season's two doors came out **514px** each, Managers' and History's four at **251px**,
and Record Book and Rules — one board of eighteen each — ran the **full 1040px**, 4.1x the width of
the Standings door one group above. Size was reading as importance and encoding nothing but group
population.

`auto-fill` keeps the empty tracks. All eighteen doors are now one 251px field, four across, with
groups as labels over that field and a short group ending in honest empty space. Scoped to
`.uhub .ugrid` rather than changed at source — `.ugrid` is general vocabulary and the hub is its
only user today, so the next thing to use it can still want auto-fit's stretch.

Verified at 375 / 768 / 1265px: eighteen doors, **one width and one height at every viewport**
(351x62 on phone and tablet, 251x62 on desktop), columns landing on 1 / 2 / 4 tracks, page overflow
0, every door over the 44px touch minimum. No colour changed.

**Not done, and deliberately not:** no live figures on the doors. That is the obvious next idea —
Champions showing the current holder, Records showing the high score — and it would make the hub
need `PSTAT`/`ARCH`, which is exactly the 1.33MB parse item 4 below wants to defer *because the hub
needs none of it*. Decide the deferral first; the doors can be fed afterwards.

### Manager Profiles: the rail travels, and the sparklines meet their axis (2026-08-12)
Second bespoke-depth surface. Two defects, both structural, both found by looking at the open
profile rather than at the code.

**The career rail stretched and stranded.** `.pfbody` is a 300px + 1fr grid. The left column holds
six career figures and four rank bars — 660px of content — and the right holds everything you
scroll: breakdown, twelve season rows, three charts, sixteen rivalries, draft history. As a plain
grid column the rail stretched to match, so the worst profile carried **1,689px of empty raised
panel**, and the figures you want beside a season row were a screen and a half above it.
`align-self:start` sizes the rail to its content — that alone kills the empty column, at any window
height. `position:sticky` then keeps it beside whatever you scrolled to, **gated on the window
being tall enough to show all of it**: `.pfcard` is capped at `calc(100vh - 68px)`, the rail runs
633-660px across all seventeen managers (measured, every one), so the gate is `min-height:760px` —
a 692px scrollport against a 660px rail. Short window: no pinning, but still no dead column. Below
861px `.pfbody` is one column and neither rule applies.

**The trend sparklines were drawing at half their own width.** The SVG is `width="100%"
height="56"` over a `0 0 260 56` viewBox, and the default `preserveAspectRatio` is `meet` — it fits
*both* axes, so in a 521px box the height bound it and the chart drew 260px wide, centred. The axis
labels underneath are a flex row and did span the full 521px, so twelve seasons of shape sat
squeezed into the middle half of their own axis. `aspect-ratio:260/56` with `height:auto` scales the
drawing uniformly to whatever column it is in: 521x112 on desktop, 295x64 on a phone, chart and
labels the same width at both, markers still circles because nothing is stretched on one axis only.
Profiles get ~160px taller; the charts became readable.

Verified at 375x812, 1265x700 and 1265x900: rail sticky only where it fits, chart width equal to
label width at every size, no page or card overflow, phone layout unchanged.

**Still open on this surface** (not attempted, in rough order of payoff): the hero's three-column
`1fr auto 1.15fr` leaves a gap between the avatar and the radar; the Franchise Grade — the number
the whole modal is about — sits under the radar at small size; and `Roster moves` still shows as a
ranked bar although ADR 0009 dropped ACTIVITY from the grade, which is defensible under the
"demote to a plain fact" rule but is worth a deliberate look rather than an assumption.

### Standings: rank and owner stay put (2026-08-12)
The tablet defect above, closed by **pinning rather than moving the breakpoint**. Raising the card
breakpoint to ~914px would have swept the five nine-column seasons (2014-2018) — which fit that band
perfectly well as tables — into the phone card layout along with the seven that don't. Pinning fixes
the actual complaint (a row goes anonymous when you scroll to its Strk), helps at every width where
a table scrolls rather than only in one band, and uses two patterns the file already has: `.ledger`
pins its name column, `.board` pins its round gutter at a fixed 38px.

**The trap, and it is worth knowing before pinning any two adjacent columns:** OWNER needs an offset
to stick at, and `width` alone does not give a stable one. Under `table-layout:auto` a squeezed table
ignores the declared width and falls back to the column's min-content — which is *precisely* the case
that scrolls. Measured with `width:44px`, the seven thirteen-column tables rendered RK at **40px** and
left a **4px transparent sliver** between the two pinned columns for the numbers to scroll through.
The fix is `--rankw` for both the width and the offset, plus `min-width` — which a table cell *does*
honour — to raise min-content to match. 40px is deliberately the value a squeezed table already lands
on, so no thirteen-column season is a pixel wider; the roomier nine-column ones hand 4-19px of gutter
slack back to the columns carrying numbers.

**Two pre-existing defects surfaced on the way and are fixed in the same commit:**
- **The OWNER header had no `.l` class.** `th("who","Owner",false)` fell down the non-sortable branch
  and emitted `<th class="">`, while every cell beneath it is `td.l`. So the header sat right-aligned
  over a column of left-aligned names, took the 7px numeric padding instead of its column's 9px, and
  could not be pinned with its own column. The `.replace()` chained onto that call was dead — it
  rewrote a `data-key` the non-sortable branch never emits.
- **The seed band scrolled away.** "Winner's bracket · seeds 1-6" is a transparent cell spanning the
  whole table, so pinning the *cell* would drag an unpainted box across the columns. The **label**
  inside it is pinned instead — safe, because nothing scrolls underneath a divider row — and it needs
  `width:max-content` or a block filling the cell has no room to slide.

Verified across all twelve seasons at 375 / 768 / 1265px: rank gutter a uniform 40px, seam 0 both
pinned and unpinned, header cells landing on exactly the same offsets as the body cells, page overflow
0 in all six views, and **every table still exactly its scroller's width at 1265** — the session-2
invariant holds. The phone is untouched: every cell computes `static`, no shadow, card layout intact.

**One thing found, tried, measured and rejected — the champion row's gold.**
`.stand tr.top1{background:var(--gold-soft)}` and its `:hover` pair are **dead on desktop**: `tbody td`
paints every cell (`--surface`, `--raise` on an even row, `--accent-soft` on hover) and a cell
background covers a row background, so the gold has only ever shown in the phone card layout, where
those cells go transparent. The obvious two-line fix is to paint the cells instead
(`.stand tr.top1 td{…}`, which does win at (0,2,2) against the stripe's (0,1,3)) — **it was written,
measured against the live build, and reverted.** 1265px, dark, composited backgrounds:

| | live | with the gold fill | AA needs |
|---|---|---|---|
| `td.dim` / `td.grp` / `.divsub` / `.dm` / `.do` | 4.58 | **2.89** | 4.5 |
| `.team` | 5.48 | **3.46** | 4.5 |
| `td.neg` | 5.16 | **3.26** | 4.5 |
| `.tag` | 6.41 | **4.25** | 4.5 |
| failing elements in champion rows | 0 | **467** | 0 |

A 14% tint lightens the dark ground enough to sink every muted and faint figure in the row. ADR 0005's
floor is the standing bar, so the fill loses; the reasoning is now a comment at the rule so nobody
"fixes" it again. The row needs nothing anyway — it is already marked twice, gold rank chip and ALMA
BOWL CHAMPION badge. **If a third marker is ever wanted it must not touch the background** — an edge
or a border, not a fill.

(Two measuring notes worth keeping. The sweep must assert its own viewport: the first run of this
looked like a no-op because the pane was still at 375px from an earlier check, where the phone layout
makes the whole question moot. And `span.rk`, the medal chip, reads 1.09-1.96 in *both* builds — that
is the compositor in the harness, not a real failure: the chip is painted with a gradient, and
`backgroundColor` reports transparent for those, so the walk lands on the wrong ancestor. ADR 0005
tuned that chip deliberately with `--on-metal`.)

### The contrast bar, re-measured — and the phone was failing (2026-08-12)
ADR 0005's floor ("both themes measure zero AA failures — treat that as the standing bar") had never
been re-run since it was set, and the sweep that set it wasn't kept. Rebuilt it as
**`contrast-sweep.js`**, checked into the repo root, and ran it across all seven routes at
{375, 1265}px x {dark, light}. It found a real regression-class defect on the first honest run:

**396 failing elements at 375px in dark, all in champion rows, all pre-existing.** `.divsub` (the
division label) and the two draft-pick badges `.dm`/`.do` measured **3.93 against a 4.5
requirement**. Cause: `.stand tr.top1`'s gold is a 14% tint that — unlike on desktop, where the cell
backgrounds paint over it — actually *renders* on a phone, lifting the card's ground from `#121828`
to about `rgb(49,46,45)`. `--faint` was tuned against the darker one. Confirmed on the **live** build
before touching anything, so it predates this session. Fixed by lifting exactly those three to
`--muted` inside a champion row, in the phone media query only: 4.7 on the tinted ground, the same
figure the team name beside them already passes at. Desktop is untouched, pixel for pixel.

**This is the same tint that was rejected for desktop earlier the same day** — there it would have
sunk 467 elements. Worth stating plainly: the gold row fill is a contrast liability wherever it
renders, and it is only tolerable on the phone because three selectors were lifted to clear it.

**Baseline now, and the number to hold:**

| | checked | failures |
|---|---|---|
| 1265px dark | 59,753 | **0** |
| 1265px light | 59,753 | **0** |
| 375px dark | 59,501 | **0** (was 396) |
| 375px light | 59,501 | **0** |

**Why the original pass missed it, and what that means for the dark-default flip:** ADR 0005 counted
21,341 elements — almost exactly what this harness counts at *desktop width on a single pass*
(21,545). The phone layout is a different population, not a narrower one, and a second pass measures
~59k because each pass expands the disclosures inside the view it sweeps. So the flip's contrast
sweep must be run at **both widths** and **twice per width**, or it will certify a bar it never
tested. The four traps that each produced a wrong answer while building this — viewport assertion,
the two-pass population, Chrome's `color(srgb …)` syntax parsing as near-black, and gradient-painted
elements being uncompositable — are all documented in the file's header.

### Dark is the default now (2026-08-12) — the last overhaul item, ADR 0011
Q18's decision, shipped. The dark palette used to live inside
`@media (prefers-color-scheme:dark)`, so the archive was a light document that went dark for readers
whose OS asked. It is now `:root:not([data-theme="light"])` with no media query: **at every OS
setting the archive opens dark, and the toggle is what changes it.** The choice still persists in
localStorage and is still applied by the no-flash script in `<head>`.

Three things this touched, and the second one is the one that would have bitten:
- The **palette block** loses its media-query wrapper. Specificity is unchanged at (0,2,0) — a media
  query adds none — so the print block's `:root:root`, which forces paper-and-ink for a dark reader's
  printout, still wins on source order exactly as before.
- **`resolved()` in the toggle had to change with it.** It answered with the OS preference, which was
  right while the palette followed the OS. Left alone, a reader on a light-mode phone would have
  looked at a dark page, clicked once to set `data-theme="dark"` — changing nothing they could see —
  and had to click again. It now answers "dark" for "no explicit choice yet", matching the
  stylesheet. Verified with the OS emulated to light: page opens dark, **one** click reaches light,
  a second returns to dark, and the aria-label and sun/moon icon track the page rather than the OS.
- The **toggle icon rules** lose the same wrapper, so the icon shows the state the page is in.

**Verified with `contrast-sweep.js`, all four combinations, fully expanded populations:**

| | checked | failures |
|---|---|---|
| 1265px dark | 59,753 | 0 |
| 1265px light | 59,753 | 0 |
| 375px dark | 59,501 | 0 |
| 375px light | 59,501 | 0 |

**One measurement note if you re-run it:** a sweep taken straight after opening the disclosures counts
~21.5k elements, not ~59.5k. The Matchups board renders each boxscore from a `toggle` handler, so the
big population only exists once those handlers have run — reveal every view, open every `<details>`,
then sweep in a *separate* call. The 21.5k number is not wrong, it is just a much smaller population
than the one this bar was set against, and it is almost exactly what ADR 0005 counted (21,341).

**Not done, deliberately:** no `color-scheme` property was declared. Adding
`:root{color-scheme:dark}` would make the UA paint scrollbars, form controls and the search caret
dark to match, which is a real improvement — but it also changes native control rendering, so it
wants its own look and its own sweep rather than riding along with the polarity change.

### The cheat-sheet cross-check, automated — and what it found (2026-08-12)
`check-cheat.py` is the manual `CHEAT`-vs-`DEPTH_TEAMS` pass, written down. It checks the 32-team
shape and bye ranges, `CHEAT`'s position-rank sequences, duplicate names and overall ranks, null
overall ranks (the value/reach threshold coerces a null to 0 in JS and calls every pick a value),
team abbreviations against `NFL_LOGO`, each player's bye against his own listed team's, duplicate
`ESPN_VERIFIED` ids — and, the reason it exists, **every name that appears in both files, for
team and bye agreement.** Verified against the real bug: re-inject A.J. Brown's stale `PHI`/bye 10
into a scratch copy and it errors and exits 1.

**It found a live defect on its first calibrated run.** `ADP_2026` held **`"Tre' Harris"`** while
the sheet, the depth chart and `ESPN_VERIFIED` all say **`"Tre Harris"`**. The page looks up
`ADP_2026[name]` with the sheet's spelling, so that receiver had **no market price and no
value/reach tag**, and nothing on the page said so.

**The sheet is not the one that is wrong.** ESPN writes `Tre' Harris`; NFL.com, the Chargers
themselves and Pro-Football-Reference — where this site's player links point — all write
`Tre Harris`. It is a join problem, not a spelling problem, so the fix went into the join:
- `refresh-adp.py` keyed the table straight off ESPN's `fullName`. It now re-keys to the sheet's
  spelling wherever the two differ only by punctuation or a suffix, and **prints every re-key** so
  it lands in the run output and the diff instead of being silent.
- **Both normalisers now DROP apostrophes rather than folding curly to straight.** That was the
  actual hole: `refresh-tiers.py` has matched exact-then-normalised since it was written, but
  `Tre' Harris` and `Tre Harris` stayed different keys under it, because sources disagree about
  whether the name carries an apostrophe *at all*. Same rules both scripts now.
- The one live key in `index.html` was renamed by hand so the tag works today rather than at the
  September refresh. Both scripts dry-run clean afterwards: ADP reports the single re-key,
  tiers still matches 125/125.

**A note on calibrating a checker.** The first version emitted 27 warnings, all of them expected
scope, and a tool that cries wolf on its first run gets ignored. The heuristic that produced most
of them — "his overall rank is inside 250, so a 250-entry ADP table should have him" — is simply
wrong: those 250 are the top 250 *by draft-room position*, a different population from the sheet's
top 250 by expert rank. What survives is the signal that matters: a near-match (difflib at 0.86)
between a name one table has and a name the other nearly has. It now reports **0 errors, 0
warnings, 11 notes**, and every note is a real statement about scope rather than a shrug.

### Boards draw on reveal — the first three (2026-08-12)
**Justin ran the measurement I could not.** On a real, visible browser: first paint at **312ms**
unthrottled and **420ms at 6x CPU** — it was never blocked, so ADR 0007's framing (and mine) was
aimed at the wrong metric. `domInteractive` is **697ms** unthrottled and **2,990ms at 6x**. That is
~2.6 seconds on a mid-range phone where the page is painted but the main thread is locked: no
toggle, no search, no countdown, no router. Nearly all of it is eighteen boards being built at load,
on the hub route, which shows none of them.

`LAZY_BOARDS` lets a board register instead of drawing, and the router draws what the view it is
revealing contains — **after** the reveal, which satisfies ADR 0007's "a draw measures its tables
while visible" by construction rather than by luck.

**Three are converted, and they are deliberately the ones that could not be done piecemeal:**
`trades` (writes `TRADE_DEALS`), `steals` (writes `HINDSIGHT`), and `records`, which reads both and
renders against `[]` and `null` without them — losing rows silently rather than failing. `records`
therefore calls `drawBoard("trades")` and `drawBoard("steals")` itself, so the chain runs in order
whichever door the reader opens first.

**Two things need boards without revealing a view, and both are wired:** `beforeprint` (a PDF holds
every section, drawn or not) and Expand all (which would otherwise open an empty panel). **Search
needs nothing** — it indexes `OWNERS` and a fixed section list, not board DOM, and its results
navigate by hash through the router.

**Proof it changes nothing.** Rendered `innerHTML` length and hash for `trlist`, `trsum` and
`recordcards`, plus `TRADE_DEALS.length` and the `HINDSIGHT` counts, captured from the live
pre-refactor build and compared against the new one down three separate entry paths:

| path | trlist | recordcards | TRADE_DEALS | HINDSIGHT |
|---|---|---|---|---|
| live build (baseline) | 67831 / −1250439290 | 773998 / −2010759261 | 42 | 569 / 755 |
| open `#records` first (the hard case) | identical | identical | 42 | identical |
| `#building` then `#records` | identical | identical | 42 | identical |
| `beforeprint` from the hub | identical | identical | 42 | identical |

Expand all also drains the map, and `afterprint` restores the disclosure state.

**The saving, measured honestly:** `domInteractive − responseEnd` over two loads each, same pane —
**before 526 / 481ms, after 403 / 421ms**, so roughly **90ms** (range 60–123). Noisy, two samples,
in a hidden pane. Scaled by the 6x ratio Justin's numbers imply (~9x observed), that is around
**0.8s** off a phone's locked-main-thread window, from three of eighteen boards.

**To convert another board:** `(function(){` → `lazyBoard("<section id>", function(){`, its closing
`})();` → `});`, and check what globals its body writes that anything below it reads. Nothing else
is needed — the router, print and Expand all triggers are generic. The four layout-reading sites
(~6739, ~7033, ~7408, ~9116+ in the pre-refactor numbering: swipe hints and scroll-spy) are the
ones that must NOT be converted without moving to reveal-time, or they measure a hidden view and
get zero.

### The rest of the IIFE boards, and where the time actually is (2026-08-12)
Seven more converted: `matchups` (the stat key), `awards`, `rules` (rule changes **and** the scoring
rulebook — two registrations under one key), `records` (the base board, which registers *before* the
cards pushed into it), `nflsched`, `draftranks`. Ten registrations across eight sections now.

**Three of them changed the mechanism or were deliberately left alone:**
- `lazyBoard` now holds a **list per section**, not one function. `#rules` has two boards and
  `#records` has two, and the second `set()` was silently discarding the first. The list runs in
  registration order, which is load-bearing exactly once: the record book's `paintBook` is assigned
  by the first block registered under `records` and *called* by the second.
- **The mechanism had to move to the top of the script.** It was defined at ~8253, below boards that
  now register at ~5030. `lazyBoard` is a hoisted function declaration so the call resolves, but
  `LAZY_BOARDS` is a `const` — a registration above its definition hits the temporal dead zone and
  throws. It now sits immediately after the `ROSTERS` alias, above every registration.
- **The draft cheat sheet (`drpanel`/`drtabs`, in `#draft2026`) stays eager, deliberately.** It is
  the one surface used under time pressure on Sept 7 and never rehearsed; its span is ~17ms. Wrong
  trade. The hub hero (`herocount`, which sits outside every section) and the swipe hints and
  scroll-spy (the layout readers) stay eager for the reasons above.

**Verified byte-identical** — 14 containers by length and hash, plus `TRADE_DEALS` and the
`HINDSIGHT` counts, against the fully-drawn live build, down three paths: force-draw-everything,
a cold deep link straight to `#records` (which pulls its base board, its pushed-in cards and two
boards from another view), and revealing all six views in order. Identical every time, and the
pending list drains exactly as each view opens.

**The saving, and the honest disappointment:** median `domInteractive − responseEnd` over two loads
each — **fully eager 488/499ms, all ten deferred 396/406ms**, so **~93ms** total. But the first
three boards were already worth ~90ms of that: **these seven added only ~11ms.** They are simply
cheap. Worth keeping — they no longer run on the hub, and the architecture is what makes the next
part possible — but nobody should expect a second 90ms from converting IIFEs.

**Where the remaining ~340ms actually is.** Re-instrumented the converted build, anchors every third
top-level statement:

| span | ms | what lives there |
|---|---|---|
| A4803→A5013 | **69.4** | rosters + matchups setup |
| A3833→A3963 | **55.1** | the ledger / owners tables |
| A4174→A4429 | **53.8** | id maps, then the ledger draw |
| A6805→A6836 | **44.5** | start & sit + grade cells |

None of it is an IIFE. It is the **bare top-level calls** — `drawOwnerLedger()`, `drawMatchups()`,
`drawRoster()`, `drawStartSit()`, `fillGradeCells()`, `drawAllPlay()`, `drawH2Detail()`, the
`#seasonlist` innerHTML assignment — plus the shared structures they build.

**That batch is a different risk class and should not be done the same way.** Those functions are
also called from event handlers (year pickers, sort headers), so only the *initial* call can be
deferred, not the function. And at least one is reachable without a view reveal at all:
`fillGradeCells()` feeds the profile overlay, which opens from the Awards Wall **and from search**,
so deferring it to `#people` would leave a profile opened from a search result with empty grade
cells. Any conversion there needs `pfOpen` as a trigger alongside the router.

### The last batch — the bare draw calls (2026-08-12)
Done. Ten more registrations, **20 board functions across 15 sections**. Only the *initial* call
moved; every function stays where it was, because the year pickers and sort headers call them again.

**Three hazards, all real, all found before shipping:**
- **`fillGradeCells()` is not a drawing function.** Its first line is `PFM = null; PFGRADE = null;`
  — it clears the memoised metrics so they recompute *now that lineup data has been parsed*. Defer
  it to `#managers` and never reveal that view, and every profile renders from the pre-lineup pass.
  Profiles open from **search**, so `pfOpen()` now calls `drawBoard("managers")` first. Verified
  cold from the hub with 15 sections pending: `pfMetrics()` returns Tate 0.95 / Ryan 1.05 / Colin
  1.00 / Michael 1.02, matching the live build exactly, and the grade renders 73.4, 7th of 12.
- **A hash can point INSIDE a board.** `#y2019` is a season card, and those only exist once the
  standings have drawn — `viewFor()` would have returned null and stranded a pasted deep link on
  the hub. It now draws everything and asks once more on a miss. Insurance rather than a hot path
  today, since the `innerHTML` assignments (standings, `myears`, `h2table`) were left eager, but it
  is what makes deferring those safe later.
- **The temporal dead zone, again, from the other side.** Deferring calls at ~3961 put registrations
  *above* the mechanism at ~4252 and the page died on load: `lazyBoard` is a hoisted function
  declaration so the call resolves, but `LAZY_BOARDS` is a `const`. It now sits at the very top of
  the script block, above everything. **Any future registration must stay below it.**

The `goto*` helpers needed nothing: `gotoMatchups()` sets `mY` and calls `drawMatchups()` directly
rather than relying on the initial draw, so a deep-linked filtered view self-heals.

**Verified byte-identical across all 21 board sections** — length and hash of each `<section>`'s
innerHTML, local against the fully-drawn live build. Twenty-one of twenty-one match. `#ahead` looked
like a mismatch at identical length; it is the draft countdown ticking inside it, proven by removing
`#dncount`/`#dnorder`/`#dnfacts` from a clone, after which both sides hash to `217974:1562397888`.
Print drains all fifteen and restores the disclosure state; no console errors anywhere.

**The saving:** `domInteractive − responseEnd`, paired loads — **fully eager 558/600ms, final
376/312ms**, about **235ms**, ~40% of script time. Against the 6x-CPU ratio Justin measured (~9x),
that is roughly **2.1 seconds** off the window where a phone is painted but frozen.

**What is still eager, and why:** the draft cheat sheet (used under time pressure on Sept 7, never
rehearsed, ~17ms — wrong trade), the hub hero and figures strip (outside every section), and the
swipe hints and scroll-spy (they read layout and would measure a hidden view as zero).

### The `innerHTML` assignments — and a latent bug they were hiding (2026-08-12)
The last ~50ms. Nine assignments wrapped — `champboard`, `draftyears`, `yearnav`, `seasonlist`,
`myears`, `h2table`, `h2pick`, the record book's first pass, `apyears` — plus `rosteryears` folded
into the existing `rosters` registration. **29 board functions across 17 sections.**

**Container-level `addEventListener` calls did not need moving.** They bind to elements in the
static markup and catch children added later, so they stay eager and keep working.

**Two statements did, and one of them took the page down.** Both operate on the produced DOM
*without naming its container*, so a scan for the container's id does not find them:
- `document.querySelectorAll("#rosteryears button")` — sets the selected-season highlight on
  buttons the assignment above it writes. Folded in, with `rY = R_YEARS[0]` left eager because it
  is state other code reads.
- **`SEASONS.forEach(s => drawSeasonBody(s.y))`** — the standings markup only creates each season's
  *empty* `<tbody>`; this fills them. Left outside the wrap it threw `Cannot set properties of null`
  and killed the rest of the script: five registrations instead of twenty-nine, and most of the
  archive blank. **This is the shape to look for when deferring anything else.**

**And then the section hashes did not match — for a good reason.** Everything was byte-identical
except `#seasons`, which came out **844 characters larger**: 2014 and 2015 only, **422 each**, one
extra `td.grp` per row. Both builds were internally consistent (header count == body count), so
nothing was misaligned — the two seasons had simply **gained a `Post` column they never had**.

`seasonRows()` decides that column from `meta.hasPost`, and running eagerly it was reading playoff
totals **before they were summed**. Deferred, it reads them after. The values are real: six teams
with playoff records in each year, 5 wins against 5 losses — exactly a six-team bracket, the same
shape as 2016, which always had the column — four teams showing "—", and Ryan Boggess at 2–0 in
2014, which the champions board independently confirms as his title year.

So **2014 and 2015 have been silently missing their playoff column on the live site**, and this
fixes it. It is a visible change to the archive rather than a pure refactor, which is why it is
called out here rather than buried.

**Confirmed, on two independent axes.** 2015 was reconstructed from `ARCH.G` directly — the raw game
log, not the aggregate the column is built from. Those games carry three bracket flags, and filtering
to **flag 1 (winner's bracket)**, the only one the site counts toward playoff records, reproduces the
restored column exactly: byes to the top two seeds, week-14 quarters (Ryan def. Leo 99.6–94.1, Adam
def. Michael 135.05–76.95), week-15 semis (Ermin def. Ryan 130.65–95.75, Christian def. Adam
95.1–70.15) and the Alma Bowl (**Christian Winn 158.9 – Ermin Cerimovic 102.7**). Five games, 5–5.
**Justin then confirmed it against his own memory of that season** (2026-08-12), including the two
rows most likely to look wrong: Ermin holding the best regular record at 9–4 but placing 2nd, since
RK is final placement, and Leo at 8–5 taking the 6 seed. Treat 2014/2015's `Post` column as verified,
not as a side effect to keep an eye on.

**The saving:** fully eager **578ms**, final **258ms** — **~320ms, about 55% of script time**.
Against the ~9x ratio Justin's throttled numbers imply, roughly **2.9 seconds** off the window
where a phone is painted but frozen.

### Working notes for whoever picks this up
- **A local HTTP server beats `preview.html` for reviewing an uncommitted change.**
  `python -m http.server 8765` in the repo root, then open `http://127.0.0.1:8765/index.html` in
  the user's Chrome (Claude in Chrome can screenshot it) and in the in-app Browser pane (which
  cannot screenshot but *can* resize its viewport, which real Chrome would not let this session do).
  No branch, no push, no CDN poll, nothing to delete in a merge commit. Two traps: `navigate` forces
  `https://` onto a bare `file:///` URL so file URLs do not work, and **the pane caches** — it
  served a pre-edit copy and reported the fix missing until the URL got a `?cb=2` on it. Check a
  marker (`[...document.styleSheets]` for a string from the new rule) before trusting a measurement.
- **`preview.html` is the review mechanism and it works.** Pages here is classic
  deploy-from-branch on `main` with no `.github/workflows`, so a branch has no URL. Copy the
  branch's `index.html` to `preview.html` on `main`, push, verify in a real browser, delete it in
  the merge commit. Six of these ran cleanly across this session.
- **Don't trust the Pages builds API.** For the last several deploys
  `gh api repos/tslytle/south-ffl/pages/builds` reported the previous commit as latest for ten
  minutes or more while the CDN was already serving the new file. Poll the served file instead —
  `until curl -s <url> | grep -q "<marker>"; do sleep 15; done` backgrounded — and use a marker
  string unique to the commit.
- **Measure in a browser, not by reading.** Every visual defect this session was invisible in the
  source: the back control at 75×16px, the `.subnav`/panel weight collision, and a fixed-width
  merge gate that false-positived on a `@media` breakpoint. Conversely the `.subnav` chips *looked*
  like a touch-target bug at 30px on desktop and were already fine at 44px on mobile — so measure
  before fixing, too.
- **Do the work on the branch.** One shell edit was written while still on `main` and had to be
  stashed across. On a repo where `main` is the live site that is the mistake worth not repeating.
- **Get eyes on the page before doing any visual work — this is the big one.** The in-app browser
  pane cannot composite screenshots in this environment (every `screenshot` call times out with
  "the Browser pane is not displayed"), so it can only measure the DOM. The **Claude in Chrome**
  tools drive the user's real Chrome and screenshot fine. Ask the user to open the site in Chrome,
  then `ToolSearch` for `mcp__claude-in-chrome__tabs_context_mcp`, `navigate` and `computer`, and
  screenshot after **every** visual change.
  Why it matters: the hub shipped with a collapsed layout — titles running inline into their
  sub-lines — and four shell steps were built on top of it, while structural checks (target
  resolution, tap depth, heading order, overflow at two widths, touch targets) all passed the whole
  time. **None of those can see a broken layout.** A single user screenshot found it instantly, and
  in the same pass found stranded disclosure chevrons and the fact that a monochrome palette was
  the wrong answer. Measuring properties is not looking at the page.
- **Never build markdown containing backticks through a shell string.** An earlier version of the
  visual-pass section above was written inside a double-quoted shell string; every backtick-quoted
  CSS term was treated as command substitution and silently replaced with nothing, leaving notes
  that read "The first fix () changed nothing". Use the editor for prose.

## Environment notes for a fresh Claude Code session
- This repo still has no `.claude/settings.local.json` of its own. There is one a level up, in
  the parent `South FFL Website/` folder, which is where the PC session's permissions actually
  live — nothing carries over from the Mac session.
- `index.html` is the single self-contained site file (~2.5MB). No build step, no backend.
- Draft night countdown target: `new Date("2026-09-07T18:00:00-05:00")`.
- **`main` is the deploy branch.** GitHub Pages serves `tslytle.github.io/south-ffl` straight off
  it, so pushing `main` republishes the public site — there is no staging step. The user's
  standing preference is to commit directly to `main` rather than work on feature branches.
- **Useful trick for auditing this file:** the page's own JS can be loaded into a Node VM with a
  stubbed DOM (`document.getElementById` returning a shared stub, `window` aliased to the
  sandbox), which lets you re-run `draftRankings()`, `pfMetrics()`, `rosterAt()` etc. out of band
  against the real data. `const`/`let` at script top level land in the context's global lexical
  scope, so a later `vm.runInContext('DRAFTS')` can read them. That is how the points-per-game
  bug, the draft-ranking correlations and the standings-overflow numbers were all measured rather
  than guessed.
- **Boards are lazy now, which changes how you inspect them from the console.** A board's DOM does
  not exist until its view is revealed, so `document.getElementById("awardswall").innerHTML` is
  empty on the hub route and any audit that walks board DOM must call `drawAllBoards()` — or
  `drawBoard("<section id>")` — first. `LAZY_BOARDS` lists what is still pending. This caught me
  once: a badge check returned zero chips and looked like a bug.
- **Publishing is a two-part question.** `git push` updating `origin/main` is not the same as
  readers seeing it. Pages serves with `Cache-Control: max-age=600`, so a returning visitor can
  hold a stale copy for ten minutes — and because the site routes client-side, **anyone with the
  tab already open keeps their copy for the whole session no matter how much they click**. Confirm
  a deploy by comparing bytes, not by trusting the push:
  ```bash
  curl -s "https://tslytle.github.io/south-ffl/?n=$(date +%s)" -o /tmp/live.html
  git hash-object index.html /tmp/live.html   # two identical hashes = live is exactly HEAD
  ```
- **Don't wait on the Pages builds API** (it lags by ten minutes or more). Poll the served file for
  a string unique to the commit instead — a fragment of a comment you just wrote works well:
  `until curl -s <url> | grep -q "<marker>"; do sleep 15; done`, backgrounded.
