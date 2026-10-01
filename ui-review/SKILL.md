---
name: ui-review
description: Use when a change alters what a user sees, when a built screen must be compared against its mock, when an area needs a UX sweep for problems nobody listed, or when a web app must be driven in a browser (open a page, click through a flow, reproduce a report). Captures screenshots with agent-browser and has a vision model on OpenRouter judge them; Claude reads the findings as text and never opens the PNG (critical debug excepted). Covers verify, compare, sweep and drive modes, the capped fix loop, and the local-stack-only privacy rule. Works in any web project; reads an optional per-project profile at .claude/ui-review.md.
---

# UI review

**Claude's eyes are text; the model's eyes are the images.** Every screenshot goes to a vision
model on OpenRouter (`scripts/review.py`); you read its findings, confirm each one from text,
fix, and re-review only what changed. **You do not open a PNG.** The one exception is a critical
debug — a crash, wrong data, a production incident — never general UI review.

## Project profile

If the project has `.claude/ui-review.md`, **read it first**. It says how to start the app, which
surfaces exist and at what viewport, where specs and mocks live, how to confirm a finding from
logs or data, and carries a *Reviewer context* section passed to the model with `--context`.
No profile → ask the user for the URL and viewport, and review with the generic rubric alone
([templates/project-profile.example.md](templates/project-profile.example.md) shows what to add).

## Modes

| Mode | When | What you do |
| --- | --- | --- |
| **verify** | any visible change | capture the touched screens → review → confirm → fix → re-review what changed |
| **compare** | a mock exists (HTML or image) | [references/mock-compare.md](references/mock-compare.md): same browser, same viewport, pairs, classified gaps |
| **sweep** | "have a look", "anything wrong with", unknown unknowns | drive the area as its user, capture each state, review with the open question in the rubric |
| **drive** | "open X", "click through Y", reproduce a report | [references/driving.md](references/driving.md) only; no review call unless asked |

## The loop

1. **Stack.** Start the app the way the profile says. Read the real URL and port from the
   command's output — never assume a port; a login page where none is expected = wrong stack.
2. **Spec before browser.** Read the plan or ticket that names the expected states and, for a
   mock, the CHOSEN frame or direction. Never infer the target from the mock alone.
3. **Capture** with `scripts/capture.sh <session> <run-dir> <name> [selector]` at the surface's
   viewport, **tool sandbox DISABLED**. It writes a clean PNG (what the model sees), an annotated
   copy for humans, the `[N]`→`@eN` legend with boxes, and the source sidecar `review.py` requires.
   **Two grains, both needed:** the whole fold (or a tall viewport) for layout, order and states;
   a **selector crop** for every control-level check — a clipped label, a wrong glyph, a missing
   key. A whole page is downscaled before send and a 40 px control becomes unreadable; a crop
   keeps full detail. Measured: the clipped button was invisible on the fold and obvious on the crop.
4. **Brief.** `<run-dir>/brief.json` with the fixed fields of
   [templates/brief.example.json](templates/brief.example.json) — no justification field, so the
   implementer cannot prime the reviewer.
5. **Review.** One call per round, all images:
   ```bash
   uv run python ~/.claude/skills/ui-review/scripts/review.py review \
     --brief <run>/brief.json --rubric ~/.claude/skills/ui-review/references/rubric.md \
     [--context .claude/ui-review.md] --image <run>/01-page.png [--pair mock.png build.png] --out <run>
   ```
   (`python3` with `httpx` and `Pillow` works too.) It prints a findings table and the tokens and
   dollars the call cost.
6. **Confirm from text** before acting on a blocker/major: DOM snapshot, `document.body.innerText`,
   the server log, a database row. Unconfirmable → `review.py ask --image <png> "<question>"`.
   "May be deliberate" → the spec decides; a silent spec sends it to the accept batch, never to a fix.
7. **Classify once:** wrong fact / broken behaviour / permission leak / vocabulary break → **fix**;
   a visible meaning or flow gap → **fix once**; pixel, spacing, placement, icon → **accept batch**.
8. **Re-review only the screens that changed.** Two rounds maximum. Residuals go to the owner in
   ONE batch; a mock is a review aid, not a pixel spec.
9. Close the session and stop the stack. Keep the run directory out of git.

## Hard rules

- **Local stacks only.** `capture.sh` and `review.py` refuse anything that is not `localhost`,
  `127.0.0.1`, `*.localhost` or a local file. A screenshot of a deployed environment can hold
  real personal data.
- **No PNG opened by Claude.** Reviewer unreachable (no key, 401, outage)? Report the change as
  **UNVERIFIED by the reviewer** and ask for the key. Do not look yourself.
- **Every finding is confirmed from text** before a fix. A click that "did nothing" is usually a
  headless-UI trigger that needs focus + keys; the server log settles it.
- **Brief = fixed fields.** No prose about intent.
- **Vendor and model names** stay in the run log and internal notes, never in client-facing copy.
- **Cost is visible.** Every call prints tokens and dollars; images are downscaled before send.
  Default model `qwen/qwen3-vl-32b-instruct` (~$0.001 per call, 20–60 s): in the bake-off it was
  the most grounded on tall pages and the only one to see a clipped label on a crop. Gemini 2.5
  Flash is 5× faster, caught a serif heading unprompted, and hallucinated on crops. Override with
  `UI_REVIEW_MODEL`; `review.py models` prints live prices.

## Red flags (each seen in a no-skill baseline run)

| Urge | Reality |
| --- | --- |
| "I'll just open the screenshot and compare" | 13 PNGs opened in one baseline run. That is the cost this skill removes. Send them. |
| "`screenshot --full` shows the whole page" | App shells that scroll an inner container return the fold. Grow the viewport. |
| "The model said the control is fine" (on a whole-page shot) | Below ~40 px it cannot see it. Crop the region and ask again. |
| "`wait 3000`" | Wait on text. A sleep is a flake with a timer. |
| "The mock's first frame is the one" | The spec names the chosen direction. Read it first. |
| "This may be deliberate, I'll file it as minor anyway" | Spec decides. Silent spec → accept batch, not a finding. |
| "One more round will get the match" | Two rounds. Uncapped loops get stopped by the owner with the pixel nits still open. |
| "The reviewer key is dead, I'll look myself" | UNVERIFIED by the reviewer. Ask for the key. |
| "The control did nothing — finding: inert" | Focus + keys, then the server log. False "inert" findings are the common failure. |

## Files

`scripts/capture.sh` · `scripts/review.py` (`review` · `ask` · `models`) ·
`references/rubric.md` (the reviewer prompt) · `references/driving.md` (agent-browser mechanics
and traps) · `references/mock-compare.md` · `templates/brief.example.json` ·
`templates/project-profile.example.md`.
