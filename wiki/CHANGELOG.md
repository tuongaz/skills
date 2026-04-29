# Changelog

All notable changes to this plugin will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Flat directories**: `raw/` and `wiki/` no longer use subdirectories. Pages are categorized by frontmatter `type:` and `index.md` sections instead of folders.
- **Inlined conventions**: each operation skill (`wiki-ingest`, `wiki-query`, `wiki-lint`) now carries the full conventions (marker, resolution probe, cache, bootstrap, layout, frontmatter, wikilinks, index/log format) inline under its own `## Conventions` section.

### Removed

- **`wiki-conventions` skill**: deleted. Its content is now inlined into each operation skill so they're self-contained.

## [0.1.0] - 2026-04-27

### Added

- Four skills: `wiki-conventions`, `wiki-ingest`, `wiki-query`, `wiki-lint`.
- Vault resolution probe (cwd → walk-up → cache → notes-tooling autodetect → ask).
- Vault cache at `~/.claude/wiki.local.md` recording `last_used` and `known_vaults`.
- Filesystem-shape marker for "is this a wiki?" — no plugin metadata in the user's vault.
- Bootstrap that creates only plugin-owned files (`index.md`, `log.md`, `raw/`, `wiki/`); never touches the user's `CLAUDE.md`.
- Generic notes-tooling autodetect: `.obsidian/`, `.logseq/`, `.dendron/`, `.foam/`.
