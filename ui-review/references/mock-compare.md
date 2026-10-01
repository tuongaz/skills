# Comparing a build against its mock

## 1. Know which frame is the target

A mock often draws several directions or states. **The plan, ticket or design note names the
chosen one** — read it before cropping anything. Inferring the target from the mock is how a
build gets compared against the wrong direction.

## 2. Render the mock the same way as the build

**HTML mock:** open it in the SAME session at the SAME viewport and DPR, then crop frames by
selector so each pair is one state:

```bash
S=verify-<project>
agent-browser --session $S set viewport 1440 900 2
agent-browser --session $S open "file://$PWD/design/record.html"
agent-browser --session $S eval "Array.from(document.querySelectorAll('[id]')).map(e=>e.tagName+'#'+e.id).join('\n')" | head -40
~/.claude/skills/ui-review/scripts/capture.sh $S <run> mock-01-view '#frame-b-view'
```

If frames have no ids, grow the viewport (`set viewport 1440 2400 2`) and capture the page once;
the model reads the frame labels. Switch the mock to the same theme (light/dark) as the build.

**Image mock (PNG/JPG):** pass it directly as the mock side of a pair — no sidecar needed; it is
a design asset, not a screenshot of anyone's data. Match the build's viewport to the mock's width.

## 3. Capture the build in the matching state

Drive the real page to the state each frame draws (the right tab, the dialog open, the empty
state) and capture with the same name prefix: `build-01-view`.

## 4. One review call, pairs in order

```bash
python3 ~/.claude/skills/ui-review/scripts/review.py review \
  --brief <run>/brief.json --rubric ~/.claude/skills/ui-review/references/rubric.md \
  [--context .claude/ui-review.md] \
  --pair <run>/mock-01-view.png <run>/build-01-view.png \
  --pair <run>/mock-02-edit.png <run>/build-02-edit.png --out <run>
```

`brief.json` has `"mock": true` and names the mock file and frame in `feature`.

## 5. Classify every gap ONCE

| Class | Examples | Action |
| --- | --- | --- |
| **fix** | wrong fact, broken behaviour, permission leak, vocabulary break, console error | fix now |
| **fix once** | a missing state, a section missing or out of order, a two-step dialog the mock draws as one | fix now, one round |
| **accept batch** | spacing, exact copy placement, icon choice, shared-component placement, mock fixture data, "may be deliberate" items the spec does not settle | list for the owner in ONE batch; never loop on it |

Two review rounds maximum. Round two sends only the pairs whose build changed. Whatever is left
after round two goes to the owner as a list, not a third round. A mock is a review aid, not a
pixel spec — 100 % match is not the bar.

## 6. What the owner sees

One page: a mock-beside-build pair per frame, a verdict pill per pair, a "found and fixed" list
and the accepted list — published once with the PR. The owner reads it in a minute and says
"ship it" or names the pairs that still bother them.
