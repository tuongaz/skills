---
name: wiki-query
description: Use when the user asks a question expecting an answer synthesized from their personal-knowledge-base wiki — phrasings like "what does my wiki say about X", "ask the wiki", "search the wiki for", "according to my notes", or any factual question posed inside a directory containing index.md, log.md, raw/, and wiki/.
---

# Wiki — Query

Workflow for answering a question against the wiki, with inline citations, optionally filing the answer back as a new wiki page so explorations compound over time.

**REQUIRED BACKGROUND:** Always load the `wiki-conventions` skill before answering. It defines wikilink syntax, the `index.md` catalog format, and the `log.md` format. The wiki's own `CLAUDE.md` overrides defaults — read it second.

## Preconditions

1. **Run the resolution probe** from `wiki-conventions` to determine which wiki to operate on. If no wiki resolves and the user declines to bootstrap, abort cleanly: this skill cannot answer questions without a wiki.
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
   - For facts that come from a raw source not yet summarized, use a markdown link to the raw path: `[Chen 2024](raw/papers/chen-2024.pdf)`.
   - When the wiki disagrees with itself, surface the disagreement explicitly: "wiki/x says A; wiki/y says B; the contradiction was flagged on YYYY-MM-DD."
   - When the wiki doesn't cover the question, say so. Do not hallucinate. Suggest what the user might ingest next to fill the gap.

4. **Log the query.** Append to `<wiki-root>/log.md` whether or not the answer is filed back:

   ```
   ## [YYYY-MM-DD] query | <one-line gist of the question>

   Question: <verbatim question>
   Answer (1 line): <one-sentence summary>
   Pages consulted: <list>
   ```

5. **Return the full answer to the user.** End with a suggested kebab-case slug they could file the answer back as (e.g. `why-rag-lost-to-long-context`), and ask: *"File this answer as `wiki/queries/<slug>.md`?"*

### Phase 2 — file back (only if user agrees)

If the user approves filing the answer back (yes, "file it", a different slug, or any clear affirmative):

1. Create `<wiki-root>/wiki/queries/<approved-slug>.md` with frontmatter:

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

   File: wiki/queries/<slug>.md
   Index: updated
   ```

4. Confirm to the user: *"Filed as `wiki/queries/<slug>.md` — also added to index.md."*

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
