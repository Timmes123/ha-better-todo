# HA-betterTodo

Custom Home Assistant integration for a feature-rich, free todo list. Will be published publicly on GitHub (account: **Timmes123**) and installed via HACS as a custom repository — later possibly submitted to the official HACS catalog. A custom Lovelace card will likely be needed alongside the integration, since the built-in HA todo card is limited.

## Project status (2026-08-25)

- Setup complete: git, Python 3.14, Node.js 24, `gh` CLI (at `C:\Program Files\GitHub CLI\gh.exe` — not on PATH in tool shells) authenticated as Timmes123.
- The user's live HA instance is reachable via MCP; HACS 2.0.5 is installed there. WS commands can be tested via `ha_call_service(ws_command="better_todo/...")`.
- Repo: **github.com/Timmes123/ha-better-todo** (public, MIT). v0.3.0 is released, installed via HACS on the live HA, and verified working (backend logic tested over WS; todo/calendar entities confirmed). CI (hassfest + HACS action) green on main. v0.3 added: due times, reminders (events), advanced schedules (multi-weekday, last day, nth weekday, until/max), tags, mirror todo + calendar entities per list, card sort/dnd/editor/7 languages. Competitor benchmark: "Home Tasks" (L3t4l3s) — features analyzed from README only, never its code (user requires clean-room implementation).
- Test dashboard "Better ToDo" (`/better-todo/aufgaben`) exists on the live HA with the custom card; test data in lists Haushalt/Finanzen/Gesunde Woche.
- Gotchas learned: hassfest rejects `{...}` braces and UTF-8 BOMs in translation files (PowerShell 5.1 `Set-Content -Encoding utf8` writes a BOM — use `[System.IO.File]::WriteAllText` with `UTF8Encoding($false)`).
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
