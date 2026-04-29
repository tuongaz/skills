---
name: wiki-query
description: Use when the user asks a question expecting an answer synthesized from their personal-knowledge-base wiki — phrasings like "what does my wiki say about X", "ask the wiki", "search the wiki for", "according to my notes", or any factual question posed inside a directory containing index.md, log.md, raw/, and wiki/.
---

# Wiki — Query

Workflow for answering a question against the wiki, with inline citations, optionally filing the answer back as a new wiki page so explorations compound over time.

The conventions below define how to find the wiki, read its pages, write wikilinks, and log queries. The wiki's own `CLAUDE.md` (at the wiki root) overrides these defaults — read it after this section.

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

1. **Run the resolution probe** (see Conventions above) to determine which wiki to operate on. If no wiki resolves and the user declines to bootstrap, abort cleanly: this skill cannot answer questions without a wiki.
2. From this point on, all paths are relative to the resolved *wiki root*.

## When to use

Trigger this skill on any question phrased as a request for synthesized knowledge from the wiki. Common forms:

- "What does the wiki say about <X>?"
- "What did <author> argue in <paper>?"
- "Has anything contradicted <claim>?"
- "Compare <X> and <Y> based on what we've ingested."
- "Summarize what we know about <topic>."

Do **not** use this skill for: editing pages, ingesting a new source (use `wiki-ingest`), or wiki health checks (use `wiki-lint`).

## Workflow

### Phase 1 — answer

1. **Read `<wiki-root>/index.md` first.** It is the catalog. Use it to shortlist candidate pages by category (entities, concepts, sources, queries). Do not glob the entire `wiki/` tree blindly.

2. **Drill into shortlisted pages.** Read just enough to answer. Grep `<wiki-root>/wiki/` only when the index alone doesn't surface a relevant page.

3. **Synthesize the answer.**
   - Place `[[slug]]` wikilinks inline at the point each fact is cited — never as a trailing bibliography. Use `[[slug|Display Text]]` when the slug doesn't read naturally in prose.
   - For facts that come from a raw source not yet summarized, use a markdown link to the raw path: `[Chen 2024](raw/chen-2024.pdf)`.
   - When the wiki disagrees with itself, surface the disagreement explicitly: "wiki/x says A; wiki/y says B; the contradiction was flagged on YYYY-MM-DD."
   - When the wiki doesn't cover the question, say so. Do not hallucinate. Suggest what the user might ingest next to fill the gap.

4. **Log the query.** Append to `<wiki-root>/log.md` whether or not the answer is filed back:

   ```
   ## [YYYY-MM-DD] query | <one-line gist of the question>

   Question: <verbatim question>
   Answer (1 line): <one-sentence summary>
   Pages consulted: <list>
   ```

5. **Return the full answer to the user.** End with a suggested kebab-case slug they could file the answer back as (e.g. `why-rag-lost-to-long-context`), and ask: *"File this answer as `wiki/<slug>.md`?"*

### Phase 2 — file back (only if user agrees)

If the user approves filing the answer back (yes, "file it", a different slug, or any clear affirmative):

1. Create `<wiki-root>/wiki/<approved-slug>.md` (flat — never under a `queries/` subdirectory) with frontmatter:

   ```yaml
   ---
   type: query
   tags: []
   created: YYYY-MM-DD
   updated: YYYY-MM-DD
   sources:
     - <wiki page paths consulted, repo-relative>
   ---
   ```

   Body: the full answer, preserving inline `[[wikilinks]]` and any markdown links to `raw/` files. Lead with the question as an H1 or in a callout.

2. Update `<wiki-root>/index.md` — add the new query under `## Queries (filed)`.

3. Append a separate `query-filed` entry to `<wiki-root>/log.md`:

   ```
   ## [YYYY-MM-DD] query-filed | <slug>

   File: wiki/<slug>.md
   Index: updated
   ```

4. Confirm to the user: *"Filed as `wiki/<slug>.md` — also added to index.md."*

If the user declines, leave the wiki untouched. Confirm: *"Answer not filed."*

## Guardrails

- Read-only by default. Phase 1 must not modify any wiki page (only `log.md` is written, as a query entry).
- Do not invent slugs without confirmation. Suggest one; let the user accept or override.
- Do not file an answer back without explicit user approval. A user asking a question is not the same as approving a new wiki page.
- If the question's answer would be better expressed as updates to existing entity/concept pages (rather than a new query page), say so — and route the user to `wiki-ingest` if a new source is needed first.

## Common mistakes

| Mistake | Fix |
|---|---|
| Trailing bibliography of citations | Move every citation inline at the point of the claim. |
| Globbing `wiki/**/*.md` before reading `index.md` | Read `index.md` first. It exists for this. |
| Hallucinating a fact the wiki doesn't support | If the wiki doesn't cover it, say so and suggest a source to ingest. |
| Auto-filing the answer without asking | Phase 2 requires explicit user approval. |
| Skipping the `query` log entry on unfiled queries | Log every query — that's how the user sees their exploration history. |
| Smoothing over a contradiction in the answer | Surface contradictions; don't pick a side silently. |
