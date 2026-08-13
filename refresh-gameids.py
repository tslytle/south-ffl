#!/usr/bin/env python3
"""Attach ESPN gameIds to the 2026 NFL schedule in index.html.

The NFL const on the page stores each game as [kickoffISO, away, home, network].
That is everything the schedule board needs to DRAW a game, but not enough to
LINK to one: ESPN's game pages are addressed only by an opaque numeric id
(espn.com/nfl/game/_/gameId/401872656) -- there is no date/team-based URL that
resolves to a single game. This script fetches those ids from ESPN's public
scoreboard endpoint and appends each one to its game as a fifth element:

    ["2026-09-10T00:20Z", "NE", "SEA", "NBC"]  ->
    ["2026-09-10T00:20Z", "NE", "SEA", "NBC", "401872656"]

Matching is on (kickoff DATE, away abbr, home abbr), not on order or on index.
ESPN returns a week's events in its own order and reorders them as the league
flexes games, so a positional match would silently mislabel rows. A team cannot
play twice on one day, so the triple is unique. Every game must match: the
script refuses to write a partial map rather than leave some rows linkless and
others not, since a board where only some games are clickable is worse than one
where none are.

Re-run this when the schedule moves. Flexed games change kickoff DATE, which is
part of the match key, so a flex shows up here as an unmatched game and fails
loudly -- refresh the NFL const from the schedule source first, then run this.

Usage:
    python refresh-gameids.py            # fetch, diff, write index.html back
    python refresh-gameids.py --dry-run  # fetch and report the diff only

Always review with `git diff` before committing (ADR 0001/0002 pattern).
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

SEASON = 2026
SEASONTYPE = 2  # regular season
SCOREBOARD = (
    "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    f"?dates={SEASON}&seasontype={SEASONTYPE}&week=%s"
)
INDEX_HTML = Path(__file__).parent / "index.html"
NFL_RE = re.compile(r"^const NFL = (\{.*?\});$", re.M | re.S)


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def read_index():
    if not INDEX_HTML.exists():
        fail(f"{INDEX_HTML} not found -- run this from the repo root")
    return INDEX_HTML.read_text(encoding="utf-8")


def fetch_week(wk):
    """(date, away, home) -> gameId for one week of ESPN's scoreboard."""
    with urllib.request.urlopen(SCOREBOARD % wk, timeout=30) as r:
        data = json.load(r)
    out = {}
    for ev in data.get("events", []):
        comp = ev["competitions"][0]
        home = away = None
        for t in comp["competitors"]:
            abbr = t["team"]["abbreviation"]
            if t["homeAway"] == "home":
                home = abbr
            else:
                away = abbr
        if home and away:
            out[(ev["date"][:10], away, home)] = ev["id"]
    return out


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--dry-run", action="store_true",
        help="fetch and report the diff, don't write index.html",
    )
    args = ap.parse_args()

    html = read_index()
    m = NFL_RE.search(html)
    if not m:
        fail("could not find `const NFL = {...};` in index.html")
    nfl = json.loads(m.group(1))
    weeks = sorted(nfl["weeks"], key=int)
    total = sum(len(v) for v in nfl["weeks"].values())
    print(f"index.html: {len(weeks)} weeks, {total} games")

    added = changed = kept = 0
    missing = []
    for wk in weeks:
        try:
            espn = fetch_week(wk)
        except Exception as e:  # noqa: BLE001 -- network shape varies; report and stop
            fail(f"week {wk}: {type(e).__name__}: {e}")
        print(f"  week {wk:>2}: {len(espn)} events from ESPN", end="")
        hit = 0
        for g in nfl["weeks"][wk]:
            key = (g[0][:10], g[1], g[2])
            gid = espn.get(key)
            if gid is None:
                missing.append((wk, *key))
                continue
            hit += 1
            if len(g) > 4:
                if g[4] == gid:
                    kept += 1
                else:
                    g[4] = gid
                    changed += 1
            else:
                g.append(gid)
                added += 1
        print(f", matched {hit}/{len(nfl['weeks'][wk])}")

    if missing:
        print(f"\n{len(missing)} game(s) had no ESPN match:", file=sys.stderr)
        for wk, date, away, home in missing[:20]:
            print(f"  week {wk}: {away} @ {home} on {date}", file=sys.stderr)
        fail(
            "refusing to write a partial map -- a board where only some games "
            "link is worse than one where none do. If the NFL has flexed a game, "
            "refresh the NFL const's kickoff times first, then re-run."
        )

    print(f"\n{added} added, {changed} changed, {kept} already correct")
    if not (added or changed):
        print("Nothing to write.")
        return

    # separators match the const's existing minified form -- this line is ~30KB
    # and reformatting it would bury the real change in whitespace noise.
    packed = json.dumps(nfl, separators=(",", ":"), ensure_ascii=False)
    new_html = html[: m.start(1)] + packed + html[m.end(1):]

    if args.dry_run:
        print(f"--dry-run: would write {INDEX_HTML} "
              f"({len(new_html) - len(html):+d} bytes)")
        return

    INDEX_HTML.write_text(new_html, encoding="utf-8")
    print(f"\nWrote {INDEX_HTML} ({len(new_html) - len(html):+d} bytes). "
          "Review with `git diff` before committing.")


if __name__ == "__main__":
    main()
