#!/usr/bin/env python3
"""Builds the River Ridge Booster Club site into ./site.

Everything a board member is likely to change lives in CONFIG below.
Run:  python3 build.py            (live build, for the real website)
      python3 build.py --preview  (adds clearly marked sample funding rows)
"""
import base64
import html
import urllib.parse

import calendar_feed as cf
import json
import pathlib
import sys

CONFIG = {
    "email": "rrhshawks@gmail.com",
    "address": "350 River Ridge Dr SE, Lacey, WA 98513",
    "ein": "91-1602695",
    "domain": "riverridgeboosterclub.com",
    "site_url": "https://www.riverridgeboosterclub.com",
    # Leave a link empty ("") until it exists; the page then says it is coming soon.
    "links": {
        "join_form": "https://docs.google.com/forms/d/e/1FAIpQLSc6knz8u0Tx218h3fQMhe9vuMv6jcbW_WBYkPckBIOPGNB63g/viewform",
        "volunteer_form": "",
        "donate": "https://square.link/u/20x2Hl8p",
        "request_form": "",
        "facebook": "https://www.facebook.com/RRHSBoosterClub/",
        "instagram": "https://www.instagram.com/riverridgeboosterclub/",
        "minutes": "https://drive.google.com/drive/folders/1_OJoKfjzlLeEhK6iobtb5KzAOGRZWuxU",
        "treasurer_reports": "https://drive.google.com/drive/folders/1C_IFfXYFO6SZ1-no9LO-pAtMDAYrKdbO",
        "bylaws": "https://drive.google.com/drive/folders/1Qt7YjUt0Bdre6tsQJ0GJWT7k1SDJoCKj",
    },
    # Google Sheet "What We've Funded": File > Share > Publish to web > CSV. Paste that link here.
    "funded_csv_url": "https://docs.google.com/spreadsheets/d/18AP6CCaACSruU0EVOuyQNUB-oXwUUzFP0o1YzarSjQk/gviz/tq?tqx=out:csv&headers=1",
    # Google Sheet "Board Officers": File > Share > Publish to web > CSV. Paste that link here.
    "board_csv_url": "https://docs.google.com/spreadsheets/d/1UI467WTmpGPaf2HtHM3AnVITunCBzZLkf9v4oD_UFyk/gviz/tq?tqx=out:csv&headers=1",
    "membership_price": "Membership is $10 a year or $50 for a lifetime. Students and staff join free.",
    # Google Calendar: Settings > (club calendar) > Integrate calendar > Calendar ID.
    # The calendar must be public: Access permissions > Make available to public > See all event details.
    "calendar_id": "rrhshawks@gmail.com",
    "calendar_tz": "America/Los_Angeles",
    # Path to the logo file inside site/ once we have it, e.g. "logo.png". Empty shows the RR mark.
    "logo": "logo-rr-hawk.png",  # Emblem A, from the club. Emblem B can go here instead.
    "events": [
        # {"mon": "Dec", "day": "3", "title": "Monthly booster club meeting",
        #  "info": "6:00 pm in the library. Open to everyone.", "volunteer": False},
    ],
    "board": [
        {"role": "President", "name": ""},
        {"role": "Vice President", "name": ""},
        {"role": "Secretary", "name": ""},
        {"role": "Treasurer", "name": ""},
    ],
}

PREVIEW = "--preview" in sys.argv
SAMPLE_ROWS = [
    {"date": "2026-10-15", "year": "2026-27", "program": "Band", "area": "Arts", "what": "Sample entry: replacement music stands", "amount": "450"},
    {"date": "2026-10-02", "year": "2026-27", "program": "Robotics", "area": "Academics", "what": "Sample entry: competition registration", "amount": "300"},
    {"date": "2026-09-18", "year": "2026-27", "program": "Girls soccer", "area": "Athletics", "what": "Sample entry: travel to an away tournament", "amount": "600"},
    {"date": "2026-09-05", "year": "2026-27", "program": "Black Student Union", "area": "Clubs and culture", "what": "Sample entry: heritage night supplies", "amount": "200"},
    {"date": "2026-05-20", "year": "2025-26", "program": "Senior scholarships", "area": "Academics", "what": "Sample entry: two graduating senior scholarships", "amount": "1000"},
    {"date": "2026-03-11", "year": "2025-26", "program": "Drama", "area": "Arts", "what": "Sample entry: spring musical lighting rental", "amount": "350"},
]

SAMPLE_BOARD = [
    {"order": 1, "name": "Sample President", "title": "President", "bio": "Sample bio. Two or three sentences about how long they have served and what they focus on.", "photo": ""},
    {"order": 2, "name": "Sample Vice President", "title": "Vice President", "bio": "Sample bio. Each officer's photo, title, and bio come from the Board Officers sheet.", "photo": ""},
    {"order": 3, "name": "Sample Secretary", "title": "Secretary", "bio": "Sample bio. Officers without a photo show their initials until one is added.", "photo": ""},
    {"order": 4, "name": "Sample Treasurer", "title": "Treasurer", "bio": "Sample bio. Change the Order column to change who appears first.", "photo": ""},
]

def sheet_snapshot(url, cache_name):
    """Fetch a public Google Sheet as CSV at build time; fall back to the last good copy in data/."""
    import urllib.request
    cache = pathlib.Path(__file__).parent / "data" / cache_name
    if url:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "rrbc-site-build"}), timeout=20) as r:
                text = r.read().decode("utf-8")
            if "," in text.splitlines()[0]:
                cache.parent.mkdir(exist_ok=True)
                cache.write_text(text, encoding="utf-8")
                return text
        except Exception as e:
            print("Sheet not reachable (" + cache_name + "):", e)
    return cache.read_text(encoding="utf-8") if cache.exists() else ""

OUT = pathlib.Path(__file__).parent / "site"
E = html.escape
L = CONFIG["links"]

NAV = [
    ("funded.html", "What we fund"),
    ("events.html", "Events"),
    ("volunteer.html", "Volunteer"),
    ("documents.html", "Documents"),
    ("board.html", "Board"),
]


def action(url, label, kind="btn"):
    if url:
        return f'<a class="{kind}" href="{E(url)}">{E(label)}</a>'
    return f'<span class="{kind} is-pending">{E(label)} (link coming soon)</span>'


def mark():
    if CONFIG["logo"]:
        return f'<img class="mark-img" src="{E(CONFIG["logo"])}" alt="River Ridge Hawks logo" width="86" height="62">'
    return '<span class="mark" aria-hidden="true">RR</span>'


def patch():
    if CONFIG["logo"]:
        return f'<div class="patch patch-logo" aria-hidden="true"><img src="{E(CONFIG["logo"])}" alt="" width="240" height="174"></div>'
    return '<div class="patch" aria-hidden="true"><span>RR</span></div>'


def page(filename, title, body, current="", scripts=False, copy=False, board=False):
    nav = "".join(
        f'<a href="{href}"{" aria-current=\"page\"" if href == current else ""}>{E(label)}</a>'
        for href, label in NAV
    )
    data = ""
    if scripts:
        cfg = {"csv": CONFIG["funded_csv_url"], "email": CONFIG["email"], "csvText": FUNDED_SNAPSHOT}
        if PREVIEW and not CONFIG["funded_csv_url"] and not FUNDED_SNAPSHOT:
            cfg["sample"] = SAMPLE_ROWS
        data = f'<script>window.RRBC={json.dumps(cfg)};</script><script src="funded.js" defer></script>'
    if board:
        bcfg = {"csv": CONFIG["board_csv_url"], "csvText": BOARD_SNAPSHOT}
        if PREVIEW and not CONFIG["board_csv_url"] and not BOARD_SNAPSHOT:
            bcfg["sample"] = SAMPLE_BOARD
        data += f'<script>window.RRBC_BOARD={json.dumps(bcfg)};</script><script src="board.js" defer></script>'
    if copy:
        data += ("<script>document.addEventListener('click',function(e){var b=e.target.closest('[data-copy]');if(!b)return;"
                 "var s=document.querySelector('[data-copy-status]');function say(t){if(s)s.textContent=t;}"
                 "try{navigator.clipboard.writeText(b.getAttribute('data-copy')).then(function(){say('Calendar link copied. Paste it into any calendar app that can subscribe by URL.');},"
                 "function(){say('Copy did not work here. The link is: '+b.getAttribute('data-copy'));});}"
                 "catch(x){say('Copy did not work here. The link is: '+b.getAttribute('data-copy'));}});</script>")
    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="The River Ridge Booster Club is a volunteer group of parents, guardians, staff, and neighbors supporting River Ridge High School students.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Graduate&family=Public+Sans:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
<link rel="icon" href="favicon.png" type="image/png">\n<link rel="apple-touch-icon" href="apple-touch-icon.png">\n<link rel="stylesheet" href="style.css">
{data}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="masthead">
<div class="wrap masthead-row">
<a class="brand" href="index.html">{mark()}<span class="brand-name">River Ridge<br>Booster Club</span></a>
<nav class="nav" aria-label="Main">{nav}<a class="btn btn-small" href="join.html">Join</a></nav>
</div>
</header>
<main id="main">
{body}
</main>
<footer class="footer">
<div class="stripes" aria-hidden="true"></div>
<div class="wrap footer-grid">
<div>
<p class="footer-name">River Ridge Booster Club</p>
<p>{E(CONFIG["address"])}</p>
<p>Registered charity, EIN {E(CONFIG["ein"])}</p>
</div>
<div>
<p class="footer-head">Contact</p>
<p><a class="footer-mail" href="mailto:{E(CONFIG["email"])}">{E(CONFIG["email"])}</a></p>
{social_line()}
</div>
<div>
<p class="footer-head">Get involved</p>
<p><a href="join.html">Join</a></p>
<p><a href="volunteer.html">Volunteer</a></p>
<p><a href="donate.html">Donate</a></p>
<p><a href="request.html">Request funds</a></p>
</div>
</div>
</footer>
</body>
</html>
"""
    (OUT / filename).write_text(doc, encoding="utf-8")


def handle(url):
    return "@" + url.rstrip("/").rsplit("/", 1)[-1]


def social_line():
    parts = []
    if L["facebook"]:
        parts.append(f'<a class="social-link" href="{E(L["facebook"])}" aria-label="Booster club on Facebook, {E(handle(L["facebook"]))}">'
                     f'<img src="icons/facebook-logo-white.png" alt="" width="28" height="28"><span>{E(handle(L["facebook"]))}</span></a>')
    if L["instagram"]:
        parts.append(f'<a class="social-link" href="{E(L["instagram"])}" aria-label="Booster club on Instagram, {E(handle(L["instagram"]))}">'
                     f'<img src="icons/instagram-glyph-white.png" alt="" width="28" height="28"><span>{E(handle(L["instagram"]))}</span></a>')
    return f'<div class="footer-social">{"".join(parts)}</div>' if parts else ""

def subhero(title, lead, extra="", path=""):
    addr = f'<p class="hero-url">{E(CONFIG["domain"])}/{E(path)}</p>' if path else ""
    return (f'<section class="hero hero-sub"><div class="wrap">{addr}<h1>{E(title)}</h1>'
            f'<p class="lead">{E(lead)}</p>{extra}</div><div class="stripes" aria-hidden="true"></div></section>')


FUNDED_SNAPSHOT = ""
BOARD_SNAPSHOT = ""
EVENTS = []          # filled in build() from the Google Calendar feed
EVENTS_SOURCE = None


def event_item(o):
    s = o["local_start"]
    ics = "events/" + o["slug"] + ".ics"
    loc = f'<p class="ev-line"><strong>Where:</strong> {E(o["location"])}</p>' if o["location"] else ""
    desc = "".join(f"<p>{E(par)}</p>" for par in o["description"].split("\n") if par.strip())
    return f"""<li class="event">
<details>
<summary>
<span class="event-date"><span>{s.strftime("%b")}</span><strong>{s.day}</strong></span>
<span class="event-body"><span class="event-title">{E(o["title"])}</span><span class="event-when">{E(cf.when_text(o))}</span></span>
<span class="event-toggle" aria-hidden="true"></span>
</summary>
<div class="event-detail">
{loc}{desc}
<div class="ev-actions">
<a class="btn btn-small" href="{E(cf.google_add_url(o))}">Add to Google Calendar</a>
<a class="btn btn-small btn-outline" href="{E(ics)}" download>Download for Apple or Outlook (.ics)</a>
</div>
</div>
</details>
</li>"""


def events_list(limit=None):
    evs = EVENTS[:limit] if limit else EVENTS
    note = ('<p class="sample-note">Sample events. The club calendar replaces these on the live site.</p>'
            if EVENTS_SOURCE == "sample" else "")
    if not evs:
        return ('<p class="empty">Nothing is on the calendar for the next few months yet. '
                f'Ask about the next meeting at <a href="mailto:{E(CONFIG["email"])}">{E(CONFIG["email"])}</a>.</p>')
    if limit:
        return note + '<ul class="events">' + "".join(event_item(o) for o in evs) + "</ul>"
    out, month = [note], None
    for o in evs:
        m = o["local_start"].strftime("%B %Y")
        if m != month:
            if month:
                out.append("</ul>")
            out.append(f'<h2 class="month-head">{E(m)}</h2><ul class="events">')
            month = m
        out.append(event_item(o))
    out.append("</ul>")
    return "".join(out)


def cal_urls():
    cid = CONFIG["calendar_id"].strip()
    if not cid:
        return None
    q = urllib.parse.quote(cid, safe="")
    tz = urllib.parse.quote(CONFIG["calendar_tz"], safe="")
    base = "https://calendar.google.com/calendar/embed?src=" + q + "&ctz=" + tz + "&showTitle=0&showPrint=0&showCalendars=0&showTz=0"
    b64 = base64.b64encode(cid.encode()).decode().rstrip("=")
    return {
        "month": base + "&mode=MONTH",
        "agenda": base + "&mode=AGENDA",
        "google": "https://calendar.google.com/calendar/u/0?cid=" + b64,
        "ics": "https://calendar.google.com/calendar/ical/" + q + "/public/basic.ics",
        "webcal": "webcal://calendar.google.com/calendar/ical/" + q + "/public/basic.ics",
    }


def calendar_month():
    u = cal_urls()
    if not u:
        return ""
    return (f'<details class="month-view"><summary>Show the month view</summary>'
            f'<iframe class="cal-frame cal-month" title="Booster club calendar, month view" src="{E(u["month"])}" loading="lazy"></iframe></details>')


def calendar_subscribe():
    u = cal_urls()
    if not u:
        return ""
    return f"""
<div class="subscribe">
<h2>Put every booster club event on your own calendar</h2>
<p>Subscribe once and new meetings, shifts, and fundraisers appear on your phone automatically. Changes and cancellations update too.</p>
<div class="sub-actions">
<a class="btn" href="{E(u["google"])}">Add to Google Calendar</a>
<a class="btn btn-outline" href="{E(u["webcal"])}">Add to Apple Calendar or Outlook</a>
<button type="button" class="btn btn-outline" data-copy="{E(u["ics"])}">Copy calendar link</button>
</div>
<p class="sub-help" data-copy-status aria-live="polite"></p>
<p class="sub-help">To save just one event, open it in the list above and choose Google Calendar or the download for Apple and Outlook.</p>
</div>"""


def social_panel():
    fb = L["facebook"]
    ig = L["instagram"]
    if fb:
        src = ("https://www.facebook.com/plugins/page.php?href=" + html.escape(fb, quote=True)
               + "&amp;tabs=timeline&amp;width=500&amp;height=640&amp;small_header=true"
                 "&amp;adapt_container_width=true&amp;hide_cover=true&amp;show_facepile=false")
        feed = (f'<iframe class="fb-feed" title="Latest posts from the booster club Facebook page" src="{src}" '
                'width="500" height="640" loading="lazy" allow="encrypted-media"></iframe>')
    else:
        feed = ('<div class="feed-empty"><p>Our latest Facebook posts will show here once the page link is added.</p></div>')
    links = []
    if fb:
        links.append(f'<a class="btn btn-light" href="{E(fb)}">Follow on Facebook</a>')
    if ig:
        links.append(f'<a class="btn btn-ghost" href="{E(ig)}">Follow on Instagram</a>')
    link_html = f'<div class="actions">{"".join(links)}</div>' if links else ""
    return f"""
<section class="band-navy" aria-labelledby="social-h">
<div class="wrap social">
<div class="social-copy">
<h2 id="social-h">Game-day news</h2>
<p>Volunteer calls, concession updates, and photos from games and performances go out on social media first.</p>
{link_html}
</div>
<div class="social-feed">{feed}</div>
</div>
</section>"""


def funded_block(limit, heading_level="h2"):
    return f"""
<div class="ledger" data-funded data-limit="{limit}">
<p class="ledger-summary" data-summary></p>
<div data-filters></div>
<ol class="ledger-list" data-list></ol>
<p class="empty" data-empty hidden>The funding history is being updated. Ask the treasurer at <a href="mailto:{E(CONFIG["email"])}">{E(CONFIG["email"])}</a>.</p>
</div>"""


def build():
    global EVENTS, EVENTS_SOURCE, FUNDED_SNAPSHOT, BOARD_SNAPSHOT
    OUT.mkdir(exist_ok=True)
    FUNDED_SNAPSHOT = sheet_snapshot(CONFIG["funded_csv_url"], "funded.csv")
    BOARD_SNAPSHOT = sheet_snapshot(CONFIG["board_csv_url"], "board.csv")
    data, EVENTS_SOURCE = cf.load(CONFIG["calendar_id"], preview=PREVIEW)
    EVENTS = cf.occurrences(data, CONFIG["calendar_tz"]) if data else []
    ev_dir = OUT / "events"
    ev_dir.mkdir(exist_ok=True)
    for old in ev_dir.glob("*.ics"):
        old.unlink()
    for o in EVENTS:
        (ev_dir / (o["slug"] + ".ics")).write_text(cf.single_ics(o, CONFIG["site_url"] + "/events.html"), encoding="utf-8", newline="")
    print("Calendar:", EVENTS_SOURCE or "none", "-", len(EVENTS), "upcoming events")
    price = CONFIG["membership_price"]

    home = f"""
<section class="hero hero-home">
<div class="wrap hero-grid">
<div class="hero-copy">
<p class="hero-place">River Ridge High School, Lacey, Washington</p>
<h1>Backing every Hawk, in every program</h1>
<p class="lead">Parents, guardians, staff, and neighbors who volunteer and raise money for River Ridge students in academics, arts, athletics, and clubs.</p>
<div class="actions"><a class="btn btn-light" href="join.html">Become a member</a><a class="btn btn-ghost" href="volunteer.html">Sign up to volunteer</a></div>
</div>
{patch()}
</div>
<div class="stripes" aria-hidden="true"></div>
</section>

<section class="wrap section" aria-labelledby="help-h">
<h2 id="help-h">How to help</h2>
<ul class="roster">
<li><a href="join.html"><span class="roster-name">Join</span><span class="roster-text">{E(price)}</span></a></li>
<li><a href="volunteer.html"><span class="roster-name">Volunteer</span><span class="roster-text">Work a concession shift, help at a fundraiser, or pitch in from home.</span></a></li>
<li><a href="donate.html"><span class="roster-name">Donate</span><span class="roster-text">Tax-deductible gifts from families and local businesses. EIN {E(CONFIG["ein"])}.</span></a></li>
<li><a href="request.html"><span class="roster-name">Request funds</span><span class="roster-text">Coaches, advisors, and student groups can apply for support.</span></a></li>
</ul>
</section>

<section class="wrap section" aria-labelledby="funded-h">
<div class="section-head"><h2 id="funded-h">Where the money goes</h2><a class="text-link" href="funded.html">See everything we have funded</a></div>
{funded_block(5)}
</section>

{social_panel()}

<section class="wrap section" aria-labelledby="events-h">
<div class="section-head"><h2 id="events-h">Coming up</h2><a class="text-link" href="events.html">Full calendar</a></div>
{events_list(3)}
</section>
"""
    page("index.html", "River Ridge Booster Club", home, scripts=True)

    page("funded.html", "What we fund | River Ridge Booster Club", subhero(
        "What we fund", "Every request the board has approved, newest first. Filter by area to see where support has gone.", "", "funded") +
        f'<section class="wrap section">{funded_block(0)}</section>', "funded.html", scripts=True)

    page("join.html", "Join | River Ridge Booster Club", subhero(
        "Become a member", price + " Open to parents, guardians, staff, alumni, and neighbors.",
        f'<div class="actions">{action(L["join_form"], "Open the membership form", "btn btn-light")}</div>', "join") + """
<section class="wrap section prose">
<h2>What membership does</h2>
<ul><li>Pays for requests from teams, clubs, and classrooms.</li><li>Gives you a vote at monthly meetings.</li><li>Puts you on the list for volunteer calls and event news.</li></ul>
<p>You do not need to be a member to volunteer or come to a meeting.</p>
</section>""", "join.html")

    page("volunteer.html", "Volunteer | River Ridge Booster Club", subhero(
        "Sign up to volunteer", "Pick the shifts that fit your week. One shift a season helps, and you do not need to be a member.",
        f'<div class="actions">{action(L["volunteer_form"], "Open the volunteer sign-up", "btn btn-light")}</div>', "volunteer") + f"""
<section class="wrap section prose">
<h2>Where help is needed</h2>
<ul><li>Concession stand shifts at home games.</li><li>Setup and cleanup at fundraisers and events.</li><li>Jobs you can do from home, like social posts and grant writing.</li></ul>
<p>Questions go to <a href="mailto:{E(CONFIG["email"])}">{E(CONFIG["email"])}</a>.</p>
</section>""", "volunteer.html")

    page("donate.html", "Donate | River Ridge Booster Club", subhero(
        "Donate", "Every dollar goes to River Ridge students. Gifts are tax-deductible as the law allows.",
        f'<div class="actions">{action(L["donate"], "Give online", "btn btn-light")}</div>', "donate") + f"""
<section class="wrap section prose">
<h2>For your records</h2>
<p>River Ridge High School Booster Club is a registered charity, EIN {E(CONFIG["ein"])}.</p>
<p>To give by check or ask about business sponsorship, email <a href="mailto:{E(CONFIG["email"])}">{E(CONFIG["email"])}</a>.</p>
<p><a href="funded.html">See what past gifts have paid for.</a></p>
</section>""", "donate.html")

    page("request.html", "Request funds | River Ridge Booster Club", subhero(
        "Request funds", "Coaches, advisors, and student groups can ask the booster club to help pay for equipment, travel, events, and supplies.",
        f'<div class="actions">{action(L["request_form"], "Open the request form", "btn btn-light")}</div>', "request") + """
<section class="wrap section prose">
<h2>How a request works</h2>
<ol><li>Fill out the request form with the amount and what it covers.</li><li>The board reviews it at the next monthly meeting.</li><li>You hear back by email after the vote.</li></ol>
</section>""", "request.html")

    page("events.html", "Events | River Ridge Booster Club", subhero(
        "Events and meetings", "Monthly meetings are open to everyone. Game days and fundraisers always need a few extra hands.", "", "events") +
        f'<section class="wrap section">{events_list()}{calendar_subscribe()}{calendar_month()}</section>', "events.html", copy=True)

    docs = [("Meeting minutes and agendas", L["minutes"]), ("Treasurer's reports", L["treasurer_reports"]), ("Bylaws", L["bylaws"])]
    rows = "".join(
        (f'<li><a href="{E(u)}">{E(n)}</a></li>' if u else f'<li><span>{E(n)}</span><span class="muted">Coming soon</span></li>')
        for n, u in docs)
    page("documents.html", "Documents | River Ridge Booster Club", subhero(
        "Club documents", "Minutes, treasurer's reports, and bylaws are public. They open in Google Drive with no login.", "", "documents") +
        f'<section class="wrap section"><ul class="doclist">{rows}</ul></section>', "documents.html")

    board_body = (f'<div class="board" data-board><ul class="officers" data-list></ul>'
                  f'<p class="empty" data-fallback hidden>Officer names and photos for this school year will be posted here soon.</p></div>')
    page("board.html", "Board | River Ridge Booster Club", subhero(
        "Meet the board", "Volunteer officers elected by the membership each spring.", "", "board") +
        f'<section class="wrap section">{board_body}<p class="after">Reach the board at <a href="mailto:{E(CONFIG["email"])}">{E(CONFIG["email"])}</a>.</p></section>', "board.html", board=True)

    print("Built", len(list(OUT.glob("*.html"))), "pages into", OUT, "(preview)" if PREVIEW else "")


if __name__ == "__main__":
    build()
