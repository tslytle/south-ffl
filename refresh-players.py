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

Two things are written per season. `rep`/`p` are the whole-season values the
Draft Rankings board reads. `wrep` is a WEEKLY replacement line -- what the man
just past the startable bar scored in that week, at each position -- and the
waiver board reads it (ADR 0019). It is baked for the same reason the season
values are: it needs NFL-wide weekly stats, and the league export only records
the men somebody was holding. Only seasons with weekly rosters get one.

Fantasy points are computed here from raw stats under *this league's* rulebook
per season -- not taken from anyone else's arithmetic. That is checkable, and
--verify checks it: it walks every roster-week the league export recorded,
2018-2025, re-scores that man from raw nflverse stats and compares. Measured
2026-08-15: 22,417 of 22,419 skill player-weeks agree exactly (99.99%), and the
run fails if that rate drops below SKILL_FLOOR.

Six rules are not on the league's scoring page and were recovered from the
residuals of that check:
  * a BLOCKED field goal counts as a miss (nflverse files it apart from
    fg_missed_*), which was 52 of the 76 original disagreements;
  * a return touchdown and a touchdown on your own recovered fumble both pay
    6 and are neither rushing nor receiving scores;
  * a kicker still scores whatever he does with the ball in his hands --
    Matt Prater threw a touchdown off a fake in 2018;
  * a missed PAT costs nothing;
  * yards allowed are NET of sack yardage -- see yards_allowed();
  * a fumble returned for a touchdown is a defensive score that nflverse keeps
    out of def_tds -- see dst_points().

The last two are the 2026-08-15 additions and they are the defensive ones.

The two player-weeks that still disagree are source differences rather than
rulebook gaps, and are recorded here so they are not re-investigated:
  * Caleb Williams 2025 wk6, +0.50. He lost 5 yards recovering his own fumble;
    ESPN charged that to his rushing yards, nflverse files it in
    fumble_recovery_yards_own. Neither is wrong, they just count it in
    different columns.
  * Tony Pollard 2020 wk17, +0.10. One yard, and nflverse carries a stat
    correction that ESPN's frozen box score does not.

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

Defences are a known and bounded exception, but a much smaller one than this
file used to claim. The old note blamed the gap on nflverse carrying ~11% more
sacks and ~23% more fumble recoveries than ESPN's feed, and put a D/ST season
total within about 12%. The 12% was right (measured: 12.8% mean absolute error
per club-season) and the diagnosis was wrong. Running the weekly check for the
first time showed the residual was almost entirely one-sided -- computed was
never meaningfully HIGH -- which is the signature of missing categories, not of
a noisier feed. The two missing rules are the last two above. With them a club
season lands within **1.9%** mean absolute error, and 91.5% of club-weeks are
exact to the point.

What remains is one yards-allowed ladder step in a single game, on about 8% of
club-weeks, and its cause is not isolated. So ADR 0015's disposition still
stands on its own terms -- defences in Draft Rankings, out of Steals & Busts --
it just rests on a tenth of the error it was written for.

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


def yards_allowed(r):
    """What one club gained, as the yards-allowed ladder means it.

    The ladder is fed TOTAL NET yards, and net yards are passing and rushing
    less what the sacks took back. nflverse keeps sack yardage in its own column
    rather than netting it out of passing_yards, so summing the two gives a club
    more yards than it gained and drops the defence a ladder step. That was the
    larger half of the defensive gap: it alone moved the exact-agreement rate
    from 63% to 88%, and it is a definition rather than a fitted correction.
    """
    return (num(r, "passing_yards") + num(r, "rushing_yards")
            - abs(num(r, "sack_yards_lost")))


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
    # A fumble returned for a touchdown is a defensive score, and nflverse files
    # it apart from def_tds -- which carries interception returns. Recovered from
    # the residuals of --verify, exactly as the four player rules above were: it
    # was 65 of the disagreements on its own. The same column also holds an
    # OFFENCE's touchdown on its own recovered fumble (the team file aggregates
    # both sides), which is why it is capped at the number of opponent fumbles
    # this defence actually recovered -- uncapped, it hands nine defences six
    # points for a touchdown their offence scored.
    p += min(num(r, "fumble_recovery_tds"), num(r, "fumble_recovery_opp")) * 6
    p += num(r, "def_2pt_made") * 2
    return p + ladder(pts_allowed, PA_LADDER) + ladder(yds_allowed, YA_LADDER)


# ── season values ───────────────────────────────────────────────────────
SCORED = ("QB", "RB", "WR", "TE", "K")


def player_weeks(year, league_pos=None):
    """Yield (gsis id, week, position, name, points) for weeks 1-17.

    `league_pos` maps a gsis id to the position THIS LEAGUE drafted him at, and
    it is what stops nflverse's own position label deciding whether a man's
    production exists. nflverse files a two-way player at his defensive
    position -- Travis Hunter is a CB there -- so the position filter alone
    dropped every catch he made in 2025 and the board baked him as a pick that
    never played. He played seven games and was bad, which is a different fact
    and the one the board exists to state.
    """
    for r in rows(grab("stats_player", f"stats_player_week_{year}.csv")):
        if r.get("season_type") != "REG" or int(float(r["week"])) > LAST_WEEK:
            continue
        pid = r.get("player_id")
        if not pid:
            continue
        pos = (r.get("position") or "").upper()
        pos = "RB" if pos == "FB" else pos
        if pos not in SCORED:
            # Only a man this league actually drafted is rescued this way; the
            # pool stays otherwise as nflverse files it, so no defender wanders
            # into the receiver pool and moves the replacement line.
            pos = (league_pos or {}).get(pid)
            if pos not in SCORED:
                continue
        pts = kicker_points(r, year) if pos == "K" else offense_points(r, year)
        yield pid, int(float(r["week"])), pos, \
            (r.get("player_display_name") or r.get("player_name")), pts


def player_season(year, league_pos=None):
    """gsis id -> {'pos':.., 'pts':.., 'games':.., 'name':..} for weeks 1-17."""
    out = {}
    for pid, _w, pos, name, pts in player_weeks(year, league_pos):
        e = out.setdefault(pid, {"pos": pos, "pts": 0.0, "games": 0, "name": name})
        e["pts"] += pts
        e["games"] += 1
    return out


def dst_weeks(year, scores):
    """(club code, week) -> points."""
    off, team_rows = {}, []
    for r in rows(grab("stats_team", f"stats_team_week_{year}.csv")):
        if r.get("season_type") != "REG" or int(float(r["week"])) > LAST_WEEK:
            continue
        w = int(float(r["week"]))
        off[(r["team"], w)] = yards_allowed(r)
        team_rows.append((r, w))
    out = {}
    for r, w in team_rows:
        pa = scores.get((str(year), str(w), r["team"]))
        ya = off.get((r["opponent_team"], w))
        if pa is None or ya is None:
            continue
        out[(r["team"], w)] = dst_points(r, pa, ya)
    return out


def dst_season(year, scores):
    """club code -> {'pts':.., 'games':..}"""
    out = defaultdict(lambda: {"pts": 0.0, "games": 0})
    for (club, _w), pts in dst_weeks(year, scores).items():
        e = out[club]
        e["pts"] += pts
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


def wire_replacement(year, scores, league_pos=None):
    """week -> {pos: what the man just past the startable bar scored THAT week}.

    The waiver board asks what a pickup gave you "above what was sitting there
    for free", and until 2026-08-15 it answered that from the ROSTERED pool --
    the (bar+1)th best man the league happened to be holding. That pool cannot
    see a free agent, which is the one thing the question is about. It is also
    biased in a single direction: the pool is a subset of the league, so the
    man just past the bar inside it is never better and usually worse than the
    man just past the bar in the NFL. Every wire value computed against it was
    therefore too generous, and most of all at exactly the positions with the
    shallowest pools.

    Drawn here over EVERY player who took the field that week instead, which is
    the same definition `replacement_from()` uses for the season and the same
    bar. That makes the two boards agree on what replacement means, rather than
    each having its own.

    A thin week stays thin on purpose -- byes cut the pool and the replacement
    line drops with them, which is the "bye-week wasteland" the board's own
    header asks for.
    """
    byw = defaultdict(lambda: defaultdict(list))
    for pid, w, pos, _nm, pts in player_weeks(year, league_pos):
        byw[w][pos].append(pts)
    for (_club, w), pts in dst_weeks(year, scores).items():
        byw[w]["D/ST"].append(pts)
    out = {}
    for w in sorted(byw):
        rep = {}
        for p, n in BAR.items():
            a = sorted(byw[w].get(p, []), reverse=True)
            if not a:
                continue
            rep[p] = round(a[n] if len(a) > n else a[-1], 1)
        out[str(w)] = rep
    return out


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


# ── the check ───────────────────────────────────────────────────────────
# Skill agreement is expected to be total: the rulebook either reproduces the
# league's own arithmetic or it does not. The floor is set just below the
# measured rate so an ordinary source correction does not fail the run, while a
# rulebook regression -- which moves hundreds of weeks at once -- does.
SKILL_FLOOR = 0.999
# A rate floor cannot see a small defect: disabling the two-way-player rescue
# costs seven player-weeks out of 22,419 and clears 99.9% comfortably, which is
# how Travis Hunter sat wrong on the board for a season. So the two remaining
# disagreements are NAMED, and any skill disagreement that is not one of these
# fails the run however few there are. Both are documented in the header; a new
# one is either a rulebook regression or a fact about the wire worth reading.
KNOWN_SKILL_DIFFS = {
    (2020, 17, "Tony Pollard"),      # own-fumble recovery yardage, +0.10
    (2025, 6, "Caleb Williams"),     # own-fumble recovery yardage, +0.50
}
# Defences cannot reach that and are not asked to. The floor sits well under the
# measured 91.5% but far above the 63% the rulebook scored before the two
# defensive rules were found.
DST_FLOOR = 0.85
# The rate alone is too blunt to guard the defensive rules: dropping the
# fumble-return touchdown costs only 3.7 points of it and clears the floor.
# Bias is the sharp instrument, and it is the one that found both rules. A
# defence that is scored under a complete rulebook is wrong in both directions
# about equally; a missing category can only ever subtract, so it shows up as a
# one-sided mean long before it dents the exact-agreement rate. Measured -0.11;
# dropping the fumble-return TD alone takes it past -0.35.
DST_BIAS_MAX = 0.25


def roster_weeks(rec):
    """Yield (week, archive player index, the points the export recorded).

    Mirrors rosterAt() in index.html, which is the only definition of this
    shape: week 1 is a full snapshot, every later week is a delta of adds,
    drops and slot moves, and each week's `p` map carries that week's points.
    A man on the roster with no entry in `p` scored nothing recorded and is
    skipped rather than read as a zero.
    """
    if rec.get("snap"):
        return
    wks = sorted(int(w) for w in rec["w"])
    cur, i = {}, 0
    for w in range(1, (max(wks) if wks else 0) + 1):
        while i < len(wks) and wks[i] <= w:
            step = rec["w"][str(wks[i])]
            if isinstance(step, list):
                cur = {r[0]: r[3] for r in step}
            else:
                for pid in step["d"]:
                    cur.pop(pid, None)
                for r in step["a"]:
                    cur[r[0]] = r[3]
                cur = {pid: None for pid in cur}
                for pid, v in (step.get("p") or {}).items():
                    if int(pid) in cur:
                        cur[int(pid)] = v
            i += 1
        for pid, pts in cur.items():
            if pts is not None:
                yield w, pid, pts


def verify_weekly(ARCH, DRAFTS, gsis_of_idx, name_to_gsis, scores):
    """Re-score every roster-week the league recorded and compare to its points.

    This is the claim the whole board rests on -- that fantasy points computed
    here from raw nflverse stats are this league's own points -- and it is the
    only part of the pipeline that can be checked against an authority rather
    than against itself. The league export holds what ESPN actually paid each
    man each week; nothing else here does.

    Skill and defence are reported apart because they are not the same claim.
    Skill scoring is exact and any disagreement is a defect until explained.
    Defensive scoring is reconstructed from public box scores and is not exact:
    it is reported with its residual so the gap is a measured number rather
    than an assurance.
    """
    tol = 0.005
    tot = defaultdict(int)
    dst_resid, skill_bad, unjoined = [], [], defaultdict(int)

    print(f"\n{'year':>5} {'skill wks':>10} {'exact':>8} {'rate':>7}    "
          f"{'D/ST wks':>9} {'exact':>7} {'rate':>7} {'mean resid':>11}")
    for y in SEASONS:
        S = ARCH["S"].get(str(y))
        if not S or S.get("static") or not S.get("teams"):
            continue    # 2014-2017 are stored as standings only, with no weeks
        drafted = {}
        for lst in DRAFTS[str(y)]["picks"].values():
            for pk in lst:
                drafted[pk[1]] = pk[3]
        league_pos = {name_to_gsis[n]: p for n, p in drafted.items()
                      if p != "D/ST" and n in name_to_gsis}
        pw = defaultdict(float)
        for pid, w, _pos, _nm, pts in player_weeks(y, league_pos):
            pw[(pid, w)] += pts
        dw = dst_weeks(y, scores)

        n = {"skill": 0, "dst": 0}
        ok = {"skill": 0, "dst": 0}
        resid = []
        for rec in S["teams"].values():
            for w, idx, export_pts in roster_weeks(rec):
                name, pos = ARCH["P"][idx][0], ARCH["P"][idx][1]
                if pos == "D/ST":
                    code = dst_code(name, y)
                    if not code or (code, w) not in dw:
                        unjoined[name] += 1
                        continue
                    got, kind = dw[(code, w)], "dst"
                else:
                    gid = gsis_of_idx.get(idx)
                    if gid is None:
                        unjoined[name] += 1
                        continue
                    got, kind = pw.get((gid, w), 0.0), "skill"
                n[kind] += 1
                if abs(got - export_pts) <= tol:
                    ok[kind] += 1
                elif kind == "dst":
                    resid.append(got - export_pts)
                else:
                    skill_bad.append((y, w, name, pos, export_pts, round(got, 2)))
        dst_resid += resid
        for k in ("skill", "dst"):
            tot[k] += n[k]
            tot[k + "_ok"] += ok[k]
        mean = sum(resid) / n["dst"] if n["dst"] else 0.0
        print(f"{y:>5} {n['skill']:>10} {ok['skill']:>8} "
              f"{100 * ok['skill'] / max(n['skill'], 1):>6.2f}%    "
              f"{n['dst']:>9} {ok['dst']:>7} "
              f"{100 * ok['dst'] / max(n['dst'], 1):>6.1f}% {mean:>+11.2f}")

    rate = tot["skill_ok"] / max(tot["skill"], 1)
    print(f"\nSkill: {tot['skill_ok']:,} of {tot['skill']:,} player-weeks reproduce the "
          f"league's own points exactly ({100 * rate:.2f}%).")
    surprises = [d for d in skill_bad if (d[0], d[1], d[2]) not in KNOWN_SKILL_DIFFS]
    for y, w, name, pos, exp, got in skill_bad:
        tag = "" if (y, w, name) in KNOWN_SKILL_DIFFS else "   <- NOT A KNOWN DIFFERENCE"
        print(f"    {y} wk{w:<3} {name:<24} {pos:<3} export {exp:>7}  here {got:>7}"
              f"  {got - exp:+.2f}{tag}")
    missing = KNOWN_SKILL_DIFFS - {(d[0], d[1], d[2]) for d in skill_bad}
    for y, w, name in sorted(missing):
        print(f"    {y} wk{w} {name} now agrees -- drop it from KNOWN_SKILL_DIFFS")
    dmean = sum(dst_resid) / max(tot["dst"], 1)
    print(f"\nD/ST: {tot['dst_ok']:,} of {tot['dst']:,} club-weeks exact "
          f"({100 * tot['dst_ok'] / max(tot['dst'], 1):.1f}%), mean residual "
          f"{dmean:+.2f} points per club-week against a mean score of about 6.8.")
    print("      The remainder is one yards-allowed ladder step in a single game"
          "\n      and the cause is not isolated. At this size defences are judged"
          "\n      on Steals & Busts as well as Draft Rankings (ADR 0017); at the"
          "\n      12% it used to be, ADR 0015 kept them off.")
    if unjoined:
        top = sorted(unjoined.items(), key=lambda t: -t[1])[:4]
        print(f"\nUnjoined: {sum(unjoined.values())} roster-weeks over {len(unjoined)} men "
              f"with no nflverse id, e.g. {', '.join(f'{k} x{v}' for k, v in top)}")

    drate = tot["dst_ok"] / max(tot["dst"], 1)
    bad = []
    if surprises:
        bad.append(f"{len(surprises)} skill player-week(s) disagree that are not in "
                   f"KNOWN_SKILL_DIFFS, the first being "
                   f"{surprises[0][2]} {surprises[0][0]} wk{surprises[0][1]}")
    if rate < SKILL_FLOOR:
        bad.append(f"skill agreement {100 * rate:.2f}% is below its "
                   f"{100 * SKILL_FLOOR:.1f}% floor")
    if drate < DST_FLOOR:
        bad.append(f"D/ST agreement {100 * drate:.1f}% is below its "
                   f"{100 * DST_FLOOR:.0f}% floor")
    if abs(dmean) > DST_BIAS_MAX:
        bad.append(f"D/ST residual is one-sided at {dmean:+.2f} points per club-week "
                   f"(limit {DST_BIAS_MAX}), which is the shape of a missing category")
    if bad:
        raise SystemExit("\nFAILED: " + "; ".join(bad) + " -- the rulebook has regressed.")
    print(f"\nVerified. Skill holds above {100 * SKILL_FLOOR:.1f}%, D/ST above "
          f"{100 * DST_FLOOR:.0f}%, and the D/ST residual is two-sided.")


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

    # The weekly check walks rosters, which reference players by their index in
    # ARCH.P rather than by name, so it needs the join keyed that way -- two men
    # can share a name and the name key keeps only the first.
    gsis_of_idx = {}
    for i, p in enumerate(ARCH["P"]):
        pfr = (PFR[i] if i < len(PFR) else "") or PFR_EXTRA.get(p[0], "")
        if pfr in gsis_of_pfr:
            gsis_of_idx[i] = gsis_of_pfr[pfr]

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
        # what this season's drafts actually name, resolved before scoring so a
        # man nflverse files at a defensive position is still scored at the one
        # he was drafted at rather than dropped
        drafted = {}
        for lst in DRAFTS[str(y)]["picks"].values():
            for pk in lst:
                drafted[pk[1]] = pk[3]
        league_pos = {name_to_gsis[n]: p for n, p in drafted.items()
                      if p != "D/ST" and n in name_to_gsis}

        pl = player_season(y, league_pos)
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
        # Weekly replacement for the waiver board. Only the seasons that have
        # weekly rosters can use it, and those are the only ones it is baked
        # for -- 2014-2017 are standings-only and no wire board runs on them.
        out[y] = {"rep": rep, "p": dict(emit)}
        if not (ARCH["S"].get(str(y)) or {}).get("static", 1):
            out[y]["wrep"] = wire_replacement(y, scores, league_pos)

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

    if args.verify:
        verify_weekly(ARCH, DRAFTS, gsis_of_idx, name_to_gsis, scores)

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
   points for 22,417 of 22,419 skill player-weeks (99.99%); the two that
   differ are columns the two sources file differently, not scoring.

   `rep` is the replacement line -- the man just past the startable bar at
   each position -- computed over EVERY NFL player, then checked against
   the baked subset so the saving cannot move an answer. Each row is
   [name, points, games played]; games is printed on the board because a
   pick that returned nothing because he never played is a different story
   from one that played and was bad, and the board states the fact rather
   than diagnosing the cause.

   Defences are within about 2% rather than exact -- see the script's
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
