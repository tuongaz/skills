---
name: wiki-ingest
description: Use when the user asks to "ingest", "add to the wiki", "summarize this into the wiki", "process this article/paper/book chapter", drops a file path expecting it to be filed into a wiki, or wants a new source absorbed into a personal-knowledge-base wiki built around raw/, wiki/, index.md, and log.md.
---

# Wiki — Ingest

Workflow for absorbing one new source into a personal-knowledge-base wiki. Run when the user wants a file (article, paper, book chapter, screenshot, transcript) summarized into the wiki and integrated with existing entity/concept pages.

The conventions below define the wiki's layout, frontmatter, wikilink rules, index format, log format, and bootstrap procedure. The wiki's own `CLAUDE.md` (at the wiki root) overrides these defaults — read it after this section.

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

## Preconditions

1. **Run the resolution probe** (see Conventions above) to determine which wiki to operate on. The probe handles cwd-detection, walk-up, cache lookup, notes-tooling autodetect, and asking the user. From this point on, refer to the resolved path as the *wiki root*.
2. If the resolution probe ended in bootstrap (the user approved initializing a new wiki), proceed against the freshly-bootstrapped wiki root.
3. The user has identified one source file. If they haven't, ask which file.

One source per ingest. Do not batch.

## Workflow

1. **Locate the source.** Verify the file exists. If it isn't already under `<wiki-root>/raw/`, move it directly into `raw/` (flat — never create subdirectories) and tell the user where you put it. Use `git mv` if the wiki is a git repo. Never edit the source — `raw/` is read-only.

2. **Read the source.** For PDFs use the Read tool's `pages` parameter and read iteratively. For long markdown/text, read in chunks. For images embedded in markdown, surface them to the user only if needed for understanding — don't load every image.

3. **Decide which pages the source affects.** Glob `wiki/*.md` (flat — no subdirectories) and grep for entity/concept names that appear in the source. Use the `type:` frontmatter on each page to filter by category. Categorize:
   - **New source-summary** (always): one new page at `wiki/<kebab-slug>.md` with `type: source-summary`. Suggest a `-summary` suffix on the slug to disambiguate from entity/concept pages.
   - **Existing entity/concept pages** to update: any page whose subject the source discusses with new information, new framing, or contradicting claims.
   - **New entity/concept pages** to create: subjects that recur in the source but have no page yet. File at `wiki/<kebab-slug>.md` with the appropriate `type:`.

4. **Write the source-summary page.** Frontmatter has `type: source-summary`, `created`/`updated` set to today, and `sources:` listing the single raw path. Body has: one-paragraph summary, key takeaways as bullets, notable quotes with section refs, and `[[wikilink]]` cross-references inline at every entity/concept mention.

5. **Update or create entity/concept pages.** For each affected page:
   - If updating: append new claims into the right section, add the source path to the `sources:` frontmatter list, bump `updated:` to today.
   - If creating: write the standard skeleton (frontmatter + 1-paragraph summary + sections like "Key claims", "Open questions", "Mentioned in").
   - When the source contradicts an existing claim, **do not silently rewrite**. Flag inline with a `> ⚠️ Contradiction:` callout citing both the older `[[source-summary]]` and the new one. The user resolves contradictions, not you.

6. **Update `index.md`.** Add new pages under the right section, bump source counts on updated pages, refresh the `_Updated YYYY-MM-DD. N pages._` line.

7. **Append to `log.md`.** Use the grep-parseable header:

   ```
   ## [YYYY-MM-DD] ingest | <source title>

   Source: raw/<...>
   Created: <list of new wiki/ paths>
   Updated: <list of modified wiki/ paths, plus index.md>
   Noteworthy: <contradictions flagged, new questions raised, anything unusual>
   ```

8. **Report back.** Print a terse summary:

   ```
   Mode: ingest
   Source: raw/...
   Created: <count> file(s)   [paths]
   Modified: <count> file(s)  [paths]
   Flagged: <count> issue(s)  [one-line each]
   ```

   Then surface anything the user should follow up on (a flagged contradiction, a new entity that needs a page, an open question worth a `/wiki-query` later).

## Guardrails

- Write only under `wiki/` (flat — never create subdirectories), plus `index.md`, `log.md`, and (during bootstrap) `CLAUDE.md`. Anything else needs explicit user approval.
- `raw/` is read-only after ingest, and stays flat — never create subdirectories under it. Treat it as immutable.
- Never delete pages. Orphans get flagged by `wiki-lint`; deletion is a separate user decision.
- When uncertain whether to update an existing page or create a new one, **prefer updating**. Near-duplicate pages degrade the wiki's coherence.
- If the wiki's `CLAUDE.md` overrides any default convention, follow the override and note the divergence in the log entry the first time it's applied.

## Common mistakes

| Mistake | Fix |
|---|---|
| Editing the raw source file | Stop. `raw/` is read-only. Re-read the convention. |
| Bibliography at the bottom of a page | Replace with inline `[[wikilinks]]` at each cited fact. |
| Silently rewriting a contradicted claim | Add `> ⚠️ Contradiction:` callout instead. Let the user adjudicate. |
| Forgetting to bump `updated:` on a touched page | Bump it on every body or frontmatter edit. |
| Batch-ingesting multiple sources in one call | Split into one ingest per source so each is reviewable. |
| Skipping the log entry | Every operation produces exactly one log entry. No exceptions. |
