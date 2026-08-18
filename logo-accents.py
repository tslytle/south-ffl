"""
logo-accents.py -- derive OWNER_ACCENT from the marks embedded in index.html.

Run it when a manager's logo changes, when a manager joins or leaves, or when
the elevation tokens move:

    python logo-accents.py            # print the table and the JS block
    python logo-accents.py --check    # verify the block in index.html matches

Needs Pillow, and nothing else. It reads index.html for OWNER_LOGO, so there
is no second copy of anything to keep in step.

THE RULE IS FIDELITY. A manager's accent is his own mark's ink. Two things,
and only these two, are allowed to move it:

  1. The contrast floor. 3.25:1 against the worst ground in each theme --
     --raise in dark, --soft in light -- with headroom over ADR 0022's 3:1.
     Gating the light value on white is the trap: white is the EASIEST ground
     it ever sits on. This is what lightens a deep ink in dark mode, and it is
     why there are two values: midnight green and shield navy are too dark to
     sit on a navy ground, so dark gets a teal and a periwinkle of the same
     hue and light gets the ink itself.

  2. Two men cannot wear one colour. Eight marks fall in the red-to-gold arc
     and three are literally the same stock clip-art. That one family fans
     out around its own centre, FAN_STEP degrees between neighbours, and no
     manager drifts more than MAX_DRIFT off his own ink -- the drift is spent
     inside the family that caused it rather than charged to the league. Where
     hue cannot separate a pair, chroma does, which happens to be faithful:
     the duller of two identical reds gets the duller accent.

An earlier version of this file did the opposite -- seventeen slots evenly
spaced, assigned by Hungarian optimum -- on the argument that six red marks
in one narrow band cannot be told apart. The objection is real; the answer
was wrong. Even spacing buys separation by spending the only thing an accent
is FOR: it put Colin Moore, whose mark is red, in purple.

SAMPLING, which is the part worth reusing. Rank a raster's pixels by count
ALONE and you get what the mark is mostly made of -- for a photograph, skin
and backdrop. Rank by count x saturation and you get what it is ABOUT. Alen's
Eagles jersey is 447 pixels and wins only under the second rule. SVGs are read
as their commonest saturated hex, which needs no such trick.

Four marks cannot be sampled correctly at all and carry HAND corrections, each
checked against the real artwork -- see HAND below. Five managers have no ink
to honour (three monochrome marks, two with no mark); they take the emptiest
hues left by farthest-point insertion, and they are the only accents here
chosen rather than measured.
"""
import base64, collections, colorsys, io, itertools, json, os, re, sys

SRC_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

# marks whose sampled ink is wrong, and why. The value is the ink to use.
HAND = {
    "Alen Huseinbegovic": ("#004C54", "photo; commonest ink is skin and backdrop. "
                                      "The mark is a man in an Eagles jersey -- 447px of it"),
    "Justin DeCesare":    ("#786BAD", "the purple missed the 30% saturation gate by two points"),
    "Tate Grainger":      ("#FB4F14", "monochrome mark; its #f0f is a placeholder, not ink. "
                                      "Who Dey -> Bengals burnt orange"),
    "Adam Boggess":       ("#FAE696", "the straw hat, not the paper behind it"),
}
# marks with no colour in them at all
NO_INK = ["Leo Thaweechok", "Michael Boggess", "Nick Drake", "RC Muncy", "Azer Sabanovic"]

DARK_WORST, LIGHT_WORST, GATE = "#2D3A59", "#EAEEF5", 3.25
MAX_DRIFT, FAN_STEP, CLUSTER = 14.0, 11.0, 20.0

def read_logos():
    html = io.open(SRC_FILE, encoding="utf-8").read()
    i = html.index("const OWNER_LOGO = {")
    return json.loads(html[html.index("{", i):html.index("};", i) + 1])

def sample(uri):
    """the ink a mark is about: count x saturation for rasters, commonest
       saturated hex for vectors. None if the mark has no colour in it."""
    m = re.match(r"^data:([^;]+);base64,(.*)$", uri, re.S)
    if not m: return None
    mime, raw = m.group(1), base64.b64decode(m.group(2))
    usable = lambda h, s, l: s >= 0.25 and 0.12 <= l <= 0.90
    if mime == "image/svg+xml":
        bins = collections.Counter()
        for hx in re.findall(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", raw.decode("utf-8", "replace")):
            if len(hx) == 3: hx = "".join(c * 2 for c in hx)
            r, g, b = (int(hx[i:i+2], 16) for i in (0, 2, 4))
            h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
            if usable(h, s, l): bins[(r, g, b)] += 1
        if not bins: return None
        top = bins.most_common(1)[0][0]
        hue = lambda c: colorsys.rgb_to_hls(*[x/255 for x in c])[0] * 360
        lit = lambda c: colorsys.rgb_to_hls(*[x/255 for x in c])[1]
        th = hue(top)
        # SHADOW IS NOT INK. Clip art shades by darkening the same hue, and a
        # hex count counts MARKUP, not area -- so a shadow can outvote the
        # colour the mark is actually drawn in. Among the entries in the
        # winner's own hue family, take the lightest. Christian's mark is
        # #BE202E with #821429 shading under it and counting alone chose the
        # shading; Braxton's ties four to four and chose it too.
        fam = [c for c in bins if min(abs(hue(c)-th), 360-abs(hue(c)-th)) < 12]
        return "#%02X%02X%02X" % max(fam, key=lit)
    from PIL import Image
    im = Image.open(io.BytesIO(raw)).convert("RGBA"); im.thumbnail((200, 200))
    scored = collections.Counter()
    for r, g, b, a in im.getdata():
        if a < 200: continue
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        if usable(h, s, l): scored[(r//20, g//20, b//20)] += s
    if not scored: return None
    q = scored.most_common(1)[0][0]
    return "#%02X%02X%02X" % (q[0]*20+10, q[1]*20+10, q[2]*20+10)

LOGOS = read_logos()
SRC = {}
for owner, uri in LOGOS.items():
    if owner in NO_INK: continue
    SRC[owner] = HAND[owner][0] if owner in HAND else sample(uri)
    if SRC[owner] is None:
        sys.exit("no ink sampled for %s and no hand correction: add one or list "
                 "the manager in NO_INK" % owner)
for owner in HAND:
    SRC.setdefault(owner, HAND[owner][0])
def hex2rgb(h): return tuple(int(h[1+2*i:3+2*i],16) for i in range(3))
def rgb2hex(r): return "#%02X%02X%02X"%tuple(max(0,min(255,round(c))) for c in r)
def hsl(h):
    r,g,b=[c/255 for c in hex2rgb(h)];H,L,S=colorsys.rgb_to_hls(r,g,b);return H*360,S,L
def fromhsl(H,S,L):
    r,g,b=colorsys.hls_to_rgb((H%360)/360,max(0,min(1,L)),max(0,min(1,S)));return rgb2hex((r*255,g*255,b*255))
def lum(h):
    f=lambda c:(c/255)/12.92 if c/255<=0.03928 else (((c/255)+0.055)/1.055)**2.4
    r,g,b=hex2rgb(h);return .2126*f(r)+.7152*f(g)+.0722*f(b)
def ratio(a,b):
    x,y=lum(a),lum(b);return (max(x,y)+.05)/(min(x,y)+.05)
def lab(h):
    r,g,b=[c/255 for c in hex2rgb(h)]
    f=lambda c:c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
    r,g,b=f(r),f(g),f(b)
    X,Y,Z=(r*.4124+g*.3576+b*.1805)/.95047,r*.2126+g*.7152+b*.0722,(r*.0193+g*.1192+b*.9505)/1.08883
    k=lambda t:t**(1/3) if t>0.008856 else 7.787*t+16/116
    X,Y,Z=k(X),k(Y),k(Z);return (116*Y-16,500*(X-Y),200*(Y-Z))
def dE(a,b): return sum((x-y)**2 for x,y in zip(lab(a),lab(b)))**0.5
def arc(a,b):
    d=abs(a-b)%360;return min(d,360-d)

items = sorted(SRC.items(), key=lambda kv: hsl(kv[1])[0])
hs=[hsl(v)[0] for _,v in items]
start=max(range(len(hs)), key=lambda i:(hs[i]-hs[i-1])%360)
items=items[start:]+items[:start]
groups,cur=[],[items[0]]
for prev,nxt in zip(items,items[1:]):
    if arc(hsl(prev[1])[0],hsl(nxt[1])[0])<CLUSTER: cur.append(nxt)
    else: groups.append(cur);cur=[nxt]
groups.append(cur)

target={}
for g in groups:
    k=len(g)
    if k==1: target[g[0][0]]=hsl(g[0][1])[0]; continue
    base=[hsl(v)[0] for _,v in g]; b0=base[0]
    unrolled=[b0+((h-b0)%360) for h in base]
    centre=sum(unrolled)/k; span=FAN_STEP*(k-1)
    for i,(name,_) in enumerate(g):
        want=centre-span/2+i*span/(k-1)
        own=unrolled[i]
        target[name]=max(own-MAX_DRIFT,min(own+MAX_DRIFT,want))%360

def solve(src,ground,hue):
    """closest colour to the ink, at the given hue, that clears the gate"""
    H0,S0,L0=hsl(src); best=None
    S=max(0.32,S0-0.20)
    while S<=min(1.0,S0+0.28)+1e-9:
        L=0.06
        while L<=0.95:
            c=fromhsl(hue,S,L)
            if ratio(c,ground)>=GATE:
                d=dE(c,src)
                if best is None or d<best[0]: best=(d,c)
            L+=0.005
        S+=0.02
    return best[1]

rows={}
for n,src in SRC.items():
    H=target[n]
    rows[n]={"src":src,"hue":round(H,1),"dark":solve(src,DARK_WORST,H),"light":solve(src,LIGHT_WORST,H)}

# farthest-point insertion: each colourless mark takes the hue furthest from
# every hue already spoken for, including the ones placed before it
taken=[r["hue"] for r in rows.values()]
for n in NO_INK:
    best=max(range(0,3600), key=lambda t: min(arc(t/10.0,h) for h in taken))
    H=best/10.0; taken.append(H)
    seed=fromhsl(H,0.72,0.5)
    rows[n]={"src":None,"hue":round(H,1),"dark":solve(seed,DARK_WORST,H),"light":solve(seed,LIGHT_WORST,H)}


# Two managers share one piece of clip-art, so hue alone cannot separate them
# and in dark mode neither can value: the ground forces every deep red up to
# the same lightness. What is left is CHROMA, and it happens to be faithful --
# #BB2B38 really is the duller of the two reds, so the duller accent is his.
def sat_of(h):
    return hsl(h)[1]
def desaturate_until(a, b, key, ground, floor=14.0):
    for _ in range(30):
        if dE(rows[a][key], rows[b][key]) >= floor: return
        dull = a if sat_of(rows[a]["src"] or rows[a][key]) < sat_of(rows[b]["src"] or rows[b][key]) else b
        H,S,L = hsl(rows[dull][key])
        if S <= 0.34: return
        for step in range(1, 40):
            c = fromhsl(H, max(0.32, S-0.03), min(0.95, L+0.004*step))
            if ratio(c, ground) >= GATE:
                rows[dull][key] = c; break
        else: return
for A,B in itertools.combinations(rows,2):
    if rows[A]["src"] and rows[B]["src"]:
        desaturate_until(A,B,"dark",DARK_WORST)
        desaturate_until(A,B,"light",LIGHT_WORST)

order=sorted(rows,key=lambda n:rows[n]["hue"])
print("%-22s %-8s %6s  %-8s %5s  %-8s %5s" % ("manager","ink","drift","dark","vs","light","vs"))
for n in order:
    r=rows[n]
    drift="\u2014" if not r["src"] else "%+.1f"%(((r["hue"]-hsl(r["src"])[0]+540)%360)-180)
    print("%-22s %-8s %6s  %-8s %5.2f  %-8s %5.2f"%(n,r["src"] or "\u2014",drift,
        r["dark"],ratio(r["dark"],DARK_WORST),r["light"],ratio(r["light"],LIGHT_WORST)))
pairs=sorted((dE(rows[a]["dark"],rows[b]["dark"]),a,b) for a,b in itertools.combinations(rows,2))
print("\nclosest pairs, dark:");  [print("   %5.1f  %s / %s"%p) for p in pairs[:4]]
pl=sorted((dE(rows[a]["light"],rows[b]["light"]),a,b) for a,b in itertools.combinations(rows,2))
print("closest pairs, light:"); [print("   %5.1f  %s / %s"%p) for p in pl[:3]]
print("min hue gap %.1f\u00b0 | worst contrast dark %.2f light %.2f" % (
  min(arc(rows[a]["hue"],rows[b]["hue"]) for a,b in itertools.combinations(rows,2)),
  min(ratio(r["dark"],DARK_WORST) for r in rows.values()),
  min(ratio(r["light"],LIGHT_WORST) for r in rows.values())))


# ── the JS block, and the check that the document still matches it ─────────
NOTE = {}
for n in rows:
    if n in NO_INK:      NOTE[n] = "no ink in the mark" if LOGOS.get(n) else "no mark at all"
    elif n in HAND:      NOTE[n] = "HAND: " + HAND[n][1]
    else:                NOTE[n] = "sampled ink"
def js_block():
    order = sorted(rows, key=lambda n: rows[n]["hue"])
    w = max(len(n) for n in order) + 3
    out = ["const OWNER_ACCENT = {"]
    for i, n in enumerate(order):
        r = rows[n]
        out.append('  %-*s ["%s","%s"]%s /* %-8s %s */' % (
            w, '"%s":' % n, r["dark"], r["light"],
            "," if i < len(order) - 1 else " ", r["src"] or "\u2014", NOTE[n]))
    out.append("};")
    return "\n".join(out)

block = js_block()
if "--check" in sys.argv:
    html = io.open(SRC_FILE, encoding="utf-8", newline=None).read()
    i = html.index("const OWNER_ACCENT = {")
    live = html[i:html.index("};", i) + 2]
    same = live.strip() == block.strip()
    print("\nindex.html %s the derivation" % ("MATCHES" if same else "does NOT match"))
    if not same:
        print("re-run without --check and paste the block below into index.html")
        print(block)
    sys.exit(0 if same else 1)
print("\n" + block)
