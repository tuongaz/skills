---
name: wiki-lint
description: Use when the user asks to "lint the wiki", "health-check the wiki", "find orphans in my notes", "audit the wiki", "look for contradictions or stale claims", or any request to scan a personal-knowledge-base wiki (raw/, wiki/, index.md, log.md) for structural problems and gaps.
---

# Wiki — Lint

Workflow for a non-destructive health check across the wiki. Reports problems; never auto-fixes.

The conventions below define the rules this skill validates against. The wiki's own `CLAUDE.md` (at the wiki root) may add or override checks — read it after this section.

## Conventions

### Marker — "is this a wiki?"

A directory is a wiki **iff all four** of these exist together at its root:

- `index.md` (file)
- `log.md` (file)
- `raw/` (directory)
- `wiki/` (directory)

That is the **only** test. The plugin never stamps metadata into the user's `CLAUDE.md` and never adds a hidden marker file.

If a `CLAUDE.md` exists at the wiki root, read it (Claude Code auto-loads it) and respect any wiki-related guidance the user has written there. Never write to it.

### Resolution probe — "which wiki am I in?"

Run this probe at the start of the operation. Stop at the first step that resolves.

1. **`cwd` has the marker** → use `cwd`.
2. **Walk up parents from `cwd`** to the filesystem root, checking each. → first ancestor with the marker wins.
3. **Read the cache** at `~/.claude/wiki.local.md`. If `last_used` points to a path that still has the marker → use it. If the path no longer has the marker, silently drop the entry and continue.
4. **Notes-tooling autodetect**: if `cwd` contains any of `.obsidian/`, `.logseq/`, `.dendron/`, or `.foam/` (and has no marker) → ask the user *"This looks like a markdown notes directory (detected `<which>`). Initialize a wiki here?"* with options:
   - **Yes** → bootstrap at `cwd` (see Bootstrap below).
   - **No, somewhere else** → continue to step 5.
   - **Cancel** → abort the operation.
5. **Cache lists `known_vaults`** that aren't `cwd` and still have markers → offer them as numbered options plus "somewhere else". Picking a known vault → use that path. Picking "somewhere else" → continue to step 6.
6. **Ask the user** for a path. Suggest common locations as hints, but make no assumptions about specific tools.

After successful resolution, update the cache. If resolution fails (user cancels, path doesn't exist), abort the operation cleanly.

### Cache (`~/.claude/wiki.local.md`)

Advisory, not authoritative. The probe always re-verifies the marker before trusting any cached path.

Format: YAML frontmatter (source of truth) plus a short human-readable body.

```markdown
---
plugin: wiki
schema_version: 1
last_used: /Users/alice/Documents/Obsidian/Personal
known_vaults:
  - path: /Users/alice/Documents/Obsidian/Personal
    label: Personal
    last_seen: 2026-04-27
last_updated: 2026-04-27
---

# wiki — vault cache

Auto-managed by the `wiki` plugin. Tracks markdown wikis you've used so the
plugin can find them again on next launch. Safe to edit or delete by hand.
```

Write the cache:
- After successful bootstrap → add a new `known_vaults` entry; set `last_used`.
- After probe steps 1 or 2 succeed → bump `last_seen`; update `last_used` if changed; create a new entry if this is a new path.
- After step 5 succeeds → bump `last_seen`; update `last_used`.
- After step 6 succeeds → add to `known_vaults`; set `last_used`.

A `known_vaults` entry whose `path` no longer has the marker is silently dropped on next probe.

### Bootstrap — only when the user opts in

Only run after the resolution probe asks the user and they approve initialization at a specific path. **Never bootstrap silently.** The plugin creates only its own files — `CLAUDE.md` is the user's territory.

1. Create the four required things at the chosen path:
   - `index.md` — see the Index format below for starter content.
   - `log.md` — single line: `# Log` (entries get appended below).
   - `raw/` (empty directory — flat).
   - `wiki/` (empty directory — flat).
2. Append a `scaffold` entry to `log.md` listing what was created.
3. Update the cache: add the new path to `known_vaults`, set `last_used`.
4. Tell the user: *"Initialized a wiki at `<path>`. To customize defaults (page types, scope, tone), add a `## Wiki` section to a `CLAUDE.md` at that path."* Do not write `CLAUDE.md` for them.

### Layer separation

1. **Raw sources** — `raw/`. Immutable. Read-only. Articles, PDFs, screenshots, papers. Users add files; the maintainer never edits them.
2. **Wiki pages** — `wiki/`. LLM-owned. Created and updated by the maintainer. Users read.
3. **User overrides** (optional) — a `## Wiki` section in the user's `CLAUDE.md` at the wiki root. Read but never written.

`raw/` and `wiki/` are **flat** — every file sits directly under its parent, no subdirectories. Organization is carried by frontmatter `type:` and `index.md` sections, not folders.

### Page types

All page files live directly under `wiki/`. The `type:` frontmatter distinguishes them.

- **entity** — a noun-like subject (person, company, book, place). File: `wiki/<kebab-name>.md`.
- **concept** — an idea, framework, theory, or phenomenon. File: `wiki/<kebab-name>.md`.
- **source-summary** — one page per raw source. File: `wiki/<kebab-name>.md` (suggest a `-summary` slug suffix to disambiguate, e.g. `chen-2024-summary`).
- **query** — optional. A filed-back question + answer. File: `wiki/<kebab-name>.md`.
- **overview** — curated higher-level pages (e.g. `wiki/overview.md`). Use `type: overview`.

Slug collisions across types are not allowed (flat directory). When a candidate slug is already taken, append a disambiguator (`-concept`, `-summary`, `-query`). The user's `CLAUDE.md` may declare additional `type:` values.

### Frontmatter

Every wiki page carries YAML frontmatter:

```yaml
---
type: entity | concept | source-summary | query | overview
tags: [tag1, tag2]
created: 2026-04-21
updated: 2026-04-21
sources:
  - raw/foo.md
  - raw/bar.pdf
---
```

Rules:
- `created` and `updated` use ISO date (YYYY-MM-DD).
- `type` is required. Allowed values: `entity`, `concept`, `source-summary`, `query`, `overview` (plus any extensions in the wiki's `CLAUDE.md`).
- `sources` is **required** on `source-summary` pages and **recommended** on `entity`, `concept`, and `overview` pages. On `query` pages list the wiki pages consulted via their repo paths.
- `updated` **must be bumped to today's date on every edit to the page body or frontmatter**. Do not update it when only cross-linking from another page.
- `tags` are optional; kebab-case when used.

Raw sources have no frontmatter requirement — they're immutable.

### Cross-linking

- **Wiki-to-wiki**: Obsidian wikilinks `[[slug]]`. Link text matches the target file's basename (without `.md`). Filenames are kebab-case (e.g. `wiki/alice-smith.md`), so wikilinks are `[[alice-smith]]`. For display text use pipe syntax: `[[alice-smith|Alice Smith]]`.
- **Wiki-to-raw**: standard markdown links with repo-relative paths. Example: `[Chen et al. 2024](raw/chen-2024.pdf)`.
- **Inline citations**: place `[[wikilinks]]` at the point each fact is stated, not as a bibliography at the bottom.

Cross-link on every mention of an entity or concept that has (or should have) its own page. If a page doesn't exist yet, leave the wikilink — it becomes a red link for lint to surface later.

### Index format

`index.md` is a catalog of all wiki pages, organized by category. Each entry follows the format `- [[slug]] — one-sentence description. (metadata)`:

```markdown
# Index

_Updated 2026-04-21. N pages._

## Entities
- [[alice-smith|Alice Smith]] — researcher focused on RLHF. (3 sources)

## Concepts
- [[retrieval-augmented-generation]] — grounding LLM answers in external documents. (5 sources)

## Source summaries
- [[chen-2024-summary]] — Chen et al. 2024 on long-context retrieval.

## Queries (filed)
- [[why-did-rag-lose-to-long-context]] — filed 2026-04-15.
```

Update `index.md` on every ingest, query-filing, lint pass, and page creation or deletion.

### Log format

`log.md` starts with an `# Log` H1 and is then an append-only chronological record. Every entry begins with a grep-parseable header:

```
## [YYYY-MM-DD] <op> | <title>
```

Where `<op>` is one of: `ingest`, `query`, `query-filed`, `lint`, `scaffold`, `prune`.

Append-only. Never rewrite past entries — they are the history. Prune only via a dedicated `prune` entry that notes what was removed and why.

## When to use

Trigger this skill on any wiki audit request:

- "Lint the wiki."
- "What's broken in the wiki?"
- "Any orphan pages?"
- "Are there contradictions I should resolve?"
- "Is the index out of sync?"

Optional scope: a `type:` filter (e.g. only `entity` pages, only `concept` pages). If unscoped, scan all of `wiki/`.

## Checks

Perform every check below. Group findings by severity in the final report.

### Critical (broken — affects correctness)

1. **Red links.** Glob `wiki/*.md` (flat — no subdirectories), extract `[[slug]]` references with `grep -oE '\[\[[^]|]+'`, and verify each target exists as `wiki/<slug>.md`. Report any wikilink whose target file is missing. Also flag any wiki page that lives in a subdirectory under `wiki/` (a structural violation of the flat-directory convention).

2. **Index drift.** Two-way:
   - Files under `wiki/` that are **not** listed in `index.md`.
   - `index.md` entries pointing to files that no longer exist.

3. **Frontmatter violations.** For every `wiki/*.md`:
   - Missing `type:` field.
   - `type:` value not in {entity, concept, source-summary, query, overview, plus any extensions declared in the wiki's `CLAUDE.md`}.
   - Missing `created:` or `updated:` (must be valid `YYYY-MM-DD`).
   - `source-summary` page with empty or missing `sources:` list.

4. **Orphaned source files.** Files under `raw/` that have no source-summary page in `wiki/` (i.e. no `wiki/<slug>.md` with `type: source-summary` and the raw path listed in its `sources:` frontmatter). Also flag any subdirectory under `raw/` (a structural violation of the flat-directory convention).

### Health (flagged — needs human review)

1. **Orphan pages.** Pages with no inbound `[[wikilink]]` from any other wiki page. Source-summary pages may legitimately be terminal — surface those separately.

2. **Contradictions.** Grep for the convention's contradiction marker (`> ⚠️ Contradiction:` or text containing "contradicts" near a wikilink). List each occurrence.

3. **Stale claims (heuristic).** Pages whose `updated:` date is older than the `created:` date of the most recent source listed in their `sources:` frontmatter. Heuristic, not certainty — surface with that caveat.

4. **Missing cross-references.** For each page, scan body text for plain-text mentions of subjects that **have** their own wiki page but are **not** wrapped in `[[ ]]`. Use the index as the authoritative list of page subjects.

### Suggestions (gaps — opportunities)

1. **Missing pages.** Subjects mentioned across two or more pages with no page of their own. Suggest creating an entity or concept page.

2. **Follow-up questions.** Open questions captured on pages (sections like "Open questions" or "TODO") that haven't been resolved. List as `wiki-query` candidates.

3. **Sources to seek.** Topics where the wiki has thin coverage (page exists but `sources:` lists only one or zero raw files). Suggest the user find more sources.

## Workflow

1. Run the resolution probe (see Conventions above) and read the wiki's `CLAUDE.md` if it exists.
2. Run every check above. Use `Glob` + `Grep` heavily; minimise per-file `Read` calls (read only when a check needs the body).
3. Produce a **report** with three sections (Critical / Health / Suggestions). For each finding include the file path and a one-line description. Be specific:
   - ❌ `wiki/rag.md:42 — wikilink [[chen-2024]] points to missing wiki/chen-2024.md`
   - ✅ `wiki/rag.md:42 — broken wikilink [[chen-2024]]`
4. Append a `lint` entry to `log.md` with **counts only**, not the full report:

   ```
   ## [YYYY-MM-DD] lint | scope: <all | wiki/entities | ...>

   Critical: <n>  (red-links: a, drift: b, frontmatter: c, orphan-sources: d)
   Health:   <n>  (orphan-pages: a, contradictions: b, stale: c, missing-xrefs: d)
   Suggestions: <n>
   ```

5. Print the full report to the user.
6. **Do not auto-fix.** Never. The user reads the report and decides what to address.

If the user asks to fix something specific from the report afterwards, route them to `wiki-ingest` (if it needs a new source) or help directly for trivial single-page fixes. Never bulk-fix lint findings.

## Guardrails

- Read-only against `wiki/` and `raw/`. The only write is the single `lint` entry to `log.md`.
- No auto-fix mode. There is no `--fix` flag, no "fix critical only" shortcut. Report-only.
- Do not delete orphan pages. Flag them; the user decides.
- If a check would require reading every page body (e.g. missing cross-references), keep token use bounded — sample if `wiki/` is very large (>500 pages) and note the sampling in the report.

## Common mistakes

| Mistake | Fix |
|---|---|
| Auto-fixing red links by creating empty stub pages | Don't. Flag and let the user ingest a real source. |
| Treating every orphan as a problem | Source-summary pages are often terminal; surface them separately from true orphans. |
| Reporting heuristic stale-claim flags as certainties | Always note "heuristic" — `updated:` lag isn't proof of staleness. |
| Putting the full report into `log.md` | Log gets counts only; the report goes to the user. |
| Skipping the log entry | Lint passes are themselves wiki history. Log every one. |
| Globbing every page body upfront | Use `Glob` for paths, `Grep` for patterns; only `Read` page bodies when a check requires it. |
