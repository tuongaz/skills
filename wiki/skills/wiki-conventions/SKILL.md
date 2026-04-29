---
name: wiki-conventions
description: Use when working in a personal-knowledge-base wiki (a directory containing some combination of CLAUDE.md, index.md, log.md, raw/, wiki/), or whenever wiki-ingest, wiki-query, or wiki-lint runs. Provides the shared layout, frontmatter, wikilink, index, and log conventions the operation skills consume.
---

# Wiki Conventions

The `wiki` plugin maintains a personal knowledge base as a directory of markdown files. This skill defines the default layout, page types, frontmatter, linking rules, and bookkeeping conventions that the operation skills (`wiki-ingest`, `wiki-query`, `wiki-lint`) all share.

This skill is **shared reference**. Always load it before running any wiki operation. Each operation skill references back here for layout, frontmatter, and bookkeeping rules — and only describes its own workflow.

The user's `CLAUDE.md` (if present at the wiki root) is read but never written. If the user has a `## Wiki` section there, follow its guidance over these defaults. Otherwise these defaults apply.

## Layer separation

Keep three layers distinct.

1. **Raw sources** — `raw/`. Immutable. Read-only. Articles, PDFs, screenshots, papers. Users add files; the maintainer never edits them.
2. **Wiki pages** — `wiki/`. LLM-owned. Created, updated, and deleted by the maintainer. Users read; the maintainer writes.
3. **User overrides** (optional) — a `## Wiki` section in the user's `CLAUDE.md` at the wiki root. Read but never written by the plugin.

## Default directory layout

```
my-wiki/
├── CLAUDE.md              # optional; user-owned, never written by the plugin
├── index.md               # catalog of wiki/ pages
├── log.md                 # chronological op record
├── raw/                   # immutable sources
│   ├── articles/
│   ├── papers/
│   └── assets/            # images, screenshots
└── wiki/                  # LLM-generated pages
    ├── entities/          # people, orgs, products, places
    ├── concepts/          # ideas, theories, frameworks
    └── sources/           # one summary page per raw source
```

Subdirectories under `wiki/` are suggestions. The user's `CLAUDE.md` may define additional categories (`wiki/themes/`, `wiki/chapters/`, `wiki/queries/`).

## Page types

- **entity** — a noun-like subject (person, company, book, place). File: `wiki/entities/<kebab-name>.md`.
- **concept** — an idea, framework, theory, or phenomenon. File: `wiki/concepts/<kebab-name>.md`.
- **source-summary** — one page per raw source. Takeaways, key claims, quotes. File: `wiki/sources/<kebab-name>.md`.
- **query** — optional. A question the user asked and its synthesized answer, filed back as a wiki page. File: `wiki/queries/<kebab-name>.md`.
- **overview** — higher-level curated pages (e.g. `wiki/overview.md`, `wiki/theses.md`). Use `type: overview` in frontmatter.

Extend with additional types when the user's `CLAUDE.md` defines them (e.g. `character`, `chapter`, `theme` for a book-reading wiki).

## Frontmatter

Every wiki page carries YAML frontmatter:

```yaml
---
type: entity | concept | source-summary | query | overview
tags: [tag1, tag2]
created: 2026-04-21
updated: 2026-04-21
sources:
  - raw/articles/foo.md
  - raw/papers/bar.pdf
---
```

Rules:
- `created` and `updated` use ISO date (YYYY-MM-DD).
- `type` is required (enables Obsidian Dataview queries). Allowed values: `entity`, `concept`, `source-summary`, `query`, `overview`.
- `sources` is **required** on `source-summary` pages (lists the single raw source) and **recommended** on `entity`, `concept`, and `overview` pages (listing every raw file whose ingestion contributed to the page). On `query` pages list the wiki pages consulted via their repo paths.
- `updated` **must be bumped to today's date on every edit to the page body or frontmatter**. Do not update it when only cross-linking from another page.
- `tags` are optional; kebab-case when used.

Raw sources have no frontmatter requirement — they're immutable.

## Cross-linking

- **Wiki-to-wiki**: Obsidian wikilinks `[[Page Name]]`. The link text must match the target file's basename (without `.md`). Filenames are always kebab-case (e.g. `wiki/entities/alice-smith.md`), so wikilinks are written as `[[alice-smith]]`, **not** `[[Alice Smith]]`. For display text, use the pipe syntax: `[[alice-smith|Alice Smith]]`. Obsidian also resolves case-insensitive Title-Case forms, but kebab matches the filename exactly and avoids ambiguity.
- **Wiki-to-raw**: standard markdown links with repo-relative paths. Example: `[Chen et al. 2024](raw/papers/chen-2024.pdf)`.
- **Inline citations**: place `[[wikilinks]]` at the point each fact is stated, not as a bibliography at the bottom.

Cross-link on every mention of an entity or concept that has (or should have) its own page. If a page doesn't exist yet, leave the wikilink — it becomes a red link for lint to surface later.

## Index

`index.md` is a catalog of all wiki pages, organized by category. Each entry is one line: link + one-sentence description + optional metadata (source count, last updated).

Structure. Each entry must follow the format ``- [[slug]] — one-sentence description. (metadata)``:

```markdown
# Index

_Updated 2026-04-21. N pages._

## Entities
- [[alice-smith|Alice Smith]] — researcher focused on RLHF. (3 sources)
- [[openai|OpenAI]] — AI lab, founded 2015. (7 sources)

## Concepts
- [[retrieval-augmented-generation]] — grounding LLM answers in external documents. (5 sources)

## Source summaries
- [[chen-2024-summary]] — Chen et al. 2024 on long-context retrieval.

## Queries (filed)
- [[why-did-rag-lose-to-long-context]] — filed 2026-04-15.
```

Update `index.md` on every ingest, query-filing, lint pass, and page creation or deletion.

## Log

`log.md` starts with an `# Log` H1 and is then an append-only chronological record. Every entry begins with a predictable header so it's grep-parseable:

```
## [YYYY-MM-DD] <op> | <title>
```

Where `<op>` is one of:
- `ingest` — a source was ingested.
- `query` — a query was run but **not** filed back. Log the question and a one-line summary of the answer. No files changed.
- `query-filed` — a query answer was filed as `wiki/queries/<slug>.md`. List the new file plus any index update.
- `lint` — a lint pass ran. Top-line counts only.
- `scaffold` — fresh wiki was bootstrapped.
- `prune` — pages were removed (noting which and why).

Entry body: what happened, which pages were touched, anything noteworthy (contradictions, new questions).

Example:

```markdown
## [2026-04-21] ingest | Chen et al. 2024 — Long-context retrieval

Source: raw/papers/chen-2024.pdf
Created: wiki/sources/chen-2024-summary.md
Updated: wiki/concepts/retrieval-augmented-generation.md, wiki/entities/alice-smith.md, index.md
Noteworthy: contradicts claim in [[rag-is-dead]] about retention. Flagged for follow-up.

## [2026-04-21] lint | scheduled health-check

Orphans: 1 ([[foo-legacy]]). Contradictions: 1 flagged. Gaps: 2 suggested.
```

Append-only. Never rewrite past entries — they are the history. Prune only via a dedicated `prune` entry that notes what was removed and why.

A handy command for recent activity:

```
grep "^## \[" log.md | tail -10
```

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
4. **Notes-tooling autodetect**: if `cwd` contains any of `.obsidian/`, `.logseq/`, `.dendron/`, or `.foam/` (and has no marker) → ask the user *"This looks like a markdown notes directory (detected `<which>`). Initialize a wiki here?"* with options:
   - **Yes** → bootstrap at `cwd` (see Bootstrap section).
   - **No, somewhere else** → continue to step 5.
   - **Cancel** → abort the operation.
5. **Cache lists `known_vaults`** that aren't `cwd` and still have markers → offer them as numbered options plus "somewhere else". Picking a known vault → use that path. Picking "somewhere else" → continue to step 6.
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

The `label` field defaults to the basename of `path` (e.g. `Personal` for `/Users/alice/Documents/Obsidian/Personal`); the user may edit it freely. The `last_seen` field is updated by the probe; `last_used` always points to the most recently resolved vault.

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

## Operations — high level

The plugin offers three operations. Each lives in its own skill which loads automatically based on what the user asks:

- **`wiki-ingest`** — read one source file, decide which pages it affects, create/update them, update `index.md`, append an `ingest` entry to `log.md`.
- **`wiki-query`** — read `index.md` first to find candidates, drill in, synthesize an answer with `[[wikilink]]` citations. Log a `query` entry whether or not the answer is filed back. If filed, create `wiki/queries/<slug>.md` and log a separate `query-filed` entry.
- **`wiki-lint`** — scan wiki pages for contradictions, orphans, stale claims, missing cross-references, and gaps. Produce a report; append a `lint` entry with top-line counts. Do not auto-fix.

Each operation skill is the source of truth for its workflow. This file just defines the shared conventions they all consume.

## Non-goals

- No automatic file deletion. Stale or orphaned pages are flagged by lint; the user decides.
- No touching `raw/`. Ever.
- No silent schema changes. When conventions need to change, update the wiki's `CLAUDE.md` and note it in `log.md`.
- No batch ingest. One source per `/wiki:ingest` call keeps edits reviewable.
