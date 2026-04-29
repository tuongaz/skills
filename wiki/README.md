# wiki — a Claude Code plugin for a personal knowledge base

Turns Claude Code into a disciplined maintainer of a markdown wiki. You curate the sources. Claude does the bookkeeping.

Based on the [LLM Wiki pattern](https://jackclark.net/llm-wiki/): a persistent, compounding knowledge base where the LLM incrementally ingests sources, maintains cross-references, flags contradictions, and answers queries against an evolving synthesis — instead of re-deriving knowledge from raw documents on every query (the RAG default).

## What it does

The plugin ships **three skills** that auto-load based on what you say:

| Skill | Triggers on phrasings like |
|---|---|
| **`wiki-ingest`** | "add this to the wiki", "ingest `foo.md`", "summarize this paper into my notes", "process `raw/bar.md`" |
| **`wiki-query`** | "what does my wiki say about X?", "ask the wiki", "according to my notes…", any factual question asked inside a wiki directory |
| **`wiki-lint`** | "lint the wiki", "health-check the wiki", "find orphans / contradictions / red links" |

Each skill carries the full conventions inline (layout, frontmatter, wikilinks, index/log format) so it operates self-contained — no separate reference skill to load first.

There are no slash commands and no subagent. Skills load when the description matches what you're doing. You just talk to Claude in a wiki directory.

## Installation

Pick one of the following depending on how you want to manage the plugin.

### Option 1 — Install from a local clone (recommended for development)

Clone this repo somewhere stable, then point Claude Code at it as a marketplace and install:

```sh
git clone <this-repo-url> ~/.claude/plugins/wiki
```

In Claude Code:

```
/plugin marketplace add ~/.claude/plugins/wiki
/plugin install wiki@wiki
```

The first command registers the cloned directory as a marketplace; the second installs the plugin from it. Updates are pulled by running `git pull` in the clone and then `/plugin update wiki@wiki`.

### Option 2 — One-shot, per-session (no install)

Useful for trying the plugin without registering it:

```sh
claude --plugin-dir /path/to/wiki
```

The plugin is active for that session only. Replace `/path/to/wiki` with the absolute path to the clone (e.g. `~/.claude/plugins/wiki`).

### Option 3 — Project-scoped install

To make the plugin available only inside a specific wiki project, copy or symlink the plugin into the project's `.claude/plugins/` directory:

```sh
mkdir -p ~/my-wiki/.claude/plugins
ln -s ~/.claude/plugins/wiki ~/my-wiki/.claude/plugins/wiki
```

Claude Code auto-discovers project-scoped plugins when launched from inside `~/my-wiki/`.

### Verify installation

After install, in Claude Code, run `/plugin` and confirm `wiki` is enabled. To verify a skill triggers correctly, ask:

> "Lint my wiki."

Claude should announce that it's loading the `wiki-lint` skill before responding (and abort cleanly if there's no wiki at the current location).

## Bootstrapping a new wiki

1. Create an empty directory for your wiki and `cd` into it.
2. Launch Claude Code (`claude` or with `--plugin-dir` per Option 2).
3. Drop your first source into the directory (anywhere — Claude will move it under `raw/`).
4. Tell Claude something like *"ingest `some-article.md` into the wiki"*. The `wiki-ingest` skill loads. If this is a fresh directory, the skill runs its resolution probe and asks whether to initialize a wiki here. On approval it scaffolds (note: **never** writes `CLAUDE.md` — that's yours):
   - `index.md` — catalog of pages.
   - `log.md` — chronological record of operations.
   - `raw/` — immutable source files (flat — no subdirectories).
   - `wiki/` — LLM-generated pages (flat — no subdirectories; pages classified by `type:` frontmatter).

   You can optionally add a `CLAUDE.md` with a `## Wiki` section at the wiki root to customize behavior — the plugin reads it but never modifies it.
5. Browse the result in any markdown viewer — Obsidian, Logseq, Foam, Dendron, VS Code, plain `cat`. The wiki is just a directory of markdown files — keep it under git and commit after ingests to track how your understanding evolves.

## Layout (default)

```
my-wiki/
├── CLAUDE.md              # optional; user-owned, never written by the plugin
├── index.md               # catalog
├── log.md                 # chronological record
├── raw/                   # immutable sources (flat — no subdirectories)
└── wiki/                  # LLM-maintained pages (flat — no subdirectories)
```

Pages under `wiki/` are categorized by `type:` frontmatter (`entity`, `concept`, `source-summary`, `query`, `overview`), not by folder.

## Conventions

**Frontmatter** on every wiki page:

```yaml
---
type: entity | concept | source-summary | query | overview
tags: [tag1, tag2]
created: 2026-04-21
updated: 2026-04-21
sources:
  - raw/foo.md
---
```

**Cross-links**:
- Wiki-to-wiki: `[[slug]]` (Obsidian wikilinks; use `[[slug|Display]]` for prose)
- Wiki-to-raw: `[Chen 2024](raw/chen-2024.pdf)`

**Log entries** begin with a predictable header so they're grep-parseable:

```sh
grep "^## \[" log.md | tail -10
```

Full spec: each operation skill (`wiki-ingest`, `wiki-query`, `wiki-lint`) carries the conventions inline under its `## Conventions` section. Each wiki instance's own `CLAUDE.md` may override any default.

## How it fits together

```
        ┌─ you, in a wiki dir ─────────┐
        │ "ingest this paper"          │
        │ "what does the wiki say…"    │
        │ "lint the wiki"              │
        └──────────────┬───────────────┘
                       ▼
        ┌──────────────────────────────┐
        │ Claude Code matches the      │
        │ phrasing to one of:          │
        │   • wiki-ingest              │
        │   • wiki-query               │
        │   • wiki-lint                │
        │ each carrying conventions    │
        │ inline (self-contained).     │
        └──────────────┬───────────────┘
                       ▼
        ┌──────────────────────────────┐
        │ reads:                       │
        │   - wiki CLAUDE.md           │
        │   - raw/ sources             │
        │   - wiki/ pages              │
        │ writes:                      │
        │   - wiki/ pages              │
        │   - index.md, log.md         │
        │ never touches raw/           │
        └──────────────────────────────┘
```

## Tips

- **Web clippers** like [Obsidian Web Clipper](https://obsidian.md/clipper) are the fastest way to get articles into `raw/` as markdown.
- **Obsidian Dataview** pairs well with the frontmatter (try `TABLE updated FROM #rag`).
- **Graph view** in Obsidian shows the shape of your wiki — useful after ~10 ingests.
- Keep the wiki in git. Commit after each ingest to track how your understanding evolves over time.

## Plugin structure

```
wiki/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── wiki-ingest/SKILL.md
│   ├── wiki-query/SKILL.md
│   └── wiki-lint/SKILL.md
└── README.md
```

## Privacy

This plugin is fully local — it makes no network calls of its own and emits no telemetry. The plugin only reads and writes:

- Markdown files inside the wiki directory you point it at (`index.md`, `log.md`, and the pages under `wiki/`).
- A small cache at `~/.claude/wiki.local.md` (created the first time the plugin successfully resolves a wiki) recording your last-used wiki path so the plugin can find it next session.

You can inspect or delete the cache at any time. Note that operations may still trigger Claude Code's own network-using tools (e.g. WebFetch when ingesting a URL), since those run in the host harness, not the plugin — that's a Claude Code permission decision, not something the plugin requests on its own.

## License

MIT.
