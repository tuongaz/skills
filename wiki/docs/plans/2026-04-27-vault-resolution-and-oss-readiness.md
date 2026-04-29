# Vault Resolution & OSS Readiness — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the `wiki` plugin resolve "which vault am I working in?" robustly across sessions, stop touching user-controlled `CLAUDE.md`, and bring the plugin to open-source-ready quality.

**Architecture:**

- **Marker = filesystem shape.** A directory is a wiki iff it contains `index.md`, `log.md`, `raw/`, and `wiki/`. No plugin metadata leaks into the user's vault. `CLAUDE.md` is user-controlled — the plugin never writes it.
- **State = one cache file at `~/.claude/wiki.local.md`.** YAML frontmatter records `last_used` and `known_vaults`. Cache is advisory; the resolution probe is authoritative.
- **Resolution probe.** Same six-step flow at the start of every operation: cwd → walk-up → cache → notes-tooling autodetect (`.obsidian/`, `.logseq/`, `.dendron/`, `.foam/`) → `known_vaults` list → ask. Lives in `wiki-conventions`; inherited by `wiki-ingest`, `wiki-query`, `wiki-lint`.
- **Tone = tool-agnostic.** `[[wikilinks]]` stay (cross-PKM standard), but framing throughout drops Obsidian-centric language.
- **OSS hygiene.** `LICENSE` (MIT), `CHANGELOG.md`, plugin.json metadata fields, privacy statement.

**Tech Stack:** Markdown skill files (`SKILL.md`), `plugin.json`, plain markdown for docs. No code execution; verification is structural inspection plus simulated probe scenarios in a temp directory.

**Out of scope** (not part of this plan):

- Per-project cache override (`.claude/wiki.local.md`). Resolution probe already handles per-directory specificity via cwd. Revisit only if a real use-case emerges.
- Configurable wikilink syntax. Locked to `[[]]` — works in Obsidian, Logseq, Foam, Dendron, Quartz, Foambubble.
- Reintroducing the subagent. Plugin stays skills-only.

**Notes for the executor:**

- All file paths are absolute under `/Users/tuongaz/dev/wiki`.
- The plugin's "code" is markdown skill files. There is no compile/test step. Verification = structural inspection (grep for expected section headers, frontmatter validation) plus simulated probe scenarios.
- Commit after each task. Use Conventional Commit prefixes (`feat:`, `chore:`, `docs:`, `refactor:`).
- Keep all skill bodies in **imperative form** (per superpowers:writing-skills). No second-person.
- Skill descriptions are **trigger conditions only**, never workflow summaries.

---

## Task 1: Add MIT LICENSE file

**Files:**

- Create: `/Users/tuongaz/dev/wiki/LICENSE`

**Step 1: Write the file**

Standard MIT license text. Replace `<copyright holder>` with the value from `plugin.json`'s `author.name` (currently "Tuong Le"). Year: 2026.

```
MIT License

Copyright (c) 2026 Tuong Le

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**Step 2: Verify**

```bash
test -f /Users/tuongaz/dev/wiki/LICENSE && head -1 /Users/tuongaz/dev/wiki/LICENSE
```

Expected output: `MIT License`

**Step 3: Commit**

```bash
git -C /Users/tuongaz/dev/wiki add LICENSE
git -C /Users/tuongaz/dev/wiki commit -m "chore: add MIT LICENSE"
```

---

## Task 2: Add CHANGELOG.md

**Files:**

- Create: `/Users/tuongaz/dev/wiki/CHANGELOG.md`

**Step 1: Write the file**

```markdown
# Changelog

All notable changes to this plugin will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-27

### Added

- Four skills: `wiki-conventions`, `wiki-ingest`, `wiki-query`, `wiki-lint`.
- Vault resolution probe (cwd → walk-up → cache → notes-tooling autodetect → ask).
- Vault cache at `~/.claude/wiki.local.md` recording `last_used` and `known_vaults`.
- Filesystem-shape marker for "is this a wiki?" — no plugin metadata in the user's vault.
- Bootstrap that creates only plugin-owned files (`index.md`, `log.md`, `raw/`, `wiki/`); never touches the user's `CLAUDE.md`.
- Generic notes-tooling autodetect: `.obsidian/`, `.logseq/`, `.dendron/`, `.foam/`.
```

**Step 2: Verify**

```bash
grep -c "^## \[" /Users/tuongaz/dev/wiki/CHANGELOG.md
```

Expected output: `2` (one Unreleased, one 0.1.0).

**Step 3: Commit**

```bash
git -C /Users/tuongaz/dev/wiki add CHANGELOG.md
git -C /Users/tuongaz/dev/wiki commit -m "chore: add CHANGELOG with 0.1.0 entry"
```

---

## Task 3: Update plugin.json with OSS metadata fields

**Files:**

- Modify: `/Users/tuongaz/dev/wiki/.claude-plugin/plugin.json`

**Step 1: Edit the file**

Add `homepage`, `repository`, `bugs` fields. Keep existing fields. Final shape:

```json
{
  "name": "wiki",
  "version": "0.1.0",
  "description": "Turns Claude Code into a disciplined maintainer of a personal markdown wiki. Ingest sources, query the wiki with citations, and lint for health.",
  "author": {
    "name": "Tuong Le",
    "email": "tuong@wisebit.com"
  },
  "homepage": "https://github.com/<owner>/wiki",
  "repository": {
    "type": "git",
    "url": "https://github.com/<owner>/wiki.git"
  },
  "bugs": {
    "url": "https://github.com/<owner>/wiki/issues"
  },
  "keywords": ["wiki", "knowledge-base", "obsidian", "logseq", "markdown", "memex", "notes", "pkm"],
  "license": "MIT"
}
```

Replace `<owner>` placeholders with the real GitHub username before publishing — but keep the placeholder for now. Note in the plan that this needs a follow-up before any public release.

**Step 2: Verify**

```bash
python3 -c "import json; d=json.load(open('/Users/tuongaz/dev/wiki/.claude-plugin/plugin.json')); print(sorted(d.keys()))"
```

Expected output: `['author', 'bugs', 'description', 'homepage', 'keywords', 'license', 'name', 'repository', 'version']`

**Step 3: Commit**

```bash
git -C /Users/tuongaz/dev/wiki add .claude-plugin/plugin.json
git -C /Users/tuongaz/dev/wiki commit -m "chore: add repository/homepage/bugs metadata to plugin.json"
```

---

## Task 4: Add privacy statement and de-Obsidian framing to README

**Files:**

- Modify: `/Users/tuongaz/dev/wiki/README.md`

**Step 1: Add a Privacy section above License**

Insert a new section directly above `## License`:

```markdown
## Privacy

This plugin is fully local. It only reads and writes files in:

- The wiki directory you point it at (your markdown files, `index.md`, `log.md`).
- A small cache at `~/.claude/wiki.local.md` recording the path of your last-used wiki(s) so the plugin can find them next session.

No network calls. No telemetry. No data leaves your machine. You can inspect or delete the cache file at any time.
```

**Step 2: Replace Obsidian-centric framing**

In the *Tips* section, replace the line:

```markdown
- **[Obsidian Web Clipper](https://obsidian.md/clipper)** is the fastest way to get articles into `raw/`.
```

with:

```markdown
- **Web clippers** like [Obsidian Web Clipper](https://obsidian.md/clipper) are the fastest way to get articles into `raw/` as markdown.
```

In the *Bootstrapping a new wiki* section, change:

```markdown
5. Browse the result in Obsidian (or any markdown viewer). The wiki is just a git repo of markdown files — commit after ingests to track how your understanding evolves.
```

to:

```markdown
5. Browse the result in any markdown viewer — Obsidian, Logseq, Foam, Dendron, VS Code, plain `cat`. The wiki is just a directory of markdown files — keep it under git and commit after ingests to track how your understanding evolves.
```

**Step 3: Verify**

```bash
grep -c "^## Privacy$" /Users/tuongaz/dev/wiki/README.md
grep -c "Logseq\|Dendron\|Foam" /Users/tuongaz/dev/wiki/README.md
```

Expected output: `1` then `≥1`.

**Step 4: Commit**

```bash
git -C /Users/tuongaz/dev/wiki add README.md
git -C /Users/tuongaz/dev/wiki commit -m "docs: add privacy statement and de-Obsidian framing in README"
```

---

## Task 5: Replace `wiki-conventions` Bootstrap section with Marker + Resolution Probe + Cache spec

**Files:**

- Modify: `/Users/tuongaz/dev/wiki/skills/wiki-conventions/SKILL.md`

This is the largest task in the plan. Three subsections replace the current `## Bootstrap` section.

**Step 1: Locate and remove the current Bootstrap section**

Current `## Bootstrap` (everything from `## Bootstrap` down to but not including `## Operations — high level`) gets replaced wholesale. The replacement contains three new sections in this order: `## Marker`, `## Resolution probe`, `## Cache (~/.claude/wiki.local.md)`, then a slimmed-down `## Bootstrap` that no longer touches `CLAUDE.md`.

**Step 2: Insert the four replacement sections**

```markdown
## Marker — "is this a wiki?"

A directory is a wiki **iff all four** of these exist together at its root:

- `index.md` (file)
- `log.md` (file)
- `raw/` (directory)
- `wiki/` (directory)

That is the **only** test. The plugin never stamps metadata into the user's `CLAUDE.md` and never adds a hidden marker file. The user's vault stays clean.

If a `CLAUDE.md` exists at the wiki root, read it (Claude Code auto-loads it) and respect any wiki-related guidance the user has written there. Never write to it.

## Resolution probe — "which wiki am I in?"

Run this probe at the start of every operation (`wiki-ingest`, `wiki-query`, `wiki-lint`). Stop at the first step that resolves.

1. **`cwd` has the marker** → use `cwd`.
2. **Walk up parents from `cwd`** to the filesystem root, checking each. → first ancestor with the marker wins.
3. **Read the cache** at `~/.claude/wiki.local.md`. If `last_used` points to a path that still has the marker → use it. If the path no longer has the marker, silently drop the entry and continue.
4. **Notes-tooling autodetect**: if `cwd` contains any of `.obsidian/`, `.logseq/`, `.dendron/`, or `.foam/` (and has no marker) → ask the user *"This looks like a markdown notes directory (detected `<which>`). Initialize a wiki here?"* with options Yes / No, somewhere else / Cancel.
5. **Cache lists `known_vaults`** that aren't `cwd` and still have markers → offer them as numbered options plus "somewhere else".
6. **Ask the user** for a path. Suggest common locations as hints (e.g. existing notes directories under the user's home), but make no assumptions about specific tools.

After successful resolution, **update the cache** (see next section).

If resolution fails (user cancels, path doesn't exist), abort the operation cleanly with a message explaining what's needed.

## Cache (~/.claude/wiki.local.md)

The cache is **advisory**, not authoritative. It speeds up resolution between sessions. The probe always re-verifies the marker before trusting any cached path.

**Location:** `~/.claude/wiki.local.md` (user scope, outside any vault). Same path on macOS, Linux, and Windows; Claude Code resolves `~` correctly.

**Format:** YAML frontmatter (source of truth) plus a short human-readable body.

```markdown
---
plugin: wiki
schema_version: 1
last_used: /Users/alice/Documents/Obsidian/Personal
known_vaults:
  - path: /Users/alice/Documents/Obsidian/Personal
    label: Personal
    last_seen: 2026-04-27
  - path: /Users/alice/notes/reading
    label: Reading list
    last_seen: 2026-04-15
last_updated: 2026-04-27
---

# wiki — vault cache

Auto-managed by the `wiki` plugin. Tracks markdown wikis you've used so the
plugin can find them again on next launch. Safe to edit or delete by hand.
```

**When to write the cache:**

- After successful bootstrap → add a new `known_vaults` entry; set `last_used`.
- After resolution probe steps 1 or 2 succeed → bump `last_seen` on the matching entry; update `last_used` if it changed; create a `known_vaults` entry if this is a new path.
- After step 5 succeeds (user picked a known vault) → bump `last_seen`; update `last_used`.
- After step 6 succeeds (user named a new path) → add to `known_vaults`; set `last_used`.

**When to invalidate:**

- A `known_vaults` entry whose `path` no longer has the marker is silently dropped on next probe. Do not warn the user — vault deletion is normal.

**`schema_version`** stays at `1` until the format changes incompatibly.

## Bootstrap — only when the user opts in

Only run after the resolution probe asks the user and they approve initialization at a specific path. **Never bootstrap silently.**

The plugin creates only its own files — `CLAUDE.md` is the user's territory.

1. Create the four required things at the chosen path:
   - `index.md` — see the Index section above for the exact starter content.
   - `log.md` — single line: `# Log` (entries get appended below).
   - `raw/` (empty directory).
   - `wiki/entities/`, `wiki/concepts/`, `wiki/sources/` (empty subdirectories).
2. Append a `scaffold` entry to `log.md` listing what was created.
3. Update the cache: add the new path to `known_vaults`, set `last_used`.
4. Tell the user: *"Initialized a wiki at `<path>`. To customize defaults (page types, scope, tone), add a `## Wiki` section to a `CLAUDE.md` at that path."* Do not write `CLAUDE.md` for them.
```

**Step 3: Update the opening paragraphs of the skill**

Find this passage near the top:

```markdown
This skill is **shared reference**. Always load it before running any wiki operation. Each operation skill references back here for layout, frontmatter, and bookkeeping rules — and only describes its own workflow.

Each wiki instance has its own `CLAUDE.md` that may override or extend these defaults. When both define something, the wiki's own `CLAUDE.md` wins.
```

Replace the second paragraph with:

```markdown
The user's `CLAUDE.md` (if present at the wiki root) is read but never written. If the user has a `## Wiki` section there, follow its guidance over these defaults. Otherwise these defaults apply.
```

**Step 4: Verify**

```bash
grep -c "^## Marker$\|^## Resolution probe$\|^## Cache" /Users/tuongaz/dev/wiki/skills/wiki-conventions/SKILL.md
grep -c "Create \`CLAUDE.md\` with exactly this content" /Users/tuongaz/dev/wiki/skills/wiki-conventions/SKILL.md
```

Expected output: `3` then `0`.

**Step 5: Commit**

```bash
git -C /Users/tuongaz/dev/wiki add skills/wiki-conventions/SKILL.md
git -C /Users/tuongaz/dev/wiki commit -m "feat(conventions): add resolution probe + cache; stop scaffolding CLAUDE.md"
```

---

## Task 6: Update `wiki-ingest` to use the resolution probe

**Files:**

- Modify: `/Users/tuongaz/dev/wiki/skills/wiki-ingest/SKILL.md`

**Step 1: Update the Preconditions section**

Find:

```markdown
## Preconditions

1. The current working directory is a wiki (or about to become one).
2. The user has identified one source file. If they haven't, ask which file.
3. If `CLAUDE.md`, `index.md`, `log.md`, `raw/`, or `wiki/` are missing, follow the **Bootstrap** section of `wiki-conventions` first. Do not silently overwrite existing files.

One source per ingest. Do not batch.
```

Replace with:

```markdown
## Preconditions

1. **Run the resolution probe** from `wiki-conventions` to determine which wiki to operate on. The probe handles cwd-detection, walk-up, cache lookup, notes-tooling autodetect, and asking the user. From this point on, refer to the resolved path as the *wiki root*.
2. If the resolution probe ended in bootstrap (the user approved initializing a new wiki), proceed against the freshly-bootstrapped wiki root.
3. The user has identified one source file. If they haven't, ask which file.

One source per ingest. Do not batch.
```

**Step 2: Update Step 1 of the Workflow (Locate the source)**

Find:

```markdown
1. **Locate the source.** Verify the file exists. If it isn't already under `raw/`, move it to the appropriate subdirectory (`raw/articles/`, `raw/papers/`, `raw/books/`, `raw/transcripts/`) and tell the user where you put it. Use `git mv` if the wiki is a git repo. Never edit the source — `raw/` is read-only.
```

Replace with:

```markdown
1. **Locate the source.** Verify the file exists. If it isn't already under `<wiki-root>/raw/`, move it to the appropriate subdirectory (`raw/articles/`, `raw/papers/`, `raw/books/`, `raw/transcripts/`) and tell the user where you put it. Use `git mv` if the wiki is a git repo. Never edit the source — `raw/` is read-only.
```

**Step 3: Verify**

```bash
grep -c "Run the resolution probe" /Users/tuongaz/dev/wiki/skills/wiki-ingest/SKILL.md
grep -c "follow the \*\*Bootstrap\*\* section" /Users/tuongaz/dev/wiki/skills/wiki-ingest/SKILL.md
```

Expected output: `1` then `0`.

**Step 4: Commit**

```bash
git -C /Users/tuongaz/dev/wiki add skills/wiki-ingest/SKILL.md
git -C /Users/tuongaz/dev/wiki commit -m "refactor(ingest): defer to wiki-conventions resolution probe"
```

---

## Task 7: Update `wiki-query` to use the resolution probe

**Files:**

- Modify: `/Users/tuongaz/dev/wiki/skills/wiki-query/SKILL.md`

**Step 1: Insert a Preconditions block**

Above the `## When to use` section, insert:

```markdown
## Preconditions

1. **Run the resolution probe** from `wiki-conventions` to determine which wiki to operate on. If no wiki resolves and the user declines to bootstrap, abort cleanly: this skill cannot answer questions without a wiki.
2. From this point on, all paths are relative to the resolved *wiki root*.
```

**Step 2: Update workflow path references**

In `### Phase 1 — answer`, change:

```markdown
1. **Read `index.md` first.** It is the catalog. ...
```

to:

```markdown
1. **Read `<wiki-root>/index.md` first.** It is the catalog. ...
```

Apply the same `<wiki-root>/` prefix to other bare paths in this skill (`wiki/`, `log.md`, `raw/`).

**Step 3: Verify**

```bash
grep -c "^## Preconditions$" /Users/tuongaz/dev/wiki/skills/wiki-query/SKILL.md
grep -c "<wiki-root>" /Users/tuongaz/dev/wiki/skills/wiki-query/SKILL.md
```

Expected output: `1` then `≥3`.

**Step 4: Commit**

```bash
git -C /Users/tuongaz/dev/wiki add skills/wiki-query/SKILL.md
git -C /Users/tuongaz/dev/wiki commit -m "refactor(query): defer to wiki-conventions resolution probe"
```

---

## Task 8: Update `wiki-lint` to use the resolution probe

**Files:**

- Modify: `/Users/tuongaz/dev/wiki/skills/wiki-lint/SKILL.md`

**Step 1: Insert a Preconditions block**

Above `## When to use`, insert:

```markdown
## Preconditions

1. **Run the resolution probe** from `wiki-conventions` to determine which wiki to lint. If no wiki resolves, abort cleanly — there is nothing to lint without a wiki.
2. From this point on, all paths are relative to the resolved *wiki root*.
```

**Step 2: Update path references**

Apply the `<wiki-root>/` prefix to bare paths in this skill (`wiki/`, `index.md`, `log.md`, `raw/`).

**Step 3: Verify**

```bash
grep -c "^## Preconditions$" /Users/tuongaz/dev/wiki/skills/wiki-lint/SKILL.md
grep -c "<wiki-root>" /Users/tuongaz/dev/wiki/skills/wiki-lint/SKILL.md
```

Expected output: `1` then `≥3`.

**Step 4: Commit**

```bash
git -C /Users/tuongaz/dev/wiki add skills/wiki-lint/SKILL.md
git -C /Users/tuongaz/dev/wiki commit -m "refactor(lint): defer to wiki-conventions resolution probe"
```

---

## Task 9: Verification — simulated probe scenarios

**Files:** none modified — this task is structural verification.

**Step 1: Set up scratch fixtures**

```bash
TMP=$(mktemp -d)
echo "Working in $TMP"

# Fixture A: a fully-initialized wiki
mkdir -p "$TMP/wiki-a/wiki/entities" "$TMP/wiki-a/raw"
echo "# Index" > "$TMP/wiki-a/index.md"
echo "# Log" > "$TMP/wiki-a/log.md"

# Fixture B: a directory that looks like an Obsidian vault but isn't a wiki yet
mkdir -p "$TMP/vault-b/.obsidian"
echo "{}" > "$TMP/vault-b/.obsidian/app.json"

# Fixture C: a Logseq-style notes dir
mkdir -p "$TMP/notes-c/.logseq"

# Fixture D: a plain directory
mkdir -p "$TMP/plain-d"

# Fixture E: a wiki nested two levels deep (for walk-up testing)
mkdir -p "$TMP/wiki-e/wiki/concepts" "$TMP/wiki-e/raw" "$TMP/wiki-e/notes/projects"
echo "# Index" > "$TMP/wiki-e/index.md"
echo "# Log" > "$TMP/wiki-e/log.md"

ls -1 "$TMP"
```

Expected output: 5 directory names listed.

**Step 2: Verify each fixture matches the marker rule**

For each fixture, verify by hand the four-thing test:

```bash
for d in wiki-a vault-b notes-c plain-d wiki-e wiki-e/notes/projects; do
  full="$TMP/$d"
  ok="yes"
  for needed in index.md log.md raw wiki; do
    [ -e "$full/$needed" ] || ok="no"
  done
  echo "$d: marker=$ok"
done
```

Expected output:

```
wiki-a: marker=yes
vault-b: marker=no
notes-c: marker=no
plain-d: marker=no
wiki-e: marker=yes
wiki-e/notes/projects: marker=no
```

**Step 3: Walk-from-cwd scenarios**

Walking up from `wiki-e/notes/projects` should hit `wiki-e` (parent has the marker). Verify:

```bash
cd "$TMP/wiki-e/notes/projects"
parent="$PWD"
found=""
while [ "$parent" != "/" ]; do
  ok="yes"
  for needed in index.md log.md raw wiki; do
    [ -e "$parent/$needed" ] || ok="no"
  done
  if [ "$ok" = "yes" ]; then found="$parent"; break; fi
  parent=$(dirname "$parent")
done
echo "walk-up result: $found"
```

Expected output: ends with `wiki-e`.

**Step 4: Confirm notes-tooling autodetect signals**

```bash
for d in vault-b notes-c plain-d; do
  for marker in .obsidian .logseq .dendron .foam; do
    [ -d "$TMP/$d/$marker" ] && echo "$d: notes-tooling=$marker"
  done
done
```

Expected output: `vault-b: notes-tooling=.obsidian` and `notes-c: notes-tooling=.logseq` (no line for `plain-d`).

**Step 5: Cleanup**

```bash
rm -rf "$TMP"
```

**Step 6: Commit (no changes — no commit needed)**

This task only verifies behavior. If verification reveals a flaw in the resolution-probe spec, return to Task 5 and fix.

---

## Task 10: Final validation pass

**Files:** none modified — read-only validation.

**Step 1: Run the plugin-validator agent**

Invoke:

```
Use the plugin-dev:plugin-validator agent to comprehensively validate the plugin at /Users/tuongaz/dev/wiki. Confirm: manifest validity, four skills present, frontmatter correctness on each SKILL.md, no remaining references to commands/agents/CLAUDE.md-scaffolding, proper resolution-probe references in operation skills, security/privacy hygiene.
```

**Step 2: Run the skill-reviewer agent on `wiki-conventions`**

The skill grew during this work; rerun the review:

```
Use the plugin-dev:skill-reviewer agent to review /Users/tuongaz/dev/wiki/skills/wiki-conventions/SKILL.md. Focus on: description quality (trigger conditions only, no workflow summary), imperative writing style, lean body, progressive disclosure, internal consistency between Marker / Resolution probe / Cache / Bootstrap sections.
```

**Step 3: Address findings**

Fold any **critical** findings back into the relevant earlier task as a follow-up commit. Stylistic suggestions can be deferred.

**Step 4: Final structural check**

```bash
find /Users/tuongaz/dev/wiki -type f -not -path '*/\.git/*' | sort
```

Expected output (in order):

```
/Users/tuongaz/dev/wiki/.claude-plugin/plugin.json
/Users/tuongaz/dev/wiki/.gitignore
/Users/tuongaz/dev/wiki/CHANGELOG.md
/Users/tuongaz/dev/wiki/LICENSE
/Users/tuongaz/dev/wiki/README.md
/Users/tuongaz/dev/wiki/docs/plans/2026-04-27-vault-resolution-and-oss-readiness.md
/Users/tuongaz/dev/wiki/skills/wiki-conventions/SKILL.md
/Users/tuongaz/dev/wiki/skills/wiki-ingest/SKILL.md
/Users/tuongaz/dev/wiki/skills/wiki-lint/SKILL.md
/Users/tuongaz/dev/wiki/skills/wiki-query/SKILL.md
```

(Eight files plus this plan plus `.gitignore`.)

**Step 5: Commit any review fixes**

```bash
git -C /Users/tuongaz/dev/wiki add -u
git -C /Users/tuongaz/dev/wiki commit -m "fix: address validator and reviewer findings"
```

---

## Open follow-ups (out of scope here, track separately)

- **Repository URL placeholder.** Tasks 3 and 4 contain `<owner>` placeholders. Replace with the real GitHub username before publishing.
- **CONTRIBUTING.md.** Decide whether to invite PRs. If yes, add a 2-paragraph CONTRIBUTING.md explaining local testing and the writing-skills conventions.
- **Marketplace publication.** Once the repository URL is real, add the plugin to a marketplace (or publish a marketplace alongside it). Out of scope here.

---

## Decisions baked into this plan (push back here, not later)

- **License:** MIT.
- **Cache scope:** user-only (`~/.claude/wiki.local.md`). No project-scope override.
- **Wikilink syntax:** locked to `[[]]`. Not user-configurable.
- **Notes-tooling autodetect set:** `.obsidian/`, `.logseq/`, `.dendron/`, `.foam/`. Add others later only if requested.
- **Bootstrap creates four things, never `CLAUDE.md`.**
- **`schema_version: 1`** in the cache file from day one.

If any of these is wrong, fix it now — don't propagate it through ten tasks.
