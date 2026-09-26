"""Write the current season into index.html as LIVE_2026.

Input is .espn-raw/live-2026.json, the compact extract taken from ESPN in a
signed-in browser tab (the league is private, so the API only answers where the
ESPN session already lives — see HANDOFF). This script only reshapes and embeds
it; it never talks to ESPN itself.

    python refresh-live.py            # rewrite the block between the markers
    python refresh-live.py --check    # report what would change, write nothing
"""
import json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / ".espn-raw" / "live-2026.json"
SITE = HERE / "index.html"
START, END = "/*LIVE_2026:start*/", "/*LIVE_2026:end*/"

# ESPN account names that differ from the name the league knows the manager by.
ALIAS = {"Taksin Thaweechok": "Leo Thaweechok"}

raw = json.loads(SRC.read_text(encoding="utf-8"))
live = {
    "season": raw["season"], "week": raw["week"], "reg": raw["reg"],
    "playoffTeams": raw["playoffTeams"], "fetched": raw["fetched"],
    "divs": raw["divs"],
    # [id, team name, manager, W, L, T, PF, PA, division, seed]
    "teams": [[t[0], t[1], ALIAS.get(t[2], t[2]), *t[3:]] for t in raw["teams"]],
    # [week, home id, home pts, away id, away pts]
    "sch": raw["sch"],
    # [round, pick in round, team id, player, pos, NFL club, keeper]
    "draft": raw["draft"],
    # team id -> [[player, pos, NFL club, lineup slot]]
    "rosters": raw["rosters"],
}
block = START + "\nconst LIVE_2026 = " + json.dumps(live, ensure_ascii=False, separators=(",", ":")) + ";\n" + END

html = SITE.read_text(encoding="utf-8")
if START in html:
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: block, html, count=1, flags=re.S)
else:
    hook = "/* ══ Hub (design 3a) "
    assert html.count(hook) == 1, "hub marker not found"
    new = html.replace(hook, block + "\n\n" + hook)

if "--check" in sys.argv:
    print("unchanged" if new == html else "would update LIVE_2026 (week %d, fetched %s)" % (live["week"], live["fetched"]))
else:
    SITE.write_text(new, encoding="utf-8", newline="")
    print("LIVE_2026 written: week %d, %d teams, %d picks, fetched %s"
          % (live["week"], len(live["teams"]), len(live["draft"]), live["fetched"]))
