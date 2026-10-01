# Driving a web app with agent-browser — the mechanics

Every item here is a trap that has already cost a session. Read once per session, then
`agent-browser skills get core` for the command reference.

## 1. A stack, and the RIGHT stack

- Start the app the way the project profile (`.claude/ui-review.md`) says. **Read the real URL and
  port from the command's output.** Conventional ports (`:3000`, `:5173`, `:8000`) are often
  somebody else's stack serving a different branch; nothing errors, you review the wrong code.
- **A login page where auto-login was expected means the wrong stack**, not broken auth.
- **Never drive a deployed environment in this skill** — its screenshots hold real personal
  data. `capture.sh` refuses non-local URLs.

## 2. Session, wait, viewport

```bash
S=verify-<project>                                  # one named session per task; never bare
agent-browser --session $S open http://localhost:<port>/path
agent-browser --session $S wait --text "Heading"    # NOT --load networkidle: dev servers with HMR never idle
agent-browser --session $S set viewport 1440 900 2  # desktop · DPR 2
agent-browser --session $S set viewport 390 844 3   # phone — mobile surfaces FIRST
agent-browser --session $S set viewport 1440 2200 2 # a long page whose app shell scrolls an INNER container:
                                                    # --full and scroll both return the fold; grow the viewport instead
```

`set viewport`, not `viewport`. `wait 3000` is a flake with a timer — wait on text.

## 3. Capture — only through capture.sh

```bash
~/.claude/skills/ui-review/scripts/capture.sh $S <run-dir> 01-page            # whole viewport
~/.claude/skills/ui-review/scripts/capture.sh $S <run-dir> 02-dialog '[role=dialog]'
```

Writes a clean PNG (the model's copy), an `.annotated.png` (labels `[N]` = ref `@eN`, for
humans), the legend with boxes and a `.src.json` sidecar with the source URL. **Crop by
selector for any control-level check** — a whole page is downscaled before send and a small
control disappears; a crop keeps full detail. Give the region an id first if it has none:
`eval "document.querySelector('h1').closest('header').id='crop'"` then `'#crop'`. **Run it with the tool sandbox DISABLED** — sandboxed, `agent-browser screenshot`
exits 0 and writes nothing. A **relative** path is resolved against the agent-browser daemon,
not your shell, and lands in `~/.agent-browser/tmp/`; the helper passes absolute paths and
falls back to the JSON-reported path. It prints the byte size so you notice either failure.
You do not open the PNG. The model does.

## 4. Interact

- `snapshot -i` lists interactive elements with `@eN` refs; **refs expire on re-render** —
  re-snapshot after every navigation or state change. `snapshot` (no flag) reads content.
- **Headless-UI triggers (Radix / Headless UI / Ark selects, menus, dialogs) often do not open on
  `click @ref`** — the click lands, `aria-expanded` stays false, no error. Focus and use keys:
  ```bash
  agent-browser --session $S eval "document.getElementById('field-id').focus();1"
  agent-browser --session $S press ArrowDown     # opens
  agent-browser --session $S press Enter         # picks the highlighted item
  ```
  Find a stable id, `data-testid` or `aria-label` in `snapshot`.
- File input: `upload "@<ref>" <path>`, then confirm with
  `eval "document.querySelector('input[type=file]').files.length"`.
- Scroll with `scroll down 300`; `tab` lists tabs as `t1`, `t2` (not `0`, `1`).
- A shell variable holding a command (`AB="agent-browser …"; $AB click`) does not run in zsh —
  use a function: `ab(){ agent-browser --session "$S" "$@"; }`.
- `type` (per key) during a recording, `fill` otherwise.

## 5. Read state as TEXT (Claude's eyes)

```bash
agent-browser --session $S snapshot                         # headings, values, pills
agent-browser --session $S eval "document.body.innerText"   # IMMEDIATELY after an action — a toast dies in ~4 s
agent-browser --session $S errors                           # JS exceptions: the bar is ZERO
agent-browser --session $S console
```

**Never conclude "the control is inert / nothing saves" from a click alone.** Three confident false
findings in one session came from clicks that never landed. The request line in the server log
or the database row is the evidence — the profile says where they are. A finding neither can
confirm goes back to the model as a question (`review.py ask`), not to your eyes.

## 6. Teardown

```bash
agent-browser --session $S close
```
Then stop the stack the way the profile says.
