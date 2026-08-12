#!/usr/bin/env python3
"""Pre-draft ADP refresh for the South FFL page (ADR 0002).

Fetches ESPN's live 2026 draft-room ADP under **half-PPR** scoring and writes
it back into ADP_2026 in index.html, along with the "captured [date]" label
and the source comment/tooltip -- all previously mislabeled "PFF" (the site's
ADP data used to actually come from pff.com/fantasy/rankings/draft; this
switches it to ESPN to match ADR 0002/CONTEXT.md's intent, at the user's
explicit choice of "ESPN half-PPR" made 2026-08-11).

ESPN's public leaguedefaults endpoint doesn't document a half-PPR id, and
ADR 0003 assumed (for TIER_2026 purposes) that only STANDARD/PPR/ELIMINATION/
SUPERFLEX exist -- true for the endpoint's own `playerRankType` labels, but
id 8 ("FFL Half PPR Scoring") does exist and its scoringSettings confirm
0.5 points per reception, i.e. genuinely half-PPR, just mislabeled PPR in
its own metadata. This script hits id 8 and verifies that 0.5-per-reception
setting itself before trusting any ADP numbers from it -- if ESPN ever
renumbers or repurposes that id, this fails loudly instead of silently
writing standard/full-PPR ADP under a "half-PPR" label.

Value/reach tags on the cheat sheet (dradelta-value / dradelta-reach) are
computed live in JS from ADP_2026 vs. each player's rank -- nothing else
needs writing back for those to update.

Usage:
    python refresh-adp.py            # fetch, diff, write index.html back
    python refresh-adp.py --dry-run  # fetch and report the diff only

Always review with `git diff` before committing (ADR 0001/0002 pattern).
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LEAGUEDEFAULTS_ID = 8  # "FFL Half PPR Scoring" -- verified via scoringSettings, not just its name
SETTINGS_URL = (
    f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2026/"
    f"segments/0/leaguedefaults/{LEAGUEDEFAULTS_ID}?view=mSettings"
)
PLAYERS_URL = (
    f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2026/"
    f"segments/0/leaguedefaults/{LEAGUEDEFAULTS_ID}?view=kona_player_info"
)
RECEPTION_STAT_ID = 53
EXPECTED_RECEPTION_POINTS = 0.5

INDEX_HTML = Path(__file__).parent / "index.html"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def get_json(url, headers=None):
    import requests

    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT, **(headers or {})}, timeout=30)
    except requests.RequestException as e:
        fail(f"could not reach ESPN ({e})")
    if resp.status_code != 200:
        fail(f"ESPN returned HTTP {resp.status_code} for {url}, expected 200")
    try:
        return resp.json()
    except ValueError as e:
        fail(f"ESPN response wasn't valid JSON ({e})")


def verify_half_ppr():
    """Confirm leaguedefaults/8 is still really half-PPR before trusting its
    ADP numbers -- ESPN's own playerRankType field for this id just says
    "PPR", so the only real signal is the reception scoring item itself."""
    d = get_json(SETTINGS_URL)
    settings = d.get("settings", {})
    scoring = settings.get("scoringSettings", {})
    items = scoring.get("scoringItems", [])
    recv = [it["points"] for it in items if it.get("statId") == RECEPTION_STAT_ID]
    if not recv:
        fail(f"leaguedefaults/{LEAGUEDEFAULTS_ID} has no reception scoring item -- "
             f"can't verify it's still half-PPR, aborting rather than guessing")
    if recv[0] != EXPECTED_RECEPTION_POINTS:
        fail(f"leaguedefaults/{LEAGUEDEFAULTS_ID} now awards {recv[0]} points/reception, "
             f"expected {EXPECTED_RECEPTION_POINTS} -- ESPN likely renumbered/repurposed "
             f"this id. Not writing anything; find the new half-PPR id and update "
             f"LEAGUEDEFAULTS_ID by hand.")
    print(f"Verified leaguedefaults/{LEAGUEDEFAULTS_ID} is half-PPR "
          f"({recv[0]} pts/reception): {settings.get('name')!r}")


def fetch_espn_adp():
    d = get_json(
        PLAYERS_URL,
        headers={"x-fantasy-filter": json.dumps(
            {"players": {"limit": 250, "sortPercOwned": {"sortPriority": 1, "sortAsc": False}}}
        )},
    )
    players = d.get("players", [])
    if not players:
        fail("ESPN returned zero players")

    espn = {}
    for p in players:
        pl = p.get("player", {})
        adp = (pl.get("ownership") or {}).get("averageDraftPosition")
        if pl.get("fullName") and adp and adp < 250:
            espn[pl["fullName"]] = round(adp, 1)

    if len(espn) < 200:
        fail(f"only {len(espn)} players had a usable ADP (expected close to 250) -- "
             f"ESPN's response shape may have changed")
    top5 = sorted(espn.items(), key=lambda kv: kv[1])[:5]
    if not all(0 < v < 20 for _, v in top5):
        fail(f"top-5 ADP values look wrong: {top5} -- expected all under pick 20")
    return espn


def load_index_html():
    if not INDEX_HTML.exists():
        fail(f"{INDEX_HTML} not found -- run this from the repo root")
    return INDEX_HTML.read_text(encoding="utf-8")


def extract_const(html, name):
    m = re.search(rf"const {name} = (\{{.*?\}});", html, re.DOTALL)
    if not m:
        fail(f"could not find 'const {name} = {{...}};' in index.html")
    try:
        return json.loads(m.group(1)), m.span(1)
    except json.JSONDecodeError as e:
        fail(f"const {name} in index.html did not parse as JSON ({e})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="fetch and report the diff, don't write index.html")
    args = ap.parse_args()

    print(f"Fetching ESPN leaguedefaults/{LEAGUEDEFAULTS_ID} settings ...")
    verify_half_ppr()
    print("Fetching ESPN draft-room ADP ...")
    espn = fetch_espn_adp()
    print(f"  {len(espn)} players with usable ADP")

    html = load_index_html()
    old_adp, adp_span = extract_const(html, "ADP_2026")

    added = sorted(set(espn) - set(old_adp))
    removed = sorted(set(old_adp) - set(espn))
    changed = sorted(k for k in (set(espn) & set(old_adp)) if abs(espn[k] - old_adp[k]) >= 0.1)
    diffs = [espn[k] - old_adp[k] for k in (set(espn) & set(old_adp))]

    print()
    print(f"page entries: {len(old_adp)} | ESPN entries: {len(espn)} | "
          f"{len(added)} added, {len(removed)} dropped, {len(changed)} moved >=0.1")
    if diffs:
        import statistics
        print(f"mean abs move: {statistics.mean(map(abs, diffs)):.1f} picks | "
              f"median: {statistics.median(map(abs, diffs)):.1f}")
    print("\nbiggest moves (old page value -> new ESPN half-PPR ADP):")
    moved = sorted(((k, old_adp[k], espn[k]) for k in changed),
                    key=lambda t: -abs(t[2] - t[1]))[:15]
    for n, pv, ev in moved:
        print(f"  {n:30s} {pv:6.1f} -> {ev:6.1f}  ({ev - pv:+.1f})")

    if args.dry_run:
        print("\n--dry-run set, not writing index.html.")
        return

    ordered_names = sorted(espn, key=lambda n: espn[n])
    ordered_adp = {n: espn[n] for n in ordered_names}
    new_json = json.dumps(ordered_adp, separators=(",", ":"), ensure_ascii=False)
    start, end = adp_span
    new_html = html[:start] + new_json + html[end:]

    # Local date, not UTC -- this is a user-facing label read by a US league,
    # and UTC rolls over hours before the local evening does.
    now_local = datetime.now()
    captured = now_local.strftime("%b %-d") if sys.platform != "win32" else now_local.strftime("%b %#d")
    captured_full = now_local.strftime("%Y-%m-%d")

    # Source comment above ADP_2026: swap PFF framing for ESPN half-PPR.
    comment_re = re.compile(
        r"/\* Consensus ADP for the 2026 draft class[\s\S]*?\*/\s*\nconst ADP_2026 = "
    )
    new_comment = (
        f"/* Consensus ADP for the 2026 draft class, half-PPR, pulled from ESPN's\n"
        f"   live draft-room defaults (leaguedefaults/{LEAGUEDEFAULTS_ID}, verified half-PPR via\n"
        f"   its 0.5-points-per-reception scoring setting -- ESPN's own metadata just\n"
        f"   labels it \"PPR\") and keyed by the same full names CHEAT uses so a lookup\n"
        f"   is just ADP_2026[name]. Not every CHEAT entry has a market price yet --\n"
        f"   names ESPN's draft room hasn't ranked simply aren't keys here, and callers\n"
        f"   should treat a miss as \"no consensus ADP\" rather than an error. Captured\n"
        f"   {captured_full}. */\nconst ADP_2026 = "
    )
    if not comment_re.search(new_html):
        fail("could not find the ADP_2026 source comment to update -- aborting before "
             "writing a data-only change with a stale/wrong comment above it")
    new_html = comment_re.sub(new_comment, new_html, count=1)

    # Inline comment a few lines above drRow(): "the market (PFF's consensus half-PPR ADP)"
    new_html = new_html.replace(
        "the market (PFF's consensus half-PPR ADP)",
        "the market (ESPN's consensus half-PPR ADP)",
    )
    # Tooltip shown on every ADP number in the UI.
    new_html, n_tooltip = re.subn(
        r'title="Consensus ADP \(PFF, half-PPR, captured [^"]*\)"',
        f'title="Consensus ADP (ESPN, half-PPR, captured {captured})"',
        new_html,
    )
    if n_tooltip == 0:
        fail("could not find the ADP tooltip string to update -- aborting before "
             "writing a data-only change with a stale/wrong tooltip")

    INDEX_HTML.write_text(new_html, encoding="utf-8")
    print(f"\nWrote {INDEX_HTML}. Review with `git diff` before committing.")


if __name__ == "__main__":
    main()
