"""Reads the club's public Google Calendar feed at build time and turns it into
event rows for the site plus one downloadable .ics file per event.

Order of sources: live feed, then data/calendar.ics (last good copy), then the
sample file in fixtures/ when building a preview.
"""
import datetime as dt
import html
import pathlib
import re
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

import icalendar
import recurring_ical_events

ROOT = pathlib.Path(__file__).parent
CACHE = ROOT / "data" / "calendar.ics"
SAMPLE = ROOT / "fixtures" / "sample.ics"


def ics_url(cal_id):
    return "https://calendar.google.com/calendar/ical/" + urllib.parse.quote(cal_id, safe="") + "/public/basic.ics"


def load(cal_id, preview=False):
    """Returns (ics_bytes, source) where source is 'live', 'cache', 'sample' or None."""
    if cal_id:
        try:
            req = urllib.request.Request(ics_url(cal_id), headers={"User-Agent": "rrbc-site-build"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            if b"BEGIN:VCALENDAR" in data:
                CACHE.parent.mkdir(exist_ok=True)
                CACHE.write_bytes(data)
                return data, "live"
        except Exception as e:  # network down, calendar private, etc.
            print("Calendar feed not reachable:", e)
        if CACHE.exists():
            return CACHE.read_bytes(), "cache"
    if preview and SAMPLE.exists():
        return SAMPLE.read_bytes(), "sample"
    return None, None


def _clean(text):
    text = str(text or "")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def occurrences(ics_bytes, tz_name, days=120, now=None):
    tz = ZoneInfo(tz_name)
    now = now or dt.datetime.now(tz)
    start = now - dt.timedelta(hours=3)
    end = now + dt.timedelta(days=days)
    cal = icalendar.Calendar.from_ical(ics_bytes)
    out = []
    for ev in recurring_ical_events.of(cal).between(start, end):
        s = ev.get("DTSTART").dt
        e = ev.get("DTEND").dt if ev.get("DTEND") else None
        allday = not isinstance(s, dt.datetime)
        if allday:
            e = e or (s + dt.timedelta(days=1))
            local_start = dt.datetime.combine(s, dt.time(0), tz)
        else:
            if s.tzinfo is None:
                s = s.replace(tzinfo=tz)
            e = e or (s + dt.timedelta(hours=1))
            if e.tzinfo is None:
                e = e.replace(tzinfo=tz)
            local_start = s.astimezone(tz)
        title = _clean(ev.get("SUMMARY")) or "Booster club event"
        out.append({
            "uid": str(ev.get("UID", "")),
            "title": title,
            "start": s, "end": e, "allday": allday,
            "local_start": local_start,
            "local_end": e if allday else e.astimezone(tz),
            "location": _clean(ev.get("LOCATION")),
            "description": _clean(ev.get("DESCRIPTION")),
            "slug": local_start.strftime("%Y-%m-%d") + "-" + (re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48] or "event"),
        })
    out.sort(key=lambda o: o["local_start"])
    seen = {}
    for o in out:  # make slugs unique when two events share a day and title
        n = seen.get(o["slug"], 0)
        seen[o["slug"]] = n + 1
        if n:
            o["slug"] += f"-{n + 1}"
    return out


def _esc(v):
    return str(v).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold(line):
    b = line.encode("utf-8")
    if len(b) <= 75:
        return line
    parts, cur = [], b""
    for ch in line:
        cb = ch.encode("utf-8")
        if len(cur) + len(cb) > (75 if not parts else 74):
            parts.append(cur.decode("utf-8"))
            cur = b""
        cur += cb
    parts.append(cur.decode("utf-8"))
    return "\r\n ".join(parts)


def _stamp(d, allday):
    if allday:
        return ";VALUE=DATE:" + d.strftime("%Y%m%d")
    return ":" + d.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def single_ics(o, page_url):
    occ = o["local_start"].strftime("%Y%m%dT%H%M")
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//River Ridge Booster Club//Website//EN",
        "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        "UID:" + _esc((o["uid"] or o["slug"]) + "-" + occ),
        "DTSTAMP:" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "DTSTART" + _stamp(o["start"], o["allday"]),
        "DTEND" + _stamp(o["end"], o["allday"]),
        "SUMMARY:" + _esc(o["title"]),
    ]
    if o["location"]:
        lines.append("LOCATION:" + _esc(o["location"]))
    desc = o["description"]
    desc = (desc + "\n\n" if desc else "") + "River Ridge Booster Club: " + page_url
    lines += ["DESCRIPTION:" + _esc(desc), "URL:" + page_url, "END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(_fold(l) for l in lines) + "\r\n"


def google_add_url(o):
    if o["allday"]:
        dates = o["start"].strftime("%Y%m%d") + "/" + o["end"].strftime("%Y%m%d")
    else:
        f = "%Y%m%dT%H%M%SZ"
        dates = o["start"].astimezone(dt.timezone.utc).strftime(f) + "/" + o["end"].astimezone(dt.timezone.utc).strftime(f)
    q = {"action": "TEMPLATE", "text": o["title"], "dates": dates}
    if o["location"]:
        q["location"] = o["location"]
    if o["description"]:
        q["details"] = o["description"][:1500]
    return "https://calendar.google.com/calendar/render?" + urllib.parse.urlencode(q)


def when_text(o):
    s = o["local_start"]
    day = s.strftime("%A, %B ") + str(s.day)
    if o["allday"]:
        last = o["end"] - dt.timedelta(days=1)
        if last > o["start"]:
            return f"{day} to {last.strftime('%A, %B ')}{last.day}, all day"
        return day + ", all day"

    def t(x):
        return x.strftime("%I:%M %p").lstrip("0").replace(":00 ", " ").replace("AM", "am").replace("PM", "pm")
    return f"{day}, {t(s)} to {t(o['local_end'])}"
