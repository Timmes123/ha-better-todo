# HA-betterTodo

Custom Home Assistant integration for a feature-rich, free todo list. Will be published publicly on GitHub (account: **Timmes123**) and installed via HACS as a custom repository — later possibly submitted to the official HACS catalog. A custom Lovelace card will likely be needed alongside the integration, since the built-in HA todo card is limited.

## Project status (2026-08-25)

- Setup complete: git, Python 3.14, `gh` CLI installed and authenticated as Timmes123 (repo + workflow scopes).
- The user's live HA instance is reachable via MCP; HACS 2.0.5 is installed there.
- GitHub repo **not yet created** (working name suggestion: `ha-better-todo`, not confirmed).
- **Feature requirements are specified and agreed** — see `SPEC.md` (the authoritative design document; keep it updated when decisions change). Key decisions: fully custom data model (no HA todo entities as source of truth), 4 task types incl. plan-based vs. completion-based recurrence and weekly/monthly habit tasks with streaks, overdue = single task with "n× fällig" counter (complete one or all; no stacking), rotation assignment with per-task person pool, central feature toggles in the options flow, card shipped by the integration (single HACS repo).

## Hard rule: deployment only via HACS releases

The user explicitly forbade direct file deployment into their Home Assistant (no `ha_write_file` for integration code, no manual copying into `custom_components/`). Every change, including debug iterations, goes the official route:

1. Develop locally in this folder
2. Commit, bump version in `manifest.json`
3. Tag + publish a GitHub release with `gh`
4. Update the integration via HACS (can be driven over MCP)
5. Restart HA, verify via logs/entities over MCP (read-only access is fine)

Slower debugging is accepted; HACS must always be the single source of truth.

## Conventions

- User speaks German — respond in German.
- HA timezone: Europe/Berlin.
- HACS repo requirements to include from the start: `custom_components/<domain>/` with `manifest.json`, `hacs.json`, README, tagged releases, HACS validation GitHub Action.
