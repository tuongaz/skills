# ui-review profile — <project>

Read by the `ui-review` skill before any browser work. Keep it short; every line is a fact the
skill cannot know on its own.

## Stack

- Start: `make verify.up APP=web` (isolated, mock auth). Read the URL, port and session name from
  its output — ports are random. Stop: `make verify.down`.
- Wrong-stack tell: a login page (the verify stack auto-signs-in).
- Never review: `*.example.com` deployed environments (real customer data).

## Surfaces and viewports

| Surface | Viewport | Note |
| --- | --- | --- |
| web (desktop) | `set viewport 1440 900 2` | long record pages: `1440 2200 2` (inner-scroll shell) |
| mobile app | `set viewport 390 844 3` | phone first |

## Specs and mocks

- Plans: `docs/plans/<date>-<topic>.md` — names the chosen mock frame.
- Mocks: `design/*.html` (HTML, open via `file://`).

## Confirming a finding from text

- Server log: `.verify/logs/backend.log` (request lines).
- DB: `psql "$DATABASE_URL"`; the data a screen shows lives in `<schema>.<table>`.

## Personas

- Table in the `eyeball` skill (or list the logins here).

## Reviewer context

(Passed to the vision model with `--context`; the model sees nothing else about the product.)

- What the product is, who uses each surface, and what they value.
- Vocabulary rules ("customer", never "client"; en-AU dates).
- Design rules the model can SEE: one typeface, one primary action per screen, terse copy.
- What not to judge: colour against any palette (the product is themed).
