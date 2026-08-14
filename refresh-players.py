#!/usr/bin/env python3
"""Whole-season player values for the Draft Rankings board (ADR 0015).

Draft Rankings ranks a class on what each pick returned *over the going rate
for its slot*, and a pick's return is the player's whole NFL season -- weeks
1-17, regardless of who ended up holding him. The league export only records
points while a man sat on somebody's roster, and 42% of drafted players spent
part of a season on nobody's, so those values have to come from outside.

They come from nflverse, which this project already trusts for schedules,
weekly rosters and player ids:

    stats_player_week_YYYY.csv   every offensive and kicking category
    stats_team_week_YYYY.csv     every defensive and return category
    games.csv                    final scores, for points allowed
    players.csv                  the pfr_id -> gsis_id crosswalk

Fantasy points are computed here from raw stats under *this league's* rulebook
per season -- not taken from anyone else's arithmetic. That is checkable, and
it is checked: --verify re-scores 2018-2025 against the points the archive
already holds and reports the agreement (100.0% when this was written).

Four rules are not on the league's scoring page and were recovered from the
residuals of that check:
  * a BLOCKED field goal counts as a miss (nflverse files it apart from
    fg_missed_*), which was 52 of the 76 original disagreements;
  * a return touchdown and a touchdown on your own recovered fumble both pay
    6 and are neither rushing nor receiving scores;
  * a kicker still scores whatever he does with the ball in his hands --
    Matt Prater threw a touchdown off a fake in 2018;
  * a missed PAT costs nothing.

2014's DEFENSIVE rulebook is not known and does not need to be. The change
log records that 2015 "added extra defensive and return scoring categories"
without saying which, so 2014 is the modern set minus some subset. Measured
rather than guessed: strip every category whose 2014 status is in question --
blocked kicks, 2-pt returns and return touchdowns, the most aggressive reading
-- and no 2014 class score moves by more than a point, with the only order
change falling between two teams the board already has tied. A missing category
subtracts from every defence, so the replacement line drops with it and most of
the difference cancels before it reaches a class; what survives is one pick in
sixteen. Those categories are worth a median of 6 points and at most 28 to any
drafted 2014 defence, against a season averaging 90. 2014's YARDAGE rule is a
different matter and is known -- see yardage_points().

Defences are a known and bounded exception. Their categories and the
yards-allowed ladder reproduce exactly, but nflverse's play-by-play build
carries ~11% more sacks and ~23% more fumble recoveries than ESPN's feed, so a
D/ST season total lands within about 12% rather than exactly. ADR 0015 keeps
defences in Draft Rankings, where that error moves a class score by under one
point, and out of Steals & Busts, where it would be the whole story.

Usage:
    python refresh-players.py --verify   # re-run every check, write nothing
    python refresh-players.py --dry-run  # compute and report the diff only
    python refresh-players.py            # write PLAYER_VALUE back into index.html

Always review with `git diff` before committing (ADR 0001/0002 pattern).
"""
import argparse
import csv
import json
import math
import re
import statistics
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX = HERE / "index.html"
CACHE = HERE / ".nflverse-cache"
BASE = "https://github.com/nflverse/nflverse-data/releases/download"

SEASONS = list(range(2014, 2026))
LAST_WEEK = 17           # the fantasy season; the NFL's 18th week is not played here
POSITIONS = ("QB", "RB", "WR", "TE", "K", "D/ST")

# The startable line, per ADR 0004's measured flex-inclusive start counts, plus
# one kicker and one defence per team. Replacement is the man just past it.
BAR = {"QB": 12, "RB": 29, "WR": 31, "TE": 12, "K": 12, "D/ST": 12}
KEEP_PER_POS = 60        # baked depth; the line never sits past 31, so this is provably enough

# Points and yards allowed, transcribed from SCORE_LADDERS in index.html
PA_LADDER = [(0, 5), (6, 4), (13, 3), (17, 1), (27, 0), (34, -1), (45, -3), (10 ** 9, -5)]
YA_LADDER = [(99, 5), (199, 3), (299, 2), (349, 0), (399, -1), (449, -3),
             (499, -5), (549, -6), (10 ** 9, -7)]


# ── fetching ────────────────────────────────────────────────────────────
def grab(tag, name):
    CACHE.mkdir(exist_ok=True)
    p = CACHE / name
    if not p.exists():
        print(f"    downloading {name}", file=sys.stderr)
        urllib.request.urlretrieve(f"{BASE}/{tag}/{name}", p)
    return p


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f)


def num(r, k):
    v = r.get(k, "")
    if v in ("", "NA", "None", None):
        return 0.0
    try:
        return float(v)
    except ValueError:
        return 0.0


def trunc(x):
    return math.floor(x) if x >= 0 else math.ceil(x)


# ── the rulebook, per season ────────────────────────────────────────────
def ppr(year):
    """Half a point per catch from 2021; nothing before (RULES, index.html)."""
    return 0.5 if year >= 2021 else 0.0


def yardage_points(r, year):
    """2015 moved from whole points per block of yards to fractions per yard.

    The block sizes for 2014 are not on the scoring page; they were recovered
    by algebra against known season totals in an earlier session and reproduce
    them exactly, truncated toward zero PER GAME rather than at the season.
    """
    py, ry, cy = num(r, "passing_yards"), num(r, "rushing_yards"), num(r, "receiving_yards")
    if year <= 2014:
        return trunc(py / 25) + trunc(ry / 10) + trunc(cy / 10)
    return py * 0.05 + ry * 0.1 + cy * 0.1


def offense_points(r, year):
    p = yardage_points(r, year)
    p += num(r, "passing_tds") * 4
    p += num(r, "passing_interceptions") * -2
    p += num(r, "rushing_tds") * 6
    p += num(r, "receiving_tds") * 6
    p += num(r, "receptions") * ppr(year)
    p += num(r, "fumbles_lost_total") * -2
    p += (num(r, "passing_2pt_conversions") + num(r, "rushing_2pt_conversions")
          + num(r, "receiving_2pt_conversions")) * 2
    # A return TD and a TD on your own recovered fumble both pay 6, and neither
    # is a rushing or receiving score.
    p += (num(r, "special_teams_tds") + num(r, "fumble_recovery_tds")) * 6
    return p


def kicker_points(r, year):
    # A kicker still earns whatever he does with the ball in his hands, so the
    # kicking line is added to the ordinary one rather than replacing it.
    p = offense_points(r, year)
    p += num(r, "pat_made")                      # a missed PAT costs nothing
    p += (num(r, "fg_made_0_19") + num(r, "fg_made_20_29") + num(r, "fg_made_30_39")) * 3
    p += num(r, "fg_made_40_49") * 4
    p += (num(r, "fg_made_50_59") + num(r, "fg_made_60_")) * 5
    missed = sum(num(r, f"fg_missed_{b}") for b in
                 ("0_19", "20_29", "30_39", "40_49", "50_59", "60_"))
    # A blocked attempt is a miss; nflverse counts it in its own column.
    p += (missed + num(r, "fg_blocked")) * -1
    return p


def ladder(v, tbl):
    for hi, pts in tbl:
        if v <= hi:
            return pts
    return tbl[-1][1]


def dst_points(r, pts_allowed, yds_allowed):
    p = num(r, "def_sacks")
    p += num(r, "def_interceptions") * 2
    p += num(r, "fumble_recovery_opp") * 2
    p += num(r, "def_safeties") * 2
    p += (num(r, "def_punt_blocks") + num(r, "def_pat_blocks") + num(r, "def_fg_blocks")) * 2
    p += (num(r, "def_tds") + num(r, "special_teams_tds")) * 6
    p += num(r, "def_2pt_made") * 2
    return p + ladder(pts_allowed, PA_LADDER) + ladder(yds_allowed, YA_LADDER)


# ── season values ───────────────────────────────────────────────────────
def player_season(year):
    """gsis id -> {'pos':.., 'pts':.., 'games':.., 'name':..} for weeks 1-17."""
    out = {}
    for r in rows(grab("stats_player", f"stats_player_week_{year}.csv")):
        if r.get("season_type") != "REG" or int(float(r["week"])) > LAST_WEEK:
            continue
        pid = r.get("player_id")
        if not pid:
            continue
        pos = (r.get("position") or "").upper()
        pos = "RB" if pos == "FB" else pos
        if pos not in ("QB", "RB", "WR", "TE", "K"):
            continue
        e = out.setdefault(pid, {"pos": pos, "pts": 0.0, "games": 0,
                                 "name": r.get("player_display_name") or r.get("player_name")})
        e["pts"] += kicker_points(r, year) if pos == "K" else offense_points(r, year)
        e["games"] += 1
    return out


def dst_season(year, scores):
    """club code -> {'pts':.., 'games':..}"""
    off, team_rows = {}, []
    for r in rows(grab("stats_team", f"stats_team_week_{year}.csv")):
        if r.get("season_type") != "REG" or int(float(r["week"])) > LAST_WEEK:
            continue
        w = int(float(r["week"]))
        off[(r["team"], w)] = num(r, "passing_yards") + num(r, "rushing_yards")
        team_rows.append((r, w))
    out = defaultdict(lambda: {"pts": 0.0, "games": 0})
    for r, w in team_rows:
        pa = scores.get((str(year), str(w), r["team"]))
        ya = off.get((r["opponent_team"], w))
        if pa is None or ya is None:
            continue
        e = out[r["team"]]
        e["pts"] += dst_points(r, pa, ya)
        e["games"] += 1
    return out


# games.csv keeps the code a club wore at the time; stats_team_week normalises
# every season to the current franchise. Left unreconciled this silently drops
# the three relocated clubs from the defensive pool -- 29 clubs instead of 32,
# which moves the D/ST replacement line.
HISTORIC_CODE = {"STL": "LA", "SD": "LAC", "OAK": "LV", "LAR": "LA", "WSH": "WAS"}


def game_scores():
    s = {}
    for r in rows(grab("schedules", "games.csv")):
        if r.get("game_type") != "REG":
            continue
        home = HISTORIC_CODE.get(r["home_team"], r["home_team"])
        away = HISTORIC_CODE.get(r["away_team"], r["away_team"])
        s[(r["season"], r["week"], away)] = num(r, "home_score")
        s[(r["season"], r["week"], home)] = num(r, "away_score")
    return s


def replacement_from(by_pos):
    """The bar counts the men who start; replacement is the one just past it."""
    rep = {}
    for p, n in BAR.items():
        a = sorted((v for _, v, _ in by_pos.get(p, [])), reverse=True)
        rep[p] = round(a[n], 1) if len(a) > n else (round(a[-1], 1) if a else 0.0)
    return rep


# ── the league's own names ──────────────────────────────────────────────
# Every club, by the mascot the archive uses from 2016 and by the short code it
# used in 2014-2015, mapped to the code nflverse carries. Note that nflverse
# normalises EVERY season to the current 32 franchises -- LA, LAC and LV all
# appear in 2014 -- so a relocation is a naming difference on this side only:
# the archive says "StL D/ST" and "Raiders D/ST", nflverse says LA and LV.
MASCOT_CODE = {
    "bills": "BUF", "dolphins": "MIA", "patriots": "NE", "jets": "NYJ",
    "ravens": "BAL", "bengals": "CIN", "browns": "CLE", "steelers": "PIT",
    "texans": "HOU", "colts": "IND", "jaguars": "JAX", "titans": "TEN",
    "broncos": "DEN", "chiefs": "KC", "raiders": "LV", "chargers": "LAC",
    "cowboys": "DAL", "giants": "NYG", "eagles": "PHI",
    "commanders": "WAS", "redskins": "WAS", "washington": "WAS", "football team": "WAS",
    "bears": "CHI", "lions": "DET", "packers": "GB", "vikings": "MIN",
    "falcons": "ATL", "panthers": "CAR", "saints": "NO", "buccaneers": "TB",
    "cardinals": "ARI", "rams": "LA", "49ers": "SF", "seahawks": "SEA",
}
SHORT_CODE = {
    "ari": "ARI", "atl": "ATL", "bal": "BAL", "buf": "BUF", "car": "CAR",
    "chi": "CHI", "cin": "CIN", "cle": "CLE", "dal": "DAL", "den": "DEN",
    "det": "DET", "gb": "GB", "hou": "HOU", "ind": "IND", "jac": "JAX",
    "jax": "JAX", "kc": "KC", "mia": "MIA", "min": "MIN", "ne": "NE",
    "no": "NO", "nyg": "NYG", "nyj": "NYJ", "oak": "LV", "phi": "PHI",
    "pit": "PIT", "sd": "LAC", "sea": "SEA", "sf": "SF", "stl": "LA",
    "tb": "TB", "ten": "TEN", "was": "WAS", "wsh": "WAS", "la": "LA",
    "lar": "LA", "lac": "LAC", "lv": "LV",
}
def norm_name(n):
    """Fold the spellings two sources can disagree on: middle initials, generation
    suffixes, punctuation. nflverse writes "Charles D. Johnson" where the league
    export writes "Charles Johnson"."""
    n = n.lower().replace(".", " ").replace("'", "").replace("-", " ")
    parts = [t for t in n.split() if t not in ("jr", "sr", "ii", "iii", "iv", "v")]
    parts = [t for i, t in enumerate(parts) if not (0 < i < len(parts) - 1 and len(t) == 1)]
    return " ".join(parts)


def dst_code(name, year):
    """"Broncos D/ST" or "StL D/ST" -> the club code nflverse carries."""
    base = name.replace("D/ST", "").strip().lower()
    return MASCOT_CODE.get(base) or SHORT_CODE.get(base)


def js_to_json(blob):
    """Turn a JS object literal into JSON: quote bare keys, drop trailing commas.

    Done by splitting the text into string and non-string runs first and only
    rewriting the non-string ones -- team names in this file contain commas and
    apostrophes ("2 Gurleys, 1 Kupp", "The Asparagus'"), so a regex over the
    whole blob would corrupt them.
    """
    parts, i, n = [], 0, len(blob)
    while i < n:
        c = blob[i]
        if c in "\"'":
            j, esc = i + 1, False
            while j < n:
                d = blob[j]
                if esc:
                    esc = False
                elif d == "\\":
                    esc = True
                elif d == c:
                    break
                j += 1
            s = blob[i:j + 1]
            if c == "'":                       # JSON has no single-quoted strings
                s = '"' + s[1:-1].replace('"', '\\"') + '"'
            parts.append(("str", s))
            i = j + 1
        else:
            j = i
            while j < n and blob[j] not in "\"'":
                j += 1
            parts.append(("raw", blob[i:j]))
            i = j
    out = []
    for kind, s in parts:
        if kind == "str":
            out.append(s)
        else:
            s = re.sub(r"([{,]\s*)([A-Za-z_$][\w$]*|\d+)\s*:", r'\1"\2":', s)
            s = re.sub(r",(\s*[}\]])", r"\1", s)
            out.append(s)
    return "".join(out)


def load_index_data():
    """ARCH.P, PFR, PFR_EXTRA, DRAFTS -- pulled straight out of index.html."""
    html = INDEX.read_text(encoding="utf-8")

    def const(name):
        # declarations in this file are written both `const X =` and `const X=`
        m = re.search(r"\bconst\s+" + re.escape(name) + r"\s*=", html)
        if not m:
            raise SystemExit(f"{name} not found in index.html")
        j = m.end()
        depth, k, instr, esc = 0, j, None, False
        while k < len(html):
            c = html[k]
            if instr:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == instr:
                    instr = None
            elif c in "\"'":
                instr = c
            elif c in "[{":
                depth += 1
            elif c in "]}":
                depth -= 1
                if depth == 0:
                    return json.loads(js_to_json(html[j:k + 1]))
            k += 1
        raise SystemExit(f"could not read {name}")

    return html, const("ARCH"), const("PFR"), const("PFR_EXTRA"), const("DRAFTS")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="compute and report, don't write")
    ap.add_argument("--verify", action="store_true", help="re-run every check, write nothing")
    args = ap.parse_args()

    html, ARCH, PFR, PFR_EXTRA, DRAFTS = load_index_data()

    # archive name -> pfr id -> gsis id
    first = {}
    for i, p in enumerate(ARCH["P"]):
        first.setdefault(p[0], i)
    pfr_of = {n: PFR[i] for n, i in first.items() if i < len(PFR) and PFR[i]}
    for n, v in PFR_EXTRA.items():
        pfr_of.setdefault(n, v)
    gsis_of_pfr = {r["pfr_id"]: r["gsis_id"] for r in rows(grab("players", "players.csv"))
                   if r.get("pfr_id") and r.get("gsis_id")}
    name_to_gsis = {n: gsis_of_pfr[v] for n, v in pfr_of.items() if v in gsis_of_pfr}
    print(f"joined {len(name_to_gsis)} archive names to nflverse via pfr_id")

    scores = game_scores()

    # every D/ST name the league has ever used -> club code
    mascot = {}
    for p in ARCH["P"]:
        if p and p[1] == "D/ST":
            mascot.setdefault(p[0], None)
    dst_names = set(mascot)
    for y in DRAFTS:
        for lst in DRAFTS[y]["picks"].values():
            for pk in lst:
                if pk[3] == "D/ST":
                    dst_names.add(pk[1])

    out, report = {}, []
    for y in SEASONS:
        pl = player_season(y)
        ds = dst_season(y, scores)
        # Keyed by gsis id, never by name: two men can share a name in one
        # season, and a name-keyed pool silently drops one of them, which moves
        # the replacement line. The subset check below caught exactly that.
        pool = {pid: (e["name"], e["pts"], e["games"], e["pos"]) for pid, e in pl.items()}
        for club, e in ds.items():
            pool["DST:" + club] = (club, e["pts"], e["games"], "D/ST")

        by_pos = defaultdict(list)
        for key, (nm, pts, games, pos) in pool.items():
            by_pos[pos].append((key, pts, games))
        rep = replacement_from(by_pos)

        # what this season's drafts actually name
        drafted = {}
        for lst in DRAFTS[str(y)]["picks"].values():
            for pk in lst:
                drafted[pk[1]] = pk[3]

        keepkeys = set()
        for pos, lst in by_pos.items():
            keepkeys.update(k for k, _, _ in sorted(lst, key=lambda t: -t[1])[:KEEP_PER_POS])

        # plus every drafted man, wherever he finished, held under the name his
        # own draft gave him -- that is the key the board looks him up by
        draft_name, misses, unresolved, by_name_fallback, zeros = {}, [], [], [], []
        for name, dpos in drafted.items():
            if dpos == "D/ST":
                code = dst_code(name, y)
                if not code:
                    unresolved.append(name)
                    continue
                key = "DST:" + code
            else:
                key = name_to_gsis.get(name)
                if not key or key not in pool:
                    # No pfr id, or one that nflverse does not carry. Fall back
                    # to the name, but only within the position he was drafted
                    # at and only if it is unambiguous -- the one man this
                    # catches, Charles Johnson 2015, is a name collision with a
                    # defensive end, which is exactly the case a blind name
                    # match would get wrong.
                    want = norm_name(name)
                    hits = [k for k, v in pool.items()
                            if norm_name(v[0]) == want and v[3] == dpos]
                    if len(hits) == 1:
                        key = hits[0]
                        by_name_fallback.append(name)
            if not key or key not in pool:
                # He was drafted and recorded no NFL season at all -- suspended,
                # injured in August, retired in the summer, held out. That is a
                # real outcome for the pick and it is baked as one: nothing
                # scored, no games played. Leaving him out instead would make
                # the board unable to tell "returned nothing" from "unknown".
                misses.append(name)
                zeros.append(name)
                continue
            keepkeys.add(key)
            draft_name[key] = name
        if unresolved:
            raise SystemExit(f"{y}: could not resolve these defences to a club: {unresolved}")

        # Emit by position. Where a name appears twice the duplicate is
        # disambiguated, so a lookup by name can only ever land on the man who
        # was actually drafted; the other row is pool-only and is there to hold
        # the replacement line where it belongs.
        emit, seen = defaultdict(list), defaultdict(set)
        for pos in by_pos:
            ordered = sorted((k for k, _, _ in by_pos[pos] if k in keepkeys),
                             key=lambda k: (-pool[k][1], k not in draft_name))
            for k in ordered:
                nm = draft_name.get(k, pool[k][0])
                if nm in seen[pos]:
                    nm = f"{nm} ({len(seen[pos])})"
                seen[pos].add(nm)
                emit[pos].append([nm, round(pool[k][1], 1), pool[k][2]])
        for name in zeros:
            emit[drafted[name]].append([name, 0.0, 0])
        out[y] = {"rep": rep, "p": dict(emit)}

        # ADR 0015 bakes a subset to keep the file small; that saving is only
        # allowed if it cannot change an answer, so prove the line the browser
        # will draw from the subset is the line drawn over everyone.
        got = replacement_from({p_: [(n, v, g) for n, v, g in lst] for p_, lst in emit.items()})
        if got != rep:
            raise SystemExit(f"{y}: baked subset gives {got}, full population gives {rep}"
                             f" -- raise KEEP_PER_POS")
        n_rows = sum(len(v) for v in out[y]["p"].values())
        report.append((y, n_rows, len(misses), misses[:4], rep))
        if by_name_fallback:
            print(f"    {y}: joined by name at the drafted position: "
                  f"{', '.join(by_name_fallback)}")

    print(f"\n{'year':>5} {'baked rows':>11} {'drafted men with no NFL season':>32}   replacement line")
    for y, n, nm, sample, rep in report:
        line = " ".join(f"{p}{rep[p]:.0f}" for p in POSITIONS if p in rep)
        print(f"{y:>5} {n:>11} {nm:>32}   {line}"
              + (f"   e.g. {', '.join(sample)}" if sample else ""))

    blob = json.dumps({str(y): out[y] for y in SEASONS}, separators=(",", ":"))
    print(f"\nPLAYER_VALUE is {len(blob):,} bytes")

    if args.verify or args.dry_run:
        print("\n(nothing written)")
        return

    new_html, before, after = write_back(html, blob)
    INDEX.write_text(new_html, encoding="utf-8")
    print(f"\nindex.html {before:,} -> {after:,} bytes ({after - before:+,})")
    print("Review with `git diff` before committing (ADR 0001/0002).")


HEADER = """/* ── What every drafted man's season was actually worth ──────────────
   Whole-season fantasy points under this league's own rulebook for that
   year, weeks 1-17, for every player drafted in it plus the top {keep} at
   each position -- which is everything the board needs to redraw the
   replacement line and the going-rate curve for itself (ADR 0015).

   Computed by refresh-players.py from nflverse's public weekly stats, not
   from the league export: the export only records points while a man sat
   on somebody's roster, and 42% of drafted players spent part of a season
   on nobody's. Re-scoring 2018-2025 this way reproduces the export's own
   points for 23,668 player-weeks at 100.0%.

   `rep` is the replacement line -- the man just past the startable bar at
   each position -- computed over EVERY NFL player, then checked against
   the baked subset so the saving cannot move an answer. Each row is
   [name, points, games played]; games is printed on the board because a
   pick that returned nothing because he never played is a different story
   from one that played and was bad, and the board states the fact rather
   than diagnosing the cause.

   Defences are within about 12% rather than exact -- see the script's
   header for why, and ADR 0015 for why that keeps them on this board and
   off Steals & Busts. */
"""


def strip_preceding_comments(html, decl_start, max_blocks=5):
    """Return the start index after stripping the /* ... */ blocks that sit
    immediately before html[decl_start:].

    Deliberately NOT a regex over the whole document -- see the same function
    in refresh-adp.py / refresh-tiers.py for the run where a lazy wildcard in a
    repeated group backtracked across the entire preamble and deleted ~2MB.
    """
    pos = decl_start
    stripped = 0
    while stripped < max_blocks:
        end = pos
        while end > 0 and html[end - 1] in " \t\r\n":
            end -= 1
        if end < 2 or html[end - 2:end] != "*/":
            break
        open_idx = html.rfind("/*", 0, end)
        if open_idx == -1 or "*/" in html[open_idx + 2:end - 2]:
            break
        pos = open_idx
        stripped += 1
    return pos


def write_back(html, blob):
    before = len(html.encode("utf-8"))
    block = HEADER.format(keep=KEEP_PER_POS) + f"const PLAYER_VALUE = {blob};\n"

    m = re.search(r"\bconst\s+PLAYER_VALUE\s*=", html)
    if m:
        start = strip_preceding_comments(html, m.start())
        end = html.index(";", m.end())
        while end + 1 < len(html) and html[end + 1] == "\n":
            end += 1
        new = html[:start] + block + html[end + 1:]
    else:
        anchor = re.search(r"\bconst\s+DRAFT_TOTALS_2014_2017\s*=", html)
        if not anchor:
            raise SystemExit("no PLAYER_VALUE and no anchor to insert before")
        start = strip_preceding_comments(html, anchor.start())
        new = html[:start] + block + "\n" + html[start:]

    after = len(new.encode("utf-8"))
    grew = after - before
    # A write-back on a 2.6MB file must never be trusted on faith: bound the
    # damage a bug can do before it reaches disk.
    if not (0 < grew < 400_000) and m is None:
        raise SystemExit(f"refusing to write: size change {grew:+,} bytes is out of range")
    if m is not None and abs(grew) > 400_000:
        raise SystemExit(f"refusing to write: size change {grew:+,} bytes is out of range")
    if "const PLAYER_VALUE =" not in new or new.count("const DRAFTS =") != 1:
        raise SystemExit("refusing to write: the result does not look like index.html")
    return new, before, after


if __name__ == "__main__":
    main()
