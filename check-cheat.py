#!/usr/bin/env python3
"""Pre-draft consistency check for the cheat sheet's own data.

`refresh-adp.py` and `refresh-tiers.py` keep prices and groupings current for
players who are *already on the sheet*. Neither will ever notice that a player
changed teams, that his bye moved with him, or that he should be there at all.
That gap is what produced the stale **A.J. Brown at PHI/bye 10** entry found on
2026-08-11 -- three months after he was traded to New England. `DEPTH_TEAMS`
had him right; `CHEAT` did not; and nothing compared the two.

Cross-checking them was a manual pass. This is that pass, written down.

Nothing here fetches anything and nothing writes anything: it reads index.html
and reports. It cannot tell you a player was traded -- only that the file
disagrees with itself, which is what caught A.J. Brown. Checking the sheet
against the actual NFL is still a human job, best done with a live search
against real sources rather than from memory (training data predates the
current transaction wire, and confidently says PHI).

Usage:
    python check-cheat.py            # report; exit 1 if any ERROR
    python check-cheat.py --quiet    # only ERRORs and the summary
    python check-cheat.py --strict   # exit 1 on WARN as well

Data shapes it reads:
    DEPTH_TEAMS  {division: [[mascot, abbr, colour, bye, [[slot, name, orank], ...]], ...]}
    CHEAT        {POS: [[posRank, overallRank, name, teamAbbr, bye], ...]}
    ADP_2026     {name: adp}
    TIER_2026    {name: tier}
    ESPN_VERIFIED{name: espnAthleteId}
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from difflib import get_close_matches
from pathlib import Path

INDEX_HTML = Path(__file__).parent / "index.html"

# K and D/ST are deliberately outside the tiered/priced depth, exactly as they
# are outside SKILL everywhere else on the site -- nobody argues about where a
# kicker went in the draft.
PRICED_POSITIONS = ("QB", "RB", "WR", "TE")
BYE_RANGE = (4, 15)          # generous; the real NFL window sits inside this

findings = {"ERROR": [], "WARN": [], "NOTE": []}


def add(level, check, msg):
    findings[level].append((check, msg))


def load(name, html):
    m = re.search(r"const " + re.escape(name) + r" = (\{.*?\});", html, re.DOTALL)
    if not m:
        print(f"ERROR: could not find 'const {name} = ...' in index.html", file=sys.stderr)
        sys.exit(2)
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError as e:
        print(f"ERROR: const {name} did not parse as JSON ({e})", file=sys.stderr)
        sys.exit(2)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quiet", action="store_true", help="only ERRORs and the summary")
    ap.add_argument("--strict", action="store_true", help="exit 1 on WARN as well as ERROR")
    args = ap.parse_args()

    if not INDEX_HTML.exists():
        print(f"ERROR: {INDEX_HTML} not found -- run this from the repo root", file=sys.stderr)
        sys.exit(2)
    html = INDEX_HTML.read_text(encoding="utf-8")

    depth = load("DEPTH_TEAMS", html)
    cheat = load("CHEAT", html)
    adp = load("ADP_2026", html)
    tier = load("TIER_2026", html)
    espn = load("ESPN_VERIFIED", html)
    logo_keys = set(re.findall(r'"([A-Z]{2,3})":"data:image', html))

    # ── DEPTH_TEAMS: the reference both other checks lean on ────────────────
    teams = [t for div in depth.values() for t in div]
    if len(teams) != 32:
        add("ERROR", "depth/count", f"{len(teams)} teams in DEPTH_TEAMS, expected 32")

    abbr_bye, abbr_mascot = {}, {}
    for mascot, abbr, _colour, bye, _roster in teams:
        if abbr in abbr_bye:
            add("ERROR", "depth/dup-abbr", f"{abbr} appears twice in DEPTH_TEAMS")
        abbr_bye[abbr] = bye
        abbr_mascot[abbr] = mascot
        if not (BYE_RANGE[0] <= bye <= BYE_RANGE[1]):
            add("ERROR", "depth/bye-range", f"{abbr} has bye {bye}, outside {BYE_RANGE}")
    if logo_keys:
        for abbr in sorted(set(abbr_bye) - logo_keys):
            add("ERROR", "depth/logo", f"{abbr} has no NFL_LOGO entry")

    # name -> (abbr, bye), the authority CHEAT is checked against
    depth_players = {}
    for mascot, abbr, _c, bye, roster in teams:
        for _slot, name, _orank in roster:
            if name and name != "-":
                depth_players.setdefault(name, (abbr, bye))

    # ── CHEAT: internal shape ───────────────────────────────────────────────
    seen_orank = {}
    cheat_names = {}
    for pos, rows in cheat.items():
        posranks = [r[0] for r in rows]
        if posranks != list(range(1, len(rows) + 1)):
            gaps = [i for i, (a, b) in enumerate(zip(posranks, range(1, len(rows) + 1))) if a != b]
            add("ERROR", "cheat/posrank",
                f"{pos} position ranks are not 1..{len(rows)} (first break at index {gaps[0]})")
        dupes = [n for n, c in Counter(r[2] for r in rows).items() if c > 1]
        for n in dupes:
            add("ERROR", "cheat/dup-name", f"{n} listed twice in CHEAT.{pos}")

        for posrank, orank, name, team, bye in rows:
            cheat_names[name] = (pos, team, bye)
            if orank is None:
                # the value/reach threshold is max(3, round(orank*0.10)); a null
                # coerces to 0 in JS and quietly makes every pick a "value"
                add("ERROR", "cheat/null-orank", f"{name} ({pos}{posrank}) has a null overall rank")
            elif orank in seen_orank:
                add("ERROR", "cheat/dup-orank",
                    f"overall rank {orank} used by both {seen_orank[orank]} and {name}")
            else:
                seen_orank[orank] = name

            if team not in abbr_bye:
                add("ERROR", "cheat/team", f"{name} has team '{team}', which is not one of the 32")
            elif bye != abbr_bye[team]:
                add("ERROR", "cheat/bye",
                    f"{name} ({team}) has bye {bye}, but {team}'s bye is {abbr_bye[team]}")

    # ── The cross-check that caught A.J. Brown ──────────────────────────────
    def near(name, pool):
        """Closest name in pool, if it is close enough to be a misspelling
        rather than a different man. 0.86 clears 'Jaylin/Jaylen Lane' and
        'Chris Godwin Jr.' while keeping brothers and cousins apart."""
        hit = get_close_matches(name, pool, n=1, cutoff=0.86)
        return hit[0] if hit and hit[0] != name else None

    for name, (pos, team, bye) in sorted(cheat_names.items()):
        if name not in depth_players:
            # DEPTH_TEAMS lists a fixed set of slots per club -- QB1-2, RB1-3,
            # WR1-3, TE1 and so on -- so anyone deeper than that is absent by
            # design, and most of these are exactly that. A misspelt name looks
            # identical from here, which is the one case worth raising.
            if pos != "DST":
                twin = near(name, depth_players)
                if twin:
                    add("WARN", "cross/near-miss",
                        f"{name} is on no depth chart, but '{twin}' is -- same player, two spellings?")
                else:
                    add("NOTE", "cross/not-on-depth",
                        f"{name} ({pos}) is deeper than the slots DEPTH_TEAMS lists -- expected,"
                        " but nothing cross-checks his team or bye")
            continue
        d_team, d_bye = depth_players[name]
        if d_team != team:
            add("ERROR", "cross/team",
                f"{name}: CHEAT says {team} (bye {bye}), DEPTH_TEAMS says {d_team} (bye {d_bye})"
                " -- this is the A.J. Brown shape; check a live source, not memory")
        elif d_bye != bye:
            add("ERROR", "cross/bye",
                f"{name}: CHEAT bye {bye}, DEPTH_TEAMS bye {d_bye} for the same team {team}")

    only_depth = sorted(set(depth_players) - set(cheat_names))
    add("NOTE", "cross/depth-only",
        f"{len(only_depth)} players are on a depth chart but not the cheat sheet"
        " (expected: backup QBs, TE2s, kickers -- CHEAT only ranks draftable depth)")

    # ── Pricing and tier coverage ───────────────────────────────────────────
    # A player with no ADP has no value/reach tag. Usually that is just depth:
    # ADP holds the top ~250 *by draft-room position*, which is a different
    # population from the sheet's top 250 by expert rank, so "his rank is inside
    # 250 therefore he should be priced" is not a real test -- it fired on 25
    # perfectly ordinary deep backs and receivers the first time it was tried.
    # The signal worth raising is a name the ADP table nearly has.
    for pos in PRICED_POSITIONS:
        rows = cheat.get(pos, [])
        missing = [r for r in rows if r[2] not in adp]
        quiet = 0
        for _pr, orank, name, _t, _b in missing:
            twin = near(name, adp)
            if twin:
                add("WARN", "adp/near-miss",
                    f"{name} ({pos}, overall {orank}) has no ADP, but the table has '{twin}'"
                    " -- same man, two spellings, and he loses his value/reach tag")
            else:
                quiet += 1
        if quiet:
            add("NOTE", "adp/unpriced",
                f"{pos}: {quiet} have no ADP and no near-match -- expected, they are below the"
                " depth the source covers")

        tiered = [r for r in rows if r[2] in tier]
        if tiered:
            depth_cut = len(tiered)
            untier = [r[2] for r in rows[:depth_cut] if r[2] not in tier]
            if untier:
                add("WARN", "tier/gap",
                    f"{pos}: {len(untier)} inside the top {depth_cut} have no tier"
                    f" ({', '.join(untier[:4])})")

    # A key in a lookup table that matches nobody is usually just scope -- the
    # tables cover more men than the sheet ranks. A key that *nearly* matches
    # somebody is a spelling drift, and it silently costs that player his ADP,
    # his tier or his player link.
    for label, table in (("ADP_2026", adp), ("TIER_2026", tier), ("ESPN_VERIFIED", espn)):
        stale = sorted(set(table) - set(cheat_names))
        typos = [(k, near(k, cheat_names)) for k in stale]
        typos = [(k, t) for k, t in typos if t]
        for k, t in typos:
            add("WARN", f"{label.lower()}/near-miss",
                f"{label} has '{k}', the sheet has '{t}' -- one of them is misspelt,"
                " and the sheet is the one that loses the value")
        rest = len(stale) - len(typos)
        if rest:
            add("NOTE", f"{label.lower()}/unused",
                f"{rest} {label} entries match nobody on the sheet -- expected, these tables"
                " cover more men than CHEAT ranks")

    by_id = defaultdict(list)
    for name, pid in espn.items():
        by_id[pid].append(name)
    for pid, names in sorted(by_id.items()):
        if len(names) > 1:
            add("ERROR", "espn/dup-id",
                f"ESPN id {pid} is shared by {' and '.join(names)} -- one links to the wrong man")

    # ── Report ──────────────────────────────────────────────────────────────
    order = ["ERROR", "WARN", "NOTE"]
    for level in order:
        if args.quiet and level != "ERROR":
            continue
        for check, msg in findings[level]:
            print(f"{level:5} [{check}] {msg}")

    n_err, n_warn = len(findings["ERROR"]), len(findings["WARN"])
    counts = (f"{len(cheat_names)} players on the sheet, {len(teams)} teams, "
              f"{len(adp)} ADP entries, {len(tier)} tiers")
    print(f"\n{counts}")
    print(f"{n_err} error(s), {n_warn} warning(s), {len(findings['NOTE'])} note(s)")
    if not n_err and not n_warn:
        print("Clean. This says the file agrees with itself -- not that it agrees with the NFL.")
    sys.exit(1 if n_err or (args.strict and n_warn) else 0)


if __name__ == "__main__":
    main()
