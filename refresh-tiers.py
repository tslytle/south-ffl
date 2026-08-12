#!/usr/bin/env python3
"""Refresh TIER_2026 in index.html from FantasyPros' position-specific draft
cheatsheets.

Per ADR 0003 (docs/adr/0003-fantasypros-half-ppr-tiers.md): uses FantasyPros'
own `tier` field directly (no separate clustering algorithm) rather than
hand-curating.

IMPORTANT correction vs. the original ADR 0003 plan: the single "all
positions" page it named (half-point-ppr-cheatsheets.php) has
`position_id: "ALL"` and its `tier` field is a *global* cross-position tier
(RB/WR dominate the early tiers by positional scarcity, so e.g. the #1
overall QB can land in "tier 3"). Using that directly per-position would
misrepresent the site's per-position groupings -- QB tier 1 is supposed to
mean "the best available QBs", not "players who happen to be QBs and are
also globally elite". FantasyPros' *position-specific* draft cheatsheets
(rb/wr/te get a half-PPR variant; QB doesn't vary by PPR so it uses the
standard one) have `tier` computed within that position instead, which is
what this script actually pulls from:

    qb-cheatsheets.php                      (position_id=QB, scoring=STD)
    half-point-ppr-rb-cheatsheets.php       (position_id=RB, scoring=HALF)
    half-point-ppr-wr-cheatsheets.php       (position_id=WR, scoring=HALF)
    half-point-ppr-te-cheatsheets.php       (position_id=TE, scoring=HALF)

Scope is intentionally bounded to match the site's existing curation:
TIER_2026 only covers the top N players per position, matching whatever
depth is currently baked into index.html's CHEAT/TIER_2026 data -- kickers
and D/ST are left untiered, and "deep bench" beyond each position's cutoff
stays untiered on purpose (see the comment above TIER_2026 in index.html).
This script refreshes tier *values* for that same shape; it does not decide
to expand or shrink which players get tiered. If the depth should change,
edit nothing here -- the cutoff is derived from the current file, so change
it there deliberately and re-run.

Usage:
    python refresh-tiers.py            # fetch, diff, write index.html back
    python refresh-tiers.py --dry-run  # fetch and report the diff only

Always review with `git diff` before committing (ADR 0001/0002 pattern) --
this script fails loudly (non-zero exit, clear message) on unexpected page
shape rather than silently writing garbage, but it can't catch everything.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

FP_URLS = {
    "QB": "https://www.fantasypros.com/nfl/rankings/qb-cheatsheets.php",
    "RB": "https://www.fantasypros.com/nfl/rankings/half-point-ppr-rb-cheatsheets.php",
    "WR": "https://www.fantasypros.com/nfl/rankings/half-point-ppr-wr-cheatsheets.php",
    "TE": "https://www.fantasypros.com/nfl/rankings/half-point-ppr-te-cheatsheets.php",
}
EXPECTED_SCORING = {"QB": "STD", "RB": "HALF", "WR": "HALF", "TE": "HALF"}

INDEX_HTML = Path(__file__).parent / "index.html"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

SUFFIX_RE = re.compile(r"\s+(Jr\.?|Sr\.?|II|III|IV|V)$", re.IGNORECASE)
APOSTROPHE_RE = re.compile(r"[‘’ʼ]")


def normalize_name(name):
    """Loose match key: strip generational suffixes, normalize apostrophes,
    drop periods, collapse whitespace. Used only as a fallback when an exact
    name match fails -- exact match is preferred and far more common."""
    n = APOSTROPHE_RE.sub("'", name)
    n = SUFFIX_RE.sub("", n)
    n = n.replace(".", "")
    n = re.sub(r"\s+", " ", n).strip()
    return n.lower()


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def fetch_position_ecr(pos, url):
    import requests

    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    except requests.RequestException as e:
        fail(f"[{pos}] could not reach FantasyPros ({e})")
    if resp.status_code != 200:
        fail(f"[{pos}] FantasyPros returned HTTP {resp.status_code}, expected 200")

    m = re.search(r"var ecrData = (\{.*?\});", resp.text, re.DOTALL)
    if not m:
        fail(
            f"[{pos}] could not find 'var ecrData = {{...}};' on {url} -- "
            f"page structure likely changed, needs a human to re-check the source"
        )
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        fail(f"[{pos}] ecrData did not parse as JSON ({e})")

    if data.get("position_id") != pos:
        fail(f"[{pos}] expected position_id={pos}, got {data.get('position_id')!r}")
    expected_scoring = EXPECTED_SCORING[pos]
    if data.get("scoring") != expected_scoring:
        fail(f"[{pos}] expected scoring={expected_scoring}, got {data.get('scoring')!r}")
    players = data.get("players")
    if not players or not isinstance(players, list):
        fail(f"[{pos}] ecrData has no players list")
    required_keys = {"player_name", "tier", "rank_ecr", "pos_rank"}
    missing = required_keys - players[0].keys()
    if missing:
        fail(f"[{pos}] player objects are missing expected keys: {sorted(missing)}")

    return data


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


def build_fp_lookup(players):
    exact, normalized = {}, {}
    for p in players:
        exact.setdefault(p["player_name"], []).append(p)
        normalized.setdefault(normalize_name(p["player_name"]), []).append(p)
    return exact, normalized


def match_player(name, exact, normalized):
    if name in exact and len(exact[name]) == 1:
        return exact[name][0], "exact"
    key = normalize_name(name)
    if key in normalized and len(normalized[key]) == 1:
        return normalized[key][0], "normalized"
    return None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="fetch and report the diff, don't write index.html")
    ap.add_argument("--min-match-rate", type=float, default=0.90,
                     help="abort if fewer than this fraction of the currently-tiered players match (default 0.90)")
    args = ap.parse_args()

    fp_by_pos = {}
    for pos, url in FP_URLS.items():
        print(f"Fetching {pos} from {url} ...")
        d = fetch_position_ecr(pos, url)
        fp_by_pos[pos] = d
        print(f"  scoring={d['scoring']}  players={len(d['players'])}  "
              f"last_updated={d.get('last_updated')}")

    html = load_index_html()
    cheat, _ = extract_const(html, "CHEAT")
    old_tier, tier_span = extract_const(html, "TIER_2026")

    # Cutoff per position = however many of that position's CHEAT rows are
    # currently tiered. Preserves existing scope; doesn't invent new depth.
    cutoff = {}
    for pos, rows in cheat.items():
        names_in_order = [row[2] for row in rows]
        tiered_count = sum(1 for n in names_in_order if n in old_tier)
        cutoff[pos] = tiered_count
    print("Position cutoffs (from current TIER_2026 coverage):",
          {p: c for p, c in cutoff.items() if c > 0})

    new_tier = {}
    unmatched = []
    considered = 0
    for pos, rows in cheat.items():
        n = cutoff.get(pos, 0)
        if n == 0:
            continue  # position not in scope (currently K, DST)
        if pos not in fp_by_pos:
            fail(f"position {pos} has {n} currently-tiered players but no FantasyPros source is configured for it")
        exact, normalized = build_fp_lookup(fp_by_pos[pos]["players"])
        for row in rows[:n]:
            name = row[2]
            considered += 1
            player, how = match_player(name, exact, normalized)
            if player is None:
                unmatched.append((pos, name))
                continue
            new_tier[name] = player["tier"]

    match_rate = (considered - len(unmatched)) / considered if considered else 0
    print(f"Matched {considered - len(unmatched)}/{considered} in-scope players "
          f"({match_rate:.0%}).")
    if unmatched:
        print("  Unmatched (kept out of TIER_2026, won't silently guess):")
        for pos, name in unmatched:
            print(f"    - [{pos}] {name}")

    if match_rate < args.min_match_rate:
        fail(
            f"match rate {match_rate:.0%} is below --min-match-rate "
            f"{args.min_match_rate:.0%} -- aborting without writing. This usually "
            f"means FantasyPros' naming or page shape changed more than expected; "
            f"needs a human look before trusting the write-back."
        )

    added = sorted(set(new_tier) - set(old_tier))
    removed = sorted(set(old_tier) - set(new_tier))
    changed = sorted(k for k in (set(new_tier) & set(old_tier)) if new_tier[k] != old_tier[k])

    print()
    print(f"Diff vs current TIER_2026: {len(added)} added, {len(removed)} dropped, "
          f"{len(changed)} tier changes, {len(new_tier) - len(added) - len(changed)} unchanged.")
    for k in changed:
        print(f"  tier change: {k}: {old_tier[k]} -> {new_tier[k]}")
    for k in added:
        print(f"  newly tiered: {k}: {new_tier[k]}")
    for k in removed:
        print(f"  dropped from tier scope: {k} (was {old_tier[k]})")

    if args.dry_run:
        print("\n--dry-run set, not writing index.html.")
        return

    # Order output: by tier ascending, then by that position's CHEAT rank --
    # mirrors the existing hand-curated ordering for a readable git diff.
    rank_lookup = {}
    for pos, rows in cheat.items():
        for row in rows:
            rank_lookup[row[2]] = row[0]
    ordered_names = sorted(new_tier, key=lambda nm: (new_tier[nm], rank_lookup.get(nm, 9999)))
    ordered_tier = {nm: new_tier[nm] for nm in ordered_names}

    new_json = json.dumps(ordered_tier, separators=(",", ":"), ensure_ascii=False)
    start, end = tier_span
    new_html = html[:start] + new_json + html[end:]

    captured = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total_experts = {pos: fp_by_pos[pos].get("total_experts") for pos in fp_by_pos}
    comment_re = re.compile(
        r"(/\* Consensus half-PPR tiers[\s\S]*?\*/\s*\n)?const TIER_2026 = "
    )
    new_comment = (
        f"/* Per-position draft tiers for the 2026 class, pulled from FantasyPros'\n"
        f"   position-specific draft cheatsheets (fantasypros.com/nfl/rankings/\n"
        f"   {{qb-cheatsheets,half-point-ppr-{{rb,wr,te}}-cheatsheets}}.php -- QB uses\n"
        f"   standard scoring since QB output doesn't depend on PPR settings; RB/WR/TE\n"
        f"   use half-PPR), using FantasyPros' own `tier` field directly (gap-based\n"
        f"   clustering within each position, not a globally computed one -- the\n"
        f"   all-positions cheatsheet's tier field is a *cross-position* tier and\n"
        f"   would misrepresent per-position groupings if used here). Expert counts:\n"
        f"   {json.dumps(total_experts)}. Captured {captured}. Good for a rough\n"
        f"   gut-check but not a substitute for judgment on draft night. Deep bench\n"
        f"   beyond each position's cutoff is left untiered on purpose -- there's no\n"
        f"   real signal to group by there. */\nconst TIER_2026 = "
    )
    new_html = comment_re.sub(new_comment, new_html, count=1)

    INDEX_HTML.write_text(new_html, encoding="utf-8")
    print(f"\nWrote {INDEX_HTML}. Review with `git diff` before committing.")


if __name__ == "__main__":
    main()
