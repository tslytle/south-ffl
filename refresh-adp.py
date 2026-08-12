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


SUFFIX_RE = re.compile(r"\s+(Jr\.?|Sr\.?|II|III|IV|V)$", re.IGNORECASE)
APOSTROPHE_RE = re.compile(r"[‘’ʼ]")


def normalize_name(name):
    """Loose match key -- same rules as refresh-tiers.py, deliberately.

    ADP_2026 is looked up at runtime as ADP_2026[name] where `name` is CHEAT's
    spelling, so a key written under ESPN's spelling is not a cosmetic
    difference: it is a player with no market price and no value/reach tag, and
    nothing on the page says so. That is not hypothetical -- ESPN lists the
    Chargers receiver as "Tre' Harris" while NFL.com, the Chargers themselves
    and Pro-Football-Reference (where this site's player links go) all write
    "Tre Harris", so he silently had no ADP until check-cheat.py found it on
    2026-08-12.

    refresh-tiers.py has matched exact-then-normalized since it was written;
    this script keyed straight off ESPN's fullName. Same rules both sides now.
    """
    n = APOSTROPHE_RE.sub("'", name)
    n = SUFFIX_RE.sub("", n)
    # Apostrophes are DROPPED, not just normalized to one shape. Sources
    # disagree about whether the name has one at all -- ESPN "Tre' Harris" vs
    # NFL.com/Chargers/PFR "Tre Harris" -- so folding curly to straight is not
    # enough; that was the whole failure. Same for periods, for "A.J." vs "AJ".
    n = n.replace("'", "").replace(".", "")
    n = re.sub(r"\s+", " ", n).strip()
    return n.lower()


def rekey_to_sheet(espn, cheat):
    """Return ESPN's ADP keyed by the sheet's spelling wherever the two differ
    only by punctuation or a suffix. Reported, never silent -- a rename that
    happens without being printed is how the next one goes unnoticed."""
    sheet = [row[2] for rows in cheat.values() for row in rows]
    by_norm = {}
    for name in sheet:
        by_norm.setdefault(normalize_name(name), []).append(name)

    out, rekeyed = {}, []
    for name, adp in espn.items():
        if name in sheet:
            out[name] = adp
            continue
        hits = by_norm.get(normalize_name(name), [])
        if len(hits) == 1:
            out[hits[0]] = adp
            rekeyed.append((name, hits[0]))
        else:
            out[name] = adp          # genuinely not on the sheet, or ambiguous
    return out, rekeyed


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


def strip_preceding_comments(html, decl_start, max_blocks=5):
    """Return the start index after stripping /* ... */ blocks that sit
    *immediately* (only whitespace between them) before html[decl_start:].

    Deliberately NOT a single regex over the whole document (that's what
    this replaced -- see refresh-tiers.py's version of this function for
    the full story: a `(?:/\\*[\\s\\S]*?\\*/\\s*\\n)*const X = ` regex over a
    2.5MB file backtracked across the entire <style>/<script> preamble on
    one run and deleted ~2MB of real content, treating unrelated code as
    if it were "one big comment"). This walks backward with plain string
    ops instead: bounded, cheap, and it can only ever remove exactly the
    comment blocks directly touching decl_start.
    """
    pos = decl_start
    blocks_stripped = 0
    while blocks_stripped < max_blocks:
        end = pos
        while end > 0 and html[end - 1] in " \t\r\n":
            end -= 1
        if end < 2 or html[end - 2:end] != "*/":
            break
        close = end
        open_idx = html.rfind("/*", 0, close)
        if open_idx == -1:
            break
        inner = html[open_idx + 2:close - 2]
        if "*/" in inner:
            break  # malformed/nested-looking -- don't guess, stop here
        pos = open_idx
        blocks_stripped += 1
    return pos


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
    cheat, _ = extract_const(html, "CHEAT")

    espn, rekeyed = rekey_to_sheet(espn, cheat)
    if rekeyed:
        print(f"  {len(rekeyed)} keyed to the sheet's spelling so the runtime lookup finds them:")
        for espn_name, sheet_name in rekeyed:
            print(f"    ESPN {espn_name!r} -> sheet {sheet_name!r}")

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
    # Strip whatever comment block(s) sit directly above `const ADP_2026 =`
    # via a bounded backward scan, not a whole-document regex.
    decl = "const ADP_2026 = "
    decl_start = new_html.index(decl)
    comment_start = strip_preceding_comments(new_html, decl_start)
    new_comment = (
        f"/* Consensus ADP for the 2026 draft class, half-PPR, pulled from ESPN's\n"
        f"   live draft-room defaults (leaguedefaults/{LEAGUEDEFAULTS_ID}, verified half-PPR via\n"
        f"   its 0.5-points-per-reception scoring setting -- ESPN's own metadata just\n"
        f"   labels it \"PPR\") and keyed by the same full names CHEAT uses so a lookup\n"
        f"   is just ADP_2026[name]. Not every CHEAT entry has a market price yet --\n"
        f"   names ESPN's draft room hasn't ranked simply aren't keys here, and callers\n"
        f"   should treat a miss as \"no consensus ADP\" rather than an error. Captured\n"
        f"   {captured_full}. */\n{decl}"
    )
    new_html = new_html[:comment_start] + new_comment + new_html[decl_start + len(decl):]

    # Inline comment a few lines above drRow(): "the market (<source>'s consensus half-PPR ADP)"
    # Matches either PFF (the original, one-time label fix) or ESPN (every
    # re-run after that) -- a source-specific-only match would silently
    # no-op forever after the first successful run, same class of bug as
    # the tooltip regex below originally had.
    new_html, n_inline = re.subn(
        r"the market \([A-Za-z]+'s consensus half-PPR ADP\)",
        "the market (ESPN's consensus half-PPR ADP)",
        new_html,
    )
    if n_inline == 0:
        fail("could not find the inline 'the market (...)' comment to update -- aborting "
             "before writing a data-only change with a stale/wrong comment")
    # Tooltip shown on every ADP number in the UI. Same reasoning: match any
    # source name and any previously-captured date, not just "PFF".
    new_html, n_tooltip = re.subn(
        r'title="Consensus ADP \([A-Za-z]+, half-PPR, captured [^"]*\)"',
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
