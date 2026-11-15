# River Ridge Booster Club website

The public website for the River Ridge High School Booster Club, served at riverridgeboosterclub.com.

This file is the handover guide. If you are a new board member taking over the website, start here.

## The short version

Most updates never touch this code. The site reads from three things the board already uses:

| To change | Edit this | Shows on the site |
|---|---|---|
| Events and meetings | The club Google Calendar (rrhshawks@gmail.com) | Within an hour |
| What we fund | Google Sheet "RR Booster Club - What We've Funded (website source)" | Right away |
| Board officers | Google Sheet "RR Booster Club - Board Officers (website source)" | Right away |
| Minutes, treasurer reports, bylaws | The matching folders in the club Google Drive | Right away (the site links to the folders) |

Everything else (wording, links, membership price, colors) is changed in `build.py`.

## Accounts

All of these should belong to the club, not to a person.

| What | Account | Notes |
|---|---|---|
| Domain riverridgeboosterclub.com | GoDaddy, River Ridge Booster Club (rrhshawks@gmail.com) | DNS settings point the domain at GitHub Pages |
| This code and the hosting | GitHub, RRHSHawks | Free. GitHub Pages serves the site from this repository |
| Calendar, Sheets, Drive, forms | Google, rrhshawks@gmail.com | Calendar must stay public |
| Donations | Square | "Give online" link on the Donate page |
| Social | Facebook @RRHSBoosterClub, Instagram @riverridgeboosterclub | Linked in the footer; Facebook posts show on the home page |

## Rules for the Google Sheets

The site finds columns by their names in row 1. Rename a heading and that column stops showing. You can reorder columns.

**What We've Funded:** Date (2026-10-15 style, optional), School year (2026-27 style), Program, Area, What it paid for, Amount (a number, optional), Show on website (Yes to publish).

**Board Officers:** Order (1, 2, 3), Name, Title, Bio, Headshot link (a Google Drive link to a photo shared as "Anyone with the link can view"), Show on website (Yes to publish).

Both Sheets must stay viewable by anyone with the link. Do not download and re-upload them; that creates a new file with a new address.

## Changing something in the code with Claude

Open a Claude session with this repository attached and describe the change in plain words, for example "add the spring auction to the home page" or "change the membership price to $15". Claude reads this file first.

Notes for Claude:
- All editable settings live in `CONFIG` at the top of `build.py`.
- `python3 build.py` builds the live site into `site/`. `python3 build.py --preview` adds clearly marked sample data where real data is missing.
- Brand rules (colors, fonts, logos, voice) are in the board's Claude project as "branding-schema-template". Colors: navy #28335D, silver #BCBDC0, ridge blue #012B65. Fonts: Graduate for headlines, Public Sans for text.
- Do not put anything private in this repository. It is public.

## How the site is built and published

- `build.py` writes the HTML pages into `site/`. Hand-written files in `site/` (`style.css`, `funded.js`, `board.js`, images) are kept as they are.
- `calendar_feed.py` reads the public Google Calendar feed and makes one downloadable `.ics` file per event in `site/events/`.
- `.github/workflows/deploy.yml` runs the build on every change and once an hour, then publishes `site/` to GitHub Pages. You can also run it by hand from the Actions tab ("Run workflow").
- `data/` holds the last good copy of the calendar and both Sheets, so the site still shows them if Google is unreachable during a build.

## If something breaks

- **Events missing:** check the calendar is still public. Settings, the calendar, Access permissions, "Make available to public".
- **Funding list or board missing:** check the Sheet is still "Anyone with the link can view" and row 1 headings are unchanged.
- **Whole site down:** check the Actions tab on GitHub for a failed run, and check the domain's DNS records at GoDaddy still point to GitHub Pages.
- **Emergency fallback:** the old Wix site still exists. Pointing the GoDaddy DNS back to Wix restores it.
