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
