---
name: wiki-ingest
description: Use when the user asks to "ingest", "add to the wiki", "summarize this into the wiki", "process this article/paper/book chapter", drops a file path expecting it to be filed into a wiki, or wants a new source absorbed into a personal-knowledge-base wiki built around raw/, wiki/, index.md, and log.md.
---

# Wiki — Ingest

Workflow for absorbing one new source into a personal-knowledge-base wiki. Run when the user wants a file (article, paper, book chapter, screenshot, transcript) summarized into the wiki and integrated with existing entity/concept pages.

**REQUIRED BACKGROUND:** Always load the `wiki-conventions` skill before doing any work. It defines layout, frontmatter, wikilink rules, the `index.md` and `log.md` formats, and the bootstrap procedure. The wiki's own `CLAUDE.md` (at the wiki root) overrides defaults — read it second.

## Preconditions

1. **Run the resolution probe** from `wiki-conventions` to determine which wiki to operate on. The probe handles cwd-detection, walk-up, cache lookup, notes-tooling autodetect, and asking the user. From this point on, refer to the resolved path as the *wiki root*.
2. If the resolution probe ended in bootstrap (the user approved initializing a new wiki), proceed against the freshly-bootstrapped wiki root.
3. The user has identified one source file. If they haven't, ask which file.

One source per ingest. Do not batch.

## Workflow

1. **Locate the source.** Verify the file exists. If it isn't already under `<wiki-root>/raw/`, move it to the appropriate subdirectory (`raw/articles/`, `raw/papers/`, `raw/books/`, `raw/transcripts/`) and tell the user where you put it. Use `git mv` if the wiki is a git repo. Never edit the source — `raw/` is read-only.

2. **Read the source.** For PDFs use the Read tool's `pages` parameter and read iteratively. For long markdown/text, read in chunks. For images embedded in markdown, surface them to the user only if needed for understanding — don't load every image.

3. **Decide which pages the source affects.** Glob `wiki/entities/`, `wiki/concepts/`, `wiki/sources/` and grep for entity/concept names that appear in the source. Categorize:
   - **New source-summary** (always): one new page at `wiki/sources/<kebab-slug>.md`.
   - **Existing entity/concept pages** to update: any page whose subject the source discusses with new information, new framing, or contradicting claims.
   - **New entity/concept pages** to create: subjects that recur in the source but have no page yet.

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

- Write only under `wiki/`, plus `index.md`, `log.md`, and (during bootstrap) `CLAUDE.md`. Anything else needs explicit user approval.
- `raw/` is read-only after ingest. Treat it as immutable.
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
