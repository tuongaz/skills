---
name: wiki-lint
description: Use when the user asks to "lint the wiki", "health-check the wiki", "find orphans in my notes", "audit the wiki", "look for contradictions or stale claims", or any request to scan a personal-knowledge-base wiki (raw/, wiki/, index.md, log.md) for structural problems and gaps.
---

# Wiki — Lint

Workflow for a non-destructive health check across the wiki. Reports problems; never auto-fixes.

**REQUIRED BACKGROUND:** Always load the `wiki-conventions` skill first. The lint checks below are derived directly from the conventions (frontmatter rules, wikilink rules, index format, log format). The wiki's own `CLAUDE.md` may add or override checks — read it second.

## When to use

Trigger this skill on any wiki audit request:

- "Lint the wiki."
- "What's broken in the wiki?"
- "Any orphan pages?"
- "Are there contradictions I should resolve?"
- "Is the index out of sync?"

Optional scope: a subdirectory like `wiki/entities/` or `wiki/concepts/`. If unscoped, scan the entire `wiki/` tree.

## Checks

Perform every check below. Group findings by severity in the final report.

### Critical (broken — affects correctness)

1. **Red links.** Glob `wiki/**/*.md`, extract `[[slug]]` references with `grep -oE '\[\[[^]|]+'`, and verify each target exists at the expected path under `wiki/`. Report any wikilink whose target file is missing.

2. **Index drift.** Two-way:
   - Files under `wiki/` that are **not** listed in `index.md`.
   - `index.md` entries pointing to files that no longer exist.

3. **Frontmatter violations.** For every `wiki/**/*.md`:
   - Missing `type:` field.
   - `type:` value not in {entity, concept, source-summary, query, overview, plus any extensions declared in the wiki's `CLAUDE.md`}.
   - Missing `created:` or `updated:` (must be valid `YYYY-MM-DD`).
   - `source-summary` page with empty or missing `sources:` list.

4. **Orphaned source files.** Files under `raw/` that have no `wiki/sources/<slug>.md` summary.

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

1. Read `wiki-conventions` and the wiki's `CLAUDE.md`.
2. Run every check above. Use `Glob` + `Grep` heavily; minimise per-file `Read` calls (read only when a check needs the body).
3. Produce a **report** with three sections (Critical / Health / Suggestions). For each finding include the file path and a one-line description. Be specific:
   - ❌ `wiki/concepts/rag.md:42 — wikilink [[chen-2024]] points to missing wiki/sources/chen-2024.md`
   - ✅ `wiki/concepts/rag.md:42 — broken wikilink [[chen-2024]]`
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
